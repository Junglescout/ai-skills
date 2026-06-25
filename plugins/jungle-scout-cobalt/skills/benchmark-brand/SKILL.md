---
name: benchmark-brand
description:
  Use this skill whenever the user asks to benchmark a brand, compare a brand
  against a category, assess brand performance versus competitors, analyze price
  tier positioning, evaluate Amazon search share-of-voice, or create a brand
  benchmarking report using the Jungle Scout Cobalt connector/MCP server.
  Trigger for prompts such as brand benchmark, benchmark this brand, compare my
  brand to the market, brand vs category, competitive landscape, price band
  opportunities, or Amazon search visibility for a brand. Produces a static,
  data-backed report; presentation styling is deferred to the
  jungle-scout-visualizer skill, which this skill depends on.
---

# Brand Benchmark

Use the Jungle Scout Cobalt connector/MCP server tools to produce a brand
benchmarking report. This skill is platform-neutral: call the available
connector tools directly and synthesize the report in the conversation or
requested artifact.

## Inputs to Resolve

Confirm the inputs with the user before running — don't guess at the brand or
category. If the environment supports a structured input form or a multiple-choice
prompt, **present one** that captures the fields below (required fields first,
optional fields pre-filled with the defaults shown). Otherwise ask a short, **batched**
set of questions in one message — not one at a time. Skip the questions only when the
user already supplied the required values in their request.

**Required**

- **Brand** — the benchmark brand, exactly as the user states it. Validate with
  `analyze_brands` or `list_org_brands` when needed.
- **Category scope** — root, branch, or leaf. If given a name, resolve with
  `search_categories_by_name`; if several plausibly match, have the user pick.

**Optional (offer with defaults)**

- **Organization** — call `list_orgs`; if the user belongs to more than one, have them
  pick.
- **Marketplace** — default `us` for market-analysis tools, `US` for org/keyword tools.
- **Date range** — default the latest trailing 12 months available to the tool.
- **Currency** — infer from marketplace when obvious; otherwise `USD`.

## Jungle Scout Cobalt Connector Tool Map

Use typed Jungle Scout Cobalt connector/MCP server tools first. Use
`query_sales_estimates` only for shapes the typed tools cannot express.

| Workflow need                                | MCP tools                                                                                                       |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Org selection                                | `list_orgs`                                                                                                     |
| Category resolution                          | `search_categories_by_name`, `get_categories_by_ids`                                                            |
| Category performance                         | `analyze_categories` with `aggregate=true` for total scope metrics                                              |
| Brand performance                            | `analyze_brands`, plus `query_org_performance` when owned-brand metrics are needed                              |
| Monthly owned trend                          | `query_org_performance` with `group_by="trend"`                                                                 |
| Competitors                                  | `analyze_brands` sorted by revenue or market share                                                              |
| Revenue vs ASP and custom competitor metrics | `query_sales_estimates` after `describe_sales_estimates_schema`                                                 |
| Owned brands                                 | `list_org_brands`, `query_org_performance` with `group_by="brand"`                                              |
| Price positioning                            | `analyze_price_tiers`                                                                                           |
| Top products for keyword research            | `analyze_products`                                                                                              |
| Keyword candidates                           | `search_keywords_by_asin` or `search_keywords_by_keyword`                                                       |
| Share of voice                               | `get_keyword_sov`; use `get_keyword_historical_sov` only when daily or fold-weighted SoV is specifically needed |

## Category Scope Rules

Do not require a leaf category.

- For `analyze_categories`, `analyze_brands`, `analyze_products`,
  `analyze_attributes`, and `query_sales_estimates`, category IDs expand to the
  full subtree.
- For `analyze_price_tiers`, use the tool directly for root, branch, or leaf
  category scopes. The Jungle Scout Cobalt connector/MCP server expands category
  IDs to the permitted subtree before computing price bins.
- Do not manually pick top leaf categories for price-tier analysis unless
  `analyze_price_tiers` fails, the user asks for leaf-level comparisons, or the
  report needs separate leaf-category price tiers.
- When a report uses a broad category scope, label findings as scoped to the
  expanded category tree.

## Data Fetch Sequence

Fetch independent data in parallel when possible.

1. Resolve org, marketplace, brand, category, date range, and currency.
2. Fetch category totals with `analyze_categories` using `aggregate=true`,
   metrics `revenue`, `revenue_growth`, `units_sold`, `units_sold_growth`,
   `avg_price`, `avg_price_growth`, `product_count`, and `brand_count`, with
   `comparison="year_ago"` for a seasonality-matched benchmark.
3. Fetch benchmark brand totals with `analyze_brands` scoped to the category,
   including `revenue`, `revenue_growth`, `market_share`, `market_share_growth`,
   `units_sold`, `units_sold_growth`, `avg_price`, `avg_price_growth`, and
   `product_count`.
4. If the brand is owned by the org or the user asks for owned performance,
   fetch `query_org_performance` for the brand and category with
   `group_by="none"`, then fetch `group_by="trend"` for the same scope.
5. Fetch top competitor brands with `analyze_brands` scoped to the same
   category, sorted by `revenue` or `market_share`; include enough rows to show
   the benchmarked brand even if it is outside the top 10.
6. Fetch price bands with `analyze_price_tiers`, passing the same category ID,
   brand, date range, currency, and `comparison="year_ago"` unless the user asks
   otherwise.
