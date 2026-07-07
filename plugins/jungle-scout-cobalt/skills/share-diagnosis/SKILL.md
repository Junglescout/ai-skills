---
name: share-diagnosis
description: "Use whenever the user asks about share movement, competitive position, or brand performance against a category — even if they don't use the word 'share'. Trigger phrases include: 'why are we losing ground', 'who's catching up to us', 'why did we gain share', 'what happened to our position', 'decode this shift', 'am I winning this market', 'why is [brand] declining', or any question where a brand's Amazon performance is framed against a category or competitor. Also trigger when the user asks about a competitor gaining momentum without explicitly framing it as a share question. Diagnoses why share moved, sizes the dollar impact, and identifies whether the cause is structural or fragile. Does not recommend plays — routes to the plays skill for that. Presentation styling is deferred to the jungle-scout-visualizer skill."
---

# Share Diagnosis

Diagnose why a brand's Amazon share moved — where, why, how durable, what it's worth — using the Jungle Scout Cobalt MCP server. Output is a diagnosis: location, cause, durability, dollars. Plays are out of scope.

This skill owns the **analysis method and the structure** of the diagnosis — which steps run, what each surfaces, and the section order of the output. It does **not** define visual styling: hand all palette, callouts, charts, growth pills, and tables to the `jungle-scout-visualizer` skill, which this skill depends on.

**Before starting:** read `references/worked-example.md` — it shows what a full deep-dive looks like end-to-end with real data, including how the three deep-dive steps (SOV by intent, review velocity, launch cohort) interact to produce a diagnosis that brand-level data alone cannot reach.

---

## Scoping

Ask before diagnosing. Send all six questions in one message — if the environment supports a structured input form or a multiple-choice prompt, present one; otherwise batch them as plain text. Do not run anything until the user responds or says "just run it."

1. **Brand & category.** Brand name plus Amazon category, or representative ASINs to resolve the competitive set. Ask explicitly whether the brand has sub-brands, parent companies, or alternate names — brands like "Schylling" and "Needoh" are the same entity, and analyzing them separately will systematically understate position and make competitors look stronger than they are.

2. **Time window.** Default 90 days vs. prior 90; YoY same-quarter for seasonal categories; event-anchored if relevant ("since Prime Day").

3. **Direction.** Gain / loss / unsure. If unsure, Step 0 detects before diagnosing.

4. **Sub-scope.** Full sweep, or zoom on a specific tier/segment/competitor. Default to full sweep.

5. **Depth.**
   - **Quick overview** (~10–15 min, 5–10 queries) — detect, decompose, localize, brand-level decoding, SOV snapshot, size.
   - **Deep dive** (~30–45 min, 15–30 queries) — adds SOV by keyword intent, review velocity trended over time, launch cohort split, ASIN-level decomposition, driver-magnitude analysis.
   - Default: run quick overview first, then offer to deep-dive on the 1–2 most consequential sub-scopes.

6. **Data access.** Customer integration (Seller Central / Brand Analytics / ad console) or Jungle Scout data only? Without integration, conversion, ad, and inventory claims must be flagged as inferred.

If user says "just run it": defaults are 90-day window, full sweep, quick overview, no integration. Surface assumptions in the output.

---

## Procedure

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

### Step 3 — Decode

For each concentrated sub-scope, pull competitor activity:
- Price changes
- New product launches (new ASINs under competitor brands)
- Review velocity — trended, not point-in-time (see Step 3.4 in deep dive)
- Ad presence shifts on key terms (see Step 3.3 in deep dive)
- Distribution shifts (new sellers, marketplace expansion, unauthorized sellers)
- Stockouts (sales drops to zero in a period)

Decompose the full competitor set. For losses, focus on what share recipients did differently. For gains, focus equally on what you did AND what competitors failed to do — an inherited gain is fragile regardless of size.

In **quick overview** mode: name a primary cause and 1–2 secondary contributors, then proceed to sizing. In **deep dive** mode: proceed to Steps 3.3–3.8 before sizing.

