---
name: deckframes-core
description: >
  The deck.md contract for deckframes: heading hierarchy (cover, chapters, sections, slides),
  `Title | Subtitle` headings, front-matter keys, inline marks (==highlight==, callouts, sources,
  speaker notes), automatic layout selection and pagination. Read before writing or editing any
  deck.md.
---

# deck.md contract

## Hierarchy

| Markdown | Becomes |
|---|---|
| `# Title` | cover |
| `## Chapter \| English` | outline entry + chapter divider (right side lists its sections) |
| `### Section` | divider sub-TOC entry + 2nd row of the nav bar |
| `#### Slide title \| subtitle` | one content slide |
| `#####` and deeper | bold sub-heading inside a slide |
| `---` inside a slide | force a page break (same title continues) |

- Any heading takes ` | ` + subtitle. Chapters use it for the English name (`## 緒論 | Introduction`);
  slides use it for a grey subtitle line.
- Content directly under `###` (no `####`) becomes one slide titled with the section name, so
  3-level scripts work unchanged.
- Slide titles render as `{section} – {slide}` (`研究背景 – 工業 4.0`); identical names show once.
  Override with `title_format`.
- Flatter scripts: `subsection_level: 0` + `slide_level: 3` (## chapter, ### slide), or
  `section_level: 0` + `subsection_level: 0` + `slide_level: 2` (## = slide).

## Front matter (all optional; `#` lines are comments)

```yaml
---
theme: blockframe            # or template: <name|path>
eyebrow: Thesis Defense      # pill above the cover title
subtitle: English subtitle
author: Presenter: Name
date: 2026 / 07 / 08
badge: 2026                  # text in the cover star burst (decorative themes)
cover_image: assets/cover.png
logo_left: assets/lab.png    # nav-bar logos
logo_right: assets/school.png
outline: true                # outline slide
outline_title: 大綱
outline_en: OUTLINE
recap: false                 # replay the chapter divider before each section, current one highlighted
title_format: "{sub} – {title}"
closing: Q&A                 # closing slide text; false = none
closing_label: THANK YOU
max_table_rows: 9            # longer tables split, header repeated
section_level: 2
subsection_level: 3
slide_level: 4
---
```

## Inline and block marks

| Write | Result |
|---|---|
| `- item` / `1. item` (indent 2–4 spaces per level) | bullets / numbered |
| plain paragraph | un-bulleted text |
| `**bold**`, `*italic*`, `` `code` ``, `[text](url)` | inline formatting |
| `==key phrase==` | highlighter mark + bold |
| `> quote` | quote; a slide holding only one quote becomes a quote card |
| `> [!NOTE] text` | bottom callout. Kinds: NOTE, TIP, IMPORTANT, WARNING, CAUTION, SUMMARY |
| paragraph starting `Source:` / `資料來源：` / `來源：` / `Ref:` | footer citation |
| `![caption](assets/x.png)` on its own line | framed image + caption tag (PNG, JPG or SVG — SVG stays vector) |
| Markdown table | native table; ○ × ✓ and numbers auto-centred |
| ```` ```lang ```` code fence | dark code card |
| ```` ```cards ```` `steps` `timeline` `flow` `stats` `compare` `chart` | infographics → `deckframes-infographics` |
| `<!-- text -->` | speaker notes (multi-line OK) |

## No emoji — use icons

Emoji are banned from every part of a deck. `deckframes build` exits with an error listing each
emoji's line and column; `deckframes check` reports `emoji` issues in a built .pptx. Typographic
symbols (✓ ✗ ○ × → ★ ■ –) are fine.

Where a pictogram helps, use an icon reference on an infographic item (`icon:`):

| Reference | Meaning |
|---|---|
| `icon: users` | Font Awesome Free (solid style first, then regular, then brands) |
| `icon: regular:clock` / `fa-regular fa-clock` | a specific Font Awesome style |
| `icon: brands:github` | brand logos |
| `icon: assets/mark.svg` | your own SVG (kept as vector) or PNG |
| `icon: ?` / `icon: A` | a plain ASCII glyph rendered as text |

Find names with `deckframes icons search <word>` (e.g. `chart`, `user`, `clock`); browse at
https://fontawesome.com/search?ic=free. Icons are downloaded once from the jsDelivr CDN and cached
in `~/.deckframes/icons/`; Font Awesome icons are recoloured to fit the fill they sit on.
Font Awesome Free icons are CC BY 4.0 — the attribution comment travels inside each embedded SVG.

## Automatic layout (canvas themes)

| Slide content | Layout |
|---|---|
| text only | full-width text, larger type ceiling |
| ≤ 4 paragraphs containing `==highlight==` | statement slide: large centred text |
| a single quote | quote card |
| text + one image/table/infographic | text left (~42–45%), visual right |
| visual(s) only | full width |
| callout | pinned to the bottom of the body area |

## Pagination

Text is measured against the real box: if it doesn't fit at 14 pt the slide is halved at a
top-level bullet boundary and the next page gets `（續）`. Extra visuals get their own slides.
Control breaks yourself with `---`.

## Assets

Image paths are relative to deck.md (or `--assets DIR`). SVG is embedded as a vector picture (with a
PNG fallback for old viewers). Prefer ≥ 1600 px
wide images.
