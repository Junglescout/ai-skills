# Advertising runbook

The heaviest part of a Command Center run. Read before Focus Area 2.

This runbook covers the recurring advertising work an Amazon operator does every week: the ten
tasks below, the campaign-type allocation logic, the decision rules for pausing, re-enabling,
pruning, scaling, and changing bids and budgets, the threshold and pacing math, and the shape
of every change list.

**The one thing to internalize first:** the connector reads; the human writes. Six of the ten
tasks below end in a human action in the Cobalt app or the Amazon Ads console. This runbook's
job is to make that action a decision that takes seconds, not a research project.

---

## The ten recurring tasks, mapped honestly

| Task | What the connector can do | Where it gets executed |
| --- | --- | --- |
| 1. Update product status reports and sync into a spreadsheet workflow | Pull every number: `query_seller_central_performance` / `query_vendor_central_performance`, `query_org_performance`, `query_ad_performance` | The spreadsheet sync is **not** a Jungle Scout capability. Emit a stable paste-ready table; the host handles the sync. |
| 2. Review campaign and inventory status; confirm titles are correctly categorized across campaigns | Ad performance by campaign / ad group / advertised product (`query_ad_performance`); inventory (`query_vendor_central_inventory`, or sessions-with-zero-sales on 3P) | **Gap.** Campaign state is not confirmed readable and Cobalt product labels are not readable at all. The categorization check needs a Cobalt export. Do the coverage check instead — see below. |
| 3. Add new titles to the appropriate campaign structures | Find the new titles (`analyze_products` with `launched_after`), check which have no ad activity, propose campaign type and seed keywords (`search_keywords_by_asin`) | Creating the campaign: Cobalt app / Ads console |
| 4. Pause product ads for titles that should no longer be active | Assemble the evidence: out-of-stock / nothing-sellable / aged inventory joined to current spend | Cobalt app (Rulebooks) / Ads console |
| 5. Re-enable paused product ads when titles become eligible again | Identify newly in-stock titles with live keyword demand | Cobalt app / Ads console. **Cannot confirm current paused state** — present as candidates. |
| 6. Review keyword performance and budget allocation across campaign types | Spend, ACoS/ROAS, CPC, CTR, pacing (`query_ad_performance`); bids, match types, search terms (`query_ad_targeting`) | Reading only. **Type bucketing depends on the user's naming convention**, since type and labels aren't readable. |
| 7. Adjust bids and budgets against ACoS thresholds | Compute against the threshold, or against the ACoS/TACoS/CPU goals joined into the ad data; rank proposed changes by dollars | Cobalt (ABC, Rulebooks) or Ads console |
| 8. Identify underperforming keywords to cut waste; scale stronger performers | The spent-but-no-conversion filter on `query_ad_targeting`; performer ranking with headroom | Cobalt Keyword Harvesting (including negative exact) or Ads console |
| 9. Research and add new keywords to Experimental campaigns | Strongest area: `search_keywords_by_asin`, `search_keywords_by_keyword`, `get_keyword_sov`, `get_keyword_search_volume_history` | Adding them: Cobalt / Ads console |
| 10. Monitor total advertising spend against budget targets | Budget pacing, campaigns and portfolios closest to their cap, account-level spend, trends | Reading only. Recurring alerting belongs in the Cobalt app. |

The honest self-description: this skill can answer *what happened, what it means, and what to
change* across all ten. It can change none of them.

---

## Campaign-type allocation

The client convention this skill was built around uses four types: **Auto**, **Experimental**,
**Short Term Boost**, and **Long Term Evergreen**. These are the **user's own campaign-type
names**, not connector fields — treat them as configurable and confirm them at input time.

**Campaign type is not confirmed readable as a field, and Cobalt product labels are not
readable at all.** So bucketing works one way only: the user tells you how type is encoded in
campaign names, and you match on that. If they cannot give you a convention, report at
campaign level and state plainly that the type breakdown was not possible. Do not infer types
from name fragments you were not given.

Each type answers a different question, so the same ACoS number means different things by type:

| Type | What it is for | Read it as |
| --- | --- | --- |
| **Auto** | Amazon-driven discovery | A **search-term mine**. Judge it on the harvestable terms it surfaces, not only on ACoS. High spend with no harvest is the real waste. |
| **Experimental** | Testing new keywords and new titles | Judge on **learning rate**, not efficiency. Expect ACoS above threshold. Cut on *no data* (spend with negligible clicks) and on clear losers, not on being above target. |
| **Short Term Boost** | Time-boxed push — launch, promo, seasonal | Judge against the **window's** goal. Above-threshold ACoS is often correct here. Check whether the window has ended and the campaign is still spending. |
| **Long Term Evergreen** | The efficient core | The **strictest** ACoS discipline. A breach here is the highest-priority flag in the run. |

