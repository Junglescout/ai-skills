---
name: innovation-whitespace
description: "Use when a specific brand is named and the question is forward-looking: what to launch, where to expand, how to differentiate, how to win against rivals, or where the whitespace is. The core trigger is a brand + a growth/innovation question — not a category question with no focal brand. Covers new product ideas (NPD), assortment gaps, adjacent category moves, competitive positioning, and right-to-win analysis. Uses Jungle Scout demand data + web research to surface 5 ranked opportunities, each with market size, a concrete product, the rival it beats, brand strengths it leverages, and a revenue scenario. Presentation styling is deferred to the jungle-scout-visualizer skill."
---

# Innovation Whitespace

## Purpose

Surface where a brand could launch next. Given one brand — on Amazon or not — find 5 product/assortment opportunities, rank them by impact × feasibility, and for each show, **on one card**: the market (size, growth, how open), the specific product to make, the rival it beats and why, the brand strengths it leverages, a revenue estimate (Amazon-validated floor grossed up to an all-channel prize), a confidence score, and a feasibility read. The default deliverable is a dense, exec-facing HTML artifact; a lighter inline chat brief is the fallback.

Sizing alone is half the job. A big market is only an opportunity if the brand can build something rivals can't easily copy. **Differentiation is not a separate document — it lives inside every opportunity.** See Step 4 and `references/differentiation.md`.

This skill leans on the Jungle Scout Cobalt connector/MCP server (`https://ai.junglescout.com/mcp`) for demand evidence and on web research for the brand's strategy, constraints, assortment, and the competitive narrative.

## Grounding rules (read first)

Jungle Scout data describes what sells *now*; this skill uses it to reason about products that don't exist yet. Bridging that gap responsibly comes down to four rules:

1. **Confidence tracks evidence, not ambition.** Proven comparable in live data → High. Inferred adjacency → Medium. Blue-sky with no analog → Low — surface it, label it, never dress it up.
2. **Revenue is a scenario, never a number.** Conservative/base/optimistic, from a visible ceiling and a visible ramp. No bare point estimates.
3. **Show the work.** Every ceiling figure prints its inputs.
4. **Use each source for what it measures.** Jungle Scout supplies category sizes, prices, sales, attributes, launch dynamics, and competitor structure. A competitor's stated strategy, review sentiment, and the brand's own strengths come from web research and reasoning — label them as such, never imply Jungle Scout measured them.

If the Jungle Scout Cobalt connector/MCP server isn't connected (its tools don't load, or a call fails auth), stop and ask the user to connect it (`https://ai.junglescout.com/mcp`) before continuing. Don't substitute web search for live demand numbers.

If a data call returns **"No approval received"** (or a similar approval/permission error), the connector is authenticated but the call is gated behind a per-call approval. Don't retry blindly — tell the user plainly that the Jungle Scout queries need their approval (approve the prompt, or set the connector to allow for the session), then continue. This is distinct from a missing connector and doesn't need a reconnect.

## When to use

Trigger on: "new product ideas for [brand]", "where should [brand] expand", "assortment gaps", "white space", "what should we launch", "innovation opportunities", "NPD for [brand]", **"how can [brand] differentiate", "how should [brand] position itself", "what do competitors do", "what's different about what [brand] can put in the market", "how does [brand] win against [rivals]"**.

Do **not** use for: benchmarking a current portfolio (`benchmark-brand`), share-movement diagnosis (`share-diagnosis`), or category sizing with no focal brand (`analyze_categories` directly).

## Step 1 — Scope (one ask, up front)

Gather these in one batched ask — if the environment supports a structured input form or a multiple-choice prompt, present one; otherwise ask them together in a single message. Only ask for what's missing from the conversation.

1. **Brand + Amazon status.** Brand name. Does it sell on Amazon? (Yes / No / Not sure.) If yes, a category or representative ASINs help anchor.
2. **Home category / where they play today** — so adjacencies are measured from the right starting point.
3. **Strategy & constraints** — the most important input. Prompt for anything that rules opportunities in or out: positioning (premium/mid/value) and margin floor; manufacturing/supply limits; off-limits or strategically core categories; innovation appetite (line extensions vs net-new); time horizon (wins this year vs 12-month bets fine).

If the user says "just run it," proceed with no constraints and **state that plainly in ASSUMPTIONS** — an unconstrained run will surface ideas the brand may have already ruled out.

