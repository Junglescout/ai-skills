---
name: pricing-deep-dive
description: "Decompose what's driving price shifts in an Amazon category or competitive set, and quantify how much those price moves contribute to category revenue growth (price effect vs. volume effect). Use whenever the user asks which products are raising or cutting prices, whether category growth is price-led or volume-led, who's discounting or premiumizing, or 'what's driving the ASP move in [category].' Runs a category-split → ASIN-mover → cohort-guard traversal against Jungle Scout market-analysis data, names the dollar contribution of price, and ranks the products behind it. Pricing analog of share-diagnosis: answers 'is this growth price or volume, and which products are behind it?' not 'who took my share?'"
---

# Pricing Deep Dive

## Purpose

Two linked questions, one traversal: **(1)** which products are driving price shifts in a category or competitive set, and **(2)** how much those price moves contribute to category revenue growth. Output decomposes category revenue growth into a **price component** and a **volume component**, then ranks the products behind the price move by their dollar contribution — and guards the read against the two ways a price signal lies (product-mix shift and new launches).

This is a decomposition skill, not a snapshot or a share story. For "where does this brand stand?" use `brand-benchmark`. For "who took my share and what's it worth?" use `share-diagnosis`. This skill answers "is the category's growth coming from price or volume, and which products are behind the price part?"

## When to use

Trigger when the user asks any of:
- "What's driving the price changes in [category]?"
- "Which products raised / cut prices in [category / competitive set]?"
- "Is [category]'s growth price-led or volume-led?"
- "Who's discounting / premiumizing in [category]?"
- "How much of the category's growth is just price?"

Do **not** use for: share-movement diagnosis (use `share-diagnosis`), a brand's competitive position (use `brand-benchmark`), category sizing without a price question (use `analyze_categories` directly), or "what price should I set?" (out of scope — this skill explains observed moves, it doesn't recommend prices).

## Scoping

Send all questions in one message via `ask_user_input_v0`. Defaults locked — only ask if missing or ambiguous. If the user says "just run it," use defaults and surface them in ASSUMPTIONS.

1. **Scope.** Either a **category leaf** (the default frame — "price shifts in Jerky") or a **competitive set** (a named list of brands, or representative ASINs, analyzed within their shared leaf — "price shifts among Chomps, Jack Link's, and Country Archer"). If the user gives a brand with no leaf, run the leaf-footprint anchor in Step 0. If they give a competitive set, resolve the shared leaf first, then constrain the ASIN pull to those brands.
2. **Time window.** Default trailing 90 days (`period: "last_90_days"`, anchored by the MCP to the latest complete week — see Step 1) vs. the same window a year ago (`comparison: "year_ago"`). Override on request. Use `year_ago` for any seasonal category so the comparison is matched.
3. **Mover depth.** Default: top 10 price movers by dollar contribution. Override to top 5 / top 20 if requested.

## Procedure

**Run discipline — silent until the brief.** Steps 0–3 are internal. A normal run emits **only** the Step 4 Output-format brief (headline, flags, decomposition + visuals, movers, new-vs-existing, ASSUMPTIONS) — no preamble, no narration of tool calls, no "I'm now pulling…/validating…" running commentary, no step headers. The reader sees the finished brief, nothing else. The **only** exceptions that surface mid-run are the things that genuinely need a decision or change the answer: a **hard quality-gate stop** (Step 0 — sub-scale category), a **stale-window stop** (Step 0 freshness), or a **multi-leaf anchor question** (Step 0, when a no-leaf brand is meaningfully split). Surface those plainly and stop; otherwise go straight to the brief.

### Step 0: Resolve org + scope

*(Shared scope-resolution preamble — identical in intent to `brand-benchmark` and `share-diagnosis`; inlined here so this skill is self-contained.)*

- `list_orgs` → `org_id`. **If more than one org is returned, do not stop to ask** — the market-analysis tools used here (`analyze_categories`, `analyze_products`, `analyze_price_tiers`) return marketplace-wide estimates that are **identical across orgs**, so the choice does not change results. Default to the first org and note it in passing. Only ask if the user explicitly cares which org is billed/attributed. **This skill uses no org-scoped tools** (`query_org_performance` / `list_org_brands`), so there is no org-sensitivity to flag.
- `search_categories_by_name` **only if the user gave a category name** (skip when they already gave a leaf ID); confirm it resolves to a leaf node, not a parent.
- **Competitive-set scope:** resolve the shared leaf (from the named brands' anchor leaf or a user-given leaf), then carry the brand list into Step 1's B/C as `filters.brands`. Note in ASSUMPTIONS that movers are restricted to the named set.
  - **Two A's in competitive-set mode — keep the universes straight (non-negotiable).** Run **A-leaf** (leaf-wide `analyze_categories`, no brand filter) *and* **A-set** (`analyze_categories` with `filters.brands` = the named set). A-leaf is used **only** as the denominator for "% of category." **A-set drives the entire Step 2 decomposition (price/volume split) and the Step 2c reconciliation** — because the user asked about the set's pricing, not the leaf's, and 2c must compare like with like. **Why this matters (verified live):** comparing leaf-wide category ASP (Jerky −1.76%) against a brand-filtered existing cohort (Chomps −8.85%) shows a false 7.1pp divergence and fires "mix masquerade" spuriously; the correct same-universe comparison (A-set −8.89% vs Chomps existing −8.85%) agrees to 0.04pp. In single-leaf mode there is no A-set; A-leaf is both denominator and decomposition base.
  - **`pct_of_total` rebaselines under a brand filter — do not read it as category share.** When `filters.brands` is set, B's `market_share` / `revenue_total_sum__pct_of_total` is share *within the named set*, not the category (verified: Chomps' top stick reads 20% filtered vs 12.6% category). Always compute a mover's "% of category change" from A-leaf's **absolute** category revenue change, never from B's `pct_of_total`. Treat `pct_of_total` from a brand-filtered B as set-relative only.

