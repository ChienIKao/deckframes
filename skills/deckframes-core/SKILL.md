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
| `![caption](assets/x.png)` on its own line | framed image + caption tag (PNG/JPG; no SVG) |
| Markdown table | native table; ○ × ✓ and numbers auto-centred |
| ```` ```lang ```` code fence | dark code card |
| ```` ```cards ```` `steps` `timeline` `flow` `stats` `compare` `chart` | infographics → `deckframes-infographics` |
| `<!-- text -->` | speaker notes (multi-line OK) |

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

Image paths are relative to deck.md (or `--assets DIR`). Convert SVG to PNG first. Prefer ≥ 1600 px
wide images.
