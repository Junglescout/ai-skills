---
name: amazon-command-center
description:
  Use this skill whenever the user wants a recurring monitoring workflow across their
  Amazon business rather than a one-off analysis — a daily or every-other-day catalog
  and advertising check, a weekly review, or a monthly/quarterly deep dive covering
  product catalog status, advertising effectiveness, and market position, using the
  Jungle Scout Cobalt connector/MCP server. Trigger for prompts such as amazon command
  center, daily catalog check, run my daily ads check, weekly amazon review, what needs
  my attention this week, which campaigns are wasting spend, which campaigns are over
  my ACoS threshold, what should I pause, what should I re-enable, keyword performance
  review, bid and budget changes, prune underperforming keywords, scale my winners, new
  keywords for my Experimental campaigns, am I on pace against budget, product status
  report, or are we losing ground to competitors. Also trigger when the user describes a
  recurring weekly process across campaigns, inventory, and catalog rather than naming a
  report. The connector is read-only, so this skill produces decision-ready change lists
  the user applies themselves and never claims to have made a change. Presentation
  styling is deferred to the jungle-scout-visualizer skill, which this skill depends on.
---

# Amazon Command Center

Run a repeatable monitoring workflow over an Amazon business using the Jungle Scout
Cobalt connector/MCP server: catch catalog declines early, find wasted and winning ad
spend fast enough to act on this week, and track market position against the category
and named competitors. Built for an operator who does the same rounds every day, every
week, and every quarter — not for a one-off report.

Advertising carries the most weight here, because that is where the recurring work is:
campaign and inventory status review, adding new titles to campaign structures, pausing
and re-enabling product ads, keyword performance and budget allocation across campaign
types, ACoS-threshold bid and budget changes, pruning underperformers, scaling winners,
new keyword research, and total spend against budget.

This skill **owns the workflow and the structure** of each run — which checks fire at
which cadence, in what order, and what each produces. It does **not** define visual
styling: defer palette, callouts, charts, growth pills, and tables to the
`jungle-scout-visualizer` skill.

**Before the first call, read `references/mcp-tools.md`.** It carries the tool inventory
with a provenance column, the parameters that are actually verified, and the hard query
limits (31-day windows, no built-in period comparison) that change how every fetch is
shaped.

## The Read-Only Boundary — State This Before You Recommend Anything

The Jungle Scout Cobalt connector is **read and analysis only**. This is confirmed, not
assumed: the engineer who shipped the advertising tools stated "all of our tools are read
only at the moment," and product confirmed "the MCP is read-only." Every tool in the
inventory is a `query_*`, `analyze_*`, `search_*`, `get_*`, `list_*`, or `describe_*`
reader. There is no tool that pauses an ad, changes a bid, changes a budget, adds a
keyword, or adds a title to a campaign.

So every action this skill produces is a **decision-ready list** — target, current value,
proposed value, evidence, and the math — that the **human applies** in the Cobalt app or
the Amazon Ads console.

- **Never** say "I paused it," "I've lowered that bid," "budget updated," or "keywords
  added." Use: *flagged for pausing*, *recommended bid*, *proposed budget*, *apply in
  Cobalt*.
- Writes against Amazon Ads do exist, but in the **Cobalt web app**, not the connector.
  Four app automations can push real changes: **Rulebooks**, **ABC**, **Dayparting**, and
  **Keyword Harvesting**. Do not name any automation feature beyond those four.
- When a recommendation is a rule the user will re-apply every week, say which of those
  four would own it going forward. A repeated manual change is a signal the right output
  is an automation profile, not a one-off list.
- This skill also cannot run itself on a schedule, write to a spreadsheet, or emit a file.
  Scheduled runs are not a connector capability; exports and charts belong to the host app.
  The user (or their host) drives the cadence.

## Cadences

Three run modes. Ask which one, or infer it from the request and say which you assumed.

| Cadence | Run | Covers |
| --- | --- | --- |
| **Pulse** — daily or every other day | Focus Area 1 + Focus Area 2 | Catalog decline and inactivity risk; wasted spend, ACoS breaches, budget pace |
| **Weekly review** | All three focus areas | Pulse plus keyword performance, campaign-type allocation, new-title routing, market position |
| **Deep dive** — monthly or quarterly | Focus Area 3 led, 1 + 2 summarized | Year-over-year and 90-day trajectory, competitive share, new entrants, price tiers |

