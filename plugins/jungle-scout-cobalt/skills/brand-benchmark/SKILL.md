---
name: brand-benchmark
description: "Benchmark a brand against its Amazon category — position, growth vs. category, competitive neighborhood (peers around its rank), price posture, and portfolio breadth. Use whenever the user asks how a brand is performing in a category, how it compares to peers, how it stacks up against category growth, or wants a 'state of the brand' snapshot. Produces a concise executive summary with two standard visuals (position bar with rank, price ladder) and offers deeper paths from there. Diagnostic-adjacent but lighter than share-diagnosis: answers 'where does this brand stand?' not 'why did it move?'"
---

# Brand Benchmark

## Purpose

Position a brand against its category in one screen: rank, growth vs. category, neighborhood, price, portfolio breadth. Outputs an executive summary with two fixed visuals. Diagnostic-adjacent, not diagnostic — does not explain *why* movement happened. For that, route to `share-diagnosis`.

## When to use

Trigger when the user asks any of:
- "How is [brand] doing in [category]?"
- "Benchmark [brand] against the category"
- "How does [brand] compare to peers?"
- "Is [brand] keeping up with category growth?"
- "Where does [brand] sit in [category]?"

Do **not** use for: share-movement diagnosis (use `share-diagnosis`), category sizing without a focal brand (use `analyze_categories` directly), forecasting, or "what should I do" plays.

## Scoping

Send all questions in one message via `ask_user_input_v0`. Defaults locked — only ask if missing or ambiguous.

1. **Brand & category.** Brand name (lowercase will be normalized) and Amazon category leaf, or representative ASINs to resolve. If the user gave a brand without a leaf, run the leaf-footprint check in Step 0 to identify the **anchor leaf** (largest-revenue leaf). If the brand is meaningfully split (top leaf <2x the second-largest leaf by revenue), surface the top 3 leaves and ask which to anchor on. Otherwise anchor automatically and note the choice in ASSUMPTIONS.
2. **Time window.** Default: trailing 90 days (`period: "last_90_days"`, anchored by the MCP to the latest complete market-analysis week — see Step 1) vs. the same window a year ago. Override on request.
3. **Neighborhood depth.** Default: brand ±3 ranks. Override to top-5 / top-10 if requested.

If user says "just run it": use defaults, surface assumptions in output.

## Procedure

### Step 0: Resolve brand + category

- `list_orgs` → `org_id`. **If more than one org is returned, do not stop to ask** — market-analysis estimates are org-independent (the underlying sales data is identical across orgs), so the choice doesn't affect results. Default to the first org (or a known house default) and note it in passing. Only ask if the user explicitly cares which org is billed/attributed.
- `search_categories_by_name` **only if the user gave a category name** (skip when they already gave a leaf ID); confirm it's a leaf node, not a parent.
- **Do not make a separate call to validate the brand in the leaf.** Step 1's B (the ranked list) already returns the focal brand with its share and rank — apply the 2% floor from there. The floor tests the brand's **share value (<2%), not its mere presence in the rows**: a brand can sit inside the top 50 and still be sub-scale (e.g. a brand at rank 17 with 0.85% share is present but fails the floor). Flag sub-scale when share <2% — whether the brand is a low-share row in B or absent from B's top 50 entirely → offer to widen scope.

