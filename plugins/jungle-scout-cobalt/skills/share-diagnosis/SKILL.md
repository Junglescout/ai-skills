---
name: share-diagnosis
description: "Use whenever the user asks about share movement, competitive position, or brand performance against a category — even if they don't use the word 'share'. Trigger phrases include: 'why are we losing ground', 'who's catching up to us', 'why did we gain share', 'what happened to our position', 'decode this shift', 'am I winning this market', 'why is [brand] declining', or any question where a brand's Amazon performance is framed against a category or competitor. Also trigger when the user asks about a competitor gaining momentum without explicitly framing it as a share question. Diagnoses why share moved, sizes the dollar impact, identifies whether the cause is structural or fragile, and points to where to focus. Delivers a client-ready narrative: a verdict, the named failures behind it, the dollar impact, and the areas to focus. Presentation styling is deferred to the jungle-scout-visualizer skill."
---

# Share Diagnosis

Diagnose why a brand's Amazon share moved — where, why, how durable, what it's worth — and what to do about it, using Jungle Scout MCP data. The deliverable is a story, not a data dump: a one-line verdict, the named failures behind it, what it costs, and a sequenced set of recommended actions.

This skill runs the full Amazon Growth Cycle (Assess → Diagnose → Act). The four root-cause lanes below are the analytical *engine* — they guarantee completeness and consistency. But the four lanes are not how you *tell* it: the narrative leads with a thesis and 2–3 named failures (see Output). Assess frames the picture, Diagnose does the analytical work across the lanes, and Act closes with the areas to focus, ordered by leverage. Focus areas are in scope; carry the analysis all the way to where the customer should concentrate — but leave the scheduling to them (no timeframes).

This skill owns the **analysis method and the structure** of the diagnosis — which steps run, what each surfaces, and the section order of the output. It does **not** define visual styling: hand all palette, callouts, charts, growth pills, and tables to the `jungle-scout-visualizer` skill, which this skill depends on.

**Before starting:** read `references/worked-example.md` — it shows what a full deep-dive looks like end-to-end with real data, including how the three deep-dive steps (SOV by intent, review velocity, launch cohort) interact to produce a diagnosis that brand-level data alone cannot reach.

---

## The four root-cause lanes

Every diagnosis is organized around the same four lanes, taken from the Growth Cycle. This is what makes the analysis consistent across brands and categories: the structure is identical every run, even when the data underneath isn't.

| Lane | The question it answers | Signals |
|---|---|---|
| **Awareness** | Are shoppers finding us? | Keyword trends, share of voice, ad presence, product innovation / new launches |
| **Conversion** | When found, do they buy us? | Pricing, PDP content, assortment / attributes, programs (Prime, S&S), reviews & ratings |
| **Buy box** | Are we winning the sale we should? | Pricing / repricing, MAP enforcement, unauthorized sellers, stockouts |
| **Sustainability** | Is the position profitable? | Margin health, ad efficiency, TACOS trends |

**Coverage varies by lane, by design.** Jungle Scout data covers Awareness fully; Conversion, Buy box, and Sustainability each include metrics that are either observable on the public listing or private to the brand until its own account is connected. Every lane appears in every diagnosis with an explicit coverage tag — what's measured directly, what's inferred, and what's one integration step away. Labeling coverage is more useful than leaving it implied.

Each datapoint (not just each lane) gets one of four coverage tags. The distinction that matters: **"Requires integration" is a claim to be earned, not a default for anything inconvenient.** Before tagging something Requires-integration, confirm no proxy and no public read exists. The most common shortcut to avoid: tagging a datapoint un-assessable and then never running the check that was available all along.

- **Direct (JS)** — the JS sales-estimate tools answer it (revenue, share, SOV, reviews, price, launch cohort).
- **Inferred (proxy)** — JS answers it indirectly through a proxy. *If a proxy exists, you MUST run it* — this tag is not permission to skip. Examples: stockout (weekly units collapsing while realized price rises and buybox max spikes), sponsored intensity (sponsored SOV), seller count (analyze_sellers). Flag the claim as inferred; a strong signature (e.g. the stockout price/volume divergence) can still be high-confidence.
- **Observable, not pulled** — publicly visible on Amazon but outside the loaded tool set: PDP content (title, bullets, images, A+), Prime / Subscribe-&-Save badges, coupons, listing status. This is a *gap in this pull*, not an integration block — note it and, if it matters to the diagnosis, go get it (web fetch the listing, load another tool) rather than writing it off.
- **Requires integration** — the metric is private *to the brand*, but JS reads it directly once the brand's own Seller/Vendor Central or ad account is connected. So this is not "permanently dark" — for a customer analyzing their own brand it's one onboarding step from Direct. It only stays unavailable when the focal brand is one you don't own (a competitor, or a client whose account isn't connected), because the org-scoped tools return only the connected org's own catalog. Genuinely in this tier: margin/cost, true conversion rate & traffic (Brand Analytics), buy-box win rate and per-seller offer detail (`analyze_competitive_offers` — connected owned catalog only), MAP thresholds, ad spend / TACOS / ad efficiency (ad console). State whether it's unavailable because no account is connected (fixable) or because the brand isn't owned (structural for this engagement).

