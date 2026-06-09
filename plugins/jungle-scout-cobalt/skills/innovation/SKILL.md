---
name: innovation
description: "Surface what's new and what's working in an Amazon topic, brand, or category — new product launches and their traction, the products and attributes gaining revenue share, and rising search-keyword demand. Use whenever the user asks what's trending, what's new, what's growing, what's emerging, which new products or features are taking off, what attributes are driving revenue, or where demand is shifting — e.g. 'what's new in creatine,' 'innovation trends in jerky,' 'what attributes are winning in whey protein,' 'what's gaining in [brand]'s category.' Produces a concise innovation brief with two standard visuals (breakout launches, rising-attribute share shift) and a rising-keywords table, and offers deeper paths. Forward-looking and discovery-oriented: answers 'what's emerging here?' — not 'where does this brand stand?' (use brand-benchmark) or 'why did share move?' (use share-diagnosis)."
---

# Innovation

## Purpose

Map the innovation frontier of a scope: which new products are gaining traction, which attributes are pulling revenue, and which search terms are rising. Outputs an innovation brief with two fixed visuals and a rising-keywords table. Discovery-oriented, not a position snapshot (`brand-benchmark`) or a movement diagnosis (`share-diagnosis`). Names what's emerging and sizes it; does not recommend plays.

## When to use

Trigger when the user asks any of:
- "What's new / trending / emerging in [category / topic]?"
- "Which new products are taking off in [scope]?"
- "What attributes are driving revenue in [category]?" / "What features are winning?"
- "What keywords are rising in [topic]?"
- "Where is demand shifting in [scope]?"

Do **not** use for: a brand's competitive position (`brand-benchmark`), why share moved (`share-diagnosis`), category sizing without an innovation angle (`analyze_categories` directly), forecasting, or "what should I do" plays.

## Scope modes

This skill runs in one of three scope modes. Resolve the mode in Step 0, then the rest of the procedure is identical.

