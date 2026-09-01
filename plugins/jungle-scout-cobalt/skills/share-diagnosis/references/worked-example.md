# Worked Example: Schylling / Needoh — Squeeze Toys

This example walks through a full deep-dive diagnosis from a real session. Use it to calibrate what "good" looks like at each step — the data values, interpretation calls, and how the three new steps (SOV by intent, review velocity, launch cohort) combined to flip the diagnosis from "competitive displacement" to "launch execution failure plus category discovery loss."

> **Lane mapping** (this example predates the four-lane restructure; the analysis is identical, only the filing changed): SOV by intent (§3.3) and launch cohort (§3.5) are the **Awareness** lane; review velocity (§3.4) is the **Conversion** lane and reads into Awareness durability. Buy box and Sustainability were Requires-integration in this session — JS-only, no Seller Central or ad console — so they'd appear tagged as such rather than dropped.

---

## Setup

**Brand:** Schylling + Needoh (same entity — Needoh is Schylling's flagship product line, sold under a separate brand name on Amazon. Combining them was the first corrective step; analyzing them separately would have put Schylling at rank #17 rather than #2.)

**Category:** Squeeze Toys (leaf ID 23538328011)

**Window:** Last 90 days (Mar 16 – Jun 13, 2026) vs. year-ago

**Direction:** Loss suspected — share flat but category growing

---

## Step 0: Detection

`analyze_brands` on Squeeze Toys showed:

- Schylling + Needoh combined: $6.73M revenue, +0.7% YoY
- Category: $129M, +3.2% YoY
- Combined share: 5.21% — down ~0.15pp YoY

Magnitude flag: 0.15pp QoQ is below the ≥1.5pp threshold on its own, but share held flat while category grew 3.2% — the "held flat, market grew without you" story. That passes the persistence test (confirmed over 3 consecutive quarters). Proceed.

Quality flags checked: no taxonomy drift; 2,821 brands tracked (well above 5-brand floor); leaf coherence clean; price range $5–$40 (8x dispersion — flagged, split analysis by tier).

---

## Step 1: Decompose

| | Schylling + Needoh | Category |
|---|---|---|
| Revenue (90d) | $6.73M | $129M |
| YoY growth | +0.7% | +3.2% |
| Share | 5.21% | — |

Share went to: Generic/unbranded pool (+10.9% YoY, growing 3× faster than the category average), Mantyplay (+6.5%), VISCOO (+5.4%). No single brand took a large chunk; it was distributed bleed to a field of growing competitors.

Core footprint: Schylling holds >2% only in Squeeze Toys — single-category brand, so footprint = category.

---

## Step 2: Localize

Price tier analysis revealed the movement was not uniform:

| Tier | Category growth | Schylling + Needoh position |
|---|---|---|
| Under $9 | +8% | 24% of combined revenue — at risk |
| $9–$10 | +4% | 22% of revenue — contested |
| $10–$15 | +6% | 35% of revenue — core |
| $15–$20 | +2% | 5% of revenue — thin |
| $20+ | +2% | 16% of revenue — growing at +30% YoY |

Movement concentrated in the $10–$15 tier (Schylling's core) and the under-$10 tiers, where Mantyplay and Generic entrants were gaining. The $20+ tier was the one bright spot — Needoh's premium SKUs growing while the rest stagnated.

---

## Step 3: Decode (brand-level)

Top competitors gaining share:
- **Mantyplay**: +6.5% YoY, launched mid-2024, concentrated revenue in a single $10 bulk-pack SKU. Rating 4.6★ vs. Schylling's 4.3★ on comparable products.
- **VISCOO**: +5.4% YoY, 26 SKUs, heavily sponsored. Rating 3.8–4.2★ — lower quality signal but aggressive paid presence.
- **Squeez'M**: Launched Dec 2024, already $828K revenue in last 90 days. Rating 4.6★. Premium positioning at $19–$39.

---

## Step 3.3: SOV by keyword intent

**Keywords used:**

Branded (from `search_keywords_by_asin` on Schylling's top ASINs): "needoh ball", "nee doh ball"

Category (from `search_keywords_by_keyword` on "squeeze toy"): "squeeze toy", "squishy toys", "sensory toys"

**Results (May 2026):**

| | Branded organic | Branded sponsored | Category organic | Category sponsored |
|---|---|---|---|---|
| Schylling + Needoh | 64% combined | ~0% | 19% | ~0% |
| VISCOO | 19% | 92% | 51% | 88% |
| Mantyplay | ~5% | ~8% | 15% | 3% |
| Drephere | 10% | ~8% | 9% | 3% |
| Squeez'M | 6% | ~0% | 5% | 0% |

**Interpretation:** This is the diagnosis-splitting finding. On branded terms, Schylling + Needoh still hold 64% of organic placements — brand equity is largely intact. On category terms ("squeeze toy", "squishy toys"), VISCOO has overtaken Schylling organically (51% vs. 19%) and dominates sponsored (88%). Schylling has near-zero paid presence on any keyword type.

This means consumers searching for "needoh" still find Schylling first. But consumers who don't yet know what they want — the discovery shopper — is increasingly finding VISCOO first. These are structurally different problems: one is brand erosion (not yet happening), the other is category discovery loss (actively happening and accelerating).

VISCOO winning sponsored but also now winning organic on category terms is the structural signal — their spend is building rank, not just buying visibility. If this continues 2–3 more quarters, they'll own category organic regardless of their spend level.

---

## Step 3.4: Review velocity

Weekly `variant_review_count_sum` trended over 18 months:

| Brand | Reviews Jun 2024 | Reviews Apr 2025 | Added in ~10 months | Rate/quarter |
|---|---|---|---|---|
| Schylling | ~4,950 | ~9,177 | +4,227 | ~1,269 |
| Needoh | ~248 | ~270 | +22 | ~7 |
| Mantyplay | 0 | 64 | +64 | ~19 |
| VISCOO | 38 | 240 | +202 | ~61 |
| Squeez'M | 0 | 65 | +65 | ~20 |

Schylling's existing catalog is accumulating reviews at a healthy rate (~1,269/quarter). But Needoh specifically is nearly flat — only 22 reviews added in 10 months on the brand that carries the most search demand ("needoh" = 14M search volume). And critically, both Needoh's and Schylling's new SKUs launched in the past year have almost no review traction (see cohort split below).

VISCOO adding 61 reviews/quarter with a sub-4.0 average rating is the fragile aggressor signal: they're building velocity but quality is low. If their ratings don't improve, organic rank gains will plateau. Squeez'M adding reviews at a similar rate but with a 4.6★ average is the more dangerous trajectory.

---

## Step 3.5: Launch cohort split

`analyze_products` with `group_by: launch_cohort`, trailing 12 months:

| | Schylling + Needoh | Mantyplay + VISCOO + Squeez'M + Drephere |
|---|---|---|
| New SKU revenue (post Jun 2025) | $2.4M | $6.1M |
| New SKU reviews | 12 | 1,452 |
| New SKU avg price | $21.70 | $18.85 |
| New as % of total revenue | 7.8% | 40.7% |

**This is the diagnosis-changing finding.** Competitors generate 41% of their revenue from SKUs launched in the past year, and those new SKUs have 1,452 reviews. Schylling's new SKUs represent only 7.8% of revenue and have accumulated 12 reviews total across all new launches.

This reframes the whole picture. The share loss is not primarily about Schylling's existing products getting worse — the existing catalog is holding reasonably well (+4,227 reviews in 10 months, stable rating). The problem is that Schylling is not successfully commercializing new products. When they launch, products don't gain traction. Competitors launch faster, capture reviews faster, and build organic rank faster.

The "innovation execution gap" is the primary diagnosis. Competitive displacement on existing SKUs is secondary.

---

## Step 3.6: Driver decomposition

| Driver | Magnitude | Confidence | Scope | Durability |
|---|---|---|---|---|
| Launch execution failure — new SKUs not converting to reviews | −~$1.2M forward exposure | Medium | All new Schylling/Needoh launches past 12 months | Structural until fixed |
| Category discovery loss — VISCOO winning category keyword organic | −~$800K forward exposure | Medium-High | $10–$20 tier, category shoppers | Structural (organic gains earned) |
| Under-$10 tier price pressure from Mantyplay/Generic | −~$400K forward exposure | Medium | Under-$10 tier only | Fragile (margin-dependent) |
| Branded keyword moat holding | +offsets above | High | All branded terms | Structural (14M search vol, 64% organic SOV) |
| $20+ Needoh premium growing | +$340K captured | High | $20+ tier | Structural if review velocity improves |
| Residual / unexplained | ~$200K | Low | — | — |

Note: no single primary cause. The launch execution failure and category discovery loss are co-primary, operating at different time horizons (launch execution is a now problem; category keyword organic is a 2–3 quarter compounding problem).

---

## Step 4: Sizing

**Realized loss:** Category grew $4.1M in 90 days that Schylling's share would have captured at its prior rate. At 5.21% of $4.1M = ~$214K in revenue Schylling didn't capture due to share erosion. Modest in absolute terms but the trajectory is the signal.

**Forward exposure (12 months):**
- If VISCOO completes its category organic takeover: ~$2–3M in category discovery revenue shifts away from Schylling annually
- If launch execution gap persists: new SKU contribution stays at <8% of revenue while competitors compound at 40%+, implying ~$4–6M opportunity cost over 2 years

**Recoverable:** Branded keyword position is largely intact (64% organic on "needoh ball"). The $20+ premium tier is growing and defensible. Core exposure is in category keywords and new product velocity — both are fixable with investment.

---

## What the three new steps changed

Without SOV by intent, the diagnosis would have been "VISCOO is gaining share, probably through paid spend." With the branded vs. category split, the diagnosis became "category discovery is broken but brand equity is intact" — a completely different strategic response.

Without the launch cohort split, the magnitude of the new-SKU execution gap would have been invisible. The brand-level revenue view looked like modest share loss. The cohort view revealed that competitors are building a new product flywheel Schylling isn't competing in.

Without review velocity trended over time, VISCOO's sponsored dominance would have looked fragile (spend-dependent). The velocity data showed their organic rank is improving, which means it's becoming structural. That changes the urgency of Schylling's paid response.
