---
name: deckframes
description: >
  Mandatory entry point for turning a Markdown script, outline or notes (plus images) into an
  editable PowerPoint (.pptx) deck with the deckframes CLI — thesis defenses, proposals, lectures,
  reports, pitch decks. Use it whenever the user asks for slides, a deck, a presentation, a PPT/PPTX,
  or wants to resume, rebuild, restyle or QA an existing deckframes project (a folder with deck.json).
  It checks the toolchain, resumes project state, runs a short intake, and routes to the workflow
  and domain skills (deckframes-core, deckframes-infographics, deckframes-design, deckframes-cli,
  deckframes-templates).
---

# deckframes entry point

deckframes **renders PowerPoint from Markdown**. A deck is one `deck.md` file whose heading
hierarchy becomes cover → outline → chapter dividers (with sub-TOC) → content slides (with a
chapter/section nav bar) → closing, and whose fenced blocks become native infographics. The
`deckframes` CLI does all rendering deterministically; your job is to shape `deck.md`, run the
CLI, verify, and iterate.

## 0. Toolchain

Run `deckframes doctor`. If the command is missing, install it (ask before installing if your
environment requires approval):

```bash
uv tool install git+https://github.com/ChienIKao/deckframes      # or
pipx install git+https://github.com/ChienIKao/deckframes         # or
pip install git+https://github.com/ChienIKao/deckframes
```

Call the `deckframes` command directly. (`python -m deckframes` only works with the Python the
package was pip-installed into — not with `uv tool` / `pipx` installs.) Preview needs PowerPoint (Windows) or
LibreOffice + `pip install pymupdf`; if neither exists, QA falls back to `deckframes check --json`.

## 1. Start from project state

Apply the first matching row:

| State | Action |
|---|---|
| A specific operation on an existing project (rebuild, restyle, check, preview) | Do only that. Load `deckframes-cli` (and `deckframes-design` for restyling). |
| `deck.json` exists in the working folder or a parent | Run `deckframes status`. Resume from `next`; reuse the recorded theme, workflow and mode. Ask nothing already recorded. |
| Fresh request | Run the intake (§ 2), then `deckframes init`, then route (§ 3). |

## 2. Intake (fresh projects only)

Ask **once, in one message**, only what the request doesn't already answer. Offer defaults.

1. **Purpose** → picks the workflow: thesis/defense/research talk → `deckframes-academic-defense`;
   anything else → `deckframes-general`.
2. **Look** → a theme or a .pptx template. Run `deckframes themes list` and show the list; if the
   user wants to see them, run `deckframes themes gallery --presets` and show the image.
   Default `blockframe`. The user may also name a HyperFrames design preset
   (`deckframes themes import <preset>`) or give a company .pptx/.potx (`deckframes-templates`).
3. **Content mode** → `verbatim` (default: fix structure, convert to infographics, never reword)
   or `refine` (long paragraphs become bullets; original text moves to speaker notes).
4. **De-AI scope** → `written` (sepia polishes only text you write: notes, card blurbs, subtitles)
   or `all` (the user's own text too — pick this when their script is itself AI-written).
   Default: `written` with `verbatim`, `all` with `refine`.

Then create the project (one folder per deck, `<YYYYMMDD-slug>/` in the working directory):

```bash
deckframes init <YYYYMMDD-slug> --from <script.md> --theme <theme> --workflow <workflow> --mode <mode> --polish <scope>
```

`<workflow>` is `deckframes-general` or `deckframes-academic-defense`; `<mode>` is `verbatim` or `refine`;
`<scope>` is `written` or `all`.

`init` copies the script to `source.md` (never edited) and `deck.md` (your working copy), copies a
sibling `assets/` folder, and writes `deck.json` and an `AGENTS.md` hand-off note.

## 3. Route

| Workflow | Skill |
|---|---|
| Thesis defense, research presentation, lab report | `deckframes-academic-defense` |
| Everything else (proposal, lecture, report, pitch) | `deckframes-general` |

Domain skills, loaded by the workflows as needed:

| Need | Skill |
|---|---|
| deck.md syntax: hierarchy, front matter, inline marks, layout rules | `deckframes-core` |
| Which infographic fits which content, and its syntax | `deckframes-infographics` |
| Themes, importing HyperFrames presets, custom theme JSON | `deckframes-design` |
| Commands, QA loop, reading `check` output | `deckframes-cli` |
| Corporate / school .pptx templates | `deckframes-templates` |

## Draft → polish → approve → build

Every workflow passes two gates between writing deck.md and the first `deckframes build`:

1. **Polish (de-AI).** Once the draft is structured, run the `sepia` skill's **refactor** operation
   over deck.md — slide text *and* `<!-- notes -->`. Do this without being asked. Scope:
   - Pass the Markdown structure as protected: headings, front matter, fenced block syntax,
     `key: value` fields, `icon:` names, `==highlight==` / callout markers, `Source:` lines, numbers.
     Only the prose inside them is in scope.
   - Scope comes from `polish` in deck.json (`deckframes status` shows it; if missing, `all` for
     `refine` and `written` for `verbatim`). `written`: also protect every sentence taken from
     `source.md`; polish only text you wrote (speaker notes, card blurbs, takeaways, subtitles).
     `all`: polish the user's text as well — an explicit opt-in that overrides the verbatim
     no-rewording rule for this pass only.
   - If `sepia` is not installed, say so and skip the pass; don't imitate it.
   Then `deckframes status --set polished`.
2. **Approve.** Show the user deck.md (or a slide-by-slide outline with notes for long decks) and
   **stop**. Do not build until they say go. Apply any requested edits to deck.md, re-polish the
   changed prose, and show it again. On a clear yes: `deckframes status --set approved`, then build.

Re-entering an earlier stage (`--set draft`) resets `polished` and `approved`, so a reworked draft
goes through both gates again. Small fixes during the build → check → review loop (overflow,
splitting a slide) don't need a new approval round; rewording does.

## Non-negotiables

- **Edit `deck.md`, never the .pptx.** Every fix goes back into the Markdown and is rebuilt.
- **No emoji — anywhere.** Not in titles, bullets, cards, tags or notes. `deckframes build` refuses a
  deck.md that contains emoji and `deckframes check` flags any in the .pptx. When a visual marker
  helps, use an icon: `icon: <font-awesome-name>` on an infographic item (find names with
  `deckframes icons search <word>`) or an SVG file (`icon: assets/x.svg`, `![caption](assets/x.svg)`).
- **Never invent numbers.** `stats` and `chart` values come from the user's material only; missing
  values become `— value —` placeholders listed in your report.
- **Don't reword in verbatim mode** (except the opted-in `polish: all` pass). Restructuring, splitting slides, converting to infographic
  blocks and adding English chapter subtitles are fine; deleting or rewriting sentences needs a yes.
- **One visual idea per slide.** ≤ 5 bullets beside a visual; move detail to `<!-- notes -->`.
- **Vary the presentation.** Plan blocks across the whole deck — 16 infographic blocks exist; don't
  ride one or two. Resolve every `monotony:` warning from `deckframes build`.
- **No build before approval.** `deckframes status` must show `approved` before the first build.
- **Record progress** with `deckframes status --set <stage>` so another agent can resume.

## Done means

- `deckframes build` succeeds, `deckframes check` reports 0 issues
- every slide reviewed in `grid.png` (or via `check --json` if you cannot view images)
- `deckframes status` shows all stages ✔
- report to the user: output path, slide count, theme, slides turned into infographics, other
  changes, and any placeholder values still to fill
