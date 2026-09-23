---
name: deckframes-design
description: >
  Choose or create the visual theme of a deckframes deck: list built-in themes, import any
  HyperFrames design preset (FRAME.md) as a PowerPoint theme, and edit theme JSON tokens (palette,
  ground, ink, fonts, border/shadow weights, decorations). Use when the user asks for a style,
  a colour scheme, a HyperFrames look, or to restyle an existing deck.
---

# Themes

A canvas theme is a JSON file of design tokens; the canvas engine draws every slide from it
(outline, dividers with sub-TOC, nav bar, infographics). Lookup order for `--theme NAME`:
a path → `./themes/NAME.json` → `~/.deckframes/themes/NAME.json` → built-ins.

```bash
deckframes themes list                  # show choices to the user
deckframes themes gallery --presets     # one image: every theme (incl. importable HyperFrames presets)
deckframes themes show blockframe       # inspect tokens
deckframes themes new my-look [--from capsule] [--project]   # scaffold an editable copy
```

When the user is choosing a look, generate the gallery and show them the image (or its path) —
it renders the same sample deck (cover, divider, content + nav bar, stats) in every theme.

| Built-in | Look |
|---|---|
| `blockframe` (default) | HyperFrames BlockFrame neo-brutalism: thick black outlines, hard zero-blur shadows, five candy colours cycling per chapter, tilted blocks, star bursts, stripe tiles |
| `default` | plain navy/white (template engine, no nav bar) |

## Importing a HyperFrames design

Any HyperFrames preset (`blockframe`, `capsule`, `coral`, `editorial-forest`, `cartesian`,
`cobalt-grid`, `daisy-days`, …) converts in one step:

```bash
deckframes themes import capsule                 # found in ~/.claude/skills or ~/.agents/skills
deckframes themes import path/to/FRAME.md --name my-look
```

The importer classifies colours by role (ground = lightest neutral, ink = darkest, palette =
saturated accents), converts border/shadow px to pt (hard offset shadows only; blurred shadows → none),
maps web fonts to fonts that ship with Office, and turns decorations/tilt on only for
brutalist presets (border ≥ 2px and hard shadow ≥ 4px). It prints what it inferred — check the
preview and hand-tune the JSON if a role was guessed wrong. The theme lands in
`~/.deckframes/themes/` and is then usable by name.

## Custom themes

When the user wants their own colours or fonts: `deckframes themes new <name>` (copies blockframe,
or `--from` another theme) → edit the tokens below (the file's `_edit` key repeats the hints) →
`deckframes themes gallery --only <name>` to show them → build with `--theme <name>`. Written to
`~/.deckframes/themes/` (all projects) or, with `--project`, `./themes/` (this project only).

## Token reference

| Key | Meaning |
|---|---|
| `engine` | `canvas` (drawn) — required for nav bar / sub-TOC / infographics |
| `colors.ground` / `text` / `muted` / `white` | slide background, body text, secondary text, card fill |
| `colors.black` | outline and connector colour (usually = text) |
| `colors.palette` | accent fills, cycled by components (≥ 2, ideally 5) |
| `colors.chapter_cycle` | chapter colours (dividers, nav band); defaults to palette |
| `fonts.display` / `label` / `body` / `code` | Latin fonts for headlines, pills, body, code |
| `fonts.ea` | CJK font (default Microsoft JhengHei) |
| `stroke.border` / `thin` | outline weights in pt (0 = no outline) |
| `stroke.shadow` / `thin_shadow` | hard shadow offsets in pt (0 = no shadow) |
| `decorations` / `tilt` | star bursts, stripe tiles, dot grids / rotated cards on or off |
| `sizes.title` `subtitle` `body_max` `body_min` `split_below` | type scale in pt |

Text on coloured fills automatically switches between ink and white for contrast, so any palette
is safe. Pick fonts that exist on the machine that will present the deck; web fonts that are not
installed are substituted by PowerPoint.