## Step 2 — Build the evidence base

**Always research the brand online first** (web search + fetch): current assortment, recent launches, stated strategy, positioning, DTC range, manufacturing footprint, warranty, press. This grounds the constraints, the adjacencies, **and the brand's hard-to-copy strengths** (Step 4). For off-Amazon brands it's the *only* brand-level signal you have. Also note the brand's total revenue if findable — you need it for the channel multiplier.

**Map the brand's real catalog before you size adjacencies.** First, find out what the brand actually makes and *where Amazon files it*: pull the brand's full product list unfiltered (`analyze_products` with `brands=[...]` and **no** category filter, sorted by revenue) plus a title-text search (`analyze_products` with `product_query="<product type>"`, e.g. "knife") across all categories. Read which leaf nodes the brand's SKUs sit in. Amazon's category nodes don't map cleanly to how brands think about products, and a brand's SKUs usually cluster in its *home* node — a multitool brand's folding knives sit under **Multitools**, not under "Pocket Knives & Folding Knives." So scoping a brand to a target node and reading low revenue there does **not** mean the brand doesn't make the product; it may be catalogued elsewhere. Do this before declaring any adjacency empty, and **reconcile it with the recent launches you found in web research** — a just-launched line won't appear in the trailing-year window even though it exists.

**Then pull demand evidence from the Jungle Scout Cobalt connector/MCP server.** Its tools may be deferred — load them before calling. Typical calls:
- `list_orgs` → `org_id` (any org is fine; market-analysis estimates are org-independent — don't stop to ask which).
- `search_categories_by_name` → resolve the home category and candidate adjacent leaves. (Substring match with semantic ranking — generic fragments like "kni" return noise; use the fuller word, e.g. "knives".)
- `analyze_categories` → size and growth of home + adjacent categories; `aggregate=true` for a clean total, or pass several leaf IDs with `group_by="category"` and `include_enrichments=["top_brand"]` to size many at once.
- `analyze_brands` scoped to a `category_ids` → competitive structure: who leads, at what share, ASP, and growth. This is the backbone of the positioning read.
- `analyze_price_tiers` → tier-level revenue and growth (underserved or growing price bands).
- `analyze_products` → comparable products and the new-vs-existing dynamic (see techniques below).
- `analyze_attributes` → attribute whitespace — **but verify before trusting it** (see techniques below).
- keyword tools → demand with weak or no incumbent supply.

Anchor windows to the MCP's latest complete week (default trailing range vs. the same window a year ago). Don't hand-compute "now."

**Techniques learned (use these to find the differentiation signal):**
- **Verify attribute fields before relying on them.** Amazon's structured attribute fields vary in coverage and granularity — `material` can blend blade/handle/packaging materials, and some fields (e.g. `metal_type`) are sparsely populated. Run `analyze_attributes` in `discover` mode to check coverage, drill only the fields with solid coverage, and prefer title-text search for feature sizing (next bullet) when a field is thinly populated.
- **To size demand for a specific feature/material, search the title text instead.** Use `analyze_products` with `product_query="<feature>"` (e.g. a specific premium steel, "cordless", "refillable") and `aggregate=true` for total revenue + ASP + growth. This is cleaner than the structured attribute and shows who already supplies it.
- **Launch-cohort split = the cadence-vs-durability signal.** `analyze_products` with `group_by="launch_cohort"` returns `new` vs `existing` revenue. If existing (>1yr) products dominate revenue and carry the review mass, the category rewards durable, trusted heroes — not fast SKU churn. This directly shapes the differentiation thesis (and tells you whether a fast-cadence rival's model actually wins).
- **Top-products pull characterizes what wins.** `analyze_products` sorted by revenue, `detail_level="standard"` (gives brand, price, launch date, rating, reviews) reveals the real price points and feature hooks — the gift/impulse floor, the premium ceiling, the feature that sells. Anchor the positioning map on these, not on guesses.

**On/off-Amazon branching:**
- **On Amazon** — measure the brand's own share, portfolio, and price position directly; base capture rates on real category share.
- **Off Amazon** — Jungle Scout still sizes categories and competitors; you can't see the brand's own numbers. Lean on web research and category comparables; flag every brand-level claim as web-sourced; bias capture conservative.

## Step 3 — Generate opportunities (think across the whole taxonomy)

Breadth is the point. Scan all six lenses before settling on five — don't return five flavors of one move.

1. **Assortment gap in a proven category** — a price tier, format, pack, variant, or attribute the brand/category underserves. *Highest data backing.*
2. **Adjacent category expansion** — a nearby category where comparable brands extend or the brand's equity/keywords already pull demand.
3. **Attribute / feature whitespace** — high demand, weak/fragmented supply (no dominant owner).
4. **Bundle / multipack / regimen** — recombining proven demand into a higher-value unit (often an *attach* play riding the bigger wins).
5. **Emerging niche** — a fast-growing category/attribute where incumbents are still weak.
6. **Blue-sky / net-new** — no direct analog; grounded in a trend signal. *Always Low confidence — at most one or two.*

## Step 4 — Differentiate, then score and rank

This is where sizing and the right-to-win come together. **Read `references/differentiation.md` before writing the brief.**

**4a. Name the brand's strength stack — once.** From the web research and brand knowledge, list the 4–6 things the brand does better than rivals and that rivals **can't easily copy** (e.g. provenance/warranty, a proprietary mechanism, serviceability, category-creator DNA, distribution/brand reach, a gifting franchise). This stack is the through-line of the whole brief.

**4b. Classify the brand's presence in each space — three states, not two.** Using the catalog map from Step 2, decide which case each opportunity is, because it changes both the framing and the capture rate:
- **(a) Brand doesn't make it** → genuine whitespace; frame as "enter a new space"; conservative new-entrant capture (1–3%).
- **(b) Brand makes it but it's catalogued elsewhere, sells mostly off-Amazon, or holds low share in the node** → **NOT greenfield.** The gap is presence/merchandising/discoverability — or the need for a *product-first* version (e.g. a standalone knife vs a multitool-with-a-blade). Frame it as "you make this but you're invisible *here*," not "you're absent." The brand has permission and adjacent SKUs, so it isn't a pure new entrant — don't auto-apply the 1–3% anchor; justify the rate.
- **(c) Truly absent from both the category and the catalog** → whitespace, framed like (a).

Only (a) and (c) are real "new aisle" plays. Misreading (b) as greenfield is the failure this step exists to prevent.

**4c. For each opportunity, build the differentiation layer:**
- **What we'd make** — the concrete product, not the category.
- **Strengths it uses** — tag which stack items it leverages. *The opportunities that leverage the most unique strengths should be the strongest; one that uses almost none is a weak bet even in a big market — say so and let it rank low.* This is the integration test (the classic trap: a large, growing category the brand has no right to win).
- **Who it beats, and why** — name the key rival(s) and the gap they leave (their lane, price/ASP from `analyze_brands`, posture from web). Be honest when the answer is "we mostly can't" — that's how a tempting-but-weak idea earns its low rank.

**4d. Size it** (Amazon-validated floor → all-channel prize → 3/6/9/12 scenarios; method in `references/opportunity-ceiling.md`).

**4e. Score** Confidence (High/Med/Low, tied to the *floor*) and Feasibility (High/Med/Low, fit vs Step 1 constraints), one line each on *why*.

**Rank by a blended impact × feasibility score** (1–3 each, rank on the product), where impact follows the user's horizon:
- **"Wins this year"** → impact = base-case 12-month cumulative revenue.
- **"12-month bets fine" / "go broad"** → impact = size-of-prize (all-channel prize / exit run-rate), *not* in-window cumulative — otherwise lead time buries the big slow bets the user asked to prioritise.

Confidence is **not** part of the rank — shown alongside as a caveat. Sanity-check the result against the strength tags: the ranking and the unique-strength count should broadly agree; if a top-ranked idea leverages no real strength, re-examine it.

## Step 5 — Write the integrated brief

**Default to an HTML artifact.** This skill owns the *structure* — the sections and the card layout below; hand all *visual styling* to the `jungle-scout-visualizer` skill (the Cobalt palette and focal-vs-gray contrast, the metric callout, growth/signal pills, the evidence-table treatment, any embedded chart templates, and the light/dark swap), and read its `references/visuals.md` before building. The two compose — this skill decides what appears and in what order, the visualizer decides how it looks; don't hardcode a separate palette. Everything lives in ONE document — do not ship sizing and differentiation as separate files. The page should:

- **Hero** — a thesis line (the strategic finding), the single biggest all-channel prize as the headline number, and 2–3 framing stats (brand's category rank/share, category size+growth, brand's share of the adjacent market).
- **The strength stack** — a short labeled row of the 4–6 hard-to-copy strengths from Step 4a. This is the spine; every opportunity card tags back to it.
- **The ranked slate** — one card per opportunity, each carrying *all* of: rank + type tag; **Market** (size, growth, how open) ; **What we'd make** (the product); **Why we win** (the rival + the gap); **Strengths used** (tags into the stack); the all-channel prize (large) with the validated Amazon floor beneath (small); and confidence / feasibility / lead-time pills.
- **Optional competitive view** — a positioning map (judgment-built; axes like price × product philosophy) and/or per-rival reference cards (lane, ASP, the gap they leave). Flag the map as judgment, not a Jungle Scout output. Fold this in only if it earns its space; for folders/EDC-type markets it usually does.
- **Two footer panels** — "what the data ruled out" (kills ideas on evidence — a declining format/tier) and "validate next" (cheapest tests first).
- **A method / sourcing footnote** — window, capture rates, multiplier, ramp, and what came from Jungle Scout vs web/judgment.

Design neutral unless the user wants it on their own brand. Keep copy exec-tight; numbers do the talking.

**Lighter alternative:** if the user asked for inline/quick output, render the same integrated content as a chat brief.

**Plain-language mode.** If the user asks for a reading level (e.g. "5th grade"), "plain"/"simple" language, or "assume terms aren't understood": keep the structure identical and simplify only the words — glossary up front, define terms before first use, short active sentences, spell out abbreviations, round numbers. Full rules and the plain-word swap list are in `references/differentiation.md` §5.

## Guardrails

- **Never invent data.** Missing data → name it in ASSUMPTIONS and downgrade confidence.
- **Round and range.** $1.8–2.4M, not $2,037,412.
- **Integrate differentiation; don't bolt it on.** Every opportunity = market + product + right-to-win + size, on one card. A big market with no right-to-win is a weak opportunity — rank it low and say why.
- **Never read "absent" from a node-scoped number.** Low revenue in node X means low share *of that node*, not that the brand doesn't make the product (it may be catalogued in its home node, sell off-Amazon, or have just launched). Verify against the brand's full catalog (Step 2) before calling anything greenfield, and state precisely what was measured ("~0% of the Pocket Knives node on Amazon").
- **Positioning maps are judgment.** Build them on the data (ASPs, shares, hero products) but label lane placements directional.
- **At most one or two blue-sky ideas**, always Low confidence. The other three-to-four should be evidence-backed.

## Next Steps

After delivering the brief, don't just stop. Propose **2–3 concrete follow-ups grounded in the slate you just produced**, and ask the user which to pursue. If the environment supports a multiple-choice prompt or form, present the options that way; otherwise list them and ask. Draw from:

- **Deep-dive the top opportunity** — a full teardown of the #1 idea: the rival's exact lane and gap, a capture-rate sensitivity (how the rank moves at ±2pp), and the cheapest validation test from the "validate next" panel.
- **Benchmark the target category** — hand off to `benchmark-brand` for the category the leading opportunity sits in (competitive landscape, price tiers, search visibility) before committing.
- **Check the current position** — if the brand is on Amazon, route to `share-diagnosis` to understand where it's winning or losing today, so the bet is placed with eyes open.
- **Tighten or widen the slate** — re-run with the brand's real constraints (margin floor, off-limits categories) if the first pass was unconstrained, or focus a single lens (e.g. attribute whitespace only) for more depth.

Make each offer specific to the finding (e.g. "deep-dive the #1 idea — $2.4M all-channel prize, ranks on a 4% capture"), not generic. Then carry out whichever the user picks.

## Reference files

- `references/differentiation.md` — the strength stack (the brief's spine), the per-opportunity differentiation layer, the competitor positioning read and the positioning-map recipe, what Jungle Scout can vs. can't carry, and the plain-language output mode (§5). Read before Step 4.
- `references/opportunity-ceiling.md` — the sizing method: opportunity ceiling by opportunity type, the all-channel-prize channel multiplier, lead time, ramp, and the 3/6/9/12 assembly with a worked example and sensitivity note. Read before Step 4d.
