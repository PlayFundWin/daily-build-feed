# The Daily Build — daily production runbook

Produce today's episode. Target: live in the feed by 07:00 UK time. Work unattended:
make reasonable choices, never block on questions, never fabricate.

Repo: `PlayFundWin/daily-build-feed`, branch `master`.
Feed: https://playfundwin.github.io/daily-build-feed/feed.xml

## Architecture — read this first

The Cowork sandbox CANNOT push binaries: `git push` is denied by the proxy (no repos in
the session's authorized set), GitHub release uploads are forbidden for this session
type, and R2 / api.cloudflare.com are blocked. So the split is:

- **This session does**: research, write the script, commit TEXT files via the GitHub
  MCP tools (`github_put_file`), dispatch the build workflow, verify, notify, log to
  Notion.
- **GitHub Actions does**: TTS render, MP3 encode, feed regeneration, committing the
  audio. Runners have full network and write access.

Commits made via the GitHub MCP tools DO fire the `push` trigger on `pending/**` (they're
authored as an external actor, not the runner's own `GITHUB_TOKEN`), so a build usually
starts on its own once both pending files land — sometimes before you get to the next
step. Still call `github_dispatch_workflow` (`build-episode.yml`, ref `master`) as a
belt-and-suspenders fallback if nothing seems to have started after a minute or two. The
workflow carries a `concurrency` group with `cancel-in-progress: true` (added
2026-08-13, after three overlapping runs from one episode's two pending-file commits
plus a manual dispatch), so extra triggers are safe — the newest one just supersedes any
earlier, still-running attempt instead of racing it to a duplicate publish. (The one
place `GITHUB_TOKEN`-authored pushes genuinely don't retrigger anything is the
workflow's own "Publish via API" step — that's a separate, still-correct fact; see the
comment above "Stage Pages site" in `build-episode.yml`.)

Pages hosting: this repo uses Actions-based Pages deployment (Settings → Pages →
Source: GitHub Actions), not the legacy branch/Jekyll builder — that builder got
permanently stuck on every single commit and never once served this repo (fixed
2026-08-06). `build-episode.yml`'s last two steps deploy the site directly
(`actions/upload-pages-artifact` + `actions/deploy-pages`), so a successful workflow
run means Pages is already live. `deploy-pages.yml` also exists in this repo as a
manual-trigger fallback (Actions tab → Deploy Pages → Run workflow) for redeploying
Pages without publishing a new episode.

## 1. Read the archive
Read `archive/covered.md` (raw URL:
https://raw.githubusercontent.com/PlayFundWin/daily-build-feed/master/archive/covered.md).
Note every item and idea already covered and any open threads marked FOLLOW-UP. Never
re-cover an item as new; follow-ups must reference the earlier episode by day. Also
check for a "Standing corrections" section at the end of the file — these are direct
corrections from Steve that override anything said in earlier episodes (e.g. a
FOLLOW-UP thread that's actually closed, or a standing fact about one of the ventures).
Read `episodes/episodes.json` for the next episode number (NNN, zero-padded to 3).

## 2. Research — three parallel subagents
Launch three general-purpose agents in ONE message so they run concurrently. Give each
today's date and the relevant archive lines so they skip covered ground.
- A: AI releases/features from the last 48h (Anthropic/Claude, OpenAI, Google, agent
  tooling, voice AI, no-code builders). Official changelogs first. Each item: what,
  exact date, source URL, small-business angle, CONFIRMED (page read) vs SEARCH-ONLY.
- B: Small AI-buildable business ideas with recent PUBLISHED revenue evidence (Indie
  Hackers, Hacker News, Starter Story, Product Hunt, subreddits). Pick ONE deep-dive
  idea: real named evidence, ~90% Claude-buildable in days, sellable in the UK, under
  five hundred pounds to start. Plus 3 runner-ups. Never invent numbers. Before picking,
  check `episodes/episodes.json` descriptions and `archive/covered.md` for ideas already
  featured — pick something meaningfully different in category, not a variant of one
  already covered.
- C: Sector news for the listener's ventures: UK fundraising/prize-draw tech and
  regulation; grassroots sports tech; UK EV destination charging. Check these named
  sources FIRST, before open web search, to keep this agent cheap on quiet weeks: the
  Fundraising Regulator's own consultation/registration pages, Zapmap and DfT public
  charging-point stats, and two or three named UK trade outlets (Third Sector, Civil
  Society, Fleet News / Fleet Point for EV). If those turn up nothing new beyond what's
  already in `archive/covered.md`, say so plainly and stop — do not pad by broadening
  into unrelated general AI/business news search just to fill space.

## 3. Script
Write the script following `STYLE.md` exactly. ~4,000 words (Kokoro at speed 1.05 runs
roughly 270 words per minute, so 4,000 words ≈ 15 minutes; scale up if you want closer
to 20). Blank line between paragraphs — each blank line becomes a spoken pause.

## 4. Queue it (text only — this is all the sandbox does)
Commit both files with `github_put_file`:
- `pending/epNNN.txt` — the script
- `pending/epNNN.json` — `{"num": NNN, "date": "YYYY-MM-DD", "title": "Ep NNN — ...",
  "description": "two-sentence summary"}`

Also update `archive/covered.md` in the same pass: append episode number, date, title,
one line per news item covered, the build idea with its evidence, and any FOLLOW-UP
threads opened or closed.

Note: `pending/` is a work queue, not an archive — the build workflow deletes both
files from it on every publish. It separately copies the script to a permanent
`transcripts/epNNN.txt` before doing so (added 2026-08-08), so the full script survives
for reuse (LinkedIn/blog/social repurposing) — don't rely on `pending/` for history, and
don't recreate the old behaviour of only keeping the two-sentence JSON description.

## 5. Build
Dispatch `build-episode.yml` on `master`. The workflow first checks the pending
episode's `date` against `episodes/episodes.json`'s most recent entry and refuses to
build if they match (added 2026-08-13 — guards against ever publishing two episodes
dated the same day, e.g. from an accidental double-trigger of this whole routine). It
then renders with Kokoro (voice `bm_daniel`, speed 1.05), encodes a 96k MP3, runs an
ASR-based content spot-check on the rendered audio (added 2026-08-13, see below),
registers the episode, prunes to the newest 30, regenerates `feed.xml`, publishes
everything to `master` via the Git Data API, then deploys `feed.xml` / `cover.png` /
`episodes/*.mp3` straight to GitHub Pages as its last two steps. Typical run: 10-20
minutes including the model downloads (cached between runs).

Poll the run until it completes. On failure, read the job logs, fix, and re-dispatch —
do not leave a half-published state (pending files present but no MP3).

**Audio content check** (`tools/verify_audio.py`): transcribes the finished MP3 with
faster-whisper (`tiny.en`, CPU) and compares the transcript's word count against the
script's. This is a coarse spot-check, not a word-for-word match — it exists to catch
truncation, silence, a stuck/looping render, or the wrong voice loading, none of which
the file-exists/`ffprobe` checks in section 6 would notice, since those only prove a
valid, playable MP3 of plausible duration exists, not that it says the right thing. The
pass/fail thresholds (0.55–1.6x the script's word count, set in `MIN_RATIO`/`MAX_RATIO`
in the script) are untuned as of 2026-08-13 — picked without a baseline of this
pipeline's actual Whisper-vs-script ratio on a known-good episode. If this step fails,
read the actual numbers in the job log before assuming the audio is broken — it may be a
threshold-tuning problem rather than a bad render, especially on the first few runs
after this was added. Tighten or loosen the thresholds once several real runs establish
what a normal ratio looks like for this voice/speed.

## 6. Verify
PRIMARY method — use the GitHub API, not a direct URL fetch. This sandbox's bash has no
general network egress (only allowlisted package registries — confirmed via curl 403
against the Pages domain), and WebFetch has proven unreliable against this feed's
XML/binary responses (repeatedly reports back "[binary data]" instead of content).
Don't waste a cycle rediscovering this each time — go straight to the API:
- `github_get` on `/repos/PlayFundWin/daily-build-feed/deployments?environment=github-pages&per_page=1`
  — the latest entry's `sha` should match the publish commit `api_publish.py` just made;
  then `github_get` its `/statuses` URL and confirm the newest status `state` is
  `success`.
- `github_get_file` on `episodes/episodes.json` (ref `master`) and confirm today's
  episode number, byte size and duration are present — `add_episode.py` only writes
  this file after `ffprobe` successfully reads a real MP3, so its presence is itself
  proof of a working render, not just a guess. It also only runs after the ASR content
  check (section 5) has passed, so this same presence check now doubles as indirect
  proof the audio content check passed too.
Treat those two checks together as sufficient proof of a live episode.
SECONDARY, opportunistic only: if you want a literal HTTP 200 and WebFetch happens to
cooperate, hit `https://playfundwin.github.io/daily-build-feed/feed.xml` and the day's
`episodes/epNNN.mp3` and check the `Content-Length` against the feed's `length`
attribute. But do not block publishing, retry-loop, or declare the run a failure solely
because this secondary check doesn't work — the API check above already is the proof.

If you see more than one workflow run in progress for the same episode (check
`/repos/PlayFundWin/daily-build-feed/actions/workflows/build-episode.yml/runs`), that's
expected now and then given two pending-file commits plus a possible manual dispatch —
the concurrency guard means only the newest survives, so just confirm the two checks
above pass, don't try to cancel anything yourself.

## 7. Log to Notion
Log today's episode to the **"Daily Build — Episode Log"** Notion database (lives under
the "PlayFundWin AI Ops" page; data source `collection://c7871de0-669f-4d3e-9d6b-ece7e19ed9a5`).
This is the durable, readable brief of what the episode contains — separate from, and
more detailed than, the "Daily Build — Ideas Ledger" database (which only tracks
build-ideas vs. actioned status).

Use `notion-create-pages` with `parent: {"type": "data_source_id", "data_source_id":
"c7871de0-669f-4d3e-9d6b-ece7e19ed9a5"}`. One page per episode:
- Properties: `Episode` (title — the full episode title, e.g. "Ep NNN — ..."),
  `Number`, `Date` (YYYY-MM-DD), `Duration` (mm:ss, from the feed/workflow),
  `Status` (`Published`), `Audio URL`
  (`https://playfundwin.github.io/daily-build-feed/episodes/epNNN.mp3`), `Description`
  (the two-sentence summary from `pending/epNNN.json`).
- Content (Notion markdown): `## News covered` (bulleted, one line per item, mirroring
  what you just wrote to `archive/covered.md` — don't shorten it to the two-sentence
  description), `## Build idea` (the pick, its evidence, and the runner-ups),
  `## Follow-ups` (status of any open FOLLOW-UP threads touched this episode),
  `## Ventures` (the PlayFundWin/LeaguePages/EV-Partnerships updates).

If Steve gives a direct correction in conversation that affects earlier episodes (a
FOLLOW-UP thread closing, a standing fact about a venture, etc.), do not rewrite the
core text of older Notion pages — append a dated "Standing correction" note instead
(same practice as `archive/covered.md`'s own "Standing corrections" section), and carry
it forward into today's brief.

If the Notion tools are unavailable or this step fails, say so plainly in the notify
step below and log the missed episode(s) to Notion retroactively next run — never let a
Notion failure block or delay publishing the episode itself.

## 8. Notify
`SendUserFile` is not available for the MP3 in this flow (the audio only exists on the
runner), so send Steve a short message: the episode title, a one-line summary, and the
fact that it is live in the feed. If ANY step failed, say plainly what failed and what
you did about it. Never claim success you did not verify.

## Cost discipline
Runs on a budget model by design. Three research subagents maximum plus at most one
verification pass. Keep subagent prompts tight. Never spend Higgsfield credits on the
daily episode.