**Multi-leaf brand check (only when a brand was given without a leaf):**
- `analyze_categories(filters={brand_query: <brand>}, options={detail_level:"summary", include_enrichments:[], sort_by:"revenue", extra_metrics:["brand_count"]})` → the brand's per-leaf footprint (one row per leaf, revenue per leaf). Use `analyze_categories`, **not** `analyze_brands` — only the category call returns the per-leaf split needed to pick an anchor.
- **Namesake-pollution guard (mandatory — `brand_query` is a fuzzy substring match).** `brand_query` matches *every* brand whose normalized name contains the string, so it sweeps in unrelated namesakes across unrelated leaves. Verified live: `brand_query:"quest"` returns Quest Nutrition's real leaves (Protein Bars $24M, Chips $12M) **plus** Clipboards, Nail Polish Remover, Faucet Mount Filters, Spray Paint, Snow Pants, Board Games. Before anchoring, **prune** footprint rows that are obviously not the target brand using two tells the data gives you:
  - **High `brand_count`** — a leaf where `brand_query` matches many distinct brands (the junk leaves showed `brand_count` 5–14) is namesake pollution; the real brand's leaves showed `brand_count` 1–2. Drop high-`brand_count` rows.
  - **Implausible category** — Quest Nutrition does not sell spray paint. If a leaf is categorically incompatible with the brand, drop it.
  - When in doubt, confirm: once a plausible anchor leaf is identified, **re-pull with an exact `filters.brands:["<stable name>"]`** (the stable brand name as it appears in the surviving rows) instead of `brand_query`, and use *that* for Step 1 — it's exact-match and immune to namesakes. Prefer `brands` over `brand_query` everywhere downstream once the name is resolved.
- **Anchor leaf** = highest-revenue leaf *among the pruned, real-brand rows*. If it's ≥2× the second-largest, anchor automatically and note it in ASSUMPTIONS. If the brand is meaningfully split (top leaf <2× the second), surface the top 3 *real* leaves via `ask_user_input_v0` and ask which to anchor on; don't guess. **Never list a pruned namesake leaf as an "other leaf" in ASSUMPTIONS.**
- **Duplicate-name guard:** if two anchor candidates share a display name (the catalog's parallel men's/women's/kids' subtrees, common in apparel/footwear), call `get_categories_by_ids` on the tied IDs to get the full disambiguated label before presenting the choice. Never show two identically-labeled options.

