#!/usr/bin/env python3
"""Keyword pool set-math for the title-rewrite-and-item-highlights skill.

Pools are JSON files of rows from search_keywords_by_asin — append each page of
each sort order to the same file via `merge`; dedupe happens here. All analysis
runs on disk so full pools never enter model context.

Usage:
  pool_tools.py merge out.json page1.json page2.json ...   # dedupe+merge pages
  pool_tools.py gap brand.json comp.json [options]         # stratified gap candidates
  pool_tools.py cluster pool.json [--synonyms map.json]    # surface-form clusters

gap options:
  --floor N            volume floor for candidates (default 500)
  --nouns "a,b,c"      product nouns/attributes (multi-word allowed, e.g.
                       "baseball glove"); mid-tail bucket = candidates whose
                       tokens include one of these (this is where
                       product-specific differentiators live)
  --synonyms map.json  semantic-sibling map {canonical: [siblings...]} so
                       "bling"/"rhinestone"/"sparkly" collapse to one cluster;
                       multi-word siblings work too, e.g.
                       {"tball": ["t ball", "tee ball"]}
  --head N             size of the head-term bucket (default 10)
  --mid N              size of the mid-tail bucket (default 15)

The gap command returns TWO buckets to verify, not a raw top-N:
  head     — top-volume clusters (usually mega-generic; cheap to confirm/reject)
  mid_tail — top product-noun-matched clusters (where differentiators hide and
             raw top-N misses them)

Row shape expected: {"id", "name", "estimated_exact_search_volume",
                     "quarterly_trend", "relative_value_score"}
(extra keys pass through untouched)
"""
import json, re, sys
from pathlib import Path


def load(p):
    data = json.loads(Path(p).read_text())
    return data.get("keywords", data) if isinstance(data, dict) else data


def load_synonyms(path):
    """{canonical: [sibling, ...]} -> {sibling_word: canonical_word}.
    Multi-word siblings are normalized to underscores so they survive tokenizing."""
    if not path:
        return {}
    raw = json.loads(Path(path).read_text())
    out = {}
    for canon, sibs in raw.items():
        c = re.sub(r"[^a-z0-9]+", "_", canon.lower()).strip("_")
        for s in [canon, *sibs]:
            key = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
            out[key] = c
    return out


def normalize(name: str, synmap=None) -> str:
    """Cluster key: collapse hyphen/plural variants so 'tball bat' and
    'tball bats' count as one demand cluster. With a synonym map, semantic
    siblings ('bling'/'rhinestone') and multi-word spacing variants
    ('t ball'/'tee ball' -> 'tball') also collapse to one key."""
    s = re.sub(r"[^a-z0-9 ]", " ", name.lower())
    for key, canon in (synmap or {}).items():
        if "_" in key:
            s = s.replace(key.replace("_", " "), canon)
    words = []
    for w in s.split():
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        w = (synmap or {}).get(w, w)
        words.append(w)
    return " ".join(sorted(words))


def vol(r):
    return r.get("estimated_exact_search_volume") or 0


def merge(out, paths):
    seen, rows = {}, []
    for p in paths:
        for r in load(p):
            if r["id"] not in seen:
                seen[r["id"]] = True
                rows.append(r)
    Path(out).write_text(json.dumps(rows))
    print(f"{out}: {len(rows)} unique keywords from {len(paths)} pages")


def build_clusters(rows, synmap):
    """Cluster rows by normalized key; keep highest-volume surface form on top."""
    clusters = {}
    for r in rows:
        clusters.setdefault(normalize(r["name"], synmap), []).append(r)
    out = []
    for forms in clusters.values():
        forms.sort(key=lambda r: -vol(r))
        head = dict(forms[0])
        head["other_surface_forms"] = [f["name"] for f in forms[1:]]
        out.append(head)
    out.sort(key=lambda r: -vol(r))
    return out


def matches_noun(name, nouns):
    stem = lambda t: t[:-1] if len(t) > 3 and t.endswith("s") and not t.endswith("ss") else t
    toks = {stem(t) for t in re.sub(r"[^a-z0-9 ]", " ", name.lower()).split()}
    return any(all(stem(w) in toks for w in n.split()) for n in nouns)


def gap(brand_p, comp_p, floor, nouns, synmap, head_n, mid_n):
    brand, comp = load(brand_p), load(comp_p)
    brand_norms = {normalize(r["name"], synmap) for r in brand}
    cands = [r for r in comp
             if normalize(r["name"], synmap) not in brand_norms
             and vol(r) >= floor]
    clusters = build_clusters(cands, synmap)

    head = clusters[:head_n]
    head_keys = {normalize(r["name"], synmap) for r in head}
    rest = [r for r in clusters if normalize(r["name"], synmap) not in head_keys]
    if nouns:
        mid = [r for r in rest if matches_noun(r["name"], nouns)][:mid_n]
        mid_label = f"product-noun-matched ({', '.join(nouns)})"
    else:
        mid = rest[:mid_n]
        mid_label = "top remaining (NO --nouns given; pass product nouns for precision)"

    print(json.dumps({"head": head, "mid_tail": mid}, indent=1))
    print(f"\n# {len(clusters)} gap clusters (brand pool: {len(brand)} kws, "
          f"competitor pool: {len(comp)} kws, floor {floor}, "
          f"synonyms: {'on' if synmap else 'off'}).", file=sys.stderr)
    print(f"# head bucket: {len(head)} top-volume clusters (usually generic — "
          f"confirm trivially-present or reject).", file=sys.stderr)
    print(f"# mid_tail bucket: {len(mid)} {mid_label} — "
          f"differentiators hide here.", file=sys.stderr)
    print(f"# NEXT: verify BOTH buckets with get_keyword_sov + relevance screen. "
          f"Set difference alone is NOT evidence of a real gap. "
          f"For each family's differentiator, also run the keyword-first sibling "
          f"audit (search_keywords_by_keyword) — pool math can't invent a "
          f"higher-volume synonym that isn't already in either pool.",
          file=sys.stderr)


def cluster(pool_p, synmap):
    clusters = {}
    for r in load(pool_p):
        clusters.setdefault(normalize(r["name"], synmap), []).append(r["name"])
    for k, names in sorted(clusters.items()):
        if len(names) > 1:
            print(f"{names}")


def _opt(flag, default=None):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "merge":
        merge(sys.argv[2], sys.argv[3:])
    elif cmd == "gap":
        floor = int(_opt("--floor", 500))
        head_n = int(_opt("--head", 10))
        mid_n = int(_opt("--mid", 15))
        nouns_arg = _opt("--nouns")
        nouns = [n.strip().lower() for n in nouns_arg.split(",")] if nouns_arg else []
        synmap = load_synonyms(_opt("--synonyms"))
        gap(sys.argv[2], sys.argv[3], floor, nouns, synmap, head_n, mid_n)
    elif cmd == "cluster":
        synmap = load_synonyms(_opt("--synonyms"))
        cluster(sys.argv[2], synmap)
    else:
        print(__doc__)
