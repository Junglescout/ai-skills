# MCP tool reference — emerging keyword analysis

Accurate parameter and **response-field** reference for the Jungle Scout Cobalt MCP tools this skill
uses. Verified against current MCP server behavior. Read this before issuing calls — a few shapes are
easy to get wrong.

## Conventions that bite

- **Every tool takes `org_id`.** Resolve it with `list_orgs` first if not already selected.
- **Marketplace casing differs by tool family:**
  - Sales-estimate tools (`analyze_categories`, `analyze_products`) take **lowercase** `marketplace`
    (e.g. `"us"`).
  - Keyword and category tools take **UPPERCASE** `country_code` (e.g. `"US"`).
- **Request friendly metric names, read raw response fields.** For the sales-estimate tools you *ask* for
  `revenue`, `units_sold`, `avg_price`… but the returned rows are keyed by the underlying field names
  (`revenue_total_sum`, `sales_total_sum`, `weighted_average_selling_price`…). Each payload includes a
  `metrics` block mapping friendly name → field, so you never have to guess.
- **Deduplicate keyword rows.** Multi-ASIN keyword pulls can return the same keyword more than once.
  Dedupe by lowercased `name` before counting, scoring, or charting.

---

## search_categories_by_name

Resolve a category name to one or more Amazon browse nodes.

- **Input:** `org_id`, `country_code` (UPPER), `name`.
- **Response:** `categories[]`, each:
  `id`, `name`, `parent_id`, `path_by_id`, `path_by_name`, `subcategory_count`, `active`, `is_permitted`.
- Keep only `active && is_permitted`. Show `path_by_name` for disambiguation. If several plausible
  categories match, ask the user which.

---

## analyze_categories

Category-level totals for the overview KPIs.

- **filters:** `category_ids` (list; expands to the subtree), `marketplace` (lower).
- **options:** `metrics` / `extra_metrics` (friendly names), `comparison` (`"none"|"prior_period"|"year_ago"`),
  `aggregate` (true → single combined row across the scope), `limit`, `period`.
- **Friendly metrics to request:** `revenue`, `revenue_growth`, `units_sold`, `units_sold_growth`,
  `avg_price`, `product_count`, `brand_count`.
- **Response:** `rows[]` keyed by raw fields, e.g. `revenue_total_sum`, `revenue_total_sum__delta_pct`,
  `sales_total_sum`, `weighted_average_selling_price`, `product_count`, `brand_count`. Use `aggregate:true`
  (or `limit:1` on a single category) for the one overview row — never sum rows yourself.

---

## analyze_products

Builds the seed ASIN pool that keywords are pulled from. The **source lens** is expressed entirely through
these calls.

- **filters:** `category_ids`, `marketplace` (lower), `launched_after` (YYYY-MM-DD), `launched_before`,
  `asins`, `brands`.
- **options:** `sort_by` (friendly metric, e.g. `"revenue"`, `"units_sold_growth"`),
  `sort_direction` (`"asc"|"desc"`), `extra_metrics`, `thresholds` (`[{metric, min_value, max_value}]`),
  `detail_level` (`"summary"|"standard"|"verbose"`), `comparison` (`"prior_period"`|…), `limit`, `offset`.
- **detail_level fields:**
  - `summary` → `asin`, `title_stable`, `brand_stable`
  - `standard`/`verbose` add `image_url_hero`, `breadcrumb_leaf_node_id_stable`,
    `breadcrumb_leaf_node_name_stable`, `first_date_available`, plus the requested metric fields.
- Use `detail_level:"summary"` for pool-building (you only need ASINs); use `"standard"` when you want
  product titles/brands/launch dates in a keyword deep-dive.

**Source lens → calls:**
- **Market Leaders:** `sort_by:"revenue", sort_direction:"desc"`.
- **Up-and-Comers (default):** two calls — (a) `sort_by:"units_sold_growth", sort_direction:"desc"`,
  `extra_metrics:["units_sold_growth"]`, `thresholds:[{metric:"revenue", min_value:25000}]`,
  `comparison:"prior_period"`; (b) recent launches: `launched_after` = ~18 months ago,
  `sort_by:"revenue"`.
