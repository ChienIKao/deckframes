"""Theme / template lookup.

Search order for a name (first hit wins):
  1. an explicit file or directory path
  2. ./themes/<name>.json            (project-local)
  3. ~/.deckframes/themes/<name>.json (user library, where `themes import` writes)
  4. built-in themes shipped with the package
Templates follow the same pattern with ./templates/<name>/ and ~/.deckframes/templates/<name>/.
"""
from __future__ import annotations

import json
from pathlib import Path

BUILTIN = Path(__file__).resolve().parent / "themes"
USER_HOME = Path.home() / ".deckframes"
DEFAULT_THEME = "blockframe"


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def theme_dirs(cwd: Path | None = None):
    cwd = cwd or Path.cwd()
    return [cwd / "themes", USER_HOME / "themes", BUILTIN]


def resolve_theme(ref: str | None, cwd: Path | None = None) -> tuple[dict, Path] | tuple[None, None]:
    if not ref:
        return None, None
    p = Path(ref)
    if p.suffix == ".json" and p.exists():
        return _load(p), p
    for d in theme_dirs(cwd):
        f = d / f"{ref}.json"
        if f.exists():
            return _load(f), f
    raise SystemExit(f"theme not found: {ref}  (try `deckframes themes list`)")


def list_themes(cwd: Path | None = None) -> list[dict]:
    seen, out = set(), []
    for d in theme_dirs(cwd):
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.json")):
            if f.stem in seen:
                continue
            seen.add(f.stem)
            t = _load(f)
            out.append({"name": f.stem, "engine": t.get("engine", "template"),
                        "description": t.get("description", ""), "path": str(f),
                        "source": "builtin" if d == BUILTIN else ("user" if d.parent == USER_HOME else "project")})
    return out


def resolve_template(ref: str | None, cwd: Path | None = None):
    """Returns (template_path | None, config dict)."""
    if not ref:
        return None, {}
    cwd = cwd or Path.cwd()
    p = Path(ref)
    if p.is_file():
        side = p.with_suffix(".json")
        return p, (_load(side) if side.exists() else {})
    for d in (p, cwd / "templates" / ref, USER_HOME / "templates" / ref):
        if d.is_dir():
            cfg = _load(d / "config.json") if (d / "config.json").exists() else {}
            tpl = d / cfg["file"] if cfg.get("file") else None
            if not tpl or not tpl.exists():
                cands = sorted(d.glob("*.pptx")) + sorted(d.glob("*.potx"))
                tpl = cands[0] if cands else None
            if tpl:
                return tpl, cfg
    raise SystemExit(f"template not found: {ref}")


EDIT_HINTS = {
    "colors.ground": "slide background",
    "colors.text / colors.black": "body text / outlines and connectors (usually the same dark colour)",
    "colors.muted": "secondary text",
    "colors.palette": "2–5 accent fills cycled by components; the 4th light one is the highlighter",
    "colors.chapter_cycle": "chapter colours for dividers and the nav band (defaults to palette)",
    "fonts": "display = Latin headlines, label = pills, body, ea = CJK font, code",
    "stroke": "border / thin = outline pt (0 = none); shadow / thin_shadow = hard shadow offset pt (0 = none)",
    "decorations / tilt": "star bursts, stripe tiles, dot grid / rotated cards on or off",
    "sizes": "title, subtitle, body_max, body_min, split_below in pt",
}


def new_theme(name: str, base: str = DEFAULT_THEME, dest: Path | None = None, force: bool = False) -> Path:
    """Scaffold an editable theme JSON by copying `base`."""
    import copy
    import re

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        raise SystemExit("theme names use lowercase letters, digits and hyphens (e.g. my-lab)")
    theme, _ = resolve_theme(base)
    t = copy.deepcopy(theme)
    t.pop("source", None)
    t = {"name": name, "description": f"Custom theme based on {base} — describe the look here",
         "based_on": base, **{k: v for k, v in t.items() if k not in ("name", "description")},
         "_edit": EDIT_HINTS}
    dest = dest or USER_HOME / "themes" / f"{name}.json"
    if dest.exists() and not force:
        raise SystemExit(f"{dest} already exists (use --force to overwrite)")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(t, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dest
