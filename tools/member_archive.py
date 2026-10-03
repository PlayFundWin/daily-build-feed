#!/usr/bin/env python3
"""Archive a posted member episode's TEXT and clear it from the queue.

Moves members/pending/<base>.txt and .json to members/published/ (plus the
render.json that records narration and timings) in one commit via the Git
Data API, the same way tools/api_publish.py publishes the private edition.

Never commits audio. Member audio lives only on deanlynn.com; the MP3 on the
runner is thrown away with the runner.

Usage: python3 tools/member_archive.py <base> <render.json>     e.g. ep053
Env:   GITHUB_TOKEN, GITHUB_REPOSITORY (owner/repo)
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1]
RENDER = sys.argv[2]
REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]
API = f"https://api.github.com/repos/{REPO}"
BRANCH = "master"


def call(path, payload=None, method=None):
    url = API + path
    data = json.dumps(payload).encode() if payload is not None else None
    m = method or ("POST" if data else "GET")
    req = urllib.request.Request(url, data=data, method=m)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"API-CALL-FAILED {m} {url} -> HTTP {e.code}: {e.read().decode(errors='replace')[:1000]}\n")
        sys.exit(1)


def blob(path):
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    return call("/git/blobs", {"content": content, "encoding": "base64"})["sha"]


ref = call(f"/git/ref/heads/{BRANCH}")
base_commit = ref["object"]["sha"]
base_tree = call(f"/git/commits/{base_commit}")["tree"]["sha"]

tree = []
for ext in ("txt", "json"):
    src = f"members/pending/{BASE}.{ext}"
    if os.path.exists(src):
        tree.append({"path": f"members/published/{BASE}.{ext}", "mode": "100644", "type": "blob", "sha": blob(src)})
        tree.append({"path": src, "mode": "100644", "type": "blob", "sha": None})
        print(f"  archive {src} -> members/published/{BASE}.{ext}")
tree.append({"path": f"members/published/{BASE}.render.json", "mode": "100644", "type": "blob", "sha": blob(RENDER)})

for t in tree:
    assert not t["path"].endswith((".mp3", ".wav")), "member audio must never be committed"

new_tree = call("/git/trees", {"base_tree": base_tree, "tree": tree})["sha"]
commit = call("/git/commits", {"message": f"Member edition {BASE}: posted to deanlynn.com as draft",
                               "tree": new_tree, "parents": [base_commit]})
call(f"/git/refs/heads/{BRANCH}", {"sha": commit["sha"], "force": False}, method="PATCH")
print(f"archived commit {commit['sha'][:8]}")