Two allocation reads worth producing every weekly run:

- **Mix** — spend share by type against the prior period. A quiet drift of spend from Evergreen
  into Experimental changes account efficiency without any single campaign looking wrong.
- **Return by type** — ACoS and ad sales per type. Report each against its own expectation,
  never all four against one threshold.

**The graduation path is the most useful recurring recommendation this section makes:** a term
proven in Auto or Experimental (meaningful clicks, conversions, ACoS at or under target across
a sustained window) belongs in Evergreen at a considered bid, and usually as a negative in the
campaign that discovered it so the two stop bidding against each other. Surface graduation
candidates by name every weekly run, with the evidence that qualified them.

---

## Threshold and pacing math

State the window and the numbers used for every figure. All of this is arithmetic on retrieved
values — never estimate a component you did not retrieve.

**ACoS** = ad spend ÷ ad sales, over one stated window. Prefer the ACoS the advertising tool
returns. Prefer the account's joined ACoS/TACoS/CPU **goals** over a threshold the user
guessed at, when those goals are set — and say which you used.

**Breach severity — rank by dollars, never by percentage.** A 400% ACoS on $12 of spend is not
the week's problem.

```
Excess spend ≈ spend − (ad sales × target ACoS)
```

That is the dollars above target in the window. Sort every ACoS list by it.

**Wasted spend** = spend above the user's spend floor with **zero** attributed sales in the
window. Rank by spend. This list is the run's most reliable finding because it needs no
threshold judgment at all.

**Budget pace.** With a stated period budget:

```
period elapsed % = days elapsed ÷ days in period
budget consumed % = spend to date ÷ period budget
pace index      = budget consumed % ÷ period elapsed %
```

Pace index above 1 is running hot, below 1 is underspending. Report the index **and** both raw
numbers, and project period-end spend at the current daily rate. Note that projection is a
linear extrapolation, not a forecast.

Without a stated budget target, the connector still reports campaign-level budget pacing and
which campaigns or portfolios sit closest to their cap — use that, and say the account-level
target was not supplied.

**Bid change sizing.** Bid moves are proportional to the gap between observed and target
efficiency, not fixed steps:

```
suggested bid ratio ≈ target ACoS ÷ observed ACoS   (on a converting target)
```

Cap any single recommendation at a conservative move — large swings on thin data are how
accounts get destabilized. Require a **minimum evidence bar** before recommending any bid
change: enough clicks in the window for the number to mean something. When a target has spend
but too few clicks to judge, the finding is *insufficient data*, not a bid change. Say:
"Available data does not indicate the underlying cause."

---

## Decision rules

Every rule below produces a **candidate with evidence**, not an executed change.

### Pause candidates

Flag for pausing when spend is live and at least one hard condition holds:

1. **Inventory** — out of stock, nothing sellable on hand, or chronic stockout
   (`query_vendor_central_inventory` on 1P; zero-sale-with-sessions plus catalog signals on 3P).
   This is the strongest pause reason because the spend cannot convert.
2. **Wasted spend** — spend above the floor with zero attributed sales across a window long
   enough to be meaningful.
3. **Severe efficiency breach** — ACoS far above target with material spend, in a type where
   the breach is not expected (Evergreen first, then Short Term Boost past its window).
4. **Ended window** — a Short Term Boost still spending after its stated window closed.

Each row states the reason, the dollars at stake, and the window. Where a title should be
excluded manually, that is the user's call — respect the exclusion list and never re-flag it.

### Re-enable candidates

Propose re-enabling when **all** hold: inventory has recovered (in stock, sellable on hand),
the ASIN is not on the manual-exclusion list, and its keywords still show live demand
(`search_keywords_by_asin` volume and trend, `get_keyword_sov` for current position).

**You cannot confirm anything is currently paused.** Present the list as "eligible to
re-enable — confirm current state in your console," and never as a set of known-paused
campaigns.

### Prune candidates (targets, not campaigns)

From `query_ad_targeting`, using the spent-but-no-conversion filter as the primary source:

- **Spent, converted nothing** over a meaningful window → prune, or add as negative exact.
- **Clicks with no conversions** at material spend → prune; check the listing before blaming
  the target.
- **High impressions, very low clicks** → **not** a bid problem. This is relevance or listing
  quality. Recommend a relevance or listing review, or a negative if the term is genuinely
  irrelevant. Do not recommend a bid change here.
- **Search term does not match the keyword it rolled up under** → a negative-keyword candidate
  in the discovering campaign rather than a bid change.

Separate *prune the target* from *negative the search term* — they are different actions with
different effects, and Keyword Harvesting in the Cobalt app can apply harvested negatives
(including negative exact) as a standing rule.

### Scale candidates