7. For search insights, fetch top products in scope with `analyze_products`,
   research keywords with `search_keywords_by_asin`, then fetch
   `get_keyword_sov` for the strongest keyword set. Keep the keyword set focused
   enough that SoV remains interpretable.

## Analysis Rules

Use only retrieved data. Do not infer strategy, consumer intent, channel
dynamics, promotions, algorithm effects, brand equity, or margin unless those
metrics are explicitly present.

- Brand share equals brand revenue divided by category revenue. If share
  changed, explain whether brand revenue outpaced the category or lagged it.
- Revenue equals units multiplied by ASP. If revenue and units move in different
  directions, identify whether volume or ASP explains the movement.
- Treat brand growth below category growth as a competitive weakness, even when
  the brand grew in absolute terms.
- For competitors, prioritize current market share, share movement, revenue
  scale, and ASP. Do not overstate tiny brands because of extreme percentage
  growth.
- For price bands, distinguish category tier growth from brand tier growth. Do
  not attribute category-level growth to the benchmarked brand.
- For search insights, compare brands within the same keyword tier. Do not frame
  lower long-tail SoV versus head SoV as erosion because tier weighting
  naturally differs.
- State when data is insufficient. Use: "Available data does not indicate the
  underlying cause."

## Presentation

This skill owns the report's **structure** — which sections appear and in what
order, and what each contains. It does **not** define visual styling. Defer all
styling — the headline callout, palette, charts, growth pills, KPI cards, and
evidence-table formatting — to the `jungle-scout-visualizer` skill.

Produce a **static report** with the data already pulled and baked in: a single
self-contained HTML artifact when the environment supports it, otherwise a clean
markdown report using the same section order (see Markdown Fallback Structure).

Section structure (content defined here; visuals styled by
`jungle-scout-visualizer`):

1. **Report header**: report title, period, marketplace, and category scope.
2. **Executive Summary**: sharp headline, one hero share figure (brand vs
   category), and exactly 3 summary takeaways synthesizing the report.
3. **Brand Performance**: headline, exactly 2 takeaways, a brand revenue or
   share trend, and KPIs for brand share, category revenue, brand revenue,
   units, and ASP.
4. **Competitive Landscape**: headline, exactly 2 takeaways, a market-share
   ranking across competitors, and a revenue-growth-vs-ASP comparison.
5. **Price Positioning**: one overview sentence, opportunity/risk/strength
   callouts, a price-band revenue distribution, and brand share by price tier.
6. **Search Insights**: headline, exactly 2 takeaways, KPIs for brand SOV,
   keyword coverage, and top competitor SOV, followed by tier-level SOV and a
   keyword opportunity table.
7. **Data Coverage**: compact notes on source tools, category scope, date range,
   missing data, and estimation caveats.

If a section's data is missing, say so plainly rather than inventing values —
honesty about the gap beats a tidy-but-wrong widget.

## Markdown Fallback Structure

When HTML/artifacts are unavailable, produce this text structure.

Produce this structure unless the user requests a different format.

```markdown
# [Brand] Benchmark Report

## Executive Summary

[Exactly 3 concise, brand-centric takeaways synthesizing multiple sections.]

## Brand Performance

[Exactly 2 takeaways comparing brand revenue, units, ASP, and share against
category metrics.]

## Competitive Landscape

[Exactly 2 takeaways naming specific competitors and tying market share, revenue
growth, and ASP together.]

## Price Positioning

[Price-band overview plus specific opportunity, risk, or strength tiers.]

## Search Insights

[Exactly 2 takeaways covering aggregate SOV/coverage and one tier-level
competitive dynamic.]

## Data Coverage

[Brief notes on category scope, date range, marketplace, and any missing data.]
```

## Writing Style

- Lead with implications, then cite metrics.
- Use concise business language without dramatic phrasing.
- Use specific numbers when available.
- Name the benchmark brand throughout; avoid generic category commentary.
- Do not recommend actions in Brand Performance or Competitive Landscape unless
  the user explicitly asks for recommendations.
- Price Positioning may include proportional actions tied directly to tier
  evidence, such as price-band coverage, assortment presence, portfolio mix, SKU
  placement, or controlled testing.

## Fallbacks

- If owned org data is unavailable, continue with market-estimate tools and
  disclose that owned-account performance was not available.
- If price-tier data is empty, include a short Price Positioning section stating
  that pricing data was insufficient for tier analysis.
- If keyword/SOV data is sparse, include Search Insights only with clear
  coverage caveats, or omit it if the user requested a shorter report.
- If a tool errors because the requested category scope is too broad, narrow to
  the largest relevant leaf categories only after explaining the scope tradeoff.

## Next Steps

After delivering the report, don't just stop. Propose **2–3 concrete follow-ups
grounded in what the report actually showed**, and ask the user which to pursue. If
the environment supports a multiple-choice prompt or form, present the options that
way; otherwise list them and ask. Draw from:

- **Competitor deep-dive** — take the competitor gaining the most share and analyze its
  share trajectory, ASP, revenue scale, and products.
- **Price-band opportunity** — drill into a specific tier flagged in Price Positioning
  (a coverage gap, a share weakness, or a fast-growing band).
- **Search visibility** — expand share-of-voice into the keyword tier where the brand is
  most under-indexed, or surface the fastest-emerging keywords in the category to find
  where new demand is forming.
- **Widen the lens** — benchmark the same brand in an adjacent category or another
  marketplace.

Make each offer specific to the finding (e.g. "deep-dive Competitor X — up ~6 pts of
share this year"), not generic. Then carry out whichever the user picks.