A datapoint can therefore sit in different tiers depending on *who the focal brand is*. Buy-box win rate is the clearest example: **Direct (JS)** when diagnosing the customer's own connected brand, **Observable/Inferred** (public featured-offer holder + buybox price) when diagnosing a brand you don't own. Always resolve which case you're in during scoping (question 1 + 6) before tagging.

Rule of thumb before writing any "Requires integration": ask "is there a JS proxy?" (→ Inferred, run it) and "is it visible on the listing?" (→ Observable, consider fetching it). Only if both are no does the tag hold.

Default coverage by datapoint (overridable per session based on confirmed data access):

| Lane | Direct (JS) | Inferred — run the proxy | Observable, not pulled | Requires integration |
|---|---|---|---|---|
| Awareness | SOV by intent, keyword trends, launch cohort, sponsored SOV | — | — | — |
| Conversion | pricing, reviews/ratings, assortment/attributes | — | PDP content quality, Prime / S&S badges, coupons | true conversion rate & traffic |
| Buy box | seller count & price (analyze_sellers); **buy-box win rate when the focal brand's own account is connected** (analyze_competitive_offers) | **stockout** (units↓ + price↑ + buybox spike), seller proliferation, featured-offer holder & buybox price (any brand) | listing/availability status on the page | buy-box win rate & per-seller offer detail for **non-owned** brands, MAP thresholds, authorized-vs-not identity |
| Sustainability | — | ad *intensity* via sponsored SOV | — | margin, ad spend, TACOS, ad efficiency |

---

## Scoping

Ask before diagnosing. Send all six questions in one message — if the environment supports a structured input form or a multiple-choice prompt, present one; otherwise batch them as plain text. Do not run anything until the user responds or says "just run it."

1. **Brand & category.** Brand name plus Amazon category, or representative ASINs to resolve the competitive set. Ask explicitly whether the brand has sub-brands, parent companies, or alternate names — brands like "Schylling" and "Needoh" are the same entity, and analyzing them separately will systematically understate position and make competitors look stronger than they are.

2. **Time window.** Default 90 days vs. prior 90; YoY same-quarter for seasonal categories; event-anchored if relevant ("since Prime Day").

3. **Direction.** Gain / loss / unsure. If unsure, Step 0 detects before diagnosing.

4. **Sub-scope.** Full sweep, or zoom on a specific tier/segment/competitor. Default to full sweep.

5. **Depth.**
   - **Quick overview** (~10–15 min, 5–10 queries) — detect, decompose, localize, then a brand-level pass across the four lanes at whatever coverage is available, and size.
   - **Deep dive** (~30–45 min, 15–30 queries) — adds the lane deep-dives: SOV by keyword intent (Awareness), review velocity trended (Conversion), launch cohort split (Awareness), ASIN-level decomposition, driver-magnitude analysis.
   - Default: run quick overview first, then offer to deep-dive on the 1–2 most consequential lanes.

6. **Data access.** Customer integration (Seller Central / Brand Analytics / ad console) or Jungle Scout data only? This directly sets the coverage tags: with integration, Conversion / Buy box / Sustainability upgrade from Requires-integration toward Direct. Without it, those lanes stay inferred or unassessable and every affected claim is flagged.

If user says "just run it": defaults are 90-day window, full sweep, quick overview, no integration. Surface assumptions in the output.

---

## Phase A — ASSESS

Understand what's happening today before diagnosing why. This phase produces a standard snapshot and a single framing hypothesis, and it is identical in shape every run.

### Step 0 — Detect

Use `analyze_brands` and `query_sales_estimates`. Compute share at the requested scope and confirm the movement is real.

Confirm with ≥2 of:
- **Magnitude**: ≥0.5pp WoW, ≥1pp MoM, ≥1.5pp QoQ (adjust for category volatility)
- **Persistence**: same direction for 3+ periods
- **Statistical**: >2σ of trailing 12-week volatility
- **Scope check**: if total share is flat, scan subcategories for masked compensating movement

If fewer than 2 criteria are met: report "within normal volatility" and stop.

**Quality flags** — run regardless of depth, because bad reads downstream are expensive:

