---
name: deckframes-infographics
description: >
  Decide which deckframes infographic block fits each slide's content (cards, steps, timeline, flow,
  stats, compare, chart, diagram, lanes, mapping, stack, matrix, pyramid, funnel, cycle, progress,
  tables, callouts, statement slides) and write its syntax. Use while shaping deck.md so slides show
  one visual idea instead of walls of bullets, and so the deck does not repeat one pattern.
---

# Content → infographic

For every slide ask: *is this content parallel items, a comparison, a transformation, a process,
numbers, or a conclusion?* Then pick the block. Plain argumentation stays as bullets — don't force
a visual.

| Content shape | Block |
|---|---|
| Parallel examples (companies, cases, products) | ```` ```cards stack ```` with `tag:` and `img:` |
| N problems / pain points / highlights | ```` ```cards ```` with a Font Awesome `icon:` each |
| A transformation (reactive → proactive, old → new) | ```` ```flow vertical ```` |
| A pipeline / system flow | ```` ```flow ```` |
| Method steps | ```` ```steps ```` (vertical) or ```` ```timeline ```` (horizontal) |
| Headline numbers | ```` ```stats ```` |
| Methods × properties matrix | Markdown table with ○ / × |
| Two or three options side by side | ```` ```compare ```` (two columns get a VS badge) |
| Experimental results | ```` ```chart column|bar|line|pie|doughnut|stacked Title ```` |
| A bridging key sentence | paragraphs with `==highlight==` → statement slide |
| Formula legend, symbol notes, the slide's takeaway | `> [!NOTE]` / `> [!IMPORTANT]` / `> [!TIP]` |
| Citation | `Source: …` paragraph |
| Screenshots, architecture, plots | `![caption](assets/x.png)` — one per slide; for app screenshots use `#### Feature \| one-line message` and no bullets (showcase layout) |
| The core message | a lone `> quote` → quote card |
| System / model architecture, data flow with branches | ```` ```diagram ```` (`A -> B` edges, `group`, `focus=`) |
| Walking through one architecture part by part | the same ```` ```diagram focus=Part ```` on consecutive slides |
| Related work or baseline comparison by year and model family | ```` ```lanes 2017-2026 ```` |
| Problems ↔ the fix for each | ```` ```mapping ```` (`Problem -> Solution`) |
| Model layers, tech stack, pipeline stages top → bottom | ```` ```stack ```` |
| 2 × 2 positioning (effort × impact, cost × quality) | ```` ```matrix x=… y=… ```` |
| Hierarchy / levels of abstraction | ```` ```pyramid ```` (top = narrowest) |
| Narrowing stages (raw data → samples, leads → customers) | ```` ```funnel ```` |
| An iterative loop (collect → train → evaluate → fix) | ```` ```cycle Center label ```` |
| Status of work items, completion | ```` ```progress ```` (`- Label \| 80%`) |
| Takeaways vs. open questions, pros vs. cons | ```` ```compare tone ```` (green / red columns, no VS) |
| A slide's problem statement / its result | `> [!PROBLEM] …` / `> [!RESULT] …` |

## Vary the presentation

A deck that uses one or two blocks throughout feels monotonous — and that is the most common
failure. Before writing, list each slide's content shape and assign blocks across the whole deck:

- No block (or plain bullets) on more than three consecutive content slides.
- No single block on more than ~45 % of content slides. `deckframes build` prints
  `monotony:` warnings when either happens — treat them like check issues and fix them.
- The same content can usually take several forms: a process is `steps`, `flow`, `stack`, `cycle`
  or `diagram`; a list of items is `cards`, `mapping`, `matrix` or a table; numbers are `stats`,
  `chart` or `progress`. Pick the one that matches the *relationship* between items.
- Repeating a `diagram` with a moving `focus=` across a sequence is fine — it is one visual story.

## Composition rules

- Text left, one visual right is the default and the most common layout.
- ≤ 5 bullets beside a visual; more → split the slide or move detail into `<!-- notes -->`.
- One visual per slide (two images may sit side by side); extra visuals get their own slides.
- One callout per slide, always at the bottom.

## Item syntax

Inside a block, one list item per element; fields are separated by ` | `:

```
- Title | Description | extra… | tag: label | img: path | icon: users
  - child line (card / compare-column bullets)