*(This `brand_query` footprint pattern is shared with `brand-benchmark`'s Step 0, which lacks the namesake guard — flag it there too.)*

**Quality checks — read off A (Step 1), but they GATE Step 2.** These are computed from A's row, so they run after the Step 1 pull — but evaluate them **before any decomposition**, because two of them are hard stops, not footnotes:

- **Category revenue ≥ $500K in window** — else **STOP**. Below this the price/volume split is noise. (Meat Floss is the canonical trap: $3.6K revenue, units −34%, ASP +17% → it decomposes to a tidy "price-led contraction," which is meaningless on $3.6K. The gate must fire *before* Step 2 writes that sentence.)
- **Brand count ≥ 10** — else **STOP** (survivorship risk; Meat Floss has 7).
- **Category revenue growth between −50% and +100% YoY** — else flag taxonomy-drift; weaken claims, proceed with caveat.
- **Price-tier dispersion** (optional D): max-tier ASP / min-tier ASP. **5–8× → informational note** ("category spans a wide price range; a category-wide ASP figure blends segments"). **>8× → flag** ("category ASP is not a meaningful single number — decompose by tier"). This matters more here than in `brand-benchmark`: a blended category ASP across incompatible segments makes the price/volume split misleading, so a high-dispersion category should be read at tier or product grain, not on the single category ASP number.

On a hard stop, say so plainly and offer to widen scope (parent category, a sibling leaf, or a longer window) — do not emit a price/volume narrative off a sub-scale category. Non-stop flags surface in ASSUMPTIONS → Data quality; they weaken affected claims, they are not competitive findings.

**Freshness — mandatory, never assume where "now" is.** Pass `period: "last_90_days"` and omit `start_date`/`end_date` on the calls that accept a period; let the MCP anchor the window to the latest complete market-analysis week.

**Read the resolved window — two sources, both valid.** A and B *do* echo the window in their **prose/text line** (e.g. `…in us (2026-02-23 to 2026-05-23)`); it's only the **JSON payload** that omits it — so "parse the dates from A's text line" works, and C's `cohort_boundary` gives the same window start independently (it's the date the MCP used to split launched-before from launched-after). Use whichever is in front of you; they agree. C is still required for the cohort *split* regardless, so reading the boundary from it costs nothing extra — but the window is not C-exclusive.

- **Freshness check:** `cohort_boundary` should sit ~90–105 days before today (a 90-day window plus normal lag). If it is materially older (e.g. >120 days back), the window has gone stale → **stop and flag**; that's a connector problem, not normal lag. Do not emit a brief on a silently stale window.
- **End date** (needed only for the price-tiers call, D): derive as `cohort_boundary + 90 days`, capped at the latest complete week (today minus the current partial week). The start is MCP-resolved, so deriving the end from it is safe — this is not the "assume today" trap the freshness rule guards against. Use this same `[cohort_boundary, end]` pair for the ASSUMPTIONS "Window" line.

### Step 1: Pull the pricing pack

Three core pulls (A, B, C); D (price tiers) is conditional. **Do not hand-compute `start_date`/`end_date`** on A/B/C — pass `period` and let the MCP anchor. `analyze_price_tiers` (D) is the exception: it *requires* explicit dates and has no freshness default, so run it *after* C, using the window C resolved (`cohort_boundary` as start; see Step 0 freshness).

**Wave 1 — A and B fire together (no data dependency).** Both run `comparison: "year_ago"`.

**A. Category totals (the price-vs-volume denominator)**
```
analyze_categories(
  filters={category_ids: [leaf_id]},
  options={
    period: "last_90_days",          # omit start_date/end_date — MCP anchors to latest complete week
    comparison: "year_ago",
    detail_level: "summary",
    include_enrichments: [],
    extra_metrics: ["revenue_growth", "units_sold_growth", "avg_price_growth",
                    "market_share_growth", "avg_price", "product_count", "brand_count"]
  }
)
```
(A's prose/text line echoes the resolved window as `…(YYYY-MM-DD to YYYY-MM-DD)`; C's `cohort_boundary` gives the same start — either works, per Step 0.) `revenue_growth`, `units_sold_growth`, and `avg_price_growth` here are the category-level inputs to the Step 2 split. **`avg_price_growth` at category grain is the revenue-weighted ASP change — it moves with product mix and new launches, not only with products repricing.** Treat it as the *symptom* to be decomposed, never as proof that products raised prices.

**B. ASIN-grain price movers (with a revenue floor — non-negotiable)**
```
analyze_products(
  filters={category_ids: [leaf_id]},          # + brands:[...] for a competitive set
  options={
    period: "last_90_days",
    comparison: "year_ago",
    detail_level: "standard",                  # returns ASIN + title + brand + first_date_available (used to name movers and classify ramp vs reclassification)
    sort_by: "revenue",                        # rank by size, NOT by avg_price_growth — see Notes
    limit: 50,
    extra_metrics: ["revenue_growth", "units_sold_growth", "avg_price_growth",
                    "avg_price", "units_sold", "market_share"],
    thresholds: [{metric: "revenue", min_value: 50000}]   # fixed $50K floor — kills small-base noise
  }
)
```
**Use a fixed `$50,000` revenue floor (not a percentage of category revenue).** A flat absolute floor is deliberate: a percentage floor (e.g. 0.5%) blows up to $550K in a $110M category — high enough to drop genuine movers — and a fixed floor also lets A and B run in true parallel (a percentage floor would make B wait on A's revenue, which is why "Wave 1" would otherwise be a lie). $50K over a 90-day window removes true small-base noise — a $3 product going to $9 is +200% `avg_price_growth` and meaningless — while keeping every product big enough to move a category. The floor is a backstop, not the main guard: because movers are ranked in Step 2 by **price-driven dollars**, small-base products sink on their own. Sort by `revenue`, never by raw `avg_price_growth` %. (In a category small enough that $50K returns almost nothing, the quality gate has already stopped the run — see Step 0.)

**C. Launch-cohort split (the new-vs-existing guard)**
```
analyze_products(
  filters={category_ids: [leaf_id]},          # same filter as B (incl. brands for competitive set)
  options={
    period: "last_90_days",
    comparison: "year_ago",
    group_by: "launch_cohort",                 # one row for "new" (launched in-window), one for "existing"
    extra_metrics: ["revenue_growth", "units_sold_growth", "avg_price_growth", "avg_price", "units_sold"]
  }
)
```
Returns two aggregate rows, each carrying `cohort_boundary` = **the resolved window start** (this is also where freshness and the price-tiers end date come from — Step 0). The **new cohort** is products first available on/after that boundary; the **existing cohort** is everything else. This isolates how much of the category's revenue change is products that didn't exist a year ago versus existing products repricing or selling more — the decisive guard for whether a category ASP move is real repricing or a mix artifact (see Step 2 and Notes). The **existing** row's `avg_price_growth` is the non-null aggregate used for the Step 2c reconciliation; the **new** row's `*_growth` fields compare to a ~zero prior and are meaningless — use its absolute revenue only.

**Wave 2 — D (conditional).** Run only if the category-ASP read needs a tier breakdown: tier dispersion looks wide (Step 0), the user asked about discounting/premiumization explicitly, or the category split is ambiguous. Uses the window C resolved.
```
analyze_price_tiers(
  filters={category_id: leaf_id},              # + brand:<stable> for a single-brand competitive lens
  options={                                    # start = C's cohort_boundary; end = start + 90d (capped at latest complete week)
    start_date: <cohort_boundary>,
    end_date: <cohort_boundary + 90d>,
    comparison: "year_ago"
  }
)
```
Reads where category revenue concentrates by price band and which bands are growing: `revenue_total_sum__pct_of_total`, `revenue_total_sum__delta_pct`, and `buybox_price_avg__delta_pct` (verified field names).

A typical single-leaf run is four calls: `list_orgs`, [`search_categories_by_name` if a name was given], A-leaf∥B, C — plus D only when conditionally triggered. **Competitive-set mode adds one call: A-set** (the brand-filtered `analyze_categories`), fired alongside A-leaf in Wave 1.

**Reading the responses (two gotchas):**
- **Field names ≠ option names.** You request `extra_metrics: ["revenue_growth", "avg_price_growth", ...]`, but the rows come back under the *underlying* field names: `revenue_total_sum`, `sales_total_sum` (units), `weighted_average_selling_price` (ASP), and the growth/delta variants `revenue_total_sum__delta_pct`, `sales_total_sum__delta_pct`, `weighted_average_selling_price__delta_pct`. Read those keys, not the option aliases. (`market_share` → `revenue_total_sum__pct_of_total`.)
- **Leaf names are truncated under `detail_level: "summary"`.** A returns `breadcrumb_leaf_node_name_stable` as just the last segment — "Olive" for Olive Oils, fine for Jerky. For any display label, use the name from `search_categories_by_name` / `get_categories_by_ids`, not the truncated row value.

### Step 2: Decompose

**Gate first.** Before computing anything here, confirm the Step 0 quality gate passed (revenue ≥$500K, brand_count ≥10). If it didn't, stop — a decomposition of a sub-scale category is the Meat Floss trap.

**(a) Category price/volume split.** Revenue ≈ price × units, so growth composes multiplicatively:
```
(1 + revenue_growth) ≈ (1 + avg_price_growth) × (1 + units_sold_growth)
```
Allocate the revenue change into a **price contribution**, a **volume contribution**, and a small **interaction/residual**. (In competitive-set mode, all the inputs here — `revenue_growth`, `avg_price_growth`, `units_sold_growth`, and `R0` — come from **A-set**, the brand-filtered category pull, not A-leaf; A-leaf is only the "% of category" denominator. See Step 0.) A clean, reportable allocation in dollar terms (let `R0` = prior-period revenue = `revenue_now / (1 + revenue_growth)`):
- Price contribution ≈ `R0 × avg_price_growth`
- Volume contribution ≈ `R0 × units_sold_growth`
- Interaction/residual ≈ `R0 × avg_price_growth × units_sold_growth`. Report it as its own line.

**The three components sum to ΔR exactly** — the split is algebraic (ASP = revenue ÷ units), not an approximation to be verified, so there is no closure "check" to run. The only place attribution genuinely leaks is **cross-grain**: per-product price-$ need not reconstruct the category price-$ — that gap is governed by Δ coverage (2b), not by the identity (verified live: at 10% coverage, computable movers recovered only ~8% of the category price effect).

**Offsetting-regime guard (the flat-revenue trap).** A large interaction is not an error — it's a *signal* that price and volume are both moving hard, which in a ~flat-revenue category means they're offsetting. Detect it directly: compute `gross = |price_$| + |vol_$|` and `net = |ΔR|`. **When `net < 0.5 × gross`, revenue is ~flat *because* large price and volume effects cancel.** In this regime:
- Do **not** express price or volume as a share of ΔR — the denominator is ~0 and the share explodes to hundreds of percent (verified: Video Monitors, revenue +0.1%, units +4.6%, ASP −4.3% → multiplicative price-share read −4059%, log-split −4151%, both garbage).
- Do **not** attempt a log split — it divides by `ln(1+revenue_growth) ≈ 0` and fails identically.
- Instead report the **signed gross dollar effects** (e.g. "revenue ~flat at +$0.1M; underneath, +$2.5M volume offset by −$2.3M price") and route to the offsetting / divergent-repricing headline branch. This single `net < 0.5 × gross` test is the one trigger for the immaterial/offsetting regime (see Step 3 Tier 2 and the headline branch).

Report the **dollar split, led by price's signed share of the revenue change** — that share is the number the user asked for, so it always leads: "price contributed +$4.4M, ~19% of the +$22.7M growth (ASP +5%); the other ~81% is unit volume." Do **not** lead with a "price-led / volume-led" verdict — on real Amazon data volume almost always dominates (units are the default growth engine; even a clear +5% inflation pass-through like coffee is volume-led), so the binary buries the price story the skill exists to surface. Reserve "price-led" for the genuine case where |price contribution| actually exceeds |volume contribution| (rare — flat/declining units with rising price). Handle sign cases in words (price up + volume down → "trading volume for price"; price down + volume up → "prices fell but volume more than absorbed it"; both up → "price and volume both contributing"). **This split uses the weighted category ASP, so it still includes mix — qualify it with the (c) reconciliation before calling the price share real repricing.**

**(b) Per-product price contribution (which products are behind the price part).** For each mover from B above the floor, decompose its *own* revenue change the same way and express the price part in dollars. With `rev` = current revenue, `pg` = `avg_price_growth`, `ug` = `units_sold_growth`, and the product's prior revenue `r0 = rev / (1 + revenue_growth)`:
- Product price-driven $ ≈ `r0 × pg`

Rank movers by **|price-driven $|**, not by `avg_price_growth` %. Report each top mover's ASP, ASP change %, and price-driven $ (the lead number). For the share column, express it as a fraction of the **gross price effect** = Σ|price-driven $| across the computable movers — **not** as a fraction of the category's total revenue change. The total-revenue-change denominator badly understates big repricers when movers offset: a −$2.07M cut reads as a trivial −2.9% of a +$71M revenue change, even though it's the single largest force in the price story. Dividing by the gross price effect ("this product is X% of all the repricing happening") keeps that legible. A product can have a huge ASP % move and a trivial dollar contribution — the dollar figure is the story, the % is context.

**Dedupe by `asin` first — the same product fans out across rows.** At `product_grain: "asin"` the tool emits one row per (asin × `parent_asin`) snapshot, so a re-parented product appears as **several rows** (verified: Lavazza Super Crema `B000SDKDM4` returned 3 rows — $6.35M, $1.87M, $695K — under 3 different parents). Before ranking movers, **collapse rows that share an `asin`**: sum their `revenue`/`units`; for the delta, use the non-null row if exactly one has it, revenue-weight if several do, else mark the product uncomputable. The `asin` is the stable product identity (different sizes/packs are genuinely different asins and stay separate). Skipping this step double-counts the biggest products in both the table and the dollar math.

**Only rows with non-null deltas are computable** — re-parented ASINs return `null` for `revenue_growth`/`avg_price_growth` (see § Notes), and in many categories they are the *majority* of revenue. Skip null-delta rows in the mover ranking. Then compute **Δ coverage** = (revenue of B rows with non-null deltas) ÷ category revenue (from A), and report it in ASSUMPTIONS. When coverage is low (rule of thumb, <60%), the mover table is **"computable movers only — not a complete attribution"**: the listed products do **not** sum to the category price move, and the category-level split from (a) — not the product list — carries the headline. Never present the movers as if they explained the whole price change.

**Classify blown-out rows by `first_date_available` — ramp vs. reclassification (two different causes).** A row with implausible YoY growth (>+500%) has two possible explanations, and the skill must not collapse them into one "taxonomy reclassification" label:
- **Young-product ramp** — `first_date_available` is **after `cohort_boundary − 365 days`** (i.e. the product launched somewhere in the ~15-month span between the prior-year baseline and now). Its prior-year base was ~zero, so a +500%–+3,500% YoY is just a launch ramping, *not* a data artifact. Label it **"low prior-year base / ramp."**
- **Ambiguous band** — `first_date_available` in the `cohort_boundary − 365d` to `− 455d` window: the product was only a few months old at the prior-year baseline, so a depressed prior base could still be a ramp. Label **"ramp or reclassification — ambiguous"** rather than forcing reclassification.
- **Likely reclassification** — `first_date_available` **older than `cohort_boundary − 455d`** and growth still blown out → a genuine taxonomy/re-parenting artifact. Keep the "likely reclassification — treat as suspect" label.

`first_date_available` is returned at `detail_level: "standard"` (already in B). Either way the dollar-ranking self-defense holds — these rows contribute trivial price-driven dollars and sink to the bottom — but the *label* must name the right cause.

**Mid-period launches also sit in the "existing" cohort — so new-vs-existing understates new-ish supply.** C's cohort boundary is the *current window start* (~90 days back), but the YoY baseline is the *prior-year window* (~15 months back). Products launched between those two dates are tagged "existing" by C yet have a near-zero prior-year base. So treat C's new-vs-existing split as "launched in the last 90 days" vs. everything older — **not** as "all genuinely new supply." When ramps are visibly inflating the existing cohort's growth, say so: the real new-supply window is ~15 months, and the 90-day new cohort is a floor on new supply, not the whole of it.

**(c) Reconciliation — new-launch/mix vs. existing-product repricing (the load-bearing guard).** Do **not** reweight B's per-ASIN `avg_price_growth` for this — most B rows have `null` deltas (re-parented ASINs; see § Notes), so a per-ASIN reweight runs on a minority of revenue and lies. Instead use the **launch-cohort existing row from C**, which gives a single non-null `avg_price_growth` covering all pre-window products at once. Compare it to the category's `avg_price_growth` **from the same universe** — A-leaf in single-leaf mode, **A-set in competitive-set mode** (never leaf-wide A against a brand-filtered cohort; that mismatch fires masquerade falsely — see Step 0):
- **They roughly agree** (Jerky: category −1.76% vs existing −1.80%; coffee: +4.98% vs +4.94%) → the category ASP move comes from **existing products**, not from new launches reshaping the mix. Report it as an existing-product move.
- **They diverge** → the category figure is **new-launch/mix-driven**: the blend shifted because the new cohort entered at higher or lower price points than the existing book. Say so and reattribute — "category ASP rose X% but the existing book moved only Y%; the gap is new-launch mix."

**Splitting the price contribution into existing-repricing vs. mix/new dollars** (the two shades for Visual 1, and the reattribution above): the split *is* computable — don't hand-wave it.
- Existing-repricing $ = `R0_existing × existing_cohort_avg_price_growth`, where `R0_existing = existing_cohort_revenue / (1 + existing_cohort_revenue_growth)` (all from C's existing row).
- Mix/new $ = total price contribution (2a) − existing-repricing $.
The remainder captures the new cohort's effect on the blend plus the small full-vs-existing reweighting; it reconciles by construction. Verified live (Chomps): total price −$0.783M ≈ −$0.780M existing-repricing + −$0.003M mix — i.e. essentially all existing repricing, mix negligible (new cohort 0.5%), so the masquerade branch correctly stays silent. When the new cohort is large, the mix term grows and carries the reattribution.

**What this can and cannot resolve — state it honestly.** The cohort split cleanly separates *new-launch mix* from *existing-book movement*. It does **not** finish the job: within the existing book, the aggregate ASP still blends true per-SKU repricing with mix-shift among existing products, and the per-ASIN deltas that would untangle those are `null` on most revenue. So the skill resolves new-vs-existing (clean) and the category price/volume split (clean), but "which exact existing SKUs repriced" is only partial. Do not claim the finest grain when coverage (2b) is low.

**(d) New vs. existing (from C).** The new cohort didn't exist a year ago, so its **entire current revenue is its contribution** to the category change — use that absolute dollar figure: new-cohort contribution ≈ new cohort `revenue_total_sum`, expressed as a % of the category revenue change (from a). **Never use the new cohort's `revenue_growth` / `avg_price_growth` — they compare against a ~zero prior base and return nonsense** (e.g. +2582% for Ground Coffee's new cohort, +1239% for Roasted Beans). Absolute revenue and share only. If new launches are **>50%** of the change, the price story is substantially a product-expansion story — reframe accordingly and offer product-level analysis as the next step rather than calling it repricing.

### Step 3: Evaluate flags (1–3 max)

Trigger only when material. Surface in severity order; cap at 3 (Tier 1 → Tier 2 → Tier 3, drop overflow from the bottom).

**Tier 1 — Category-level (context that overrides product signals):**
- **Material price contribution** — price is a meaningful share of the revenue change: price contribution ≥25% of |total revenue change| OR |avg_price_growth| ≥ 3%. (Replaces a "price-led" test — on real data price rarely exceeds volume, so the useful signal is "price is a real part of the move," not "price won." When price genuinely exceeds volume, say "price-led" in prose.)
- **New-launch / mix masquerade** — category `avg_price_growth` and C's existing-cohort `avg_price_growth` (Step 2c) diverge by ≥5pp. The headline ASP move is the new cohort reshaping the mix, not the existing book repricing. (Overrides any "category raised/cut prices" read.)

**Tier 2 — Driver concentration:**
- **Concentrated price effect** — the top 1–3 movers account for >50% of the **gross price effect** (Σ|price-driven $| across computable movers). Use gross, **not** the net category price contribution: when big hikes and cuts offset, net price can be tiny while a single product is >100% of it, which makes a net-denominator concentration ratio explode meaninglessly. (Verified live: net category price was +$1.93M but THORNE alone was −$2.07M — 107% of *net*; against gross it reads as the dominant single force, which is the true story.) When the run is in the **offsetting regime** (`net < 0.5 × gross`, the single test defined in Step 2a), the category price move is small-on-net only because large moves offset — say so and lean on the divergent-repricing flag for the headline.
- **Divergent repricing** — meaningful movers are splitting direction (some cutting ≥5%, some hiking ≥5%) rather than moving together — a competitive price war or segmentation, not a category-wide trend.

**Tier 3 — Composition / quality:**
- **New-launch-driven** — new cohort >50% of category revenue change (Step 2d). Route to product analysis; the price read is a launch-mix story.
- **Noise excluded** — note the count of sub-floor rows dropped, so the reader knows movers below `<FLOOR>` were intentionally excluded.

**No flags fired** — "No material flags. Price and volume moving in proportion." (or as the data warrants).

### Step 4: Render

See § Output format. This is the **only** thing a normal run emits (per Run discipline above) — the brief, nothing before it. Always render the two visuals in order: **decomposition → top movers.** Each visual is bookended by a setup sentence and a read-out sentence; it replaces a paragraph, it doesn't add to one.

## Output format

```
HEADLINE  (pick the branch that matches the data — don't force a price lead)
- **Price is material** (material-price flag fired): lead with price's signed share — "$X of the $Y category growth (~Z%) is price; the rest is volume" — plus the ASP move and the single biggest computable mover. Say "price-led" only if price truly exceeds volume.
- **Price is immaterial / offsetting** (material-price flag did NOT fire, OR the offsetting-regime test `net < 0.5 × gross` from Step 2a is true): **say so and pivot.** In this branch the headline numbers are the **signed gross dollar effects**, never a %-of-ΔR figure (which explodes when ΔR≈0). When revenue genuinely moved but price was small: "Price is not a driver — this is a volume story (units +X%, +$Y volume)." When revenue is ~flat because price and volume offset: lead with the gross dollars and make two-way repricing the story — "revenue ~flat at +$0.1M; underneath, +$2.5M volume offset by −$2.3M price — premium SKUs hiking, mainstream cutting." Never lead with a near-zero or triple-digit-percent price share as if it were the finding.
- **New-launch/mix masquerade** (2c fired): lead with that — "the category's ASP rose X% but the existing book barely moved; the shift is new-launch mix."

[Headline number: the figure that matches the branch — signed price $ and its % of the change when price is material; the volume figure (units %, volume $) when it isn't.]

FLAGS  (1–3 max; omit section if none triggered)
⚑ [Flag name] — [one-line evidence]

DECOMPOSITION
[Two sentences: the category's revenue change and how it splits into price vs. volume (vs. residual). Name the reconciliation result (2c) — is the price part real repricing or mix?]

[VISUAL 1: Price vs. volume decomposition]

[One sentence reading the visual: "Two-thirds of the $X growth is volume; price added $Y; the residual is small." Or "Price contributed $X but the weighted product repricing was near zero — the bar is mix."]

TOP PRICE MOVERS
| Product (ASIN) | Brand | ASP | ASP Δ% | Price-driven $ | % of gross price effect |
| ... | ... | ... | ... | ... | ... |
(ranked by |price-driven $|; cutters and hikers both shown; computable-delta rows only — if Δ coverage <60%, title this "Computable price movers" and add a one-line note that re-parented ASINs (most of category revenue) are excluded and the rows do not sum to the category price move; flag any row with revenue_growth or ASP Δ >+500% with an asterisk, and label the cause by `first_date_available` per Step 2b — ramp / ambiguous / reclassification)

[VISUAL 2: Top price movers]

[One sentence reading the visual: "Three products account for most of the price contribution; all are hikes." Or "The movers split — two big cutters offset by one hiker."]

NEW VS. EXISTING
- New cohort: $X of category revenue change (Y%)
- Existing cohort: $X (Z%)
- [If new >50%: "The price read is substantially a product-expansion story — recommend product-level analysis."]

[Closing line — single sentence. Name fired flags as drill-down options; close with "or have a different question?". If <2 flags fired, fill out to 2–3 with the most actionable prose-surfaced concern.]

---

ASSUMPTIONS
- Window: [resolved dates], comparison: YoY
- Scope: [leaf id, name] / [competitive set: brands] — movers restricted to named set: yes/no
- Anchor leaf (if brand given without leaf): [id, name] — [X]% of brand's Amazon revenue
- Revenue floor for movers: $50K (fixed); N sub-floor rows excluded
- Δ coverage: ~X% of category revenue sits in ASINs with computable YoY deltas (rest are re-parented → null); mover attribution covers that share only
- Decomposition: multiplicative price×volume identity; interaction term reported separately
- Data quality: [flags fired or "clean"]
```

Tables for evidence; prose around the visuals carries the argument. No bullets in narrative sections.

## The two visuals

Both use `visualize:show_widget` with HTML + Chart.js. Load `read_me` with `modules=["chart"]` once at the start of the run. Constraints below are non-negotiable — they prevent drift across runs.

**If the visualizer is unavailable** (`show_widget` errors/4xx, or `read_me` won't load), do **not** drop the analysis or retry in a loop. Render each visual's content as a **compact markdown table** instead — Visual 1 as a 3-row price/volume/interaction table with signed dollars, Visual 2 as the top-movers table (which the brief already includes) — and add one line: "Charts unavailable this run; showing the underlying numbers as tables." The brief's substance must survive a visualizer outage.

**Common constraints:**
- Chart.js UMD via cdnjs: `<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>`
- Hardcoded hex (canvas can't read CSS vars). Detect dark mode with `matchMedia('(prefers-color-scheme: dark)').matches` and swap the palette.
- **Palette — Jungle Scout brand (both modes).** Light: focal `#4A2DFF`, peer/secondary `#40AFFF`, other `#C9C9CB`, text `#444441`, grid `rgba(0,0,0,0.06)`, positive/hike `#007A6B`, negative/cut/attention `#FF5E00`. Dark: focal `#8B73FF`, peer `#40AFFF`, other `#5F5E5A`, text `#D3D1C7`, grid `rgba(255,255,255,0.08)`, positive `#2FB89E`, negative `#FF7A33`. Colors only — never JS fonts/logos. Use orange surgically: price cuts and attention only.
- Custom HTML legends above the chart (not Chart.js built-in). Round all displayed numbers. Disable the built-in legend: `plugins: { legend: { display: false } }`.

### Visual 1 — Price vs. volume decomposition

Reads: "How does the category's revenue change split into price and volume?"

**Spec:**
- Above the chart, a metric callout: "CATEGORY REVENUE Δ · **$XM** · +Y% YoY", with the dollar change in the sign-appropriate color (teal up / orange down).
- A horizontal **stacked or paired bar** showing the three components from Step 2a: **Volume contribution**, **Price contribution**, **Interaction/residual**, each as a signed dollar value summing to the revenue change. Use focal/peer/other for the three; orange a *negative* price contribution (a category-wide cut).
- If the mix-masquerade reconciliation (2c) fired, render the price bar in two shades using the **Step 2c dollar split** — existing-repricing $ (`R0_existing × existing-cohort ASP-growth`) vs. mix/new $ (the remainder) — and annotate both. Don't render the two-shade split when masquerade didn't fire (existing repricing ≈ the whole price bar); a single shade is correct there.
- End-of-bar labels: signed dollar value, colored by sign.
- Custom HTML legend: Volume / Price / Residual swatches.

### Visual 2 — Top price movers

Reads: "Which products are behind the price part, and how big is each?"

**Spec:**
- Horizontal bar chart (`indexAxis: 'y'`), top N movers (default 10) ranked by **|price-driven $|** (descending).
- Bar length = price-driven dollar contribution (signed). **Hikes** in teal/focal, **cuts** in orange — direction is the read.
- Y-axis tick = short product label (brand + truncated title); focal-weight the label of the single biggest contributor.
- End-of-bar label = ASP change %, sign-colored. Apply the same **suspect-row guard** as the table: a label >+500% renders as `>+500%*`, not the raw value (small-base / reclassification artifact).
- Custom HTML legend above: "Price hike" (teal swatch), "Price cut" (orange swatch).
- X-axis ticks formatted as currency `$XK`/`$XM`.

**End-of-bar label plugin (required, both visuals — template):**
```js
const chart = Chart.getChart('moversChart');
const origDraw = chart.draw;
chart.draw = function() {
  origDraw.call(this);
  const ctx = this.ctx, meta = this.getDatasetMeta(0);
  ctx.save(); ctx.font = '500 11px sans-serif'; ctx.textBaseline = 'middle';
  meta.data.forEach((bar, i) => {
    const v = data[i].aspGrowth;
    ctx.fillStyle = v < 0 ? NEGATIVE_HEX : POSITIVE_HEX;
    const label = v > 500 ? '>+500%*' : (v > 0 ? '+' : '') + Math.round(v) + '%';
    ctx.fillText(label, bar.x + 6, bar.y);
  });
  ctx.restore();
};
chart.draw();
```

### Why Chart.js, not hand-coded SVG

Chart.js auto-resizes on mobile and narrow widths with no fixed-viewBox math — the load-bearing reason; the same brief must render on a phone and a laptop without per-device tuning. It also handles tooltips and light/dark text adaptation natively. The only tradeoff is ~15 lines of plugin code for end-of-bar labels, templated above.

## Notes for the agent

- **The revenue floor is the whole ballgame at ASIN grain.** This is the known cross-skill finding: *sorting or surfacing price movers by `avg_price_growth` % at ASIN grain surfaces small-base noise — a cheap product doubling in price reads as a giant mover and means nothing.* Always apply the `thresholds: [{metric:"revenue", min_value: 50000}]` filter (fixed $50K, not a percentage — see Step 1 B for why), sort by `revenue`, and rank by **price-driven dollars**, never by raw % move. State the floor and the excluded-row count in ASSUMPTIONS.

- **Category `avg_price_growth` is a weighted blend, not a repricing measure.** It moves when the product mix shifts (more high-priced SKUs sold, or new high-priced launches) even if no product changed its own price. The Step 2c reconciliation — C's existing-cohort `avg_price_growth` vs. the category figure — is mandatory before you call a category ASP move "price increases." When they diverge, it's new-launch mix; say so and reattribute. This is the pricing analog of `share-diagnosis`'s "mix shift looking like price action."

- **Quarantine new launches with the launch cohort.** `group_by: "launch_cohort"` splits new (in-window first-available) from existing products in one call. A category whose ASP rose because three premium products launched is not a repricing story. If the new cohort drives >50% of the revenue change, reframe as product expansion and route to product-level analysis.

- **Null deltas are the norm at ASIN grain, not an edge case.** Re-parented ASINs (Amazon changes a product's parent when sellers re-shelve, consolidate, or relaunch variants) break the YoY join, so `revenue_growth` / `units_sold_growth` / `avg_price_growth` come back `null` — and in real categories these rows are frequently the *majority* of revenue (verified in Jerky and Olive Oil). Consequences, all handled above: rank movers only over non-null rows (Step 2b); report Δ coverage and caveat the table when it's low; and run the reconciliation off C's existing-cohort aggregate (non-null), never off a per-ASIN reweight of B. The cohort and category-total calls are not affected — they aggregate before the join — which is why the category split (A) and new-vs-existing (C) stay reliable even when per-ASIN attribution is thin.

- **The same product fans out across rows — dedupe by `asin`.** Re-parenting makes one ASIN appear as multiple rows under different `parent_asin` values (Lavazza Super Crema returned 3 rows). Always collapse by `asin` before ranking movers or summing dollars (Step 2b), or the biggest products get double-counted. This is separate from, and compounds with, the null-delta problem above.

- **The split closes exactly — the real leak is cross-grain, not the identity.** At category grain, price + volume + interaction = ΔR *exactly* (ASP = revenue ÷ units, so it's algebraic, not approximate) — there's no closure check to run, and per-row closure holds wherever deltas exist (verified ≤0.005pp gap across 63 categories + ASIN rows). Report the interaction as its own line; don't fold it into price or volume. A *large* interaction isn't error — it's the tell for the offsetting regime (price and volume both moving hard against ~flat revenue); handle it with the `net < 0.5 × gross` guard in Step 2a, not a log split (which fails identically). The attribution that genuinely leaks is cross-grain — the per-product table need not reconstruct the category price-$ — and that's governed by Δ coverage (2b), not the identity.

- **Rank by dollars, report the percent as context.** Humans ask "which products are driving it" expecting the ones that *matter*, which is a dollar question. A +400% ASP move on a $30K product is a footnote next to a +6% move on a $4M product. Lead every mover with its price-driven dollar contribution.

- **Cutters and hikers are both movers.** Don't filter to one direction. A category that looks flat on net ASP can hide a price war (big cutters) offset by premiumization (big hikers) — the "divergent repricing" flag exists to catch exactly this. Show both directions in the table and the movers visual.

- **Competitive-set mode runs two A's — don't conflate them.** Constrain B/C to the named brands, and run both **A-leaf** (leaf-wide, the "% of category" denominator) and **A-set** (brand-filtered, the decomposition + reconciliation base). The trap is using A-leaf for the 2c reconciliation against a brand-filtered cohort: different universes, false masquerade (verified — Jerky −1.76% vs Chomps existing −8.85% = spurious 7.1pp gap; A-set −8.89% vs −8.85% agrees). The set's price story is computed on A-set; only the "share of category" framing uses A-leaf. Note the restriction in ASSUMPTIONS.

- **Flag suspect rows, but name the right cause (ramp vs. reclassification).** Any mover row with implausible growth (>+500%) is asterisked and its bar label capped at `>+500%*` rather than printing a blown-out number. But split the *cause* by `first_date_available` (Step 2b): a product launched within the last ~15 months (after `cohort_boundary − 365d`) is a **young-product ramp on a near-zero prior base**, not a taxonomy artifact — labeling it "reclassification" is wrong. Only older ASINs with blown-out growth are "likely reclassification." Verified live: in supplements, THORNE 30-serv (launched 2025-02-03) posted +3,528% YoY purely as a ramp, yet contributed just +$3.2K price-driven — sinks on dollars, but it's a ramp, not a reclass.

- **Two visuals, always, in order: decomposition → movers.** Each sits in the section whose argument it carries, bookended by a setup and a read-out sentence. Don't refer to visuals by number in prose — speak about "the decomposition bar," "the movers chart."

- **Don't drift into recommendations.** Stop at "here's what's driving the price move and what it's worth." No "you should raise/cut prices." If asked, name that as out of scope.

- **Don't fabricate.** If a pull is incomplete or a quality check fires, name it in ASSUMPTIONS rather than papering over it. Honesty about what the data shows beats a confident partial brief.
