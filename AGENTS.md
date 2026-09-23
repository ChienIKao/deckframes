# AGENTS.md

Guidance for coding agents (Codex, Claude Code, Cursor, …) working **in this repository** or
**using deckframes** to make decks.

## Using deckframes to make a deck

If the deckframes skills are installed, load the `deckframes` skill and follow it. Otherwise:

1. `deckframes doctor` (install with `pip install -e .` from this repo, or
   `uv tool install git+https://github.com/ChienIKao/deckframes`).
2. `deckframes init <folder> --from <script.md>` → edit `<folder>/deck.md` following
   `skills/deckframes-core/SKILL.md` and `skills/deckframes-infographics/SKILL.md`.
3. `deckframes build && deckframes check && deckframes preview`, fix `deck.md`, repeat.
4. Never hand-edit the .pptx, never invent numbers, never reword the user's text in verbatim mode.

## Repository layout

```
src/deckframes/
  cli.py            argparse entry point (`deckframes …`)
  markdown.py       deck.md → Doc tree (chapters › sections › slides), inline runs
  layout.py         text measurement, pagination, template-engine planning
  engines/canvas.py theme-token renderer: cover, outline, dividers, nav bar, infographics
  engines/template.py  placeholder renderer for user .pptx/.potx templates
  check.py          structural QA report (JSON-serialisable)
  preview.py        PowerPoint COM / LibreOffice → PNG + grid
  project.py        deck.json state, init, stage tracking
  themes.py         theme/template lookup (project → ~/.deckframes → built-in)
  frame_import.py   HyperFrames FRAME.md → canvas theme
  themes/*.json     built-in themes
skills/<name>/SKILL.md   agent skills (Agent Skills format; installable with `npx skills add`)
examples/                demo decks (fictional content)
tests/                   pytest smoke tests
```

## Development

Contribution recipes (new theme, template, infographic component, workflow skill) are in
[CONTRIBUTING.md](CONTRIBUTING.md).

```bash
pip install -e ".[preview]" pytest
pytest -q
ruff check --select F,E9 src      # lint used in review
deckframes build examples/demo.md -o /tmp/demo.pptx && deckframes check /tmp/demo.pptx
```

- Keep rendering deterministic: same deck.md + theme → same slides.
- Canvas drawing must stay token-driven — no hard-coded colours outside theme JSON except neutral
  fallbacks; text on fills goes through `Canvas.on()` for contrast.
- CLI output and skills are English; user-facing docs may be bilingual.
- Skills must stay agent-neutral: no tool names specific to one agent product.
