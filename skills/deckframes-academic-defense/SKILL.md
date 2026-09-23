---
name: deckframes-academic-defense
description: >
  Workflow for thesis defenses, dissertation proposals and research talks with deckframes: chapter
  structure (Introduction, Related Work, Data, Method, Results, Conclusion), English chapter
  subtitles, citations, formula callouts, results charts, recap dividers and Q&A closing. Use after
  the deckframes entry skill routes an academic deck here.
---

# Academic defense workflow

Audience: a committee that reads every slide closely and asks about method and evidence. The deck
must make the argument traceable: problem → gap → method → evidence → contribution.

## 1. Structure deck.md

Typical chapters (keep the user's own if they differ); every chapter gets an English subtitle:

| Chapter | Sections usually inside |
|---|---|
| `## 緒論 \| Introduction` | background, problem, objectives, scope & limitations |
| `## 文獻探討 \| Related Work` | one section per research stream + a comparison table |
| `## 資料集 \| Dataset` | sources, preprocessing, statistics |
| `## 研究方法 \| Methodology` | pipeline overview, then one section per module |
| `## 研究結果 \| Results` | experiments, ablations, error analysis |
| `## 結論 \| Conclusion` | contributions, future work |

Front matter: `eyebrow` (e.g. 碩士論文口試報告 / Thesis Defense), `author`, `date`, English
`subtitle`, lab/school logos as `logo_left` / `logo_right` if provided, `closing: Q&A`.
Set `recap: true` when chapters have ≥ 4 sections, so the committee sees where they are.

## 2. Convert content (see `deckframes-infographics`)

| Academic content | Treatment |
|---|---|
| Industry context / motivating cases | `cards stack` with `tag:` |
| Research gaps or "three problems" | `cards` with `icon:` |
| Contributions / highlights | `stats` only if the numbers are in the script; otherwise `cards` |
| Literature comparison | ○ × table + `> [!NOTE]` legend |
| Method pipeline | `flow` overview slide, then one slide per stage |
| Algorithm steps, hyper-parameter search | `steps` / `timeline` |
| Formulas | put the formula as an image or code line; explain symbols in `> [!NOTE]` |
| Results tables | Markdown tables (auto-split past `max_table_rows`) |
| Results trends | `chart` from the script's numbers; never estimate from a figure |
| Key finding | statement slide with `==highlight==` |
| Figures from the thesis | `![Figure 3-2 …](assets/...)` with the caption |
| Every borrowed claim | `Source: …` footer (IEEE-style reference is fine) |

## 3. Speaker notes

Put timing and talking points in `<!-- -->` per slide. Budget ≈ 1 slide per minute of the allotted
talk; if the deck runs long, tell the user which sections to compress rather than cutting content
yourself.

## 4. Build, check, review

Follow `deckframes-cli`. Additional checks for defenses:
- every chapter divider lists its sections; nav bar labels fit
- citation footers present wherever a source is quoted
- no invented numbers; list every placeholder in the report
