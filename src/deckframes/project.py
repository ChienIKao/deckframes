"""Deck projects: a folder with deck.md + assets/ + deck.json (resumable state).

deck.json is the hand-off contract between agents: any agent (Claude Code, Codex,
Cursor…) that opens the folder reads it to know the chosen theme, workflow,
content mode and which stages are done — so work can resume without re-asking.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import shutil
from pathlib import Path

STATE = "deck.json"
STAGES = ["brief", "draft", "built", "checked", "reviewed"]

STARTER = """---
theme: {theme}
eyebrow: PRESENTATION
subtitle: English subtitle
author: Speaker name
date: {date}
---

# Deck title

## Chapter one | Chapter One

### Section

#### First slide

- Point one
- Point two

## Chapter two | Chapter Two

### Section

#### Key numbers

```stats
- — value — | Label | Where this number comes from
```
"""


HANDOFF = """# deckframes project

This folder is a deckframes deck (Markdown → editable PowerPoint). Any coding agent can continue it.

1. Run `deckframes status` — it prints the theme, workflow, content mode, finished stages and the next step.
2. Edit only `deck.md` (`source.md` is the untouched original). Never hand-edit the .pptx.
3. Loop: `deckframes build` → `deckframes check` (fix until 0 issues) → `deckframes preview` (inspect grid.png).
4. Record progress: `deckframes status --set draft|reviewed`.
5. Never invent numbers; in `verbatim` mode never reword the user's text.

If the deckframes skills are installed, load `deckframes` for the full workflow.
Install the CLI: `uv tool install git+https://github.com/ChienIKao/deckframes`.
"""


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\-]+", "-", text.strip().lower()).strip("-")
    return s or "deck"


def find_project(start: Path) -> Path | None:
    for d in [start, *start.parents]:
        if (d / STATE).exists():
            return d
    return None


def load_state(root: Path) -> dict:
    return json.loads((root / STATE).read_text(encoding="utf-8"))


def save_state(root: Path, state: dict) -> None:
    (root / STATE).write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mark(root: Path, stage: str, value: bool = True) -> None:
    st = load_state(root)
    st.setdefault("status", {})[stage] = value
    if value and stage in STAGES:  # later stages become stale when an earlier one is redone
        for later in STAGES[STAGES.index(stage) + 1:]:
            st["status"][later] = False
    save_state(root, st)


def init(root: Path, source: Path | None, theme: str, template: str | None, workflow: str, mode: str) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    if (root / STATE).exists():
        raise SystemExit(f"{root / STATE} already exists — use `deckframes status` to resume")
    (root / "assets").mkdir(exist_ok=True)
    (root / "output").mkdir(exist_ok=True)
    today = dt.date.today().isoformat()
    if source:
        shutil.copyfile(source, root / "source.md")
        if not (root / "deck.md").exists():
            shutil.copyfile(source, root / "deck.md")
        src_assets = source.parent / "assets"
        if src_assets.is_dir():
            shutil.copytree(src_assets, root / "assets", dirs_exist_ok=True)
    elif not (root / "deck.md").exists():
        (root / "deck.md").write_text(STARTER.format(theme=theme, date=today), encoding="utf-8")
    if not (root / "AGENTS.md").exists():
        (root / "AGENTS.md").write_text(HANDOFF, encoding="utf-8")
    slug = slugify(root.resolve().name)
    state = {
        "deckframes": 1,
        "name": slug,
        "created": today,
        "workflow": workflow,
        "theme": None if template else theme,
        "template": template,
        "mode": mode,
        "source": "source.md" if source else None,
        "deck": "deck.md",
        "output": f"output/{slug}.pptx",
        "status": {s: False for s in STAGES} | {"brief": True},
        "notes": [],
    }
    save_state(root, state)
    return state


def next_step(state: dict) -> str:
    st = state.get("status", {})
    if not st.get("draft"):
        return ("draft: normalise deck.md (hierarchy, English chapter subtitles, infographic blocks), "
                "then `deckframes status --set draft`")
    if not st.get("built"):
        return "build: `deckframes build`"
    if not st.get("checked"):
        return "check: `deckframes check` until 0 issues"
    if not st.get("reviewed"):
        return "review: `deckframes preview` and inspect grid.png, then `deckframes status --set reviewed`"
    return "done: report deliverables to the user"
