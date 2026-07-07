# Opportunity ceiling & revenue scenarios

How to turn demand evidence into a defensible revenue range for a product that doesn't exist yet. The goal is auditable, not precise — every number prints its inputs.

## Step A — Opportunity ceiling (realistic addressable annual revenue)

The ceiling is **not** the whole category. It's what this brand could realistically capture, derived from a real comparable. Pick the method that matches the opportunity type.

**1. Assortment gap (proven category).**
- Segment revenue = the underserved tier/format/attribute's annual revenue (from `analyze_price_tiers` / `analyze_attributes` / `analyze_categories`).
- Capture % = the brand's existing category share if it's on Amazon; if absent or off-Amazon, use a conservative entrant anchor (1–3%).
- **Ceiling = segment revenue × capture %.**

**2. Adjacent category expansion.**
- Category revenue + growth (`analyze_categories`).
- Capture % depends on adjacency strength: strong equity/keyword pull → base 2–4%; weak adjacency → 1–2%.
- **Ceiling = category revenue × capture %.**

**3. Attribute / feature whitespace.**
- Estimate attribute demand $ = monthly search volume (sum the relevant keywords) × assumed conversion (default 10%, flag it) × category ASP × 12.
- Capture % = 2–5% if supply is genuinely weak.
- **Ceiling = attribute demand × capture %.** *Inherently rougher — cap confidence at Medium.*

**4. Bundle / multipack.**
- Combined single-unit demand for the bundled items (from `analyze_products`).
- Shift assumption: 5–15% of that demand migrates to the bundle.
- **Ceiling = combined demand × shift %.**

**5. Blue-sky / net-new.**
- No analog → order-of-magnitude only, anchored to the nearest adjacent category or a cited trend size. **Confidence Low, always.** State explicitly it's directional.

Always print the chosen capture % and why. A reader who disagrees with the % can re-run the math in their head — that's the trust mechanism. This Amazon figure is the **validated floor** — the number the data proves.

**Entrant vs. incumbent — check the catalog first.** The 1–3% new-entrant anchor only applies if the brand genuinely doesn't sell the product type (Step 4b case (a)/(c)). If the brand already makes it but is catalogued elsewhere or holds low node share (case (b)), it has permission and adjacent SKUs — it is *not* a pure new entrant. Don't auto-apply the entrant anchor; pick a rate that reflects its real standing and say why. Reading a brand as a "new entrant" when it already makes the product (just filed under another node) both mis-sizes the floor and mis-frames the opportunity.

## Step A2 — All-channel prize (the headline)

The validated floor is Amazon-only. For a brand that sells mostly off-Amazon, that understates the real opportunity many times over — a $2M Amazon ceiling on a $500M brand reads as trivial when the all-channel prize is an order of magnitude bigger. Gross the floor up:

**Prize = validated floor × channel multiplier.**

- **Baseline multiplier = 1 ÷ (the brand's Amazon share of its own revenue).** If Amazon is ~12% of the brand's total revenue, multiplier ≈ ×8. This says: "if a new product distributes across channels like the brand's existing products do, the all-channel prize is ~8× the Amazon-measured floor." Two real numbers, one assumption, easy to defend.
- **Vary it by where the idea's demand actually lives.** An idea whose demand is largely *off* Amazon (c-store impulse, single-serve, club packs) deserves a *higher* multiplier (×10+) — Amazon barely captures that demand, so it understates the prize most. An idea that *over*-indexes on Amazon (a premium niche with a strong DTC/online skew) deserves a *lower* one. State the multiplier and the reason every time.
- Confidence still tracks the **floor**, not the prize. The prize is the size of the bet; the floor is the proof it's real. Never let the gross-up inflate confidence.
- Sanity-check, don't replace: if total-category retail size is known from market research, use it to check the prize is in a believable range — but don't build the forecast on it (capture rates at total-retail scale get speculative fast).

## Step B — Lead time (decide → first sale)

Lead time determines *when* revenue starts. It is the reason a big-ceiling idea can still show near-zero at month 3. Defaults (user can override):

| Opportunity type | Lead time |
| New variant / pack, existing supplier | 3 months |
| New format / reformulation / new attribute | 6 months |
| New category (new supply chain) | 9 months |
| Net-new / blue-sky | 12 months |

## Step C — Ramp (launch → steady state)

Products don't hit the ceiling on day one. Convert the annual ceiling to a monthly run-rate (ceiling ÷ 12), then ramp linearly from 0 at launch to a steady-state fraction of run-rate by 12 months post-launch:

- Conservative → 25% of run-rate at 12mo post-launch
- Base → 50%
- Optimistic → 75%

**Ramp speed varies by opportunity type.** The defaults above assume a genuinely new product. A **repack or line extension of a proven hero SKU** (e.g. an existing best-seller in a new pack size or a new flavor on the current line) ramps much faster — the demand and the supply already exist. Raise the steady-state fractions (e.g. base 60–70%) and say why. Conversely, a net-new category entry with no brand permission ramps slower. Match the ramp to how much of the product is genuinely new.

(A brand with strong existing demand and fast distribution can justify a higher steady-state — note it if you raise it.)

## Step D — Assemble the 3/6/9/12 table

Windows are measured **from decision (now)**, not from launch.
1. Months before launch (= lead time) contribute $0.
2. After launch, monthly revenue = run-rate × (months-since-launch ÷ 12) × steady-state fraction, capped at run-rate × steady-state fraction.
3. Cumulative = sum of monthly revenue up to each window.
4. Also report the **exit monthly run-rate at month 12** — cumulative under-sells a late, fast launch, so the exit rate shows where it's heading.

## Worked example

**Idea:** brand enters a new format. **Ceiling = $2.0M/yr** (segment revenue $40M × 5% capture). Run-rate at 100% = $167K/mo.
**Lead time:** 6 months → launches at month 6. Windows from decision.

Base case (steady-state 50%):
- Months 1–6: pre-launch, $0.
- Post-launch monthly revenue ramps 0 → 50% of $167K over 12 months. By month 12 from decision = 6 months post-launch = (6÷12)×50% × $167K ≈ $42K that month.
- **Cumulative: 3mo $0 · 6mo $0 · 9mo ~$63K · 12mo ~$210K · exit run-rate ~$42K/mo (and climbing toward the $83K base steady-state).**

The headline this produces: "big ceiling, but the lead time means it's a 12-month-plus bet — near-zero before then." That honesty is the deliverable. Contrast with a 3-month assortment extension on the same ceiling, which would post real revenue by month 6 and rank higher on near-term impact despite a smaller ceiling — exactly the tradeoff the ranking should surface.

## Sensitivity note

The two assumptions that move everything are **capture %** and **steady-state fraction**. When an idea's rank hinges on them, say so in one line ("ranks #2 on a 4% capture; at 2% it's #4") rather than hiding the fragility.
