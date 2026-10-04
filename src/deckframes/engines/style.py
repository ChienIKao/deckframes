"""Visual-style system for the canvas engine.

A theme's `style` block decides *how* things are drawn, not just their colours:

  surface   card treatment: brutal | pixel | flat | outline | soft | glass | clay | neu |
            paper | sketch | neon | luxury | ornate
  radius    corner radius (in) for cards / boxes
  cover / divider / nav / outline / callout / closing   layout variants (see chrome.py)
  ground    {"type": "solid"} | {"type": "gradient", "colors": [a, b], "angle": 90}
  texture   overlay drawn on every slide: none | grid | scanlines | dots | paper | noise
  decor     decoration vocabulary used on cover / outline / divider / statement slides

Everything stays native PowerPoint (shapes, gradient fills, DrawingML effects), so decks stay editable.
"""
from __future__ import annotations

import math

from lxml import etree
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_PATTERN
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.util import Pt

IN = 914400
W, H = 13.333, 7.5

VARIANT_DEFAULTS = {"cover": "split", "divider": "panel", "nav": "band", "outline": "line",
                    "callout": "pill", "closing": "frame"}
EFFECT_ORDER = ("a:blur", "a:fillOverlay", "a:glow", "a:innerShdw", "a:outerShdw", "a:prstShdw",
                "a:reflection", "a:softEdge")


def E(x: float) -> int:
    return int(round(x * IN))


def rgb(h: str) -> RGBColor:
    return RGBColor.from_string(h.lstrip("#").upper())


