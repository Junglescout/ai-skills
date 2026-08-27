# Differentiation, positioning & plain-language output

How to make each opportunity carry a *right to win*, not just a market size — and how to render the brief in plain language when asked. Read this with the main SKILL.md (Step 4 and Step 5).

## 1. The strength stack (the spine of the brief)

A whitespace opportunity is only real if the brand can build something rivals can't easily copy. Before scoring, name the brand's **hard-to-copy strengths once**, then tag every opportunity with the ones it uses.

**How to derive it** (from web research + brand knowledge, not Jungle Scout):
- 4–6 items, each a *durable* advantage a competitor can't bolt on next quarter.
- Sources of durable advantage to look for: provenance / country-of-origin, a lifetime or long warranty, a proprietary mechanism or platform, serviceability / repairability / replaceable parts, category-creator or domain DNA, manufacturing capability, distribution footprint, brand fame, a gifting franchise, an installed base.
- Write each as a plain phrase the team would recognise (e.g. "Made in USA + lifetime promise", "the magnetic one-hand mechanism", "parts you can replace", "multitool know-how", "famous, trusted name").

**The integration test.** Tag each opportunity with the stack items it leverages, then check:
- Opportunities that leverage **more unique strengths** should rank **higher**. The ranking (impact × feasibility) and the strength-count should broadly agree.
- An opportunity that uses **few or no** unique strengths is a **weak bet even in a big, growing market** — the classic trap. Keep it in the slate if it's instructive, but rank it low and say plainly why (e.g. "uses the fewest strengths — that's why it ranks low; play it as a bundle/attach, not a main bet").
- If a *top-ranked* idea leverages no real strength, something is wrong — re-examine the sizing or the feasibility read.

This is what turns "here are 5 big markets" into "here are 5 markets where the brand has an unfair edge."

## 2. Per-opportunity differentiation layer

On every card, alongside the size and scores:

- **What we'd make** — the concrete product, described in one or two sentences. Not "enter folding knives" but "a premium folding knife with the magnetic one-hand action, a replaceable blade, made in the USA, with the lifetime promise — plus an engravable gift version."
- **Strengths used** — the tags from §1.
- **Who it beats, and why** — name the key rival(s) and the *gap* they leave. Pull their price posture (ASP) and share from `analyze_brands` scoped to the category; pull their stated lane/positioning from web. Frame as "beats X by …, beats Y with …". When the honest answer is "we mostly can't out-position the incumbent here," say so — that candor is how a tempting-but-weak idea earns its low rank.

## 3. Competitor positioning read

Jungle Scout gives you the *quantitative* competitive structure; web gives the *qualitative* lane.

- **From Jungle Scout** (`analyze_brands` on the category, `analyze_products` for heroes): each rival's revenue, share, ASP, growth, product count; the top-selling products and their price points / feature hooks; the new-vs-existing split (does cadence or durability win?).
- **From web + reasoning**: what each rival *says* it is (heritage, tactical, design-led, value, premium), where it's made, its franchise. Jungle Scout measures sales structure, not stated strategy or review sentiment.
- **Per-rival reference cards** (optional but strong): brand · lane (price/posture/origin) · what it does well · the gap it leaves for the focal brand.

**The positioning map** (optional signature visual):
- Pick two axes that actually sort the market. Common pair: price (value → premium) on x; product philosophy (disposable/fashion → engineered/built-to-keep) on y. Choose axes the *data and the brand's edge* make meaningful, not generic ones.
- Place rivals using real anchors (ASPs, shares, hero-product prices). Mark the brand's *target* zone — usually the thin, defensible corner an incumbent only half-owns.
- **Label the map as judgment**, built on the data but not a direct Jungle Scout output. Lane placements are directional.

## 4. What Jungle Scout can and can't carry (state this in the method note)

| Supplies (use directly) | Comes from web + reasoning |
| Category size, growth, price tiers | Competitor stated strategy / messaging |
| Brand & competitor share, ASP, growth, product counts | Review-text sentiment / what shoppers complain about |
| Top products, price points, launch dates, ratings/review counts | The focal brand's own strengths, warranty, manufacturing |
| New-vs-existing launch dynamics | The brand's off-Amazon business (only Amazon is measured) |
| Feature/material demand via title search (`product_query`) | Anything not yet for sale |

Attribute caveat: Amazon's structured attribute fields (`material`, `metal_type`, etc.) vary in coverage — verify in `discover` mode and prefer title-text search for feature sizing when a field is thinly populated.

## 5. Plain-language output mode

Trigger when the user asks for a reading level (e.g. "5th grade"), "plain"/"simple" language, or "assume terms aren't understood until defined." Keep the *structure* identical (strength stack → integrated cards → ruled-out → validate-next → sourcing note); simplify only the words.

Rules:
- **Glossary up front** defining the core terms; define any other term **inline at first use**. Assume nothing is known until defined.
- Short, active sentences. One idea per sentence.
- Spell out abbreviations and round numbers ($851,000, not $851K; "+25%" is fine but gloss it as "selling more than last year" once).
- Keep brand names and dollar figures as-is — those are facts, not jargon.

Plain-word swaps for this skill's recurring jargon:

| Jargon | Plain |
| revenue / sales total | "sales" or "money from sales" |
| market size | "how much people spend on that kind of product in a year" |
| growing / declining | "selling more / less than last year" |
| average selling price (ASP) | "usual price" / "what shoppers usually pay" |
| market share | "how much of the sales one brand gets" |
| validated floor / Amazon ceiling | "Amazon guess" (low, safe estimate of yearly Amazon sales) |
| all-channel prize / channel multiplier | "all-in guess" — about 3× the Amazon number, because Amazon is only ~a third of the brand's sales, so the rest spreads across stores, the website, and other countries |
| capture % | "the share of sales we think the brand could win" |
| feasibility | "how doable it is" |
| adjacency / adjacent category | "a nearby kind of product" |
| assortment gap | "a type or price the brand doesn't sell yet" |
| SKU / cadence | "product" / "how fast a brand puts out new products" |
| lead time | "time to launch" |

Define the data source plainly too: "Jungle Scout is a tool that estimates how much products sell on Amazon."
