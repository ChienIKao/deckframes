"""deckframes command-line interface.

  deckframes init [DIR] [--from SOURCE.md] [--theme T | --template T] [--workflow W] [--mode M]
  deckframes build [DECK.md] [-o OUT.pptx] [--theme T] [--template T] [--assets DIR]
  deckframes check [DECK.pptx] [--json] [--no-outline]
  deckframes preview [DECK.pptx] [--out DIR] [--cols N] [--backend auto|powerpoint|libreoffice]
  deckframes status [--set STAGE | --unset STAGE] [--json]
  deckframes themes list | show NAME | import FRAME.md|PRESET [--name N] [--out PATH]
  deckframes themes gallery [--presets] [--only a,b] [--out gallery.png]
  deckframes themes new NAME [--from BASE] [--project | --out PATH] [--force]
  deckframes template inspect FILE.pptx [--write-config config.json]
  deckframes doctor

Inside a project folder (one containing deck.json) DECK/OUT arguments default
from deck.json, so agents can simply run `deckframes build && deckframes check`.
"""
from __future__ import annotations

import argparse
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from . import project as proj
from .themes import DEFAULT_THEME, USER_HOME, list_themes, resolve_template, resolve_theme


def _version() -> str:
    try:
        return version("deckframes")
    except PackageNotFoundError:
        return "dev"


def _project(path: Path | None = None):
    root = proj.find_project((path or Path.cwd()).resolve())
    return (root, proj.load_state(root)) if root else (None, None)


# --------------------------------------------------------------------------- commands


WORKFLOWS = {"deckframes-general": "deckframes-general", "general": "deckframes-general",
             "deckframes-academic-defense": "deckframes-academic-defense",
             "academic-defense": "deckframes-academic-defense", "academic": "deckframes-academic-defense"}


def cmd_init(a):
    if a.workflow not in WORKFLOWS:
        raise SystemExit(f"unknown workflow '{a.workflow}' — use deckframes-general or deckframes-academic-defense")
    a.workflow = WORKFLOWS[a.workflow]
    root = Path(a.dir).resolve()
    src = Path(a.source).resolve() if a.source else None
    if src and not src.exists():
        raise SystemExit(f"source not found: {src}")
    state = proj.init(root, src, a.theme, a.template, a.workflow, a.mode)
    print(f"✔ project {root}")
    print(f"  deck:     {root / state['deck']}")
    print(f"  output:   {root / state['output']}")
    print(f"  next:     {proj.next_step(state)}")


def cmd_build(a):
    from .markdown import parse_markdown

    root, state = _project(Path(a.deck).parent if a.deck else None)
    deck = Path(a.deck) if a.deck else (root / state["deck"] if root else None)
    if deck is None or not deck.exists():
        raise SystemExit("no deck given and no deck.json found — pass DECK.md or run `deckframes init`")
    deck = deck.resolve()
    doc = parse_markdown(deck.read_text(encoding="utf-8"))
    out = Path(a.output) if a.output else (root / state["output"] if root else deck.with_suffix(".pptx"))
    cwd = root or deck.parent

    tpl_ref = a.template or doc.meta.get("template") or (state or {}).get("template")
    tpl_path, cfg = resolve_template(tpl_ref, cwd)
    theme_ref = a.theme or doc.meta.get("theme") or (state or {}).get("theme") or cfg.get("theme_ref") \
        or (None if tpl_path else DEFAULT_THEME)
    theme, _ = resolve_theme(theme_ref, cwd) if theme_ref else (None, None)
    if cfg.get("theme"):
        theme = {**(theme or {}), **cfg["theme"]}
    base = Path(a.assets).resolve() if a.assets else deck.parent

    if theme and theme.get("engine") == "canvas" and tpl_path is None:
        from .engines.canvas import build_canvas
        prs, eng = build_canvas(doc, theme, base)
        engine = f"canvas/{theme.get('name', theme_ref)}"
    else:
        from .engines.template import build_template
        prs, eng = build_template(doc, tpl_path, cfg, theme, base)
        engine = f"template/{tpl_path.name if tpl_path else theme_ref}"
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    print(f"✔ {out}  ({len(prs.slides)} slides, {engine})")
    for w in eng.warnings:
        print("  ⚠", w)
    if root:
        proj.mark(root, "built")


