"""Deck-level lint: warn when a deck leans on one or two presentation patterns."""
from __future__ import annotations

from collections import Counter

from .markdown import Doc

RUN_LIMIT = 3          # same pattern on more than this many consecutive content slides → warn
SHARE_LIMIT = 0.45     # one pattern on more than this share of content slides → warn
MIN_SLIDES = 6         # share check only applies to decks with at least this many content slides


def slide_pattern(blocks) -> str:
    """The dominant visual pattern of one content slide."""
    kinds = [b.kind for b in blocks]
    for b in blocks:
        if b.kind == "component":
            return b.data["type"]
    if "image" in kinds:
        return "image"
    if "table" in kinds:
        return "table"
    if "code" in kinds:
        return "code"
    if "bullets" in kinds:
        return "bullets"
    if "quote" in kinds or "callout" in kinds:
        return "quote"
    return "text"


def content_slides(doc: Doc):
    for sec in doc.sections:
        yield from sec.slides
        for sub in sec.subsections:
            if sub.blocks:
                yield sub
            yield from sub.slides


def variety(doc: Doc) -> list[str]:
    seq = [(sl.title, slide_pattern(sl.blocks)) for sl in content_slides(doc) if sl.blocks]
    warnings = []
    run_start = 0
    for i in range(1, len(seq) + 1):
        if i == len(seq) or seq[i][1] != seq[run_start][1]:
            n = i - run_start
            if n > RUN_LIMIT:
                warnings.append(f"monotony: {n} consecutive slides use `{seq[run_start][1]}` "
                                f"(from \"{seq[run_start][0]}\") — vary the presentation")
            run_start = i
    if len(seq) >= MIN_SLIDES:
        top, n = Counter(p for _, p in seq).most_common(1)[0]
        if n / len(seq) > SHARE_LIMIT:
            warnings.append(f"monotony: `{top}` on {n}/{len(seq)} content slides — "
                            "rotate other components (see deckframes-infographics)")
    return warnings
