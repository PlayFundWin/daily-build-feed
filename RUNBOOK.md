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
  MCP tools (`github_put_file`), dispatch the build workflow, verify, notify.
- **GitHub Actions does**: TTS render, MP3 encode, feed regeneration, committing the
  audio. Runners have full network and write access.

CRITICAL: commits made through the API do NOT fire `push` workflow triggers. After
committing the pending files you MUST explicitly dispatch the workflow
(`github_dispatch_workflow` with workflow `build-episode.yml`, ref `master`) or nothing
will build.

## 1. Read the archive
Read `archive/covered.md` (raw URL:
https://raw.githubusercontent.com/PlayFundWin/daily-build-feed/master/archive/covered.md).
Note every item and idea already covered and any open threads marked FOLLOW-UP. Never
re-cover an item as new; follow-ups must reference the earlier episode by day.
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
  five hundred pounds to start. Plus 3 runner-ups. Never invent numbers.
- C: Sector news for the listener's ventures: UK fundraising/prize-draw tech and
  regulation; grassroots sports tech; UK EV destination charging.

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

## 5. Build
Dispatch `build-episode.yml` on `master`. The workflow renders with Kokoro (voice
`bm_daniel`, speed 1.05), encodes a 96k MP3, registers the episode, prunes to the newest
30, regenerates `feed.xml`, deletes the pending files and pushes. Typical run: 10-20
minutes including the model download (cached between runs).

Poll the run until it completes. On failure, read the job logs, fix, and re-dispatch —
do not leave a half-published state (pending files present but no MP3).

## 6. Verify
- `https://playfundwin.github.io/daily-build-feed/feed.xml` returns 200 and contains
  today's `<item>`.
- `https://playfundwin.github.io/daily-build-feed/episodes/epNNN.mp3` returns 200 with a
  Content-Length matching the feed's `length` attribute.
Pages deploys take a couple of minutes after the push — retry before declaring failure.

## 7. Notify
`SendUserFile` is not available for the MP3 in this flow (the audio only exists on the
runner), so send Steve a short message: the episode title, a one-line summary, and the
fact that it is live in the feed. If ANY step failed, say plainly what failed and what
you did about it. Never claim success you did not verify.

## Cost discipline
Runs on a budget model by design. Three research subagents maximum plus at most one
verification pass. Keep subagent prompts tight. Never spend Higgsfield credits on the
daily episode.