Keep the same scope, thresholds, and metric definitions across runs so consecutive runs
are comparable. When the user has run this before, open with what changed since the last
run rather than restating the whole picture.

For the Deep Dive, hand the heavy competitive work to the existing skills rather than
restating their method: `benchmark-brand` for brand-versus-category benchmarking and price
tiers, `share-diagnosis` for why share moved, `analyze-category-keywords` for emerging
category demand. This skill's job at that cadence is to run them on a schedule and tie
their findings back to the advertising decisions.

## Inputs to Resolve

Confirm the inputs with the user before running — don't guess at the brand, the platform,
or the thresholds. If the environment supports a structured input form or a
multiple-choice prompt, **present one** that captures the fields below (required first,
optional pre-filled with the defaults shown). Otherwise ask a short, **batched** set of
questions in one message — not one at a time. Skip the questions only when the user
already supplied the values, or has run this skill before and the setup is unchanged.

**Required**

- **Cadence** — Pulse, Weekly review, or Deep dive (see above).
- **Brand / customer** — the brand(s) covered, exactly as the user states them. Validate
  with `list_org_brands` or `analyze_brands`.
- **Platform** — Vendor Central, Seller Central, or both. This decides which actuals tools
  can run at all, and which vocabulary is correct (glance views and net PPM are 1P terms;
  sessions and Buy Box win rate are 3P terms). Never mix the two vocabularies.
- **Product lines** — the lines or categories in scope. Resolve category names with
  `search_categories_by_name`; if several plausibly match, have the user pick.

**Optional (offer with defaults)**

- **Organization** — call `list_orgs`; if the user belongs to more than one, have them pick.
- **Marketplace** — default `us` for sales-estimate tools, `US` for keyword/category tools.
  Note the casing difference; see `references/mcp-tools.md`.
- **Priority ASINs** — the named watch list checked every Pulse run. Default: derive the
  top ASINs by revenue in scope with `analyze_products` and offer that list for the user to
  edit. A user-curated list beats a derived one — ask for it.
- **Catalog decline threshold** — percent decline week over week that trips a flag.
  Default **10%**, on a 14-day versus prior-14-day window.
- **ACoS threshold** — the ACoS above which a campaign is flagged. No default: ask, because
  an inherited number produces wrong flags. Offer to read the ACoS/TACoS/CPU goals already
  joined into the advertising data instead, if the account has them set.
- **Spend floor** — minimum spend in the last 7 days for a no-sales campaign to be worth
  flagging. Default **$100**; scale it to account size.
- **Total budget target** — the period budget the run paces against. Ask for the number and
  the period; the connector reports spend and pacing, not the user's internal target.
- **Campaign-type naming** — how campaign types are identifiable from campaign names, e.g.
  the client convention **Auto**, **Experimental**, **Short Term Boost**, **Long Term
  Evergreen**. **You must ask for this.** Campaign type is not confirmed readable as a
  field, and Cobalt product labels are not readable by the connector at all, so bucketing
  depends entirely on a naming convention the user gives you. If they can't give one,
  report at the campaign level and say the type breakdown was not possible.
- **Excluded ASINs / campaigns** — titles under manual exclusion that should never be
  flagged for re-enabling.

Record the resolved inputs in the output so the next run reuses them verbatim.

## Jungle Scout Cobalt Connector Tool Map

Two tiers of confidence, and the difference matters. **Repo-verified** tools have a
hand-checked parameter and response reference in this repository. **Announcement-sourced**
tools are named in internal Cobalt release announcements; the names are well corroborated
but **their parameters, enums, and response fields are not verified here** — discover the
schema at call time from the tool definition and use only fields the response actually
returns. Never assert a parameter name for an announcement-sourced tool.

