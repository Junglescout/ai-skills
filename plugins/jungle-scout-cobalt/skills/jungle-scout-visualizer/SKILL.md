---
name: jungle-scout-visualizer
description: "Presentation standard for any data pulled from the Jungle Scout Cobalt connector/MCP server. Apply by DEFAULT every time Jungle Scout Cobalt data is about to be presented — raw pulls, ad hoc analyze_*/query_*/keyword calls (search_keywords_by_*, get_keyword_sov), AND the output of any other skill that runs on this data (a brand benchmark, a keyword analysis, and so on). Lead with a headline callout of the number(s) that answer the question; add a visualization when the data has a story a chart tells better than a sentence. There are exactly two opt-outs: the user explicitly asks you not to (e.g. 'just the number', a specific format), or the active skill explicitly enforces its own custom styling. In every other case these defaults apply — even inside another skill, even if the user didn't ask for a chart or callout."
---

# Data Display

How to present data pulled from the Jungle Scout MCP so the answer reads as a story, not a data dump. Every answer leads with the number that matters; visuals appear when they carry an argument a sentence can't.

This is a **default presentation layer**, not an analysis skill. It does not decide _what_ to pull or _what it means_ — it decides _how the result is shown_ once another skill (or a raw pull) has produced it.

## Precedence: apply by default, opt out by exception

This is the **default styling layer** for everything built on Jungle Scout Cobalt data. Apply it whenever such data is about to be presented — a raw MCP pull, an ad hoc call, or the report produced by another skill — without being told to.

When another skill drives the analysis, it owns _what_ is shown and _in what order_ (the sections, the metrics, the narrative); this skill owns _how it looks_ (the callout, palette, charts, tables). The two roles **compose** — they don't compete — so you apply these defaults inside another skill's structure by default.

**Stand down only in these two cases:**

1. **The user opts out.** They ask for "just the number," a table only, a specific chart type, or "don't format it." Honor that over these defaults.
2. **The active skill enforces its own custom styling.** If the skill driving the analysis has a section that *explicitly* defines its own palette, visuals, or output format, follow that skill's spec exactly and ignore this one — two styling standards fighting produces worse output than either alone.

A skill that merely defines **structure** (which sections appear, the metrics, the order) without enforcing styling is **not** an opt-out — that's the composing case above: follow its structure, style it with this skill. When in doubt, apply.

## The smart floor

Two tiers, applied every time:

1. **Callout — always.** Lead with the number(s) that directly answer the question, formatted as a metric callout (see `references/visuals.md`). The headline number is large and in the focal color; a one-line context sits beneath it. Even a one-number answer gets the callout treatment — it's the difference between "Quest did $14.2M" buried in a sentence and a number the eye lands on.

2. **Visualization — when it earns its place.** Add a chart when the data has shape a sentence flattens: a comparison, a ranking, a trend, a distribution, a composition — or a **stated or implied time window**. A window is shape: "revenue over the last 90 days" is not a bare scalar, because the metric moved across the weeks inside it. Lead with the **total** in the callout and support it with a **time series** over that same window. The only answers that stay callout-only are **point-in-time scalars with no window and nothing to compare** ("current ASP", "how many SKUs"). Over-visualizing (a bar chart with one bar, a pie with two slices) is as much a failure as under-visualizing.

Ask: _does a picture make the surrounding prose shorter?_ If yes, render it. If the chart would just restate the callout, skip it.

## Choosing the visualization

Match the chart to the question's shape. Default to the simplest form that carries the story.

Each "Use" below names a template that lives in `references/visuals.md` — the table and the templates share one vocabulary so there's no gap between what you pick and what's built for you.

| The data is…                                            | The question sounds like…                                         | Use                                                                                                                                   |
| ------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Ranking across entities                                 | "Top brands in…", "who's biggest", "where does X rank"            | **Ranking bar** — horizontal, sorted, focal in indigo                                                                                 |
| Distribution across ordered buckets                     | "by price tier", "by rating band"                                 | **Ranking bar, ladder mode** — natural order, top bucket first, story bucket highlighted                                              |
| Change over time, or a metric over a window             | "trend", "over the last N weeks", "revenue over the last 90 days" | **Trend line**, focal series in indigo; for a window, pair it with a callout for the **total** and mark/exclude a partial latest week |
| One entity's share of a whole                           | "what % of the category is X"                                     | **Donut share gauge** — focal slice indigo, rest gray, share number in the hole                                                       |
| Composition split across several entities               | "share breakdown by brand"                                        | **Stacked-100% share bar** — focal segment indigo, gray ramp for the rest                                                             |
| Focal vs. a benchmark, or one metric across two periods | "you vs. category", "this year vs. last", YoY                     | **Paired two-layer bar** — focal indigo, benchmark/prior gray; or a callout with a delta pill for a single entity                     |
| Two continuous metrics, many points                     | "price vs. revenue across ASINs"                                  | Scatter — build ad hoc; no standard template (the bias is the simplest shape that carries the story)                                  |
| A point-in-time scalar, no window or comparison         | "current ASP", "how many SKUs"                                    | **Callout only — no chart**                                                                                                           |