- **Everything:** Market Leaders + Up-and-Comers calls combined.
- **Widest Net:** Up-and-Comers + an additional category-wide `search_keywords_by_keyword` seed (below).

Merge pools round-robin (so each source is represented), dedupe by `asin`, cap ~150.

---

## search_keywords_by_asin  /  search_keywords_by_keyword

The keyword candidates. Each row carries **inline 30-day and 90-day trend**, so momentum is computed with
**no per-keyword history calls**.

- **Common filters:** `country_code` (UPPER), `min_search_volume`, `min_relevancy_score`, plus many
  `*_gte`/`*_lte` range filters.
  - `search_keywords_by_asin` adds `asins` (list; ASINs or `US_`-prefixed IDs) / `product__id__in`.
  - `search_keywords_by_keyword` adds `keyword` / `keywords` (seed text or keyword IDs) / `keyword__id__in`.
- **options:** `metrics`, `ordering` (e.g. `"-quarterly_trend"`, `"-estimated_exact_search_volume"`),
  `order_by`, `sort_direction`, `limit` (≤1000), `offset`, date window.
- **Valid metrics (friendly):** `id`, `name`, `search_volume`, `quarterly_trend`, `monthly_trend`,
  `relevancy_score`, `relative_value_score`, `ease_to_rank`.
- **Response:** `keywords[]` (raw rows) + a `metrics` metadata block. Friendly `search_volume` maps to the
  response field **`estimated_exact_search_volume`**. `quarterly_trend` = 90-day trend %, `monthly_trend`
  = 30-day trend %.
- **Not available:** `top_asins` and `category` are **not** supported keyword metrics. To find the products
  winning a keyword, use `get_keyword_sov` (brands) and/or `analyze_products` scoped to the category —
  do not request `top_asins`.

Recommended pull: sample ≤50 ASINs from the pool (a 50-ASIN sample already spans the category's keyword
universe), `metrics:["id","name","search_volume","quarterly_trend","monthly_trend","relevancy_score","ease_to_rank"]`,
`ordering:"-quarterly_trend"`, `min_search_volume` = the volume floor, `min_relevancy_score` = the
relevance floor.

---

## get_keyword_sov

Brand-level share of voice for specific search terms — "who owns this keyword."

- **filters:** `keywords` (list of **search-term text**, ≥1 required), `country_code` (UPPER),
  `featured_brand` (optional — when set, returns that brand's series with period-over-period change),
  `brands` (optional — restrict the competitive set; shares measured within it).
- **options:** `aggregation` (`"week"|"month"`), `metrics` (default `"equal_weighted_organic"`; also
  `equal_weighted_overall|equal_weighted_sponsored|position_weighted_*`), `top_brands` (default 10,
  set null for all), `include_others`, `search_time_min`/`search_time_max` (default last ~90 days),
  `limit`, `offset`, `currency`.
- **Response:** `{ rows: [...], metrics: {...} }`. Each row is a **brand × time-bucket** record:
  `brand`, `week__week` (or `week__month`), and the SoV metric field(s) e.g. `sov_equal_weighted_organic`
  (0–100). With `featured_brand` set, rows also carry `…__delta` and `…__comparison_period`.
- It is a **time series**, not a single snapshot. For a current "who owns it" read, take the latest
  bucket per brand. There is **no** `is_organization_brand` flag — to mark owned brands, cross-reference
  `list_org_brands`, or pass the owned brand as `featured_brand`.

---

## get_keyword_search_volume_history

Weekly search-volume history for one keyword — drives the 12-month curve and the seasonality check.

- **filters:** `keyword_text` (required), `country_code` (UPPER).
- **options (required — no default object):** `search_time_min`, `search_time_max` (ISO dates),
  `group_by` (default `"keyword__text,keyword__country_code,search_time_week"`),
  `metrics` (default `"estimated_search_volume"`), `ordering` (default `"search_time_week"`),
  `limit`, `offset`.
- **Response:** `rows[]` with `keyword__text`, `keyword__country_code`, `search_time_week`,
  `estimated_search_volume`. Sort by `search_time_week` ascending before charting.
- Use sparingly — one call per keyword. In the report, fetch history only for the handful of top terms
  you deep-dive, not the whole list.