| Workflow need | MCP tools | Provenance |
| --- | --- | --- |
| Org selection | `list_orgs` | Repo-verified |
| Owned brands | `list_org_brands` | Repo-verified |
| Category resolution | `search_categories_by_name`, `get_categories_by_ids` | Repo-verified |
| Category totals and growth | `analyze_categories` | Repo-verified |
| Brand and competitor performance, share | `analyze_brands` | Repo-verified |
| ASIN-level estimates, launches, launch-cohort split | `analyze_products` | Repo-verified |
| Price-tier position | `analyze_price_tiers` | Repo-verified |
| Product attribute breakdown | `analyze_attributes` | Repo-verified |
| Custom shapes the typed tools can't express | `describe_sales_estimates_schema` then `query_sales_estimates` | Repo-verified |
| Owned/managed brand performance and trend | `query_org_performance` | Repo-verified |
| Keyword discovery and demand trend | `search_keywords_by_asin`, `search_keywords_by_keyword` | Repo-verified |
| Share of voice, organic and sponsored | `get_keyword_sov` | Repo-verified |
| Daily or fold-weighted SoV, only when specifically needed | `get_keyword_historical_sov` | Repo-verified |
| One keyword's weekly volume history | `get_keyword_search_volume_history` | Repo-verified |
| Ad spend, ad sales, ACoS/ROAS, CPC, CTR, budget pacing | `query_ad_performance` | Announcement-sourced |
| Keyword targets with bid and match type, shopper search terms, spent-but-no-conversion | `query_ad_targeting` | Announcement-sourced |
| 3P actuals: sessions, zero-sale products, Buy Box win rate, organic vs ad-attributed, TACoS | `query_seller_central_performance` | Announcement-sourced |
| 1P actuals: net PPM, glance views, returns, manufacturing vs sourcing | `query_vendor_central_performance` | Announcement-sourced |
| 1P inventory: aged stock, chronic out-of-stock, nothing-sellable, open POs and fill rate | `query_vendor_central_inventory` | Announcement-sourced |
| Buy box winner and price, new or unauthorized sellers, own catalog only | `analyze_competitive_offers` | Announcement-sourced |
| Seller drill-down across a shortlist of own ASINs | `analyze_seller_product_offers` | Announcement-sourced |

Notes that prevent wrong calls:

- Portfolio-level advertising questions and Amazon DSP reporting are answered by the
  advertising surface, but **no distinct tool name is documented for either** — they are
  most likely levels or filters on the advertising tools. Discover them from the live tool
  list; do not guess a tool name.
- The advertising and actuals tools require a connected Seller/Vendor Central account, and
  the advertising tools require a connected Amazon Advertising account. `analyze_competitive_offers`
  and `analyze_seller_product_offers` work **only on ASINs in the user's own catalog**.
- `query_ad_performance` reports at campaign, ad group, advertised-product, and account
  level. The exact advertised-product-to-title mapping shape is unconfirmed; check what the
  response gives you before promising ad-level detail.
- Rendering tools (`visualize:show_widget`, `read_me`) belong to the host, not the
  connector — see `jungle-scout-visualizer`.

## Data Availability — Documented Gaps

These are real, known gaps. Design each run around them and say so in the output rather
than papering over them. A documented gap is a correct answer.

| The workflow wants | Status | How this skill degrades |
| --- | --- | --- |
| Campaign **state** (enabled / paused / archived) | **Not confirmed readable.** No status field appears in any documentation. | Never claim a campaign is paused or active. Ask the user for current state, or produce the list as "flagged for pausing / eligible to re-enable — confirm current state in your console." |
| Campaign **type** (Auto / Experimental / Short Term Boost / Long Term Evergreen) | **Not confirmed readable** as a field. | Bucket from the user's naming convention. If none is supplied, report at campaign level and state that the type breakdown was not possible. |
| Cobalt **product labels** | **Not readable** by the connector or AI Chat. | The "titles correctly categorized across campaigns" check cannot be done from connector data. Do the coverage check instead: which in-scope ASINs have advertising activity and which have none. Flag the label check as requiring a Cobalt export. |
| Confirming a title is a "product ad" per campaign | Advertised-product level is available; the mapping shape is unconfirmed. | Verify against the response before claiming ASIN-to-campaign attribution. |
| Hourly / dayparting granularity | Absent. | Report at day/week/month. Route recurring time-of-day changes to Dayparting in the Cobalt app. |
| Keyword relevancy / value score inside the advertising tools | Absent there; present on `search_keywords_by_asin` / `search_keywords_by_keyword`. | Pull relevance and ease-to-rank from the keyword tools and join it to the advertising view by keyword text. Say it is a join, not one source. |
| ASIN / conquest targeting | Absent. | Cover competitor presence with `get_keyword_sov` sponsored metrics instead, and label it share of voice, not targeting. |
| MAP-breach detection and lost-revenue sizing | Absent. | Report the offer facts `analyze_competitive_offers` returns; do not infer a policy breach. |
| Writing any change | Absent — read-only. | Decision-ready list; human applies it. |
| Spreadsheet sync (e.g. the Google Sheets workflow) | Not a Jungle Scout capability. | Emit a stable, paste-ready table with an unchanging column order; the host handles the sync. |
| Scheduled/proactive runs, exports, files | Not connector capabilities. | The user drives the cadence; recurring alerting belongs in the Cobalt app. |
| Advertising data refresh cadence and lag | **Undetermined.** | Report the latest date the data actually covers, and flag it when a figure rests on a refresh more than a few days old. |
| Whether the 31-day window cap applies to the advertising tools | **Undetermined.** | Chunk defensively at 31 days; if a wider window succeeds, note it and continue. |

