#!/usr/bin/env python3
"""Shared helpers for the member edition ("The Daily Build — with Dean Lynn").

Imported by tools/render_elevenlabs.py, tools/denylist_check.py and
tools/ingest_post.py. Keep the spoken disclosure wording here and nowhere else
so the render, the transcript and the checks can never drift apart.

Script format (members/pending/epNNN.txt):
  - Plain text, blank line between paragraphs (each blank line = a spoken pause).
  - Marker lines, each on a line of its own, never spoken or published:
        [[CHAPTER: Cold open]]
        [[STORY: s1]]
    A CHAPTER marker starts a chapter (its title is what members see in the
    player). A STORY marker ties the next paragraph to stories[].id in the
    JSON so the player can jump to it. Markers force an audio chunk boundary,
    so their start times are exact, not estimated.
  - The first paragraph must be DISCLOSURE, word for word. If it is missing,
    the renderer inserts it (and warns) rather than publish without it.
"""
import re

DISCLOSURE = (
    "Quick note before we start: this update is researched and drafted with AI "
    "help, in my words, and read by an AI clone of my own voice, made with my consent."
)

# Spoken when the clone is unavailable and Kokoro stands in. The clone clause of
# DISCLOSURE would be untrue in that case, so the opening becomes the first
# sentence of DISCLOSURE (still true) followed by the fallback line.
FALLBACK_LINE = "Today's update is read by an AI stand-in voice, not my clone. Normal service tomorrow."
DISCLOSURE_CORE = (
    "Quick note before we start: this update is researched and drafted with AI help, "
    "in my words."
)
FALLBACK_OPENING = DISCLOSURE_CORE + " " + FALLBACK_LINE
# Text-only (both audio engines failed): nothing is read aloud, so only the
# first clause of the disclosure applies.
TEXT_ONLY_OPENING = DISCLOSURE_CORE
OPENINGS = {"clone": DISCLOSURE, "fallback": FALLBACK_OPENING, "text": TEXT_ONLY_OPENING}

ID3_COMMENT_CLONE = "AI-narrated in Dean's cloned voice"
ID3_COMMENT_FALLBACK = "AI-narrated in a stand-in voice (Kokoro), not Dean's clone"

NARRATION_CLONE = "elevenlabs_clone"
NARRATION_FALLBACK = "kokoro_fallback"
NARRATION_TEXT_ONLY = "text_only"

MARKER_RE = re.compile(r"^\s*\[\[\s*(CHAPTER|STORY)\s*:\s*(.+?)\s*\]\]\s*$", re.IGNORECASE)
TARGET_WORDS = (1600, 2200)


def _norm(s):
    return re.sub(r"\s+", " ", s).strip()


def parse_script(text):
    """Return a list of blocks: {"text": str, "chapter": str|None, "story": str|None}.

    chapter/story are set on the first paragraph after the marker.
    """
    blocks = []
    pending_chapter = None
    pending_story = None
    para_lines = []

    def flush():
        nonlocal pending_chapter, pending_story, para_lines
        para = _norm(" ".join(para_lines))
        para_lines = []
        if not para:
            return
        blocks.append({"text": para, "chapter": pending_chapter, "story": pending_story})
        pending_chapter = None
        pending_story = None

    for line in text.splitlines():
        m = MARKER_RE.match(line)
        if m:
            flush()
            kind, value = m.group(1).upper(), m.group(2)
            if kind == "CHAPTER":
                pending_chapter = value
            else:
                pending_story = value
            continue
        if not line.strip():
            flush()
            continue
        para_lines.append(line.strip())
    flush()
    return blocks


def ensure_disclosure(blocks, mode="clone"):
    """Make the first block the right disclosure for how this edition is narrated.

    mode: "clone" (ElevenLabs), "fallback" (Kokoro stand-in) or "text" (no audio).
    Returns (blocks, inserted: bool) - inserted means the script lacked it.
    """
    opening = OPENINGS[mode]
    inserted = False
    if blocks and _norm(blocks[0]["text"]) == _norm(DISCLOSURE):
        first = dict(blocks[0])
        first["text"] = opening
        blocks = [first] + blocks[1:]
    else:
        inserted = True
        chapter = None
        if blocks and blocks[0]["chapter"]:
            # keep the first chapter marker attached to the very start
            chapter = blocks[0]["chapter"]
            blocks = [dict(blocks[0], chapter=None)] + blocks[1:]
        blocks = [{"text": opening, "chapter": chapter, "story": None}] + blocks
    return blocks, inserted


def blocks_to_text(blocks):
    return "\n\n".join(b["text"] for b in blocks) + "\n"


def published_transcript(text, mode="clone"):
    """The member-facing transcript: markers stripped, correct disclosure first."""
    blocks, _ = ensure_disclosure(parse_script(text), mode=mode)
    return blocks_to_text(blocks)


def word_count(text):
    return len(re.findall(r"\b\w+\b", text))


def load_pronunciations(path):
    """Parse members/pronunciations.md: markdown table rows `| Term | Spoken as |`.

    Rows whose alias is empty or says ASK DEAN are skipped (not yet decided).
    Returns a list of (term, alias), longest term first so "OpenAI" wins over
    anything shorter it contains.
    """
    pairs = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line.startswith("|"):
                    continue
                cells = [c.strip() for c in line.strip("|").split("|")]
                if len(cells) < 2:
                    continue
                term, alias = cells[0].strip("` "), cells[1].strip("` ")
                if not term or term.lower() in ("term", "written") or set(term) <= set("-: "):
                    continue
                if not alias or "ASK DEAN" in alias.upper():
                    continue
                pairs.append((term, alias))
    except FileNotFoundError:
        return []
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


def apply_pronunciations(text, pairs):
    """Client-side alias replacement, so the Kokoro fallback says things the
    same way as the clone. Case-sensitive, whole-token matches only."""
    for term, alias in pairs:
        pattern = r"(?<![\w.])" + re.escape(term) + r"(?![\w])"
        text = re.sub(pattern, alias, text)
    return text
