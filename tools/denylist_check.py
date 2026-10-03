#!/usr/bin/env python3
"""Fail the member edition if it mentions anything from the private estate edition.

Usage: python3 tools/denylist_check.py <script.txt> [<meta.json> ...] [--denylist members/denylist.txt]

Checks the script text AND every string value in each JSON file (headlines,
facts, build steps, vault extras, newsletter summary ... all of it). Exit 1 on
any match, printing where it matched, so the workflow stops before a single
ElevenLabs character is spent. The producer should run this locally before
committing, too (see RUNBOOK.md step 3b).

Denylist syntax (members/denylist.txt), one entry per line:
  # comment              ignored, as are blank lines
  Some Phrase            case-insensitive, whole words/phrase only; any run of
                         spaces, hyphens or line breaks between words matches
  cs:Some Phrase         the same, but case-SENSITIVE
  re:<regex>             Python regex, case-insensitive
"""
import argparse
import json
import re
import sys

DEFAULT_DENYLIST = "members/denylist.txt"


def load_denylist(path):
    rules = []
    with open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            entry = line.strip()
            if entry.startswith("re:"):
                pat = re.compile(entry[3:], re.IGNORECASE)
            else:
                # tolerate any run of whitespace/hyphens (including a line break)
                # between words, for cs: entries too
                case_sensitive = entry.startswith("cs:")
                phrase = entry[3:] if case_sensitive else entry
                words = [re.escape(w) for w in re.split(r"[\s\-]+", phrase) if w]
                pat = re.compile(r"(?<!\w)" + r"[\s\-]*".join(words) + r"(?!\w)",
                                 0 if case_sensitive else re.IGNORECASE)
            rules.append((entry, pat, n))
    if not rules:
        raise SystemExit(f"::error::Denylist {path} is empty - refusing to pass an unchecked member edition.")
    return rules


def walk_strings(obj, path="$"):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk_strings(v, f"{path}[{i}]")


def scan(label, text, rules, hits, line_numbers=False):
    for entry, pat, rule_line in rules:
        for m in pat.finditer(text):
            lo, hi = max(0, m.start() - 40), min(len(text), m.end() + 40)
            ctx = text[lo:hi].replace("\n", " ")
            where = f"{label}:{text.count(chr(10), 0, m.start()) + 1}" if line_numbers else label
            hits.append(f"{where}: matched denylist entry '{entry}' (denylist line {rule_line}) -> ...{ctx}...")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", help="script .txt and/or meta .json files")
    ap.add_argument("--denylist", default=DEFAULT_DENYLIST)
    args = ap.parse_args()

    rules = load_denylist(args.denylist)
    hits = []
    for path in args.files:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        if path.endswith(".json"):
            data = json.loads(raw)
            for jpath, s in walk_strings(data):
                scan(f"{path} {jpath}", s, rules, hits)
        else:
            # Whole text, not line by line: a phrase wrapped across a line break
            # ("Play Fund" / "Win") must still fail the gate. Hits report the line
            # the match starts on.
            scan(path, raw, rules, hits, line_numbers=True)

    if hits:
        print(f"::error::DENYLIST GATE FAILED - {len(hits)} match(es). The member edition must not "
              f"mention private estate names, people or niches. Rewrite and recommit.")
        for h in hits:
            print(h)
        sys.exit(1)
    print(f"Denylist gate passed: {len(rules)} entries checked against {len(args.files)} file(s).")


if __name__ == "__main__":
    main()