When in doubt between two chart types, pick the one with fewer moving parts. A clean bar beats a clever combo chart.

## Color: draw the eye to the focal entity

The Cobalt palette is the default. Full hex values, dark-mode variants, and Chart.js templates live in `references/visuals.md` — read it before your first `show_widget` call.

The one rule that matters most for this skill: **if there is a focal brand, keyword, or ASIN that everything else is being compared against, it gets the attention color (indigo `#5357F8`) and everything else recedes into gray.** The reader should find the subject of the question without being told which bar it is.

- Focal entity → **indigo `#5357F8`** (the focus brand's bars, its table value, its line)
- Comparison set → **gray `#BABABA`** — one gray for simple charts; a gray ramp (darkest = biggest) only when one chart must separate several competitors
- Positive growth → **green `#01765B`**, rendered as a pill with an up arrow
- Negative growth → **red `#D44343`**, rendered as a pill with a down arrow
- Secondary callout you want noticed → **orange `#FF5E00`** (a risk/opportunity flag — never the primary number, never growth)
- Focus entity's table row → tinted **`#F6F7FF`**, its name/value in indigo
- **No named focal?** When ranking sub-entities of a single subject (a brand's 3P sellers, a brand's ASINs, a category's brands) and the user named nothing to compare against, highlight the **leader** — or whichever row carries the story — in the focal color. Don't leave every bar identical; give the eye a place to land.

Lead with indigo; competitors stay gray. Growth is always a colored pill, never bar-end text. Don't rainbow — one focal indigo plus a recessive gray carries almost every chart.

## Rendering

Use `visualize:show_widget` with HTML + Chart.js — it resizes correctly on phone and laptop without per-device tuning, which hand-coded SVG does not. Load `read_me` with `modules=["chart"]` once at the start of a run. `references/visuals.md` ships the palette (light + dark), formatting helpers, the dark-mode swap, and a template for each thing this skill asks for: the metric callout, the growth pill, the **evidence table** (focal row tinted, growth pills in cells), the ranking bar (with ladder mode), the trend line, the paired two-layer bar (you vs. category), the donut share gauge, and the stacked-100% share bar.

## Structure of the answer

```
[HEADLINE — either a metric callout (focus number in indigo) OR a one-line
 insight headline ("BIC excels in the $0-$9 range") + a supporting sentence]

[Setup sentence: name what the visual below shows and why it answers the question.]

[VISUAL — only if it earns its place]

[Insight sentence: read the visual out — the one thing it tells you.]

[EVIDENCE TABLE — when there are rows worth scanning; focus row tinted, its value indigo]

[Closing line — offer the natural next cut, or "anything else you want from this?"]
```

- **Two ways to open.** A metric callout (the focus number in indigo, growth as a pill) when the answer is a number; or a narrative insight headline plus one supporting sentence when the answer is a finding. Both are house style — pick by what the question wants.
- **Bookend every visual.** A sentence before naming what it shows; a sentence after drawing the insight. The visual replaces a paragraph of description — it doesn't sit next to one.
- **Don't refer to visuals by number** ("as the chart above shows"). Name the thing: "the revenue bar," "the trend line."
- **Tables for evidence, prose for the argument.** Put scannable rows in a table; tint the focus row and put its value in indigo; show growth as green/red pills.
- **Round displayed numbers.** `$14.2M`, not `$14,238,991`. Use `toLocaleString` / `toFixed` in chart labels.

## Guardrails

- **One good visual beats three.** If three charts each show a slice, ask whether one chart with the focal entity highlighted would tell the whole story. Usually it would.
- **Callout context lines state one settled fact — never working-out.** "Biggest single slice in the category," not "more than the next two combined? no — A + B = 20.5%." The card shows a conclusion; reasoning stays out of it.
- **Don't fabricate to fill a layout.** If a pull is incomplete or a number is missing, say so in a line beneath the callout rather than inventing a bar. Honesty about the gap is more useful than a tidy-but-wrong chart.
- **Don't pad prose to justify a chart.** If a section has nothing a visual clarifies, the callout and a sentence are the whole answer.
- **Deduplicate multi-ASIN keyword pulls before counting** (known MCP behavior) — a chart built on undeduped rows overstates. Handle the dedup/join/compute in a bundled script or in code, not by eyeballing raw rows.

## Reference files

- `references/visuals.md` — Cobalt palette (light + dark hex), formatting helpers, the metric-callout and growth-pill blocks, the evidence-table template (focal row tinted, growth pills in cells), and Chart.js templates for the ranking bar (+ ladder mode), trend line, paired two-layer bar, donut share gauge, and stacked-100% share bar — plus the dark-mode detection swap. Read before the first `show_widget` call.