## Data Fetch Sequence

Fetch independent data in parallel when possible. Resolve inputs first, then run the focus
areas the cadence calls for. Two constraints shape every fetch: requests are capped at a
**31-day window** with roughly **14 months** of history, and built-in period-over-period
comparison was removed — so **compute every comparison yourself from separate calls**. A
90-day or year-over-year read is three or more chunked calls per period, not one. See
`references/mcp-tools.md`.

0. **Resolve** org, marketplace, brand, platform, product lines, priority ASINs, thresholds,
   budget target, and campaign-type naming.

### Focus Area 1 — Product Catalog Status (Pulse and Weekly)

Goal: catch a real decline early enough to act on, not read about it afterward.

1. **Priority-ASIN trend** — pull the last 14 days and the prior 14 days as **separate
   calls** and compute the delta yourself. On Vendor Central use
   `query_vendor_central_performance` (glance views, net PPM); on Seller Central use
   `query_seller_central_performance` (sessions, Buy Box win rate). Scope to the priority
   ASINs. If actuals are unavailable, fall back to `analyze_products` filtered to those
   ASINs and label every figure an estimate.
2. **Threshold screen** — list the priority ASINs that declined more than the catalog
   decline threshold, and state whether the traffic metric moved with revenue or not.
3. **Inactivity screen** — priority ASINs with no revenue in the last 30 days (chunk the
   window). On Seller Central, the sessions-with-zero-sales cut from
   `query_seller_central_performance` is the sharper version of this question.
4. **Revenue down, traffic flat** — flag these separately. That pattern points toward price
   or Buy Box loss rather than traffic loss. Confirm with `analyze_competitive_offers` on
   those ASINs: who is winning the buy box and at what price, and whether new sellers
   appeared. Use `analyze_seller_product_offers` to drill into a specific seller.
5. **Inventory cross-check** — on Vendor Central, `query_vendor_central_inventory` for
   chronic out-of-stock, nothing-sellable, and aged stock across the flagged ASINs. This is
   the input to the pause list in Focus Area 2, so run it before that list.
6. **Outside the watch list** — `analyze_products` sorted by revenue decline across the
   in-scope categories, to catch decliners the priority list misses.

### Focus Area 2 — Advertising Effectiveness (Pulse and Weekly — the heaviest section)

Goal: catch wasted spend and clear wins fast enough to act on this week. Read
`references/advertising-runbook.md` before this section — it carries the decision rules,
the threshold math, the campaign-type allocation logic, and the exact shape of each change
list.

7. **Account pace** — `query_ad_performance` at account level for the period to date:
   spend, ad sales, ACoS, and budget pacing. Compare against the user's stated budget target
   and report pace as a percentage of period elapsed versus budget consumed.
8. **Campaign roll-up** — `query_ad_performance` at campaign level for the last 7 days,
   with the prior 7 days as a separate call for the comparison. Bucket by campaign type
   using the user's naming convention.
9. **Wasted spend** — campaigns above the spend floor with no attributed sales, then
   campaigns above the ACoS threshold. Rank by dollars at risk, not by percentage.
10. **Target-level detail** — `query_ad_targeting` for the campaigns that surfaced in step 9:
    keyword targets with bid and match type, shopper search terms, cost per search term, and
    the spent-but-no-conversion filter. This is where prune-versus-scale decisions are made.
11. **High impressions, low clicks** — from the target-level data, isolate targets with
    impressions but few clicks. Treat that as a relevance or listing problem, not a bidding
    problem, and say which.
