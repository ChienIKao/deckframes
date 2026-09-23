"""Convert a HyperFrames design preset (FRAME.md) into a deckframes canvas theme.

FRAME.md front matter is free-form across presets (colour keys differ, borders /
shadows are optional), so tokens are classified by role heuristics:

  ground  – the lightest low-saturation colour (or a key named bg/ground/paper/cream…)
  ink     – the darkest colour (or ink/black/text-primary)
  muted   – a mid-luminance grey (or gray/muted/text-secondary), else derived
  palette – remaining saturated colours, most saturated first (max 5)

Web fonts are mapped to fonts that ship with Windows/Office so decks don't reflow
on another machine; CJK text always uses Microsoft JhengHei.
"""
from __future__ import annotations

import colorsys
import re
from pathlib import Path

import yaml

HEX = re.compile(r"#([0-9a-fA-F]{6})\b")
PX = re.compile(r"([\d.]+)px")

PRESET_DIRS = [
    Path.home() / ".claude" / "skills" / "hyperframes-creative" / "frame-presets",
    Path.home() / ".agents" / "skills" / "hyperframes-creative" / "frame-presets",
    Path.cwd() / ".agents" / "skills" / "hyperframes-creative" / "frame-presets",
    Path.cwd() / ".claude" / "skills" / "hyperframes-creative" / "frame-presets",
]

SERIF = ("serif", "bodoni", "playfair", "garamond", "newsreader", "georgia", "instrument", "fraunces", "lora",
         "dm serif", "libre", "cormorant", "source serif", "merriweather", "crimson")
MONO = ("mono", "code", "courier")
CONDENSED = ("bebas", "oswald", "anton", "league gothic", "barlow condensed")
HEAVY = ("archivo black", "shrikhand", "black", "inter", "space grotesk", "grotesk", "manrope", "sora", "syne")


def find_preset(name: str) -> Path | None:
    for d in PRESET_DIRS:
        f = d / name / "FRAME.md"
        if f.exists():
            return f
    return None


def _front_matter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    body = re.sub(r"^(\s*[\w-]+):\{", r"\1: {", m.group(1), flags=re.M)  # `key:{…}` isn't valid YAML
    try:
        return yaml.safe_load(body) or {}
    except yaml.YAMLError:
        return _front_matter_loose(body)


def _front_matter_loose(body: str) -> dict:
    """Fallback for front matter YAML can't parse: pull out the blocks we need line by line."""
    out: dict = {}
    section = None
    for line in body.splitlines():
        top = re.match(r"^([\w-]+):\s*(.*)$", line)
        if top:
            section = top.group(1)
            if top.group(2):
                out[section] = top.group(2).strip().strip('"')
            else:
                out[section] = {}
            continue
        kv = re.match(r"^\s+([\w-]+):\s*(.+)$", line)
        if kv and isinstance(out.get(section), dict):
            key, val = kv.group(1), kv.group(2).strip()
            fam = re.search(r'fontFamily:\s*"([^"]+)"', val)
            out[section][key] = {"fontFamily": fam.group(1)} if fam else val.strip('"')
    return out


def _hsl(hex_: str):
    """(luminance, chroma, lightness) — chroma (max−min) keeps creams/greys 'neutral' where HLS saturation doesn't."""
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (0, 2, 4))
    _, l, _ = colorsys.rgb_to_hls(r, g, b)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return lum, max(r, g, b) - min(r, g, b), l


def _map_font(family: str | None, role: str) -> str:
    f = (family or "").lower()
    if any(k in f for k in MONO):
        return "Consolas"
    if any(k in f for k in SERIF):
        return "Georgia"
    if role == "display":
        if any(k in f for k in CONDENSED):
            return "Impact"
        if any(k in f for k in HEAVY):
            return "Arial Black"
        return "Arial"
    if role == "label":
        return "Bahnschrift"
    return "Arial"


def _px(value) -> float | None:
    m = PX.search(str(value or ""))
    return float(m.group(1)) if m else None


def _shadow_px(value) -> float:
    """Hard offset shadows only: `8px 8px 0 black` → 8. Blurred shadows → 0."""
    nums = [float(t[:-2] if t.endswith("px") else t) for t in str(value or "").split()
            if re.fullmatch(r"-?[\d.]+(px)?", t)]
    if len(nums) < 2 or (len(nums) >= 3 and nums[2] > 0):
        return 0.0
    return abs(nums[0])


def _describe(desc: str) -> str:
    """FRAME.md descriptions open with boilerplate; keep the part that describes the look."""
    d = " ".join(desc.split())
    m = re.search(r"sacred\s*[—-]+\s*(.+)", d)
    return (m.group(1) if m else d)[:160]


