#!/usr/bin/env python3
"""Publish JT Morning Brief episode files to the repo via the GitHub Git Data API.

Mirrors tools/api_publish.py exactly, namespaced under bedford/ for this separate show
(see RUNBOOK.md's Bedford Town section). Same reason for existing: the runner's git
credential path has proven unreliable, so this uses the Git Data API directly instead
of `git push`.

Usage: python3 tools/api_publish_bedford.py <base>       e.g. ep002
Env:   GITHUB_TOKEN, GITHUB_REPOSITORY (owner/repo)
"""
import base64, json, os, sys, urllib.request, urllib.error

BASE = sys.argv[1]
REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]
API = f"https://api.github.com/repos/{REPO}"
BRANCH = "master"


def call(path, payload=None, method=None):
    url = path if path.startswith("http") else API + path
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
        try:
            body = e.read().decode(errors="replace")
        except Exception:
            body = "<no body>"
        sys.stderr.write(f"API-CALL-FAILED {m} {url} -> HTTP {e.code}\n")
        sys.stderr.write(f"RESPONSE-BODY: {body[:1500]}\n")
        if payload is not None:
            sys.stderr.write(f"PAYLOAD-KEYS: {list(payload.keys())}\n")
            if "tree" in payload:
                sys.stderr.write(f"TREE-PATHS: {[t.get('path') for t in payload['tree']]}\n")
        sys.stderr.flush()
        sys.exit(1)


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

add = [f"bedford/episodes/{BASE}.mp3", "bedford/episodes/episodes.json", "bedford/feed.xml"]
if os.path.exists("bedford/cover.png"):
    add.append("bedford/cover.png")
# NOTE: bedford/archive/covered.md is intentionally NOT in this list, for the exact
# same reason archive/covered.md is excluded from tools/api_publish.py -- see that
# file's comment and RUNBOOK.md's Process log entry for 2026-08-28. This script never
# modifies bedford/archive/covered.md itself; it's edited only by the Cowork session
# via github_put_file, around the pending-file commits that trigger this workflow.
# base_tree above is fetched fresh from master's current tip, so this file inherits
# forward correctly with no re-upload needed -- re-uploading it from this job's
# on-disk checkout would risk silently clobbering a same-run session edit with a stale
# pre-session copy, exactly as happened to archive/covered.md on Ep20/Ep21.

tree = []
for path in add:
    if not os.path.exists(path):
        print(f"  skip missing {path}")
        continue
    tree.append({"path": path, "mode": "100644", "type": "blob", "sha": blob(path)})

# Permanently archive the script under bedford/transcripts/ before bedford/pending/
# gets swept below -- same reasoning as tools/api_publish.py: pending/ is a work
# queue, not an archive.
script_src = f"bedford/pending/{BASE}.txt"
if os.path.exists(script_src):
    tree.append({
        "path": f"bedford/transcripts/{BASE}.txt",
        "mode": "100644",
        "type": "blob",
        "sha": blob(script_src),
    })
    print(f"  archive {script_src} -> bedford/transcripts/{BASE}.txt")

# delete the pending files and any pruned episodes
existing_entries = call(f"/git/trees/{base_tree_sha}?recursive=1")["tree"]
existing = {e["path"] for e in existing_entries if e.get("type") == "blob"}
already_in_tree = {t["path"] for t in tree}
for path in existing:
    if path in already_in_tree:
        continue
    if path.startswith("bedford/pending/") and path.startswith(f"bedford/pending/{BASE}"):
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
        print(f"  delete {path}")
    elif path.startswith("bedford/episodes/") and path.endswith(".mp3") and not os.path.exists(path):
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
        print(f"  delete pruned {path}")

if not tree:
    print("nothing to publish")
    sys.exit(0)

new_tree = call("/git/trees", {"base_tree": base_tree_sha, "tree": tree})["sha"]
commit = call("/git/commits", {
    "message": f"Publish Bedford {BASE}",
    "tree": new_tree,
    "parents": [base_commit_sha],
})
call(f"/git/refs/heads/{BRANCH}", {"sha": commit["sha"], "force": False}, method="PATCH")
print(f"published commit {commit['sha'][:8]} with {len(tree)} tree entries")