```

`icon:` works on `cards` (icon square), `steps` (replaces the number), `timeline` (in the step
header) and `flow` (above the node title, when the box is tall enough). Use a Font Awesome Free name
(`deckframes icons search chart`), a style-qualified name (`regular:clock`, `brands:github`) or an
SVG path. Pick icons that carry meaning (clock = waiting time, database = data) — and never emoji.

| Block | 1st field | 2nd field | extra / children | Options after the block name |
|---|---|---|---|---|
| `cards` | card title | one-line description | bullet details | `stack`, `grid`, `cols=3` |
| `steps` / `timeline` | step name | description | bullet details | `vertical`, `horizontal` |
| `flow` | node | small caption | — | `vertical`, `horizontal`; or one line `A -> B -> C` |
| `stats` | the number (`38`, `3.8%`, `2×`) | label | supporting note | — |
| `compare` | column title | column subtitle | children = column bullets | — |
| `chart` | — | — | body is a Markdown table: first column = categories, other columns = series | type, then title |
| `diagram` | `A -> B` edge, or a node | node caption (node lines only) | free lines `group Label: a, b` | `focus=A,B`, `dir=tb` |
| `lanes` | year (`2021`) | item name | `lane: …`, `note: …` | year range `2017-2026`, `ticks=…`, `focus=…` |
| `mapping` | `Problem -> Solution` | — | — | `neutral` (palette colours instead of red/green) |
| `stack` / `pyramid` / `funnel` | level name | description | — | — |
| `matrix` | quadrant title (TL, TR, BL, BR) | description | — | `x=label y=label` |
| `cycle` | stage | description | — | centre label |
| `progress` | label | `80%` | — | — |
| `compare` | column title | column subtitle | children = column bullets | `tone` (positive / negative columns) |

### diagram

~~~markdown
```diagram focus=Cross-attention
- Noisy input -> Encoder
- Condition -> Embedding
- Encoder -> Cross-attention
- Embedding -> Cross-attention
- Cross-attention -> Decoder
group Denoiser: Encoder, Cross-attention, Decoder
```
~~~

Nodes are laid out left → right by dependency (`dir=tb` for top → bottom). `focus=` highlights
nodes and dims the rest; groups draw a dashed frame with a label.

### lanes

Use a lane timeline to compare baseline methods or related work by model family and publication year.
Each lane gets a theme-colored band; methods are native PowerPoint pills with an optional venue note.
Colliding pills and their notes stack into rows, and crowded lanes receive more vertical space.

~~~markdown
```lanes 2017-2026 focus=Our model
- 2017 | Baseline A | lane: Graph models | note: Conference A
- 2020 | Baseline B | lane: Diffusion models | note: Conference B
- 2026 | Our model | lane: Diffusion models | note: This work
```
~~~

The default axis is proportional to the year range (inferred from items when omitted).
`focus=Name` uses the theme's positive tone to highlight a method without fading its peers;
comma-separated names highlight several methods.

For sparse older work and a crowded recent period, give explicit, increasing ticks:

~~~markdown
```lanes ticks=2018,2022,2023,2024,2025 focus=Our model
- 2012 | Earlier work | lane: Sequence models | note: Conference A · 2012
- 2024 | Recent work | lane: Language models | note: Conference B
- 2025 | Our model | lane: Language models | note: This work
```
~~~

Explicit ticks are equally spaced. Skipped years show an axis break; dates between ticks interpolate
within that interval. Items older/newer than the endpoints share the first/last tick, labelled with
≤/≥, so include their actual year in `note:` when useful. Keep a normal range when proportional
elapsed time matters. Use one visual per slide for a dense comparison; split it if labels become small.
The template engine preserves year, family, method and note as a table.
See `examples/model-timeline.md` for a complete three-family example.

## Example

~~~markdown
#### Shifting habits | Industry trend

Takeaway and delivery keep growing; small cafés face ==staffing== and ==digital== pressure.

- Short-staffed: **slow service at peak**
- No data: **stock ordered by gut feel**

```cards stack
- Chain A | Member app, mobile pay, points | tag: more repeat visits | img: assets/logo-a.png
- Café B | Pre-order, pick-up | tag: no queue
```

> [!NOTE] Waiting time = order to pick-up.

Source: author's survey, 2026.
~~~

## Never

- Use emoji anywhere (the build fails). Use `icon:` instead.
- Invent values for `stats` or `chart`. Use `— value —` and report it.
- Delete or reword the user's sentences in verbatim mode (converting structure is fine).
