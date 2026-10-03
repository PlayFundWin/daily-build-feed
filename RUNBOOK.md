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

Also read the **Process log** section near the end of this file — it's the same idea as
covered.md's Standing corrections, but for how this pipeline itself is run rather than
episode content. It's short; read it every time.

## 2. Research — three parallel subagents
Launch three general-purpose agents in ONE message so they run concurrently. Give each
today's date and the relevant archive lines so they skip covered ground.

Research window (corrected 2026-09-18 — see Process log): do NOT use a fixed "last 48
hours" cutoff for agent A. Read the most recent entry in `episodes/episodes.json` (or
`archive/covered.md`) and use THAT episode's date as the actual research boundary —
"everything dated after the last published episode." A fixed 48-hour window kept
clipping stories right at the edge (flagged as "just outside window" across Ep19, 28,
36, 38, 40 and 41 alone), sometimes covering them a day late and sometimes narrating
them as boundary cases mid-script for no reason. Using the actual last-episode date
instead means nothing falls in the gap and nothing gets covered twice, regardless of
whether an episode ships early, late, or exactly on schedule.

- A: AI releases/features dated after the last published episode (see Research window
  above) — Anthropic/Claude, OpenAI, Google, agent tooling, voice AI, no-code builders.
  Read `reference/ai-news-sources.md` FIRST (added 2026-09-18 — see Process log) and
  hit every URL on it directly rather than relying on open search to surface what's
  new; only search the open web for stories those sources don't cover themselves
  (secondhand financial press, industry commentary). Each item: what, exact date,
  source URL, small-business angle, CONFIRMED (page read) vs SEARCH-ONLY. No-code
  builders: check Lovable AND Base44 by name every pass (added 2026-09-16 at Steve's
  explicit request — Base44 had never once appeared in this show despite Lovable being
  a running thread since Ep8; Base44 is Wix-owned since an ~$80M acquisition, reportedly
  around $100-150M ARR as of September 2026, and ships several updates a day via its
  own changelog, so checking it directly is cheap even on a quiet day).
- B: Small AI-buildable business ideas with recent PUBLISHED revenue evidence (Indie
  Hackers, Hacker News, Starter Story, Product Hunt, subreddits including r/SaaS and
  r/microsaas, TrustMRR/RevenueCat-verified listings, Getlatka, Failory case studies,
  founder-interview podcasts like My First Million and The Bootstrapped Founder). Pick
  ONE deep-dive idea: real named evidence, ~90% Claude-buildable in days, sellable in
  the UK, under five hundred pounds to start. Plus 3 runner-ups. Never invent numbers.
  Before picking, read `reference/business-idea-categories.md` (added 2026-09-18 — see
  Process log) as a fast first filter for mechanics already used, then spot-check the
  actual `archive/covered.md` entry for anything that looks close — pick something
  meaningfully different in category, not a variant of one already covered. Append one
  line to `reference/business-idea-categories.md` for today's pick in the same pass as
  the rest of step 4's commits.
