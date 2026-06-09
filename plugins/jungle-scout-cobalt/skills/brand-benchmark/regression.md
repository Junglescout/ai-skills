# Brand Benchmark — Regression Harness (lightweight)

A fixed set of cases, each pinned to one branch of `brand-benchmark`, that an agent runs and checks against expected **behavior**. It exists because end-to-end "it ran and produced a brief" testing validates what the agent *did*, not what `SKILL.md` *says* — and that gap is where every shipped bug in this skill has lived (wrong tool call written in prose, dead guardrails, branches never exercised, data shapes nobody picked).

This is **not** automated CI. It's a checklist an agent (or a person directing one) runs after any edit to the skill, or periodically to catch live-data drift. The value is the *case selection* — the inputs are chosen specifically to hit the branches the happy path skips.

## How to run

1. Resolve `org_id` via `list_orgs`. **Any org works** — market-analysis estimates are org-independent, so results don't depend on the choice.
2. For each case below, run `brand-benchmark` exactly as a user would (use the **Input** prompt verbatim), letting the skill do its own scope resolution and freshness anchoring.
3. After each run, check the **Assertions**. Each is observable either from the tool calls the agent made or from the rendered brief.
4. Record PASS / FAIL per assertion. Any FAIL means the skill regressed on that branch — fix before shipping.

Run all six for a full pass (~6 brand-benchmark runs). For a quick smoke test after a small edit, run only the cases touching the edited section (the **Branch** column tells you which).

## How to read assertions

Two kinds, and the distinction matters because **the underlying data drifts**:

- **Shape assertions** (durable) — assert on structure/behavior, never on a specific number. These are the real test; they survive data drift. Example: "the ASP-implied tier is not the largest-revenue tier → dual-surface fires." That stays true even as the percentages move.
- **Baseline values** (bonus sanity check, *as of 2026-06-03*) — current live figures, given so a runner can confirm the case still hits its intended branch. If a baseline value has drifted enough that the case no longer exercises its branch (e.g. Epic climbs above 2% share), swap in a fresh brand that does — don't assert the stale number.

If a case stops hitting its branch because the market moved, that's expected maintenance — update the case, keep the assertion.

---

## The cases

| # | Case | Input | Branch exercised | Maps to fixed issue |
|---|------|-------|------------------|---------------------|
| C1 | Multi-leaf anchor | "Benchmark Garmin" | Step 0 footprint pull + 2× auto-anchor | #1 |
| C2 | Present-but-sub-scale | "Benchmark Epic in Jerky" | 2% floor on a low-share *present* row | #5 |
| C3 | Bimodal home tier | "Benchmark Optimum Nutrition in Whey Protein" | <10% ASP-tier redefinition | (Edit 7) |
| C4 | Split-tier home | "Benchmark Jack Link's in Jerky" | ASP-tier ≥10% but not largest → dual-surface | #2 |
| C5 | Noisy neighborhood | "Benchmark Epic in Jerky" (same run as C2) | suspect >500% row guard in table + bar | #6 |
| C6 | Share-transfer scan + tier alignment | "Benchmark Jack Link's in Jerky" (same run as C4) | scan all 50 rows by share Δ; tier-migration call | #3 |

