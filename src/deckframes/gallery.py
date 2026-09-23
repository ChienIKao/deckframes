"""Theme gallery: render the same sample deck in every theme and tile the results.

One row per theme: label column + cover, chapter divider, content slide (nav bar + cards),
stats slide. `--presets` also includes every HyperFrames design preset found on the machine
(imported on the fly, nothing is saved).
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .frame_import import PRESET_DIRS, import_frame
from .markdown import parse_markdown
from .preview import render
from .themes import list_themes, resolve_theme

SAMPLE = """---
eyebrow: THEME PREVIEW
subtitle: deckframes theme gallery
author: Speaker
date: 2026
closing: Q&A
---

# 主題預覽 Theme Preview

## 緒論 | Introduction

### 背景

#### 三個重點

說明文字與==重點強調==。

- 第一個條列
- 第二個條列

```cards stack
- 卡片一 | 範例說明文字 | tag: 標籤
- 卡片二 | 範例說明文字
- 卡片三 | 範例說明文字
```

### 方法

#### 流程

```flow
- 輸入
- 處理
- 輸出
```

## 結果 | Results

### 數據

#### 關鍵數字

```stats
- 42 | 範例數字 | 示意
- 3× | 範例倍數 | 示意
- 99% | 範例比例 | 示意
```
"""

CANVAS_PICK = [1, 3, 4, 7]    # cover, chapter divider, content + nav, stats
TEMPLATE_PICK = [1, 3, 4, 6]

FONT_CANDIDATES = ["msjh.ttc", "msjhbd.ttc", "C:/Windows/Fonts/msjh.ttc", "NotoSansCJK-Regular.ttc",
                   "/System/Library/Fonts/PingFang.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                   "arial.ttf", "DejaVuSans.ttf"]


def _font(size: int, bold: bool = False):
    names = (["msjhbd.ttc", "C:/Windows/Fonts/msjhbd.ttc"] if bold else []) + FONT_CANDIDATES
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _presets(known: set[str]):
    seen = set()
    for d in PRESET_DIRS:
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*/FRAME.md")):
            name = f.parent.name
            if name in known or name in seen:
                continue
            seen.add(name)
            yield name, f


def _build(theme: dict, out: Path):
    doc = parse_markdown(SAMPLE)
    if theme.get("engine") == "canvas":
        from .engines.canvas import build_canvas
        prs, _ = build_canvas(doc, theme, out.parent)
    else:
        from .engines.template import build_template
        prs, _ = build_template(doc, None, {}, theme, out.parent)
    prs.save(out)


def gallery(out: Path, presets: bool = False, backend: str = "auto", names: list[str] | None = None) -> dict:
    rows = []
    for t in list_themes():
        if names and t["name"] not in names:
            continue
        theme, _ = resolve_theme(t["name"])
        rows.append({"name": t["name"], "source": t["source"], "engine": t["engine"],
                     "description": t["description"], "theme": theme})
    if presets:
        for name, f in _presets({r["name"] for r in rows}):
            if names and name not in names:
                continue
            try:
                theme, _ = import_frame(f, name)
            except SystemExit as e:
                print(f"  · skip {name}: {e}", file=sys.stderr)
                continue
            rows.append({"name": name, "source": "hyperframes (import)", "engine": "canvas",
                         "description": theme["description"], "theme": theme})

    w, h, gap, label_w = 400, 225, 8, 300
    tiles = []
    with tempfile.TemporaryDirectory() as tmp:
        for r in rows:
            pptx = Path(tmp) / f"{r['name']}.pptx"
            _build(r["theme"], pptx)
            res = render(pptx, Path(tmp) / f"{r['name']}_png", backend=backend)
            pick = CANVAS_PICK if r["engine"] == "canvas" else TEMPLATE_PICK
            files = res["slides"]
            tiles.append([Image.open(files[min(i, len(files)) - 1]).convert("RGB").resize((w, h)) for i in pick])
            print(f"  ✔ {r['name']}", file=sys.stderr)

    cols = len(CANVAS_PICK)
    sheet = Image.new("RGB", (label_w + cols * (w + gap) + gap, len(rows) * (h + gap) + gap), "#2B2B2B")
    draw = ImageDraw.Draw(sheet)
    f_name, f_meta = _font(30, bold=True), _font(17)
    for k, (r, imgs) in enumerate(zip(rows, tiles)):
        y = gap + k * (h + gap)
        draw.text((20, y + 20), r["name"], font=f_name, fill="#FFFFFF")
        draw.text((20, y + 64), f"{r['engine']} · {r['source']}", font=f_meta, fill="#BBBBBB")
        desc, line, lines = r["description"] or "", "", []
        for ch in desc:
            if draw.textlength(line + ch, font=f_meta) > label_w - 36:
                lines.append(line)
                line = ""
            line += ch
        lines.append(line)
        for j, ln in enumerate(lines[:5]):
            draw.text((20, y + 96 + j * 24), ln, font=f_meta, fill="#DDDDDD")
        for c, im in enumerate(imgs):
            sheet.paste(im, (label_w + gap + c * (w + gap), y))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return {"file": str(out), "themes": [{k: r[k] for k in ("name", "engine", "source")} for r in rows]}


if __name__ == "__main__":
    print(json.dumps(gallery(Path("gallery.png"), presets=True), indent=2))