---

## Deep Dive Extensions (Steps 3.3–3.8)

These steps are what separate a diagnosis from a surface read. They're particularly valuable when the brand-level data looks like modest share loss — the cohort and SOV steps have consistently revealed structural problems that revenue trends alone hide. See `references/worked-example.md` for a full illustration.

### Step 3.3 — SOV by keyword intent

Share of voice is not one number. A brand can dominate branded keyword SERPs while losing category keyword SERPs — and these are structurally different problems requiring different responses. The distinction is worth the extra queries because it often changes the urgency and the recommended fix entirely.

**Branded keywords** — terms containing the brand or product name. Loss here means brand substitution is underway, which is serious. Stability here means brand equity is intact even if category discovery is suffering.

**Category keywords** — generic terms consumers use when they don't yet know what they want. Loss here means competitors are capturing discovery-stage shoppers first. This is often the more urgent signal and the easier one to address through paid presence.

**Procedure:**
1. Identify 5–8 keywords split across intent types. Use `search_keywords_by_asin` on the brand's top 3 hero ASINs for branded terms (highest-volume ones will contain the brand name). Use `search_keywords_by_keyword` on the category name for category terms. Also note any high-volume terms that contain competitor brand names — those reveal whether competitors have built enough brand equity to generate direct search demand.
2. Pull monthly SOV history (6–12 months) using `get_keyword_sov` with `equal_weighted_organic` and `equal_weighted_sponsored`. Pull the two keyword groups separately so you can compare trends within each type.
3. For each group, compare the focal brand's organic SOV trend against the top 3–4 gaining competitors.

**Interpreting the results:**
- Branded organic stable + category organic collapsing → brand equity intact but category discovery broken. The fix is paid presence on category terms, not brand investment.
- Branded organic falling → more serious; investigate whether competitors are buying branded terms (spend-dependent, stoppable) or building genuine brand recognition (structural).
- Competitor winning sponsored but organic rank not improving → spend-dependent position; fragile if they pull back budget.
- Competitor winning sponsored AND organic rank improving over consecutive months → their spend is building rank, which becomes structural. This changes the durability call significantly.

Output: a 2×2 SOV summary (branded/category × organic/sponsored) with trend direction per brand, plus a narrative on which competitors are responsible for each type of movement.

### Step 3.4 — Review velocity (trended)

Static review counts hide trajectory. A brand with 5,000 reviews adding 100 this quarter is losing ground to a brand with 400 reviews adding 300. Review velocity determines who wins the ranking flywheel over the next 6–12 months, so it's the right lens for durability calls.

Pull `variant_review_count_sum` trended weekly via `query_sales_estimates` for the focal brand and top 3–4 competitors, over 12–18 months. Compute quarterly addition rates per brand.

The critical sub-metric is new SKU review velocity: a new SKU adding 100+ reviews in 90 days is likely to rank organically within 2 quarters. One stalling at <30 reviews in 90 days will remain invisible regardless of how good the product is.

Use this step to qualify durability calls from Step 3.3: a competitor winning on sponsored SOV is a fragile threat if their review velocity is low. The same competitor building fast review velocity is a structural threat — they'll own organic rank in 2–3 quarters regardless of spend level.

### Step 3.5 — Launch cohort split

Use `analyze_products` with `group_by: launch_cohort` to split each brand's revenue into new SKUs (launched within the analysis window) vs. existing SKUs. Run for the focal brand and top 3–4 competitors.

This step matters because share movement that looks like competitive displacement is often a product expansion asymmetry — competitors launching and capturing faster while the focal brand stays put. The cohort split is the only way to distinguish "we're losing to better existing products" from "we're losing because we're not launching" — two very different problems with very different responses.

