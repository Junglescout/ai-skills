# MCP tool reference — title rewrite and item highlights

Accurate parameter and **response-field** reference for the Jungle Scout Cobalt MCP tools this
skill uses. Verified against live MCP server behavior on 2026-07-21. Read this before issuing
calls — several shapes are easy to get wrong, and a few differ from what the tool names suggest.

## Conventions that bite

- **Every tool takes `org_id`.** Resolve it with `list_orgs` first.
- **Marketplace casing differs by tool family:**
  - Sales-estimate tools (`analyze_products`, `analyze_brands`) take **lowercase** `marketplace`
    (e.g. `"us"`).
  - Keyword tools take **UPPERCASE** `country_code` (e.g. `"US"`).
- **Request friendly metric names, read raw response fields.** You *ask* for `revenue`,
  `search_volume`… but rows come back keyed by raw fields (`revenue_total_sum`,
  `estimated_exact_search_volume`…). Each payload includes a `metrics` block mapping friendly
  name → raw field, so never guess.
- **Deduplicate keyword rows** by `id` (or lowercased `name`) — multi-ASIN pulls repeat keywords.
  `scripts/pool_tools.py merge` does this for you.

---

## list_orgs

Entry point. Call with no arguments; pass the returned `id` as `org_id` everywhere else.

---

## analyze_products

Catalog census and competitor ASIN pools.

- **filters:** `brands` (stable brand names), `category_ids`, `asins`, `parent_asins`,
  `marketplace` (lower), `launched_after`/`launched_before`.
- **options:** `product_grain` (`"asin"` default | `"parent_asin"` | `"variant_group"`),
  `detail_level` (`"summary"|"standard"|"verbose"`), `sort_by`, `metrics`/`extra_metrics`,
  `period` (default `last_365_days` — the trailing-12-month window this skill wants),
  `comparison`, `limit` (≤500), `offset`.

**Grain shapes (live-verified 2026-07-21 — they matter a lot to this skill):**

- `asin` grain rows: `asin`, `title_stable`, `brand_stable` (+ requested metric fields;
  `standard`/`verbose` add category breadcrumbs, launch date, part number). **This is the only
  grain that returns per-child titles — the compliance census MUST run here.** Rows do **not**
  currently include `parent_asin`, so child→family mapping is not free at this grain.
- `parent_asin` grain rows: `parent_asin`, `brand_stable` + metrics — **no titles, no child
  ASINs**. Standalone listings collapse into a single `parent_asin: null` bucket. The payload's
  `enrichments.hero_asin` map carries one representative child (`asin`, `title`, `image_url`)
  per parent.
- `variant_group` grain rows: `variant_group`, `top_level_asin`, `is_standalone`,
  `brand_stable` + metrics, with `enrichments.variant_group` carrying `hero_asin`,
  `hero_title`, `hero_image_url` per family. Unlike `parent_asin` grain, standalone listings
  appear as their own rows (`is_standalone: true`) instead of being dropped into a null bucket —
  **use this grain for the family view**.
- To enumerate a specific family's children, call `asin` grain with
  `filters.parent_asins: ["<top_level_asin>"]`.

**Census recipe:** `asin` grain, `detail_level: "summary"`, `metrics: ["revenue"]`,
default period, paginate with `limit: 500` until exhausted → every child title + trailing-12-month
revenue. Separately pull `variant_group` grain once for the family roll-up (family revenue,
hero title, standalone flags).

---

## analyze_brands

Competitor set derivation, scoped to a category.

- **filters:** `category_ids`, `marketplace` (lower), `brands`.
- **options:** `sort_by` — friendly metrics including `revenue` and `revenue_growth`
  (growth requires `comparison` ≠ `none`), `limit`, `period`.
- **Response:** rows keyed by raw fields (e.g. `revenue_total_sum`) + the `metrics` mapping
  block.

