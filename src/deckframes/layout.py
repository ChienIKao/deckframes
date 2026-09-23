"""Text measurement, pagination and slide planning shared by both engines."""
from __future__ import annotations

import math

from .markdown import Block, Doc, SlideSpec, disp_width, plain

EMU_PER_PT = 12700

def estimate_height_pt(paras, size, width_emu):
    width_pt = width_emu / EMU_PER_PT - 14.4
    total = 0.0
    for p in paras:
        s = size * p.get("scale", 1.0)
        avail = max(40.0, width_pt - 22 * p.get("level", 0) - (18 if p.get("bullet") != "none" else 0))
        lines = 0
        for seg in plain(p["text"]).split("\n"):
            lines += max(1, math.ceil(disp_width(seg) * s / avail))
        total += lines * s * 1.2 + s * 0.45
    return total + 7.2


def fit_size(paras, w, h, max_size, min_size):
    for s in range(int(max_size), int(min_size) - 1, -1):
        if estimate_height_pt(paras, s, w) <= h / EMU_PER_PT:
            return s, True
    return int(min_size), False


# --------------------------------------------------------------------------- planning


def text_units(block: Block):
    """Split a text block into atomic units (for pagination) with a weight each."""
    if block.kind == "bullets":
        groups, cur = [], []
        for it in block.data:
            if it["level"] == 0 and cur:
                groups.append(cur)
                cur = []
            cur.append(it)
        if cur:
            groups.append(cur)
        return [(Block("bullets", g), sum(1 + disp_width(plain(it["text"])) // 40 for it in g)) for g in groups]
    if block.kind in ("para", "quote"):
        return [(block, 1 + disp_width(plain(block.data)) // 40)]
    return [(block, 1)]


TEXT_KINDS = ("bullets", "para", "sub", "quote")


def merge_bullets(bs):
    """Merge adjacent bullet groups back into one block."""
    out = []
    for b in bs:
        if out and b.kind == "bullets" and out[-1].kind == "bullets":
            out[-1] = Block("bullets", out[-1].data + b.data)
        else:
            out.append(b)
    return out


def paginate(title, blocks, notes, cfg):
    max_units = int(cfg.get("max_lines", 9))
    max_rows = int(cfg.get("max_table_rows", 10))
    visuals, units = [], []
    for b in blocks:
        if b.kind == "table" and len(b.data["rows"]) - 1 > max_rows:
            head, body = b.data["rows"][0], b.data["rows"][1:]
            for k in range(0, len(body), max_rows):
                visuals.append(Block("table", {"rows": [head] + body[k:k + max_rows], "aligns": b.data["aligns"]}))
        elif b.kind in ("image", "table", "code"):
            visuals.append(b)
        else:
            units.extend(text_units(b))

    # with a visual beside the text, the text column holds less
    limit = max_units if not visuals else max(4, int(max_units * 0.75))
    pages, cur, w = [], [], 0
    for blk, wt in units:
        if cur and w + wt > limit:
            pages.append(cur)
            cur, w = [], 0
        cur.append(blk)
        w += wt
    if cur or not pages:
        pages.append(cur)

    specs = []
    extra_visuals = visuals[2:] if len(pages) == 1 and len(visuals) > 2 and units else []
    first_visuals = visuals[:2] if extra_visuals else visuals
    for n, pg in enumerate(pages):
        vis = first_visuals if n == 0 else []
        # tables beyond the first get their own slides
        tables = [v for v in vis if v.kind == "table"]
        if len(tables) > 1:
            vis = [v for v in vis if v.kind != "table"] + tables[:1]
            extra_visuals = tables[1:] + extra_visuals
        specs.append(SlideSpec("content", title=title, blocks=merge_bullets(pg) + vis, notes=notes if n == 0 else []))
    for v in extra_visuals:
        specs.append(SlideSpec("content", title=title, blocks=[v]))
    cont = cfg.get("continued_suffix", "（續）")
    for s in specs[1:]:
        s.title = f"{title}{cont}" if title else ""
    return specs


def degrade(blocks):
    """Map canvas-only blocks onto what the template engine can draw."""
    out = []
    for b in blocks:
        if b.kind == "component":
            d = b.data
            if d["type"] == "chart" and d["rows"]:
                out.append(Block("table", {"rows": d["rows"], "aligns": []}))
                continue
            items = []
            for it in d["items"]:
                t = f"**{it['title']}**" + (f"：{it['desc']}" if it["desc"] else "")
                items.append({"level": 0, "text": t, "ordered": d["type"] in ("steps", "timeline", "flow")})
                items += [{"level": 1, "text": c, "ordered": False} for c in it["children"]]
            if items:
                out.append(Block("bullets", items))
        elif b.kind == "callout":
            out.append(Block("quote", b.data["text"]))
        elif b.kind == "source":
            out.append(Block("para", b.data))
        else:
            out.append(b)
    return out


def plan(doc: Doc, cfg: dict):
    meta = doc.meta
    slides = []
    cover = doc.cover
    subtitle = meta.get("subtitle", "")
    intro = cover.blocks
    if not subtitle and len(intro) == 1 and intro[0].kind in ("para", "quote") and disp_width(intro[0].data) <= 60:
        subtitle, intro = intro[0].data, []
    extra = " · ".join(str(meta[k]) for k in ("author", "date") if meta.get(k))
    slides.append(SlideSpec("cover", title=cover.title, subtitle="\n".join(x for x in (subtitle, extra) if x),
                            notes=cover.notes))
    if intro:
        slides += paginate(cover.title, intro, [], cfg)

    named = [s for s in doc.sections if s.title]
    if meta.get("agenda", cfg.get("agenda", True)) and len(named) >= 2:
        slides.append(SlideSpec("agenda", title=meta.get("agenda_title", cfg.get("agenda_title", "目錄")),
                                blocks=[Block("agenda", [s.title for s in named])]))

    label_fmt = meta.get("section_label", cfg.get("section_label", "{n:02d}"))
    n = 0
    for sec in doc.sections:
        if sec.title:
            n += 1
            sub, body = "", sec.blocks
            if len(body) == 1 and body[0].kind in ("para", "quote") and disp_width(body[0].data) <= 60:
                sub, body = body[0].data, []
            slides.append(SlideSpec("section", title=sec.title, subtitle=sub, notes=sec.notes,
                                    label=label_fmt.format(n=n)))
            if body:
                slides += paginate(sec.title, degrade(body), [], cfg)
        elif sec.blocks:
            slides += paginate("", degrade(sec.blocks), sec.notes, cfg)
        for s in sec.slides:
            slides += paginate(s.title, degrade(s.blocks), s.notes, cfg)
        for sub in sec.subsections:
            if sub.blocks or not sub.slides:
                slides += paginate(sub.title, degrade(sub.blocks), sub.notes, cfg)
            for s in sub.slides:
                slides += paginate(s.title, degrade(s.blocks), s.notes, cfg)

    closing = meta.get("closing", cfg.get("closing", False))
    if closing:
        slides.append(SlideSpec("closing", title=str(closing) if closing is not True else "謝謝聆聽"))
    return slides
