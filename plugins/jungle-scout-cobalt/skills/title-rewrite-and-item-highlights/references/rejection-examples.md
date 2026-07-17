# Keyword relevance screen — accept / reject cases

> RECONSTRUCTED 2026-06-15. The original reference (with your real per-category
> pilot cases) was unreachable when this bundle was built. The patterns below
> are faithful to the screen described in SKILL.md Stage 4, but you should merge
> your original accept/reject examples back into this file — the concrete,
> category-specific cases are what make the screen reliable.

The relevance screen runs on every gap candidate **before** it touches a title.
A keyword passes only if BOTH hold:

1. **Quantitative** — the brand's SOV is materially below the keyword's leading
   brands (or absent), so there's real share to win.
2. **Qualitative** — the brands owning the SERP sell a *comparable product*, and
   the keyword makes no claim this product can't support.

A high volume or high relative-value score is **not** a pass. Score doesn't know
what the product is.

## Reject patterns

**Different product.** The keyword describes an adjacent but distinct item.
- Reject "sliding mitt" for a *fielding glove* — a sliding mitt is a separate
  product worn for base-stealing, not a fielding glove. SERP is dominated by
  sliding-mitt makers; the customer searching it does not want a fielder's glove.
- Reject "weighted baseballs" for *regular baseballs* — weighted balls are a
  training-specific SKU; claiming it misrepresents the product.

**Unsupported claim / spec.** The keyword asserts an attribute the listing can't
substantiate.
- Reject "UV400 sunglasses" if the feed has no UV rating to back it. Licensing
  the attribute is the binding constraint — if you can't prove it, it can't go in
  the title. (Route to the user as an attribute question in Stage 0.)

**Demand-side intent, not product description.** The keyword captures buyer
*intent* rather than what the product *is*.
- Reject "gift", "gifts for her", "party favors", "stocking stuffer" — these are
  occasion/intent terms. Amazon's rule bars demand-side intent words that don't
  describe the product, and they read as spam in a title.

**SERP noise / wrong neighborhood.** The brands ranking for the term sell
something unrelated; the keyword is ambiguous or polluted.
- Reject a term whose top SOV holders are a different category entirely — the
  shared token is coincidental, not real shared demand.

## Accept patterns

**Product-specific differentiator the brand doesn't own.** The strongest accepts.
- Accept "rhinestone sunglasses" for a rhinestone-trimmed frame when the brand
  doesn't index on it and SOV is fragmented (no leader above ~20%). This is the
  keyword-first differentiator win from Stage 5: the higher-volume sibling of a
  term the brand already weakly ranks for ("bling").

**Verified generic gap with real share to take.** A head/category term the brand
is absent from and that accurately describes the product.
- Accept the category noun ("sunglasses") only if it isn't already trivially
  present in every title — otherwise it's not a gap, just table stakes.

## When in doubt

Reject. A title with one fewer keyword is recoverable; a title making a claim the
product can't support, or chasing the wrong buyer, costs conversion and risks a
compliance flag. Log every reject — with its reason and SOV evidence — in
`evidence-trail.md` so any keyword choice can be challenged and defended.