- C: Sector news for the listener's ventures: UK fundraising/prize-draw tech and
  regulation; grassroots sports tech; UK EV destination charging. Check these named
  sources FIRST, before open web search, to keep this agent cheap on quiet weeks: the
  Fundraising Regulator's own consultation/registration pages (baseline facts are also
  in `reference/fundraising-regulator-notes.md` — read that first and only search for
  what's changed since its date-stamp, rather than re-deriving the whole picture from
  scratch every episode; added 2026-09-16, see Process log), Zapmap and DfT public
  charging-point stats, and two or three named UK trade outlets (Third Sector, Civil
  Society, Fleet News / Fleet Point for EV). If those turn up nothing new beyond what's
  already in `archive/covered.md`, say so plainly and stop — do not pad by broadening
  into unrelated general AI/business news search just to fill space. Note: DfT's public
  charging-point statistics are typically published around 09:30 UK time — since this
  show targets a 07:00 UK ship time, don't chase "today's" DfT release on its actual
  publish day expecting fresh numbers; plan to report the real figures the day after
  they land instead (see Process log, 2026-08-27).

  EV-Partnerships thesis (corrected 2026-09-16, at Steve's explicit direction — see
  Process log): this is NOT primarily a match-day-utilisation bet. The pitch is a
  community-hub model — a small local club (football, rugby, cricket, golf) that
  already has a bar, restaurant or cafe and is a place people return to regularly, not
  just on fixture days, so EV charging there gets used far more like a destination
  charger than a stadium-only one. The eight named national operators
  (IONITY/RAW Charging/Allego/Believ/InstaVolt/Osprey/GRIDSERVE/Pod Point) are tracked
  because they are the plausible THIRD-PARTY entrants into this space — that thread
  measures whether the big networks have noticed grassroots clubs as a category, which
  is a genuinely separate question from whether EV-Partnerships' own direct,
  club-by-club sales motion is working. Do not conflate "no national operator has
  moved" with "the thesis is unproven" — EV-Partnerships sells directly and Steve has
  said (2026-09-16, see covered.md Standing corrections) that this is already
  happening; treat the operator-gap thread and EV-Partnerships' own pipeline as two
  separate facts in the script rather than one.

  Operator-gap reporting cadence (corrected 2026-09-18, at Steve's explicit direction —
  see Process log): Steve already knows where the eight named operators sit and does not
  want the "checked again, nothing new, gap still open for N consecutive episodes" beat
  repeated every single episode — he flagged this as actively unwanted, not just stale
  phrasing. From Ep42 onward: keep checking the eight operators as part of research every
  episode, so nothing is missed, but only put it in the script when there's an actual
  finding — a real new operator move at a sports/leisure venue, confirmed or debunked.
  Do not narrate "still nothing," the running episode-count, or the "genuine gap vs.
  match-day economics" theory as filler when nothing has changed. If nothing has changed,
  the operator-gap thread simply does not appear in that day's script — handle it the same
  way the retired prize-draw-ruling thread (Ep15/Steve correction) is handled.

Vary how you phrase these three briefs and which named sources you check first from one
day to the next — don't silently reuse identical query wording or check the same source
first every single run, since that flattens both what gets found and how the eventual
script reads (see Process log, 2026-08-27). Rotate the order within a category (e.g.
don't always hit Indie Hackers before Starter Story, don't always check the Fundraising
Regulator before Zapmap) and phrase each day's actual search queries freshly.

## 3. Script
Write the script following `STYLE.md` exactly, including its vocabulary-variety rules —
don't lean on the same connective phrases or copy any of STYLE.md's example phrasing
verbatim into the script episode after episode; every example in that file illustrates a
pattern, it isn't text to reuse. ~4,000 words (Kokoro at speed 1.05 runs
roughly 270 words per minute, so 4,000 words ≈ 15 minutes; scale up if you want closer
to 20). Blank line between paragraphs — each blank line becomes a spoken pause.

## 4. Queue it (text only — this is all the sandbox does)
Commit both files with `github_put_file`:
- `pending/epNNN.txt` — the script
- `pending/epNNN.json` — `{"num": NNN, "date": "YYYY-MM-DD", "title": "Ep NNN — ...",
  "description": "two-sentence summary"}`

Also update `archive/covered.md` in the same pass: append episode number, date, title,
one line per news item covered, the build idea with its evidence, and any FOLLOW-UP
threads opened or closed. In the same pass, append today's pick to
`reference/business-idea-categories.md` (name + one-line mechanic) — see step 2B.

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
- `github_get_file` on `archive/covered.md` (ref `master`) and confirm today's episode
  actually has a section in it (added 2026-08-27, see Process log — Ep20 was published
  with no covered.md entry at all and nothing in this runbook would have caught it
  before this check existed).
Treat those three checks together as sufficient proof of a live, properly-recorded
episode.
SECONDARY, opportunistic only: if you want a literal HTTP 200 and WebFetch happens to
cooperate, hit `https://playfundwin.github.io/daily-build-feed/feed.xml` and the day's
`episodes/epNNN.mp3` and check the `Content-Length` against the feed's `length`
attribute. But do not block publishing, retry-loop, or declare the run a failure solely
because this secondary check doesn't work — the API checks above already are the proof.

