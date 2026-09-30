# Member edition pronunciations

Read by `tools/member_edition.py` (`load_pronunciations`). Every row is applied as a
plain text alias to the spoken copy of the script before rendering, for BOTH engines
(the ElevenLabs clone and the Kokoro fallback), so the two say names the same way.
The published transcript keeps the original spelling.

Mirror these rows into the ElevenLabs pronunciation dictionary as **alias** rules
(`ELEVENLABS_PRON_DICT_ID` / `ELEVENLABS_PRON_DICT_VERSION`). Alias rules work with
`eleven_multilingual_v2`; phoneme rules do not, so don't add IPA here.

Matching is case-sensitive and whole-token (`GPT` is replaced, `ChatGPT` is left
alone). Rows whose "Spoken as" says ASK DEAN are skipped until Dean decides.

| Written | Spoken as | Notes |
|---|---|---|
| Base44 | Base forty-four | |
| Claude | Clawd | |
| Anthropic | Ann-throppick | |
| Stamford | Stam-ford | |
| Lincolnshire | Lincoln-sher | |
| deanlynn.com | dean lynn dot com | |
| Higgsfield | Higgs field | |
| OpenAI | Open A I | |
| GPT | G P T | |
| LLM | L L M | |
| API | A P I | |
| Onyxia | ASK DEAN | not applied until Dean confirms how he says it |

Verified against the first clone render: not yet (update this line with the date and
any fixes after Dean listens to the first episode).
