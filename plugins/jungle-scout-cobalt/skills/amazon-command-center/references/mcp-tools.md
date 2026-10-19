# MCP tool reference — Amazon Command Center

Tool inventory, provenance, and the query limits that shape every fetch in this skill. Read
before the first call.

## Provenance — why this file has two tiers

Not every tool name in this reference carries the same weight of verification, and treating
them as equal is how a run produces a confidently wrong call.

- **Repo-verified** — the tool is named in this repository, and for most of them a
  hand-checked parameter and response reference exists at
  `../../analyze-category-keywords/references/mcp-tools.md` ("Verified against current MCP
  server behavior"). **That file is the authority for anything it covers.** When it and this
  file disagree, it wins.
- **Announcement-sourced** — the tool is named in internal Cobalt release announcements. The
  names are well corroborated, but **parameters, enums, and response fields were not
  verifiable**: no live tool listing was reachable when this skill was written, and the
  repository's verified schema file predates the advertising tools. So: use the names, and
  **discover the schema at call time** from the tool definition. Never assert a parameter
  name for an announcement-sourced tool, and never claim a response field before you have
  seen it in a response.

If a call fails, read the error and inspect the tool definition. Do not retry a guessed
parameter.

---

## Conventions that bite

- **Every repo-verified tool takes `org_id`.** Resolve it with `list_orgs` first if not
  already selected.
- **Marketplace casing differs by tool family.** Sales-estimate tools (`analyze_categories`,
  `analyze_products`) take **lowercase** `marketplace` (e.g. `"us"`); keyword and category
  tools take **UPPERCASE** `country_code` (e.g. `"US"`).
- **Request friendly metric names, read raw response fields.** For the sales-estimate tools
  you ask for `revenue`, `units_sold`, `avg_price`… but returned rows are keyed by underlying
  field names (`revenue_total_sum`, `sales_total_sum`, `weighted_average_selling_price`…).
  Each payload includes a `metrics` block mapping friendly name → field.
- **Deduplicate keyword rows.** Multi-ASIN keyword pulls can return the same keyword more
  than once. Dedupe by lowercased `name` before counting, scoring, or charting.
- **Actuals and estimates are different classes of number.** Connected-account tools return
  actuals; market tools return estimates. Label which is which and never sum across them.

---

## Hard query limits — these change how every fetch is shaped

**31-day maximum window per call, about 14 months of history.** Requests are capped at a
31-day window at a time, with the number of data points per request also limited, to protect
against upstream query timeouts. History reaches back roughly 14 months and no further.

So a 90-day read is **three or more calls**, and a year-over-year read is that again for the
prior period. It is slower than the sales-estimate tools. Plan the call budget before
starting, and prefer the narrowest window that answers the question.

This cap was announced for the Seller Central / Vendor Central tools. **Whether it also
applies to the advertising tools is undetermined** — chunk defensively at 31 days; if a wider
window succeeds, note it and continue.

**Built-in period-over-period comparison was removed.** The connected-account tools no longer
return a comparison; the agent makes two calls and computes the delta itself. Never blend two
windows into one figure, and state both windows explicitly whenever you report a change.

**Some metrics were hidden** on those tools for performance reasons. If an expected metric is
absent from a response, treat it as unavailable rather than substituting an adjacent one.

**Year-over-year accuracy caveat.** Year-ago comparisons align on **exact calendar dates**
rather than comparable **Sunday–Saturday retail weeks**. A customer's agency figures
disagreed with a year-ago read for exactly this reason. Warn about it on every
year-over-year read in a run, and prefer a same-weekday-aligned window when the number will
be compared against an agency or an internal report.

**Access prerequisites.** The advertising tools require a connected Amazon Advertising
account; the actuals and competitive-offer tools require a connected Seller/Vendor Central
account. The competitive-offer tools work **only on ASINs in the user's own catalog**.

**Not connector capabilities at all:** writing any change, running on a schedule, emitting a
file or export, and reading Cobalt product labels. Charts and widgets belong to the host
(see `jungle-scout-visualizer`), not to the connector.

---

# Repo-verified tools

For `search_categories_by_name`, `analyze_categories`, `analyze_products`,
`search_keywords_by_asin`, `search_keywords_by_keyword`, `get_keyword_sov`, and
`get_keyword_search_volume_history`, the full verified parameter and response reference is
`../../analyze-category-keywords/references/mcp-tools.md`. Summarized below only as far as
this skill uses them — **read that file for exact shapes**.

## list_orgs

Organization selection. Call first when the org is not already chosen; if the user belongs to
more than one, have them pick. Every repo-verified tool takes the resulting `org_id`.

## list_org_brands

The org's owned/managed brands. Use it to validate the brand input, and to mark which brands
in a competitive set are the user's own — `get_keyword_sov` has **no** `is_organization_brand`
flag, so cross-reference here or pass the owned brand as `featured_brand`.

## search_categories_by_name

Resolve a category name to Amazon browse nodes.

- **Input:** `org_id`, `country_code` (UPPER), `name`.
- **Response:** `categories[]`, each with `id`, `name`, `parent_id`, `path_by_id`,
  `path_by_name`, `subcategory_count`, `active`, `is_permitted`.
- Keep only `active && is_permitted`. Show `path_by_name` for disambiguation; if several
  plausibly match, ask the user which.

## get_categories_by_ids

Category resolution by ID. Parameters are not documented in this repository — inspect the
tool definition before calling.

## analyze_categories

Category totals and growth, for the market-position section.

- **filters:** `category_ids` (expands to the subtree), `marketplace` (lower).
- **options:** `metrics` / `extra_metrics` (friendly names), `comparison`
  (`"none"|"prior_period"|"year_ago"`), `aggregate` (true → single combined row), `limit`,
  `period`.
- **Friendly metrics used here:** `revenue`, `revenue_growth`, `units_sold`,
  `units_sold_growth`, `avg_price`, `product_count`, `brand_count`.
- Use `aggregate:true` for a single scope row — never sum rows yourself.
- When using `comparison:"year_ago"`, apply the year-over-year caveat above.

## analyze_brands

Brand and competitor performance within a category scope. Metrics used here: `revenue`,
`revenue_growth`, `market_share`, `market_share_growth`, `units_sold`, `units_sold_growth`,
`avg_price`, `avg_price_growth`, `product_count`. Sort by `revenue` or `market_share`, and
include enough rows that the user's brand appears even when it falls outside the top 10.

## analyze_products

ASIN-level estimates — the fallback when actuals are unavailable, the source for new-launch
detection, and the tool behind the outside-the-watch-list decline scan.

- **filters:** `category_ids`, `marketplace` (lower), `launched_after` (YYYY-MM-DD),
  `launched_before`, `asins`, `brands`.
- **options:** `sort_by` (friendly metric), `sort_direction` (`"asc"|"desc"`),
  `extra_metrics`, `thresholds` (`[{metric, min_value, max_value}]`), `detail_level`
  (`"summary"|"standard"|"verbose"`), `comparison`, `limit`, `offset`.
- **detail_level fields:** `summary` → `asin`, `title_stable`, `brand_stable`;
  `standard`/`verbose` add `image_url_hero`, `breadcrumb_leaf_node_id_stable`,
  `breadcrumb_leaf_node_name_stable`, `first_date_available`, plus requested metric fields.
- Use `asins` to scope to the priority ASIN list; `launched_after` for new titles;
  `group_by: launch_cohort` to split a brand's revenue into new versus existing SKUs.
- Everything this tool returns is a **market estimate**, not an account actual. Label it.

## analyze_price_tiers

Price-band position for a category and brand. The repository documents passing a category ID,
brand, date range, currency, and `comparison="year_ago"`; other parameters are not documented
here. Category IDs expand to the permitted subtree, so root, branch, or leaf scope all work —
don't hand-pick leaves unless the tool fails or the user asks for leaf-level comparison.

## analyze_attributes

Product attribute breakdown. Category IDs expand to the full subtree. Parameters are not
documented in this repository — inspect the tool definition before calling.

## describe_sales_estimates_schema → query_sales_estimates

The escape hatch for shapes the typed tools cannot express. **Always call
`describe_sales_estimates_schema` first** and use only fields it reports — this is also the
correct way to check whether a field the user asked for exists at all, instead of guessing.
Known use from elsewhere in this repository: `variant_review_count_sum` trended weekly.

## query_org_performance

The org's own managed-brand performance. Documented here: scope it to the brand and category,
with `group_by="none"` for totals, `group_by="trend"` for the trend series, and
`group_by="brand"` for a per-brand split. **No metric list is documented in this
repository** — request what the tool exposes and read the response; do not assume a
particular metric (including any advertising metric) is present until you see it.

If owned-org data is unavailable, continue with market-estimate tools and disclose that
owned-account performance was not available.

## search_keywords_by_asin / search_keywords_by_keyword

Keyword candidates for new-title routing and Experimental-campaign research. Each row carries
inline 30-day and 90-day trend, so momentum needs **no** per-keyword history call.

- **Common filters:** `country_code` (UPPER), `min_search_volume`, `min_relevancy_score`,
  plus `*_gte`/`*_lte` range filters. `search_keywords_by_asin` adds `asins` /
  `product__id__in`; `search_keywords_by_keyword` adds `keyword` / `keywords` /
  `keyword__id__in`.
- **options:** `metrics`, `ordering` (e.g. `"-quarterly_trend"`), `order_by`,
  `sort_direction`, `limit` (≤1000), `offset`, date window.
- **Valid metrics:** `id`, `name`, `search_volume`, `quarterly_trend`, `monthly_trend`,
  `relevancy_score`, `relative_value_score`, `ease_to_rank`.
- Friendly `search_volume` maps to response field **`estimated_exact_search_volume`**;
  `quarterly_trend` = 90-day trend %, `monthly_trend` = 30-day trend %.
- **Not available:** `top_asins` and `category` are **not** supported keyword metrics — do
  not request them.
- Dedupe by lowercased `name` across multi-ASIN pulls.

`relevancy_score`, `relative_value_score`, and `ease_to_rank` live **here**, not in the
advertising tools. Joining them to advertising data is a join by keyword text — say so when
you present it.

## get_keyword_sov

Brand-level share of voice — organic and sponsored. The only advertising-adjacent signal
available without a connected Advertising account, and the substitute for the absent
ASIN/conquest targeting data.

- **filters:** `keywords` (search-term text, ≥1 required), `country_code` (UPPER),
  `featured_brand` (optional — returns that brand's series with period-over-period change),
  `brands` (optional — restrict the competitive set).
- **options:** `aggregation` (`"week"|"month"`), `metrics` (default
  `"equal_weighted_organic"`; also `equal_weighted_overall`, `equal_weighted_sponsored`,
  `position_weighted_*`), `top_brands` (default 10, null for all), `include_others`,
  `search_time_min`/`search_time_max` (default last ~90 days), `limit`, `offset`, `currency`.
- **Response:** `{ rows, metrics }`; each row is a **brand × time-bucket** record — `brand`,
  `week__week` (or `week__month`), and the SoV field(s) e.g. `sov_equal_weighted_organic`
  (0–100). With `featured_brand`, rows also carry `…__delta` and `…__comparison_period`.
- It is a **time series, not a snapshot**. For a current read, take the latest bucket per
  brand.
- Sponsored SoV is a **placement-share** signal. It is not spend, not ACoS, and not a bid.
  Never present it as an advertising cost or efficiency metric.

## get_keyword_historical_sov

Use **only** when daily or fold-weighted SoV is specifically needed. Parameters are not
documented in this repository — inspect the tool definition before calling.

## get_keyword_search_volume_history

Weekly search-volume history for **one keyword per call**.

- **filters:** `keyword_text` (required), `country_code` (UPPER).
- **options (required — no default object):** `search_time_min`, `search_time_max` (ISO
  dates), `group_by` (default `"keyword__text,keyword__country_code,search_time_week"`),
  `metrics` (default `"estimated_search_volume"`), `ordering` (default
  `"search_time_week"`), `limit`, `offset`.
- **Response:** `rows[]` with `keyword__text`, `keyword__country_code`, `search_time_week`,
  `estimated_search_volume`. Sort ascending by `search_time_week` before charting.
- Use sparingly — only for the handful of terms you feature, never the whole list.

---

# Announcement-sourced tools

Names are corroborated by internal release announcements. **Parameters and response fields
are not verified — discover them at call time.** Everything below describes what the
announcements say the tool answers, which is a guide to *whether to reach for it*, not a
schema.

## query_ad_performance

The core advertising tool. Reports **spend, ad sales, ACoS/ROAS, CPC, CTR, and budget
pacing**, at **campaign, ad group, advertised-product, or whole-account** level, trendable by
day / week / month. ACoS, TACoS, and CPU **goals are joined in automatically**, so it can
show which ads miss their target — prefer those joined goals over a threshold the user
guesses at, when the account has them set.

Questions it answers: which campaigns are burning budget; how ACoS moved week over week;
which campaigns pace at roughly 100% of budget; account-level spend.

Known boundaries:
- **Campaign state (enabled / paused / archived) is not confirmed readable.** No status field
  appears in any documentation. Do not infer state from the presence or absence of spend.
- **Campaign type is not confirmed readable** as a field either. Bucket by the user's naming
  convention.
- The **advertised-product-to-title mapping shape is unconfirmed**. Check the response before
  promising ASIN-level ad attribution.
- **Hourly / dayparting granularity is absent.** Day is the finest grain to report.
- **Keyword relevancy / value score is absent here** — join it from the keyword tools.
- **ASIN / conquest targeting is absent.**
- **Portfolio-level** questions (spend, sales, ACoS, orders by portfolio; which portfolios sit
  closest to their budget cap; same-SKU ROAS) and **Amazon DSP** reporting (spend, sales,
  ROAS by advertiser, order, line item, creative; delivery status; site, placement, supply
  source; audience segment cost-per-order) are both available on the advertising surface, but
  **no distinct tool name is documented for either**. They are most likely levels or filters
  here. Discover them from the live tool list; do not guess a tool name.

## query_ad_targeting

Target-level detail: **keyword targets with bid and match type**, the **shopper search terms**
that triggered ads, and **cost per search term** next to the keyword it rolled up under.
Carries a **"spent money, converted nothing"** filter — that filter is the fastest path to
the prune list, so reach for it directly rather than reconstructing it from raw rows.

This is where prune-versus-scale and bid-change decisions are made. It reports current bids;
it cannot change them.

## query_seller_central_performance

3P (Seller Central) actuals at **daily grain**: sales and traffic, **sessions**, products with
**sessions but zero sales**, **Buy Box win rate** per product, **organic versus
ad-attributed** revenue split and **TACoS**, and a B2B versus consumer split. Groups by
product / brand / marketplace, trends by day / week / month, and supports threshold screening.

The sessions-with-zero-sales cut is the sharp form of the inactivity-risk question on 3P.
Subject to the 31-day cap and the removed period comparison.

## query_vendor_central_performance

1P (Vendor Central) actuals at **daily grain**: sales actuals with a manufacturing-versus-
sourcing view, **net PPM**, **glance views**, and returns. Same grouping, trending, and
threshold screening as above.

Glance views and net PPM are the playbook's 1P catalog-health signals. They indicate
suppression or inactivity **risk** — never a confirmed status. Subject to the 31-day cap and
the removed period comparison.

## query_vendor_central_inventory

1P inventory and supply chain at **daily grain**: **aged (90+ day) inventory**, chronically
**out-of-stock** products, **open PO quantities and fill rate**, and ASINs with **nothing
sellable on hand**. Same grouping, trending, and threshold screening.

This is the evidence base for inventory-driven pause candidates, and for re-enable candidates
once stock recovers.

## analyze_competitive_offers

Per-ASIN offer detail: **who is winning the buy box and at what price**, new or
**unauthorized sellers**, feedback scores, FBA/FBM split, and period-over-period share
changes. The right confirmation step for the revenue-down-but-traffic-flat pattern.

Requires a connected Seller/Vendor Central account and works **only on ASINs in the user's own
catalog**. It will **not** tell you whether a price breaks MAP — report the offer facts and do
not infer a policy breach.

## analyze_seller_product_offers

Seller drill-down across a shortlist of the user's own ASINs. Same account requirement and
same own-catalog-only limit.

---

## Host rendering tools (not the connector)

`visualize:show_widget` renders HTML + Chart.js widgets, and `read_me` with
`modules=["chart"]` loads the chart module once at the start of a run. These belong to the
**host**, not to Jungle Scout — inside Cobalt AI Chat they are unavailable, so the polished
callout-and-chart pattern does not transfer there. See `jungle-scout-visualizer` and its
`references/visuals.md` for the palette and templates.
