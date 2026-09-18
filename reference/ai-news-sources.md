# AI news sources — checklist for research agent A

Added 2026-09-18 (Steve's request — see RUNBOOK.md Process log) to replace "check
official changelogs first" with an actual list. The failure mode this fixes: Base44
went unmentioned on the show for five weeks despite a similar instruction already
existing, because there was no concrete list to check against — it relied on the
research agent's own search recall each run. Read this file, hit each URL directly,
and only fall back to open web search for stories these sources don't cover
themselves (e.g. secondhand financial-press reporting, industry commentary).

Check ALL of these every research pass, not just the ones that come to mind — that's
the whole point of the list. Rotate the order you check them in from one episode to
the next (see RUNBOOK.md's phrasing-variety instruction) so the show doesn't develop a
habit of checking the same two or three first and treating the rest as an afterthought.

## Frontier labs
- Anthropic news/blog: https://www.anthropic.com/news
- Anthropic research page (longer research posts, distinct from the news blog):
  https://www.anthropic.com/research
- Claude Code changelog: https://code.claude.com/docs/en/changelog
- Claude Platform (API) release notes: https://platform.claude.com/docs/en/release-notes/overview
- OpenAI news/blog: https://openai.com/news/
- Google DeepMind blog: https://deepmind.google/discover/blog/
- Google's Gemini API changelog: https://ai.google.dev/gemini-api/docs/changelog
- Google Workspace Updates blog (Gemini-in-Workspace features specifically):
  https://workspaceupdates.googleblog.com/
- xAI news: https://x.ai/news
- Meta AI blog: https://ai.meta.com/blog/
- Mistral AI news: https://mistral.ai/news
- Hugging Face blog (never checked before 2026-09-18 — add to rotation):
  https://huggingface.co/blog

## Agent tooling / coding assistants
- GitHub changelog: https://github.blog/changelog/
- GitHub blog (product announcements, distinct from the changelog):
  https://github.blog/
- Cursor changelog: https://cursor.com/changelog
- Replit changelog/blog: https://blog.replit.com/
- Perplexity blog (covers Comet/Portable Computer agent work, not just search):
  https://www.perplexity.ai/hub/blog
- Microsoft Copilot / AI blog: https://blogs.microsoft.com/ai/

## No-code builders (check by name every pass, per the 2026-09-16 correction)
- Lovable changelog: https://docs.lovable.dev/changelog
- Base44 changelog: https://docs.base44.com/changelog/product

## Voice AI
- ElevenLabs changelog: https://elevenlabs.io/docs/changelog

## Notes
- These URLs were verified live on 2026-09-18. Sites restructure without warning —
  if one 404s or redirects somewhere unexpected, note it in the episode's research
  write-up so this file gets fixed rather than silently working around a dead link
  forever.
- This list is not exhaustive by design — it's the baseline that must never be
  skipped, not a ceiling on what agent A can check. Genuinely new, relevant sources
  can and should be added here as they come up (the way Base44 and Hugging Face just
  were), same as `reference/fundraising-regulator-notes.md` gets updated when the
  Fundraising Regulator's own site changes.
