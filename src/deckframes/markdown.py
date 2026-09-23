"""Markdown → deck tree (chapters › subsections › slides) and inline-run parsing."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# --------------------------------------------------------------------------- model


@dataclass
class Block:
    kind: str  # bullets | para | sub | quote | image | table | code
    data: object


@dataclass
class Container:
    title: str = ""
    subtitle: str = ""
    blocks: list = field(default_factory=list)
    notes: list = field(default_factory=list)


@dataclass
class Subsection(Container):
    slides: list = field(default_factory=list)


@dataclass
class Section(Container):
    slides: list = field(default_factory=list)        # slides before the first subsection
    subsections: list = field(default_factory=list)


@dataclass
class Doc:
    meta: dict
    cover: Container
    sections: list


@dataclass
class SlideSpec:
    role: str  # cover | agenda | section | content | closing
    title: str = ""
    subtitle: str = ""
    blocks: list = field(default_factory=list)
    notes: list = field(default_factory=list)
    label: str = ""


# --------------------------------------------------------------------------- markdown

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
IMAGE_LINE = re.compile(r'^!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+"[^"]*")?\s*\)$')
FENCE = re.compile(r"^(`{3,}|~{3,})\s*([\w+-]*)\s*(.*)$")
HR = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
ALERT = re.compile(r"^\[!(\w+)\]\s*(.*)$")
SOURCE = re.compile(r"^(資料來源|来源|來源|參考資料|Sources?|Ref(?:erences?)?)\s*[:：]", re.I)
COMPONENT_TYPES = {"cards", "steps", "timeline", "flow", "stats", "compare", "chart"}
ATTR = re.compile(r"^(tag|img|icon|color)\s*[:：]\s*(.+)$", re.I)


def is_cjk(ch: str) -> bool:
    return unicodedata.east_asian_width(ch) in ("W", "F")


def join_lines(a: str, b: str) -> str:
    if not a:
        return b
    if a and b and (is_cjk(a[-1]) or is_cjk(b[0])):
        return a + b
    return a + " " + b


def split_frontmatter(text: str):
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line and not line.lstrip().startswith("#"):
                    k, v = line.split(":", 1)
                    v = v.strip().strip('"').strip("'")
                    if v.lower() in ("true", "false"):
                        v = v.lower() == "true"
                    meta[k.strip()] = v
            text = text[end + 4:]
    return meta, text


def split_row(line: str):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def split_heading(text: str):
    """`標題 | Subtitle` → (標題, Subtitle)"""
    if " | " in text:
        a, b = text.split(" | ", 1)
        return a.strip(), b.strip()
    return text.strip(), ""


def make_item(text: str):
    pos, attrs = [], {}
    for part in re.split(r"\s\|\s", text):
        part = part.strip()
        m = ATTR.match(part)
        if m:
            attrs[m.group(1).lower()] = m.group(2).strip()
        elif part:
            pos.append(part)
    return {"title": pos[0] if pos else "", "desc": pos[1] if len(pos) > 1 else "",
            "extra": pos[2:], "attrs": attrs, "children": []}


def parse_component(kind: str, info: str, body: str):
    items, free = [], []
    for line in body.split("\n"):
        m = LIST_ITEM.match(line.replace("\t", "    "))
        if m and (not m.group(1) or not items):
            items.append(make_item(m.group(3)))
        elif m:
            items[-1]["children"].append(m.group(3).strip())
        elif line.strip() and items and line.startswith((" ", "\t")):
            items[-1]["children"].append(line.strip())
        elif line.strip():
            free.append(line.strip())
    if kind == "flow" and not items:
        for ln in free:
            if "->" in ln or "→" in ln:
                items += [make_item(x) for x in re.split(r"\s*(?:->|→)\s*", ln) if x.strip()]
    rows = [split_row(l) for l in free if l.startswith("|") and not TABLE_SEP.match(l)]
    return {"type": kind, "args": info.split(), "items": items, "lines": free, "rows": rows}


def parse_markdown(text: str) -> Doc:
    meta, body = split_frontmatter(text.replace("\r\n", "\n"))
    sec_lv = int(meta.get("section_level", 2))
    sub_lv = int(meta.get("subsection_level", 3))
    sl_lv = int(meta.get("slide_level", 4))
    doc = Doc(meta=meta, cover=Container(title=meta.get("title", "")), sections=[])
    cur: Container = doc.cover
    cur_section: Section | None = None
    cur_sub: Subsection | None = None
    title_seen = bool(meta.get("title"))

    para: list[str] = []
    bullets: list | None = None
    indents: list[int] = []

    def flush():
        nonlocal para, bullets, indents
        if para:
            text_ = ""
            for ln in para:
                text_ = join_lines(text_, ln.strip())
            cur.blocks.append(Block("source" if SOURCE.match(text_) else "para", text_))
            para = []
        if bullets:
            cur.blocks.append(Block("bullets", bullets))
        bullets, indents = None, []

    def ensure_section():
        nonlocal cur_section
        if cur_section is None:
            cur_section = Section(title="")
            doc.sections.append(cur_section)
        return cur_section

    lines = body.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # speaker notes: <!-- ... -->
        if stripped.startswith("<!--"):
            flush()
            chunk = [stripped[4:]]
            while "-->" not in chunk[-1] and i + 1 < len(lines):
                i += 1
                chunk.append(lines[i])
            note = "\n".join(chunk).split("-->")[0].strip()
            note = re.sub(r"^(notes?|備註|讲稿|講稿)\s*[:：]\s*", "", note, flags=re.I)
            if note:
                cur.notes.append(note)
            i += 1
            continue

        fm = FENCE.match(stripped)
        if fm:
            flush()
            fence, lang, info = fm.group(1), fm.group(2), fm.group(3)
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(fence):
                code.append(lines[i])
                i += 1
            if lang.lower() in COMPONENT_TYPES:
                cur.blocks.append(Block("component", parse_component(lang.lower(), info, "\n".join(code))))
            else:
                cur.blocks.append(Block("code", {"lang": lang, "text": "\n".join(code)}))
            i += 1
            continue

        hm = HEADING.match(line)
        if hm:
            flush()
            lvl = len(hm.group(1))
            title, subtitle = split_heading(hm.group(2))
            if lvl == 1 and not title_seen:
                doc.cover.title, doc.cover.subtitle = title, subtitle
                cur = doc.cover
                title_seen = True
            elif sec_lv and lvl <= sec_lv:
                cur_section = Section(title=title, subtitle=subtitle)
                doc.sections.append(cur_section)
                cur, cur_sub = cur_section, None
            elif sub_lv and lvl == sub_lv:
                ensure_section()
                cur_sub = Subsection(title=title, subtitle=subtitle)
                cur_section.subsections.append(cur_sub)
                cur = cur_sub
            elif lvl <= sl_lv:
                ensure_section()
                cur = Container(title=title, subtitle=subtitle)
                (cur_sub.slides if cur_sub else cur_section.slides).append(cur)
            else:
                cur.blocks.append(Block("sub", hm.group(2).strip()))
            i += 1
            continue

        if HR.match(line):
            flush()
            owner = cur_sub.slides if cur_sub else (cur_section.slides if cur_section else None)
            if owner is not None and (cur in owner or cur is cur_sub):
                cur = Container(title=cur.title, subtitle=cur.subtitle)
                owner.append(cur)
            i += 1
            continue

        im = IMAGE_LINE.match(stripped)
        if im:
            flush()
            cur.blocks.append(Block("image", {"alt": im.group(1), "path": im.group(2)}))
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and TABLE_SEP.match(lines[i + 1]):
            flush()
            header = split_row(lines[i])
            aligns = []
            for c in split_row(lines[i + 1]):
                aligns.append("r" if c.endswith(":") and not c.startswith(":")
                              else "c" if c.startswith(":") and c.endswith(":") else "l")
            rows = [header]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            cur.blocks.append(Block("table", {"rows": rows, "aligns": aligns}))
            continue

        if stripped.startswith(">"):
            flush()
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(lines[i].strip()[1:].strip())
                i += 1
            am = ALERT.match(q[0]) if q else None
            if am:
                q[0] = am.group(2)
            text_ = ""
            for ln in q:
                text_ = join_lines(text_, ln)
            if am:
                cur.blocks.append(Block("callout", {"kind": am.group(1).lower(), "text": text_}))
            else:
                cur.blocks.append(Block("quote", text_))
            continue

        lm = LIST_ITEM.match(line.replace("\t", "    "))
        if lm:
            if para:
                flush()
            indent = len(lm.group(1))
            if bullets is None:
                bullets, indents = [], []
            while indents and indent < indents[-1]:
                indents.pop()
            if not indents or indent > indents[-1]:
                indents.append(indent)
            level = min(len(indents) - 1, 4)
            ordered = lm.group(2)[0].isdigit()
            bullets.append({"level": level, "text": lm.group(3).strip(), "ordered": ordered})
            i += 1
            continue

        if not stripped:
            if para:
                flush()
            i += 1
            continue

        # continuation line of a list item, or plain paragraph text
        if bullets and line.startswith((" ", "\t")):
            bullets[-1]["text"] = join_lines(bullets[-1]["text"], stripped)
        else:
            if bullets:
                flush()
            para.append(stripped)
        i += 1

    flush()
    return doc


# --------------------------------------------------------------------------- inline

INLINE = re.compile(
    r"==(?P<hl>.+?)==|\*\*(?P<b>.+?)\*\*|__(?P<b2>.+?)__|`(?P<code>[^`]+)`|\[(?P<lt>[^\]]+)\]\((?P<lu>[^)]+)\)"
    r"|(?<![\w*])\*(?!\s)(?P<i>.+?)(?<!\s)\*(?!\*)|(?<!\w)_(?!\s)(?P<i2>.+?)(?<!\s)_(?!\w)"
)


def inline_runs(text: str):
    runs, pos = [], 0
    for m in INLINE.finditer(text):
        if m.start() > pos:
            runs.append((text[pos:m.start()], {}))
        if m.group("hl"):
            runs.append((m.group("hl"), {"hl": True, "bold": True}))
        elif m.group("b") or m.group("b2"):
            runs.append((m.group("b") or m.group("b2"), {"bold": True}))
        elif m.group("code"):
            runs.append((m.group("code"), {"code": True}))
        elif m.group("lt"):
            runs.append((m.group("lt"), {"link": m.group("lu")}))
        else:
            runs.append((m.group("i") or m.group("i2"), {"italic": True}))
        pos = m.end()
    if pos < len(text):
        runs.append((text[pos:], {}))
    return runs or [("", {})]


def plain(text: str) -> str:
    return "".join(t for t, _ in inline_runs(text))


def disp_width(s: str) -> float:
    """Approximate width in em."""
    w = 0.0
    for ch in s:
        if is_cjk(ch):
            w += 1.0
        elif ch == " ":
            w += 0.28
        elif ch.isupper() or ch.isdigit():
            w += 0.62
        else:
            w += 0.5
    return w
