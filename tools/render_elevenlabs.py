#!/usr/bin/env python3
"""Render the member edition ("The Daily Build — with Dean Lynn") to MP3.

Usage:
  python3 tools/render_elevenlabs.py --script members/pending/epNNN.txt \
      --meta members/pending/epNNN.json --out-dir build/member \
      --engine elevenlabs|kokoro|text-only [--pron members/pronunciations.md] [--plan]

Engines:
  elevenlabs  Dean's voice clone. eleven_multilingual_v2, chunks of at most
              2,500 characters, request stitching via previous_request_ids (last
              three request IDs), fixed seed, optional pronunciation dictionary,
              retries with backoff, quota pre-check.
  kokoro      Fallback. Kokoro bm_daniel 1.05 (same as the private edition),
              opening swapped for the stand-in disclosure + FALLBACK_LINE.
              (text-only keeps only the "drafted with AI help" clause.)
              Needs kokoro-v1.0.onnx and voices-v1.0.bin in the working dir.
  text-only   No audio. Writes the transcript and a render.json that says so.
  --plan      Print the chunk plan and exit (no API calls, no audio). Use locally.

Writes to --out-dir:
  member.mp3       128k mono MP3, loudness-normalised to about -16 LUFS, ID3 comment
                   stating the narration (not written for text-only)
  spoken.txt       exactly what was sent to TTS (aliases applied) - verify_audio input
  transcript.txt   the member-facing transcript (markers stripped, correct disclosure)
  render.json      {narration, seconds, chapters[{title,start_s}], story_starts{id:s},
                    chunks, characters, engine}

Chapter and story start times are exact: every [[CHAPTER]] / [[STORY]] marker
forces a new chunk, and start_s is the summed duration of everything before it.

Env (elevenlabs engine; names only, values live in repo secrets):
  ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID (required)
  ELEVENLABS_PRON_DICT_ID, ELEVENLABS_PRON_DICT_VERSION (optional, both or neither)
  ELEVENLABS_SEED (optional, default below)

Exit codes: 0 rendered, 1 failed (the workflow then falls back), 2 usage error.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import member_edition as me  # noqa: E402

API = "https://api.elevenlabs.io"
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
MAX_CHARS = 2500
DEFAULT_SEED = 20260930
VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.8,
    "style": 0.0,
    "use_speaker_boost": True,
}
RETRY_DELAYS = [5, 15, 45]  # seconds; 4 attempts in total per chunk
HTTP_TIMEOUT = 180
GAP_CHAPTER = 0.6   # seconds of silence before a new chapter
GAP_CHUNK = 0.25    # seconds of silence between other chunks
KOKORO_VOICE, KOKORO_SPEED, KOKORO_PARA_GAP = "bm_daniel", 1.05, 0.55
SAMPLE_RATE = 44100
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- chunk plan

def split_long(text, limit):
    """Split an over-long paragraph on sentence ends, then on commas, then hard."""
    if len(text) <= limit:
        return [text]
    parts, cur = [], ""
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if len(sent) > limit:
            for piece in re.split(r"(?<=,)\s+", sent):
                while len(piece) > limit:
                    parts.append(piece[:limit])
                    piece = piece[limit:]
                if len(cur) + len(piece) + 1 > limit and cur:
                    parts.append(cur)
                    cur = ""
                cur = (cur + " " + piece).strip()
            continue
        if len(cur) + len(sent) + 1 > limit and cur:
            parts.append(cur)
            cur = ""
        cur = (cur + " " + sent).strip()
    if cur:
        parts.append(cur)
    return parts


def build_chunks(blocks, pron_pairs):
    """Group paragraphs into chunks <= MAX_CHARS, starting a new chunk at every marker."""
    chunks = []
    cur = None
    for b in blocks:
        spoken = me.apply_pronunciations(b["text"], pron_pairs)
        pieces = split_long(spoken, MAX_CHARS)
        for i, piece in enumerate(pieces):
            starts_marker = i == 0 and (b["chapter"] or b["story"])
            if (cur is None or starts_marker
                    or len(cur["text"]) + 2 + len(piece) > MAX_CHARS):
                cur = {"text": piece,
                       "chapter": b["chapter"] if i == 0 else None,
                       "story": b["story"] if i == 0 else None,
                       "paragraphs": [piece]}
                chunks.append(cur)
            else:
                cur["text"] += "\n\n" + piece
                cur["paragraphs"].append(piece)
    for c in chunks:
        assert len(c["text"]) <= MAX_CHARS, "chunk over limit"
    return chunks


# ---------------------------------------------------------------- audio utils

def run(cmd):
    subprocess.run(cmd, check=True)


def duration(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", path]).decode().strip()
    return float(out)


def to_wav(src, dst):
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
         "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", dst])


def silence(dst, seconds):
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
         "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono", "-t", f"{seconds:.3f}",
         "-c:a", "pcm_s16le", dst])


def assemble(chunk_files, chunks, work, out_mp3, meta, narration):
    """Normalise chunks to WAV, add gaps, loudness-normalise, encode 128k MP3.
    Returns (total_seconds, chunk_starts)."""
    wavs, starts, t = [], [], 0.0
    gap_ch = os.path.join(work, "gap_chapter.wav")
    gap_ck = os.path.join(work, "gap_chunk.wav")
    silence(gap_ch, GAP_CHAPTER)
    silence(gap_ck, GAP_CHUNK)
    for i, (src, c) in enumerate(zip(chunk_files, chunks)):
        if i > 0:
            gap = gap_ch if c["chapter"] else gap_ck
            wavs.append(gap)
            t += GAP_CHAPTER if c["chapter"] else GAP_CHUNK
        w = os.path.join(work, f"norm_{i:03d}.wav")
        to_wav(src, w)
        starts.append(round(t, 2))
        t += duration(w)
        wavs.append(w)
    listing = os.path.join(work, "concat.txt")
    with open(listing, "w") as f:
        for w in wavs:
            f.write(f"file '{os.path.abspath(w)}'\n")
    joined = os.path.join(work, "joined.wav")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", listing, "-c", "copy", joined])
    comment = me.ID3_COMMENT_CLONE if narration == me.NARRATION_CLONE else me.ID3_COMMENT_FALLBACK
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", joined,
         "-af", LOUDNORM, "-ar", str(SAMPLE_RATE), "-ac", "1",
         "-codec:a", "libmp3lame", "-b:a", "128k", "-id3v2_version", "3",
         "-metadata", f"title={meta.get('title', '')}",
         "-metadata", "artist=Dean Lynn",
         "-metadata", "album=The Daily Build — with Dean Lynn",
         "-metadata", f"date={meta.get('date', '')}",
         "-metadata", f"comment={comment}",
         out_mp3])
    return round(duration(out_mp3), 2), starts


# ---------------------------------------------------------------- ElevenLabs

def http(method, url, key, body=None, accept="application/json"):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("xi-api-key", key)
    req.add_header("Accept", accept)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        # r.headers is an HTTPMessage: .get() is case-insensitive, which matters for
        # the "request-id" header used for stitching. Do not convert it to a dict.
        return r.status, r.headers, r.read()


def quota_precheck(key, needed_chars):
    """GET /v1/user/subscription and compare remaining characters with what we need.

    TO BE CONFIRMED against ElevenLabs' live API docs before relying on it: the
    endpoint path and the character_count / character_limit field names are
    what this code expects. If the call fails or the fields are missing we warn
    and carry on (the chunk calls will fail loudly on quota anyway), rather than
    block a render on an unverified check.
    Returns False only when the check ran and says we are short.
    """
    try:
        status, _, raw = http("GET", f"{API}/v1/user/subscription", key)
        sub = json.loads(raw)
        used, limit = int(sub["character_count"]), int(sub["character_limit"])
    except Exception as e:  # noqa: BLE001
        log(f"::warning::ElevenLabs quota pre-check could not run ({type(e).__name__}: {e}). "
            f"Endpoint/fields to be confirmed; continuing without it.")
        return True
    remaining = limit - used
    log(f"ElevenLabs quota: {used} of {limit} characters used, {remaining} left, this episode needs {needed_chars}.")
    if remaining < int(needed_chars * 1.05):
        log(f"::error::ElevenLabs quota too low: {remaining} characters left, need about {needed_chars}. "
            f"Falling back.")
        return False
    return True


def tts_chunk(key, voice_id, text, prev_ids, seed, dict_loc):
    body = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": VOICE_SETTINGS,
        "seed": seed,
    }
    if prev_ids:
        body["previous_request_ids"] = prev_ids[-3:]
    if dict_loc:
        body["pronunciation_dictionary_locators"] = [dict_loc]
    url = f"{API}/v1/text-to-speech/{voice_id}?output_format={OUTPUT_FORMAT}"
    last_err = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            status, headers, audio = http("POST", url, key, body, accept="audio/mpeg")
            if not audio:
                raise RuntimeError("empty audio body")
            req_id = headers.get("request-id")
            return audio, req_id
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:400]
            last_err = f"HTTP {e.code}: {detail}"
            if e.code not in (408, 409, 425, 429) and e.code < 500:
                break  # auth, validation, voice not found: retrying will not help
        except Exception as e:  # noqa: BLE001
            last_err = f"{type(e).__name__}: {e}"
        if attempt < len(RETRY_DELAYS):
            log(f"  chunk attempt {attempt + 1} failed ({last_err}); retrying in {RETRY_DELAYS[attempt]}s")
            time.sleep(RETRY_DELAYS[attempt])
    raise RuntimeError(f"ElevenLabs chunk failed: {last_err}")


def render_elevenlabs(chunks, work):
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "").strip()
    if not key or not voice_id:
        raise RuntimeError("ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID must both be set")
    seed = int(os.environ.get("ELEVENLABS_SEED") or DEFAULT_SEED)
    dict_id = os.environ.get("ELEVENLABS_PRON_DICT_ID", "").strip()
    dict_ver = os.environ.get("ELEVENLABS_PRON_DICT_VERSION", "").strip()
    dict_loc = None
    if dict_id and dict_ver:
        dict_loc = {"pronunciation_dictionary_id": dict_id, "version_id": dict_ver}
    elif dict_id or dict_ver:
        log("::warning::Only one of ELEVENLABS_PRON_DICT_ID / _VERSION is set; dictionary not used "
            "(local aliases from members/pronunciations.md still apply).")
    needed = sum(len(c["text"]) for c in chunks)
    if not quota_precheck(key, needed):
        raise RuntimeError("quota")
    files, prev_ids = [], []
    for i, c in enumerate(chunks):
        t0 = time.time()
        audio, req_id = tts_chunk(key, voice_id, c["text"], prev_ids, seed, dict_loc)
        path = os.path.join(work, f"chunk_{i:03d}.mp3")
        with open(path, "wb") as f:
            f.write(audio)
        if req_id:
            prev_ids.append(req_id)
        else:
            log("::warning::No request-id header returned; stitching continues without this chunk.")
        log(f"[{i + 1}/{len(chunks)}] {len(c['text'])} chars, {round(time.time() - t0)}s")
        files.append(path)
    return files


# ---------------------------------------------------------------- Kokoro

def render_kokoro(chunks, work):
    import numpy as np  # noqa: WPS433
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
    files = []
    for i, c in enumerate(chunks):
        pieces, sr = [], 24000
        for j, para in enumerate(c["paragraphs"]):
            samples, sr = k.create(para, voice=KOKORO_VOICE, speed=KOKORO_SPEED, lang="en-gb")
            pieces.append(samples.astype(np.float32))
            if j < len(c["paragraphs"]) - 1:
                pieces.append(np.zeros(int(KOKORO_PARA_GAP * sr), dtype=np.float32))
        audio = np.concatenate(pieces)
        peak = np.abs(audio).max()
        if peak > 0:
            audio = audio * (0.89 / peak)
        path = os.path.join(work, f"chunk_{i:03d}.wav")
        sf.write(path, audio, sr)
        log(f"[{i + 1}/{len(chunks)}] kokoro chunk rendered")
        files.append(path)
    return files


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--engine", choices=["elevenlabs", "kokoro", "text-only"], default="elevenlabs")
    ap.add_argument("--pron", default="members/pronunciations.md")
    ap.add_argument("--plan", action="store_true")
    args = ap.parse_args()

    with open(args.script, encoding="utf-8") as f:
        raw = f.read()
    with open(args.meta, encoding="utf-8") as f:
        meta = json.load(f)

    mode = {"elevenlabs": "clone", "kokoro": "fallback", "text-only": "text"}[args.engine]
    blocks, inserted = me.ensure_disclosure(me.parse_script(raw), mode=mode)
    if inserted:
        log("::warning::Script did not open with the disclosure paragraph; it has been inserted.")
    transcript = me.blocks_to_text(blocks)
    words = me.word_count(transcript)
    lo, hi = me.TARGET_WORDS
    if not lo <= words <= hi:
        log(f"::warning::Member script is {words} words; target is {lo}-{hi}.")

    pron = me.load_pronunciations(args.pron)
    chunks = build_chunks(blocks, pron)
    chapter_titles = [c["chapter"] for c in chunks if c["chapter"]]
    log(f"{words} words, {sum(len(c['text']) for c in chunks)} spoken characters, "
        f"{len(chunks)} chunks, {len(chapter_titles)} chapters, {len(pron)} pronunciation aliases.")

    if args.plan:
        # Actions logs on this repo are public while it is public: never print script
        # text there. The text preview only shows on a local run.
        show_text = os.environ.get("GITHUB_ACTIONS") != "true"
        for i, c in enumerate(chunks):
            tag = f" CHAPTER={c['chapter']}" if c["chapter"] else ""
            tag += f" STORY={c['story']}" if c["story"] else ""
            preview = f" | {c['text'][:70]!r}" if show_text else ""
            log(f"  chunk {i:02d}: {len(c['text']):4d} chars{tag}{preview}")
        return 0

    os.makedirs(args.out_dir, exist_ok=True)
    work = os.path.join(args.out_dir, "work")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    with open(os.path.join(args.out_dir, "transcript.txt"), "w", encoding="utf-8") as f:
        f.write(transcript)
    with open(os.path.join(args.out_dir, "spoken.txt"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(c["text"] for c in chunks) + "\n")

    render = {
        "engine": args.engine,
        "chunks": len(chunks),
        "characters": sum(len(c["text"]) for c in chunks),
        "words": words,
        "seconds": None,
        "chapters": [{"title": t, "start_s": None} for t in chapter_titles],
        "story_starts": {c["story"]: None for c in chunks if c["story"]},
    }

    if args.engine == "text-only":
        render["narration"] = me.NARRATION_TEXT_ONLY
        with open(os.path.join(args.out_dir, "render.json"), "w") as f:
            json.dump(render, f, indent=2)
        log("Text-only render.json written (no audio).")
        return 0

    try:
        if args.engine == "elevenlabs":
            files = render_elevenlabs(chunks, work)
            narration = me.NARRATION_CLONE
        else:
            files = render_kokoro(chunks, work)
            narration = me.NARRATION_FALLBACK
        out_mp3 = os.path.join(args.out_dir, "member.mp3")
        seconds, starts = assemble(files, chunks, work, out_mp3, meta, narration)
    except Exception as e:  # noqa: BLE001
        log(f"::error::{args.engine} render failed: {type(e).__name__}: {e}")
        return 1

    render["narration"] = narration
    render["seconds"] = seconds
    render["chapters"] = [{"title": c["chapter"], "start_s": s}
                          for c, s in zip(chunks, starts) if c["chapter"]]
    render["story_starts"] = {c["story"]: s for c, s in zip(chunks, starts) if c["story"]}
    with open(os.path.join(args.out_dir, "render.json"), "w") as f:
        json.dump(render, f, indent=2)
    shutil.rmtree(work, ignore_errors=True)
    log(f"WROTE {out_mp3}: {seconds}s ({round(seconds / 60, 1)} min), narration={narration}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
