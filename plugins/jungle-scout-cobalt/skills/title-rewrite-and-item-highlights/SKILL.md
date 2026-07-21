---
name: title-rewrite-and-item-highlights
description: "Bulk-rewrite a brand's Amazon product titles to meet Amazon's 75-character title requirement (in force since July 27, 2026) using verified keyword gap analysis against the Jungle Scout Cobalt connector/MCP server. Use this skill whenever the user mentions the 75-character title rule, title compliance, bulk title rewrites, 'Amazon is rewriting our titles', 'Amazon rewrote our titles', a Review Listing Changes alert, title audits, revenue at risk from title changes, or wants keyword-optimized titles for a brand's catalog — even if they don't say '75 characters' explicitly. Also trigger when a customer asks how exposed their catalog is to Amazon's AI title rewrites, wants to replace Amazon's AI-suggested titles with their own, or wants a CSV of new titles for bulk upload."
---

# Title Rewrite and Item Highlights

Rewrite every over-limit title in a brand's Amazon catalog to ≤75 characters, packing in the most valuable *verified* keywords, and produce a bulk-upload-ready CSV plus an evidence trail that defends every keyword choice.

Why this exists: since July 27, 2026, any title over 75 characters is gradually replaced by Amazon's own AI recommendation — brand owners get a rolling 14-day review window per listing as Amazon works through catalogs. A brand that does nothing hands its titles to Amazon; a brand that already got rewritten is living with Amazon's generic choice. This skill produces better titles than Amazon's rewrite — before the rewrite lands or as a replacement for one — with data behind every word.

Exact tool parameters, response shapes, and the gotchas (grain behavior, marketplace casing, what can and cannot be batched) live in `references/mcp-tools.md`. **Read it before issuing the first call.**

## Environment

This skill is platform-neutral: it calls the connector tools directly and runs its bundled scripts in whatever code-execution environment is available. Two things shape how it operates, and both are handled below:

- **Data comes from the Jungle Scout Cobalt connector/MCP server.** Every data tool this skill uses (`list_orgs`, `analyze_products`, `analyze_brands`, `search_keywords_by_asin`, `search_keywords_by_keyword`, `get_keyword_sov`, `get_keyword_search_volume_history`) is provided by the connector. Call these tools directly; the bundled scripts never make network calls — they only do set math on the JSON written to the sandbox. Every tool takes `org_id`; sales-estimate tools take lowercase `marketplace`, keyword tools take UPPERCASE `country_code` (see the reference).
- **Files live in the code-execution sandbox.** Scripts (`scripts/pool_tools.py`, `scripts/lint_titles.py`) and assets (`assets/title-rules.json`) run as-is in the sandbox. Intermediate pools are written to the sandbox working directory; final outputs are delivered to the user as downloadable files, not saved to a mounted folder.

## Scope and routing

This skill owns title rewriting and item-highlights authoring. It is not a general keyword-research skill: keyword discovery or emerging-keyword questions without title-rewrite intent route to `analyze-category-keywords`, and share/competitive-position questions route to `share-diagnosis`. If the user wants the census or evidence summary presented as a styled report, hand presentation to `jungle-scout-visualizer`; the CSV outputs of this skill are deliverables in their own right and need no styling pass.

### Stage 0 — Setup (interactive)

**Connector check first.** Call `list_orgs`. If it fails or returns nothing, stop and tell the user to connect the Jungle Scout Cobalt connector/MCP server, then retry — do not attempt to proceed without it. If it succeeds, resolve `org_id` from the result; if the user belongs to more than one organization, have them pick.

Then confirm the inputs before running — batched in one message, or via a structured form / multiple-choice prompt if the environment supports one. Skip questions the user already answered in their request.

**Required**

- **Brand** — exactly as the user states it; validate against `analyze_brands` if unsure.
- **Voice rules** — keep model codes in titles? abbreviations like RHT acceptable? policy on gendered terms ("for boys")? These become generation constraints. Ask now, not after generating 500 titles.

**Fixed**

- **Marketplace: US only.** Localized keywords (`guantes de beisbol`) go to flags, not titles. If the user needs another marketplace, say so upfront and stop rather than producing unverifiable output.

**Attribute availability — ask upfront, not at generation time.** Licensing an attribute is the binding constraint on every high-value keyword: a keyword you can't substantiate can't go in the title. So resolve this before any generation. During census (Stage 1) capture, per variant family, the variant attributes (color, lens, size) and substantiable specs (UV400, frame shape, material, certifications) present in the feed. Where the feed is missing attributes that the category's high-value keywords depend on — identical child titles with no recoverable color/lens data, no UV rating to back "UV400", etc. — list those gaps and ask the user to supply or confirm them now. Do not discover missing attributes when you're already writing titles.

