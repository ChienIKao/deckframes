"""Icons: Font Awesome Free (fetched on demand, cached) and SVG files, embedded as vector SVG.

Icon references (used by `icon:` on infographic items):
  users | fa:users | fa-users | fa-solid fa-users | regular:clock | brands:github
  assets/logo.svg  (any SVG / PNG / JPG path, relative to deck.md)
Plain ASCII glyphs (`?`, `1`, `A`) still render as text. Emoji are rejected (see markdown.find_emoji).

SVGs are embedded the way PowerPoint 2016+ does it: a PNG fallback blip plus an `svgBlip`
extension, so the icon stays crisp (and can be "Converted to Shape") in PowerPoint while older
viewers show the PNG. Font Awesome SVGs keep their licence comment (CC BY 4.0 attribution).
"""
from __future__ import annotations

import io
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from lxml import etree
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import Part
from pptx.oxml.ns import qn

from .themes import USER_HOME

FA_VERSION = "6.7.2"
CDN = f"https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@{FA_VERSION}"
CACHE = USER_HOME / "icons" / f"fontawesome-{FA_VERSION}"
STYLES = ("solid", "regular", "brands")
STYLE_ALIASES = {"fas": "solid", "fa-solid": "solid", "solid": "solid", "far": "regular", "fa-regular": "regular",
                 "regular": "regular", "fab": "brands", "fa-brands": "brands", "brands": "brands"}
SVG_EXT_URI = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
ASVG_NS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"


class IconError(Exception):
    pass


# --------------------------------------------------------------------------- references


def parse_ref(ref: str):
    """→ ("file", path) | ("fa", style | None, name) | ("text", glyph)"""
    s = ref.strip()
    if re.search(r"\.(svg|png|jpe?g|gif)$", s, re.I):
        return ("file", s)
    low = s.lower()
    if re.fullmatch(r"[a-z0-9:/ -]+", s) and re.search(r"[a-z]", s) and len(s) >= 2:
        tokens = [t for t in re.split(r"[\s:/]+", low) if t]
        style = next((STYLE_ALIASES[t] for t in tokens if t in STYLE_ALIASES), None)
        names = [t for t in tokens if t not in STYLE_ALIASES and t not in ("fa", "font-awesome")]
        if names:
            name = names[-1]
            name = name[3:] if name.startswith("fa-") else name
            return ("fa", style, name)
    return ("text", s)


# --------------------------------------------------------------------------- Font Awesome


def _download(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise FileNotFoundError(url) from e
        raise IconError(f"download failed ({e.code}): {url}") from e
    except urllib.error.URLError as e:
        raise IconError(f"cannot reach {CDN} ({e.reason}); icons already used once are cached in {CACHE}") from e


def metadata() -> dict:
    """{name: {"label", "styles", "terms"}} for all Font Awesome Free icons (cached)."""
    cached = CACHE / "icons.json"
    if cached.exists():
        return json.loads(cached.read_text(encoding="utf-8"))
    import yaml
    raw = yaml.safe_load(_download(f"{CDN}/metadata/icons.yml").decode("utf-8"))
    meta = {k: {"label": v.get("label", k), "styles": v.get("styles", []),
                "terms": [str(t) for t in (v.get("search") or {}).get("terms", []) or []]}
            for k, v in raw.items()}
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return meta


def fa_svg(name: str, style: str | None = None) -> tuple[bytes, str]:
    """SVG bytes for a Font Awesome Free icon; tries solid → regular → brands unless a style is given."""
    for st in ([style] if style else list(STYLES)):
        f = CACHE / st / f"{name}.svg"
        if f.exists():
            return f.read_bytes(), st
        try:
            data = _download(f"{CDN}/svgs/{st}/{name}.svg")
        except FileNotFoundError:
            continue
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        return data, st
    hint = f" in style '{style}'" if style else ""
    raise IconError(f"unknown Font Awesome icon '{name}'{hint} — try `deckframes icons search {name}`")


def search(query: str, limit: int = 20) -> list[dict]:
    q = query.lower().strip()
    scored = []
    for name, m in metadata().items():
        terms = [t.lower() for t in m["terms"]]
        if name == q:
            s = 0
        elif name.startswith(q):
            s = 1
        elif q in name:
            s = 2
        elif q in terms:
            s = 3
        elif any(q in t for t in terms) or q in m["label"].lower():
            s = 4
        else:
            continue
        scored.append((s, len(name), name, m))
    scored.sort()
    return [{"name": n, "styles": m["styles"], "label": m["label"]} for _, _, n, m in scored[:limit]]


# --------------------------------------------------------------------------- SVG helpers


def resolve(ref: str, base: Path) -> tuple[str, bytes, bool]:
    """→ (kind, data, recolourable) where kind is 'svg' | 'raster'."""
    kind = parse_ref(ref)
    if kind[0] == "fa":
        data, _ = fa_svg(kind[2], kind[1])
        return "svg", data, True
    if kind[0] == "file":
        p = Path(kind[1])
        p = p if p.is_absolute() else base / p
        if not p.exists():
            raise IconError(f"icon file not found: {kind[1]}")
        return ("svg" if p.suffix.lower() == ".svg" else "raster"), p.read_bytes(), False
    raise IconError(f"not an icon reference: {ref}")


def recolor(svg: bytes, hex_: str) -> bytes:
    """Monochrome icons (Font Awesome) take the fill from the root element."""
    txt = svg.decode("utf-8")
    txt = re.sub(r"<svg\b", f'<svg fill="#{hex_.lstrip("#")}"', txt, count=1)
    return txt.encode("utf-8")


def svg_aspect(svg: bytes) -> float:
    m = re.search(rb'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', svg)
    if m:
        return float(m.group(1)) / float(m.group(2))
    w = re.search(rb'\bwidth="([\d.]+)', svg)
    h = re.search(rb'\bheight="([\d.]+)', svg)
    return float(w.group(1)) / float(h.group(1)) if w and h else 1.0


def rasterize(svg: bytes, px: int = 256) -> bytes:
    try:
        import pymupdf
    except ImportError:  # older installs
        import fitz as pymupdf
    page = pymupdf.open(stream=svg, filetype="svg")[0]
    zoom = px / max(page.rect.width, page.rect.height)
    return page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=True).tobytes("png")


def add_svg_picture(slide, svg: bytes, x: int, y: int, w: int, h: int, descr: str = ""):
    """Insert an SVG as a native PowerPoint vector picture (PNG fallback + svgBlip)."""
    png = rasterize(svg, 512)
    pic = slide.shapes.add_picture(io.BytesIO(png), x, y, w, h)
    package = slide.part.package
    part = Part(package.next_image_partname("svg"), "image/svg+xml", package, svg)
    rid = slide.part.relate_to(part, RT.IMAGE)
    blip = pic._element.find(".//" + qn("a:blip"))
    ext_lst = blip.find(qn("a:extLst"))
    if ext_lst is None:
        ext_lst = etree.SubElement(blip, qn("a:extLst"))
    ext = etree.SubElement(ext_lst, qn("a:ext"), uri=SVG_EXT_URI)
    svg_blip = etree.SubElement(ext, f"{{{ASVG_NS}}}svgBlip", nsmap={"asvg": ASVG_NS})
    svg_blip.set(qn("r:embed"), rid)
    pic._element.nvPicPr.cNvPr.set("descr", descr)
    return pic
