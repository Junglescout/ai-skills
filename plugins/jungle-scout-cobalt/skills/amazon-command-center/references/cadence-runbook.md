# Cadence runbook

The per-cadence checklists. Read when starting a run.

Each question below is one the run answers, in order, with the tool that answers it and the
degraded path when that tool is unavailable. Two constraints apply to every row and are not
repeated: requests are capped at a **31-day window** with about **14 months** of history, and
built-in period comparison was removed, so **every comparison is computed from separate
calls**. See `mcp-tools.md`.

Notation: **[R]** = repo-verified tool, **[A]** = announcement-sourced tool (name corroborated,
schema unverified — discover parameters at call time).

---

## Before any run

1. Resolve or reuse the inputs: cadence, brand, platform, product lines, marketplace, priority
   ASINs, catalog decline threshold, ACoS threshold, spend floor, budget target,
   campaign-type naming convention, exclusion list.
2. If the user has run this before, reuse the recorded inputs verbatim and confirm nothing
   changed. Comparability across runs is the whole point of a cadence.
3. Load the org (`list_orgs` **[R]**) and validate the brand (`list_org_brands` **[R]**).
4. Note the latest date the data actually covers, per source, and carry it into the header.
5. State which platform vocabulary is in force. **1P:** glance views, net PPM. **3P:**
   sessions, Buy Box win rate. Never mix them.

---

## Pulse — daily or every other day

Focus Areas 1 and 2 only. The goal is a short list of decisions, not a report. Target roughly
a dozen calls; if the priority-ASIN list is long, sample it and say so.

### Focus Area 1 — Product Catalog Status

Goal: catch a real decline early enough to act on, not read about it afterward.

| # | Question | Tool | If unavailable |
| --- | --- | --- | --- |
| 1 | For each priority ASIN, how did traffic and the platform health metric trend over the last 14 days versus the prior 14? | `query_vendor_central_performance` **[A]** (1P: glance views, net PPM) or `query_seller_central_performance` **[A]** (3P: sessions, Buy Box win rate). Two separate calls, one per window. | `analyze_products` **[R]** filtered by `asins` — label every figure a market estimate, not an actual |
| 2 | Which priority ASINs declined more than the decline threshold, and did the traffic metric move with revenue? | Same rows as #1 | Same fallback; weaken the conclusion |
| 3 | Have any priority ASINs had no revenue in the last 30 days? | Same tools, chunked across the 30 days. On 3P the sessions-with-zero-sales cut is the sharper form. | `analyze_products` **[R]** with a revenue threshold |
| 4 | Which ASINs show a sharp revenue drop with **flat** traffic? | Same rows as #1 — this is a pattern read, not a separate pull | Same fallback |
| 5 | For those, who is winning the buy box, at what price, and did new or unauthorized sellers appear? | `analyze_competitive_offers` **[A]**; `analyze_seller_product_offers` **[A]** to drill into one seller | Say the offer check was not available and leave the cause open |
| 6 | Which flagged ASINs have inventory problems — out of stock, nothing sellable, aged stock? | `query_vendor_central_inventory` **[A]** | State that inventory could not be checked; the pause list loses its strongest reason |
| 7 | Outside the priority list, which in-scope ASINs moved into the top decliners? | `analyze_products` **[R]** sorted by revenue decline across the in-scope categories | — |

Run #6 **before** the advertising pause list — it is that list's primary evidence.

**Language discipline:** a decline in glance views, net PPM, sessions, or Buy Box win rate is a
**risk signal** for suppression or inactivity. It is never a confirmed status. Say "at risk,"
and add that this is an early warning, not a substitute for checking the ASIN directly in
Vendor or Seller Central.

### Focus Area 2 — Advertising Effectiveness

Goal: catch wasted spend and clear wins fast enough to act on this week. Read
`advertising-runbook.md` for the decision rules and the math.

| # | Question | Tool | If unavailable |
| --- | --- | --- | --- |
| 8 | Where is account spend against the budget target, and what is the pace index? | `query_ad_performance` **[A]** at account level | No spend data at all — see the no-Advertising-account fallback below |
| 9 | Which active campaigns spent more than the spend floor in the last 7 days with **no** attributed sales? | `query_ad_performance` **[A]** at campaign level | — |
| 10 | Which campaigns are above the ACoS threshold over the last 7 days? Prefer the account's joined ACoS/TACoS/CPU goals over a guessed threshold. | `query_ad_performance` **[A]** | — |
| 11 | What are the top campaigns by wasted spend, and what is the recommended fix for each? | #9 and #10 ranked by dollars, plus `query_ad_targeting` **[A]** for the fix | — |
| 12 | Which keyword targets spent and converted nothing? | `query_ad_targeting` **[A]** — use its spent-but-no-conversion filter directly | — |
| 13 | Which targets have high impressions and low clicks? | `query_ad_targeting` **[A]** | — |
| 14 | Which campaigns or targets are performing well enough to scale, and do they have headroom? | `query_ad_performance` **[A]** with pacing | — |
| 15 | Which ASINs flagged in #6 are spending against unsellable inventory? | Join #6 to #9/#10 | Drop the pause list's inventory reason |

Question 13 is a **relevance or listing** signal, not a bid signal. Never answer it with a bid
change.

Pulse output stays short: the header, "Needs a decision today," a compact catalog table, the
advertising lists, and the coverage note. Skip Market Position entirely.

---

## Weekly review

Everything in Pulse, plus the questions below. This is the run that touches campaign structure
and keyword slates.

### Advertising — the weekly additions