- Subcategory revenue +>50% YoY or share moving >15pp → likely taxonomy drift, not competitive movement
- Revenue base under ~$500K or fewer than 5 brands tracked → noise / survivorship risk
- Spot-check top 10 ASINs: if >30% don't match the leaf name, the leaf is noisy
- ASP range >5x within one leaf → competitive substitution unlikely; split by tier
- Brand count change >25% YoY → suspect taxonomy reclassification

When flags fire, surface them in ASSUMPTIONS and weaken affected claims. These patterns are common — don't treat the leaf as clean by default.

### Step 1 — Decompose share math

Three components: your absolute revenue change, category total revenue change, competitor share changes (full competitive set, not just top 1).

Which story is true:
- **Declined absolutely** → ASIN-level revenue equation is the root; share is a downstream symptom
- **Held flat, market grew without you** → competitive or structural problem
- **Grew slower than market** → both; weight by magnitude

For losses, trace where share *went*. For gains, trace where it *came from*. Both directions matter.

**Multi-category brands:** aggregate share against the brand's core footprint — categories where it holds ≥2%. Exclude the long tail; it dilutes the denominator without reflecting competitive reality. Always report both brand-wide revenue change and core-footprint share change.

**Share held, dollars lost:** a brand can hold share while losing meaningful revenue if the category is contracting. Surface the absolute revenue gap separately from share movement, or readers see stable share and miss the dollar exposure.

### Step 2 — Localize

Decompose movement by subcategory, price tier, product attributes, and variation type to find where movement concentrates. A brand-level share shift that's actually concentrated in one price tier requires a tier-specific response, not a portfolio-wide one.

If attribute data isn't directly available, use keyword clusters or top-N competitor product analysis as a proxy.

### Assess snapshot (emit before diagnosing)

Close Phase A with a fixed snapshot block so the opening reads the same every time:

```
ASSESS SNAPSHOT
Category:      TAM $X, growing Y% YoY
Focal brand:   $X revenue (Zpp share), growing Y% — [outpacing / lagging] category
Competitive set: [top 3–5 movers, each with share Δ]
Concentration: movement sits in [tier / subcategory / segment]
```

Then state one **framing hypothesis** — the single sentence that Diagnose will test, e.g. "Share held flat while the category grew; the loss looks concentrated in the $10–$15 tier and among category-keyword shoppers." This is the Goal-Setting bridge in miniature: it points Diagnose at where to focus rather than sweeping everything equally.

---

## Phase B — DIAGNOSE

Identify the root cause across the four lanes. Every diagnosis walks all four, each datapoint carrying its own coverage tag. Where a datapoint is genuinely Requires-integration it appears with a one-line "not assessable — needs X" note rather than being dropped; but first apply the two-question test (proxy? public listing?) so you don't mislabel an assessable datapoint as gated.

In **quick overview** mode: one brand-level pass per lane, name a primary cause and 1–2 secondary contributors, then size. In **deep dive** mode: run the lane deep-dives below before sizing.

For each lane, decode the full competitor set. For losses, focus on what share recipients did differently; for gains, focus equally on what you did AND what competitors failed to do — an inherited gain is fragile regardless of size.

### Lane 1 — Awareness  ·  *Are shoppers finding us?*

Coverage: **Direct (JS)** in most sessions. Signals: keyword trends, SOV by intent, ad/sponsored presence, product innovation (new launches).

**Quick pass:** competitor new-ASIN launches, sponsored presence on key terms, keyword trend direction.

**Deep dive — SOV by keyword intent (highest-signal step in the whole skill).** Share of voice is not one number. A brand can dominate branded keyword SERPs while losing category keyword SERPs — structurally different problems requiring different responses.

- **Branded keywords** — terms containing the brand/product name. Loss here means brand substitution is underway (serious). Stability means brand equity is intact even if discovery is suffering.
- **Category keywords** — generic terms shoppers use when they don't yet know what they want. Loss here means competitors are capturing discovery-stage shoppers first — often the more urgent signal, and the more addressable through paid presence.

Procedure:
1. Identify 5–8 keywords split across intent types. `search_keywords_by_asin` on the brand's top 3 hero ASINs for branded terms; `search_keywords_by_keyword` on the category name for category terms. Note any high-volume terms containing competitor brand names — those reveal whether competitors have built enough equity to generate direct search demand.
2. Pull monthly SOV history (6–12 months) with `get_keyword_sov` using `equal_weighted_organic` and `equal_weighted_sponsored`. Pull the two keyword groups as separate calls — a combined call obscures the intent segmentation that drives the diagnosis.
3. For each group, compare the focal brand's organic SOV trend against the top 3–4 gaining competitors.