def import_frame(path: Path, name: str | None = None) -> tuple[dict, list[str]]:
    text = path.read_text(encoding="utf-8")
    fm = _front_matter(text)
    notes: list[str] = []
    raw = fm.get("colors") or {}
    colors = {}
    for k, v in raw.items():
        m = HEX.search(str(v))
        if m:
            colors[str(k)] = m.group(1).upper()
    if len(colors) < 3:
        raise SystemExit(f"{path}: fewer than 3 hex colours in front matter — cannot build a theme")

    info = {k: (v, *_hsl(v)) for k, v in colors.items()}  # key → (hex, lum, sat, light)

    def pick(keys, pred=None, order=None):
        for k in colors:
            if any(w in k.lower() for w in keys) and (pred is None or pred(info[k])):
                return k
        cands = [k for k in colors if pred is None or pred(info[k])]
        return sorted(cands, key=order)[0] if cands and order else None

    ground = pick(("offwhite", "ground", "bg-primary", "background", "paper", "cream", "canvas", "bg"),
                  pred=lambda t: t[1] > 0.75 and t[2] < 0.2, order=lambda k: -info[k][1])
    ink = pick(("ink", "black", "text-primary", "text", "outline"), pred=lambda t: t[1] < 0.2,
               order=lambda k: info[k][1])
    if ground is None:
        ground = max(colors, key=lambda k: info[k][1])
        notes.append(f"no light neutral found; using lightest colour '{ground}' as ground")
    if ink is None:
        ink = min(colors, key=lambda k: info[k][1])
    used = {ground, ink}
    muted = pick(("gray", "grey", "muted", "text-secondary", "secondary"),
                 pred=lambda t: 0.25 < t[1] < 0.7 and t[2] < 0.12, order=None)
    if muted:
        used.add(muted)
    palette = [k for k in colors if k not in used and colors[k] not in ("FFFFFF",)
               and not re.search(r"dark|deep|overlay|line|shadow", k.lower())]
    palette.sort(key=lambda k: -info[k][2])
    uniq, seen = [], set()
    for k in palette:
        if colors[k] not in seen:
            uniq.append(colors[k])
            seen.add(colors[k])
    palette = uniq[:5]
    if len(palette) < 2:
        notes.append("fewer than 2 accent colours; padded with ink/ground tints")
        palette += [colors[ink], colors[ground]][: 2 - len(palette)]

    borders = fm.get("borders") or {}
    shadows = fm.get("shadows") or {}
    if isinstance(borders, dict):
        bpx = _px(borders.get("primary")) or next((v for v in map(_px, borders.values()) if v), 0.0)
        tpx = _px(borders.get("thin")) or bpx * 0.75
    else:
        bpx = _px(borders) or 0.0
        tpx = bpx * 0.75
    spx = _shadow_px(shadows.get("default") if isinstance(shadows, dict) else shadows)
    tspx = _shadow_px(shadows.get("small") if isinstance(shadows, dict) else None) or spx / 2
    brutal = bpx >= 2 and spx >= 4
    if bpx == 0:  # no outline in the source: keep cards legible with a hairline in ink
        bpx = tpx = 1.5
        notes.append("no border token; using a 0.75pt hairline for cards")

    typo = fm.get("typography") or {}

    entries = {str(k): v for k, v in typo.items() if isinstance(v, dict) and v.get("fontFamily")}

    def family(keys):
        for want in keys:
            for k, v in entries.items():
                if k == want or k.startswith(want + "-"):
                    return v["fontFamily"]
        return None

    def size(v):
        try:
            return float(v.get("cqw") or 0)
        except (TypeError, ValueError):
            return 0.0

    display_src = max(entries.values(), key=size)["fontFamily"] if entries else None  # largest ramp step
    body_src = family(("body",)) or display_src
    label_src = family(("label", "caption", "micro", "pill-text")) or body_src
    theme = {
        "name": name or path.parent.name,
        "engine": "canvas",
        "description": _describe(fm.get("description") or ""),
        "source": f"HyperFrames preset {path.parent.name} (imported by `deckframes themes import`)",
        "colors": {
            "black": colors[ink], "white": "FFFFFF", "ground": colors[ground], "text": colors[ink],
            "muted": colors[muted] if muted else "7A7A7A", "palette": palette, "chapter_cycle": palette,
        },
        "fonts": {
            "display": _map_font(display_src, "display"), "label": _map_font(label_src, "label"),
            "body": _map_font(body_src, "body"), "ea": "Microsoft JhengHei", "code": "Consolas",
        },
        "stroke": {"border": round(bpx / 2, 2), "shadow": round(spx / 2, 2),
                   "thin": round(tpx / 2, 2), "thin_shadow": round(tspx / 2, 2)},
        "decorations": brutal,
        "tilt": brutal,
        "sizes": {"title": 28, "subtitle": 16, "body_max": 20, "body_min": 12, "split_below": 14},
    }
    notes.append(f"fonts: display {display_src!r}→{theme['fonts']['display']}, body {body_src!r}→{theme['fonts']['body']}")
    notes.append(f"stroke: border {bpx}px→{theme['stroke']['border']}pt, hard shadow {spx}px→{theme['stroke']['shadow']}pt; "
                 f"decorations {'on' if brutal else 'off'}")
    return theme, notes