12. **Scale candidates** — campaigns and targets performing well inside the ACoS threshold
    with pacing headroom. Rank by incremental opportunity.
13. **Coverage and new titles** — new or recently launched ASINs in scope via
    `analyze_products` with `launched_after`, cross-checked against which ASINs appear in
    the advertising data. Anything selling with no advertising activity is a routing
    candidate. For each, propose the campaign type and seed keywords from
    `search_keywords_by_asin`, filtered by relevance and volume.
14. **New keyword research for Experimental** — `search_keywords_by_asin` on the relevant
    hero ASINs and `search_keywords_by_keyword` on the category term, filtered by the volume
    and relevance floors, ranked by demand trend and ease to rank. Check current position
    with `get_keyword_sov`, and pull `get_keyword_search_volume_history` only for the handful
    you feature — it is one keyword per call. For a full discovery pass, hand off to
    `analyze-category-keywords` rather than reimplementing it.
15. **Re-enable candidates** — ASINs whose inventory recovered in step 5 and whose keywords
    still show live demand. Exclude anything on the user's manual-exclusion list. Present as
    candidates to confirm, never as confirmed-paused campaigns.

### Focus Area 3 — Market Position and Competitive Benchmarking (Weekly light, Deep dive full)

Goal: are we winning or losing ground, and against whom?

16. **Own trajectory** — `query_org_performance` for the brand and scope, and
    `group_by="trend"` for the trend series. For a 90-day or year-over-year read, chunk the
    windows and compute the comparison yourself.
17. **Category and competitors** — `analyze_categories` for category totals and growth, and
    `analyze_brands` scoped to the same categories for competitor revenue, share, share
    movement, units, and ASP. Include enough rows that the user's brand appears even when it
    sits outside the top 10.
18. **What's driving a competitor's gain** — separate price, new SKUs, and rank movement:
    `analyze_price_tiers` for price position, `analyze_products` with `group_by:
    launch_cohort` for new-SKU contribution, `get_keyword_sov` for organic and sponsored
    rank movement on shared terms.
19. **New entrants** — `analyze_products` with `launched_after` roughly 90 days back, and
    `analyze_brands` for brands that were not material six months ago.
20. **Segment versus market** — the last 14 days for the user's scope against the same
    window for the broader category, as separate chunked calls.

For anything beyond this — a full benchmark, a real share diagnosis — invoke
`benchmark-brand` or `share-diagnosis` and carry their findings into the advertising
decisions rather than duplicating their method here.

## Analysis Rules and Guardrails

Use only retrieved data. Do not infer strategy, consumer intent, promotions, algorithm
effects, margin, or campaign state unless the metric is explicitly present in a response.

- **Suppression and inactivity are risk signals, never confirmed statuses.** A glance-view
  or net-PPM decline (1P), or a sessions or Buy Box win-rate decline (3P), indicates *risk*
  of suppression or inactivity. Say "at risk," never "suppressed" or "inactive." This is an
  early warning, not a substitute for checking the ASIN directly in Vendor or Seller Central
  — say that too.
- **Never state a campaign is paused, active, or archived.** State is not confirmed
  readable. Frame every such item as a candidate to confirm.
- **Flag stale data.** Report the latest date each figure actually covers, and call it out
  when a number rests on a refresh more than a few days old. The advertising refresh cadence
  is undetermined — treat that as a reason to state the coverage date, not to stay silent.
- **Year-over-year comparisons carry a known accuracy caveat.** Year-ago comparisons align
  on exact calendar dates rather than comparable Sunday–Saturday retail weeks, which has
  produced figures that disagreed with a customer's agency. Warn about it wherever the run
  makes a year-over-year read, and prefer a same-weekday-aligned window when precision
  matters.
- **Compute comparisons from separate calls** and never blend two different windows into one
  figure. Chunk at 31 days; history reaches back about 14 months and no further. If a
  request needs more, say so instead of extrapolating.
- **Separate actuals from estimates.** Connected-account actuals and market estimates are
  different classes of number. Label which is which, and never sum across them.
- **Don't mix 1P and 3P vocabulary.** Glance views and net PPM are Vendor Central; sessions
  and Buy Box win rate are Seller Central. Use only the set matching the resolved platform.
- **Revenue equals units times price.** When revenue and units move in different directions,
  identify whether volume or price explains it.