**Multi-leaf brand check (when user didn't specify a leaf):**
- Run `analyze_categories` with `filters={brand_query: <brand>}` (no `category_ids`), `detail_level: "summary"`, `include_enrichments: []`, `sort_by: "revenue"` to get the brand's **leaf-by-leaf footprint** — one row per leaf the brand sells in, with revenue per leaf. This is the only extra data call, and only in the no-leaf path.
  - **Use `analyze_categories`, not `analyze_brands`, for this.** `analyze_brands(brand_query=…)` returns *brand-grain* rows (the brand plus name-variants/accessory brands), each with revenue aggregated across all categories — it has no per-leaf breakdown and cannot identify an anchor leaf. `analyze_categories(brand_query=…)` returns the per-leaf split, which is what this step needs.
  - With no `category_ids` filter, each leaf row's `market_share` reads as **the leaf's share of the brand's own total revenue** — use it directly for the "% of brand's Amazon revenue" figures in ASSUMPTIONS.
- Identify the **anchor leaf** = the leaf with the highest brand revenue. This is the default.
- **If the top leaf is clearly dominant** (revenue ≥2x the second-largest leaf) → anchor there automatically. Note the choice in ASSUMPTIONS.
- **If the brand is meaningfully split** (top leaf <2x the second-largest leaf, e.g. Neutrogena across Cloths & Towelettes, Cleansers, Moisturizers) → surface the top 3 leaves via `ask_user_input_v0` and ask which to anchor on. In the conversational message before the options, note that they can name a smaller leaf in chat if their target isn't in the top 3. Don't guess.
  - **Duplicate-name guard:** the footprint frequently returns multiple *distinct leaf IDs that share the same display name* — the catalog's parallel men's/women's/kids'/unisex subtrees (e.g. Crocs returns "Mules & Clogs" / "Clogs & Mules" four times across different leaf IDs). This is an artifact of `detail_level: "summary"` truncating the leaf name to its last segment. If two or more anchor candidates share a name, call `get_categories_by_ids` on the tied leaf IDs — its `name` field returns the full, disambiguated label ("Women's Mules & Clogs", "Men's Mules & Clogs", "Boys' Clogs & Mules", etc.; `path_by_name` carries the full breadcrumb if you need more). Present those disambiguated names in the ask. Never show two identically-labeled options.
  - When duplicate-named leaves are *individually* small but collectively dominant (e.g. four clog leaves that together are 57% of the brand but each ~10–25%), note in the conversational message that the brand's clog business is split across several catalog leaves, and offer to anchor on the largest single leaf or treat them together — don't silently anchor on just one and imply it's the whole clog presence.
- **If the user says "just run it"** on a multi-leaf brand → anchor on the largest-revenue leaf and surface the assumption.
- The **top 3 other leaves** where the brand holds ≥2% share are listed in ASSUMPTIONS as out-of-scope context. If more than 3 exist, append "(+N more)" rather than enumerating all — readers don't need a 50-line appendix for sprawling brands.

**Quality checks — evaluated on the Step 1 pulls (A/B/C), not separate calls:**
- Category revenue ≥ $500K in window — else noise risk (from A)
- Brand count ≥ 10 — else survivorship risk (from A)
- Category revenue growth between −50% and +100% YoY — else taxonomy drift suspected (from A)
- Price-tier dispersion: max-tier ASP / min-tier ASP across the tiers in C. **5–8x → informational note** in ASSUMPTIONS ("category spans a wide price range; competitive comparisons span segments"). **>8x → flag** in ASSUMPTIONS ("competitive set may not be truly competitive — incompatible segments"). Under 5x = silent. (from C)
- Latest-week freshness: handled in Step 1 — never pass hand-computed dates to the category/brand calls; let the MCP anchor `end_date` to the latest complete week and read that window back. Do not anchor to a date inferred from training-era assumptions about "now" — that is how the window drifts a year stale.

**Conditional check (costs one extra `analyze_products` call — run ONLY if a cheap signal already looks off):** Leaf title coherence — when category growth is implausible, brand-count is unstable, or tier dispersion is >5x, spot-check the top 10 ASINs by revenue; if >30% of revenue is products that don't match the leaf name (e.g. mass gainers in a whey-protein leaf), flag as a noisy leaf. In clean categories, skip it — the cheap signals above already guard most noise.

Quality flags surface in ASSUMPTIONS → Data quality, not in the FLAGS section. They weaken affected claims rather than describing competitive movement.

### Step 1: Pull the benchmark pack

Three queries (A, B, C). **Do not hand-compute `start_date`/`end_date`.** `analyze_categories` and `analyze_brands` default `end_date` to the latest complete market-analysis week and accept a `period` enum — let them do the anchoring. Passing explicit dates overrides that freshness default, and a date inferred from training-era assumptions about "now" is exactly how the window silently drifts a year stale.

- **A and B** — pass `period: "last_90_days"` and **omit `start_date`/`end_date`**. Run in parallel; no data dependency between them.
- **C** (`analyze_price_tiers`) — the exception: it *requires* explicit `start_date`/`end_date` and has no freshness default. Run it *after* A, using the exact window A resolved to.

**Read the resolved window from A's response** — it is echoed in the response header as `(YYYY-MM-DD to YYYY-MM-DD)`. Use those exact dates for C and for the ASSUMPTIONS "Window" line; never print a hand-computed range.

**Freshness sanity check** — the resolved `end_date` should be within ~2 weeks of today. If it is more than ~6 weeks stale, stop and flag: that signals a connector/query problem, not normal data lag. Do not emit a brief on a silently stale window.

**Performance — two waves, lean payloads.** The whole pull is two waves: A and B fire together (Wave 1), then C on A's resolved window (Wave 2). Both A and B run `detail_level: "summary"` with `include_enrichments: []`, which drops the unused brand/category enrichment block — the single largest part of each response — with no loss of any field the brief uses. Do not add a brand-validation call or an always-on ASIN pull (see Step 0). A typical single-leaf run is four calls total: `list_orgs`, [`search_categories_by_name` only if given a name], A∥B, C.

**A. Category totals (with YoY comparison)**
```
analyze_categories(
  filters={category_ids: [leaf_id]},
  options={
    period: "last_90_days",          # omit start_date/end_date — MCP anchors to latest complete week
    comparison: "year_ago",
    detail_level: "summary",
    include_enrichments: [],          # drop top_brand block — unused, large
    extra_metrics: ["revenue_growth", "units_sold_growth",
                    "market_share_growth", "avg_price_growth",
                    "brand_count", "product_count"]
  }
)
```

**B. Brand ranked list (for neighborhood)**
```
analyze_brands(
  filters={category_ids: [leaf_id]},
  options={
    period: "last_90_days",          # omit start_date/end_date — MCP anchors to latest complete week
    comparison: "year_ago",
    detail_level: "summary",
    include_enrichments: [],          # drop top_category block — unused, ~half the payload
    sort_by: "revenue",
    limit: 50,
    extra_metrics: ["revenue_growth", "market_share_growth",
                    "avg_price_growth", "product_count"]
  }
)
```
Identify the brand's rank. Slice ±3 around it (so brand is row 4 of 7 in a balanced view; edge cases: if brand is rank 1–3, show rank 1–7; if near tail, show last 7).

**C. Price tiers (category + brand overlay)** — runs *after* A; this tool requires explicit dates, so pass the exact window A resolved to.
```
analyze_price_tiers(
  filters={category_id: leaf_id, brand: brand_stable},
  options={start_date, end_date}     # the exact window A resolved to
)
```

**Innovation: cut for now.** New-launch counts via `revenue_growth: null` proxy are unreliable — parent-ASIN re-parenting and consolidation create false positives. Until `first_date_available` is exposed in the MCP, omit the Innovation Pulse section. Replace with a one-line "Portfolio breadth" metric using `product_count` from `analyze_brands` — honest, no proxy.

### Step 2: Compute the headline metrics

- **Growth multiple** = brand revenue growth % ÷ category revenue growth %. Express as "Nx faster than category" (humans read multiples, not ratios). Handle sign edge cases in words: brand +5% in -3% category → "outperforming a declining category"; brand -3% in +5% category → "declining in a growing category". **For same-sign multiples below 1× (brand growing but slower than category), narrate in words rather than printing the decimal** — "0.35× faster" is clumsy; say "growing at about a third of the category's pace" (or "roughly half," "about a quarter," as the ratio warrants).
- **Share Δ** in percentage points (pp), not %.
- **Share-transfer match** — if brand share Δ is negative, scan **all brands in B sorted by share Δ** (not just the top 5 by revenue) for the largest positive share Δ. The dominant recipient is frequently outside the top 5 by revenue — a fast-growing rank-6+ brand can be the real recipient (e.g. a rank-6 gainer at +2.4pp absorbing a −2.1pp loss). Take the largest share-gainer regardless of its revenue rank. If |gainer Δ| is **between 70% and 120%** of |brand Δ| (asymmetric — captures dominant-recipient cases where the gainer absorbed most of the loss without exceeding it by more than 20%), run a **tier-alignment check** before calling it a 1:1 transfer:
  - **Same tier** — gainer's home price tier (from `analyze_price_tiers`) matches the focal brand's home tier, OR ASPs are within 20% of each other → **displacement.** Name the recipient in the headline: "X's loss almost perfectly mirrors Y's gain."
  - **Different tier** — different tier label AND ASPs differ by >20% → **tier migration, not displacement.** The category moved; the gainer was positioned in the right tier, the focal brand wasn't. Headline reads: "[Focal] lost [N]pp share, but the recipient sits in a different price tier — the category migrated from [focal tier] ([X]% YoY) to [gainer tier] ([Y]% YoY), and [gainer] was positioned in the growing tier."
  
  Same logic in reverse for share-gaining brands: identify the largest share-shedder, then check tier alignment. Diffuse loss (no recipient between 70% and 120% of focal brand Δ) is its own signal — say so.
- **Price premium/discount vs. category ASP** = (brand ASP − category weighted ASP) ÷ category weighted ASP. Category weighted ASP = category revenue ÷ category units. Also note brand's home price tier and whether that tier is growing or contracting.
- **Home tier definition.** Home tier = tier containing the brand's weighted ASP — *unless* that tier holds <10% of brand revenue. In that case the brand is **bimodal** (weighted ASP falls between two concentrated tiers with little volume in between); redefine home tier as the **largest-revenue tier** and note the bimodal pattern in price-posture prose: "Brand ASP falls between two concentrated tiers — [tier A] ([X]% of brand revenue) and [tier B] ([Y]%) — with little volume in the ASP-implied tier." Optimum Nutrition in Whey Protein is the canonical example: ASP $54 places it in $45–55 (1.5% of revenue), but 39% lives in $70+ and 35% in $35–45.
  - **Split-tier guard (ASP tier clears 10% but isn't the largest):** when the ASP-implied tier holds ≥10% of brand revenue but is **not** the brand's largest-revenue tier, do **not** silently treat the ASP tier as the sole home. **Dual-surface both tiers** in price-posture prose — the ASP-implied tier and the largest-revenue tier — and report each tier's brand-vs-category growth, because they often diverge and neither alone tells the story. Example (Jack Link's in Jerky): ASP-implied home $14–22 holds 23.8% and is *losing* (−30% YoY vs category tier +6%), while the largest tier Under $14 holds 33.8% and is *winning* (+96% vs +67%). Surface both; do not let the tier-strand flag hinge on an arbitrary single-tier pick. **Evaluate tier-strand condition (c) against the largest-revenue tier** (where the brand's volume actually lives), and mention the ASP-tier divergence in prose rather than firing the flag off the smaller tier.
- **Portfolio breadth** = brand `product_count`. Compare against neighborhood median.
- **Rank Δ** = current rank − YoY rank.

### Step 3: Evaluate flags (1–3 max)

Trigger flags only when material. Surface in severity order; cap at 3.

**Tier 1 — Category-level** (highest severity — context that overrides individual brand signals):
- **Category contracting** — category revenue growth < −5% (overrides positive brand signals)
- **Top of category wobbling** — #1 or #2 brand shedding >1pp share, **provided that brand is NOT the focal brand**. When focal brand IS the wobbler, "Losing share in a growing category" captures the same signal at the right level — no redundant flag.

**Tier 2 — Competitive** (brand vs. peers in the market):
- **Losing share in a growing category** — brand share Δ < −0.5pp AND category revenue growth > +5%
- **Peer overtaking** — a brand ranked below moved up past the focal brand YoY
- **Tier strand** — fires when any of: (a) brand's home tier is contracting (tier YoY < −5%) while adjacent tiers grow (tier YoY > +10%) — structural strand; (b) brand's home tier YoY is **≥15pp behind category YoY** — tier lag (e.g. home tier +8% in a +28% category); (c) brand's revenue growth in its home tier is **≥20pp behind that tier's category-wide growth** — brand losing share inside its own band. Brand is in the wrong tier OR losing inside the right tier.

**Tier 3 — Operational** (brand-internal characteristics):
- **Concentration risk** — 60–80% of brand revenue in a single price tier OR a single parent ASIN line → **informational note** in ASSUMPTIONS ("X% of brand revenue concentrated in [tier/line]"). >80% → **Tier 3 flag** (existing severity).
- **Portfolio thin vs. peers** — brand `product_count` < 50% of neighborhood median (less depth = more risk if a SKU breaks)
- **Price drift** — fires when either: (a) **same-sign** — brand ASP change > 2x category ASP change; OR (b) **cross-sign** — brand and category ASP move in opposite directions AND brand ASP change ≥3% absolute, regardless of ratio. (Cross-sign branch exists because ratio-only rules misfire when category ASP barely moves: a small category move makes any brand divergence trip 2x, while a larger category move suppresses meaningful cross-sign divergence.)

**No flags fired** — surface a single positive: "No material flags. Tracking with category."

**Cap-at-3 logic** (mechanical): If more than 3 flags fire, take them in list order — Tier 1 first, then Tier 2, then Tier 3 — and drop overflow from the bottom. Within a tier, the listed order is the severity order. A Tier 1 flag, if it fires, always makes the cut.

### Step 4: Render output

See § Output format. Always render the two visuals (position → price). Portfolio breadth as a one-line metric, per § Notes.

## Output format

Each visual sits inside the narrative section where its data carries the argument — not in a top-loaded block. Each one is preceded by a sentence that names what it shows and followed by a sentence that draws the insight out. Visuals earn their place by making the surrounding prose shorter, not longer.

```
HEADLINE
[One sentence. Rank, growth-vs-category framing in "Nx faster" multiples, one tension or strength.]
[Headline number: realized revenue or share delta.]

FLAGS  (1–3 max; omit section if none triggered)
⚑ [Flag name] — [one-line evidence]

POSITION
[Two sentences setting up rank and competitive context — "Brand sits #X of Y in this leaf. The bar chart below shows how the top 10 stack up and where the brand's growth ranks against neighbors." If the focal brand's rank changed YoY, the rank callout above the chart includes "was #Z a year ago" inline (e.g. "#2 of 937 tracked brands · was #1 a year ago"). If rank is unchanged, just the current rank.]

[VISUAL 1: Position bar with rank callout]

[One sentence reading the visual: "Brand is #X by revenue but the only one in the top 5 with negative growth." Or "Top 5 are all green; the focal brand is the outlier."]

NEIGHBORHOOD (±3 ranks)
| Rank | Brand | Revenue | YoY % | Share | ASP |
| ...  | ...   | ...     | ...   | ...   | ... |
(focal brand row bolded; flag any row where YoY > +500% with an asterisk and a one-line footnote — "Likely taxonomy reclassification; treat rank as suspect")

PRICE POSTURE
[Two sentences naming the brand's ASP, premium/discount vs. category, and home tier — "Brand ASP $X sits in the $Y–$Z tier. The ladder below shows where the category's revenue concentrates and which tiers are growing or contracting."]

[VISUAL 2: Price ladder]

[One sentence reading the visual: "The brand's home tier is growing +16% but the brand's revenue inside that tier is flat — losing share in their own price band." Or "Brand sits in the only contracting tier while peer growth is concentrated in the $X+ band."]

PORTFOLIO BREADTH
- Brand: X products
- Neighborhood median: Y products
- [Wider / narrower / in line] than peers

[Closing line — single sentence. Name the fired flags as drill-down options; close with "or have a different question?". If fewer than 2 flags fire, the closing line may also reference the most-actionable concern surfaced in prose (e.g. a structural tier mismatch or a price divergence the rules didn't quite catch) — pattern is: fired flags first, prose-surfaced concerns to fill out to 2–3 drill-downs. If no flags AND no notable prose concerns, default to "Anything you want to drill into from here?"]

---

ASSUMPTIONS
- Window: [dates], comparison: YoY
- Anchor leaf: [id, name] — [X]% of brand's Amazon revenue
- Other top leaves (out of scope, ≥2% brand share): [top 3 by revenue, comma-separated; append "(+N more)" if more exist; omit line entirely if none]
- Brand share in anchor leaf: X% (≥2% threshold met / waived)
- Data quality: [flags fired or "clean"]
```

Tables for evidence. Prose around visuals carries the argument. Visuals always render in this order: position → price.

## The two visuals

Both use `visualize:show_widget` with HTML + Chart.js. Load `read_me` with `modules=["chart"]` once at start of run. Design constraints below are non-negotiable — they prevent drift across runs.

**Common constraints:**
- Chart.js UMD via cdnjs: `<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>`
- Hardcoded hex colors (canvas can't read CSS vars). Detect dark mode with `matchMedia('(prefers-color-scheme: dark)').matches` and swap the palette.
- **Palette — Jungle Scout brand, used by default (both modes defined).** Light mode: focal `#4A2DFF` (purple), peer/neighborhood `#40AFFF` (sky blue), other `#C9C9CB` (gray), text `#444441`, grid `rgba(0,0,0,0.06)`, positive growth `#007A6B` (teal), negative growth / laggard `#FF5E00` (orange). Dark mode: focal `#8B73FF`, peer `#40AFFF`, other `#5F5E5A`, text `#D3D1C7`, grid `rgba(255,255,255,0.08)`, positive `#2FB89E`, negative / laggard `#FF7A33`. Same brand hues in both modes — the dark values are lighter tints for legibility on dark backgrounds, not different colors. Detect with `matchMedia('(prefers-color-scheme: dark)').matches` and swap. Colors only — never adopt JS fonts, logos, or other brand elements. Use orange surgically: only for the focal brand's growth label when it is the laggard, and for a strand-flagged home tier; over-using orange kills the attention-direction effect.
- **Generic palette (external / white-label deliverables only — not Jungle Scout-internal).** Light mode: focal `#534AB7`, peer `#888780`, other `#D3D1C7`, text `#444441`, grid `rgba(0,0,0,0.06)`, positive `#0F6E56`, negative `#993C1D`. Dark mode: focal `#AFA9EC`, peer `#B4B2A9`, other `#5F5E5A`, text `#D3D1C7`, grid `rgba(255,255,255,0.08)`, positive `#5DCAA5`, negative `#F0997B`.
- Custom HTML legends above the chart (not Chart.js built-in legend — looks bulkier and uses round dots).
- Round all displayed numbers — `Math.round`, `.toFixed(n)`, `toLocaleString()`.
- Disable default Chart.js legend: `plugins: { legend: { display: false } }`.

### Visual 1 — Position bar with rank callout

Reads: "Where does the brand sit in the top 10, and what's the YoY direction of each?"

**Spec:**
- Above the chart, a metric callout: "BRAND RANK · **#X** · of Y tracked brands". Rank in focal color, 24px/500. **If the focal brand's rank changed YoY**, append "· was #Z a year ago" in the secondary text line (12–14px, secondary text color). If rank is unchanged, omit the YoY annotation.
- Custom HTML legend with three swatches: focal, neighborhood, other.
- Horizontal bar chart (`indexAxis: 'y'`), top 10 by revenue.
- Color logic per bar: focal brand = focal color; neighborhood ±3 (excluding focal) = peer color; remaining top 10 = other color.
- Y-axis tick for the focal row uses focal color, weight 500.
- Layout right padding `~70` to leave room for end-of-bar growth labels.
- X-axis ticks formatted as currency `$XM`.
- Tooltip includes both revenue and YoY %.

**End-of-bar growth label plugin (required):**

```js
const chart = Chart.getChart('positionChart');
const origDraw = chart.draw;
chart.draw = function() {
  origDraw.call(this);
  const ctx = this.ctx;
  const meta = this.getDatasetMeta(0);
  ctx.save();
  ctx.font = '500 11px sans-serif';
  ctx.textBaseline = 'middle';
  meta.data.forEach((bar, i) => {
    const g = data[i].growth;
    const color = g > 0 ? POSITIVE_HEX : g < 0 ? NEGATIVE_HEX : TEXT_HEX;
    ctx.fillStyle = color;
    // Suspect-row guard: mirror the neighborhood table's >500% rule. A raw
    // "+6807%" label reads as a broken chart and almost always reflects
    // taxonomy reclassification — cap the display and asterisk it instead.
    const label = g > 500 ? '>+500%*' : (g > 0 ? '+' : '') + g + '%';
    ctx.fillText(label, bar.x + 6, bar.y);
  });
  ctx.restore();
};
chart.draw();
```

### Visual 2 — Price ladder

Reads: "Where is the money in this category by price, and which tier does the brand live in?"

**Spec:**
- Horizontal bar chart, one bar per price tier from `analyze_price_tiers`.
- Tiers listed top-to-bottom from highest price to lowest (matches mental model of a "ladder").
- Bar length = tier's `revenue_total_sum__pct_of_total` as percentage.
- Bar color: brand's home tier (the one containing brand ASP) = focal color; all others = peer color.
- Custom HTML legend above: "Category share of revenue" (peer swatch), "Brand's home tier" (focal swatch).
- End-of-bar labels: tier's YoY growth %, colored green/red. Use the same plugin template as Visual 1.
- Footer prose (outside chart): "Brand ASP $X sits in the largest tier (±Y% YoY). The $Z+ tier is the only one contracting (−W% YoY)." — adapt per data shape.

### Why Chart.js, not hand-coded SVG

Chart.js auto-resizes on **mobile and narrow widths** with no fixed-viewBox math — this is the load-bearing reason; the same brief needs to render correctly on a phone and a laptop without per-device tuning. It also handles hover tooltips, dual-axis, and light/dark-mode text color adaptation natively, and produces consistent output across runs without manual coordinate tuning. The tradeoff: custom annotations (end-of-bar labels) need ~15 lines of plugin code, templated in Visual 1 above and reused in Visual 2.

## Worked example: Jack Link's in Jerky

A reference run that exercises tier alignment, the share-transfer rule, tiered flag ordering, and the migration headline. **Illustrative figures based on early-2026 data — refresh when running against current data.**

**Setup:** "Benchmark Jack Link's in Jerky." Single-leaf brand, no anchoring decision. Defaults: 90 days vs YoY, neighborhood ±3.

**Data (Step 1, parallel calls):**
- Jack Link's: rank #2 of 723 (was #1), $9.1M rev (−28% YoY), 14.8% share (−5.6pp), ASP $16
- Largest gainer: Chomps, +5.3pp share, +34% rev, ASP $29.52
- Tiers: $14–22 (focal home) −9% YoY; $22–30 (Chomps home) +16% YoY
- Category: ~flat (−1% YoY)

**Share-transfer match (Step 2):**
- Magnitude: |Chomps +5.3| ÷ |Jack Link's −5.6| = 95% → within 70–120% asymmetric band ✓
- Tier alignment: different tier labels, ASPs $16 vs $29.52 (84% delta, >20%) → **tier migration, not displacement**

**Headline:** "Jack Link's lost the #1 position in Jerky and −5.6pp share, but the recipient sits in a different price tier — the category migrated from $14–22 (−9% YoY) to $22–30 (+16% YoY), and Chomps was positioned in the growing tier."

**Flags fired (Step 3):**
- Tier 2 · Tier strand — home tier contracting −9% while $22–30 grew +16%
- Tier 2 · Peer overtaking — Chomps passed Jack Link's
- Tier 3 · Price drift — brand ASP −15.5% YoY vs category ~flat

**Closing line:** "Want to dig into the tier strand, Chomps' peer overtake, or the price drift — or have a different question?"

## Notes for the agent

- **This is a snapshot, not a diagnosis.** Resist the urge to explain *why* the brand is over/underperforming. If the story is movement, name `share-diagnosis` as the next step in a closing line, but don't try to do its job here.

- **Growth multiple: sign handling first, magnitude second.** Compute and report "Nx faster/slower than category" *only* when brand growth and category growth have the same sign. When signs differ, narrate in words:
  - Brand +5% in −3% category → "outperforming a declining category"
  - Brand −3% in +5% category → "declining in a growing category"
  - Brand −10% in −15% category → "declining more slowly than a contracting category"
  
  In the same-sign case, use "Nx faster" not "growth index Nx" — multiples read more naturally than ratios. **When the same-sign multiple is below 1× (brand growing but trailing the category), narrate it in words — "growing at about a third of the category's pace" — rather than printing "0.35× faster," which reads awkwardly.** Don't anchor on dramatic single-period multiples (an 18x reading is usually a small-base artifact, not a sustained trend); name the multiple but qualify it if either side is in the high double-digits.

- **Neighborhood scoping has edges.** Brand at rank 1 → show ranks 1–7. Brand at last rank → show last 7. Always show 7 rows.

- **2% share floor on focal brand, applied to the anchor leaf.** Below that, the benchmark frame is misleading — brand is sub-scale for this leaf. Flag and offer to widen scope (parent category, different leaf, or multi-leaf footprint).

- **Multi-leaf brands anchor on largest-revenue leaf by default.** For brands with meaningful presence across multiple Amazon leaves (Neutrogena across Cloths & Towelettes / Cleansers / Moisturizers; Dove across Body Wash / Deodorant / Shampoo), anchor on the leaf with the highest brand revenue. If the top leaf is ≥2x the second-largest, anchor automatically. If the brand is more evenly split (top <2x second), ask the user rather than guessing — the right anchor depends on what they want to learn. Always name the anchor choice. In ASSUMPTIONS, list the **top 3 other leaves** with ≥2% brand share; if more exist, append "(+N more)" rather than listing them all. Readers need to know what's in scope and roughly what was excluded — they don't need a 50-item appendix. **Apparel and footwear brands routinely return same-named leaves** (the catalog splits Pants/Tops/Clogs into parallel men's/women's/kids' subtrees), so the duplicate-name guard in Step 0 — disambiguate via `get_categories_by_ids` before the ask — fires often there. Never present two identically-labeled anchor options.

- **No new-launch proxy.** Until `first_date_available` is exposed in the MCP, do not infer new launches from `revenue_growth: null`. Parent-ASIN re-parenting and consolidation create false positives (a brand re-shelving 7 SKUs under a new parent will read as 7 new launches). Use `product_count` for portfolio breadth instead. When users ask about innovation explicitly, route to deep-dive product analysis rather than scoring it in the benchmark.

- **Cap flags at 3.** More than 3 dilutes signal. Use the tiered list in Step 3 — Tier 1 (category-level) → Tier 2 (competitive) → Tier 3 (operational) — and drop overflow from the bottom. Within a tier, the listed order is the severity order.

- **Surface share-transfer matches in the headline — but check tier alignment first.** A magnitude match (gainer Δ between 70% and 120% of focal brand Δ — asymmetric, captures dominant-recipient cases) is necessary but not sufficient for calling displacement. If the gaining brand sits in a different price tier than the focal brand (different tier label AND ASPs differing by >20%), the share movement is **tier migration**, not displacement — the category moved to a tier the focal brand wasn't positioned in. A $16 brand cannot have been displaced by a $29 brand; the buyer pool is different. Three patterns to distinguish in the headline: same-tier 1:1 → displacement ("X's loss almost perfectly mirrors Y's gain"); different-tier 1:1 → migration ("X lost share, but the recipient sits in a different price tier — the category migrated from [tier A] to [tier B]"); diffuse loss → category leak, not head-to-head.

- **Flag suspect peer rows, don't hide them.** Per the >50% YoY taxonomy-drift rule inherited from share-diagnosis, peer rows showing implausible growth (>500% YoY) almost always reflect reclassification. Mark the row with an asterisk and a one-line footnote inline in the neighborhood table rather than only mentioning it in ASSUMPTIONS — readers scan the table first.

- **Two visuals, always, in this order:** position → price. Each one sits inside the section whose argument it carries — not collected in a top block. Every visual is bookended: a setup sentence before ("Brand sits #X — here's how the top 10 stack up:") and a reading-out sentence after ("Brand is the only top-5 row with negative growth — that's the outlier"). The visual replaces a paragraph of description; it doesn't add to one. If a section has nothing the visual would clarify, do not pad it just to render the chart.

- **Don't refer to visuals by number in prose** ("as visual 2 shows…"). Speak about the chart itself: "the position bar," "the trend," "the price ladder." The reader sees them inline; they aren't a numbered list.

- **Chart.js, not hand-coded SVG.** SVG drifts: coordinates need re-tuning when data shifts, labels misalign, mobile sizing breaks. Chart.js handles all of that — and critically, it's responsive to narrow viewports without per-device tuning. Plugin code for end-of-bar labels is templated in § The two visuals — copy it, don't reinvent.

- **Don't fabricate.** If a data pull is incomplete or a quality check fires, name it explicitly in ASSUMPTIONS rather than papering over the gap. Honesty about what the data does and doesn't show is more useful than a confident but partial brief.
