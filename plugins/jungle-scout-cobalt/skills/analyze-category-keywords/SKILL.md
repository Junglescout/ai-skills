---
name: analyze-category-keywords
description:
  Use this skill whenever the user wants to discover emerging, trending, breakout, or
  fastest-growing search keywords in an Amazon category — rising search demand, new
  keyword opportunities, keyword discovery for product ideas, or "what search terms are
  taking off in a category". Triggers on prompts such as emerging keywords, trending
  keywords, breakout search terms, fastest-growing keywords, what's rising in a category,
  keyword opportunities, or new product-idea keywords, using the Jungle Scout Cobalt
  connector/MCP server. Produces a static, data-backed report; presentation styling is
  deferred to the jungle-scout-visualizer skill.
---

# Analyze Category Keywords

Surface the search terms accelerating fastest inside an Amazon category — the non-obvious,
genuinely new keywords worth building or optimizing a product around. The method: seed from a
chosen set of category products, pull keywords that carry inline 30-day and 90-day trend, flag
each as still-climbing vs. peaked from the two windows alone, score them so meaningful risers
lead, cluster them into themes, and (for the strongest terms) reveal who's winning them and how
the demand has moved over a year.

This skill **owns the report's structure** (which sections appear and in what order) and the
**analysis methodology**. It does **not** define visual styling: defer all palette, callouts,
charts, and tables to the `jungle-scout-visualizer` skill. The output is a **static baked report** —
Claude pulls every figure via the MCP and renders it; there is no live/interactive data bridge.

Exact tool parameters and response fields live in `references/mcp-tools.md`. Read it before
issuing calls.

## Inputs to resolve

Confirm the inputs with the user before running — don't guess at the category. If the
environment supports a structured input form or a multiple-choice prompt, **present one**: the
category is the one required field, the rest pre-filled with the defaults below. Make the **source
lens** prominent — it's the highest-leverage choice. Otherwise ask a short, **batched** set of
questions in one message, not one at a time. Skip the questions only when the user already gave you
the category and is fine with defaults.

**Required**

- **Category:** resolve a name with `search_categories_by_name`; keep only `active && is_permitted`
  results, and if several plausibly match, have the user pick. Category IDs expand to the subtree.

**Optional (offer with defaults)**

- **Source lens:** the discovery lever (see below); default **Up-and-Comers**.
- **Organization:** call `list_orgs`; if the user belongs to more than one, have them pick.
- **Marketplace:** default `us`. Note casing — sales-estimate tools take lowercase `marketplace`,
  keyword/category tools take UPPERCASE `country_code`.
- **Volume floor:** minimum estimated monthly searches. Default **2,000**; raise to cut long-tail noise.
- **Relevance floor:** how tightly a keyword must relate to the category. Default a balanced
  `min_relevancy_score` of ~15; 0 = loose, ~35 = strict.
- **Phrases only:** default on — keep multi-word phrases (≥2 words, ≥5 chars), drop single fragments.

## Source lens — the discovery lever

Which products seed the keyword search determines what you find. Pick one (default Up-and-Comers):

- **Up-and-Comers** — the category's fastest-growing products plus launches in the last ~18 months.
  Where new demand shows up first; the discovery default.
- **Market Leaders** — the category's revenue leaders (the incumbents).
- **Everything** — leaders and up-and-comers combined.
- **Widest Net** — Up-and-Comers plus a category-wide keyword search, not limited to sampled products.

Each lens maps to specific `analyze_products` calls (and, for Widest Net, an extra
`search_keywords_by_keyword` seed). See `references/mcp-tools.md` → *analyze_products*.

## Data fetch sequence

Fire independent calls in parallel where possible.

1. **Resolve** org, marketplace, category, floors, and lens.
2. **Category overview** — `analyze_categories` (single aggregated row) requesting friendly metrics
   `revenue`, `revenue_growth`, `units_sold`, `avg_price`, `product_count`, `brand_count`. Feeds the
   KPI block.
3. **Build the ASIN pool** — `analyze_products` per the chosen lens, `detail_level:"summary"`. Merge
   pools round-robin, dedupe by `asin`, cap ~150.