def cmd_check(a):
    from .check import check, format_report

    root, state = _project()
    target = Path(a.pptx) if a.pptx else (root / state["output"] if root else None)
    if target is None or not target.exists():
        raise SystemExit("no .pptx given and no built output found")
    report = check(target)
    print(json.dumps(report, ensure_ascii=False, indent=2) if a.json else format_report(report, not a.no_outline))
    if root and not a.pptx:
        proj.mark(root, "checked", report["ok"])
    sys.exit(0 if report["ok"] else 1)


def cmd_preview(a):
    from .preview import render

    root, state = _project()
    target = Path(a.pptx) if a.pptx else (root / state["output"] if root else None)
    if target is None or not target.exists():
        raise SystemExit("no .pptx given and no built output found")
    res = render(target, Path(a.out) if a.out else None, a.cols, a.backend)
    print(f"✔ {len(res['slides'])} slides rendered with {res['backend']}")
    print(f"  grid:   {res['grid']}")
    print(f"  slides: {res['dir']}")


def cmd_status(a):
    root, state = _project()
    if not root:
        raise SystemExit("not inside a deckframes project (no deck.json found)")
    for stage in a.set or []:
        proj.mark(root, stage, True)
    for stage in a.unset or []:
        proj.mark(root, stage, False)
    state = proj.load_state(root)
    if a.json:
        print(json.dumps({**state, "root": str(root), "next": proj.next_step(state)}, ensure_ascii=False, indent=2))
        return
    print(f"project  {root}")
    for k in ("workflow", "theme", "template", "mode", "deck", "output"):
        if state.get(k):
            print(f"{k:9}{state[k]}")
    print("status   " + "  ".join(f"{'✔' if v else '·'} {k}" for k, v in state["status"].items()))
    print(f"next     {proj.next_step(state)}")


def cmd_themes(a):
    if a.action == "list":
        rows = list_themes()
        if a.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return
        for r in rows:
            print(f"{r['name']:18} {r['engine']:9} {r['source']:8} {r['description'][:80]}")
    elif a.action == "show":
        theme, path = resolve_theme(a.name)
        print(f"# {path}")
        print(json.dumps(theme, ensure_ascii=False, indent=2))
    elif a.action == "import":
        from .frame_import import find_preset, import_frame
        src = Path(a.name)
        if not src.exists():
            src = find_preset(a.name)
            if not src:
                raise SystemExit(f"FRAME.md not found for '{a.name}' — pass a path to a HyperFrames FRAME.md")
        theme, notes = import_frame(src, a.as_name)
        out = Path(a.out) if a.out else USER_HOME / "themes" / f"{theme['name']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(theme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"✔ theme '{theme['name']}' → {out}")
        for n in notes:
            print("  ·", n)
    elif a.action == "new":
        from .themes import new_theme
        dest = Path(a.out) if a.out else (Path.cwd() / "themes" / f"{a.name}.json" if a.project else None)
        path = new_theme(a.name, a.base, dest, a.force)
        engine = resolve_theme(str(path))[0].get("engine", "template")
        print(f"✔ theme '{a.name}' (copied from {a.base}) → {path}")
        print("  edit: colors.palette / ground / text, fonts, stroke, decorations (hints in the _edit key)")
        print(f"  try:  deckframes themes gallery --only {a.name}")
        print(f"  use:  deckframes build deck.md --theme {a.name}   (or `theme: {a.name}` in front matter)")
        if engine != "canvas":
            print(f"  note: '{a.base}' uses the template engine — no nav bar / sub-TOC; base on blockframe for those")
    elif a.action == "gallery":
        from .gallery import gallery
        out = Path(a.out or "themes-gallery.png")
        res = gallery(out, presets=a.presets, backend=a.backend, names=a.only.split(",") if a.only else None)
        print(f"✔ {len(res['themes'])} themes → {res['file']}")


def cmd_template(a):
    from .engines.template import inspect_template
    print(inspect_template(Path(a.file), Path(a.write_config) if a.write_config else None))


