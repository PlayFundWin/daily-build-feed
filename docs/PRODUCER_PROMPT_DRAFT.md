# Producer prompt additions — member edition + private estate edition

Draft, 2026-09-30. For Dean to paste into the Cowork desktop scheduled task that
produces The Daily Build. That task's current prompt text is not visible from the repo,
so these are additions, not a full replacement. Paste them only AFTER the PR is merged
(rollout step 4) — before that, `STYLE-MEMBERS.md`, `members/` and the new workflow
don't exist on `master`.

Keep the existing prompt's instruction to follow `RUNBOOK.md` and `STYLE.md`. RUNBOOK.md
carries the detail; these lines make the scheduled task actually do the new steps and
stop addressing Steve.

---

## Block 1 — replace any line that names Steve as the listener or recipient

```
The Daily Build is now Dean's private estate briefing. Listener: Dean Lynn. Apply it
covers Dean's estate as listed in STYLE.md ("Dean's estate"). Do not address Steve, do
not say "your three businesses", and do not cover EV-Partnerships or Onyxia (Dean no
longer has Onyxia; dropped 2026-09-30). Send the finished-run message to Dean, not
Steve.
```

## Block 2 — add after the research step

```
After the three research agents report, and before writing anything, commit today's
research as research/YYYY-MM-DD.json exactly as RUNBOOK.md step 2b describes: every
story, quick item, build pick, runner-up and sector item with the source URLs the
agents actually read. Mark every sector (agent C) item "private": true. Never type a
URL from memory; if an item has no readable source page, leave it out.
```

## Block 3 — replace the script-writing instruction

```
Write TWO scripts from research/YYYY-MM-DD.json (RUNBOOK.md step 3):
1. The private estate edition per STYLE.md, about 3,800 words (the voice runs at about
   190 words per minute, so that is about 20 minutes). Commit pending/epNNN.txt and
   pending/epNNN.json as before.
2. The member edition, "The Daily Build — with Dean Lynn", per STYLE-MEMBERS.md: Dean's
   first-person voice, 1,600 to 2,200 words, opening with the disclosure paragraph word
   for word, [[CHAPTER: ...]] and [[STORY: id]] marker lines, a generic build idea with
   steps and may / may-not guardrails, only research items marked "private": false.
   Write members/pending/epNNN.json with every field STYLE-MEMBERS.md lists (see
   members/pending/ep053.example.json for the shape), copying source URLs from the
   research file.
Before committing the member files, check both against members/denylist.txt (run
python3 tools/denylist_check.py members/pending/epNNN.txt members/pending/epNNN.json
if you can run Python; otherwise search the text for every denylist entry yourself).
Any match: rewrite, don't commit. Commit members/pending/epNNN.txt first, then
members/pending/epNNN.json. Same NNN as the private edition.
```

## Block 4 — replace the verify and notify instructions

```
Verify per RUNBOOK.md step 6 for BOTH workflows: build-episode.yml (private; check its
annotations for any ingest warning) and build-member-edition.yml (member; check which
voice read it). Then message Dean: the private episode title and one-line summary, and
whether it reached his private feed on deanlynn.com or only the old Pages feed; the
member edition title, which voice read it (clone / stand-in / text only), and that it
is waiting as a DRAFT on deanlynn.com for his approval. If anything failed, say exactly
what and what you did about it. Never report success you did not verify.
```

## Block 5 — add to the file-update step

```
In archive/covered.md, add one line per episode saying what the member edition used
(story headlines and build title). In reference/business-idea-categories.md, add the
member build idea as its own line marked "(member)".
```

---

Also on the scheduled task (Dean, by hand):
- Give it an end condition or review-by date if it doesn't have one (suggest: review
  after the first seven two-edition runs).
- Nothing else about its schedule needs to change: both editions come out of the same
  run.
