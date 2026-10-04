"""Layout variants for the slide chrome: cover, outline, chapter divider, nav bar, callout, closing.

Each theme picks one variant per role in `style` (see style.py); the original BlockFrame layouts
live in canvas.py as `cover_split`, `outline_line`, `divider_panel`, `nav_band`, `callout_pill`
and `closing_frame`.
"""
from __future__ import annotations

import math

from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from ..markdown import disp_width
from .style import H, W, mix

PAD = 0.55
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
NAV_TOP = {"band": 1.3, "pills": 1.12, "underline": 1.08, "breadcrumb": 0.82, "none": 0.5}
CALLOUT_ICONS = {"note": "circle-info", "tip": "lightbulb", "important": "circle-exclamation",
                 "warning": "triangle-exclamation", "caution": "triangle-exclamation", "summary": "list-check",
                 "problem": "circle-xmark", "negative": "circle-xmark", "result": "circle-check",
                 "success": "circle-check", "positive": "circle-check"}


class ChromeMixin:
    # ------------------------------------------------------------------ dispatch
    def render_cover(self, pg):
        getattr(self, f"cover_{self.variants['cover']}", self.cover_split)(pg)

    def render_outline(self, pg):
        getattr(self, f"outline_{self.variants['outline']}", self.outline_line)(pg)

    def render_divider(self, pg):
        getattr(self, f"divider_{self.variants['divider']}", self.divider_panel)(pg)

    def render_closing(self, pg):
        getattr(self, f"closing_{self.variants['closing']}", self.closing_frame)(pg)

    def nav(self, s, ci, si):
        v = self.variants["nav"]
        if v != "none":
            getattr(self, f"nav_{v}", self.nav_band)(s, ci, si)

    def callout(self, s, d, x, y, w, h):
        getattr(self, f"callout_{self.variants['callout']}", self.callout_pill)(s, d, x, y, w, h)

    def content_top(self, pg):
        if pg.chapter is None:
            return 0.5
        return NAV_TOP.get(self.variants["nav"], 1.3)

    # ------------------------------------------------------------------ shared helpers
    def title_size(self, text, width, max_size=54, min_size=28, max_lines=3):
        n = max(1.0, disp_width(text))
        return max(min(max_size, int(width * 72 / math.ceil(n / k) * 0.95)) for k in range(1, max_lines + 1)) \
            if n else max_size

    def meta_line(self):
        m = self.meta
        return "  ·  ".join(str(m[k]) for k in ("author", "date") if m.get(k))

    def heading_text(self, text):
        return text.upper() if self.t.get("style", {}).get("title_upper") and text.isascii() else text

    def sub_list(self, s, pg, x, y, w, h, col, numbered=True):
        """Sections of a chapter as a vertical list (current one highlighted when recapping)."""
        subs = self.chapters[pg.chapter].subsections
        if not subs:
            return
        step = min(0.78, h / len(subs))
        for k, sub in enumerate(subs):
            cy = y + k * step
            current = pg.recap and k == pg.sub
            dim = pg.recap and k != pg.sub
            label = ROMAN[k] if k < len(ROMAN) else str(k + 1)
            colr = self.muted if dim else self.title_ink
            if numbered:
                self.text(s, x, cy, 0.7, step, label, 18, font="display", color=col if not dim else self.muted,
                          anchor=MSO_ANCHOR.MIDDLE, bold=True)
            self.text(s, x + (0.75 if numbered else 0), cy, w - 0.75, step, sub.title, 22 if not current else 24,
                      bold=True, color=colr, anchor=MSO_ANCHOR.MIDDLE, font="heading")
            if k < len(subs) - 1:
                ln = self.line(s, x, cy + step, x + w, cy + step, color=mix(self.muted, self.ground, 0.5), width=0.5)
                self.alpha_line(ln, 0.8)

    def sub_chips(self, s, pg, x, y, w, col):
        subs = self.chapters[pg.chapter].subsections
        cx = x
        for k, sub in enumerate(subs):
            current = pg.recap and k == pg.sub
            fill = col if (current or not pg.recap) else mix(col, self.ground, 0.7)
            _, pw = self.pill(s, cx, y, f"{ROMAN[k] if k < len(ROMAN) else k + 1}  {sub.title}", fill, size=13,
                              upper=False, font="body", shadow=self.surface in ("brutal", "pixel"))
            cx += pw + 0.2
            if cx > x + w - 1.0:
                cx, y = x, y + 0.55

    # ------------------------------------------------------------------ covers
    def cover_centered(self, pg):
        s = self.new_slide(notes=pg.notes, role="cover")
        m = self.meta
        self.decorate(s, (W - 3.4, 0.35, 3.0, 2.6), "outline")
        self.decorate(s, (0.35, H - 2.9, 3.0, 2.6), "divider")
        eb = m.get("eyebrow", "PRESENTATION")
        self.pill(s, (W - self.pill_width(eb, 13)) / 2, 1.35, eb, self.pal(0), size=13,
                  shadow=self.surface in ("brutal", "pixel"))
        title = self.heading_text(pg.title)
        size = self.title_size(title, 10.0, 56)
        self.text(s, 1.6, 2.0, W - 3.2, 2.6, title, size, bold=True, color=self.title_ink, font="heading",
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.05)
        if pg.subtitle:
            self.text(s, 1.6, 4.75, W - 3.2, 0.6, pg.subtitle, 20, color=self.muted, align=PP_ALIGN.CENTER,
                      bold=True)
        self.text(s, 1.6, 5.7, W - 3.2, 0.4, self.meta_line(), 14, color=self.ink, align=PP_ALIGN.CENTER,
                  font="label")

    def cover_poster(self, pg):
        s = self.new_slide(notes=pg.notes, role="cover")
        m = self.meta
        self.shape(s, MSO_SHAPE.RECTANGLE, W - 4.2, 0, 4.2, H, fill=self.pal(0))
        self.decorate(s, (W - 4.0, 0.5, 3.6, 6.5), "cover")
        self.text(s, PAD, 0.55, 6, 0.4, m.get("eyebrow", "PRESENTATION").upper(), 13, font="label", bold=True,
                  color=self.pal(1) if self.luminance(self.pal(1)) < 0.6 else self.title_ink, spc=3)
        title = self.heading_text(pg.title)
        size = self.title_size(title, 8.2, 80, max_lines=4)
        self.text(s, PAD, 1.1, 8.3, 4.4, title, size, bold=True, color=self.title_ink, font="heading",
                  anchor=MSO_ANCHOR.MIDDLE, line_spacing=0.95)
        if pg.subtitle:
            self.text(s, PAD, 5.6, 8.3, 0.5, pg.subtitle, 18, color=self.muted, bold=True)
        self.shape(s, MSO_SHAPE.RECTANGLE, PAD, 6.35, 1.2, 0.08, fill=self.title_ink)
        self.text(s, PAD + 1.45, 6.2, 6.8, 0.4, self.meta_line(), 13, color=self.ink, font="label",
                  anchor=MSO_ANCHOR.MIDDLE)

    def cover_editorial(self, pg):
        """Academic / editorial: tag pill, serif title, accent rule, author + affiliation columns, footer."""
        s = self.new_slide(notes=pg.notes, role="cover")
        m = self.meta
        eb = m.get("eyebrow", "")
        if eb:
            self.pill(s, PAD + 0.45, 1.05, eb, self.pal(0), size=12, upper=False, font="label", shadow=False)
        title = self.heading_text(pg.title)
        size = self.title_size(title, 11.2, 34, 22)
        self.text(s, PAD + 0.45, 1.6, 11.6, 1.5, title, size, bold=True, color=self.title_ink, font="heading",
                  anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.12)
        self.shape(s, MSO_SHAPE.RECTANGLE, PAD + 0.45, 3.2, 11.3, 0.05, fill=self.accent_line or self.pal(1))
        if pg.subtitle:
            self.text(s, PAD + 0.45, 3.35, 11.3, 0.45, pg.subtitle, 15, color=self.muted, bold=True)
        authors = [a.strip() for a in str(m.get("authors", "")).split(";") if a.strip()]
        affils = [a.strip() for a in str(m.get("affiliations", "")).split(";") if a.strip()]
        if authors:
            self.text(s, PAD + 0.45, 3.95, 5.2, 1.6, [{"text": a, "size": 13} for a in authors], 13, color=self.ink,
                      font="heading")
        if affils:
            self.text(s, PAD + 6.0, 3.95, 6.0, 1.6, [{"text": a, "size": 13} for a in affils], 13, color=self.muted,
                      font="heading")
        if m.get("date"):
            self.text(s, PAD + 0.45, H - 1.1, 4, 0.4, str(m["date"]), 12, color=self.muted, font="label")
        if m.get("author"):
            self.text(s, W - PAD - 5.5, H - 1.1, 5.0, 0.4, str(m["author"]), 13, color=self.muted,
                      align=PP_ALIGN.RIGHT, font="heading")

    def cover_frame(self, pg):
        s = self.new_slide(notes=pg.notes, role="cover")
        m = self.meta
        col = self.accent_line or self.black
        self.shape(s, MSO_SHAPE.RECTANGLE, 0.45, 0.45, W - 0.9, H - 0.9, fill=None, line=col, lw=2)
        self.shape(s, MSO_SHAPE.RECTANGLE, 0.62, 0.62, W - 1.24, H - 1.24, fill=None, line=col, lw=0.75)
        for fx, fy in ((0.45, 0.45), (W - 0.45, 0.45), (0.45, H - 0.45), (W - 0.45, H - 0.45)):
            self.shape(s, MSO_SHAPE.DIAMOND, fx - 0.2, fy - 0.2, 0.4, 0.4, fill=col)
        eb = m.get("eyebrow", "")
        if eb:
            self.text(s, 1.5, 1.35, W - 3.0, 0.4, eb.upper(), 14, font="label", color=col, align=PP_ALIGN.CENTER,
                      spc=4, bold=True)
        title = self.heading_text(pg.title)
        size = self.title_size(title, 9.5, 52)
        self.text(s, 1.8, 1.85, W - 3.6, 2.4, title, size, bold=True, color=self.title_ink, font="heading",
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.05)
        self.shape(s, MSO_SHAPE.DIAMOND, W / 2 - 0.13, 4.45, 0.26, 0.26, fill=col)
        self.line(s, W / 2 - 2.4, 4.58, W / 2 - 0.3, 4.58, color=col, width=0.75)
        self.line(s, W / 2 + 0.3, 4.58, W / 2 + 2.4, 4.58, color=col, width=0.75)
        if pg.subtitle:
            self.text(s, 1.8, 4.85, W - 3.6, 0.5, pg.subtitle, 18, color=self.muted, align=PP_ALIGN.CENTER,
                      font="heading")
        self.text(s, 1.8, 5.75, W - 3.6, 0.4, self.meta_line(), 13, color=self.ink, align=PP_ALIGN.CENTER,
                  font="label")

    def cover_bento(self, pg):
        s = self.new_slide(notes=pg.notes, role="cover")
        m = self.meta
        g = 0.22
        x0, y0, cw, ch = PAD, 0.55, (W - 2 * PAD - 3 * g) / 4, (H - 1.1 - 2 * g) / 3
        tile = lambda c, r, sw, sh, fill: self.block(s, x0 + c * (cw + g), y0 + r * (ch + g),  # noqa: E731
                                                     cw * sw + g * (sw - 1), ch * sh + g * (sh - 1), fill)
        big = tile(0, 0, 3, 2, self.white)
        title = self.heading_text(pg.title)
        size = self.title_size(title, cw * 3 - 0.8, 50)
        self.text(s, 0, 0, 0, 0, title, size, bold=True, color=self.card_ink, font="heading",
                  anchor=MSO_ANCHOR.MIDDLE, target=big, margin=0.4)
        acc = tile(3, 0, 1, 1, self.pal(0))
        self.text(s, 0, 0, 0, 0, m.get("eyebrow", "DECK"), 16, bold=True, color=self.on(self.pal(0)),
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, target=acc, font="label", margin=0.15)
        side = tile(3, 1, 1, 2, self.pal(1))
        self.glyph(s, "layer-group", x0 + 3 * (cw + g), y0 + (ch + g), cw, ch * 2 + g, self.on(self.pal(1)), 0.45)
        sub = tile(0, 2, 2, 1, self.pal(2))
        if pg.subtitle:
            self.text(s, 0, 0, 0, 0, pg.subtitle, 16, bold=True, color=self.on(self.pal(2)), anchor=MSO_ANCHOR.MIDDLE,
                      target=sub, margin=0.3)
        meta = tile(2, 2, 1, 1, self.pal(3))
        self.text(s, 0, 0, 0, 0, self.meta_line().replace("  ·  ", "\n"), 13, color=self.on(self.pal(3)),
                  anchor=MSO_ANCHOR.MIDDLE, target=meta, margin=0.2, font="label")
        _ = side

    def cover_minimal(self, pg):
        s = self.new_slide(notes=pg.notes, role="cover")
        m = self.meta
        self.shape(s, MSO_SHAPE.OVAL, PAD + 0.05, 2.15, 0.22, 0.22, fill=self.pal(0))
        if m.get("eyebrow"):
            self.text(s, PAD + 0.45, 2.05, 8, 0.4, m["eyebrow"], 13, color=self.muted, font="label",
                      anchor=MSO_ANCHOR.MIDDLE)
        title = self.heading_text(pg.title)
        size = self.title_size(title, 9.5, 48, 26)
        self.text(s, PAD, 2.6, 10, 2.2, title, size, bold=True, color=self.title_ink, font="heading",
                  line_spacing=1.08)
        if pg.subtitle:
            self.text(s, PAD, 4.9, 10, 0.5, pg.subtitle, 16, color=self.muted)
        self.text(s, PAD, H - 0.95, 10, 0.4, self.meta_line(), 12, color=self.muted, font="label")
        self.decorate(s, (W - 3.0, H - 3.0, 2.4, 2.4), "divider")

    # ------------------------------------------------------------------ outlines
    def _outline_head(self, s, x=PAD, y=0.55):
        m = self.meta
        self.text(s, x, y, 6, 0.9, m.get("outline_title", "大綱"), 40, bold=True, color=self.title_ink, font="heading")
        self.text(s, x, y + 0.85, 6, 0.4, m.get("outline_en", "OUTLINE"), 14, font="label", color=self.muted, spc=3,
                  bold=True)

    def outline_list(self, pg):
        s = self.new_slide(role="outline")
        self._outline_head(s)
        n = len(self.chapters)
        cols = 1 if n <= 5 else 2
        rows = -(-n // cols)
        top, bottom = 2.2, H - 0.7
        step = min(1.0, (bottom - top) / rows)
        cw = (W - 2 * PAD - 0.6 * (cols - 1)) / cols
        for k, ch in enumerate(self.chapters):
            c, r = divmod(k, rows)
            x, y = PAD + c * (cw + 0.6), top + r * step
            self.text(s, x, y, 1.3, step, f"{k + 1:02d}", 34, font="display", color=self.ch_color(k)
                      if self.luminance(self.ch_color(k)) < 0.75 else self.title_ink, anchor=MSO_ANCHOR.MIDDLE)
            lines = [{"text": ch.title, "size": 24, "bold": True, "color": self.title_ink, "font": "heading"}]
            if ch.subtitle:
                lines.append({"text": ch.subtitle.upper(), "size": 11, "font": "label", "color": self.muted, "spc": 2})
            self.text(s, x + 1.4, y, cw - 1.4, step, lines, 24, anchor=MSO_ANCHOR.MIDDLE)
            ln = self.line(s, x, y + step, x + cw, y + step, color=mix(self.muted, self.ground, 0.4), width=0.75)
            _ = ln
        self.decorate(s, (W - 2.4, 0.4, 1.9, 1.6), "accent")
        self.counter_pill(s)

    def outline_grid(self, pg):
        s = self.new_slide(role="outline")
        self._outline_head(s)
        n = len(self.chapters)
        cols = n if n <= 3 else (2 if n == 4 else 3)
        rows = -(-n // cols)
        g = 0.35
        top = 2.25
        cw = (W - 2 * PAD - g * (cols - 1)) / cols
        ch_h = min(2.2, (H - 0.75 - top - g * (rows - 1)) / rows)
        for k, ch in enumerate(self.chapters):
            r, c = divmod(k, cols)
            x, y = PAD + c * (cw + g), top + r * (ch_h + g)
            col = self.ch_color(k)
            self.block(s, x, y, cw, ch_h, self.white)
            self.text(s, x + 0.3, y + 0.2, 1.4, 0.8, f"{k + 1:02d}", 32, font="display",
                      color=col if self.luminance(col) < 0.75 else self.card_ink)
            lines = [{"text": ch.title, "size": 22, "bold": True, "color": self.card_ink, "font": "heading"}]
            if ch.subtitle:
                lines.append({"text": ch.subtitle.upper(), "size": 11, "font": "label", "color": self.card_muted,
                              "spc": 2})
            self.text(s, x + 0.3, y + 1.0, cw - 0.6, ch_h - 1.1, lines, 22)
        self.counter_pill(s)

    # ------------------------------------------------------------------ dividers
    def divider_hero(self, pg):
        ch = self.chapters[pg.chapter]
        col = self.ch_color(pg.chapter)
        s = self.new_slide(notes=pg.notes, role="divider")
        num_col = col if self.luminance(col) < 0.8 else self.title_ink
        self.text(s, PAD - 0.1, 0.6, 5.0, 4.2, f"{pg.chapter + 1:02d}", 200, font="display", color=num_col,
                  anchor=MSO_ANCHOR.MIDDLE, spc=-6)
        self.shape(s, MSO_SHAPE.RECTANGLE, PAD, 4.95, 3.2, 0.08, fill=num_col)
        lines = [{"text": self.heading_text(ch.title), "size": 44, "bold": True, "color": self.title_ink,
                  "font": "heading", "space_after": 4}]
        if ch.subtitle:
            lines.append({"text": ch.subtitle.upper(), "size": 16, "font": "label", "color": self.muted, "spc": 3})
        self.text(s, 5.6, 1.0, W - 5.6 - PAD, 1.6, lines, 44, anchor=MSO_ANCHOR.BOTTOM)
        self.sub_list(s, pg, 5.6, 2.95, W - 5.6 - PAD, 3.6, num_col)
        self.decorate(s, (W - 2.0, H - 1.9, 1.6, 1.6), "divider")
        self.counter_pill(s)

    def divider_centered(self, pg):
        ch = self.chapters[pg.chapter]
        col = self.ch_color(pg.chapter)
        s = self.new_slide(notes=pg.notes, role="divider")
        self.decorate(s, (W - 3.2, 0.4, 2.8, 2.6), "outline")
        label = f"{pg.chapter + 1:02d}"
        self.pill(s, (W - self.pill_width(label, 18)) / 2, 1.15, label, col, size=18,
                  shadow=self.surface in ("brutal", "pixel"))
        self.text(s, 1.0, 1.85, W - 2.0, 1.4, self.heading_text(ch.title), 56, bold=True, color=self.title_ink,
                  font="heading", align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if ch.subtitle:
            self.text(s, 1.0, 3.25, W - 2.0, 0.5, ch.subtitle.upper(), 16, font="label", color=self.muted,
                      align=PP_ALIGN.CENTER, spc=4)
        subs = ch.subsections
        if subs:
            widths = [self.pill_width(f"{ROMAN[k] if k < 12 else k + 1}  {sb.title}", 13, "body", False) + 0.2
                      for k, sb in enumerate(subs)]
            total = sum(widths)
            self.sub_chips(s, pg, max(PAD, (W - total) / 2), 4.4, W - 2 * PAD, col)
        self.counter_pill(s)

    def divider_band(self, pg):
        ch = self.chapters[pg.chapter]
        col = self.ch_color(pg.chapter)
        s = self.new_slide(notes=pg.notes, role="divider")
        self.shape(s, MSO_SHAPE.RECTANGLE, 0, 1.7, W, 2.6, fill=col)
        ink = self.on(col)
        self.text(s, PAD, 1.7, 2.6, 2.6, f"{pg.chapter + 1:02d}", 110, font="display", color=ink,
                  anchor=MSO_ANCHOR.MIDDLE)
        lines = [{"text": self.heading_text(ch.title), "size": 48, "bold": True, "color": ink, "font": "heading"}]
        if ch.subtitle:
            lines.append({"text": ch.subtitle.upper(), "size": 15, "font": "label", "color": ink, "spc": 4})
        self.text(s, 3.6, 1.7, W - 3.6 - PAD, 2.6, lines, 48, anchor=MSO_ANCHOR.MIDDLE)
        if ch.subsections:
            self.sub_chips(s, pg, 3.6, 4.85, W - 3.6 - PAD, mix(col, self.ground, 0.25))
        self.decorate(s, (W - 2.2, 0.15, 1.6, 1.4), "divider")
        self.counter_pill(s)

    def divider_minimal(self, pg):
        ch = self.chapters[pg.chapter]
        col = self.ch_color(pg.chapter)
        s = self.new_slide(notes=pg.notes, role="divider")
        acc = col if self.luminance(col) < 0.8 else self.title_ink
        self.text(s, PAD, 1.6, 6, 0.5, f"CHAPTER {pg.chapter + 1:02d}", 14, font="label", color=acc, spc=4, bold=True)
        self.text(s, PAD, 2.1, 6.4, 1.8, self.heading_text(ch.title), 48, bold=True, color=self.title_ink,
                  font="heading", anchor=MSO_ANCHOR.TOP)
        if ch.subtitle:
            self.text(s, PAD, 3.9, 6.4, 0.5, ch.subtitle, 16, color=self.muted)
        self.line(s, 7.3, 1.4, 7.3, H - 1.2, color=mix(self.muted, self.ground, 0.4), width=0.75)
        self.sub_list(s, pg, 7.7, 1.5, W - 7.7 - PAD, 4.6, acc)
        self.counter_pill(s)

    # ------------------------------------------------------------------ nav bars
    def nav_pills(self, s, ci, si):
        """Lab-meeting style: chapter pills, section pills on an accent rule."""
        left, right = PAD + 0.6, W - PAD - 0.6
        n = len(self.chapters)
        gap = 0.18
        pw = min(1.55, (right - left - gap * (n - 1)) / n)
        x = (W - (pw * n + gap * (n - 1))) / 2
        for k, ch in enumerate(self.chapters):
            cur = k == ci
            fill = self.pal(0) if cur else mix(self.muted, self.ground, 0.72)
            sp = self.shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x + k * (pw + gap), 0.2, pw, 0.34, fill=fill)
            self.text(s, 0, 0, 0, 0, ch.title, 12, bold=True, color=self.on(fill) if cur else mix(self.on(fill), fill,
                                                                                                     0.35),
                      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, target=sp)
        rule = self.accent_line or self.pal(1)
        subs = self.chapters[ci].subsections
        y = 0.72
        sx = PAD + 0.55
        self.line(s, PAD, y, sx - 0.08, y, color=rule, width=1.5)
        for k, sub in enumerate(subs):
            cur = k == si
            w = self.measure(sub.title, 10) + 0.36
            fill = self.pal(0) if cur else mix(self.muted, self.ground, 0.78)
            sp = self.shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, sx, y - 0.13, w, 0.26, fill=fill)
            self.text(s, 0, 0, 0, 0, sub.title, 10, bold=cur, color=self.on(fill) if cur else mix(self.on(fill), fill, 0.4),
                      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, target=sp)
            sx += w + 0.12
        self.line(s, sx + 0.04, y, W - PAD, y, color=rule, width=1.5)

    def nav_underline(self, s, ci, si):
        x = PAD
        rule_y = 0.62
        for k, ch in enumerate(self.chapters):
            cur = k == ci
            w = self.measure(ch.title, 13) + 0.3
            self.text(s, x, 0.2, w, 0.38, ch.title, 13, bold=cur, color=self.title_ink if cur else self.muted,
                      anchor=MSO_ANCHOR.MIDDLE, font="label")
            if cur:
                self.shape(s, MSO_SHAPE.RECTANGLE, x, rule_y - 0.05, w - 0.25, 0.06, fill=self.pal(0))
            x += w + 0.25
        self.line(s, PAD, rule_y, W - PAD, rule_y, color=mix(self.muted, self.ground, 0.45), width=0.75)
        subs = self.chapters[ci].subsections
        x = PAD
        for k, sub in enumerate(subs):
            cur = k == si
            w = self.measure(sub.title, 10.5) + 0.3
            self.text(s, x, 0.66, w, 0.3, sub.title, 10.5, bold=cur, color=self.pal(0) if cur and
                      self.luminance(self.pal(0)) < 0.7 else (self.title_ink if cur else self.muted),
                      anchor=MSO_ANCHOR.MIDDLE)
            x += w + 0.1

    def nav_breadcrumb(self, s, ci, si):
        ch = self.chapters[ci]
        sub = ch.subsections[si].title if si is not None and ch.subsections else ""
        acc = self.ch_color(ci) if self.luminance(self.ch_color(ci)) < 0.75 else self.title_ink
        self.text(s, PAD, 0.22, 0.6, 0.36, f"{ci + 1:02d}", 13, font="label", bold=True, color=acc,
                  anchor=MSO_ANCHOR.MIDDLE)
        crumb = ch.title + (f"   /   {sub}" if sub else "")
        self.text(s, PAD + 0.55, 0.22, 9, 0.36, crumb, 12, font="label", color=self.muted, anchor=MSO_ANCHOR.MIDDLE)
        n = len(self.chapters)
        for k in range(n):
            d = 0.13
            x = W - PAD - (n - k) * 0.28
            fill = acc if k == ci else mix(self.muted, self.ground, 0.6)
            self.shape(s, MSO_SHAPE.OVAL, x, 0.34, d, d, fill=fill)

    # ------------------------------------------------------------------ callouts
    def callout_banner(self, s, d, x, y, w, h):
        fill = self.tone_fill(d["kind"]) or self.pal(0)
        sp = self.shape(s, MSO_SHAPE.RECTANGLE if self.radius <= 0 else MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w,
                        min(h, 0.62), fill=fill)
        if self.radius > 0:
            sp.adjustments[0] = 0.25
        size = 16
        while size > 11 and self.measure(d["text"], size) > w - 0.6:
            size -= 1
        self.text(s, 0, 0, 0, 0, d["text"], size, bold=True, color=self.on(fill), align=PP_ALIGN.CENTER,
                  anchor=MSO_ANCHOR.MIDDLE, target=sp, margin=0.12)

    def callout_tint(self, s, d, x, y, w, h):
        base = self.tone_fill(d["kind"]) or self.pal(1)
        fill = mix(base, self.ground, 0.78)
        self.block(s, x, y, w, h, fill, thin=True)
        icon = CALLOUT_ICONS.get(d["kind"], "circle-info")
        ink = base if self.luminance(base) < 0.65 else self.on(fill)
        self.glyph(s, icon, x + 0.15, y, 0.7, h, ink, scale=0.55)
        size = 15
        while size > 11 and self.lines_height([{"text": d["text"], "size": size}], w - 1.2) + 0.2 > h:
            size -= 1
        self.text(s, x + 0.95, y, w - 1.2, h, d["text"], size, bold=True, color=self.on(fill),
                  anchor=MSO_ANCHOR.MIDDLE)

    # ------------------------------------------------------------------ closings
    def closing_centered(self, pg):
        s = self.new_slide(role="closing")
        self.decorate(s, (W - 3.4, 0.4, 3.0, 2.6), "outline")
        self.decorate(s, (0.4, H - 2.8, 2.6, 2.4), "divider")
        label = self.meta.get("closing_label", "THANK YOU")
        self.text(s, 1, 2.0, W - 2, 0.5, label.upper() if label.isascii() else label, 16, font="label",
                  color=self.muted, align=PP_ALIGN.CENTER, spc=5, bold=True)
        font = "display" if pg.title.isascii() else "heading"
        self.text(s, 1, 2.6, W - 2, 2.2, self.heading_text(pg.title), 88, bold=True, color=self.title_ink, font=font,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        self.shape(s, MSO_SHAPE.RECTANGLE, W / 2 - 0.8, 5.05, 1.6, 0.07, fill=self.accent_line or self.pal(0))

    def closing_poster(self, pg):
        s = self.new_slide(role="closing")
        self.shape(s, MSO_SHAPE.RECTANGLE, 0, 0, W * 0.42, H, fill=self.pal(0))
        self.decorate(s, (0.5, 0.6, W * 0.42 - 1.0, H - 1.2), "cover")
        label = self.meta.get("closing_label", "THANK YOU")
        self.text(s, W * 0.46, 2.0, W * 0.5, 0.5, label.upper() if label.isascii() else label, 16, font="label",
                  color=self.muted, spc=4, bold=True)
        font = "display" if pg.title.isascii() else "heading"
        self.text(s, W * 0.46, 2.5, W * 0.5, 2.6, self.heading_text(pg.title), 96, bold=True, color=self.title_ink,
                  font=font, anchor=MSO_ANCHOR.MIDDLE)
