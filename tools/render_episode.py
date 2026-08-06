#!/usr/bin/env python3
"""Render a Daily Build episode script to WAV with kokoro-onnx.

Usage: python3 render_episode.py <script.txt> <out.wav> [voice] [speed]
Requires kokoro-v1.0.onnx and voices-v1.0.bin in the working directory:
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
  https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
Then encode: ffmpeg -i out.wav -codec:a libmp3lame -b:a 96k -ar 44100 out.mp3
"""
import sys, time
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

script_path, out_wav = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else "bm_daniel"
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.05

paragraphs = [p.strip() for p in open(script_path).read().split("\n\n") if p.strip()]
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
sr = 24000
gap = np.zeros(int(0.55 * sr), dtype=np.float32)
pieces = []
t0 = time.time()
for i, para in enumerate(paragraphs):
    samples, sr = k.create(para, voice=voice, speed=speed, lang="en-gb")
    pieces.append(samples.astype(np.float32))
    pieces.append(gap)
    print(f"[{i+1}/{len(paragraphs)}] {round(time.time()-t0)}s elapsed", flush=True)
audio = np.concatenate(pieces)
peak = np.abs(audio).max()
if peak > 0:
    audio = audio * (0.89 / peak)
sf.write(out_wav, audio, sr)
print(f"WROTE {out_wav}: {round(len(audio)/sr/60, 2)} minutes")