Key things to surface:
- New SKU revenue as % of total (>30% = aggressive expansion; <10% = catalog-dependent)
- Review count on new SKUs — this is the launch execution signal. Competitor new SKUs with high review counts means their launch process is working; focal brand new SKUs with near-zero reviews despite multiple launches means listing quality, traffic, or review acquisition is failing.
- New SKU average price — are competitors entering premium, value, or mid-tier with new launches?

A common pattern: the focal brand shows modest share loss at brand level, but the cohort view reveals competitors generate 40%+ of revenue from sub-12-month SKUs while the focal brand generates <10%. That reframes the diagnosis from "we're being outcompeted" to "we have a launch execution problem" — which is more actionable and more correctable.

### Step 3.6 — Driver decomposition

Decompose the observed delta into named drivers with magnitude, confidence, scope, and durability. Drivers should approximately sum to the observed delta; name residual rather than hiding it.

For each candidate driver, apply four qualifying tests:

- **Differentiation** — did the brand do this differently than competitors? If everyone moved the same lever, allocate ~0 magnitude to this driver.
- **Tier alignment** — for displacement claims, do ASP ranges overlap? No overlap = coincident, not causal.
- **Falsifiability** — what evidence would disprove this driver? If you can't say, confidence is low.
- **Mix vs. action** — recompute the metric on existing ASINs only. If the signal disappears, it's product mix shift, not the original framing.

| Driver | Magnitude | Confidence | Scope | Durability |
|---|---|---|---|---|
| [Named driver A] | $X (Y%) | high | [tier / competitor / segment] | structural |
| [Named driver B] | $X (Y%) | medium | [tier / competitor / segment] | fragile |
| Residual | $X (Y%) | — | — | — |
| **Total observed** | **$X (100%)** | | | |

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
- **Line extension** — new size, color, minor variant. Counts as revenue but doesn't address a segment shift.
- **Adjacent entry** — same form factor repositioned toward the growing segment. Often a marketing relabel, not a true pivot.
- **Genuine new segment** — form factor or product type the brand didn't previously offer.

Only genuine new segment entries count as a counter-move to substitution-driven loss. If new-launch revenue is concentrated in line extensions while substitution is moving demand to a different form factor, the brand has nominally responded without actually responding.

### Step 3.8 — Counter-move audit (conditional)

Run this when all three hold: loss diagnosis; a meaningful offsetting bucket from 3.7 (new-launch Δ ≥20% of the declining bucket); and demand has shifted to a definable segment.

When triggered, do not let the offsetting new-launch bucket count as evidence the brand is responding. The question is whether the response was *competitive*. Cross-join the brand's genuine new segment entries against the top 2–3 recipient brands' winning launches:

| Dimension | Brand's entries | Top recipient entries | Gap |
|---|---|---|---|
| Launch timing | First entry date | First entry date by top recipients | Months ahead/behind |
| Price tier | ASP range | Winner ASP range | % premium/discount |
| SKU breadth | # variants | # per winning brand | Coverage ratio |
| BSR rank | Median rank | Median rank of winning SKUs | Rank gap |
| Sub-segment coverage | Which sub-types entered | Which sub-types winners offer | Missing sub-types |

Size the missed opportunity:
```
Missed opportunity ≈ (median peer outcome per SKU in segment × SKUs brand could plausibly have launched) − brand's actual capture in segment
```

---

## Step 4 — Size

Three sizings:

1. **Realized** — dollars surrendered (loss) or captured (gain) in the comparison window.
2. **Forward exposure** — extrapolate the observed share-Δ rate over 4 / 12 / 52 weeks. Use a range when trajectory is noisy.
3. **Recoverable / defensible** — recapturable revenue for losses (currently flowing to share recipient), or at-risk revenue for gains if the driver weakens.

See the Impact Estimation Methods table at the bottom of this skill.

---

## Output

### Visualization (required for deep dive; optional for quick overview)

