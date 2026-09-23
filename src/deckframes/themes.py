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
