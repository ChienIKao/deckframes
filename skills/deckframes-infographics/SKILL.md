---
name: deckframes-infographics
description: >
  Decide which deckframes infographic block fits each slide's content (cards, steps, timeline, flow,
  stats, compare, chart, tables, callouts, statement slides) and write its syntax. Use while shaping
  deck.md so slides show one visual idea instead of walls of bullets.
---

# Content → infographic

For every slide ask: *is this content parallel items, a comparison, a transformation, a process,
numbers, or a conclusion?* Then pick the block. Plain argumentation stays as bullets — don't force
a visual.

| Content shape | Block |
|---|---|
| Parallel examples (companies, cases, products) | ```` ```cards stack ```` with `tag:` and `img:` |
| N problems / pain points / highlights | ```` ```cards ```` with `icon:` |
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
| Screenshots, architecture, plots | `![caption](assets/x.png)` |
| The core message | a lone `> quote` → quote card |

## Composition rules

- Text left, one visual right is the default and the most common layout.
- ≤ 5 bullets beside a visual; more → split the slide or move detail into `<!-- notes -->`.
- One visual per slide (two images may sit side by side); extra visuals get their own slides.
- One callout per slide, always at the bottom.

## Item syntax

Inside a block, one list item per element; fields are separated by ` | `:

```
- Title | Description | extra… | tag: label | img: path | icon: ?
  - child line (card / compare-column bullets)
```

| Block | 1st field | 2nd field | extra / children | Options after the block name |
|---|---|---|---|---|
| `cards` | card title | one-line description | bullet details | `stack`, `grid`, `cols=3` |
| `steps` / `timeline` | step name | description | bullet details | `vertical`, `horizontal` |
| `flow` | node | small caption | — | `vertical`, `horizontal`; or one line `A -> B -> C` |
| `stats` | the number (`38`, `3.8%`, `2×`) | label | supporting note | — |
| `compare` | column title | column subtitle | children = column bullets | — |
| `chart` | — | — | body is a Markdown table: first column = categories, other columns = series | type, then title |

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

- Invent values for `stats` or `chart`. Use `— value —` and report it.
- Delete or reword the user's sentences in verbatim mode (converting structure is fine).
