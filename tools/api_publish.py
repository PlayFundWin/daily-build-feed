#!/usr/bin/env python3
"""Publish episode files to the repo via the GitHub Git Data API.

Used instead of `git push` because the runner's git credential path has proven
unreliable. Handles binary (MP3, PNG) correctly via base64 blobs.

Usage: python3 tools/api_publish.py <base>       e.g. ep002
Env:   GITHUB_TOKEN, GITHUB_REPOSITORY (owner/repo)
"""
import base64, json, os, sys, urllib.request

BASE = sys.argv[1]
REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]
API = f"https://api.github.com/repos/{REPO}"
BRANCH = "master"


def call(path, payload=None, method=None):
    url = path if path.startswith("http") else API + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"))
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def blob(path):
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    sha = call("/git/blobs", {"content": content, "encoding": "base64"})["sha"]
    print(f"  blob {path} -> {sha[:8]}")
    return sha


ref = call(f"/git/ref/heads/{BRANCH}")
base_commit_sha = ref["object"]["sha"]
base_tree_sha = call(f"/git/commits/{base_commit_sha}")["tree"]["sha"]
print(f"base commit {base_commit_sha[:8]}")

add = [f"episodes/{BASE}.mp3", "episodes/episodes.json", "feed.xml"]
if os.path.exists("cover.png"):
    add.append("cover.png")
if os.path.exists("archive/covered.md"):
    add.append("archive/covered.md")

tree = []
for path in add:
    if not os.path.exists(path):
        print(f"  skip missing {path}")
        continue
    tree.append({"path": path, "mode": "100644", "type": "blob", "sha": blob(path)})

# Permanently archive the script under transcripts/ before pending/ gets swept below.
# pending/ is a work queue, not an archive -- it gets deleted on every publish, so
# without this the ~4,000-word researched script for every episode was simply lost,
# leaving only the two-sentence JSON description and the one-line covered.md summary.
script_src = f"pending/{BASE}.txt"
if os.path.exists(script_src):
    tree.append({
        "path": f"transcripts/{BASE}.txt",
        "mode": "100644",
        "type": "blob",
        "sha": blob(script_src),
    })
    print(f"  archive {script_src} -> transcripts/{BASE}.txt")

# delete the pending files and any pruned episodes
existing = {e["path"] for e in call(f"/git/trees/{base_tree_sha}?recursive=1")["tree"]}
for path in existing:
    if path.startswith("pending/") and path.startswith(f"pending/{BASE}"):
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
        print(f"  delete {path}")
    elif path.startswith("episodes/") and path.endswith(".mp3") and not os.path.exists(path):
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
        print(f"  delete pruned {path}")

if not tree:
    print("nothing to publish")
    sys.exit(0)

new_tree = call("/git/trees", {"base_tree": base_tree_sha, "tree": tree})["sha"]
commit = call("/git/commits", {
    "message": f"Publish {BASE}",
    "tree": new_tree,
    "parents": [base_commit_sha],
})
call(f"/git/refs/heads/{BRANCH}", {"sha": commit["sha"], "force": False}, method="PATCH")
print(f"published commit {commit['sha'][:8]} with {len(tree)} tree entries")