- **Rank by dollars, not percentages.** A 400% ACoS on $12 of spend is not the week's
  problem. Sort every list by money at stake.
- **High impressions with low clicks is a relevance or listing problem**, not a bid problem.
  Don't recommend a bid change for it.
- **Never invent a metric name, a report name, or a UI path.** Use the field names the
  response returns. If the user's term has no matching field, say the field was not available
  rather than mapping it to something adjacent.
- **State when data is insufficient.** Use:
  "Available data does not indicate the underlying cause."

## Presentation

This skill owns the run's **structure** — which sections appear, in what order, and what
each contains. It does **not** define visual styling. Defer the headline callout, palette,
charts, growth pills, KPI cards, and evidence-table formatting to the
`jungle-scout-visualizer` skill.

Produce a **static report** with the data already pulled and baked in: a single
self-contained HTML artifact when the environment supports it, otherwise clean markdown in
the same section order. Lead with what needs a decision today, not with the methodology.

1. **Run header** — cadence, brand, platform, product lines, marketplace, the window
   covered, the latest date the data actually covers, and the thresholds in force.
2. **Needs a decision today** — the consolidated action list, highest dollars first, each
   row carrying target, current value, proposed value, evidence, and where to apply it.
   This is the section the user reads first; everything below is support.
3. **Catalog status** — priority-ASIN risk table, threshold breaches, inactivity risk, the
   revenue-down-traffic-flat set, and inventory cross-check. Risk language throughout.
4. **Advertising effectiveness** — the weightiest section. Account pace against budget;
   wasted spend; ACoS breaches; campaign-type allocation; prune list; scale list; new-title
   routing; new keyword candidates for Experimental; re-enable candidates. Each list is
   decision-ready with reasons.
5. **Market position** — own trajectory versus category, competitor share movement, what is
   driving the biggest mover, new entrants. Light at Pulse cadence, full at Deep dive.
6. **Automation candidates** — recurring changes that should become a Rulebook, ABC,
   Dayparting, or Keyword Harvesting profile in the Cobalt app instead of a weekly manual
   pass. Omit when nothing recurred.
7. **Paste-ready status table** — one stable, unchanging column order for the spreadsheet
   workflow. Keep the schema identical run to run so it can be appended without rework.
8. **Data coverage and gaps** — source tools, actuals versus estimates, windows and chunking,
   coverage dates, which documented gaps affected this run, and what could not be checked.

If a section's data is missing, say so plainly rather than inventing values — honesty about
the gap beats a tidy-but-wrong widget.

## Markdown Fallback Structure

When HTML/artifacts are unavailable, produce this text structure unless the user requests a
different format.

```markdown
# [Brand] Amazon Command Center — [Cadence] Run, [date]

Scope: [product lines] · [platform] · [marketplace] · Window: [window]
Data covers through: [latest date in data] · Thresholds: decline [X]%, ACoS [X]%, spend floor $[X]

## Needs a Decision Today

[Ranked by dollars at stake. One row per action: what, current, proposed, why, where to apply.
Read-only reminder: apply these in Cobalt or the Amazon Ads console.]

## Catalog Status

[Priority-ASIN risk table. Threshold breaches with the traffic metric alongside. Inactivity
risk. Revenue-down-traffic-flat set with buy-box evidence. Inventory cross-check. Risk
language only — never "suppressed."]

## Advertising Effectiveness

**Pace:** [spend to date vs. budget target, % of period elapsed]

[Wasted spend — campaigns above the spend floor with no attributed sales.]
[ACoS breaches — above threshold, ranked by dollars.]
[By campaign type — allocation across the user's campaign types, or a note that the type
breakdown was not possible.]
[Prune — targets that spent and did not convert.]
[Scale — performers with headroom.]
[New titles to route — ASIN, proposed campaign type, seed keywords.]
[New keywords for Experimental — term, volume, trend, ease to rank, current SoV.]
[Re-enable candidates — confirm current state before acting.]

## Market Position

[Own trajectory vs. category. Competitor share movement. What's driving the biggest mover.
New entrants.]

## Automation Candidates

[Recurring changes better encoded as a Rulebook, ABC, Dayparting, or Keyword Harvesting
profile. Omit if none.]

## Status Table

[Stable column order for the spreadsheet workflow — identical every run.]

## Data Coverage and Gaps

[Tools used. Actuals vs. estimates. Windows and chunking. Coverage dates. Which documented
gaps affected this run. What could not be checked.]
```

