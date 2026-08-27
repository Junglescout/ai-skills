#!/usr/bin/env python3
"""Deterministic title compliance linter for the title-rewrite-and-item-highlights skill.

Rules load from ../assets/title-rules.json — never hardcode them here, so a
verified rules update changes behavior without touching code.

Usage:
  lint_titles.py --census titles.csv          # compliance census of CURRENT titles
                                              # (csv needs: asin,title[,revenue])
  lint_titles.py --check titles.csv           # lint PROPOSED titles
                                              # (csv needs: asin,new_title[,item_highlights][,keywords])
                                              # keywords: semicolon-separated, enables
                                              # exact-phrase vs token coverage report
                                              # item_highlights: required non-empty, <=125 chars,
                                              # comma-separated phrases (see title-rules.json)

Exit code 1 if any proposed title fails — wire this into the generate/regenerate loop.
"""
import argparse, csv, json, re, sys
from collections import Counter
from pathlib import Path

RULES = json.loads((Path(__file__).parent.parent / "assets" / "title-rules.json").read_text())


def lint(title: str, brand: str | None = None) -> list[str]:
    errs = []
    if len(title) > RULES["max_length"]:
        errs.append(f"LENGTH {len(title)}>{RULES['max_length']}")
    bad = sorted(set(title) & set(RULES["banned_chars"]))
    if bad:
        errs.append(f"BANNED_CHARS {bad}")
    if "|" in title and RULES["pipe_char"]["policy"] == "strip":
        tag = "PIPE" + ("" if RULES["pipe_char"].get("verified") else "_UNVERIFIED_RULE")
        errs.append(tag)
    words = re.findall(r"[a-z0-9']+", title.lower())
    exempt = set(RULES["repeat_exempt_words"])
    if RULES["numerals_in_repeat_rule"]["policy"] != "count":
        words = [w for w in words if not w.isdigit()]
    rep = [w for w, c in Counter(w for w in words if w not in exempt).items()
           if c > RULES["max_word_repeats"]]
    if rep:
        errs.append(f"REPEATED>{RULES['max_word_repeats']} {rep}")
    low = title.lower()
    promo = [p for p in RULES["no_promotional_claims"] if p in low]
    if promo:
        errs.append(f"PROMO_CLAIM {promo}")
    if brand and RULES["brand_first"] and not title.lower().startswith(brand.lower()):
        errs.append("BRAND_NOT_FIRST")
    return errs


def kw_coverage(keyword: str, title: str) -> str:
    """Report exact-phrase vs token coverage. Phrase order matters for exact-match
    indexing, so don't let a tokens-only hit masquerade as a phrase match."""
    norm = lambda s: re.sub(r"[^a-z0-9 ]", " ", s.lower().replace("-", "")).split()
    t_words, k_words = norm(title), norm(keyword)
    k_words = [w for w in k_words if w not in set(RULES["repeat_exempt_words"])]
    if not k_words:
        return "empty"
    joined_t, joined_k = " ".join(t_words), " ".join(norm(keyword))
    if joined_k and joined_k in joined_t:
        return "exact_phrase"
    stem = lambda w: w.rstrip("s")
    t_stems = {stem(w) for w in t_words}
    hits = sum(1 for w in k_words if stem(w) in t_stems)
    return f"tokens {hits}/{len(k_words)}"


def _content_tokens(s: str) -> list[str]:
    """Content tokens for title-vs-highlights overlap: lowercased, stopwords
    dropped, light plural stemming (the same stemming the title coverage uses)."""
    stop = set(RULES["repeat_exempt_words"])
    toks = re.findall(r"[a-z0-9]+", s.lower())
    return [t.rstrip("s") if len(t) > 3 else t for t in toks if t not in stop]


def lint_highlights(ih: str | None, title: str = "") -> list[str]:
    """Validate the item_highlights field against title-rules.json's
    'item_highlights' block. Highlights are required non-empty by default (a
    blank fails), must fit the length limit, and must add information the title
    does not already carry rather than simply restating it."""
    cfg = RULES.get("item_highlights", {})
    ih = (ih or "").strip()
    errs = []
    if not ih:
        if cfg.get("required", True):
            errs.append("ITEM_HIGHLIGHTS_EMPTY")
        return errs
    maxlen = cfg.get("max_length", 125)
    if len(ih) > maxlen:
        errs.append(f"ITEM_HIGHLIGHTS_LENGTH {len(ih)}>{maxlen}")
    if cfg.get("reuse_banned_chars", True):
        bad = sorted(set(ih) & set(RULES["banned_chars"]))
        if bad:
            errs.append(f"ITEM_HIGHLIGHTS_BANNED_CHARS {bad}")
    if cfg.get("reuse_promotional_claims", True):
        low = ih.lower()
        promo = [p for p in RULES["no_promotional_claims"] if p in low]
        if promo:
            errs.append(f"ITEM_HIGHLIGHTS_PROMO {promo}")
    if cfg.get("format") == "comma_separated_phrases" and (ih.endswith(".") or ". " in ih):
        errs.append("ITEM_HIGHLIGHTS_SENTENCE_STYLE")
    if cfg.get("forbid_title_duplication") and title:
        title_toks = set(_content_tokens(title))
        h_toks = set(_content_tokens(ih))
        if h_toks:
            new = h_toks - title_toks
            if not new:
                errs.append("ITEM_HIGHLIGHTS_DUPLICATES_TITLE")
            else:
                frac = len(new) / len(h_toks)
                minf = cfg.get("min_new_token_fraction", 0.5)
                if frac < minf:
                    errs.append(f"ITEM_HIGHLIGHTS_MOSTLY_TITLE {frac:.0%}<{minf:.0%} new; "
                                f"repeated={sorted(h_toks & title_toks)}")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--census", action="store_true")
    mode.add_argument("--check", action="store_true")
    ap.add_argument("--brand", default=None)
    args = ap.parse_args()

    with open(args.csv_path, newline="") as f:
        rows = list(csv.DictReader(f))
    if not RULES.get("verified"):
        print(f"NOTE: rules version {RULES['version']} is UNVERIFIED — "
              f"surface unverified-rule hits in flags.md\n")

    if args.census:
        over = [r for r in rows if len(r["title"]) > RULES["max_length"]]
        rev_known = all("revenue" in r and r["revenue"] for r in rows)
        print(f"{len(over)}/{len(rows)} titles over {RULES['max_length']} chars")
        if rev_known:
            at_risk = sum(float(r["revenue"]) for r in over)
            total = sum(float(r["revenue"]) for r in rows)
            pct = (100 * at_risk / total) if total else 0
            print(f"Revenue at risk: ${at_risk:,.0f} of ${total:,.0f} ({pct:.0f}%)")
        for r in sorted(over, key=lambda r: len(r["title"]), reverse=True)[:10]:
            print(f"  {r['asin']} {len(r['title'])}ch")
        return

    fails = 0
    for r in rows:
        title = r.get("new_title") or r["title"]
        errs = lint(title, args.brand) + lint_highlights(r.get("item_highlights"), title)
        if errs:
            fails += 1
            print(f"FAIL {r['asin']}: {errs} :: {title}")
        for kw in (r.get("keywords") or "").split(";"):
            if kw.strip():
                print(f"  {r['asin']} kw[{kw.strip()}] -> {kw_coverage(kw.strip(), title)}")
    print(f"\n{len(rows)} titles, {fails} failures")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
