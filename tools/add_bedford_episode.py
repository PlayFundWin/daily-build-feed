#!/usr/bin/env python3
"""Register a rendered JT Morning Brief episode in bedford/episodes/episodes.json.

Usage: python3 tools/add_bedford_episode.py <base> <meta.json>
  <base>      e.g. ep002  -> bedford/episodes/ep002.mp3 must exist
  <meta.json> {"num": 2, "date": "2026-09-12", "title": "...", "description": "..."}

Also prunes to the newest 30 episodes (deletes older MP3s and their entries). Mirrors
tools/add_episode.py exactly, namespaced under bedford/ for this separate show.
"""
import json, os, subprocess, sys

base, meta_path = sys.argv[1], sys.argv[2]
meta = json.load(open(meta_path))
mp3 = f"bedford/episodes/{base}.mp3"

dur = float(subprocess.check_output([
    "ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", mp3,
]).decode().strip())

entry = {
    "num": int(meta["num"]),
    "date": meta["date"],
    "title": meta["title"],
    "description": meta["description"],
    "file": f"{base}.mp3",
    "bytes": os.path.getsize(mp3),
    "seconds": int(round(dur)),
}

path = "bedford/episodes/episodes.json"
eps = json.load(open(path)) if os.path.exists(path) else []
eps = [e for e in eps if e["num"] != entry["num"]]
eps.append(entry)
eps.sort(key=lambda e: e["num"], reverse=True)

for old in eps[30:]:
    old_path = f"bedford/episodes/{old['file']}"
    if os.path.exists(old_path):
        os.remove(old_path)
        print(f"pruned {old_path}")
eps = eps[:30]

json.dump(eps, open(path, "w"), indent=2)
print(f"registered episode {entry['num']}: {entry['seconds']}s, {entry['bytes']} bytes")
if not 780 <= entry["seconds"] <= 1560:
    print(f"WARNING: duration {entry['seconds']}s is outside the 13-26 minute target")
