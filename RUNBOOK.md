# The Daily Build — daily production runbook

Produce today's episode end-to-end. Target: published by 07:00 UK time. Work
unattended: make reasonable choices, never block on questions.

Repo: `PlayFundWin/daily-build-feed` (GitHub Pages serves it at
https://playfundwin.github.io/daily-build-feed/). All publishing is a push to master.

## 0. Setup (~3 min)
```
pip install kokoro-onnx soundfile --break-system-packages -q
curl -sL --retry 3 -O https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
curl -sL --retry 3 -O https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
git clone https://x-access-token:${GITHUB_TOKEN}@github.com/PlayFundWin/daily-build-feed.git
```
If git push is denied by the proxy, fall back to the GitHub MCP tools
(github_get_file / github_put_file) for text files; if the MP3 cannot be uploaded at
all, still deliver it into the session with SendUserFile and say plainly that the feed
was not updated. ffmpeg is preinstalled. Verify both model files downloaded
(kokoro-v1.0.onnx ≈ 310 MB).

## 1. Read the archive
Read `archive/covered.md` in the repo. Note every item and idea already covered, and
any open threads marked FOLLOW-UP. Never re-cover an item as new; follow-ups must
reference the earlier episode.

## 2. Research (3 parallel subagents, ~5 min)
Launch three general-purpose agents (they inherit the session model):
- A: AI releases/features from the last 48h (Anthropic/Claude, OpenAI, Google, agent
  tooling, voice AI, no-code builders). Official changelogs first. Each item: what,
  exact date, source URL, small-business angle, CONFIRMED (page read) vs SEARCH-ONLY.
- B: Small AI-buildable business ideas with recent published revenue evidence (Indie
  Hackers, Hacker News, Starter Story, Product Hunt, subreddits). Pick ONE deep-dive
  idea meeting: real named evidence, ~90% Claude-buildable in days, sellable in the UK,
  under five hundred pounds to start. Plus 3 runner-ups. Never invent numbers.
- C: Sector news for the listener's ventures: UK fundraising/prize-draw tech +
  regulation; grassroots sports tech; UK EV destination charging.
Pass each agent the day's date and the relevant archive items so they skip covered ground.

## 3. Script
Write `episode_NNN_script.txt` (~3,300 words) following `STYLE.md` exactly. NNN = next
episode number from `episodes/episodes.json`.

## 4. Render + encode (~15 min)
```
python3 tools/render_episode.py episode_NNN_script.txt epNNN.wav bm_daniel 1.05
ffmpeg -y -i epNNN.wav -codec:a libmp3lame -b:a 96k -ar 44100 \
  -metadata title="The Daily Build — Episode NNN — <date>" \
  -metadata artist="The Daily Build" episodes/epNNN.mp3
```
Sanity-check with ffprobe: duration 15–24 min, then volumedetect (mean ≈ -18 to -22 dB,
no silence >4s via silencedetect).

## 5. Publish
1. Copy the MP3 into the repo `episodes/`, add an entry to `episodes/episodes.json`
   (num, date, title, description = 2-sentence episode summary, file, bytes, seconds).
2. `python3 tools/generate_feed.py` from repo root.
3. Append to `archive/covered.md`: episode number/date/title, every news item covered
   (one line each), the build idea, and any FOLLOW-UP threads opened.
4. Commit and push to master. Keep only the newest 30 MP3s in `episodes/` (delete older
   ones from git AND remove their episodes.json entries feed-side; leave the archive
   log intact).
5. Verify after ~2 min: `https://playfundwin.github.io/daily-build-feed/feed.xml`
   returns 200 and contains today's item; the new MP3 URL returns 200 with the right
   Content-Length. GitHub Pages builds can take a few minutes — retry before declaring failure.

## 6. Notify
Send the MP3 into the session with SendUserFile (status: proactive) with a 1-line
summary of the episode, and mention it is also live in the podcast feed. If anything
failed (research thin, render failed, push rejected), say plainly what failed and what
you did instead — never pretend success.

## Cost discipline
This runs on a budget model by design. Keep subagent prompts tight, don't spawn more
than the three research agents plus (optionally) one verification pass, and never use
Higgsfield credits for the daily episode.