def mix(a: str, b: str, t: float) -> str:
    """Blend hex colour a toward b by t (0..1)."""
    ca = [int(a.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


class StyleMixin:
    # ------------------------------------------------------------------ setup
    def init_style(self, theme):
        st = theme.get("style", {})
        default_surface = "brutal" if (self.bw > 0 and self.sw > 0) else ("outline" if self.bw > 0 else "flat")
        self.surface = st.get("surface", default_surface)
        self.radius = float(st.get("radius", 0.0))
        self.variants = {k: st.get(k, d) for k, d in VARIANT_DEFAULTS.items()}
        default_decor = ["blocks", "stripes", "stars", "dots"] if self.deco else []
        self.decor = st.get("decor", default_decor) if self.deco or "decor" in st else []
        self.ground_spec = st.get("ground", {"type": "solid"})
        self.texture = st.get("texture", "none")
        self.rule_w = st.get("rule", 3 if self.surface in ("brutal", "pixel") else 1.25)
        self.table_rule = theme.get("stroke", {}).get("table", self.tw if self.tw > 0 else 0.75)
        self.table_line = st.get("table_line", self.black if self.surface in ("brutal", "pixel", "outline",
                                                                             "ornate", "sketch") else
                                 mix(self.muted, self.ground, 0.4))
        self.shadow_color = st.get("shadow", self.black)
        self.accent_line = st.get("accent_line")          # e.g. academic's gold rule
        f = theme["fonts"]
        self.f_heading = f.get("heading", f["body"])
        self.f_ea_heading = f.get("ea_heading", f["ea"])
        self.stat_colored = st.get("stat_color", False)

    def stat_ink(self, k):
        return self.color_for(k) if self.stat_colored and self.luminance(self.color_for(k)) < 0.6 else self.card_ink

    def tone_fill(self, kind: str):
        if kind in ("problem", "negative", "warning", "caution", "risk", "con"):
            return self.tones["negative"]
        if kind in ("result", "success", "positive", "pro", "solution"):
            return self.tones["positive"]
        return None

    # ------------------------------------------------------------------ DrawingML effects
    @staticmethod
    def _effect_list(sp):
        spPr = sp._element.spPr
        eff = spPr.find(qn("a:effectLst"))
        if eff is None:
            eff = etree.Element(qn("a:effectLst"))
            anchor = spPr.find(qn("a:ln"))
            if anchor is None:
                for tag in ("a:solidFill", "a:gradFill", "a:noFill", "a:pattFill", "a:blipFill", "a:prstGeom"):
                    anchor = spPr.find(qn(tag))
                    if anchor is not None:
                        break
            if anchor is not None:
                anchor.addnext(eff)
            else:
                spPr.append(eff)
        return eff

    def _effect(self, sp, tag, attrs, color, alpha):
        eff = self._effect_list(sp)
        el = etree.Element(qn(tag), **{k: str(v) for k, v in attrs.items()})
        c = etree.SubElement(el, qn("a:srgbClr"), val=color.lstrip("#").upper())
        etree.SubElement(c, qn("a:alpha"), val=str(int(alpha * 100000)))
        # keep schema order inside effectLst
        pos = EFFECT_ORDER.index(tag)
        for child in eff:
            name = "a:" + etree.QName(child).localname
            if name in EFFECT_ORDER and EFFECT_ORDER.index(name) > pos:
                child.addprevious(el)
                return el
        eff.append(el)
        return el

    def soft_shadow(self, sp, blur=10, dist=4, angle=90, color=None, alpha=0.22):
        return self._effect(sp, "a:outerShdw", {"blurRad": int(blur * 12700), "dist": int(dist * 12700),
                                                "dir": int(angle * 60000), "algn": "ctr", "rotWithShape": "0"},
                            color or self.shadow_color, alpha)

    def inner_shadow(self, sp, blur=8, dist=3, angle=225, color="FFFFFF", alpha=0.6):
        return self._effect(sp, "a:innerShdw", {"blurRad": int(blur * 12700), "dist": int(dist * 12700),
                                                "dir": int(angle * 60000)}, color, alpha)

    def glow(self, sp, color, radius=6, alpha=0.55):
        return self._effect(sp, "a:glow", {"rad": int(radius * 12700)}, color, alpha)

    def soft_edge(self, sp, radius=18):
        eff = self._effect_list(sp)
        etree.SubElement(eff, qn("a:softEdge"), rad=str(int(radius * 12700)))

    @staticmethod
    def alpha(sp, value, which="fill"):
        """Transparency on a solid fill or line (value = opacity 0..1)."""
        spPr = sp._element.spPr
        node = spPr.find(qn("a:solidFill")) if which == "fill" else spPr.find(qn("a:ln") + "/" + qn("a:solidFill"))
        if node is None:
            return
        clr = node[0]
        for old in clr.findall(qn("a:alpha")):
            clr.remove(old)
        etree.SubElement(clr, qn("a:alpha"), val=str(int(value * 100000)))

    @staticmethod
    def dash(sp, style="sysDash"):
        ln = sp._element.spPr.find(qn("a:ln"))
        if ln is not None:
            for old in ln.findall(qn("a:prstDash")):
                ln.remove(old)
            d = etree.Element(qn("a:prstDash"), val=style)
            fill = ln.find(qn("a:solidFill"))
            (fill.addnext(d) if fill is not None else ln.insert(0, d))

    def gradient(self, sp, c1, c2, angle=90):
        sp.fill.gradient()
        sp.fill.gradient_angle = angle
        st = sp.fill.gradient_stops
        st[0].color.rgb, st[0].position = rgb(c1), 0.0
        st[1].color.rgb, st[1].position = rgb(c2), 1.0

    # ------------------------------------------------------------------ surfaces
    def _jitter(self, x, y, amp):
        if not self.tilt:
            return 0.0
        return round(math.sin(x * 12.9898 + y * 78.233) * amp, 2)

    def surface_block(self, s, x, y, w, h, fill, thin=False, rot=0.0, kind=MSO_SHAPE.RECTANGLE, line=None,
                      shadow=None):
        pill = kind == MSO_SHAPE.ROUNDED_RECTANGLE
        sf = self.surface
        lw = self.tw if thin else self.bw
        if not pill and kind == MSO_SHAPE.RECTANGLE and self.radius > 0:
            kind = MSO_SHAPE.ROUNDED_RECTANGLE
        radius_adj = 0.5 if pill else (min(0.5, self.radius / max(0.05, min(w, h))) if self.radius > 0 else None)

        def main(fill_=fill, line_=None, lw_=None, rot_=rot):
            sp = self.shape(s, kind, x, y, w, h, fill=fill_, line=line_, lw=lw_, rot=rot_)
            if radius_adj is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
                sp.adjustments[0] = radius_adj
            return sp

        if sf in ("brutal", "pixel"):
            off = (self.tsw if thin else self.sw) / 72
            if off > 0:
                if sf == "pixel":
                    self.shape(s, kind, x + off, y + off, w, h, fill=shadow or self.shadow_color, rot=rot)
                    self.shape(s, kind, x + off / 2, y + off / 2, w, h, fill=mix(shadow or self.shadow_color,
                                                                                    self.ground, 0.45), rot=rot)
                else:
                    sh = self.shape(s, kind, x + off, y + off, w, h, fill=shadow or self.shadow_color, rot=rot)
                    if radius_adj is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
                        sh.adjustments[0] = radius_adj
            return main(line_=line or self.black, lw_=lw)
        if sf == "flat":
            return main()
        if sf == "outline":
            return main(line_=line or self.black, lw_=max(lw, 0.75))
        if sf == "soft":
            sp = main(line_=line, lw_=0.75 if line else None)
            self.soft_shadow(sp, blur=12 if not thin else 6, dist=4 if not thin else 2, alpha=0.18)
            return sp
        if sf == "glass":
            base = fill if fill not in (None, self.white) else "FFFFFF"
            sp = main(fill_=base, line_="FFFFFF", lw_=1.0)
            self.alpha(sp, 0.32 if base == "FFFFFF" else 0.55)
            self.alpha(sp, 0.7, which="line")
            self.soft_shadow(sp, blur=18, dist=6, alpha=0.18)
            return sp
        if sf == "clay":
            sp = main()
            self.soft_shadow(sp, blur=16, dist=7, angle=60, color=mix(fill or self.white, "000000", 0.55), alpha=0.35)
            self.inner_shadow(sp, blur=10, dist=4, angle=225, color="FFFFFF", alpha=0.65)
            return sp
        if sf == "neu":
            base = self.ground if fill in (None, self.white) else fill
            twin = self.shape(s, kind, x, y, w, h, fill=base, rot=rot)
            if radius_adj is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
                twin.adjustments[0] = radius_adj
            self.soft_shadow(twin, blur=14, dist=6, angle=225, color="FFFFFF", alpha=0.85)
            sp = main(fill_=base)
            self.soft_shadow(sp, blur=14, dist=6, angle=45, color=mix(self.ground, "000000", 0.35), alpha=0.45)
            return sp
        if sf == "paper":
            sp = main(rot_=rot or self._jitter(x, y, 1.2))
            self.soft_shadow(sp, blur=6, dist=3, angle=100, alpha=0.25)
            return sp
        if sf == "sketch":
            sp = main(line_=line or self.black, lw_=1.5, rot_=rot or self._jitter(x, y, 0.8))
            self.dash(sp, "sysDash")
            return sp
        if sf == "neon":
            accent = line or (fill if fill not in (None, self.white) else self.palette[0])
            sp = main(fill_=self.white if fill in (None, self.white) else mix(fill, self.ground, 0.75),
                      line_=accent, lw_=1.5)
            self.glow(sp, accent, radius=5, alpha=0.5)
            return sp
        if sf in ("luxury", "ornate"):
            sp = main(line_=line or self.black, lw_=0.75 if sf == "luxury" else 1.5)
            inset = 0.06 if sf == "luxury" else 0.08
            if w > 0.6 and h > 0.4 and not pill:
                inner = self.shape(s, kind, x + inset, y + inset, w - 2 * inset, h - 2 * inset, fill=None,
                                   line=line or self.black, lw=0.5, rot=rot)
                if radius_adj is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
                    inner.adjustments[0] = radius_adj
            return sp
        return main(line_=line or self.black, lw_=lw)

    # ------------------------------------------------------------------ ground + texture
    def paint_ground(self, s, ground=None, role=None):
        spec = self.ground_spec
        roles = spec.get("roles", {})
        if role in roles:
            spec = {**spec, **roles[role]}
        fill = s.background.fill
        if ground:
            fill.solid()
            fill.fore_color.rgb = rgb(ground)
            return
        if spec.get("type") == "gradient":
            c1, c2 = (spec.get("colors") or [self.ground, self.palette[0]])[:2]
            fill.gradient()
            fill.gradient_angle = spec.get("angle", 90)
            stops = fill.gradient_stops
            stops[0].color.rgb, stops[0].position = rgb(c1), 0.0
            stops[1].color.rgb, stops[1].position = rgb(c2), 1.0
        else:
            fill.solid()
            fill.fore_color.rgb = rgb(spec.get("color", self.ground))
        self.paint_texture(s)

    def paint_texture(self, s):
        t = self.texture
        if t in (None, "none"):
            return
        line = mix(self.muted, self.ground, 0.55)
        if t == "grid":
            for k in range(1, 27):
                ln = self.line(s, k * 0.5, 0, k * 0.5, H, color=line, width=0.4)
                self.alpha_line(ln, 0.35)
            for k in range(1, 15):
                ln = self.line(s, 0, k * 0.5, W, k * 0.5, color=line, width=0.4)
                self.alpha_line(ln, 0.35)
        elif t == "scanlines":
            sp = self.shape(s, MSO_SHAPE.RECTANGLE, 0, 0, W, H, fill=(mix(self.ground, "FFFFFF", 0.08), self.ground),
                            pattern=MSO_PATTERN.NARROW_HORIZONTAL)
            sp.name = "texture"
        elif t == "dots":
            self.shape(s, MSO_SHAPE.RECTANGLE, 0, 0, W, H, fill=(line, self.ground), pattern=MSO_PATTERN.PERCENT_5)
        elif t == "paper":
            self.shape(s, MSO_SHAPE.RECTANGLE, 0, 0, W, H, fill=(mix(self.ground, "8B6F47", 0.12), self.ground),
                       pattern=MSO_PATTERN.PERCENT_10)
        elif t == "noise":
            self.shape(s, MSO_SHAPE.RECTANGLE, 0, 0, W, H, fill=(mix(self.ground, "000000", 0.06), self.ground),
                       pattern=MSO_PATTERN.PERCENT_20)

    @staticmethod
    def alpha_line(ln, value):
        lnel = ln._element.spPr.find(qn("a:ln"))
        fill = lnel.find(qn("a:solidFill")) if lnel is not None else None
        if fill is not None:
            etree.SubElement(fill[0], qn("a:alpha"), val=str(int(value * 100000)))

    # ------------------------------------------------------------------ decorations
    def decorate(self, s, box, where="cover"):
        """Draw the style's decoration vocabulary inside box=(x, y, w, h)."""
        if not self.decor:
            return
        kinds = self.decor if where == "cover" else self.decor[:2] if where == "outline" else self.decor[:1]
        x, y, w, h = box
        small = where in ("divider", "accent")
        for i, kind in enumerate(kinds):
            fn = getattr(self, f"deco_{kind}", None)
            if fn:
                fn(s, x, y, w, h, i, small)

    def deco_blocks(self, s, x, y, w, h, i, small):
        if small:
            return self.deco_stars(s, x, y, w, h, i, small)
        self.block(s, x + w * 0.2, y + h * 0.08, w * 0.68, h * 0.4, self.pal(0), rot=6)
        self.block(s, x + w * 0.06, y + h * 0.42, w * 0.56, h * 0.34, self.pal(1), rot=-4)

    def deco_stripes(self, s, x, y, w, h, i, small):
        if small:
            return
        d = min(w, h) * 0.3
        self.stripes(s, x + w - d * 1.15, y + h * 0.62, d, d, self.pal(2), rot=8)

    def deco_stars(self, s, x, y, w, h, i, small):
        d = min(w, h) * (0.8 if small else 0.24)
        self.star(s, x + w - d, y + (h - d if small else 0), d, self.pal(3), text=None if small else self.meta.get("badge"),
                  rot=14)

    def deco_dots(self, s, x, y, w, h, i, small):
        if small:
            return
        self.shape(s, MSO_SHAPE.RECTANGLE, x - 0.4, max(0, y - 0.5), w + 0.8, h * 0.55,
                   fill=(self.muted, self.ground), pattern=MSO_PATTERN.PERCENT_5)

    def deco_orbs(self, s, x, y, w, h, i, small):
        spots = [(0.55, 0.12, 0.5), (0.12, 0.42, 0.42), (0.5, 0.55, 0.34)] if not small else [(0.1, 0.1, 0.8)]
        for k, (fx, fy, fr) in enumerate(spots):
            d = min(w, h) * fr
            sp = self.shape(s, MSO_SHAPE.OVAL, x + w * fx, y + h * fy, d, d, fill=self.pal(k))
            self.alpha(sp, 0.55)
            self.soft_edge(sp, radius=max(6, d * 72 * 0.18))

    def deco_clay(self, s, x, y, w, h, i, small):
        spots = [(0.5, 0.06, 0.42, "OVAL"), (0.08, 0.38, 0.34, "ROUNDED"), (0.56, 0.58, 0.3, "OVAL")]
        if small:
            spots = spots[:1]
        for k, (fx, fy, fr, sh) in enumerate(spots):
            d = min(w, h) * fr * (1.3 if small else 1)
            kind = MSO_SHAPE.OVAL if sh == "OVAL" else MSO_SHAPE.ROUNDED_RECTANGLE
            sp = self.shape(s, kind, x + w * fx, y + h * fy, d, d, fill=self.pal(k))
            if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
                sp.adjustments[0] = 0.3
            self.soft_shadow(sp, blur=16, dist=8, angle=60, color=mix(self.pal(k), "000000", 0.5), alpha=0.4)
            self.inner_shadow(sp, blur=12, dist=5, angle=225, color="FFFFFF", alpha=0.7)

    def deco_sparkles(self, s, x, y, w, h, i, small):
        spots = [(0.78, 0.06, 0.22), (0.1, 0.3, 0.12), (0.62, 0.7, 0.16), (0.3, 0.82, 0.08)]
        for k, (fx, fy, fr) in enumerate(spots[:1] if small else spots):
            d = min(w, h) * fr * (3 if small else 1)
            sp = self.shape(s, MSO_SHAPE.STAR_4_POINT, x + w * fx, y + h * fy, d, d, fill=self.pal(k + 2))
            sp.adjustments[0] = 0.12

    def deco_bubbles(self, s, x, y, w, h, i, small):
        spots = [(0.45, 0.1, 0.46), (0.1, 0.5, 0.3), (0.62, 0.62, 0.22)]
        for k, (fx, fy, fr) in enumerate(spots[:1] if small else spots):
            d = min(w, h) * fr * (1.8 if small else 1)
            sp = self.shape(s, MSO_SHAPE.OVAL, x + w * fx, y + h * fy, d, d, fill="FFFFFF")
            self.gradient(sp, "FFFFFF", self.pal(k), angle=45)
            sp.line.color.rgb = rgb("FFFFFF")
            sp.line.width = Pt(1.5)
            self.soft_shadow(sp, blur=10, dist=3, alpha=0.2)

    def deco_sun(self, s, x, y, w, h, i, small):
        d = min(w, h) * (0.9 if small else 0.72)
        cx, cy = x + (w - d) / 2, y + h * (0.02 if not small else 0.05)
        sun = self.shape(s, MSO_SHAPE.OVAL, cx, cy, d, d, fill=self.pal(0))
        self.gradient(sun, self.pal(1), self.pal(0), angle=90)
        self.glow(sun, self.pal(0), radius=14, alpha=0.4)
        for k in range(5):  # horizontal cuts through the lower half
            band_y = cy + d * (0.55 + k * 0.09)
            self.shape(s, MSO_SHAPE.RECTANGLE, cx - 0.05, band_y, d + 0.1, d * (0.012 + k * 0.012),
                       fill=self.ground_spec.get("colors", [self.ground])[-1] if self.ground_spec.get("type") == "gradient"
                       else self.ground)

    def deco_floor(self, s, x, y, w, h, i, small):
        if small:
            return
        horizon = y + h * 0.62
        col = self.pal(2)
        for k in range(7):
            yy = horizon + (h * 0.38) * (k / 6) ** 1.6
            ln = self.line(s, x - 0.5, yy, x + w + 0.5, yy, color=col, width=1.0)
            self.glow(ln, col, radius=3, alpha=0.4)
        cx = x + w / 2
        for k in range(-5, 6):
            ln = self.line(s, cx + k * 0.12, horizon, cx + k * w * 0.22, y + h, color=col, width=1.0)
            self.glow(ln, col, radius=3, alpha=0.4)

    def deco_pixels(self, s, x, y, w, h, i, small):
        grid = ["..XX...XX..", ".XXXX.XXXX.", "XXXXXXXXXXX", "XXXXXXXXXXX", ".XXXXXXXXX.",
                "..XXXXXXX..", "...XXXXX...", "....XXX....", ".....X....."]
        cell = min(w / 13, h / 11) * (0.7 if small else 1)
        ox, oy = x + w - cell * 12, y + (h - cell * 10 if small else 0)
        for r, row in enumerate(grid):
            for c, ch in enumerate(row):
                if ch == "X":
                    self.shape(s, MSO_SHAPE.RECTANGLE, ox + c * cell, oy + r * cell, cell, cell,
                               fill=self.pal((r + c) // 4))
        if not small:
            for k in range(6):
                sz = cell * (1 + k % 2)
                self.shape(s, MSO_SHAPE.RECTANGLE, x + w * (0.08 + k * 0.13), y + h * (0.72 + (k % 3) * 0.07), sz, sz,
                           fill=self.pal(k))

    def deco_tape(self, s, x, y, w, h, i, small):
        if small:
            sp = self.shape(s, MSO_SHAPE.RECTANGLE, x, y + h * 0.3, w * 0.9, h * 0.22, fill=self.pal(1), rot=-12)
            self.alpha(sp, 0.7)
            return
        photo = self.shape(s, MSO_SHAPE.RECTANGLE, x + w * 0.18, y + h * 0.12, w * 0.62, h * 0.62, fill="FFFFFF",
                           rot=4)
        self.soft_shadow(photo, blur=8, dist=4, angle=100, alpha=0.3)
        inner = self.shape(s, MSO_SHAPE.RECTANGLE, x + w * 0.22, y + h * 0.16, w * 0.54, h * 0.44, fill=self.pal(0),
                           rot=4)
        self.alpha(inner, 0.85)
        for fx, fy, r, col in ((0.12, 0.08, -18, self.pal(2)), (0.66, 0.66, 14, self.pal(3))):
            t = self.shape(s, MSO_SHAPE.RECTANGLE, x + w * fx, y + h * fy, w * 0.3, h * 0.08, fill=col, rot=r)
            self.alpha(t, 0.75)
        note = self.shape(s, MSO_SHAPE.RECTANGLE, x + w * 0.02, y + h * 0.62, w * 0.36, w * 0.32, fill=self.pal(1),
                          rot=-7)
        self.soft_shadow(note, blur=6, dist=3, alpha=0.25)

    def deco_rules(self, s, x, y, w, h, i, small):
        col = self.accent_line or self.pal(0)
        if small:
            self.shape(s, MSO_SHAPE.RECTANGLE, x, y + h * 0.5, w, 0.06, fill=col)
            return
        for k, frac in enumerate((0.2, 0.5, 0.8)):
            self.line(s, x, y + h * frac, x + w, y + h * frac, color=self.black if k != 1 else col,
                      width=0.75 if k != 1 else 3)
        d = min(w, h) * 0.28
        self.shape(s, MSO_SHAPE.OVAL, x + w - d, y + h * 0.5 - d / 2, d, d, fill=col)

    def deco_circle(self, s, x, y, w, h, i, small):
        d = min(w, h) * (0.9 if small else 0.78)
        self.shape(s, MSO_SHAPE.OVAL, x + w - d, y + (h - d) / 2 if not small else y, d, d, fill=self.pal(0))
        if not small:
            self.shape(s, MSO_SHAPE.RECTANGLE, x, y + h * 0.82, w * 0.62, 0.18, fill=self.black)
            self.shape(s, MSO_SHAPE.RECTANGLE, x + w * 0.1, y + h * 0.1, 0.18, h * 0.5, fill=self.black)

    def deco_arches(self, s, x, y, w, h, i, small):
        d = min(w, h) * (0.95 if small else 0.9)
        cx, base = x + (w - d) / 2, y + (h - d / 2 if not small else h * 0.2)
        for k in range(4):
            dd = d * (1 - k * 0.22)
            arc = self.shape(s, MSO_SHAPE.BLOCK_ARC, cx + (d - dd) / 2, base - dd / 2 + (d - dd) / 2 * 0 + (d - dd) / 2,
                             dd, dd, fill=self.pal(k))
            arc.adjustments[0] = 180
            arc.adjustments[1] = 0
            arc.adjustments[2] = 0.11
        if not small:
            sun = min(w, h) * 0.18
            self.shape(s, MSO_SHAPE.OVAL, x + w * 0.08, y + h * 0.08, sun, sun, fill=self.pal(1))

    def deco_enso(self, s, x, y, w, h, i, small):
        d = min(w, h) * (0.9 if small else 0.7)
        arc = self.shape(s, MSO_SHAPE.BLOCK_ARC, x + (w - d) / 2, y + (h - d) / 2 * (0.4 if not small else 1), d, d,
                         fill=self.black)
        arc.adjustments[0] = 300
        arc.adjustments[1] = 250
        arc.adjustments[2] = 0.07
        self.alpha(arc, 0.85)
        if not small:
            st = self.shape(s, MSO_SHAPE.OVAL, x + w * 0.62, y + h * 0.72, w * 0.3, h * 0.14, fill=self.pal(0))
            self.alpha(st, 0.8)

    def deco_ornament(self, s, x, y, w, h, i, small):
        col = self.accent_line or self.black
        if small:
            self.shape(s, MSO_SHAPE.DIAMOND, x + w / 2 - 0.2, y + h / 2 - 0.2, 0.4, 0.4, fill=col)
            return
        self.shape(s, MSO_SHAPE.RECTANGLE, x, y, w, h, fill=None, line=col, lw=1.5)
        self.shape(s, MSO_SHAPE.RECTANGLE, x + 0.12, y + 0.12, w - 0.24, h - 0.24, fill=None, line=col, lw=0.5)
        for fx, fy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            self.shape(s, MSO_SHAPE.DIAMOND, x + fx * w - 0.16, y + fy * h - 0.16, 0.32, 0.32, fill=col)
        m = min(w, h) * 0.34
        self.shape(s, MSO_SHAPE.DIAMOND, x + w / 2 - m / 2, y + h / 2 - m / 2, m, m, fill=None, line=col, lw=1.0)
        self.shape(s, MSO_SHAPE.OVAL, x + w / 2 - m / 6, y + h / 2 - m / 6, m / 3, m / 3, fill=self.pal(0))

    def deco_hazard(self, s, x, y, w, h, i, small):
        if small:
            sp = self.shape(s, MSO_SHAPE.RECTANGLE, x, y + h * 0.4, w, h * 0.2, fill=(self.black, self.pal(0)),
                            pattern=MSO_PATTERN.WIDE_UPWARD_DIAGONAL)
            return sp
        cut = self.shape(s, MSO_SHAPE.SNIP_2_DIAG_RECTANGLE, x + w * 0.15, y + h * 0.08, w * 0.75, h * 0.55,
                         fill=None, line=self.pal(0), lw=2)
        self.glow(cut, self.pal(0), radius=6, alpha=0.5)
        self.shape(s, MSO_SHAPE.RECTANGLE, x, y + h * 0.75, w, h * 0.1, fill=(self.ground, self.pal(1)),
                   pattern=MSO_PATTERN.WIDE_UPWARD_DIAGONAL)
        for k in range(4):
            ln = self.line(s, x + w * 0.05, y + h * (0.68 + k * 0.025), x + w * (0.3 + k * 0.15),
                           y + h * (0.68 + k * 0.025), color=self.pal(k % 2), width=1.5)
            self.glow(ln, self.pal(k % 2), radius=3, alpha=0.5)

    def deco_scan(self, s, x, y, w, h, i, small):
        if small:
            return
        box = self.shape(s, MSO_SHAPE.RECTANGLE, x + w * 0.1, y + h * 0.1, w * 0.8, h * 0.62, fill=None,
                         line=self.pal(0), lw=1.25)
        self.glow(box, self.pal(0), radius=4, alpha=0.4)
        for k in range(8):
            yy = y + h * (0.16 + k * 0.065)
            ln = self.line(s, x + w * 0.16, yy, x + w * (0.3 + 0.5 * ((k * 37) % 10) / 10), yy, color=self.pal(k % 3),
                           width=2)
            self.alpha_line(ln, 0.85)
        self.deco_pixels(s, x, y + h * 0.55, w, h * 0.45, i, True)

    def deco_tiles(self, s, x, y, w, h, i, small):
        if small:
            sp = self.shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w * 0.8, h * 0.8, fill=self.pal(0))
            sp.adjustments[0] = 0.2
            return
        g = 0.14
        cells = [(0, 0, 2, 1), (2, 0, 1, 2), (0, 1, 1, 1), (1, 1, 1, 1), (0, 2, 3, 1)]
        cw, chh = (w - 2 * g) / 3, (h - 2 * g) / 3
        for k, (c, r, sw, sh) in enumerate(cells):
            sp = self.shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x + c * (cw + g), y + r * (chh + g),
                            cw * sw + g * (sw - 1), chh * sh + g * (sh - 1), fill=self.pal(k))
            sp.adjustments[0] = 0.12
            self.soft_shadow(sp, blur=10, dist=3, alpha=0.12)

    def deco_doodle(self, s, x, y, w, h, i, small):
        d = min(w, h) * (0.8 if small else 0.5)
        c = self.shape(s, MSO_SHAPE.OVAL, x + w * 0.4, y + h * 0.05, d, d, fill=None, line=self.black, lw=1.5,
                       rot=8)
        self.dash(c, "sysDash")
        if small:
            return
        arr = self.shape(s, MSO_SHAPE.CURVED_DOWN_ARROW, x + w * 0.05, y + h * 0.5, w * 0.4, h * 0.25, fill=None,
                         line=self.black, lw=1.25, rot=-10)
        self.dash(arr, "sysDot")
        star = self.shape(s, MSO_SHAPE.STAR_5_POINT, x + w * 0.66, y + h * 0.66, d * 0.5, d * 0.5, fill=None,
                          line=self.pal(0), lw=1.5, rot=-8)
        self.dash(star, "solid")
        box = self.shape(s, MSO_SHAPE.RECTANGLE, x + w * 0.1, y + h * 0.06, w * 0.3, h * 0.3, fill=self.pal(1),
                         rot=-5)
        self.alpha(box, 0.5)

    def deco_glass(self, s, x, y, w, h, i, small):
        self.deco_orbs(s, x, y, w, h, i, small)
        if small:
            return
        pane = self.shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x + w * 0.18, y + h * 0.26, w * 0.66, h * 0.46,
                          fill="FFFFFF", line="FFFFFF", lw=1)
        pane.adjustments[0] = 0.12
        self.alpha(pane, 0.28)
        self.alpha(pane, 0.75, which="line")
        self.soft_shadow(pane, blur=18, dist=6, alpha=0.18)

    def deco_neu(self, s, x, y, w, h, i, small):
        d = min(w, h) * (0.8 if small else 0.46)
        for k, (fx, fy) in enumerate(((0.45, 0.08), (0.12, 0.5)) if not small else ((0.1, 0.1),)):
            twin = self.shape(s, MSO_SHAPE.OVAL, x + w * fx, y + h * fy, d, d, fill=self.ground)
            self.soft_shadow(twin, blur=16, dist=8, angle=225, color="FFFFFF", alpha=0.9)
            sp = self.shape(s, MSO_SHAPE.OVAL, x + w * fx, y + h * fy, d, d, fill=self.ground)
            self.soft_shadow(sp, blur=16, dist=8, angle=45, color=mix(self.ground, "000000", 0.4), alpha=0.5)
            if k == 0:
                dot = d * 0.3
                self.shape(s, MSO_SHAPE.OVAL, x + w * fx + (d - dot) / 2, y + h * fy + (d - dot) / 2, dot, dot,
                           fill=self.pal(0))

    def deco_surreal(self, s, x, y, w, h, i, small):
        self.deco_orbs(s, x, y, w, h, i, small)
        if small:
            return
        arch = self.shape(s, MSO_SHAPE.FLOWCHART_DELAY, x + w * 0.25, y + h * 0.18, w * 0.42, h * 0.62,
                          fill=self.pal(1), rot=-90)
        self.gradient(arch, self.pal(1), self.pal(2), angle=90)
        eye = min(w, h) * 0.16
        self.shape(s, MSO_SHAPE.OVAL, x + w * 0.38, y + h * 0.4, eye * 1.8, eye, fill="FFFFFF")
        self.shape(s, MSO_SHAPE.OVAL, x + w * 0.38 + eye * 0.55, y + h * 0.4 + eye * 0.15, eye * 0.7, eye * 0.7,
                   fill=self.black)
        stair_w = w * 0.12
        for k in range(4):
            self.shape(s, MSO_SHAPE.RECTANGLE, x + w * 0.62 + k * stair_w * 0.6, y + h * (0.84 - k * 0.08),
                       stair_w, h * 0.08 * (k + 1), fill=self.pal(3))