| # | Question | Tool | If unavailable |
| --- | --- | --- | --- |
| 16 | How is spend allocated across campaign types, and how did the mix shift versus the prior week? | `query_ad_performance` **[A]**, bucketed by the user's naming convention | **No convention supplied → campaign-level only.** State that the type breakdown was not possible. |
| 17 | How does each type perform against its own expectation, not one shared threshold? | Same rows as #16 | Same |
| 18 | Which titles entered the catalog recently, and which in-scope ASINs sell with **no** advertising activity? | `analyze_products` **[R]** with `launched_after`, cross-checked against the advertised products in `query_ad_performance` **[A]** | Report new titles only; say the coverage check needed ad data |
| 19 | For each of those, what campaign type and seed keywords should it enter with? | `search_keywords_by_asin` **[R]** with the relevance and volume floors; `get_keyword_sov` **[R]** for current standing | — |
| 20 | Which keywords are proven enough in Auto or Experimental to graduate to Evergreen? | `query_ad_targeting` **[A]** for conversion evidence, joined to `search_keywords_by_asin` **[R]** for demand and ease to rank | Skip; say graduation needed target-level ad data |
| 21 | Which new keywords should enter Experimental this week? | `search_keywords_by_asin` **[R]**, `search_keywords_by_keyword` **[R]**, ranked by trend against `ease_to_rank`; `get_keyword_sov` **[R]** for position; `get_keyword_search_volume_history` **[R]** for featured terms only | This section runs **without** an ads account — keep it |
| 22 | Which titles became eligible to re-enable? | #6 recovery joined to #21 demand, minus the exclusion list | — |
| 23 | Which changes have now recurred across runs and should become an automation? | Comparison against prior runs | Skip on a first run |

Question 21 is worth protecting: it is the one advertising-adjacent section that works fully on
repo-verified tools and needs no connected account. For a full discovery pass, hand off to
`analyze-category-keywords`.

### Focus Area 3 — Market Position, light

| # | Question | Tool |
| --- | --- | --- |
| 24 | How is the brand's own revenue trending in scope? | `query_org_performance` **[R]**, `group_by="trend"` |
| 25 | How does that compare to category growth over the same window? | `analyze_categories` **[R]** with `aggregate:true` |
| 26 | Which competitor brands gained the most share this week? | `analyze_brands` **[R]** sorted by `market_share`, enough rows to include the user's brand |
| 27 | How does the last 14 days in scope compare to the broader category over the same window? | #24 and #25 as separate chunked calls |

Keep this to a few sentences and one table at weekly cadence. The full treatment belongs to
the Deep Dive.

---

## Deep dive — monthly or quarterly

Focus Area 3 leads; Focus Areas 1 and 2 are summarized to their trends rather than re-listed
item by item. **Chunk every window**: a 90-day read is three or more calls per period, and a
year-over-year read is that again for the prior period. Plan the call budget first.

| # | Question | Tool | Notes |
| --- | --- | --- | --- |
| 28 | How is revenue in scope trending over the last 90 days versus the same period last year? | `query_org_performance` **[R]** for owned actuals; `analyze_categories` **[R]** / `analyze_brands` **[R]** for the market view | **Apply the year-over-year caveat** — see below |
| 29 | How does the growth rate compare to the top 5 competitor brands this quarter? | `analyze_brands` **[R]** | Compare growth rates, not absolute revenue |
| 30 | Which competitors are gaining the most share right now? | `analyze_brands` **[R]** by `market_share_growth` | Rank by share points and revenue scale, not by percentage growth on a tiny base |
| 31 | Is the gain driven by price, new SKUs, or rank movement? | `analyze_price_tiers` **[R]** for price; `analyze_products` **[R]** with `group_by: launch_cohort` for new-SKU contribution; `get_keyword_sov` **[R]** for organic and sponsored rank movement | Answer all three separately; do not collapse them into one cause |
| 32 | Are there new entrants gaining meaningful share that were not on the radar six months ago? | `analyze_products` **[R]** with `launched_after`; `analyze_brands` **[R]** | Six months back is within the ~14-month history |
| 33 | How does segment performance over the last 14 days compare to the overall market segment? | #24 and #25, chunked | Separate calls, explicit windows |
| 34 | What actions would most likely close the gap between our growth rate and the category's? | Synthesis across the run, tied to the advertising decisions | The one place in the run that proposes strategy — keep it grounded in retrieved figures |
| 35 | Over the quarter, which advertising changes recurred often enough to be encoded as automations? | Comparison across runs | Route to Rulebooks, ABC, Dayparting, or Keyword Harvesting |

For anything deeper — a real benchmark or a share diagnosis — invoke `benchmark-brand` or
`share-diagnosis` and carry their findings back into the advertising decisions. Do not restate
their method here.

**The year-over-year caveat, stated in the output every time it applies:** year-ago
comparisons align on **exact calendar dates** rather than comparable **Sunday–Saturday retail
weeks**. This has produced figures that disagreed with a customer's agency. Note it wherever
the run makes a year-over-year read, and prefer a same-weekday-aligned window when the number
will be compared against an agency or an internal report.

---

## Closing every run

1. **Rank the consolidated action list by dollars at stake**, across all action types. That
   list is the deliverable; everything else is support.
2. **Record the resolved inputs** — thresholds, priority ASINs, campaign-type convention,
   budget target — so the next run is directly comparable.
3. **State the coverage**: which tools ran, which returned actuals versus estimates, the
   windows and chunk boundaries, the latest date each source covers, which documented gaps
   affected this run, and what could not be checked at all.
4. **Say what changed since the last run** if there was one. A cadence exists to show
   movement; a run that reads identically to a standalone report wastes the cadence.
5. **Never claim an executed change.** Flagged, recommended, proposed, eligible, candidate —
   applied by the user in Cobalt or the Amazon Ads console.
