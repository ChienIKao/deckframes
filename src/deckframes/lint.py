"""Deck-level lint: presentation variety, defensive disclaimers, invented subtitles, missing speaker notes."""
from __future__ import annotations

import re
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


# Defensive disclaimers and hedges: phrases that soften or excuse the point instead of stating it.
# Front matter `hedges: allow` turns the warning off for decks that keep the user's own caveats.
HEDGES = re.compile("|".join([
    r"僅供參考", r"仅供参考", r"供參考", r"供参考", r"僅為示意", r"仅为示意", r"以實際為準", r"以实际为准",
    r"視情況而定", r"视情况而定", r"因人而異", r"因人而异", r"因情況而異", r"因情况而异",
    r"有待進一步", r"有待进一步", r"仍需進一步", r"仍需进一步", r"需要進一步", r"需要进一步", r"仍有待",
    r"尚待(驗證|研究|確認|观察|觀察|验证|确认)", r"值得注意的是", r"需要注意的是", r"必須指出", r"必须指出",
    r"一定程度上", r"某種程度上", r"某种程度上", r"並非(完整|全部|絕對|唯一)", r"并非(完整|全部|绝对|唯一)",
    r"不構成.{0,6}建議", r"不构成.{0,6}建议", r"不保證", r"不保证", r"結果可能(因|會)", r"结果可能(因|会)",
    r"初步(結果|结果|觀察|观察)", r"免責", r"免责",
    r"for reference only", r"results may vary", r"may vary depending", r"depending on the situation",
    r"further (research|study|studies|investigation|work|validation) (is|are|will be) (needed|required)",
    r"(it )?should be noted", r"(it is|it's) worth noting", r"not (an )?exhaustive", r"not a complete list",
    r"subject to change", r"to some extent", r"does not constitute", r"no guarantee", r"illustrative only",
    r"should not be (taken|construed) as", r"preliminary (results|findings)", r"disclaimer",
]), re.I)


def _texts(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _texts(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _texts(v)


def _containers(doc: Doc):
    """(label, container) for the cover, every chapter, section and slide."""
    yield "cover", doc.cover
    for sec in doc.sections:
        if sec.title:
            yield f"chapter \"{sec.title}\"", sec
        for sl in sec.slides:
            yield f"\"{sl.title}\"", sl
        for sub in sec.subsections:
            yield f"\"{sub.title}\"", sub
            for sl in sub.slides:
                yield f"\"{sl.title}\"", sl


def hedges(doc: Doc) -> list[str]:
    if str(doc.meta.get("hedges", "")).lower() in ("allow", "true", "yes"):
        return []
    warnings, seen = [], set()
    for label, c in _containers(doc):
        texts = [c.title, c.subtitle, *_texts([b.data for b in c.blocks]), *c.notes]
        if c is doc.cover:
            texts += [str(doc.meta.get(k, "")) for k in ("subtitle", "eyebrow")]
        for t in texts:
            for m in HEDGES.finditer(t or ""):
                key = (label, m.group(0).lower())
                if key not in seen:
                    seen.add(key)
                    warnings.append(f"hedge: \"{m.group(0)}\" on {label} — cut the disclaimer and state the point")
    return warnings


def subtitles(doc: Doc, source: str | None) -> list[str]:
    """Slide and cover subtitles that are not in the user's script. Chapter subtitles (English names)
    are exempt; without a source script nothing is checked."""
    if source is None:
        return []
    flat = re.sub(r"\s+", "", source)
    found = [("cover", doc.cover.subtitle or str(doc.meta.get("subtitle", "")))]
    found += [(label, c.subtitle) for label, c in _containers(doc) if not label.startswith(("cover", "chapter"))]
    return [f"subtitle: \"{s}\" on {label} is not in the script — drop it unless the user asked for it"
            for label, s in found if s and re.sub(r"\s+", "", s) not in flat]


def missing_notes(doc: Doc) -> list[str]:
    """The cover and every chapter divider need speaker notes, so the presenter is never left blank."""
    warnings = []
    if (doc.cover.title or doc.meta.get("title")) and not doc.cover.notes:
        warnings.append("notes: the cover has no speaker notes — add an opening line under `# Title`")
    for sec in doc.sections:
        if sec.title and not sec.notes:
            warnings.append(f"notes: chapter divider \"{sec.title}\" has no speaker notes — "
                            "add a transition line under its `##` heading")
    return warnings