Note C2/C5 share one run, and C4/C6 share one run — so the full harness is **four** brand-benchmark invocations (Garmin, Epic/Jerky, Optimum Nutrition/Whey, Jack Link's/Jerky), not six.

---

### C1 — Multi-leaf anchor (issue #1)

**Input:** "Benchmark Garmin" (no category named)

**Branch:** Step 0 no-leaf path — pull the brand's leaf footprint, auto-anchor if the top leaf is ≥2× the second.

**Assertions:**
- **[shape]** The footprint call is `analyze_categories(filters={brand_query:"garmin"})` — leaf-grain. **FAIL if** the agent calls `analyze_brands(brand_query=…)` for the footprint (returns brand-grain rows, can't anchor — this is the original bug).
- **[shape]** The response yields multiple leaf rows (one per leaf the brand sells in), and the agent picks the highest-revenue leaf as the anchor.
- **[shape]** Because the top leaf is ≥2× the second, the skill **auto-anchors without asking** and names the choice in ASSUMPTIONS.
- **[shape]** ASSUMPTIONS lists the top 3 other leaves as out-of-scope, with "(+N more)" if more exist.
- **[baseline, 2026-06-03]** Anchor resolves to **Smartwatches** (~$87M, ~45% of Garmin's Amazon revenue), ~6.8× the second leaf (Activity & Fitness Trackers ~$13M). Other leaves: Fish Finders, Handheld GPS, Marine Chartplotters, etc.

---

### C2 — Present-but-sub-scale (issue #5)

**Input:** "Benchmark Epic in Jerky"

**Branch:** 2% focal-brand floor — must test the brand's **share value**, not its mere presence in the ranked rows.

**Assertions:**
- **[shape]** The skill flags the brand as **sub-scale (<2%)** and offers to widen scope — *even though the brand appears in the B ranked list*. **FAIL if** it proceeds with a normal benchmark because the brand was "present in the rows."
- **[baseline, 2026-06-03]** Epic is **rank ~17 in Jerky at ~0.85% share** — present in the top 50, well under 2%. (If Epic has since climbed above 2%, substitute another present-but-sub-scale brand — e.g. scan Jerky's B-rows for one in the 0.5–1.9% band.)

---

### C3 — Bimodal home tier (Edit 7)

**Input:** "Benchmark Optimum Nutrition in Whey Protein"

**Branch:** home-tier definition — when the ASP-implied tier holds <10% of brand revenue, redefine home to the largest-revenue tier and narrate the two-peak shape.

**Assertions:**
- **[shape]** Price-posture prose notes the **bimodal** pattern — weighted ASP falls in a tier that holds little of the brand's revenue, while volume concentrates in two other tiers.
- **[shape]** The home tier used for flag logic is the **largest-revenue tier**, not the (near-empty) ASP-implied tier.
- **[baseline, 2026-06-03]** ON's ASP (~$54) lands in the $45–55 tier (~1–2% of brand revenue), while ~39% sits in $70+ and ~35% in $35–45. This example has matched live consistently — a good stable oracle.

---

### C4 — Split-tier home (issue #2)

**Input:** "Benchmark Jack Link's in Jerky"

**Branch:** home-tier split guard — when the ASP-implied tier clears 10% but is **not** the largest-revenue tier, dual-surface both tiers rather than silently picking one.

**Assertions:**
- **[shape]** Price-posture prose **surfaces both** the ASP-implied tier and the largest-revenue tier, with each tier's brand-vs-category growth — because they diverge.
- **[shape]** Tier-strand flag logic is evaluated against the **largest-revenue tier** (where volume lives); the ASP-tier divergence is mentioned in prose, not used to fire the flag off the smaller tier. **FAIL if** the brief silently treats the ASP-implied tier as the sole home and the strand flag hinges on that pick.
- **[baseline, 2026-06-03]** ASP-implied home $14–22 holds ~24% and is **losing** (~−30% YoY vs category tier ~+6%); largest tier Under $14 holds ~34% and is **winning** (~+96% vs category ~+67%). The divergence is the whole point — if both tiers ever move the same direction, this case stops exercising the branch; refresh it.

---

### C5 — Noisy neighborhood / suspect-row guard (issue #6)

**Input:** "Benchmark Epic in Jerky" (read off the same run as C2)

**Branch:** suspect-row handling — neighborhood table asterisks >500% YoY rows; the position-bar end-of-bar label must do the same, not print a raw blown-out number.

**Assertions:**
- **[shape]** Any neighborhood-table row with YoY > +500% is asterisked with a one-line "likely taxonomy reclassification" footnote.
- **[shape]** The position-bar growth label for such a row renders as **`>+500%*`** (or suppressed + asterisked), **not** the raw value. **FAIL if** a label like "+6807%" prints on the bar.
- **[baseline, 2026-06-03]** Jerky's top brands include **Paleovalley (~+6807% YoY)** and Grazly (~+3740%) — both should trip the guard. (These are small-base/reclassification artifacts and reliably present; if they age out, any category with a freshly reclassified brand works.)

---

### C6 — Share-transfer scan + tier alignment (issue #3)

**Input:** "Benchmark Jack Link's in Jerky" (read off the same run as C4)

**Branch:** share-transfer match — scan **all** B-rows by share Δ (not just top 5 by revenue) for the dominant recipient, then run the tier-alignment check.

**Assertions:**
- **[shape]** The recipient scan considers the largest share-gainer **regardless of revenue rank** — a rank-6+ gainer must be eligible. **FAIL if** the scan is limited to the top 5 by revenue and reports "diffuse loss" while a qualifying recipient sits just outside that window.
- **[shape]** Once a recipient in the 70–120% band is found, the tier-alignment check runs: if the recipient sits in a different price tier (different label AND ASPs >20% apart), the headline calls **tier migration**, not displacement.
- **[baseline, 2026-06-03]** Jack Link's is **losing** share (~−6.2pp); the dominant gainer is **Chomps (~+5.2pp, ~84% of JL's loss — in band)** at ASP ~$29.56 vs JL ~$16.32 (>20% apart, different tier) → **tier migration**. (Here the recipient happens to be rank #1, so this run mainly exercises the tier-alignment half; for the *scan-window* half, see the note below.)

> **Scan-window coverage gap:** the live Jerky recipient (Chomps) is currently rank #1, so this run doesn't fully prove the "rank-6+ recipient" fix on its own. To exercise that specific branch, periodically check Whey Protein for the Optimum-Nutrition→Transparent-Labs pattern (a dominant gainer outside the top 5 by revenue), or any category where the largest share-gainer is not a top-5-revenue brand. Add such a case when one is live.

---

## Maintenance

- **Re-baseline quarterly or after any SKILL.md edit.** Update the *baseline values* to current live figures; leave the *shape assertions* alone unless the skill's logic changed.
- **If a case stops hitting its branch** (market moved — e.g. Epic crosses 2%, or Jack Link's tiers re-converge), swap the brand/category for one that currently exhibits the pattern. The case's job is to exercise the branch, not to track a particular brand.
- **When you add a skill** (`pricing-deep-dive`, `innovation`) that shares the Step 0 scope-resolution preamble, add its branch cases here (or to a sibling harness) — the multi-leaf, sub-scale, and freshness branches are common across the library, so one harness pattern covers all of them.
- **Known coverage gap:** the rank-6+ share-recipient branch (C6 scan-window half) needs a live example to fully exercise; see the note under C6.

## Baseline snapshot

All baseline values above were verified live on **2026-06-03**, window **2026-02-23 → 2026-05-23** (the freshness-anchored trailing-90-day window), org-independent. Re-verify on next run.