## Writing Style

- Lead with implications, then cite metrics.
- Open with what needs a decision, not with what was fetched.
- Use concise business language without dramatic phrasing.
- Use specific numbers, and name the ASIN, campaign, or keyword. "A campaign is overspending"
  is useless; "Campaign X spent $1,240 in 7 days with no attributed sales" is usable.
- Every recommendation carries its reason and its evidence in the same row.
- Use decision vocabulary, never execution vocabulary: *flagged for pausing*, *recommended
  bid*, *proposed budget*, *candidate to confirm*, *apply in Cobalt*.
- Label risk as risk. Label estimates as estimates. Label a join as a join.
- Keep the paste-ready table's schema fixed across runs even when a column is empty.

## Fallbacks

- **No connected Seller/Vendor Central or Advertising account** — the advertising and actuals
  tools cannot run. Fall back to market-estimate tools (`analyze_products`, `analyze_brands`,
  `analyze_categories`, `query_sales_estimates`) plus `get_keyword_sov` sponsored metrics as
  the only advertising-adjacent signal available, and disclose plainly that spend, ACoS, bid,
  and budget figures were not available.
- **No campaign-type naming convention supplied** — report at campaign level and state that
  the type breakdown was not possible. Do not guess types from campaign names without the
  user's convention.
- **Campaign state unknown** — present pause and re-enable lists as candidates to confirm.
  Never assert current state.
- **A window exceeds the cap** — chunk into 31-day calls and stitch the result, noting the
  chunk boundaries. If the request reaches past about 14 months, say the history is not
  available rather than extrapolating.
- **An announcement-sourced tool rejects a parameter** — read the error, inspect the tool
  definition, and correct the call. Do not retry a guessed parameter name.
- **Actuals unavailable but estimates are** — continue with estimates, relabel every affected
  figure, and weaken the conclusions that rested on actuals.
- **A pull is empty** — say so in that section. Do not fill the slot.
- **First run with no history** — run it as a baseline, state that no prior run exists for
  comparison, and record the resolved inputs for next time.

## Next Steps

After delivering the run, don't just stop. Propose **2–3 concrete follow-ups grounded in what
this run actually surfaced**, and ask which to pursue. If the environment supports a
multiple-choice prompt or form, present the options that way; otherwise list them and ask.
Draw from:

- **Work the biggest wasted-spend campaign** — pull its full target-level detail and produce a
  line-by-line prune and negative-keyword list.
- **Build the new-title routing pack** — for the ASINs with no advertising activity, assemble
  proposed campaign type, seed keywords, and match types ready to enter.
- **Expand the Experimental keyword slate** — run `analyze-category-keywords` on the category
  to widen the candidate pool beyond the current ASIN seeds.
- **Diagnose the catalog decline** — take the sharpest decliner and separate traffic, price,
  and buy-box causes.
- **Deep-dive the competitor gaining most share** — hand off to `share-diagnosis`.
- **Encode a recurring change as an automation** — turn a rule the user applied again this
  week into a Rulebook, ABC, Dayparting, or Keyword Harvesting profile.
- **Set the next run** — confirm the cadence and lock the inputs so the next run is directly
  comparable.

Make each offer specific to the finding (e.g. "work Campaign X — $1,240 spent, no attributed
sales in 7 days"), not generic. Then carry out whichever the user picks.

## Reference files

- `references/mcp-tools.md` — the tool inventory with provenance, verified parameters and
  response fields for the repo-verified tools, marketplace casing rules, the 31-day window
  and 14-month history caps, the removed period-comparison behavior, and the year-over-year
  accuracy caveat. **Read before the first call.**
- `references/advertising-runbook.md` — the advertising workflow in full: the ten recurring
  operator tasks mapped to what the connector can and cannot do, campaign-type allocation,
  the pause / re-enable / prune / scale / bid / budget decision rules, ACoS and pacing math,
  the change-list schema, and when to route a recurring change to a Cobalt automation.
  **Read before Focus Area 2.**
- `references/cadence-runbook.md` — the per-cadence checklists: the literal questions each run
  answers, in order, with the tool for each and the degraded path when it is unavailable.
  Read when starting a run.