If you see more than one workflow run in progress for the same episode (check
`/repos/PlayFundWin/daily-build-feed/actions/workflows/build-episode.yml/runs`), that's
expected now and then given two pending-file commits plus a possible manual dispatch —
the concurrency guard means only the newest survives, so just confirm the checks
above pass, don't try to cancel anything yourself.

## 7. Log to Notion
Log today's episode to the **"Daily Build — Episode Log"** Notion database (lives under
the "PlayFundWin AI Ops" page; data source `collection://c7871de0-669f-4d3e-9d6b-ece7e19ed9a5`).
This is the durable, readable brief of what the episode contains — separate from, and
more detailed than, the "Daily Build — Ideas Ledger" database (see step 7a below, which
is a separate step and must not be skipped).

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

## 7a. Log to Ideas Ledger
Also upsert one entry for today's build idea in the **"Daily Build — Ideas Ledger"**
Notion database (data source `collection://eb0480b5-9d8f-43dd-91d8-76fa1032eb30`, lives
under "PlayFundWin AI Ops"). This step was missing from the runbook for the first 20
episodes and the ledger drifted badly out of date as a result (fixed 2026-08-27, see
Process log) — do not skip it.

Use `notion-create-pages` with `parent: {"type": "data_source_id", "data_source_id":
"eb0480b5-9d8f-43dd-91d8-76fa1032eb30"}`. One page for today's build idea:
- `Idea` (title — "Ep NNN — <idea name>, niched to <venture>" where it was niched for
  one of Steve's ventures, otherwise just "Ep NNN — <idea name>")
- `Episode` (number), `Date` (YYYY-MM-DD)
- `Evidence` (named source + revenue figure cited on air, one or two sentences)
- `Stream` (PFW / LeaguePages / Energy Partners / Cross-venture / New/Standalone)
- `Status`: always `Proposed` by default. Only ever set `In Progress` or `Live` if
  Steve has explicitly said, in conversation, that he or someone named is acting on it
  — never infer this from the episode content alone.
- `Owner`: `Unassigned` by default; only set to a named person if Steve has said so
  explicitly.

This is a **passive record only**. Steve does not want ideas he hasn't acted on chased,
resurfaced, or asked about, on air or anywhere else — if he wants to progress an idea
he'll raise it himself in chat. Never build or run any mechanism that revisits a
`Proposed` idea to report or ask what happened to it.

## 8. Notify
`SendUserFile` is not available for the MP3 in this flow (the audio only exists on the
runner), so send Steve a short message: the episode title, a one-line summary, and the
fact that it is live in the feed. If ANY step failed, say plainly what failed and what
you did about it. Never claim success you did not verify.

## Process log
Dated entries only, added when a real gap in this pipeline is found and fixed — not a
running commentary. This section is read in step 1 alongside the archive.

- 2026-09-18 (later same day): Steve asked how to improve the research pass generally.
  Two concrete gaps, not a vague "widen the scope": (1) a fixed 48-hour lookback window
  on agent A kept clipping stories at the edge — flagged "just outside window" across
  Ep19/28/36/38/40/41 — replaced with "everything since the last published episode's
  date," read from `episodes/episodes.json`. (2) "Check official changelogs first" was
  too vague to reliably act on — it's exactly how Base44 went unmentioned for five
  weeks despite a similar instruction already existing. Added
  `reference/ai-news-sources.md`, a concrete checklist of URLs agent A must hit
  directly every pass (including two never-checked-before sources, Perplexity and
  Hugging Face). Also added `reference/business-idea-categories.md` for agent B, a
  cheap first-pass filter against 40-plus episodes of prior picks, since scanning all
  of `archive/covered.md` for category uniqueness is getting expensive. Both reference
  files follow the same pattern as `reference/fundraising-regulator-notes.md` — a
  standing checklist that gets updated as sources/categories change, not re-derived
  from scratch every episode.
- 2026-09-18: Steve gave two live corrections outside the normal episode flow, both about
  the show repeating itself when nothing has actually changed. (1) The sports-venue
  EV-charging operator-gap thread had been running a "checked again, nothing new, gap
  still open for N episodes" beat every single episode since Ep18 — Steve said plainly to
  stop, he already knows where the operators sit and only wants to hear about it when
  there's an actual finding. Step 2C corrected accordingly: keep checking quietly, only
  script it on a real change. (2) Steve pushed back on being told the Meridian FC
  installation "isn't confirmed" — to be precise, the archive has recorded it as his
  stated fact since 2026-09-11/16 and never disputed it; what's been withheld is naming
  the club ON AIR, which is a separate, explicit-consent question he was asked twice
  (Ep37, Ep39) and hadn't yet answered. Distinction restated to Steve directly rather than
  silently clearing the on-air block; see covered.md Standing corrections for whatever he
  decides.

- 2026-09-16: Steve raised three fixes in one conversation, outside the normal episode
  flow. (1) Base44 had never once been checked or mentioned despite Lovable running
  since Ep8 — step 2A now names both explicitly. (2) The EV-Partnerships thesis this
  show has been narrating (a match-day-utilisation bet, "genuine gap vs. fixture-day
  economics" per Ep36-38) was wrong — Steve's actual pitch is a community-hub model
  (clubs with a bar/restaurant/cafe that people visit regularly, not just on fixture
  days), and EV-Partnerships sells directly club-by-club rather than waiting for a
  national operator to move — step 2C corrected accordingly. (3) Steve asked, in plain
  terms, what tracking the Fundraising Regulator actually gets PlayFundWin beyond extra
  work — researched properly this session (see `reference/fundraising-regulator-notes.md`,
  new this date): registration is voluntary, not a legal requirement, gated behind a
  proposed charitable-contribution threshold (10% 2026/27 → 15% 2027/28 → 20% 2028/29),
  and buys the Fundraising Badge as a public trust signal in a sector the Regulator's
  own reasoning says is confusing donors about how much money reaches charity. The
  sharper reason to keep tracking it: DCMS's separate Voluntary Code of Good Practice
  for Prize Draw Operators (took effect 2026-05-20) states plainly that if voluntary
  self-regulation doesn't resolve the sector's problems, government will legislate —
  so staying ahead of this is a hedge against it becoming mandatory, not goodwill. Ep40
  must fold this reasoning into its Apply It segment for PlayFundWin rather than
  repeating bare status — a listener who's heard eight "still pending" episodes is
  owed the actual "why," not just another status line. After Ep40 carries it once,
  STYLE.md's normal don't-repeat-yourself discipline applies — no standing instruction
  to re-explain this every episode, just don't leave it unexplained forever either.
- 2026-08-27: The Ideas Ledger (see 7a) wasn't being updated per-episode — this runbook
  only ever referenced Episode Log, so the ledger had 4 entries out of 20 episodes.
  Added step 7a; backfilled the missing 16 historical entries the same day, sourced
  from `archive/covered.md` and `episodes/episodes.json` (thin entries marked as thin,
  nothing invented).
- 2026-08-27: `archive/covered.md` silently missed an entire episode (Ep20) with no
  error anywhere — the verify step (section 6) only ever checked that the audio
  published, never that the archive got its entry. Verify now also confirms
  `covered.md` has a section for the just-published episode number.
- 2026-08-27: DfT charging-point stats structurally can't be live when this show ships
  (07:00 UK target vs DfT's ~09:30 publish time) — flagged as "check today" across four
  separate episodes (17–20) without ever landing real numbers on the actual release
  day. Research agent C (step 2) now plans to report real figures the day after they
  publish rather than chasing them on release day itself.
- 2026-08-27: Steve does not want the podcast chasing or resurfacing ideas he hasn't
  acted on. The Ideas Ledger (7a) is a passive record only; no on-air "what happened to
  last idea" segment exists or should ever be built.
- 2026-08-27: Steve flagged the show repeating itself episode to episode — the fixed
  segment structure was producing near-identical phrasing (STYLE.md's own example
  confidence-flag line was found copy-pasted almost verbatim into Ep21's actual script
  rather than used as an illustration). STYLE.md now has explicit vocabulary-variety
  rules; step 2's research briefs are now varied in phrasing/source order rather than
  reused verbatim day to day.
- 2026-08-27: Steve wants the feed made more private (it was previously fine being
  public-but-obscure). Implementation approach not yet decided/built as of this entry —
  update this log once it is.
- 2026-08-28: Found the actual root cause of Ep20 and Ep21 both publishing with no
  `covered.md` entry (the 2026-08-27 fix only added a verify check for this, it never
  found *why* it kept happening). `tools/api_publish.py` fetches a fresh `base_tree`
  from master right before publishing (correct), but then explicitly re-uploaded
  `archive/covered.md` from its own on-disk checkout as one of the tree blobs anyway —
  and that checkout is pinned to the push that triggered the run, so it's stale
  relative to anything committed to master afterward. Since this session typically
  commits `archive/covered.md` alongside or after the `pending/` files (which
  auto-trigger the build via the `push` event), the sequence in practice is: pending
  files land → build starts and checks out the repo → session commits
  `archive/covered.md` (now stale in the running job's checkout) → job's publish step
  re-uploads that stale local copy, silently overwriting the newer commit on master.
  `RUNBOOK.md` was never affected by this because it was never in `api_publish.py`'s
  explicit re-upload list, so it always inherited correctly through `base_tree`.
  Fixed by removing `archive/covered.md` from that list — it now inherits through
  `base_tree` the same way, no re-upload needed since this script never actually
  modifies that file itself. Also hit this exact bug live during the Ep22 run today:
  committed `archive/covered.md` at 09:37 while the auto-triggered build (checked out
  09:35) was still running, watched the publish step (09:46) clobber it back to the
  pre-session state, and re-landed the correct content afterward once the run had
  finished (so no further publish could clobber it again). Section 6's covered.md
  check is what caught this live before the notify step; keep trusting it. If it fails
  again after this fix, the api_publish.py theory above is wrong or incomplete — read
  the job log's `PUBLISH-VIA-API`/tree-entries output for that run before backfilling
  again, rather than assuming this same cause.

## Cost discipline
Runs on a budget model by design. Three research subagents maximum plus at most one
verification pass. Keep subagent prompts tight. Never spend Higgsfield credits on the
daily episode.

# JT Debrief — production runbook

Renamed and restructured from "JT Morning Brief" 2026-10-03, at Steve's direction —
see the Process log below for the full reasoning. Still the second, separate show in
this same repo for James (assistant manager, Bedford Town FC) rather than Steve; still
lives entirely under `bedford/`, with the same feed, the same episode numbering, and
the same session/Actions split as before (see the Architecture section at the top of
this file). What changed is the trigger and the content, not the plumbing: this show
no longer runs daily and no longer covers team news or the wider divisional picture.
It is event-triggered — it exists to turn a scouting data file Steve uploads (a
Wyscout/Hudl-style team report on Bedford Town's next opponent so far, or similar)
into a plain-language breakdown of that opponent for the coaching staff, plus whatever
supplementary research confirms, extends, or dates that data. Read STYLE.md's JT
Debrief section (same location in that file, below the Daily Build style guide), not
the old Bedford Town section, before writing a script for this show.

Feed: https://playfundwin.github.io/daily-build-feed/bedford/feed.xml (unchanged)
Workflow: `.github/workflows/build-bedford-episode.yml`, triggered on push to
`bedford/pending/**` (unchanged — see the Architecture section above for the two-track
session/Actions split; not repeated here). This push trigger already IS this show's
on-demand mechanism — there is no cron involved in producing an episode, and there
never needs to be again for this show.

## Trigger — no schedule
There is no scheduled task driving this show. The scheduled task that used to fire
this routine ("JT Morning Brief — daily episode", trig_01B71Nzn5MgvukkokeGNvce8) has
been disabled, not deleted, 2026-10-03 — deleting it would have ended the very session
that disabled it, since that scheduled task is what started it (a scheduled task
cannot delete itself; see its own tool's refusal message if this comes up again).
Leave it disabled; do not re-enable it and do not create a replacement scheduled task
for this show without Steve explicitly asking for one. An episode happens only when
Steve uploads a data file for a specific opponent in conversation. Do not build an
episode from opposition analytics alone without a genuine data file behind it — the
hard content rule against ever inventing a stat makes the data file a prerequisite,
not an optional nice-to-have.

## League tiers — reconfirm every season, never assume
As of this show's launch (September 2026), Bedford Town sit in **National League
North** (Step 2). One tier above is the **National League** (Step 1); one tier below
is the **Southern League Premier Division Central** (Step 3, the league Bedford Town
were promoted from). Composition of all three leagues, and Bedford Town's own
division, changes at the end of every season via promotion/relegation — verify all
three are still correct at the start of a new season (roughly each June/July) before
relying on them, rather than carrying last season's structure forward unchecked. This
still matters for this show even though it no longer covers the wider divisional
picture day to day, because it governs which league table/results source applies to
whichever team is the current focus.

## 1. Read the archive
Read `bedford/archive/covered.md`. Note every opponent, framing, and closing line
already used — closing quotes especially must never repeat. If this episode's focus
team has appeared before (a repeat opponent later in the season), reference the
earlier episode rather than re-covering the same ground from scratch. Check the
"Standing corrections" section for anything that overrides an earlier episode. Read
`bedford/episodes/episodes.json` for the next episode number — numbering continues
from the old show, it does not reset with the rename (same precedent as the
2026-09-11 "Bedford Town Briefing" to "JT Morning Brief" rename; see the Process log).

## 2. Read the data file
The uploaded file (a PDF so far — a Wyscout/Hudl-style "Team Report": players and
player stats, formations, match-by-match breakdowns, defence, build-up, attack,
finishing, transitions, sustained danger, and set pieces) is this episode's spine.
Read every page — these reports run long and the useful detail is spread across the
player-stats tables, the per-match formation/lineup pages, and the zone-by-zone
duel/defence pages, not just a summary page. Before writing anything else, note
explicitly:
- What window the data covers — how many games, against whom, which dates. This show
  must state that window on air; never let a listener assume "the data" means "the
  season" when it might mean five games.
- The team-level aggregate numbers for both the focus team and their opposition across
  that window — goals, expected goals, possession, pass accuracy, PPDA (passes per
  defensive action, a pressing-intensity metric — explain it in the script, don't just
  name it). The gap between goals and expected goals is often the single most useful
  line in the episode.
- The individual players producing or conceding the most, by category: shots and
  expected goals, key passes and expected assists, dribbles, duels won and lost by
  zone, crosses, set-piece takers.
- Set-piece patterns: corners and free kicks, who takes them, which side, conversion
  so far.
Cross-check anything you plan to state as a specific scoreline, scorer, or table
position against the research in step 3, same discipline as every other show in this
repo. Ep 2's Chester FC report checked out exactly against Football Web Pages'
independent record, including scorers, for its most recent match — a good first data
point that this report format is reliable, but confirm each time rather than assuming
that holds forever; a single clean check is not a standing guarantee.

## 3. Research — supplementary, focus team only
Confirm and extend what the data file shows. Do not research, and do not fold in,
anything about Bedford Town's own squad, shape, or personnel — Steve has been
explicit that matching the opposition's weaknesses to Bedford's own players and
tactics is the coaching staff's job, not this show's. Stay on the opposition's side of
the ball throughout. Tag every claim CONFIRMED (a source page actually read) or
SEARCH-ONLY, same convention as the rest of this repo. Roughly in priority order:
- The fixture itself: confirm date, venue, and competition from Football Web Pages or
  the focus team's own site — don't assume the data file's most recent match is close
  to today's date.
- Current league position and form, from Football Web Pages or NonLeagueHQ (the same
  stats backbone this repo already uses) — gives the data file's form run context: a
  hot streak, a slump, settled mid-table, whatever it actually is.
- Management and squad context: who manages the focus team, how long, any recent
  managerial change. This explains shifts the data file alone can't — a new manager
  mid-season is a plausible reason underlying numbers and actual results diverge. The
  focus team's own site/news page plus a general web search for recent, dated
  coverage are the right tools here.
- Team news close to the actual fixture — injuries, suspensions, likely absentees.
  Often genuinely unavailable when an episode is built well ahead of kickoff; say so
  plainly rather than leave a silent gap. Built closer to kickoff, the focus team's
  own X account and site are the first place to check — same sourcing tier the old
  Morning Brief used for its day-before scan.
- Wider storylines only if they bear directly on the focus team (a managerial change,
  a financial story, a genuine injury crisis) — this show does not need a wider
  National League North round-up; stay on the one team.

Named sources, reused from this repo's existing Bedford Town coverage tiers:
- **First-party / CONFIRMED-grade**: the focus team's own X account and club site;
  TheFA.com; the National League's own site; the Southern League's own site.
- **Stats backbone**: Football Web Pages (`footballwebpages.co.uk` — fixtures,
  results, tables, form, for every step) and NonLeagueHQ (`nonleaguehq.com`). FotMob
  and Sofascore for per-match lineups, subs and cards.
- **Storylines / SEARCH-ONLY until read**: NewsNow's club-specific filter if one
  exists; The Non-League Football Paper (paywalled — a signal, not a CONFIRMED source,
  unless the article is actually accessible); BBC Sport's non-league coverage.
Checked and rejected, carried over unchanged: Non League Matters, The Non-League
Network, botw.org.uk.

A specific scoreline, scorer, or table position needs a per-game primary-source check,
not just a table widget's season summary — same rule as the rest of this repo. When an
aggregate figure and an individual match report disagree, trust the individual report.

## 4. Script
Write the script following STYLE.md's JT Debrief section exactly. There is no fixed
word-count target for this show — let the material set the length. A thorough data
file plus solid supplementary research will likely run shorter than the old
20-minute Morning Brief target, because this show has one job instead of several; say
so plainly in the episode rather than padding toward a number that was never this
show's target in the first place. Blank line between paragraphs — each blank line
becomes a spoken pause.

Always close with a genuine, correctly attributed, real quote if the research turned
up one that actually fits and hasn't been used before (check the archive) — never an
invented one, and never one forced in just to fill the slot; a plain sign-off is fine
if nothing fits.

## 5. Queue it
Commit with `github_put_file`:
- `bedford/pending/epNNN.txt` — the script
- `bedford/pending/epNNN.json` — `{"num": NNN, "date": "YYYY-MM-DD", "title": "...",
  "description": "two-sentence summary"}`

Update `bedford/archive/covered.md` in the same pass: append the episode's entry —
focus team, the data window it drew on, the key findings covered, and the closing
quote if one was used (see that file's own header for the exact format).

## 6. Build
Dispatch `build-bedford-episode.yml` on `master` (a push touching
`bedford/pending/**` usually starts it on its own — dispatch is the fallback). Same
duplicate-date guard, ASR content spot-check, and Git Data API publish pattern as
before — see the Architecture section above for what these do and why; mechanics are
unchanged from the old Morning Brief workflow, just namespaced the same way under
`bedford/`.

## 7. Verify
Same GitHub-API-first approach as the rest of this repo (this sandbox has no general
network egress and WebFetch is unreliable against this feed's binary/XML responses):
- `github_get` the latest `/deployments?environment=github-pages&per_page=1` entry and
  its `/statuses` — confirm `state` is `success` and the `sha` matches the publish
  commit.
- `github_get_file` on `bedford/episodes/episodes.json` (ref `master`) — confirm
  today's episode, byte size and duration are present.
- `github_get_file` on `bedford/archive/covered.md` (ref `master`) — confirm today's
  episode has a section.

## 8. Notify
Send Steve a short message: the episode title, a one-line summary, and confirmation
it's live. State plainly if anything failed.

No Notion logging for this show, same as before — revisit only if Steve asks.

## Process log
- 2026-10-03: Renamed from "JT Morning Brief" to "JT Debrief" and restructured from a
  daily team-news show into an event-triggered opposition-analytics show, at Steve's
  explicit direction. He supplied a Wyscout "Team Report" PDF on Chester FC (Bedford
  Town's National League North opponent, away, Saturday the tenth of October 2026) as
  the first focus-team data file, for Ep 2. Three explicit directions shaped this
  rewrite, given in his own words: (1) "not a daily routine only triggers when I
  upload" data — the show's scheduled task is disabled, not deleted (see the Trigger
  section above for why it couldn't be deleted outright); (2) "do extra research on
  team that we have focus on" — step 3 above is new, reusing this repo's existing
  sourcing tiers but pointed only at the opposition; (3) "dont worry about what
  Bedford can do - that the coaching staffs job" — explicitly out of scope. An earlier
  draft of this plan had recommended Bedford Town get its own Wyscout report too, to
  pair the opposition's weaknesses against Bedford's own strengths; Steve corrected
  that directly and it was dropped. The show's value, per Steve, is "break down these
  analytics in a clear and understandable fashion" — translation, not prescription.
- 2026-10-03: The League tiers section and named-source tiers above are carried over
  from the old Morning Brief runbook essentially unchanged, since this show still
  needs Bedford Town's league context and still uses the same stats backbone, just
  pointed at a single focus team instead of the whole division. The old show's
  day-to-day steps (team news, the day-before scan, the wider NLN picture) do not
  carry over — this show does not do that job — but the scoreline-verification
  discipline and the rejected-sources list do, since both are still true regardless of
  what the show covers.
- 2026-09-11: Show launched as "The Bedford Town Briefing", then renamed "JT Morning
  Brief" the same day at Steve's request — see the rename sweep this entry originally
  documented: this file's section header, STYLE.md's section header,
  `tools/generate_bedford_feed.py` (RSS `<title>` and `<itunes:author>`),
  `tools/make_bedford_cover.py` (cover art text), `build-bedford-episode.yml`'s MP3
  artist/album ID3 tags, and the scheduled task's own prompt text. The RSS guid prefix
  (`bedford-briefing-ep...`) was deliberately left unchanged then, and is unchanged
  again by the 2026-10-03 rename — it is a permanent per-episode identifier, not a
  display name. A full-repo grep for the old name caught two tool docstrings the
  original sweep missed (`tools/add_bedford_episode.py`, `tools/api_publish_bedford.py`)
  — worth repeating that grep after the 2026-10-03 rename rather than trusting the
  "files that matter" list alone twice in a row.
- 2026-09-11: Ep 1's research caught and fixed a wrong scoreline from a first-pass
  aggregator source — the fix is a process rule now (see step 2's cross-check
  requirement above), not a one-off correction.
- 2026-09-11: Ep 1 measured 211 words per minute against a script written for an
  assumed ~165 wpm (copied from Daily Build's own figure without checking it applied
  here), so the episode ran short against its then-20-minute target — partly thin
  news, partly this miscalibration. Moot now that this show has no fixed word-count
  target, but the underlying wpm figure (Kokoro bm_daniel, speed 1.05) may still be
  useful if word-per-minute pacing ever needs estimating again.
- 2026-09-18: Sourcing upgrade at Steve's request, while this was still "JT Morning
  Brief": the club's own X account became a named first-tier source, Pitchero's
  match-reports archive replaced the fixture list, Football Web Pages and NonLeagueHQ
  were added as the stats backbone, FotMob/Sofascore for lineups, NewsNow for a quick
  scan. Three candidate sources were checked and rejected (listed in step 3 above) so
  no future run re-adds them. That sourcing upgrade is what step 3 above still draws
  on, now re-pointed at a single focus team. Kept deliberately clear of Wyscout-style
  analytics then (xG, PPDA) as "the wrong kind of detail for a spoken briefing" — note
  that this show now does the opposite on purpose: Wyscout-style analytics are the
  entire point of JT Debrief. That is an intentional difference between what this show
  now is and what the old Morning Brief was, not an oversight to fix.

## Cost discipline
Runs on a budget model by design, same as the rest of this repo. One research pass is
usually enough given step 3's narrower scope — go wider only if the data file is thin
or supplementary research turns up little on the first pass. Never spend Higgsfield
credits on this show.