4. **Pull keywords** — `search_keywords_by_asin` over a ≤50-ASIN sample of the pool (a sample that size
   already spans the category's keyword universe), with
   `metrics:["id","name","search_volume","quarterly_trend","monthly_trend","relevancy_score","ease_to_rank"]`,
   `ordering:"-quarterly_trend"`, and the volume/relevance floors. For **Widest Net**, also call
   `search_keywords_by_keyword` on a seed derived from the category name and merge the results.
5. **Deep-dive the top terms only** (optional, the handful you'll feature): `get_keyword_sov` for
   who-owns-it, `get_keyword_search_volume_history` for the 12-month curve and seasonality. Do **not**
   fetch history for every keyword.

## Momentum, scoring, and seasonality

Each keyword row carries `quarterly_trend` (90-day, call it `q`) and `monthly_trend` (30-day, `m`).
Classify momentum from the two windows — comparing them tells you whether a riser is still
accelerating or already rolling over, with no history calls:

- **✨ Breakout** — `q ≥ 150%` and `m` not negative. Exploding from a low base, still rising. The
  freshest, most winnable demand.
- **🔥 Exploding** — `q ≥ 50%` (and `m ≥ -8%`).
- **📈 Rising** — `q ≥ 15%`.
- **⚠️ Peaked** — `q > 20%` but `m ≤ -12%`: grew over the quarter, rolling over in the last 30 days.
- **Plateauing** — everything else.

**Emergence score** ranks the list so meaningful risers lead instead of tiny spikes:
`emergence = log-damped(growth) × log-damped(volume) × relevance`. Default the report's primary sort to
emergence; offer growth or volume as alternates.

**Seasonality** (only when you've pulled a term's 12-month history): if demand is high now **and** was
high ~a year ago with a dip in between, flag it 📅 Seasonal — likely recurring demand rather than
brand-new. Otherwise treat sustained acceleration as genuinely emerging.

## Cleaning

- **Deduplicate** keyword rows by lowercased `name` before scoring or counting — multi-ASIN pulls
  repeat keywords.
- Apply the **phrases-only** filter and the **volume/relevance** floors.
- If nothing survives, say so and suggest loosening: lower the volume floor, relax relevance, or turn
  off phrases-only.

## Themes

Cluster the top ~40 keywords into **3–6 named themes** a brand should watch for product ideas, each with
a one-line "why it matters" and its member keywords (every keyword in a theme must come from the list).
Add an overall **emerging temperature** — HOT / WARMING / STABLE — and a single punchy headline naming
the biggest emerging shift, with a number.

## Report structure

This skill defines the sections and their order. Hand all styling — the headline callout, charts,
evidence-table formatting, palette, growth pills — to `jungle-scout-visualizer`. Render a static report
(a self-contained HTML artifact if the environment supports it, otherwise clean markdown) with the data
already pulled and baked in.

1. **Verdict / headline** — the emerging temperature and the single biggest shift (the theme headline),
   plus the top riser named with its 90-day growth.
2. **Category overview** — KPI block: category revenue (+ YoY), units, ASINs, brands, ASP.
3. **Emerging themes** — the 3–6 clusters with their one-line insight and keyword tags.
4. **Top emerging keywords** — the ranked evidence table: keyword, momentum badge, 90-day, 30-day,
   monthly volume, ease-to-rank, emergence score. Sorted by emergence (offer growth/volume re-sorts).
5. **Keyword deep-dive** (optional, top terms only) — for each featured term: who owns it (SoV by brand),
   the 12-month search-volume trend, related niche keywords, and any seasonality flag.
6. **Data coverage** — category scope, marketplace, source lens, date window, and any data gaps.

## Analysis rules and guardrails

- Use only retrieved data. Don't infer strategy, intent, promotions, or margins that aren't in the data.
- Don't fabricate to fill a section. If a pull is empty or a figure is missing, say so plainly rather
  than inventing a bar or a number.
- Don't overstate tiny, spiky terms — that's exactly what the emergence score guards against; let it lead.
- Distinguish still-climbing from rolled-over: a high 90-day number with a negative 30-day is Peaked, not
  emerging. Frame it that way.
- Treat estimates as estimates; the top-products revenue figure is a proxy for a term's commercial size,
  not a keyword-attributed revenue.
- State when data is insufficient: "Available data does not indicate the underlying cause."

## Next steps

After delivering the report, don't just stop. Propose **2–3 concrete follow-ups grounded in the
findings**, and ask the user which to pursue. If the environment supports a multiple-choice prompt or
form, present the options that way; otherwise list them and ask. Draw from:

- **Keyword deep-dive** — take a specific breakout term and pull who's winning it (share of voice),
  its 12-month trend, related niche keywords, and the products ranking for it.
- **Widen or narrow the scan** — re-run with a broader source lens (Widest Net) or a lower volume
  floor to surface more candidates, or tighten relevance to cut noise.
- **Brand angle** — benchmark a brand competing in this category, or check a focal brand's share of
  voice on the top emerging terms.
- **Shortlist & export** — pick the most winnable terms (high momentum, high ease-to-rank) and pull
  them into a focused shortlist for a roadmap.

Make each offer specific to the finding (e.g. "deep-dive the top breakout term — +320% / 90d, ease
72"), not generic. Then carry out whichever the user picks.

## Reference files

- `references/mcp-tools.md` — exact parameters, enums, casing rules, and **response field names** for
  every tool this skill calls, with the gotchas (friendly-request vs. raw-response fields, the SoV
  response shape, unsupported keyword metrics). Read before the first call.