Run twice per category: top 5 by `revenue`, top 3 by `revenue_growth`. Then pull each
competitor set's ASINs with `analyze_products` using `filters.brands: [<competitors>]` —
filter server-side, don't pull the whole category and drop the client brand in code.

---

## search_keywords_by_asin  /  search_keywords_by_keyword

The keyword pools.

- **Batch endpoint:** `search_keywords_by_asin` takes `filters.asins` as a list — pass all of a
  category's ASINs in ONE call, never loop per ASIN.
- **Common filters:** `country_code` (UPPER), `estimated_exact_search_volume_gte` (the volume
  floor — filter server-side), `min_search_volume`, `min_relevancy_score`, many `*_gte`/`*_lte`
  ranges. `search_keywords_by_keyword` takes a seed phrase instead of ASINs.
- **options:** `metrics` (friendly names or raw fields), `ordering` (raw field, e.g.
  `"-relative_value_score"`, `"-estimated_exact_search_volume"`), `limit` (≤1000), `offset`,
  and a date window: `search_time_min`/`search_time_max`.
- **The window defaults to the trailing 30 days.** Set `search_time_min`/`search_time_max` to
  the trailing 12 months so the aggregated `estimated_exact_search_volume` IS the
  trailing-12-month volume — this is how the skill ranks candidates without any per-keyword
  history calls.
- **Response:** `keywords[]` rows always carry `id` (e.g. `US_stanley tumbler`), `name`,
  `query_keyword`, `results_count`; requested metrics come back as raw fields
  (`estimated_exact_search_volume`, `relative_value_score`, `quarterly_trend`). A `metrics`
  metadata block maps friendly → raw.
- **Context-safe pull (verified):** `metrics: ["search_volume", "relative_value_score",
  "quarterly_trend"]`, `limit` ≈200, floor via `estimated_exact_search_volume_gte`. Write each
  page to the sandbox immediately.

---

## get_keyword_sov

Brand share of voice for the verification screen — "who owns this keyword."

- **filters:** `keywords` — a list of **search-term text** (e.g. `"rhinestone sunglasses"`),
  matched normalized. **NOT keyword IDs** — there is no ID-resolution step. Batch terms freely.
  `featured_brand` (optional) returns only the client brand's series with period-over-period
  change — use it for the "is our share materially below the leaders" check. `country_code`
  (UPPER).
- **options:** `metrics` (default `"equal_weighted_organic"`; also `equal_weighted_overall`,
  `equal_weighted_sponsored`, `position_weighted_*`), `aggregation` (`"week"` default |
  `"month"`), `top_brands` (default 10), `search_time_min`/`search_time_max` (default trailing
  ~90 days), `limit`, `offset`.
- **Response:** one row per **brand × time bucket**: `brand`, `week__month` (or `week__week`),
  `rank`, and the metric field e.g. `sov_equal_weighted_organic`. **Values are fractions 0–1**
  (0.38 = 38% share), not percentages. A `brand: null` row can appear (unattributed placements)
  — skip it. It is a time series, not a snapshot: take the latest bucket for a current read.
- **Context discipline:** weekly grain × 10 brands × N keywords adds up fast. For verification
  use `aggregation: "month"` over the trailing ~90 days with `top_brands: 5–10`.

---

## get_keyword_search_volume_history

Weekly search-volume history for ONE keyword.

- **filters:** `keyword_text` (a single keyword — **this tool cannot be batched**),
  `country_code` (UPPER).
- **options (required):** `search_time_min`, `search_time_max` (ISO dates); defaults for
  `group_by`, `metrics` (`"estimated_search_volume"`), `ordering` are fine.
- **Response:** `rows[]` of `keyword__text`, `search_time_week`, `estimated_search_volume`.
- **Use sparingly — one call per keyword.** Candidate ranking uses the 12-month window on the
  pool pulls instead (above). Reserve this tool for seasonality-tagging the final 2–4 keywords
  per family that actually enter a title.
