# Visuals — Cobalt palette + render templates

The presentation toolkit for `data-display`. Copy a block, swap in the data, ship it
inside `visualize:show_widget`. Every template assumes one focal entity drawn in indigo
with everything else receding to gray — that single contrast does most of the work.

Read this once at the start of a run, before your first `show_widget` call.

## Contents
- [Palette](#palette) — light + dark hex, what each color means
- [Theme setup + dark-mode swap](#theme-setup--dark-mode-swap) — the token object every template reads from
- [Formatting helpers](#formatting-helpers) — rounding `$14.2M`, not `$14,238,991`
- [Metric callout](#metric-callout) — the headline number; used on every answer
- [Growth pill](#growth-pill) — green up / red down; used inline and in table cells
- [Evidence table](#evidence-table) — scannable rows, focal row tinted, pills in cells
- [Ranking bar](#ranking-bar) — ranking across entities; ladder mode for ordered buckets
- [Trend line](#trend-line) — change over time / a metric over a window
- [Paired two-layer bar](#paired-two-layer-bar) — focal vs. a benchmark, or two periods
- [Donut share gauge](#donut-share-gauge) — one entity's share of a whole
- [Stacked-100% share bar](#stacked-100-share-bar) — composition split across entities
- [Scatter](#scatter) — two continuous metrics, many points (ad hoc, not a standard template)

---

## Palette

The Cobalt palette. Each color has a job — the point of the system is that color *means*
something, so the reader decodes the chart without a legend. Don't introduce colors outside
this set; the discipline is what makes the focal entity findable.

| Token | Role | Light | Dark |
|---|---|---|---|
| `focal` | The subject of the question — its bar, line, share, table value | `#5357F8` | `#8A8DFF` |
| `comparison` | Everything being compared against the focal — recedes | `#BABABA` | `#5A5A66` |
| `positive` | Positive growth (always a pill with an up arrow) | `#01765B` | `#3DD9A8` |
| `negative` | Negative growth (always a pill with a down arrow) | `#D44343` | `#FF6B6B` |
| `flag` | A risk/opportunity you want noticed — never the primary number, never growth | `#FF5E00` | `#FF8A3D` |
| `focalRow` | Tint behind the focal entity's table row | `#F6F7FF` | `#1E1F3A` |
| `ink` | Primary text, axis labels, the callout number | `#1A1A2E` | `#ECECF2` |
| `muted` | Secondary text, context lines, non-focal axis labels | `#6B6B7B` | `#9A9AAB` |
| `grid` | Gridlines, table borders | `#E8E8EE` | `#2A2A38` |

The dark-mode hexes are tuned for contrast on a dark surface — the focal indigo and the
growth colors brighten so they still pop, the grays and grid darken. If Cobalt has canonical
dark values that differ, swap them into the token object below in one place and every
template inherits them.

A gray *ramp* (instead of one flat `comparison` gray) is only for the rare chart that must
separate several competitors at once — darkest gray = biggest competitor. Default to a single
gray; a ramp is a last resort, not a habit.

---

## Theme setup + dark-mode swap

Drop this once at the top of the widget. Every template below reads `C.focal`, `C.grid`, etc.,
so light/dark is decided in exactly one place and the rest of the code never branches on theme.

```html
<script>
  const DARK = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const C = DARK ? {
    focal:'#8A8DFF', comparison:'#5A5A66', positive:'#3DD9A8', negative:'#FF6B6B',
    flag:'#FF8A3D', focalRow:'#1E1F3A', ink:'#ECECF2', muted:'#9A9AAB', grid:'#2A2A38'
  } : {
    focal:'#5357F8', comparison:'#BABABA', positive:'#01765B', negative:'#D44343',
    flag:'#FF5E00', focalRow:'#F6F7FF', ink:'#1A1A2E', muted:'#6B6B7B', grid:'#E8E8EE'
  };
  // Chart.js global defaults so every chart inherits theme text color + font
  if (window.Chart) {
    Chart.defaults.color = C.muted;
    Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif";
    Chart.defaults.font.size = 13;
  }
</script>
```

Keep the widget background transparent so it sits cleanly on whatever surface the host renders
on — don't paint a white card behind the chart.

---

## Formatting helpers

Displayed numbers are rounded and human — `$14.2M`, `12.4K units`, `+18%` — never the raw
`$14,238,991`. Put these helpers next to the theme block and call them in every label and
callout.

```html
<script>
  const fmtUSD = n => {
    const a = Math.abs(n);
    if (a >= 1e9) return '$' + (n/1e9).toFixed(1) + 'B';
    if (a >= 1e6) return '$' + (n/1e6).toFixed(1) + 'M';
    if (a >= 1e3) return '$' + (n/1e3).toFixed(1) + 'K';
    return '$' + Math.round(n).toLocaleString();
  };
  const fmtNum = n => {
    const a = Math.abs(n);
    if (a >= 1e6) return (n/1e6).toFixed(1) + 'M';
    if (a >= 1e3) return (n/1e3).toFixed(1) + 'K';
    return Math.round(n).toLocaleString();
  };
  const fmtPct = n => (n > 0 ? '+' : '') + n.toFixed(1) + '%';
</script>
```

---

## Metric callout

The headline. Lead with the one number that answers the question, large and in `ink` (the focus
*number* is the hero; indigo is reserved for it when it's also the focal entity's value). One
context line beneath states a single settled fact — a conclusion, never the working-out. Optional
growth pill sits inline with the number.

```html
<div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;">
  <div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;">
    <span style="font-size:48px;font-weight:700;line-height:1;color:#5357F8;letter-spacing:-0.02em;">
      $14.2M
    </span>
    <!-- optional: drop a growth pill here -->
  </div>
  <div style="margin-top:8px;font-size:14px;color:#6B6B7B;">
    Quest's trailing-90-day revenue in Sports Nutrition Protein Bars
  </div>
</div>
```

- The number color is `ink` by default; use `focal` (indigo) when the number *is* the focal
  entity's value, so the callout and the chart's focal bar read as the same subject.
- The context line carries one fact. Not "more than the next two combined? no — A+B=20.5%."
  That reasoning belongs in your prose, not on the card.
- If a pull is incomplete, say so here ("excludes the partial current week") rather than
  inventing a number to fill the slot.

---

## Growth pill

Growth is *always* a pill — never bar-end text, never a bare number. Green + up arrow for
positive, red + down arrow for negative. The arrow makes direction readable before the eye
parses the digits.

```html
<!-- positive -->
<span style="display:inline-flex;align-items:center;gap:3px;padding:3px 9px;border-radius:999px;
  font-size:13px;font-weight:600;background:rgba(1,118,91,0.12);color:#01765B;">
  ▲ +18.4%
</span>

<!-- negative -->
<span style="display:inline-flex;align-items:center;gap:3px;padding:3px 9px;border-radius:999px;
  font-size:13px;font-weight:600;background:rgba(212,67,67,0.12);color:#D44343;">
  ▼ −6.2%
</span>
```

In dark mode swap the text colors to `positive`/`negative` dark hexes and keep the same
translucent background (the `rgba(...,0.12)` tint works on either surface).

---

## Evidence table

Use when there are rows worth scanning — a leaderboard, a set of ASINs, competitors around the
focal entity. The table carries the evidence; your prose carries the argument. The whole point of
the styling is that the reader's eye lands on the focal row without being told which one it is:
its row is tinted `focalRow`, its name and key value go indigo, everyone else stays neutral.

```html
<table style="width:100%;border-collapse:collapse;font-family:-apple-system,BlinkMacSystemFont,
  'Segoe UI',system-ui,sans-serif;font-size:14px;">
  <thead>
    <tr style="text-align:left;color:#6B6B7B;font-size:12px;text-transform:uppercase;
      letter-spacing:0.04em;border-bottom:1px solid #E8E8EE;">
      <th style="padding:8px 12px;font-weight:600;">Brand</th>
      <th style="padding:8px 12px;font-weight:600;text-align:right;">Revenue</th>
      <th style="padding:8px 12px;font-weight:600;text-align:right;">Share</th>
      <th style="padding:8px 12px;font-weight:600;text-align:right;">YoY</th>
    </tr>
  </thead>
  <tbody>
    <!-- non-focal row -->
    <tr style="border-bottom:1px solid #E8E8EE;color:#1A1A2E;">
      <td style="padding:10px 12px;">Barebells</td>
      <td style="padding:10px 12px;text-align:right;">$22.7M</td>
      <td style="padding:10px 12px;text-align:right;">19.1%</td>
      <td style="padding:10px 12px;text-align:right;">
        <span style="display:inline-flex;align-items:center;gap:3px;padding:2px 8px;border-radius:999px;
          font-size:12px;font-weight:600;background:rgba(1,118,91,0.12);color:#01765B;">▲ +31%</span>
      </td>
    </tr>
    <!-- FOCAL row: tinted background, name + primary value in indigo -->
    <tr style="border-bottom:1px solid #E8E8EE;background:#F6F7FF;">
      <td style="padding:10px 12px;font-weight:700;color:#5357F8;">Quest</td>
      <td style="padding:10px 12px;text-align:right;font-weight:700;color:#5357F8;">$14.2M</td>
      <td style="padding:10px 12px;text-align:right;color:#1A1A2E;">12.0%</td>
      <td style="padding:10px 12px;text-align:right;">
        <span style="display:inline-flex;align-items:center;gap:3px;padding:2px 8px;border-radius:999px;
          font-size:12px;font-weight:600;background:rgba(212,67,67,0.12);color:#D44343;">▼ −6%</span>
      </td>
    </tr>
    <tr style="color:#1A1A2E;">
      <td style="padding:10px 12px;">Built Bar</td>
      <td style="padding:10px 12px;text-align:right;">$9.8M</td>
      <td style="padding:10px 12px;text-align:right;">8.3%</td>
      <td style="padding:10px 12px;text-align:right;">
        <span style="display:inline-flex;align-items:center;gap:3px;padding:2px 8px;border-radius:999px;
          font-size:12px;font-weight:600;background:rgba(1,118,91,0.12);color:#01765B;">▲ +12%</span>
      </td>
    </tr>
  </tbody>
</table>
```

- Tint and indigo apply to the **focal** row. If nothing was named to compare against, tint the
  **leader** (or whichever row carries the story) — never leave every row identical, the eye
  needs a place to land.
- Right-align numbers so columns scan vertically. Growth always rides in a pill cell, never raw.
- Round every value with the helpers. A table is for scanning, not for auditing to the dollar.
- For dark mode, swap `#E8E8EE`→`C.grid`, `#F6F7FF`→`C.focalRow`, `#1A1A2E`→`C.ink`,
  `#6B6B7B`→`C.muted`, `#5357F8`→`C.focal`. (When generating dynamically, template these from `C`
  rather than hardcoding — the literals above are just for legibility.)

---

## Ranking bar

For "top brands," "who's biggest," "where does X rank." Horizontal bars, sorted longest-to-shortest,
focal entity in indigo and everyone else gray. Horizontal (not vertical) because entity labels read
cleanly on the left and the length comparison is what matters.

**Ladder mode** — for distribution across *ordered buckets* ("by price tier," "by rating band"),
use the same template but **don't sort by value**: keep the buckets in their natural order with the
top bucket first, and highlight the bucket that carries the story.

```html
<div style="max-width:640px;"><canvas id="rankBar"></canvas></div>
<script>
  const labels = ['Barebells','Quest','Built Bar','One','Pure Protein'];
  const values = [22.7, 14.2, 9.8, 7.1, 5.4];   // $M
  const focalIdx = 1;                             // Quest
  new Chart(document.getElementById('rankBar'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: values.map((_, i) => i === focalIdx ? C.focal : C.comparison),
        borderRadius: 4, barThickness: 22
      }]
    },
    options: {
      indexAxis: 'y', responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => fmtUSD(ctx.raw * 1e6) } }
      },
      scales: {
        x: { grid: { color: C.grid }, ticks: { callback: v => '$' + v + 'M' } },
        y: { grid: { display: false }, ticks: { color: C.ink } }
      }
    }
  });
</script>
```

---

## Trend line

For "trend," "over the last N weeks," "is it growing," and for a metric **over a time window**
(pair it with a callout showing the window's total). Focal series in indigo; if you overlay a
comparison series (e.g. category), it stays gray. Mark or drop a partial latest week so a
half-finished bar doesn't read as a real dip.

```html
<div style="max-width:680px;"><canvas id="trend"></canvas></div>
<script>
  const weeks = ['Mar 30','Apr 6','Apr 13','Apr 20','Apr 27','May 4','May 11','May 18'];
  const focal = [1.5, 1.6, 1.55, 1.7, 1.62, 1.48, 1.51, 1.44]; // $M/wk
  new Chart(document.getElementById('trend'), {
    type: 'line',
    data: {
      labels: weeks,
      datasets: [{
        data: focal, borderColor: C.focal, backgroundColor: C.focal,
        borderWidth: 2.5, pointRadius: 0, pointHoverRadius: 4, tension: 0.25
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => fmtUSD(ctx.raw * 1e6) } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: C.muted } },
        y: { grid: { color: C.grid }, ticks: { callback: v => '$' + v + 'M', color: C.muted } }
      }
    }
  });
</script>
```

To overlay the category as context, add a second dataset with `borderColor: C.comparison`,
`borderDash: [4,4]` — the focal series stays solid indigo and reads as the subject.

---

## Paired two-layer bar

For "you vs. category," "this year vs. last," YoY, or any one-metric-across-two-conditions
comparison. Two bars per group: the focal condition in indigo, the benchmark/prior in gray.
This absorbs the old "grouped bar (current vs. prior)" case — same shape, named consistently.

```html
<div style="max-width:640px;"><canvas id="paired"></canvas></div>
<script>
  const groups = ['Revenue','Units','ASP'];
  new Chart(document.getElementById('paired'), {
    type: 'bar',
    data: {
      labels: groups,
      datasets: [
        { label: 'Quest',    data: [14.2, 410, 34.6], backgroundColor: C.focal,      borderRadius: 4 },
        { label: 'Category', data: [11.8, 360, 32.8], backgroundColor: C.comparison, borderRadius: 4 }
      ]
    },
    options: {
      indexAxis: 'y', responsive: true,
      plugins: { legend: { position: 'top', labels: { color: C.muted, boxWidth: 12 } } },
      scales: {
        x: { grid: { color: C.grid }, ticks: { color: C.muted } },
        y: { grid: { display: false }, ticks: { color: C.ink } }
      }
    }
  });
</script>
```

Here the legend earns its place because two conditions share the chart — this is the one
template where a legend is worth the ink.

---

## Donut share gauge

For "what % of the category is X" — one entity's share of a whole. The focal slice is indigo,
the remainder is a single gray "everyone else." A donut (not a full pie) leaves a center hole
for the share number, which is the actual answer.

```html
<div style="max-width:280px;position:relative;">
  <canvas id="share"></canvas>
  <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;
    justify-content:center;pointer-events:none;">
    <span style="font-size:32px;font-weight:700;color:#5357F8;">12.0%</span>
    <span style="font-size:12px;color:#6B6B7B;">Quest share</span>
  </div>
</div>
<script>
  new Chart(document.getElementById('share'), {
    type: 'doughnut',
    data: {
      labels: ['Quest','Rest of category'],
      datasets: [{ data: [12.0, 88.0], backgroundColor: [C.focal, C.comparison], borderWidth: 0 }]
    },
    options: { cutout: '72%', responsive: true, plugins: { legend: { display: false } } }
  });
</script>
```

Reserve the donut for a **single focal share vs. the rest**. When you need to split a whole
across several named entities, use the stacked-100% bar below — a donut with 5+ slices is a
legend hunt, exactly the thing this palette exists to avoid.

---

## Stacked-100% share bar

For composition split across several entities — "share breakdown by brand." One horizontal bar
totaling 100%, focal segment in indigo, the rest in a gray ramp (darkest = largest competitor)
so adjacent segments stay distinguishable without a rainbow.

```html
<div style="max-width:680px;"><canvas id="stack"></canvas></div>
<script>
  // focal first so it anchors the left edge; grays ramp by size after it
  const segs = [
    { name:'Quest',        val:12.0, color:C.focal },
    { name:'Barebells',    val:19.1, color:'#8A8A8A' },
    { name:'Built Bar',    val:8.3,  color:'#A6A6A6' },
    { name:'One',          val:6.0,  color:'#BABABA' },
    { name:'Others',       val:54.6, color:'#D6D6D6' }
  ];
  new Chart(document.getElementById('stack'), {
    type: 'bar',
    data: {
      labels: ['Category'],
      datasets: segs.map(s => ({
        label: s.name, data: [s.val], backgroundColor: s.color, borderWidth: 0
      }))
    },
    options: {
      indexAxis: 'y', responsive: true,
      scales: {
        x: { stacked: true, max: 100, grid: { display: false }, ticks: { callback: v => v + '%' } },
        y: { stacked: true, grid: { display: false }, display: false }
      },
      plugins: {
        legend: { position: 'bottom', labels: { color: C.muted, boxWidth: 12 } },
        tooltip: { callbacks: { label: ctx => ctx.dataset.label + ': ' + ctx.raw + '%' } }
      }
    }
  });
</script>
```

In dark mode, build the gray ramp from the dark `comparison` family rather than the light hexes
above (e.g. `#6E6E7A` → `#3A3A46`); keep the focal segment on `C.focal`.

---

## Scatter

For two continuous metrics across many points ("price vs. revenue across every ASIN"). There's
**no standard template** here on purpose — scatter is an edge case, and the skill's bias is the
simplest shape that carries the story. When you genuinely need it, build it ad hoc: focal points
in `C.focal`, the rest in `C.comparison`, axis labels formatted with the helpers. If you find
yourself reaching for scatter often, that's a signal to add a vetted template here.