Interpreting:
- Branded organic stable + category organic collapsing → equity intact, discovery broken. Fix is paid presence on category terms.
- Branded organic falling → more serious; check whether competitors are buying branded terms (spend-dependent, stoppable) or building genuine recognition (structural).
- Competitor winning sponsored but organic rank not improving → spend-dependent, fragile.
- Competitor winning sponsored AND organic rank improving month-over-month → spend is building rank; becomes structural in 2–3 quarters. Changes the durability call.
- A **presence collapse** — organic SOV cliff, or a hero ASIN's days-present dropping sharply — is NOT self-evidently a competitive loss or a listing event. It triggers a mandatory **availability differential** before any other conclusion. Run these JS-assessable checks first, in order:
  1. **Stockout (check this first — it's the most common cause and needs no integration).** Pull the ASIN's weekly units/revenue. The stockout signature: units/day falling toward zero *while realized price rises and the buybox max spikes far above normal* (the primary offer vanished; only marked-up third-party offers remain). Progressive volume decay + inflating price = a sustained out-of-stock, and the organic collapse is downstream of it (Amazon demotes out-of-stock items). If this fires, inventory/supply is the root cause and the SOV story is a symptom — do not diagnose "competitive erosion" or "listing event."
  2. **Relist / restructure.** Units move to a new ASIN at normal price while the old one zeroes. First-available dates on the new ASINs are recent; review equity resets.
  3. **Suppression / policy flag.** Units and presence both drop with no price spike and no replacement ASIN — often a single-week cliff.
  4. **Rank loss to competitors.** Presence fades gradually, units hold or shift to named competitors at comparable price.
  Only after stockout and relist are ruled out does a presence cliff read as competitive or suppression-driven. The tell that separates them is the price/volume relationship, so always pull it.

Output: a 2×2 SOV summary (branded/category × organic/sponsored) with trend direction per brand, plus which competitors drive each type of movement.

**Deep dive — launch cohort split.** `analyze_products` with `group_by: launch_cohort` splits each brand's revenue into new SKUs (launched within the window) vs. existing. Run for focal brand and top 3–4 competitors.

Share movement that looks like competitive displacement is often a product-expansion asymmetry — competitors launching and capturing faster while the focal brand stays put. Surface:
- New SKU revenue as % of total (>30% = aggressive expansion; <10% = catalog-dependent)
- Review count on new SKUs — the launch-execution signal. Competitor new SKUs with high review counts means their launch process works; focal-brand new SKUs with near-zero reviews despite multiple launches means listing quality, traffic, or review acquisition is failing.
- New SKU average price — which tier competitors are entering with new launches.

The launch cohort split is frequently the diagnosis-changing finding: it reframes "we're being outcompeted on existing products" into "we have a launch execution problem" — a different and more correctable diagnosis.

### Lane 2 — Conversion  ·  *When found, do they buy us?*

Coverage: **Mixed.** Direct (JS): pricing, reviews & ratings, assortment / attributes. Observable but not in these tools: PDP content quality and Prime / S&S badges — publicly visible on the listing, so a gap in this pull, not an integration block (web-fetch the listing if it's material). Requires integration (genuinely private): true conversion rate and traffic. Tag each accordingly; don't blanket the lot as "needs integration."

**Quick pass:** price position vs. the gaining set, rating gaps on comparable products, obvious assortment/attribute gaps (from Step 2 localize).

**Deep dive — review velocity (trended).** Static review counts hide trajectory. A brand with 5,000 reviews adding 100 this quarter is losing ground to one with 400 adding 300. Pull `variant_review_count_sum` trended weekly via `query_sales_estimates` for the focal brand and top 3–4 competitors over 12–18 months; compute quarterly addition rates.

The critical sub-metric is new SKU review velocity: a new SKU adding 100+ reviews in 90 days is likely to rank organically within 2 quarters; one stalling at <30 reviews in 90 days stays invisible regardless of product quality.

*Cross-lane note:* review velocity is filed here (reviews & ratings are a Conversion signal) but it also qualifies **Awareness durability** — it determines who wins the ranking flywheel. Use it to grade the Awareness SOV calls: a competitor winning sponsored SOV is a fragile threat if review velocity is low, and a structural threat if velocity is high (they'll own organic rank in 2–3 quarters regardless of spend).

*Programs & PDP:* Prime/S&S badges and PDP content are on the public listing — if they're material to the diagnosis, fetch the listing rather than writing them off as "needs integration." Only *true conversion rate* is genuinely integration-gated; don't infer it from JS alone.

### Lane 3 — Buy box  ·  *Are we winning the sale we should?*

Coverage depends on whether the focal brand is one the org owns and has connected. JS Direct: seller count and price (`analyze_sellers`, any brand). **Buy-box win rate is Direct (JS)** via `analyze_competitive_offers` / `analyze_seller_product_offers` (they return `buy_box_win_pct` per seller) — *but only for the connected org's own catalog*; call them on a brand you don't own and they error ("only available for products your connected account owns"). Inferred proxies you must run: stockout (weekly units/revenue + buybox price), seller proliferation, and the public featured-offer holder + buybox price (a point-in-time buy-box read available for any listing, even non-owned). Requires integration / not available: continuous buy-box win rate and per-seller offer detail for **non-owned** brands, MAP thresholds, authorized-vs-unauthorized identity.

The practical split: if you're diagnosing the customer's own brand, connect their Seller/Vendor Central and buy-box win rate becomes Direct — don't tag it as gated. If you're diagnosing a competitor or an unconnected brand, you can't get the measured win rate, but you can still read who holds the featured offer and at what price, and infer buy-box pressure from that plus the stockout signature.

**Quick pass:** scan the focal brand's hero ASINs for stockout signatures and for a rising seller count (a proxy for unauthorized sellers eroding the buy box). Both are inferred — flag them.

**Stockout is Inferred, not Requires-integration — never park it.** The single most common cause of a hero ASIN losing revenue and organic rank is running out of stock, and it is fully JS-inferable without Seller Central: pull weekly units/revenue and buybox price, and look for volume decaying toward zero while realized price rises and buybox max spikes far above the normal price (only marked-up third-party offers left). This is the *first* thing to check whenever Awareness shows a presence/SOV collapse (see the availability differential in Lane 1) — do not defer it to the "needs integration" bucket. Buy box *win rate* needs integration; buy box *loss to a stockout* does not.

When the focal brand's own account is connected, pull buy-box win rate and MAP flags directly (Direct). Otherwise state plainly which reason applies: "Win rate isn't measurable here because the account isn't connected" (fixable via onboarding) or "…because this brand isn't in our catalog" (structural — use the public featured-offer holder and buybox price plus the stockout signature instead, which is a high-confidence read even without integration)."

### Lane 4 — Sustainability  ·  *Is the position profitable?*

Coverage: **one inferable signal, the rest integration-gated.** Inferred (run it): ad *intensity* via sponsored SOV — whether the brand advertises at all and its share of sponsored placements. Requires integration (private): margin, ad spend, TACOS, ad efficiency. So the lane is never fully blank even JS-only — you can always say whether there's a paid presence, just not whether it's profitable.

**Quick pass:** the only JS-visible read is directional — heavy sponsored presence (from Lane 1) with weak organic backing implies spend-dependent share, which is a sustainability risk even though the actual TACOS is unknown. Mark it inferred.

State plainly when unassessable: "Margin health, ad efficiency, and TACOS require the ad console; not assessable this session." Do not drop the lane.

---

### Step 3.6 — Driver decomposition (cross-lane synthesis)

Pull the lanes together. Decompose the observed delta into named drivers with magnitude, confidence, scope, and durability. Tag each driver with the lane it belongs to. Drivers should approximately sum to the observed delta; name residual rather than hiding it.

For each candidate driver, apply four qualifying tests:
- **Differentiation** — did the brand do this differently than competitors? If everyone moved the same lever, allocate ~0 magnitude.
- **Tier alignment** — for displacement claims, do ASP ranges overlap? No overlap = coincident, not causal.
- **Falsifiability** — what evidence would disprove this driver? If you can't say, confidence is low.
- **Mix vs. action** — recompute the metric on existing ASINs only. If the signal disappears, it's product mix shift, not the original framing.

| Driver | Lane | Magnitude | Confidence | Scope | Durability |
|---|---|---|---|---|---|
| [Named driver A] | Awareness | $X (Y%) | high | [tier / competitor / segment] | structural |
| [Named driver B] | Conversion | $X (Y%) | medium | [tier / competitor / segment] | fragile |
| Residual | — | $X (Y%) | — | — | — |
| **Total observed** | | **$X (100%)** | | | |

If residual >20%, the diagnosis is incomplete — dig further or flag it explicitly.

### Step 3.7 — ASIN-level decomposition

For each concentrated sub-scope, split the brand's delta into:

| Bucket | Δ revenue | % of total delta |
|---|---|---|
| New launches (first available ≥ comparison start) | $X | Y% |
| Refresh (new ASIN replacing a declining predecessor in the same line) | $X | Y% |
| Existing ASINs (in both periods) | $X | Y% |
| **Total** | **$X** | **100%** |

Classify new launches by strategic intent:
- **Line extension** — new size, color, minor variant. Revenue, but doesn't address a segment shift.
- **Adjacent entry** — same form factor repositioned toward the growing segment. Often a relabel, not a true pivot.
- **Genuine new segment** — form factor or product type the brand didn't previously offer.

Only genuine new segment entries count as a counter-move to substitution-driven loss.

### Step 3.8 — Counter-move audit (conditional)

Run when all three hold: loss diagnosis; a meaningful offsetting bucket from 3.7 (new-launch Δ ≥20% of the declining bucket); and demand has shifted to a definable segment. When triggered, the question is whether the response was *competitive* — cross-join the brand's genuine new segment entries against the top 2–3 recipient brands' winning launches (launch timing, price tier, SKU breadth, BSR rank, sub-segment coverage) and size the missed opportunity:

```
Missed opportunity ≈ (median peer outcome per SKU in segment × SKUs brand could plausibly have launched) − brand's actual capture in segment
```

---

## Phase C — SIZE

Three sizings:

1. **Realized** — dollars surrendered (loss) or captured (gain) in the comparison window.
2. **Forward exposure** — extrapolate the observed share-Δ rate over 4 / 12 / 52 weeks. Use a range when trajectory is noisy.
3. **Recoverable / defensible** — recapturable revenue for losses, or at-risk revenue for gains if the driver weakens.

See the Impact Estimation Methods table at the bottom.

---

## Phase D — ACT (focus areas)

Close with where to focus — the payoff, not a handoff. Translate each diagnosed driver into a focus area, drawing the action families from the lane the driver sits in:

| Diagnosed lane | Action families |
|---|---|
| Awareness | Win SoV, keyword automation, product innovation / launch remediation, external traffic (DSP / influencers / TikTok) |
| Conversion | Pricing / profitability, PDP optimization, assortment / attributes, program enrollment, review acquisition |
| Buy box | Automated repricer, MAP compliance, unauthorized-seller enforcement |
| Sustainability | Media planning, retail media optimization, opportunity discovery |

Frame these as areas to focus, not a dated action plan. Discipline that keeps them honest (not a generic best-practices list):

- **Every focus area traces to a diagnosed driver.** If it doesn't map to something in the driver-decomposition table, cut it.
- **Order by leverage, not by calendar.** Lead with the highest-leverage, highest-confidence area — the one that addresses the biggest driver with the most certainty. Do not attach timeframes, deadlines, or sequencing language ("same-week," "next quarter," "start now," "first signal in N months"). Owning the *why it matters* and *how to tell it's working* is the skill's job; committing the customer to a schedule is not.
- **Each area carries three things:** the specific focus, the expected recovery or impact (tie to the sizing), and a watch-metric (the one number that shows it's working). No dates.
- **Name the root-cause area as the structural one** — describe it as the deeper fix versus the quicker recapture, in leverage terms, without putting a clock on it.
- Requires-integration lanes still generate a focus area: "connect Seller Central / ad console" *is* an area, because you can't fix what you can't see.

---

## Output

### Deliverable by depth

- **Deep dive → one self-contained HTML report** (the standard deliverable) when the environment supports artifacts or file output; otherwise clean markdown with the same section order. It is downloadable, iterable, and holds the full narrative plus the evidence appendix.
- **Quick overview → inline summary** (optional), rendered as a widget via `visualize:show_widget` where that is available. A scannable glance in-chat; offer to upgrade to the full report.

Never silently downgrade a deep dive to a widget or a chat summary — neither can carry the story or the evidence, and neither is downloadable.

### Tell it as a story, not a data dump

The most common weak deliverable presents the four lanes as a grid of findings — complete but inert. The four lanes are the *engine*; they are not the *narrative*. Lead with a verdict and 2–3 named failures, thread the numbers through the argument, and end on the areas to focus. Study `references/exemplar-narrative.md` — it is the reference standard for structure, voice, and pacing.

The narrative arc (this is the section order of the artifact):

1. **Verdict headline + hero argument.** The `<h1>` is a claim, not a label — "Category discovery is broken," not "Share diagnosis." Follow with 2–3 sentences that argue the whole case and lead with the counterintuitive reframe. The single best pattern: state the paradox in numbers. "The brand grew +X%. The category grew +Y%. That gap — not a competitor — is the diagnosis." If there's one number that reframes everything, it goes here.

2. **The diagnosis — named failures.** Don't open with a lane grid. Synthesize the drivers into **2–3 named failures** (e.g. "SERP collapse," "branded-term infiltration," "launch-execution gap"), each with a one-line thesis. State explicitly what the surface read *looks* like and what it *actually* is ("what looks like competitive displacement is actually a product-expansion asymmetry"). This is the reframe that makes the analysis feel like insight rather than reporting.

3. **One section per major failure**, in priority order. Each section: a numbered kicker ("02 / Share of voice"), a titled phrase, a **lead sentence that makes a claim** (not a chart caption), then the evidence — a callout that says what the number *means* ("The critical signal: category organic SOV fell from 64% to 10% in four months"), and a chart whose subtitle states the takeaway. Numbers live inside sentences, not in naked tables.

4. **Sizing as three horizons.** Already lost (realized) / at risk if nothing changes (forward exposure) / immediately recoverable. Frame each as a sentence, not just a figure — the horizon is the story.

5. **Focus areas — where to concentrate.** The payoff section. Present as areas to focus (Phase D), ordered by leverage — highest-leverage, highest-confidence first. Each carries the specific focus, expected recovery, and a watch-metric. No timeframes, deadlines, or sequencing language: frame the root-cause area as the deeper structural fix versus the quicker recapture, in leverage terms, not on a clock. This is the section the reader acts on; make it the strongest, not an afterthought.

6. **Evidence appendix.** *Now* the dense tables live here — competitive set with share deltas, price-tier decomposition, driver-decomposition (lane-tagged), ASIN-level detail — plus the assumptions/coverage block. The four-lane coverage lives here as a completeness check: a compact table showing each lane's coverage tag and one-line finding, so coverage gaps stay visible without leading the story. This section can be data-dense; the sections above cannot.

Rules of voice: prose carries the argument; tables are reference, pushed to the appendix. Every chart has a takeaway subtitle. Callouts state meaning, not restated numbers. No naked metric grid above the appendix. Round every displayed number.

### Charts that earn their place

A deep dive is one of the rare cases where several charts each earn their place, so the visualizer's "one good visual beats three" default gives way to this structure. Each chart lives inside the failure section it evidences — never as a standalone dashboard:

- **SOV by keyword intent** (Awareness section) — branded organic + sponsored over one row, category organic + sponsored over the next. Monthly, 6–12 months. Focal brand in the focal color, competitors receding to gray; any competitor that has recently overtaken the focal brand takes the flag color.
- **Review velocity** (Conversion / durability section) — cumulative review count over 12–18 months, all brands. The signal is slope, not level: 400 reviews on a steep line beats 2,000 on a flat one.
- **Launch cohort comparison** (Awareness / launch-execution section) — focal brand vs. competitors combined, showing new-SKU revenue, new-SKU review count, new-SKU ASP, and new-as-% of total, with signal pills.
- **Keyword demand** (Awareness section) — top 8–10 keywords from the brand's hero ASINs by search volume, with quarterly trend and intent label (branded / category / competitor-branded). Flag high-trend terms the brand isn't bidding on.

### House style

Hand all styling to the `jungle-scout-visualizer` skill, and read its `references/visuals.md` before the first chart — it owns the palette (light + dark), the Chart.js templates, growth and signal pills, the evidence-table treatment, and the formatting helpers. Don't define a separate palette or hardcode hexes here.

What this skill owns on top of that, because it is editorial rather than visual:
- Four-step text hierarchy (heading / body / sub / hint) and generous section rhythm.
- Numbered kickers in mono uppercase (`02 / Share of voice`); the mono-vs-sans contrast is part of the voice.
- Chart cards carry a title **and** a takeaway subtitle stating the conclusion, not axis names.
- Color only on signal — severity, focal vs. field, coverage badges — never decoration.
- Self-contained single file: inline CSS, Chart.js from cdnjs, no external assets, `<h2 class="sr-only">` summary and `aria-label` on every canvas.

---

## Agent notes

These aren't rules — they're the judgment calls that separate a sharp diagnosis from a shallow one.

**The four lanes organize Decode and the output — they do not replace the rigor.** Step 0 detection, Step 1 share math, driver decomposition, and sizing all still run in full. The lanes are a filing system for causes, not a substitute for finding them. The risk in adopting a company-wide framework is flattening a rigorous diagnostic into a tidy grid — keep the depth under each lane.

**A named coverage gap beats a hidden one — but earn the label first.** When something is genuinely Requires-integration, show the lane, tag it, say what's missing. But before you write "needs integration" on any datapoint, run the two-question test: is there a JS proxy (→ Inferred, and you must run it), and is it visible on the public listing (→ Observable, fetch it if it matters)? The classic trap is filing a JS-inferable signal (like a stockout) as integration-gated and parking it. It generalizes: PDP content, Prime/S&S badges, sponsored intensity, and seller counts are all assessable without the customer's accounts. "Requires integration" is reserved for genuinely private data — margin, true conversion rate, ad spend/TACOS — plus data that's private *to a brand you don't own* (buy-box win rate, per-seller offers, MAP). That last group flips to Direct the moment the customer connects their own account, so distinguish "one onboarding step away" from "structurally unavailable because it's a competitor." Everything else you either pull or fetch.

**Resolve aliases before the first query.** Analyzing Schylling and Needoh separately puts Schylling at rank #17 with 0.67% share. Combined, they're rank #2 with 5.21%. Always ask about parent/sub-brand relationships upfront.

**SOV by intent is the highest-signal step (Awareness lane).** A brand can be winning the branded SERP (equity intact) while losing the category SERP (discovery broken) — completely different responses. The Schylling case: branded organic SOV ~64% stable; category organic SOV collapsed from 83% to 19% in 17 months. Without the split, the diagnosis would have been "VISCOO is gaining via paid spend." With it: "category discovery is structurally broken" — far more urgent.

**The cohort split often reveals the real problem (Awareness lane).** Share movement that looks like competitive displacement is frequently a product-expansion asymmetry. Schylling case: competitors 41% of revenue from sub-12-month SKUs with 1,452 reviews; Schylling's new launches 7.8% of revenue with 12 reviews. The right diagnosis was "launch execution failure," not "outcompeted on existing products."

**Review velocity changes the durability call (Conversion lane, reads into Awareness).** A competitor winning sponsored SOV looks fragile until you check whether organic rank is improving. If it is, spend is building rank — structural in 2–3 quarters. If not, spend-dependent and stoppable.

**A presence collapse is a supply question until proven otherwise.** When a hero ASIN falls out of organic placement or SOV cliffs, the reflex is to reach for a competitive or listing-event story. Check inventory first: pull the ASIN's weekly units and buybox price. Volume decaying while realized price climbs and buybox max spikes far above normal is a stockout — the primary offer is gone and only marked-up third-party offers remain, and the organic rank loss is a *downstream consequence*, not the cause. Stockout is JS-inferable without integration, so there is no excuse to skip it. Diagnosing "competitive erosion" or "relist" over an unchecked stockout is the most expensive mistake to make — it sends the customer to fix marketing when the real fix is supply.

**Cite specifics, not directions.** "A competitor lowered price" is useless. "Mantyplay's B0FJRL61FJ dropped from $12.99 to $9.95 in Mar 2025, correlating with a 3× unit velocity increase" is useful. Name competitor, ASIN, date, magnitude.

**Multi-cause is the default.** Most share shifts have 2–3 contributing causes across different lanes at different magnitudes and durabilities. Forcing a single primary cause will mislead downstream planning.

**Durability is the highest-stakes call.** Misclassifying a fragile gain as structural sets up bad bets. When evidence is thin, lean fragile.

**Tier alignment before any displacement claim.** A $10 bulk pack cannot have displaced a $30 branded toy in direct substitution. Check ASP overlap before naming displacement.

**Carry it through to focus areas — but keep them disciplined.** The payoff is where to concentrate, not "here's what happened." Every focus area must trace to a diagnosed driver, be ordered by leverage, and carry an expected recovery and a watch-metric. Don't pad with generic best practices that don't map to a driver, and don't attach timeframes, deadlines, or sequencing — frame the root-cause area as the deeper fix versus the quicker recapture in leverage terms, and leave scheduling to the customer.

**Tell it, don't dump it.** The four lanes guarantee completeness; they are not the story. Lead with a verdict and 2–3 named failures, thread numbers through prose, push dense tables to the evidence appendix. A reader skimming only the headline, section leads, and recommendations should get the whole argument. See `references/exemplar-narrative.md`.

---

## Impact estimation methods

| Method | Use for | Calculation | Confidence |
|---|---|---|---|
| Share-to-revenue sizing | Realized impact | Share Δ (pp) × category revenue | High |
| Trend extrapolation | Forward exposure | Recent share Δ rate × projected periods × category trajectory | Medium |
| Share capture sizing | Recoverable — competitor took share | Recipient revenue in scope × estimated capturable % | Medium |
| Defensive necessity sizing | Recoverable — loss ongoing | Project share-loss trend forward; sum at-risk revenue | Medium-High |
| Stockout cost | Inventory-driven losses (Buy box) | Avg daily revenue × projected stockout days | High |
| Buybox recapture | Distribution-driven losses (Buy box) | ASIN revenue × (target − current win rate) × recapture rate | High |
| Keyword gap value | Traffic-driven losses (Awareness) | Search vol × CTR at target rank × conv rate × price | High |
| New launch sizing | Expansion opportunities (Awareness) | Target subcategory revenue × realistic Y1 share | Low-Medium |

**Y1 share heuristic:**
- Fragmented (top brand <15% share) → 3–5%
- Moderate (15–30%) → 2–3%
- Concentrated (>30%) → 1–2%

Always distinguish observed data from assumptions. Label assumptions as adjustable. Use ranges for Medium-or-below confidence. Lead with realized impact — it carries the highest confidence.