- **Category** — a named category/leaf (or representative ASINs). The default and cleanest frame; all quality checks apply.
- **Brand** — a named brand. Anchor on the brand's largest-revenue leaf (Step 0 multi-leaf logic, shared with `brand-benchmark`), run the category-level innovation lenses on that leaf, and **overlay the brand's own new-launch participation** (what the brand has launched vs. what the category's newcomers are doing). Make explicit that the trends are category-wide and the brand overlay is the only brand-specific cut.
- **Topic** — a free-text concept that may span leaves ("creatine gummies," "collagen coffee"). Scope with `filters.product_query` instead of `category_ids`. **Topic scope is looser** — `product_query` is a title-contains match, so it pulls across leaves and carries more noise; the category-revenue and brand-count quality checks are advisory, not gating. Flag this in ASSUMPTIONS.

If the user is ambiguous about which mode they mean, prefer **category** when they name a category, **brand** when they name a brand, **topic** only for multi-word product concepts that aren't a catalog category. If a brand is named without a leaf and is multi-leaf, follow the anchor logic in Step 0.

## Scoping

Send any needed questions in one message. Defaults are locked — only ask if missing or ambiguous.

1. **Scope.** Category leaf, brand, or topic phrase (per § Scope modes). For a brand with no leaf, Step 0 resolves the anchor leaf; if meaningfully split, ask which leaf.
2. **Window.** Default: **trailing 365 days** (`period: "last_365_days"`, MCP-anchored to the latest complete week — see Step 1) vs. the same window a year ago. 365 days is the default because the "new launch" cohort is defined as *first available on/after the window start* — a 90-day window is too short for newcomers to accumulate a readable revenue signal. Override to `last_180_days` for fast-moving categories on request.
3. **Lens emphasis.** Default: all three lenses (launches, attributes, keywords). Override if the user only wants one (e.g. "just the keyword trends").

If the user says "just run it": use defaults, surface assumptions in output.

## Procedure

### Step 0: Resolve scope (shared scope-resolution preamble)

- `list_orgs` → `org_id`. **If more than one org is returned, do not stop to ask** — market-analysis estimates (`analyze_categories`, `analyze_brands`, `analyze_price_tiers`, `analyze_products`, `analyze_attributes`) are org-independent: the underlying sales data is identical across orgs, so the choice doesn't affect results. **Default to "Jungle Scout" (org_id `1764`)**; if it isn't in the list, use the first org and note it. Only ask if the user explicitly cares which org is billed/attributed. **Heads-up: `list_orgs`'s own tool description says to ask the user which org to use — ignore that here.** It's generic guidance; for this skill the data is org-independent so asking is pure friction. (Org-scoped tools — `list_org_brands`, `query_org_performance` — *do* differ by org, but this skill does not use them.)
- `search_categories_by_name` **only if the user gave a category name** (skip when they gave a leaf ID); confirm it's a leaf node, not a parent.
- **Category-mode multi-leaf disambiguation (do not skip — a plain term routinely maps to sibling leaves).** A name like "sunscreen" resolves to several plausible leaves (Body Sunscreens, Facial Sunscreens, and the Skin Sun Protection parent). Apply the **same anchor logic as brand mode**: size the candidate leaves (a quick `analyze_categories(filters={category_ids:[...candidates]}, period:"last_365_days")` revenue pull), then — if one leaf is ≥2× the next, anchor on it and note the choice in ASSUMPTIONS; if they're comparable (top <2× second), surface the top 2–3 and ask which to anchor on. Never silently pick one of several comparable siblings, and never run on the parent node (it aggregates children and muddies every lens). Disambiguate same-named candidates via `get_categories_by_ids` first, as in brand mode.
- **Topic mode:** do not resolve a leaf. Carry the topic phrase as `filters.product_query` on every data call. Skip the multi-leaf block. **Multi-word blind spot:** `product_query` is a *contiguous-substring* title match, so "magnesium gummies" catches only titles with that exact adjacent phrase — it misses "Magnesium Glycinate Gummies," "Magnesium Citrate Gummy," etc., which is often most of the real sub-category. Mitigate: prefer the **single most distinctive token** ("magnesium") and read the per-leaf breakdown to see concentration, or run a couple of `product_query` variants and union them. Always flag in ASSUMPTIONS that a multi-word topic undercounts intervening-word variants.

**Multi-leaf brand check (brand mode, when the user didn't specify a leaf):**
- Run `analyze_categories` with `filters={brand_query: <brand>}` (no `category_ids`), `detail_level: "summary"`, `include_enrichments: []`, `sort_by: "revenue"` to get the brand's **leaf-by-leaf footprint** — one row per leaf, revenue per leaf. Use `analyze_categories`, **not** `analyze_brands` (the latter is brand-grain and can't identify an anchor leaf). With no `category_ids`, each leaf row's `market_share` reads as the leaf's share of the brand's own total revenue — use it for the "% of brand revenue" figures.
- **Brand-match sanity check (do this before anchoring).** `brand_query` is a contains-match against the *normalized* brand value, and a multi-word storefront name often fails to match the canonical catalog brand. If the footprint comes back empty or implausibly tiny (total across leaves under ~$500K, or just a couple of stray low-revenue rows), the brand string didn't resolve — **do not anchor on the garbage rows.** Retry with the core brand token: drop corporate suffixes ("Nutrition", "Inc", "Co", "Labs", "LLC") and trailing descriptors, keeping the distinctive head word (e.g. "Quest Nutrition" → "Quest", "Liquid I.V." → "Liquid IV"). If the retry still looks empty, tell the user the brand wasn't found as given and ask for the exact storefront brand or a representative ASIN — don't fabricate a footprint. (Verified live 2026-06-03: "Quest Nutrition" → ~$10K of mis-tagged rows; "Quest" → ~$210M real footprint.)
- **Anchor leaf** = highest brand revenue. If top leaf ≥2× the second → anchor automatically, note in ASSUMPTIONS. If meaningfully split (top <2× second) → surface the top 3 leaves and ask which to anchor on; note they can name a smaller leaf in chat.
- **Duplicate-name guard:** the footprint frequently returns multiple distinct leaf IDs sharing a display name (the catalog's parallel men's/women's/kids' subtrees, an artifact of `detail_level: "summary"`). If two+ candidates share a name, call `get_categories_by_ids` on the tied IDs for the full disambiguated label before presenting the ask. Never show two identically-labeled options.
- "Just run it" on a multi-leaf brand → anchor on the largest-revenue leaf, surface the assumption.

**Quality checks — evaluated on the Step 1 pulls (A and the cohort split), not separate calls:**
- Category revenue ≥ $500K in window — else noise risk. (Advisory only in topic mode.)
- Brand count ≥ 10 — else survivorship risk. (Advisory only in topic mode.)
- Category revenue growth between −50% and +100% YoY — else taxonomy drift suspected.
- Latest-week freshness: handled in Step 1 — never hand-compute dates. Let the MCP anchor `end_date` to the latest complete week and read it back. Stop and flag if it resolves >6 weeks stale.

Quality flags surface in ASSUMPTIONS → Data quality, not in the FLAGS section. They weaken affected claims rather than describing innovation movement.

### Step 1: Pull the innovation pack

**Do not hand-compute `start_date`/`end_date`.** `analyze_categories`, `analyze_products`, and `analyze_attributes` default `end_date` to the latest complete market-analysis week and accept a `period` enum — let them anchor it. Passing explicit dates overrides the freshness default; a date inferred from training-era assumptions about "now" is exactly how the window drifts a year stale.

**Read the resolved window from A's response header** — echoed as `(YYYY-MM-DD to YYYY-MM-DD)`. Call that `[win_start, win_end]`. Use `win_end` as the freshness anchor and the keyword-history end date; use `win_start` as the launch cutoff. **Freshness sanity check:** `win_end` should be within ~2 weeks of today; if >6 weeks stale, stop and flag (connector/query problem, not normal lag).

Scope key: in **category/brand mode** pass `filters={category_ids:[leaf_id]}`; in **topic mode** pass `filters={product_query: "<topic>"}`. Below, `<scope_filter>` stands for whichever applies.

**A. Category/scope totals (context + freshness anchor).** Run first; everything else derives its window from A.
```
analyze_categories(
  filters=<scope_filter>,
  options={
    period: "last_365_days",          # omit start_date/end_date — MCP anchors
    comparison: "year_ago",
    detail_level: "summary",
    include_enrichments: [],
    extra_metrics: ["revenue", "avg_price", "revenue_growth", "units_sold_growth",
                    "avg_price_growth", "brand_count", "product_count"]
  }
)
```
`avg_price` here is the **category weighted ASP** — the baseline the Step 2 cohort ASP-posture read needs. (It was missing before; without it the posture read had no baseline and had to be derived as revenue÷units.)

**Topic-mode A returns a per-leaf breakdown, not one scope total.** With `product_query` (and no `category_ids`), `analyze_categories` returns one row per leaf the matched products fall in. So: **sum `revenue` across rows for the scope total**, report the **dominant leaf and how concentrated the topic is** (a topic that's 90% one leaf is really that leaf; one spread across many leaves is genuinely cross-category), and treat per-leaf `revenue_growth` as **advisory only** — it routinely returns `null` and absurd values (e.g. +2963%) because product-title matching reshuffles which leaf an ASIN lands in. Evaluate the quality floors on the summed total. (Category and brand modes pass a single `category_ids`, so A returns one clean row — the freshness window still reads from its header.)

Waves B–D run after A (they need `win_start`/`win_end`); B, C, D have no dependency on each other and fire together.

**B. Launch cohort (new vs. existing revenue split).**
```
analyze_products(
  filters=<scope_filter>,
  options={
    group_by: "launch_cohort",
    period: "last_365_days",
    comparison: "none",               # cohort growth-vs-year-ago is meaningless: the new cohort didn't exist a year ago
    detail_level: "summary",
    metrics: ["revenue", "units_sold", "avg_price"]   # NOT product_count — invalid at product grain
  }
)
```
Returns two rows, `cohort: "new"` and `cohort: "existing"`, each with `revenue_total_sum`, `sales_total_sum`, `weighted_average_selling_price`, and `cohort_boundary` (= `win_start`, the launch cutoff). **Compute new-cohort revenue share by hand:** `new_rev / (new_rev + existing_rev)`. **Do not read `revenue_total_sum__pct_of_total` / `market_share` here — it returns `1.0` for both cohorts** (each cohort is 100% of its own partition; it is not category share). **Denominator note:** the share's denominator is B's `new + existing`, which can run a few percent short of A's category total (ASINs with a null `first_date_available` fall out of the cohort split — verified live: a cohort total ~$10M under a $360M category). Use B's own total as the denominator and don't mix it with A's; the small gap is expected, not an error.

**C. Breakout launches (the specific new products gaining traction).**
```
analyze_products(
  filters={ ...<scope_filter>, launched_after: win_start },
  options={
    period: "last_365_days",
    comparison: "none",
    detail_level: "standard",          # need title + brand to name the launch
    sort_by: "revenue",
    limit: 25,                         # over-pull; collapses to ~8 lines after parent dedupe below
    extra_metrics: ["units_sold", "avg_price", "rating"]   # NOT reviews — variant_review_count_sum is null for ~half of new launches; unusable
  }
)
```
`launched_after: win_start` restricts to ASINs first available on/after the cutoff — the same cohort as B's "new" row, now itemized.

**Dedupe by parent line before ranking (required).** The result is one row per ASIN, and sibling variants of a single new product (the 10-count and 20-count of the same sampler, different flavors of one launch) each get their own row — so a single product line double-lists and its revenue splits across rows. **`product_grain: "parent_asin"` does NOT fix this** — the same `parent_asin` still returns multiple rows (verified live 2026-06-03: The New Primal parent `B0FT6CW9VV` appeared twice). So pull at ASIN grain with `limit: 25` and **collapse in two passes: (1) dedupe by `asin` first** — the *same* ASIN can appear under two different `parent_asin`s when Amazon re-parents a variant mid-window (verified live: Amazon Basics yoga mat `B0DN5SBPG3` appeared under two parents at $264K and $52K). Keep one row per ASIN, taking the **max-revenue** instance (conservative — summing risks double-counting a re-parented estimate). **(2) Then group the deduped ASINs by `parent_asin`** (falling back to `asin` when null), sum `revenue`/`units`, take max `rating` / earliest `first_date_available`. Rank the collapsed lines by summed revenue; take the top ~8 for the visual. **Then cap display at one line per brand** unless a brand genuinely has two distinct launches — otherwise one incumbent's variant spree (e.g. five New Primal SKUs) crowds out the rest of the frontier. Note the crowding in prose rather than letting it fill the chart. **Hijacker/dupe guard:** a "new" ASIN whose title is a verbatim copy of an established product's title (seen live: a `gonalulu` listing duplicating "Relief Sun"'s title) is a hijacker/counterfeit, not a launch — it would mis-tag as a new-to-category entrant. Drop a breakout line whose title exactly matches a known existing product under a different brand.

**Find the theme first — it's the real innovation signal, not brand newness.** The most useful read is the *shared descriptor* across the breakout lines: scan the deduped titles for a recurring claim/format/ingredient and report it as the headline. In Whey the breakouts cluster on **"clear whey / clear protein"** (Arrae, Oath, SEEQ, Bloom, Myprotein, GRAMMS) — that theme is the story, more than any single launch. Themes cross brand age: **a genuine innovation is often launched by an incumbent**, so do NOT gate the innovation read on whether the brand is new (verified live 2026-06-03: SEEQ had ~$8M prior-year revenue — an incumbent — yet its clear-whey SKUs are squarely part of the clear-protein wave). Lead with the theme and the lines that carry it, regardless of brand age.

**Fallback when no single word repeats — look for a *pattern*, not a phrase.** The shared-token scan works for "clear whey" but misses *combinatorial* innovation, where the pattern is structural. In Collagen the frontier was collagen used as a **stacking base** — collagen + colostrum (Jocko Fuel), + creatine (NeoCell), + electrolytes (Ultima, FlavCity), + HMB (Juven), + bone broth (Brodo) — no recurring word, but an obvious "base + functional add-in" pattern (verified live). When titles share no token, check for: (a) a recurring *combination* (the category as a base + a rotating second ingredient/benefit), (b) a recurring *format×claim* pairing, or (c) a recurring *positioning* (e.g. "for women," "sugar-free"). Name the pattern in plain language ("collagen as a stacking base for [X]") rather than forcing a non-existent keyword. If neither a phrase nor a pattern emerges, say the launches are heterogeneous — don't invent a theme.

**Secondary tag — new-to-category brand vs. incumbent line extension.** Useful context, not the lead. Pull the brand set once with a year-ago comparison:
```
analyze_brands(filters=<scope_filter>, options={period:"last_365_days", comparison:"year_ago",
  detail_level:"summary", include_enrichments:[], sort_by:"revenue", limit:200,
  extra_metrics:["revenue_comparison"]})
```
A breakout whose brand had **~zero prior-year revenue** (`revenue_comparison` ≈ 0 / absent from the year-ago set) is a **new-to-category entrant**; meaningful prior-year revenue = **incumbent extension**. Use this to separate a pure flavor/pack line extension (Premier "Plus Fiber," Dymatize ISO100 flavor, Jack Link's × MrBeast box) from a true new brand — but remember an incumbent extension can still be a genuine innovation (SEEQ), so weight it by the *theme*, not the tag.

**Leaf-coherence caveat (R3-C).** A product leaf often contains mis-shelved accessories — the "Yoga Mats" leaf returns yoga-mat *holders* and *cleaner sprays* as "launches" (verified live). Don't hard-drop them (you'll lose legit edge products), but **prefer breakout lines whose titles match the category concept** when choosing the top ~8, and if a meaningful share of breakout revenue is off-concept, note it in ASSUMPTIONS → Data quality ("leaf includes accessories/adjacent products; breakout list lightly filtered to the category concept").

**In brand mode**, also note which (if any) of these top lines belong to the focal brand — that is the brand overlay.

**D. Attribute share shift (which attributes/values are driving revenue) — discover → drill.**
- **Discover** (rank the attribute vocabulary):
```
analyze_attributes(filters=<scope_filter>, options={mode:"discover", period:"last_365_days"})
```
  **Rank discover rows by `product_count` (distinct, safe to aggregate) — NOT by `revenue_total_sum`.** Discover revenue is inflated for multi-value attributes (a product with three flavors counts in three rows), so a multi-value attribute like "ingredients" can read multiples of the true category revenue. Pick the **1–2 attributes that are high-coverage AND carry a product *concept*** — format, claim, ingredient, or material: `item_form`, `material`, `flavor`, `ingredients`, `fabric_type`, `style`. **De-prioritize pure dimensional attributes — `size` and `color` — for the innovation read.** They're high-coverage but reflect *assortment mix*, not innovation: drilling `size` on Women's Leggings shows "M +3.4pp, L +2.1pp" — a brand adding mid-size variants, signifying nothing about what's new (verified live 2026-06-03). Use size/color only as context, never as the headline rising attribute, and **never fire the attribute-migration flag off `size`** (color only if it plausibly encodes a trend, e.g. a launch-color wave). Also skip pure-identifier attributes (`items_per_pack`, `num_packs`, `total_items_count`). **Coverage floor:** ignore any attribute whose `product_count` is under ~5% of the category's product count — spurious mis-tags, not real dimensions (e.g. "flavor"/"ingredients" on Yoga Mats with a handful of products each).
- **Drill** each chosen attribute (drill revenue *is* clean — per single value, sums to category total):
```
analyze_attributes(
  filters={ ...<scope_filter>, attribute: "<name>" },
  options={ mode:"drill", period:"last_365_days", comparison:"year_ago",
            sort_by:"revenue", limit:15,
            extra_metrics:["revenue_growth","market_share","market_share_growth"] }
)
```
  Per value you get `revenue_total_sum`, `revenue_total_sum__pct_of_total` (clean category share), `revenue_total_sum__delta_pct` (revenue growth), `revenue_total_sum__pct_of_total_delta` (**share-point change**, as a fraction — ×100 for pp), and `product_count`.
  - **Exclude catch-all values from the rising/fading narrative and the bar:** `Other`, `Assorted`, `Mixed`, `Various`, `Unspecified`. These are large and often among the biggest movers (jerky flavor "Other" is 27.6% share, −2.8pp) but mean nothing — you cannot report "the Other flavor is declining." Note `Unflavored` is a *real* value (the protein category's fastest-rising flavor), not a catch-all — the exclusion list is literal, not "anything vague."
  - **Meaningful-move gate (the lens is only a trend if something actually moved):** the magnitude of the top share shift varies wildly by category — jerky flavor "Beef" moved **+4.9pp** while collagen item_form's top mover was **+0.25pp** (verified live). So only name a value as **rising/fading if |share Δ| ≥ 0.5pp**; if no value (after catch-all exclusion and the small-base floor) clears 0.5pp, **report "mix is stable — no meaningful migration"** rather than crowning a sub-0.3pp "winner." Reserve the *attribute-migration flag* (Step 3) for ≥2pp moves.
  - **Reconcile with the launches lens (C) before floor-ing a value out.** The attribute floor can suppress exactly the signal C is highlighting: "serum sunscreen" was the #3 breakout launch ($876K, The Ordinary) yet sat at 0.47% category share in D and got floored (verified live). When a value is **prominent among new launches (C) but sub-floor in total share (D)**, that's the signature of an *emerging* form — surface it as "emerging but still small" from C rather than letting D's floor erase it, and don't let the migration flag crown a duller high-share move (e.g. "Cream over Lotion") while the real story is the small-but-launching form. Cross-check the breakout theme against the attribute movers and report the disagreement when it happens.

**E. Rising keywords (search demand momentum).** Only if the keyword lens is in scope.
- **Derive the seed term explicitly** (this isn't automatic): take the **product concept, stripped of qualifiers** — for category mode, drop the segment words from the leaf name ("Body Sunscreens" → `sunscreen`, "Sports Nutrition Whey Protein Powders" → `whey protein`); for topic mode, use the topic phrase's head noun; for brand mode, use the anchor-leaf concept (not the brand name — you want the category's demand, not branded search). State the seed you used in ASSUMPTIONS.
- **Scope mismatch warning:** this lens is **concept-scoped, not leaf-scoped** — it searches all keywords co-occurring with the seed, so seeding off "Body Sunscreens" returns face/lip/kids terms too (verified live). It therefore operates at a *broader* scope than lenses A–D, which are pinned to one leaf. Say so in ASSUMPTIONS, and where the tool allows, narrow with `root_category` / `category__in` to pull the keyword set toward the leaf's category. Don't present keyword findings as if they're scoped to the same leaf as the launch/attribute lenses.
- **Discover rising related terms:**
```
search_keywords_by_keyword(
  filters={ keyword: "<derived seed>", country_code: "US",
            min_search_volume: 500, min_relevancy_score: 0.5 },   # 0.5 = weak default; the token filter below is the real screen
  options={ order_by: "search_volume", sort_direction: "desc", limit: 50 }
)
```
  **Retry once on a transient gate.** The keyword tools intermittently return "No approval received" on the first call and succeed on retry (verified live). Retry once before treating the keyword lens as unavailable — important for unattended/scheduled runs, which would otherwise drop the lens silently.
  **The raw related-keyword set is heavily contaminated** — it returns co-searched terms, not topic terms. Seeding "creatine" surfaced "lightning deals of today prime," "lemme gummies," "goli gummies," "cortisol supplements for women," "collagen for women" alongside the real hits (verified live 2026-06-03). **Filter before reporting.** The **topic-token post-filter is the load-bearing one**: keep a row only if its text contains the head term or an obvious synonym/root (for "creatine": keep "creatine gummies," "creatine for women," "creatina"; drop "lemme gummies," "lightning deals"). `min_relevancy_score` is a weak secondary screen — at 0.5 it still left "life" (+196%) in the collagen results (verified live), so do not rely on it alone. Never report a term that fails the token filter, regardless of its relevancy score or trend.
  - **Separate brand terms from generic/attribute terms.** Brand searches ("thorne creatine," "optimum nutrition whey protein," "ghost protein powder") are a legitimate *rising-brand* signal but are NOT attribute/format trends — don't blend them into the "what attribute is rising" read. Bucket them: report rising *generic/attribute* terms (the demand-shape signal) separately from rising *brand* terms (a competitive signal), and lead with the generic ones.
  - **Run the token filter BEFORE trusting any trend number.** `quarterly_trend` throws absurd seasonal/event spikes on off-topic junk — seeding "collagen" returned "mother's day" at +4,564% and "life" at +196% (verified live). These vanish once the token filter runs, so filter first, *then* rank — never let a high trend pull a non-topic term into the report.
  - **Allow known-root and language variants in the token filter.** The filter is "contains a topic token," not "contains the exact English head term" — keep obvious roots and translations (for "collagen": `colageno`, `colágeno`, `colageno hidrolizado`; for "creatine": `creatina`). Rising Spanish-language terms are a real US-marketplace demand signal, not noise.
  Pick 1–3 surviving generic terms that read as *emerging* (a new attribute, format, or claim — e.g. "clear whey," "grass fed whey," "creatine gummies") rather than the generic head term.
- **Confirm momentum** — pull weekly history for the head term and the candidate rising terms over the trailing ~52 weeks of the resolved window:
```
get_keyword_search_volume_history(
  filters={ keyword_text: "<term>" },
  options={ search_time_min: <win_end minus ~364 days>, search_time_max: win_end }
)
```
  This tool has **no `period` enum and requires explicit dates** — derive them from `win_end` (the resolved freshness anchor), not from a hand-guessed "now."
  - **Shortlist on `quarterly_trend`, but report YoY from the history.** The discovery call's `quarterly_trend` (QoQ) is a fine cheap filter to pick candidates, but it **diverges materially from the real trend and must not be the reported number**: for "creatine gummies" `quarterly_trend` read +12.8% while the series (≈50K → ≈131K over the year) gives a YoY of **≈+28%** — QoQ understated it ~2× and is seasonally noisy (verified live 2026-06-03). So for each of the 1–3 finalists, compute momentum from the history as **latest-4-weeks mean vs. the same 4 weeks a year earlier** (YoY, to strip seasonality); fall back to trailing-13 vs. prior-13 only if a year of history isn't available. Report the YoY figure.
  - **Seasonal categories: YoY-from-history is mandatory, not optional.** For anything with a strong season (sunscreen, allergy, holiday, swimwear), `quarterly_trend` is *dominated* by where the window sits in the season — a May sunscreen pull showed toddler +891%, kids +667%, baby +455% QoQ, all season artifacts (verified live). Never report QoQ for a seasonal scope; the YoY comparison of matched calendar weeks is the only valid read. (This is the keyword-lens analog of the apparel hazard on the attribute lens — flag it in ASSUMPTIONS for seasonal scopes.)

### Step 2: Compute the headline metrics

- **New-launch revenue share** = `new_rev / (new_rev + existing_rev)` from B (computed by hand — see B). Express as "% of category revenue from products launched in the last [window]" with the dollar figure. Compare to a rough expectation: in most mature categories <5% is normal; >10% signals an unusually active innovation frontier.
- **New-launch ASP vs. category ASP** — is the new cohort entering above or below the category's weighted ASP (from A)? Premium entry vs. value entry is an innovation-posture signal.
- **Breakout launches** — from C, **after parent-dedupe and one-line-per-brand capping**, the top new lines by summed revenue. Name brand + a short product descriptor + trailing revenue + launch month, and **tag each as new-to-category entrant or incumbent line extension** (per C's brand-newness classification). Rank by absolute revenue, not growth %, so a $5K novelty doesn't outrank a $2M genuine breakout. **Do not quote per-product ASP as a price signal** (pack-size distortion); read price posture at the cohort level instead (next bullet). **Lead with the shared theme across the breakouts** (e.g. "clear protein") — the recurring descriptor is the innovation story; the new-vs-incumbent tag is secondary context, since incumbents launch genuine innovations too.
- **New-launch ASP posture (cohort level only)** — compare B's new-cohort weighted ASP to the category weighted ASP from A. This is the legitimate price read; per-product ASPs are not comparable across pack sizes.
- **Rising attributes** — from D, rank attribute values by **share-point change** (`pct_of_total_delta` ×100), not raw revenue growth %. Apply three gates in order: (1) **exclude catch-alls** (`Other`, `Assorted`, `Mixed`, `Various`, `Unspecified` — uninterpretable); (2) **small-base floor** — ignore values under 1% category share unless they cleared ~$1M revenue (a +89% growth on a 1%-share / 36-product value like "Lemonade" is noise; a +1.55pp gain on a large base like "Unflavored" is real); (3) **meaningful-move gate** — only name a value rising/fading if |share Δ| ≥ 0.5pp; if nothing clears it, report "mix is stable." For surviving values report share Δ (pp), revenue growth %, and current share; name 1–2 fading values for contrast.
- **Rising keywords** — from E, the terms with the largest YoY volume increase that also clear a volume floor (~1,000 weekly searches). Report current volume and YoY %.
- **Brand overlay (brand mode only)** — the brand's own new launches among C (count and revenue), and whether the brand is represented in the rising attributes/keywords. State plainly whether the brand is participating in the frontier or absent from it.

### Step 3: Evaluate flags (1–3 max)

Trigger only when material. Surface in severity order; cap at 3.

**Thresholds below are calibrated against live data (2026-06-03) across ~10 categories** — new-launch share runs 2–9% in CPG/supplements but ~12% in apparel (SKU churn, not innovation), so surge logic pairs share with growth. Re-check the calibration if the data drifts; see regression I15.

**Tier 1 — Scope-level** (context that overrides individual signals):
- **Hot frontier** (positive) — category revenue growth **≥+25% YoY**: a genuinely booming category; name the launch theme and lead with it. (Fires creatine +65%, electrolytes +28%; quiet on collagen +19%, jerky +16%.)
- **Stagnant frontier** — category revenue growth **<−3%** OR (new-launch share **<3% AND** growth **<+5%**): contracting or inert; overrides individual "rising" signals. (Fires Colloidal Gold −7%, Silk Eye Bags −6%.)
- **Taxonomy drift suspected** — category revenue growth >+100% or brand-count change >25% YoY: treat all share-shift reads as suspect.

**Tier 2 — Frontier** (where the innovation is concentrating):
- **Newcomer surge** — new-launch revenue share **≥7% AND category growth ≥+10%**: an unusually active launch frontier in a growing market; name the cohort's ASP posture. (The growth gate is load-bearing — it excludes apparel like Women's Leggings, which hits 12% new-share on flat +3.8% growth from SKU churn, not real entry. Fires creatine 7.8%/+65%, electrolytes 8.6%/+28%.)
- **Attribute migration** — **any single non-catch-all attribute value with |share Δ| ≥1.5pp** (gain or loss); name it and its counterpart. This is OR logic, not "a +2pp gainer AND a −2pp shedder" — the old AND form never fired because excluding catch-alls (`Other`/`Assorted`) usually removes the big shedder. (Fires jerky Beef +4.9pp, whey Unflavored +1.6 / Chocolate −2.0, electrolytes Lemonade +1.7; quiet on collagen <0.3pp.)
- **Demand-ahead-of-supply** — a rising keyword (>+25% YoY volume) whose matching attribute/product is *not* among the revenue leaders: search interest is running ahead of what's selling (a whitespace signal).

**Tier 3 — Brand (brand mode only):**
- **Brand absent from the frontier** — zero of the brand's ASINs appear in the breakout launches AND the brand is not represented in the leading rising attribute: the category is innovating without the brand.
- **Brand riding the frontier** — the brand has ≥1 breakout launch OR leads a rising attribute: name it as a positive.

**No flags fired** — surface a single read: "Frontier is quiet — tracking with category, no concentrated innovation signal."

**Cap-at-3 (mechanical):** Tier 1 → Tier 2 → Tier 3, drop overflow from the bottom. Within a tier the listed order is the severity order. A Tier 1 flag, if it fires, always makes the cut.

### Step 4: Render output

See § Output format. Always render the two visuals (breakout launches → rising attributes), then the rising-keywords table. Skip a lens cleanly (with a one-line note) if its data didn't clear the quality floor, rather than padding.

## Output format

Each visual sits inside the narrative section whose argument it carries — not in a top block. Each is preceded by a sentence naming what it shows and followed by a sentence drawing the insight out. Visuals earn their place by making the surrounding prose shorter.

```
HEADLINE
[One sentence. New-launch revenue share + the single sharpest frontier signal (a launch theme like "clear protein," an attribute migration, or a rising term).]
[Headline number: new-launch revenue $ and % of category.]

FLAGS  (1–3 max; omit section if none triggered)
⚑ [Flag name] — [one-line evidence]

NEW LAUNCHES
[Two sentences: how much of the category's revenue is going to products launched in the window, the dollar figure, and whether newcomers are entering premium or value vs. category ASP. Then set up the breakout bar.]

[VISUAL 1: Breakout launches bar]

[One sentence reading the visual: "The top newcomer, [brand] [product] at $X ASP, has already pulled $YM — more than the next three combined." Or "No single breakout; new revenue is spread thin across many small launches."]

| New product | Brand | Type | Launched | Revenue | ASP* | Rating |
| ...         | ...   | ...  | ...      | ...     | ...  | ...    |
(top ~6–8 deduped parent lines; Type = new-to-category entrant / incumbent extension; bold focal-brand rows in brand mode)
*ASP is listing/pack price — not unit-comparable across pack sizes; shown for reference, not as a price-trend signal.

RISING ATTRIBUTES
[Two sentences: which attribute is reshaping demand, naming the value gaining the most share and the one shedding it. Then set up the share-shift bar.]

[VISUAL 2: Rising-attribute share-shift bar]

[One sentence reading the visual: "[Value] gained +Npp share while [value] shed −Mpp — demand is migrating toward [theme]."]

RISING KEYWORDS  (omit if keyword lens out of scope or no term cleared the floor)
| Search term | Weekly volume | YoY Δ | Read |
| ...         | ...           | ...   | ...  |
[One line: the sharpest rising term and whether selling supply has caught up to it.]

[Brand overlay paragraph — brand mode only: is the focal brand launching into this frontier, or absent from it? One honest sentence.]

[Closing line — single sentence. Name fired flags / the sharpest prose signal as drill-down options; close with "or have a different question?". If nothing notable, "Anything you want to drill into from here?"]

---

ASSUMPTIONS
- Scope: [category leaf id+name / brand+anchor leaf / topic phrase], mode: [category/brand/topic]
- Window: [win_start to win_end], comparison: YoY; launch cutoff: [win_start]
- Anchor leaf (brand mode): [id, name] — [X]% of brand's Amazon revenue; other top leaves: [...]
- Lenses run: [launches / attributes / keywords]; any skipped and why
- Keyword seed + scope (if keyword lens ran): [seed term used], concept-scoped (broader than the leaf); for seasonal scopes note momentum is YoY-from-history, not QoQ
- Org: Jungle Scout (org-independent data); new-launch share denominator = launch-cohort total (may run a few % under category total)
- Data quality: [flags fired or "clean"; note topic-mode looser guarantees]
```

Tables for evidence. Prose around visuals carries the argument. Visuals always render in order: breakout launches → rising attributes.

## The two visuals

Both use `visualize:show_widget` with HTML + Chart.js. Load `read_me` with `modules=["chart"]` once at start of run. Constraints below are non-negotiable — they prevent drift across runs and match the rest of the skill library.

**Common constraints:**
- Chart.js UMD via cdnjs: `<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>`
- Hardcoded hex (canvas can't read CSS vars). Detect dark mode with `matchMedia('(prefers-color-scheme: dark)').matches` and swap the palette.
- **Palette — Jungle Scout brand (default).** Light: focal `#4A2DFF`, peer `#40AFFF`, other `#C9C9CB`, text `#444441`, grid `rgba(0,0,0,0.06)`, positive `#007A6B`, negative/attention `#FF5E00`. Dark: focal `#8B73FF`, peer `#40AFFF`, other `#5F5E5A`, text `#D3D1C7`, grid `rgba(255,255,255,0.08)`, positive `#2FB89E`, negative `#FF7A33`. Same hues both modes; dark values are lighter tints. Colors only — never adopt JS fonts/logos. Use orange surgically (only for share-shedding values and for the laggard signal).
- Custom HTML legends above the chart (not Chart.js built-in). Round all displayed numbers. Disable default legend: `plugins:{legend:{display:false}}`.

### Visual 1 — Breakout launches bar

Reads: "Which products launched in the window are pulling the most revenue, and at what price?"

**Spec:**
- Above the chart, a metric callout: "NEW-LAUNCH REVENUE · **$XM** · Y% of category". Number in focal color, 24px/500; secondary line "products launched since [win_start]".
- Horizontal bar chart (`indexAxis:'y'`), top ~8 **deduped parent lines** by trailing revenue (one row per parent, ≤1 per brand — see Step 1 C).
- **Bar color by brand newness (P4): new-to-category entrants = focal color; incumbent line extensions = peer color** — so the genuine frontier reads at a glance against incumbents extending a line. In **brand mode**, give the focal brand's own lines a third treatment (a darker focal or an outline) and say so in the legend. Custom HTML legend labels whichever split applies.
- X-axis ticks currency `$XM`. Right padding ~70 for end-of-bar labels.
- **End-of-bar label = launch month** (e.g. `Aug '25`), in text color — recency is the honest second variable. **Do NOT label ASP**: weighted ASP is the listing/pack price, so an 80-count case ($145) and a 15-count ($19) of the same product look wildly different — ASP is not unit-comparable across pack sizes and misleads on the bar (verified live 2026-06-03). Keep ASP in the tooltip only, and read price *posture* at the cohort level (Step 2), where pack-size mix washes out.
- Tooltip: revenue, units, ASP (labeled "listing price"), rating, launch date.
- If fewer than 3 deduped lines clear ~$100K revenue, **skip the chart** and say so in prose ("no breakout launches — new revenue is diffuse"); don't render a near-empty bar.

### Visual 2 — Rising-attribute share-shift bar

Reads: "Which attribute values are gaining or losing revenue share year-over-year?"

**Spec:**
- Horizontal bar chart, one bar per attribute value, sorted by **share-point change** (`pct_of_total_delta`×100) descending — gainers on top, shedders at the bottom. Show the top ~5 gainers and bottom ~3 shedders (diverging).
- Bar length & sign = share-point change in pp (a diverging bar centered at 0). Positive bars positive-color (teal), negative bars attention-color (orange).
- Above the chart: the attribute name as title ("Flavor — share shift, YoY") and a legend ("Gaining share" teal / "Losing share" orange).
- End-of-bar label = the value's current category share `%` (so a big gain on a small base is visually honest). Plugin template below.
- Apply the **small-base floor before plotting** (Step 2): drop values under 1% share unless they cleared the ~$1M revenue floor — keeps small-base noise off the chart.
- **Exclude catch-all values** (`Other`, `Assorted`, `Mixed`, `Various`, `Unspecified`) from the bar — they're uninterpretable even when they move a lot.
- **Stable-mix case:** if no remaining value clears ±0.5pp share change, **skip this visual** and write one line — "form/flavor mix is stable, no meaningful migration" — instead of plotting a bar of sub-0.3pp noise. The chart earns its place only when something actually moved.

**End-of-bar label plugin (required, both visuals):**
```js
const chart = Chart.getChart('CHART_ID');
const origDraw = chart.draw;
chart.draw = function() {
  origDraw.call(this);
  const ctx = this.ctx, meta = this.getDatasetMeta(0);
  ctx.save(); ctx.font='500 11px sans-serif'; ctx.textBaseline='middle';
  meta.data.forEach((bar,i)=>{ ctx.fillStyle=TEXT_HEX;
    ctx.fillText(LABELS[i], bar.x + 6, bar.y); });
  ctx.restore();
};
chart.draw();
```

### Why Chart.js, not hand-coded SVG

Chart.js auto-resizes on mobile and narrow widths with no fixed-viewBox math — the load-bearing reason; the same brief renders on a phone and a laptop without per-device tuning. It also handles tooltips and light/dark text adaptation natively, and produces consistent output across runs. Tradeoff: end-of-bar labels need ~12 lines of plugin code, templated above.

## Worked example: Whey Protein Powders (category mode)

**Illustrative figures from the 2026-06-03 live window (2025-05-24 → 2026-05-23) — refresh when running.**

**Setup:** "What's new in whey protein?" → category mode, leaf 6973717011, defaults (365d vs YoY, all lenses).

**Data (Step 1):**
- A: category ~$1.14B revenue. B: new cohort $36.4M / existing $1.108B → **new-launch share 3.2%**; new-cohort ASP $40.3 vs existing $49.4 → newcomers entering ~18% below category ASP (value entry).
- D (flavor drill): Unflavored +1.55pp share (rev +42.7%, 11.7% share) and Coffee/Cinnamon gaining; Cookies & Cream −0.77pp, Chocolate −1.98pp. Lemonade +89% growth but 1.0% share / 36 products → **dropped by the small-base floor.**

**Headline:** "Products launched in the last year hold just 3.2% of whey-protein revenue ($36.4M), and they're entering ~18% below category price — but demand is migrating on flavor: Unflavored gained +1.6pp share while Chocolate shed −2.0pp."

**Flags:** Tier 2 · Attribute migration (Unflavored +1.6pp vs Chocolate −2.0pp). No newcomer surge (3.2% < 10%).

**Closing:** "Want to dig into the flavor migration, the value-priced newcomers, or the rising search terms — or a different question?"

## Notes for the agent

- **This is a discovery brief, not a diagnosis.** Name what's emerging and size it; don't explain *why* a brand is winning/losing (that's `share-diagnosis`) or rank a brand against peers (`brand-benchmark`). If the story turns into "why," name the next skill in the closing line.

- **`launch_cohort` market share is a trap.** The `revenue_total_sum__pct_of_total` / `market_share` field returns `1.0` for both the new and existing cohorts — it's share *within the cohort partition*, not category share. Always compute new-launch share by hand: `new_rev / (new_rev + existing_rev)`. Verified live 2026-06-03.

- **Discover-mode attribute revenue is double-counted.** A product with N values of an attribute contributes to N rows, so discover `revenue_total_sum` can exceed true category revenue several-fold (e.g. "ingredients" ≈ $4.96B in a ~$1.14B category). Rank discover by `product_count` (distinct). Only **drill**-mode revenue is clean.

- **Sort innovation signals by the right grain.** Raw growth % at fine grain surfaces small-base noise — a 36-product flavor at +89% is not a trend. Rank breakout launches by **absolute revenue**, rank rising attributes by **share-point change** with a share/revenue floor, rank rising keywords by **YoY volume change** with a volume floor. This is the same lesson as "use brand grain, not ASIN grain" — fine-grain growth % over-rewards tiny bases.

- **Dedupe breakout launches in two passes — ASIN first, then parent.** `product_grain:"parent_asin"` does NOT collapse variants (one parent, multiple rows), and the *same ASIN* can appear under two different parents when Amazon re-parents mid-window (Amazon Basics yoga mat at $264K and $52K). So over-pull at ASIN grain, dedupe by `asin` (keep the max-revenue instance), then group by `parent_asin`, then cap one line per brand so an incumbent's variant spree doesn't fill the chart. Skipping this double-counts a single launch.

- **Innovation theme > brand newness.** The headline launch signal is the recurring descriptor across breakout titles (e.g. "clear protein"), not whether the brand is new — incumbents launch genuine innovations (SEEQ, an ~$8M-prior-year brand, rode the clear-whey wave). Use the new-vs-incumbent tag as secondary context only.

- **Product leaves contain mis-shelved accessories.** Holders and cleaner sprays surface as "yoga mat launches." Don't hard-filter, but prefer on-concept titles for the top ~8 and caveat in ASSUMPTIONS when off-concept revenue is meaningful.

- **Rising attributes ≠ dimensional attributes.** `size` and `color` are high-coverage but encode assortment mix, not innovation (leggings "size M +3.4pp" means nothing). Lead the rising-attribute read with concept attributes (form/material/ingredient/claim); never fire the migration flag off `size`.

- **Reviews are unusable on new launches — null OR wildly inflated.** `variant_review_count_sum` is null for ~half of new ASINs and occasionally inflated by parent rollup (a 2026-04 launch showed 57K reviews on $20K revenue). Dropped from the breakout call; use `rating` only, and even then treat a high rating on a tiny base with caution.

- **US by default; non-US needs full consistency.** `marketplace:"uk"` works (returns real UK data) but leaf IDs differ by marketplace and the keyword tools key on `country_code`. For a non-US run, pass the marketplace on every `analyze_*` call, resolve leaves in that marketplace, and set keyword `country_code` to match — don't mix.

- **Keyword discovery is co-search, not topic search — filter hard.** `search_keywords_by_keyword` returns terms searched by the same shoppers, so "creatine" pulls in "lemme gummies" and "lightning deals." Always apply `min_relevancy_score` *and* a topic-token post-filter, and bucket rising *brand* terms separately from rising *generic/attribute* terms. Never report a term that contains no topic token.

- **Default to a 365-day window.** The launch cohort is "first available on/after window start." A 90-day window leaves newcomers too little time to register revenue; 365 days reads the real frontier. Drop to 180 only for genuinely fast-moving categories.

- **Never hand-compute dates.** Let `analyze_*` anchor `end_date` to the latest complete week; read `[win_start, win_end]` from A's header. `launched_after` uses `win_start`; keyword history (which has no `period` enum) derives its dates from `win_end`. Stop and flag if the window resolves >6 weeks stale — that's a connector problem, not lag.

- **Topic mode is looser — say so.** `product_query` is a title-contains match across leaves; it carries cross-category noise and the revenue/brand-count quality floors become advisory. Always flag topic-mode looseness in ASSUMPTIONS so the reader discounts appropriately.

- **Brand mode = category frontier + brand overlay.** The trends are category-wide; the only brand-specific cut is whether the brand's own ASINs appear among the breakout launches / lead a rising attribute. State plainly whether the brand is participating in or absent from the frontier — that honest one-liner is often the most useful sentence in the brief.

- **`brand_query` under-matches multi-word storefront names — sanity-check the footprint.** It's a contains-match on the normalized brand, so "Quest Nutrition" resolves to ~$10K of stray rows while "Quest" returns the real ~$210M footprint. Before anchoring, confirm the footprint total is plausible; if not, retry with the core token (drop "Nutrition"/"Labs"/"Inc"/etc.) and, failing that, ask for the exact brand or an ASIN. This gotcha is shared with `brand-benchmark`'s Step 0 — the same retry guard belongs there.

- **Two visuals, always, in this order:** breakout launches → rising attributes. Keyword momentum is a table (offer the trend chart as a drill-down rather than spending the visual budget). Each visual is bookended by a setup and a read-out sentence and replaces a paragraph of description. Skip a visual cleanly if its data didn't clear the floor — don't render a near-empty chart.

- **Don't refer to visuals by number** ("as visual 2 shows"). Speak about the chart: "the breakout bar," "the share-shift bar."

- **Don't fabricate.** If a lens has no signal (no breakouts, flat attributes, no rising terms), say so plainly. A short honest "frontier is quiet here" is more useful than a manufactured trend. Flag every quality issue in ASSUMPTIONS rather than papering over it.