### Stage 1 — Catalog census

Two pulls (see the reference's census recipe):

1. **Child titles — `asin` grain.** `analyze_products` filtered by brand, `product_grain: "asin"`, `detail_level: "summary"`, trailing 12 months, paginate to exhaustion. This is the only grain that returns per-child `title_stable`, and every child title must be linted — variants of one parent can carry different (and differently non-compliant) titles.
2. **Family view — `variant_group` grain.** One `analyze_products` call at `product_grain: "variant_group"` for the family roll-up: family revenue, `top_level_asin`, `is_standalone`, and a hero title per family via `enrichments`. Do not use `parent_asin` grain for this — it returns no titles and silently collapses standalone listings into a null bucket.

Run `scripts/lint_titles.py --census` on the child titles to produce the compliance census: how many titles exceed 75 chars and how much revenue they carry. Report this to the user before proceeding — "$X of trailing-12-month revenue is on titles Amazon will rewrite (or already has)" is the number that motivates everything after. Surface any attribute gaps found here back to Stage 0's question to the user.

Analyze at family grain so one variant-heavy product doesn't eat the analysis (a backpack with 5 colors is one title problem, not five): the family's base title comes from its hero, variants get suffix rules in Stage 7. When you need a specific family's children, filter `asin`-grain by `parent_asins: [<top_level_asin>]`.

### Stage 2 — Keyword universes, per leaf category

Group the brand's ASINs by leaf category (breadcrumbs come from the `asin`-grain census at `standard` detail). For each category:

- **Brand pool:** `search_keywords_by_asin` with ALL the brand's ASINs in that category in one call (it's a batch endpoint — never loop per ASIN). Pull two sorts (`-relative_value_score` and `-estimated_exact_search_volume`), volume floor via `estimated_exact_search_volume_gte: 100` — filter server-side, don't pull and discard. Batch per category, never whole-brand: mixed-category batches pollute RVS rankings.
- **Competitor pool:** derive the competitor set with `analyze_brands` scoped to the category — top 5 by `revenue` plus top 3 by `revenue_growth` (growth catches Amazon-native challengers that revenue-only misses). Pull their ASINs with `analyze_products` using `filters.brands: [<competitors>]` (top by revenue, cap 5 ASINs per competitor brand so one brand can't dominate the pool). Then the same batched keyword pull.

**Set the 12-month window on every keyword pull.** The keyword tools default to a trailing-30-day window; pass `search_time_min`/`search_time_max` spanning the trailing 12 months so the aggregated volume IS trailing-12-month volume. This is what candidates are ranked on later — no per-keyword history calls needed.

**Context-safe pulls (required).** A 1,000-row page with full metadata overflows the inline tool result, and in some environments the overflow file is not reachable from the analysis sandbox — so an exhausted pool you can't read is worthless. Request **minimal metrics only** (`search_volume, relative_value_score, quarterly_trend` — `id` and `name` always come back) and use **moderate pages** (≈200 rows) rather than 1,000-row pages. You do not need to exhaust the pool: top-N-by-volume is provably sufficient for finding the top-K gaps, because a keyword below the cutoff cannot outrank one above it on the metric you're ranking by. Paginate only until the volume floor is reached or two consecutive pages add no candidate above the floor. The one exception is the differentiator audit in Stage 5, which is keyword-first and does not rely on this pool depth.

Write every pool to the sandbox working directory as JSON immediately (`pools/<category>-brand.json`, `pools/<category>-comp.json`). Do not hold pools in context — at full catalog scale they won't fit, and all set math happens in code anyway.

### Stage 3 — Gap candidates (code, not judgment)

Run `scripts/pool_tools.py gap` per category: set difference (competitor − brand), volume floor, and surface-form clustering ("tball bat" / "t ball bat" / "tee ball bat" are one demand cluster — the title gets the highest-volume form, the rest are noted for backend search terms).

**Stratify candidates before verifying — do not just take top-N by raw volume.** Raw top-N is dominated by mega-generic head terms ("sunglasses", "glasses", "beach essentials") that are either trivially already in every title or obvious rejects, which burns SOV-verification budget while mid-tail product-specific gaps (e.g. "rhinestone sunglasses", 5K/mo) fall below the cutoff and never get tested. Split the candidate list into two buckets and verify both: (1) the top head terms, and (2) the top **product-noun-matched mid-tail** terms — candidates whose tokens include the product's actual noun/attributes, surfaced regardless of where they sit on raw volume. The mid-tail bucket is where differentiators live.

**Cluster semantic siblings, not just spelling variants.** `pool_tools.py` collapses spacing/plural variants ("t ball"/"tee ball" — seed these in a synonyms map) but treats synonyms like "bling"/"rhinestone"/"sparkly"/"crystal" as unrelated, so the highest-volume form of a *concept* never surfaces from set math alone. Close this by sibling-testing every differentiator in Stage 5 (below); optionally seed a small per-category synonym map so obvious sibling clusters merge in code.

### Stage 4 — Verification

For each gap candidate, call `get_keyword_sov` — it takes **keyword text** (a list of search terms, matched normalized; there are no keyword IDs to resolve), so batch the candidate terms. Use `aggregation: "month"` over the trailing ~90 days with the default `equal_weighted_organic` metric and `top_brands` 5–10 — weekly grain across many keywords floods context. SoV values come back as fractions (0.38 = 38%). Keep a gap keyword only if both hold:

- **Quantitative:** the client brand's SOV is materially below the keyword's leading brands (or absent). For the client-brand side of this check, `featured_brand` mode returns just their series with period-over-period change.
- **Qualitative (relevance screen):** the brands owning the SERP sell *comparable products*, and the keyword makes no claim this product can't support. This is where you reject "sliding mitt" for a fielding glove and "weighted baseballs" for regular ones — see `references/rejection-examples.md`.

Rank survivors on the trailing-12-month volume already carried by the pools (Stage 2's window — no extra calls). Quarterly trend is seasonal context, not evidence — a +500% trend in June for a baseball keyword is spring, not momentum. Seasonality tagging comes later, in Stage 6, and only for the keywords that actually enter a title.

### Stage 5 — Differentiator audit (keyword-first)

This stage fixes a structural bias: every pool so far is ASIN-anchored, and `search_keywords_by_asin` only returns terms a product *already ranks for*. If you choose a family's differentiator keyword from that pool, you anchor the differentiator slot to where the brand already is — typically a weak, low-volume incumbent term. Generic gaps are unaffected (they come from competitor pools), but the product-specific mid-tail differentiator is exactly what ASIN-anchoring gets wrong. Run this keyword-first instead.

For each family (or each product line sharing a differentiator), take its differentiating attribute and enumerate semantic siblings with `search_keywords_by_keyword` — e.g. "bling" → "rhinestone", "sparkly", "crystal", "diamond". Compare cluster volumes across the siblings, then `get_keyword_sov`-verify the winner (and confirm the brand doesn't already index on it / SOV is fragmented enough to win). Pick the highest-volume *substantiable* sibling, not the one the brand happens to rank for. Budget ≈2–3 extra calls per product line; this is where a 2x-volume differentiator is found (the "bling" → "rhinestone" case: ~10K/mo cluster vs ~6K, and the brand didn't index on it at all). The winner becomes a `verified-gap` target carried into assignment.

### Stage 6 — Per-family assignment (tiered)

- **≤50 families in scope:** one `search_keywords_by_asin` call per family (its children via `filters.parent_asins`) for an exact keyword→product mapping. Mark assignments `confidence: measured`.
- **>50 families:** assign from the category pool by matching keyword meaning against title/attributes. Mark `confidence: inferred`. Tell the user which tier ran.

Each family ends with 2–4 target keywords, each carrying: volume, annualized volume, SOV leader, source (`brand-indexed`, `verified-gap`, or `differentiator` from Stage 5), confidence. For the final keywords only, pull `get_keyword_search_volume_history` (**one call per keyword — it cannot be batched**) over 52 weeks to tag seasonal keywords with their peak months.

### Stage 7 — Generate and lint

Template: `Brand + Line + Product Type + Key Spec + Size/Count`. One generation pass per family; variants get suffix rules (color/size appended). Place the #1 keyword as a contiguous phrase when it reads naturally — exact-phrase match beats scattered tokens, but never at the cost of a title a human wouldn't click.

Hard rules live in `assets/title-rules.json` and are enforced by `scripts/lint_titles.py`, not by eyeballing. Run the linter on every batch; regenerate only failures (the loop converges in 1-2 passes).

**Item Highlights is authored for every family and is never left blank.** It is a separate field Amazon shows beneath the title (up to 125 characters), written as comma-separated product-detail phrases (materials, specs, certifications, compatibility, recommended use, size/count), not full sentences. Populate it two ways: (1) with anything substantiable that would not fit the 75-character title, and (2) proactively, with the product's key substantiable details even when the title had room to spare. **Highlights must complement the title, not echo it:** carry the details the title does not already state, so the field adds information rather than repeating keywords already in the title. Amazon's example does exactly this, trimming the title and putting different specs (USB-C, PPS Support, cable not included) in the highlights. Every listing benefits from highlights, so there is no reason for the field to be empty: if a family genuinely has no substantiable detail to list, treat that as an attribute gap and route it back to the Stage 0 question rather than shipping a blank cell. Draw only from the substantiable attributes captured in Stage 1, and hold item highlights to the same content bar as titles (no unsupported claims, no competitor brand names, no promotional or subjective language, no demand-side intent words). The linter fails any row whose `item_highlights` is empty, exceeds 125 characters, or merely restates the title (it requires a meaningful share of the highlight content to be new relative to the title), so the generate/regenerate loop cannot ship a blank or a title-duplicating highlight.

Amazon's guidance (Product title requirements, Seller Central) frames item highlights as an additional 125 characters for product details such as materials or recommended use cases, written as comma-separated phrases rather than full sentences. Example: a title trimmed to 75 characters, with `USB-C, PPS Support, Cable not included` moved into item highlights.

Never put in a title: competitor brand names, attributes absent from the source listing, promotional or subjective claims, demand-side intent words ("gift", "favors") that don't describe the product.

### Stage 8 — Outputs (write per category as you go, deliver as downloads)

- **`rewrites.csv`** — columns: `asin, parent_asin, category, current_title, current_length, new_title, new_length, status, top_keywords (with volume + source + confidence), baseline_sov, baseline_date, item_highlights, rationale`. `item_highlights` is populated for every row (non-empty, up to 125 characters, comma-separated phrases); a blank here is a linter failure, not an acceptable output.
- **`evidence-trail.md`** — per category: both pools' top rows, the accept/reject table with SOV evidence and reasoning, per-ASIN rationale. A customer should be able to challenge any keyword and find the answer here.
- **`flags.md`** — feed errors found in current titles (impossible specs, wrong attributes), keywords rejected for titles but valuable elsewhere (backend search terms, product-line whitespace like a high-velocity adjacent product the brand doesn't make), low-confidence assignments, any rule applied from `title-rules.json` that is marked `"verified": false`, and any family whose `item_highlights` could only be minimally populated because the feed lacked substantiable attributes (so it can be enriched at the source rather than shipped thin).

Surface each file to the user as a download as it's completed.

## Guardrails

- **Use only retrieved data.** No attribute enters a title or highlight unless it came from the product feed or the user confirmed it in Stage 0. No volume, SOV, or trend figure is ever estimated — every number in the evidence trail traces to a tool result.
- **Don't fabricate to fill a cell.** If a pull is empty or a figure is missing, flag the row rather than inventing a value.
- **Reject when in doubt.** A title with one fewer keyword is recoverable; a title making a claim the product can't support costs conversion and risks a compliance flag (see `references/rejection-examples.md`).
- Treat sales and volume figures as estimates when presenting them to the user.

## Next steps

After delivering the outputs, remind the user that Amazon shows its AI-suggested title in *Review Listing Changes* with a 14-day approval window — they should diff these titles against Amazon's suggestion before approving either. Then propose 2–3 concrete follow-ups grounded in the run and ask which to pursue:

- **Post-upload lint** — re-run `lint_titles.py --census` on the live catalog after the bulk upload lands to confirm compliance took.
- **SOV re-check** — `baseline_sov` and `baseline_date` are in the CSV precisely so the keyword bets can be measured: re-pull SOV on the targeted keywords in ~4 weeks and report movement.
- **Backend search terms** — the rejected-but-valuable keywords in `flags.md` are a ready-made backend search-term list; offer to format it.
- **Attribute enrichment** — if `flags.md` lists thin-feed families, offer the list as a feed-fix worksheet.

## Scale and cost discipline

Call budget is roughly 8–13 calls per leaf category (pools, SOV verification batches, differentiator audits), plus one keyword pull per family in the measured tier, plus one history call per final title keyword for seasonality — catalog size barely matters, category count does. Both customer-side context and the environment's per-conversation limits are the real constraint: pools live in the sandbox, only shortlists enter context, and outputs are written incrementally per category.

Do not assume an entire large catalog fits in one conversation. **Process category by category and export `rewrites.csv` per category as you finish it.** For a small brand (a few categories) one session is fine. For a large brand (many categories, hundreds of families, or a long-running conversation), run categories across separate sessions and concatenate the per-category CSVs at the end — the per-category method and call budget are unchanged. Tell the user which categories a given session covered so nothing is silently dropped.

## Known limits

US marketplace only (localized keywords like `guantes de beisbol` go to flags, not titles). `assets/title-rules.json` carries a `verified` flag and date — if `verified` is false, say so in the output rather than presenting the linter as authoritative. Media categories are exempt from the 75-char rule. Requires the Jungle Scout Cobalt connector/MCP server to be enabled; without it the skill cannot run.