Propose scaling when a campaign or target is **at or under** target ACoS with material
conversion volume, **and** there is headroom: the campaign is not already capped by budget, or
it is capped and the pacing data shows it hits the cap consistently (a capped, efficient
campaign is the cleanest budget-increase case in the run).

Rank by incremental opportunity, not by ACoS alone. A target at 12% ACoS on $40 of spend is a
smaller opportunity than one at 22% on $900.

### New-title routing

For each in-scope ASIN with sales activity and **no** advertising activity (the coverage check
that stands in for the unreadable label check):

1. Name the ASIN and its recent performance.
2. Propose the campaign type — new and unproven titles usually enter **Experimental** or
   **Auto**; a title with a proven analogue in the catalog can enter **Evergreen** directly.
3. Supply seed keywords from `search_keywords_by_asin`, filtered by the relevance and volume
   floors, with volume, trend, and `ease_to_rank`.
4. Propose match types, and flag terms where `get_keyword_sov` shows the brand already ranks
   organically — those need a different bid posture than terms it does not rank for.

### New keywords for Experimental

Discovery is the connector's strongest advertising-adjacent capability. Run
`search_keywords_by_asin` on the relevant hero ASINs and `search_keywords_by_keyword` on the
category term, apply the volume and relevance floors, dedupe by lowercased name, and rank by
demand trend against `ease_to_rank`. Check current standing with `get_keyword_sov`, and pull
`get_keyword_search_volume_history` only for the handful you feature — one keyword per call.

Present each candidate with volume, 90-day and 30-day trend, ease to rank, current SoV, and
whether the brand already ranks organically. For a full discovery pass, hand off to
`analyze-category-keywords` instead of reimplementing it.

Distinguish a **still-climbing** term from one that has **already peaked**: strong 90-day
growth with a negative 30-day is a peaked term, not an opportunity. Do not put peaked terms in
an Experimental slate without labeling them.

---

## The change-list schema

Every advertising output row carries the same six fields, so the list can be worked top to
bottom without re-reading the analysis:

| Field | Contents |
| --- | --- |
| **Target** | The campaign, ad group, advertised product, or keyword — named, not described |
| **Action** | Flag for pausing / eligible to re-enable / prune / add as negative exact / raise bid / lower bid / raise budget / lower budget / route to campaign |
| **Current** | The observed value: current bid, current budget, current ACoS, current spend |
| **Proposed** | The recommended value, or "confirm state first" where state is unknown |
| **Evidence** | The numbers and the window: spend, ad sales, ACoS, clicks, inventory status |
| **Apply in** | Cobalt app or Amazon Ads console — and which of Rulebooks, ABC, Dayparting, or Keyword Harvesting would own it if it recurs |

Sort the consolidated list by **dollars at stake**, descending, across all action types. The
user works down until they run out of time, and the most expensive decision is always first.

---

## When to recommend an automation instead of a change

A change the user makes again every week is a rule they have not written down yet. Four Cobalt
app automations can push real changes to Amazon — **Rulebooks**, **ABC**, **Dayparting**, and
**Keyword Harvesting**. Do not name any automation feature beyond those four.

| The recurring pattern | Route it to |
| --- | --- |
| The same threshold-based bid or budget change every week | **Rulebooks** |
| Budget multipliers applied to a base budget on a repeating schedule | **ABC** |
| Bid changes tied to time of day — note that hourly granularity is **not** readable via the connector, so this is a routing recommendation, not a finding | **Dayparting** |
| Harvesting proven search terms into campaigns, or adding poor performers as negative exact | **Keyword Harvesting** |

Say it plainly: "this is the third run flagging the same rule — encode it as a Rulebook rather
than applying it by hand." That is a more valuable output than the individual change.

---

## Advertising fallbacks

- **No connected Advertising account** — the advertising tools cannot run. There is no spend,
  ACoS, bid, or budget data. The only advertising-adjacent signal available is sponsored share
  of voice from `get_keyword_sov`, which is a **placement-share** metric — present it as
  presence, never as cost or efficiency. Say plainly which figures were unavailable, and offer
  the keyword-research and market sections, which do not depend on the account.
- **No campaign-type convention** — campaign-level reporting only, with the gap stated.
- **Campaign state unknown** — always. Candidates to confirm, never confirmed states.
- **Goals not set on the account** — use the user's stated ACoS threshold and say the account's
  joined goals were not available.
- **No budget target supplied** — report campaign-level pacing and cap proximity, and say the
  account-level target was not supplied.
- **Thin data on a target** — insufficient-data finding, not a bid change. Use:
  "Available data does not indicate the underlying cause."
- **A parameter is rejected** — the advertising tools' schemas are unverified in this
  repository. Read the error, inspect the tool definition, correct the call. Do not retry a
  guessed parameter name.