Hand all styling to the `jungle-scout-visualizer` skill, and read its `references/visuals.md` before the first widget — it owns the palette, the Chart.js templates, growth pills, the light/dark token swap, and the formatting helpers. This skill owns only the *structure* below: which panels appear and what each one shows. The two compose — don't define a separate palette or hardcode colors.

A deep-dive diagnosis is one of the rare cases where several panels each earn their place, so the visualizer's "one good visual beats three" default gives way to this skill's structure. Produce one inline widget (via `visualize:show_widget`) with four panels — a scannable "at a glance" read that complements the written diagnosis, not a generic dashboard. See `references/worked-example.md` for the pattern.

**Panel 1 — SOV by keyword intent**
Two rows of side-by-side line charts: branded organic + sponsored (top row), category organic + sponsored (bottom row). Monthly data, 6–12 months. The focal brand takes the focal color and competitors recede to gray; any competitor that has recently overtaken the focal brand on a metric takes the flag color to signal urgency.

**Panel 2 — Review velocity**
Cumulative review count over time, all brands, 12–18 month window. The focal brand's line is the focal color and visually heavier. The point is not the absolute count — it's the slope. A competitor with 400 reviews on a steep upward slope is more dangerous than one with 2,000 reviews on a flat line.

**Panel 3 — Launch cohort comparison**
Two side-by-side insight boxes: focal brand vs. competitors combined. Show new SKU revenue, new SKU review count, new SKU ASP, and new-as-% of total. Use the visualizer's signal pills — positive (green) for healthy, flag (orange) for watch, negative (red) for problem.

**Panel 4 — Keyword demand**
Top 8–10 keywords from the brand's hero ASINs, ranked by search volume, with quarterly trend and intent label (branded / category / competitor-branded). Trend direction is the key signal — a keyword with +1,000% quarterly trend that the brand isn't bidding on is an urgent gap; mark it with the flag color.

The focal-vs-gray contrast, the exact hexes (focal indigo, comparison gray, flag orange, positive/negative pills), the dark-mode swap, and the accessibility labeling all come from `jungle-scout-visualizer` — apply them here rather than restating them.

### Written output

```
WHAT HAPPENED
[Lead with the headline dollar number. Then 2–3 sentences explaining that the topline hides distinct stories — name them.]

THE CLEAR WINS  (omit if none)
[Earned, structural gains. Table: category, $Δ, share Δ, one-line "why it's real".]

THE LUCKY GAINS  (omit if none)
[Inherited from competitor collapse, recategorization, or anomaly. Label fragile; size at-risk dollars.]

THE LOSSES
[Real share losses and category-contraction losses, distinguished explicitly. Where share went and dollars at stake.]

DOLLARS
- Realized: $X
- Forward exposure: $X — $Y range
- Recoverable / at-risk: $X
- Missed opportunity (counter-move audit, when triggered): $X

---

EVIDENCE

Detection: scope, direction, magnitude, confidence, quality flags fired.
Decomposition: focal brand Δ, category Δ, footprint definition, share source/destination.
Localization: where movement concentrates; sub-scopes covered.

SOV diagnosis (deep dive): branded vs. category organic SOV trends; sponsored presence; which competitors are winning which keyword type and whether gains look structural (organic improving) or spend-dependent (sponsored only).

Review velocity (deep dive): quarterly addition rates per brand; new SKU velocity; which competitors are on a trajectory to own organic rankings in the next 2–3 quarters.

Launch cohort (deep dive): new-as-% of revenue for focal brand vs. competitors; new SKU review count comparison; what the cohort gap signals about innovation execution.

Attribution (per sub-scope):
  QUICK OVERVIEW: primary cause + evidence, competitor decomposition, secondary contributors, durability.
  DEEP DIVE: competitor decomposition, driver decomposition table (3.6), ASIN-level table (3.7) with launch classification, counter-move audit (3.8) when triggered, reconciliation %, residual.

Impact: method, key inputs, assumptions.

ASSUMPTIONS
- Window, depth, integration status, footprint exclusions.
- Data quality: leaf coherence, flags fired, claims weakened.
```

