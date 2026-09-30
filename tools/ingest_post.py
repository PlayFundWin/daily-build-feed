#!/usr/bin/env python3
"""POST a finished episode to the deanlynn.com ingest function.

This is the ONE place that knows the ingest contract. If the endpoint, header
or payload shape changes on deanlynn.com, change it here and nowhere else.

Contract (as specified 2026-09-30; the endpoint was being built in parallel -
re-check against the live function before relying on anything marked below):
  POST https://deanlynn.com/functions/ingestDailyBuild
  Header  X-Ingest-Key: $DAILY_BUILD_INGEST_SECRET
  JSON    {kind: 'private'|'member',
           meta: {num, date, title, description, ...member fields},
           audio_base64 | audio_url,   (neither = text-only)
           transcript}
  Member meta fields: slug, dek, cold_open, chapters[{title,start_s}],
    stories[{id,tag,headline,short,facts[],what_it_means,confidence,
             sources[{name,url}],start_s}], quick_ones[{headline,url}],
    build{title,why_now,steps[],may[],may_not[]},
    vault_extras{build_pack_md,prompts[{title,body}]}, poll{question,options[]},
    newsletter_summary, narration
  Member posts always land as a draft on deanlynn.com for Dean to approve;
  nothing in this script can publish a member episode.
  UNVERIFIED: maximum request body size. A 20-minute private episode at 96k is
  ~14 MB of MP3 (~19 MB as base64). If the function rejects large bodies, set
  INGEST_MAX_INLINE_MB so this fails fast with a clear message, and switch to
  --audio-url once the audio is hosted somewhere the function can fetch it.
  UNVERIFIED: whether the function upserts on (kind, num). Workflow re-runs can
  post the same episode twice; the function should treat that as an update.

Usage:
  python3 tools/ingest_post.py --kind private --meta pending/epNNN.json \
      --transcript pending/epNNN.txt --audio episodes/epNNN.mp3
  python3 tools/ingest_post.py --kind member --meta members/pending/epNNN.json \
      --transcript build/member/transcript.txt --render build/member/render.json \
      [--audio build/member/member.mp3 | --audio-url https://... | (neither = text-only)]
  Add --dry-run to print the payload summary without sending.

Env: DAILY_BUILD_INGEST_SECRET (required unless --dry-run)
     INGEST_URL (optional override of the endpoint)
     INGEST_MAX_INLINE_MB (optional; refuse inline audio above this size)
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

INGEST_URL = "https://deanlynn.com/functions/ingestDailyBuild"
KEY_HEADER = "X-Ingest-Key"
SECRET_ENV = "DAILY_BUILD_INGEST_SECRET"
TIMEOUT = 300
RETRY_DELAYS = [10, 30, 90]

PRIVATE_META = ("num", "date", "title", "description")
MEMBER_META = ("num", "date", "title", "description", "slug", "dek", "cold_open",
               "chapters", "stories", "quick_ones", "build", "vault_extras", "poll",
               "newsletter_summary", "narration")


def build_meta(kind, meta, render):
    keys = PRIVATE_META if kind == "private" else MEMBER_META
    missing = [k for k in ("num", "date", "title", "description") if not meta.get(k)]
    if missing:
        raise SystemExit(f"::error::meta is missing required field(s): {missing}")
    out = {k: meta[k] for k in keys if k in meta}
    out["num"] = int(out["num"])
    if kind == "member":
        if render is None:
            raise SystemExit("::error::--render is required for kind member (narration + timings)")
        out["narration"] = render["narration"]
        # chapters: the script's [[CHAPTER]] markers are the source of truth
        out["chapters"] = render.get("chapters") or out.get("chapters") or []
        starts = render.get("story_starts") or {}
        stories = []
        for s in out.get("stories") or []:
            s = dict(s)
            s["start_s"] = starts.get(s.get("id"))
            if s["start_s"] is None and render["narration"] != "text_only":
                print(f"::warning::story {s.get('id')} has no [[STORY: {s.get('id')}]] marker; start_s left empty")
            stories.append(s)
        out["stories"] = stories
    return out


def post(url, secret, body_bytes):
    last = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        req = urllib.request.Request(url, data=body_bytes, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header(KEY_HEADER, secret)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.status, r.read().decode(errors="replace")
        except urllib.error.HTTPError as e:
            text = e.read().decode(errors="replace")
            last = f"HTTP {e.code}: {text[:800]}"
            if e.code == 413:
                raise SystemExit(f"::error::INGEST REJECTED BODY SIZE (413). Payload was "
                                 f"{len(body_bytes) / 1e6:.1f} MB. Use --audio-url or a smaller encode. {text[:300]}")
            if e.code < 500 and e.code not in (408, 429):
                raise SystemExit(f"::error::INGEST FAILED {last}")
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
        if attempt < len(RETRY_DELAYS):
            print(f"ingest attempt {attempt + 1} failed ({last}); retrying in {RETRY_DELAYS[attempt]}s", flush=True)
            time.sleep(RETRY_DELAYS[attempt])
    raise SystemExit(f"::error::INGEST FAILED after retries: {last}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["private", "member"], required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--render", help="render.json from tools/render_elevenlabs.py (member only)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--audio", help="local MP3 to send inline as base64")
    g.add_argument("--audio-url", help="URL the ingest function fetches the audio from")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(args.meta, encoding="utf-8") as f:
        meta = json.load(f)
    render = None
    if args.render:
        with open(args.render, encoding="utf-8") as f:
            render = json.load(f)
    with open(args.transcript, encoding="utf-8") as f:
        transcript = f.read()

    payload = {"kind": args.kind, "meta": build_meta(args.kind, meta, render), "transcript": transcript}
    audio_desc = "none (text-only)"
    if args.audio:
        size = os.path.getsize(args.audio)
        cap = os.environ.get("INGEST_MAX_INLINE_MB")
        if cap and size * 4 / 3 > float(cap) * 1e6:
            raise SystemExit(f"::error::Inline audio would be {size * 4 / 3 / 1e6:.1f} MB base64, over "
                             f"INGEST_MAX_INLINE_MB={cap}. Use --audio-url.")
        with open(args.audio, "rb") as f:
            payload["audio_base64"] = base64.b64encode(f.read()).decode()
        audio_desc = f"inline {size / 1e6:.1f} MB MP3"
    elif args.audio_url:
        payload["audio_url"] = args.audio_url
        audio_desc = f"url {args.audio_url}"

    body = json.dumps(payload).encode()
    m = payload["meta"]
    print(f"ingest {args.kind} ep{m['num']:03d} {m['date']} '{m['title']}': audio {audio_desc}, "
          f"transcript {len(transcript.split())} words, body {len(body) / 1e6:.1f} MB")
    if args.kind == "member":
        print(f"  narration={m.get('narration')} chapters={len(m.get('chapters') or [])} "
              f"stories={len(m.get('stories') or [])}")
    if args.dry_run:
        print("dry run: not sent")
        return

    secret = os.environ.get(SECRET_ENV, "").strip()
    if not secret:
        raise SystemExit(f"::error::{SECRET_ENV} is not set")
    url = os.environ.get("INGEST_URL", "").strip() or INGEST_URL
    status, text = post(url, secret, body)
    print(f"ingest OK: HTTP {status} {text[:500]}")


if __name__ == "__main__":
    main()
