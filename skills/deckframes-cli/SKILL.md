---
name: deckframes-cli
description: >
  deckframes command reference and the build → check → preview QA loop: init, build, check
  (human or --json), preview (grid.png), status (resumable stages), themes, template inspect,
  doctor. Use when running, debugging or verifying a deckframes deck.
---

# CLI and QA loop

Inside a project folder (one with `deck.json`) arguments default from the project, so the loop is:

```bash
deckframes build            # deck.md → output/<name>.pptx      (marks stage "built")
deckframes check            # overflow / off-slide QA; exit 1 on issues (marks "checked" when clean)
deckframes preview          # PNG per slide + output/<name>_preview/grid.png
deckframes status --set reviewed
```

## Commands

| Command | Purpose |
|---|---|
| `deckframes init DIR --from script.md [--theme T \| --template T] [--workflow W] [--mode verbatim\|refine]` | create a project |
| `deckframes status [--set STAGE] [--unset STAGE] [--json]` | stages `brief draft built checked reviewed` + suggested next step |
| `deckframes build [deck.md] [-o out.pptx] [--theme T] [--template T] [--assets DIR]` | render |
| `deckframes check [file.pptx] [--json] [--no-outline]` | structural QA + slide outline |
| `deckframes preview [file.pptx] [--backend auto\|powerpoint\|libreoffice] [--cols N]` | render images |
| `deckframes themes list \| show NAME \| import PRESET\|FRAME.md [--name N] [--out PATH]` | themes |
| `deckframes template inspect FILE.pptx [--write-config config.json]` | map template layouts |
| `deckframes doctor` | dependencies and renderers |

Building a single file outside a project also works: `deckframes build talk.md -o talk.pptx`.

## QA loop

1. **Build.** Every `⚠` line (missing image, SVG, table too long) must be resolved in deck.md.
2. **Check.** Fix until `0 issue(s)`. `--json` gives
   `{ok, slides, issues, pages:[{index, layout, text:[{level,text}], pictures, tables, charts, notes, issues:[{type, …}]}]}`;
   issue types are `text_overflow` (needed_pt vs available_pt) and `off_slide`.
3. **Look.** Open `grid.png` (and individual `slide-NNN.png` for detail) if you can view images.
   Check: no clipped text, visuals not cramped or floating in empty space, images not tiny, nav bar
   labels legible. If you cannot view images, compare the `check --json` outline against deck.md
   slide by slide instead, and say so in your report.
4. **Fix in deck.md, rebuild.** Usually 1–2 rounds. Then `deckframes status --set reviewed`.

## Common fixes (always in deck.md)

| Symptom | Fix |
|---|---|
| Text overflow / tiny text in the left column | ≤ 5 bullets; split with `---`; move detail to `<!-- notes -->` |
| Nav bar sections cramped | shorten section names (≤ 6 CJK chars) or split the chapter |
| Infographic cramped or lost in whitespace | 2–4 items per `cards`/`stats`; many items → `steps`; options → `compare` |
| Table overflow | fewer columns, or split the table |
| Highlight not visible | `==x==` needs PowerPoint 2019 / Microsoft 365 |
| Divider right side empty | the chapter has no `###` sections — add them or a one-line intro under `##` |
| Wrong layouts with a .pptx template | fix `layouts` in the template's config.json (`deckframes-templates`) |
