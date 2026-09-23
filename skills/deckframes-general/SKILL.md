---
name: deckframes-general
description: >
  General deckframes workflow for proposals, lectures, reports, pitches and internal talks:
  shape a Markdown script into chapters/sections/slides, convert content into infographics,
  build, check and review. Use after the deckframes entry skill routes a non-academic deck here.
---

# General deck workflow

1. **Structure.** Map the script onto `##` chapters (3–6), `###` sections, `####` slides
   (`deckframes-core`). Add English chapter subtitles (`## 方案 | Proposal`) unless the user
   declines. If the script is flat, pick the flatter hierarchy settings instead of inventing
   chapters.
2. **Front matter.** `eyebrow` (event or purpose), `author`, `date`, `subtitle`; logos if supplied.
3. **Infographics.** Walk every slide through `deckframes-infographics`; keep plain arguments as
   bullets.
4. **Assets.** Put images in `assets/`, reference them where they support the point; propose
   placements to the user when the script doesn't say.
5. **Mode.** In `refine` mode shorten long paragraphs into bullets and move the original wording
   to `<!-- notes -->`; in `verbatim` mode never reword.
6. **Build → check → review** per `deckframes-cli`, then `deckframes status --set draft` /
   `reviewed` as you go.
7. **Report**: output path, slide count, theme, infographic conversions, other edits, placeholders.