def cmd_doctor(a):
    from .preview import find_soffice, has_powerpoint
    ok = True
    print(f"deckframes {_version()}  python {sys.version.split()[0]}")
    for mod in ("pptx", "PIL", "lxml", "yaml"):
        try:
            m = __import__(mod)
            print(f"  ✔ {mod} {getattr(m, '__version__', '')}")
        except ImportError:
            ok = False
            print(f"  ✘ {mod} missing")
    import importlib.util
    fitz_ok = bool(importlib.util.find_spec("pymupdf") or importlib.util.find_spec("fitz"))
    so = find_soffice()
    pp = has_powerpoint()
    print(f"  {'✔' if pp else '·'} PowerPoint (Windows COM) for preview")
    print(f"  {'✔' if so else '·'} LibreOffice {so or ''}")
    print(f"  {'✔' if fitz_ok else '·'} PyMuPDF (LibreOffice → PNG)")
    if not pp and not (so and fitz_ok):
        print("  ⚠ preview unavailable: install LibreOffice and `pip install pymupdf`, or use PowerPoint on Windows")
    print(f"  themes: {', '.join(t['name'] for t in list_themes())}")
    sys.exit(0 if ok else 1)


# --------------------------------------------------------------------------- parser


def main(argv=None):
    ap = argparse.ArgumentParser(prog="deckframes", description="Markdown → editable PowerPoint decks.",
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("--version", action="version", version=f"deckframes {_version()}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create a deck project folder")
    p.add_argument("dir", nargs="?", default=".")
    p.add_argument("--from", dest="source", help="existing Markdown script to start from")
    p.add_argument("--theme", default=DEFAULT_THEME)
    p.add_argument("--template")
    p.add_argument("--workflow", default="deckframes-general",
                   help="deckframes-general | deckframes-academic-defense")
    p.add_argument("--mode", choices=["verbatim", "refine"], default="verbatim")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("build", help="deck.md → .pptx")
    p.add_argument("deck", nargs="?")
    p.add_argument("-o", "--output")
    p.add_argument("--theme")
    p.add_argument("--template")
    p.add_argument("--assets")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("check", help="overflow / bounds QA (exit 1 on issues)")
    p.add_argument("pptx", nargs="?")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-outline", action="store_true")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("preview", help="render slides to PNG + grid.png")
    p.add_argument("pptx", nargs="?")
    p.add_argument("--out")
    p.add_argument("--cols", type=int, default=4)
    p.add_argument("--backend", choices=["auto", "powerpoint", "libreoffice"], default="auto")
    p.set_defaults(fn=cmd_preview)

    p = sub.add_parser("status", help="show / update project state")
    p.add_argument("--set", action="append", choices=proj.STAGES)
    p.add_argument("--unset", action="append", choices=proj.STAGES)
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("themes", help="list / show / import themes")
    p.add_argument("action", choices=["list", "show", "import", "gallery", "new"])
    p.add_argument("name", nargs="?")
    p.add_argument("--name", dest="as_name", help="(import) theme name to save as")
    p.add_argument("--out", help="(import) theme path / (gallery) image path")
    p.add_argument("--presets", action="store_true", help="(gallery) also show every HyperFrames preset found")
    p.add_argument("--only", help="(gallery) comma-separated theme names")
    p.add_argument("--from", dest="base", default=DEFAULT_THEME, help="(new) theme to copy")
    p.add_argument("--project", action="store_true", help="(new) write to ./themes/ instead of ~/.deckframes/themes/")
    p.add_argument("--force", action="store_true", help="(new) overwrite an existing file")
    p.add_argument("--backend", choices=["auto", "powerpoint", "libreoffice"], default="auto")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_themes)

    p = sub.add_parser("template", help=".pptx template tools")
    p.add_argument("action", choices=["inspect"])
    p.add_argument("file")
    p.add_argument("--write-config")
    p.set_defaults(fn=cmd_template)

    p = sub.add_parser("doctor", help="check dependencies and renderers")
    p.set_defaults(fn=cmd_doctor)

    a = ap.parse_args(argv)
    if a.cmd == "themes" and a.action in ("show", "import", "new") and not a.name:
        ap.error(f"themes {a.action} needs NAME")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    a.fn(a)


if __name__ == "__main__":
    main()
