#!/usr/bin/env python3
"""Spot-check that the rendered episode audio roughly matches the script.

Transcribes the MP3 with a small, fast Whisper model (faster-whisper, tiny.en,
CPU/int8) and compares word counts against the original script. This is
deliberately NOT a word-for-word check -- ASR errors and TTS pronunciation
quirks are expected even on a clean render -- it's a coarse guard against the
failure modes that today's checks (file exists, ffprobe reads a valid MP3)
can't catch: truncation, silence, a stuck/looping render, or the wrong voice
loading and producing garbage.

Added 2026-08-13 after a process review found that "a valid MP3 of plausible
duration exists" was the entire content-correctness check for a live public
feed. The thresholds below are a starting point (untuned on this pipeline's
actual output) -- expect to tighten or loosen them after a few real runs.
"""
import re
import sys

from faster_whisper import WhisperModel

# Whisper's tiny.en model under-transcribes somewhat even on a clean render
# (missed words, merged/dropped short words) -- 0.55 is a deliberately
# generous floor so a normal good render doesn't false-positive. 1.6 catches
# the opposite failure: looping, repeated segments, or garbled output that
# inflates the transcript well past what the script actually contains.
MIN_RATIO = 0.55
MAX_RATIO = 1.6


def word_count(text):
    return len(re.findall(r"\b\w+\b", text))


def main():
    if len(sys.argv) != 3:
        print("usage: verify_audio.py <mp3_path> <script_path>", file=sys.stderr)
        sys.exit(2)

    mp3_path, script_path = sys.argv[1], sys.argv[2]

    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()
    script_words = word_count(script_text)

    if script_words == 0:
        print("::error::Script is empty, cannot verify audio content against it.")
        sys.exit(1)

    print(f"Transcribing {mp3_path} with faster-whisper (tiny.en, CPU) for a content spot-check...")
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    segments, info = model.transcribe(mp3_path, beam_size=1, vad_filter=True)
    transcript = " ".join(segment.text for segment in segments)
    transcript_words = word_count(transcript)

    ratio = transcript_words / script_words if script_words else 0

    print(f"Script word count: {script_words}")
    print(f"Transcribed word count: {transcript_words}")
    print(f"Audio duration per Whisper: {info.duration:.1f}s")
    print(f"Ratio (transcribed / script): {ratio:.2f}")

    if ratio < MIN_RATIO:
        print(
            f"::error::AUDIO CONTENT CHECK FAILED - transcribed word count "
            f"({transcript_words}) is only {ratio:.0%} of the script's "
            f"{script_words} words. Likely truncated, silent, or badly "
            f"garbled render. Refusing to register/publish this episode."
        )
        sys.exit(1)

    if ratio > MAX_RATIO:
        print(
            f"::error::AUDIO CONTENT CHECK FAILED - transcribed word count "
            f"({transcript_words}) is {ratio:.0%} of the script's "
            f"{script_words} words, unexpectedly high. Possible looping or "
            f"garbled repeat. Refusing to register/publish this episode."
        )
        sys.exit(1)

    print(f"Audio content check passed ({ratio:.0%} of script word count transcribed).")


if __name__ == "__main__":
    main()