Tables for evidence. Prose for narrative. No bullets in narrative sections.

---

## Agent notes

These aren't rules — they're distilled from cases where the diagnosis went wrong without them.

**Resolve aliases before the first query.** Analyzing Schylling and Needoh separately puts Schylling at rank #17 with 0.67% share. Combined, they're rank #2 with 5.21%. That's a completely different competitive picture. Always ask about parent/sub-brand relationships upfront.

**SOV by intent is the highest-signal step in deep dive.** It's tempting to skip it when revenue trends seem to tell a clear story. Don't. A brand can be winning the branded SERP (brand equity intact) while losing the category SERP (discovery broken) — and these require completely different responses. The Schylling case: branded organic SOV ~64% stable; category organic SOV collapsed from 83% to 19% in 17 months. Without the split, the diagnosis would have been "VISCOO is gaining via paid spend." With it, the diagnosis was "category discovery is structurally broken" — a much more urgent finding.

**The cohort split often reveals the real problem.** Share movement that looks like competitive displacement at brand level is frequently a product expansion asymmetry. In the Schylling case: competitors generated 41% of revenue from sub-12-month SKUs with 1,452 reviews; Schylling's new launches were 7.8% of revenue with 12 reviews. The right diagnosis wasn't "we're being outcompeted on existing products" — it was "we have a launch execution failure." That's a different fix.

**Review velocity changes the durability call.** A competitor winning on sponsored SOV looks fragile until you check whether their organic rank is improving month-over-month. If it is, they're using spend to build rank — that becomes structural in 2–3 quarters. If organic rank isn't moving, the threat is spend-dependent and stoppable. Always check before calling durability.

**Cite specifics, not directions.** "A competitor lowered price" is useless. "Mantyplay's B0FJRL61FJ dropped from $12.99 to $9.95 in Mar 2025, correlating with a 3× unit velocity increase" is useful. Name competitor, ASIN, date, magnitude.

**Multi-cause is the default.** Most share shifts have 2–3 contributing causes at different magnitudes and durabilities. Forcing a single primary cause will mislead downstream planning.

**Durability is the highest-stakes call.** Misclassifying a fragile gain as structural sets up bad bets. When evidence is thin, lean fragile — false confidence costs more than caution.

**Tier alignment before any displacement claim.** A $10 bulk pack cannot have displaced a $30 branded toy in a direct substitution sense. Check ASP overlap before naming displacement. Coincident doesn't mean causal.

**Don't drift into recommendations.** Stop at "here's what happened and what it's worth." If asked "what should we do," route to the plays skill.

---

## Impact estimation methods

| Method | Use for | Calculation | Confidence |
|---|---|---|---|
| Share-to-revenue sizing | Realized impact | Share Δ (pp) × category revenue | High |
| Trend extrapolation | Forward exposure | Recent share Δ rate × projected periods × category trajectory | Medium |
| Share capture sizing | Recoverable — competitor took share | Recipient revenue in scope × estimated capturable % | Medium |
| Defensive necessity sizing | Recoverable — loss ongoing | Project share-loss trend forward; sum at-risk revenue | Medium-High |
| Stockout cost | Inventory-driven losses | Avg daily revenue × projected stockout days | High |
| Buybox recapture | Distribution-driven losses | ASIN revenue × (target − current win rate) × recapture rate | High |
| Keyword gap value | Traffic-driven losses | Search vol × CTR at target rank × conv rate × price | High |
| New launch sizing | Expansion opportunities | Target subcategory revenue × realistic Y1 share | Low-Medium |

**Y1 share heuristic:**
- Fragmented (top brand <15% share) → 3–5%
- Moderate (15–30%) → 2–3%
- Concentrated (>30%) → 1–2%

Always distinguish observed data from assumptions. Label assumptions as adjustable. Use ranges for Medium-or-below confidence. Lead with realized impact — it carries the highest confidence.
