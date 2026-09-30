# The Daily Build — with Dean Lynn — style guide (member edition)

Added 2026-09-30 (Dean's decision). The member edition goes to deanlynn.com members as
audio, text and email. It is written in Dean's own first-person voice and read by an
ElevenLabs clone of his voice, made with his consent. Every episode lands on
deanlynn.com as a DRAFT; Dean approves it before members see it.

Same morning research as the private edition (`research/YYYY-MM-DD.json`), second
script. The private edition's rules live in `STYLE.md`; its hard content rules and
TTS-safe rules apply here too and are restated below so this file stands alone.

## Who is speaking, who is listening
- Speaker: Dean Lynn, in the first person. A repeat tech founder who has been building
  and running ventures since 2005, AI-first, builds on Base44, based in Stamford,
  Lincolnshire. Lead with that register, not with a list of company names.
- Listener: a deanlynn.com member. Founders, operators and small-business owners,
  mostly UK, who want to know what changed in AI this week and what to do about it.
  Assume they're smart and busy, not technical.
- "You" = the member. "I" = Dean. Never "we at [company]".

## The private/public line (hard rule, enforced)
Nothing from the private estate edition goes in here:
- No venture names from Dean's estate, no clients, no installers, no Steve, no
  "your three businesses", no private sector niches (prize draws, fundraising
  regulation, EV charging, grassroots sport). The build idea is generic, never niched
  to one of Dean's ventures.
- Only use research items where `"private": false`. Sector items (agent C) are always
  private.
- `members/denylist.txt` is checked against the script AND every string in the JSON
  before any audio is made; one match fails the build. Run
  `python3 tools/denylist_check.py members/pending/epNNN.txt members/pending/epNNN.json`
  before committing.
- Dean's own story is fine at the level his public site tells it ("I've been building
  businesses since two thousand and five"). No funding, legal, family or company
  finances, ever.

## Voice and tone (seeded from Dean's own writing rules)
- Direct, founder-led, human, slightly punchy. Never corporate-bland, never
  buzzword-heavy, never "icky". No hype.
- UK English spelling and idiom throughout.
- Numbers over adjectives. "Two dollars in, ten out" beats "competitively priced".
- Grounded claims. Unverified figures get cautious wording and a named source, or they
  don't go in. Separate what's current from what's history.
- Practical: every story ends with what a member should actually do or watch.
- Short sentences, varied rhythm. One dry line beats three jokes.
- Confidence flags spoken naturally and varied ("I read the announcement myself",
  "I've only seen this secondhand"). Illustrations of the pattern, not lines to reuse.
- Never say "great question", "absolutely", "let's dive in", "game-changer",
  "in today's fast-paced world".
- Vocabulary variety: before finishing, scan for any word or phrase used more than two
  or three times and swap or cut it (same discipline as `STYLE.md`).

## Structure (~1,600-2,200 words, ~8-12 minutes)
Pace: the private edition measures ~190 wpm on Kokoro. The clone's pace is not yet
measured — after the first three episodes, compare word count with the rendered
`seconds` in `members/published/epNNN.render.json` and correct this line.

Mark sections in the script with marker lines (never spoken, never published):
`[[CHAPTER: <title>]]` before the first paragraph of each chapter, and
`[[STORY: <id>]]` before the first paragraph of each story (ids match `stories[].id`
in the JSON). The render uses these for exact chapter and story start times.

1. **Disclosure** — the first paragraph, word for word:
   "Quick note before we start: this update is researched and drafted with AI help, in
   my words, and read by an AI clone of my own voice, made with my consent."
   (The renderer inserts it if missing and swaps it for the stand-in version on a
   Kokoro fallback. Don't paraphrase it.)
2. **Cold open** (~80-120 words): two or three sentences on the day's best stories,
   then "This is The Daily Build, for <spoken date>. I'm Dean Lynn." and a one-line
   "research and opinion, not financial advice".
3. **The news** — 4-6 stories (~150-220 words each): what happened, dated, sourced by
   name, then "What this means" in Dean's voice for a small business.
4. **Quick ones** — two or three one-to-two-sentence items.
5. **The build** (~350-450 words): one generic build idea. Why now, five or so steps,
   then guardrails spelled out as "it may…" and "it may not…". Evidence-first when
   agent B found published revenue (named source, attributed figure); if there's no
   revenue evidence, say so plainly rather than imply it.
6. **Runners-up** — two or three ideas, a sentence or two each, with their caveats.
7. **One action** (~80-120 words): one thing, thirty minutes or less, no code.
8. **Recap** — "Sixty seconds, five things", numbered.
9. **Outro** — one or two lines, pointing members to the discussion thread under the
   episode on dean lynn dot com. Vary the wording day to day.

## Hard content rules (same as STYLE.md)
- Every news claim dated 2026 with a source the research pass actually read. Nothing
  from training data dressed up as news. Discard rumours.
- Never invent a number, name, quote, URL or source. Revenue figures only as published
  and attributed.
- No callbacks to private-edition episodes ("on Monday we covered…"): members didn't
  hear them. Refer to earlier member episodes only once the member archive exists.
- No URLs read aloud; attribute sources by name. URLs go in the JSON `sources`.
- Never chase or resurface past build ideas unless Dean raises them.

## TTS-safe writing (the clone reads this aloud verbatim)
- Numbers and prices in words ("two dollars per million input tokens", "ninety-five
  per cent", "four hundred and fifty pounds").
- Dates spoken ("Wednesday the thirtieth of September").
- No parentheses, bullets, markdown or symbols in the script. Paragraph breaks =
  natural pauses.
- Write names as normal; `members/pronunciations.md` handles how the voice says them
  (Base44, Claude, Anthropic, OpenAI, GPT, API…). Add a row there when a new name comes
  out wrong, rather than misspelling it in the script.

## The JSON (members/pending/epNNN.json)
Fields the ingest expects (see `tools/ingest_post.py` for the single source of truth):
`num, date, title, description, slug, dek, cold_open, chapters[{title}],
stories[{id, tag, headline, short, facts[], what_it_means, confidence, sources[{name,
url}]}], quick_ones[{headline, url}], build{title, why_now, steps[], may[], may_not[]},
vault_extras{build_pack_md, prompts[{title, body}]}, poll{question, options[]},
newsletter_summary`. The workflow fills `start_s` and `narration`.
`members/pending/ep053.example.json` shows the shape.
