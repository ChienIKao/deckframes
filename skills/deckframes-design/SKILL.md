---
name: deckframes-design
description: >
  Choose or create the visual theme of a deckframes deck: list built-in themes, import any
  HyperFrames design preset (FRAME.md) as a PowerPoint theme, and edit theme JSON tokens (palette,
  ground, ink, fonts, border/shadow weights, surface / cover / nav variants, decorations). 24
  built-ins from academic, minimalism and swiss to claymorphism, glassmorphism and synthwave. Use when the user asks for a style,
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

Built-in themes differ in **structure**, not just colour: each picks a surface treatment, a cover /
divider / nav / outline / callout / closing variant, a background, a texture and its own decorations.

| Built-in | Look |
|---|---|
| `blockframe` (default) | Neo-Brutalism: thick black outlines, hard shadows, candy colours per chapter, star bursts |
| `academic` | Lab-meeting / thesis style: white, blue pill nav bar, gold rule, serif titles, red/green problem/result banners, editorial cover with authors and affiliations |
| `minimalism` | lots of white space, one blue accent, no decoration |
| `swiss` | Swiss grid: bold sans, red/black/white, big circle and rules, flush left |
| `editorial` | magazine: off-white paper, Bodoni headlines, hairline rules, vermilion accent |
| `bento` | rounded tiles of mixed sizes, product-launch clean |
| `luxury` | black and gold, Bodoni, double hairline frames |
| `claymorphism` | pastel clay blocks with soft outer shadow + inner highlight |
| `neumorphism` | same-colour embossed cards, light/dark double shadows |
| `glassmorphism` | frosted translucent cards on a vivid gradient with glowing orbs |
| `y2k` | pink/purple gradient, bubbles, sparkles, glossy cards |
| `ethereal` | pale gradient, soft-focus orbs, sparkles, thin type |
| `synthwave` | 80s neon, purple night gradient, striped sun, perspective grid floor |
| `cyberpunk` | black, neon yellow/cyan, chamfered panels, hazard stripes, glow |
| `cybercore` | terminal green on black, scan lines, pixel noise, mono font |
| `pixel-art` | 8-bit palette, blocky hard shadows, grid ground, pixel hearts |
| `maximalism` | clashing colours with every decoration layered |
| `scrapbook` | kraft paper, polaroid cards, washi tape, handwriting, slight tilt |
| `sketch` | conceptual sketch: grid paper, handwritten titles, dashed boxes, doodle arrows |
| `surrealism` | sunset gradient sky, floating spheres and arches, dream-like |
| `bohemian` | earth tones, rainbow arches, sun circle, paper texture |
| `victorian` | parchment, burgundy and forest green, ornate double frames, serif |
| `wabi-sabi` | greige and earth, imperfect ink circle, stones, paper grain |
| `default` | plain navy/white (template engine, no nav bar) |

Match the theme to the audience: `academic` / `minimalism` / `swiss` / `editorial` for lab meetings,
defenses and reports; the expressive ones for pitches, classes and events.

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
| `stroke.image` | thin outline around pictures in pt (default 1; 0 = none). Pictures never get a card or shadow |
| `decorations` / `tilt` | star bursts, stripe tiles, dot grids / rotated cards on or off |
| `sizes.title` `subtitle` `body_max` `body_min` `split_below` | type scale in pt |
| `fonts.heading` / `ea_heading` | title font (Latin / CJK); defaults to body fonts |
| `colors.title` / `card_text` / `card_muted` | title ink, text on cards (when cards are dark, e.g. glass) |
| `colors.on_light` / `on_dark` | text colour chosen on light / dark fills |
| `colors.negative` / `positive` | tone colours for `[!PROBLEM]` / `[!RESULT]`, `compare tone`, `mapping` |

### `style` — the structural look

| Key | Values |
|---|---|
| `surface` | how cards and boxes are drawn: `brutal` `pixel` `flat` `outline` `soft` `glass` `clay` `neu` `paper` `sketch` `neon` `luxury` `ornate` |
| `radius` | corner rounding 0 – 0.5 |
| `cover` | `split` `centered` `poster` `editorial` (authors / affiliations block) `frame` `bento` `minimal` |
| `divider` | `panel` `hero` `centered` `band` `minimal` |
| `nav` | `band` `pills` `underline` `breadcrumb` `none` |
| `outline` | `line` `list` `grid` |
| `callout` | `pill` `banner` (full-width coloured bar) `tint` (tinted box with icon) |
| `closing` | `frame` `centered` `poster` |
| `ground` | `{"type": "solid"}` or `{"type": "gradient", "colors": [a, b], "angle": 90}`; `roles: {cover: {...}, divider: {...}}` overrides per slide role |
| `texture` | `none` `grid` `scanlines` `dots` `paper` `noise` |
| `decor` | list of decorations: `blocks` `stripes` `stars` `dots` `orbs` `clay` `sparkles` `bubbles` `sun` `floor` `pixels` `tape` `rules` `circle` `arches` `enso` `ornament` `hazard` `scan` `tiles` `doodle` `glass` `neu` `surreal` |
| `accent_line` | colour of a thin rule under titles (e.g. academic gold) |
| `stat_color` | colour stat numbers with the palette |
| `title_upper` | upper-case Latin titles |

Start from the built-in closest to what the user wants (`themes new my-look --from swiss`) and
change colours / fonts first; change `style` only when the structure itself should differ.

Text on coloured fills automatically switches between ink and white for contrast, so any palette
is safe. Pick fonts that exist on the machine that will present the deck; web fonts that are not
installed are substituted by PowerPoint.
