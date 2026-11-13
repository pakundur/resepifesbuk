#!/usr/bin/env python3
"""
Wired ad engine v2 — per-link copy, per-row rotation, one-ad-per-page guard.

Guarantees enforced here:
  1. ONLY the 16 products in affiliate_links.json may render. The 125 other
     keywords in the general copy bank can never produce an ad.
  2. Every rendered card carries all 3 links, and each link brings its OWN copy
     block (ad_copy_per_link).
  3. Row order rotates per recipe by a stable hash, so aff1 is not always row 1.
     Same recipe always gets the same order (cacheable, no mid-read swap).
  4. ONE AD PER PAGE when the recipe triggers only one wired product (303
     recipes). Two ads for the same product on one page reads as spam.

Trigger sources per product:
  - appliance / equipment -> scanned in steps + tips, because recipes say
    "panaskan kuali" but never list kuali as an ingredient.
"""
import json, hashlib, re
from pathlib import Path

import ad_copy_per_link as COPYBANK

BASE = Path(__file__).resolve().parent
DATA = json.loads((BASE / "affiliate_links.json").read_text())["products"]

KW2KEY = {p["keyword"]: k for k, p in DATA.items()}

PATTERNS = {
    "oven":        r"\boven\b|\bketuhar\b",
    "mixer":       r"\bmixer\b|\bpengadun\b",
    "blender":     r"\bblender\b",
    "pengisar":    r"\bpengisar\b|\bgrinder\b",
    "ricecooker":  r"\brice ?cooker\b|\bperiuk nasi elektrik\b",
    "grillpan":    r"\bgrill\b|\bpemanggang\b",
    "microwave":   r"\bmicrowave\b",
    "freezer":     r"\bfreezer\b|\bpeti sejuk beku\b",
    "waffle":      r"\bwaffle\b",
    "takoyaki":    r"\btakoyaki\b",
    "pressure":    r"\bpressure ?cooker\b|\bperiuk tekanan\b",
    "kuali":       r"\bkuali\b",
    "periuk":      r"\bperiuk\b",
    "loyang":      r"\bloyang\b",
    "kukus":       r"\bpengukus\b|\bkukus\b",
    "acuan":       r"\bacuan\b",
}

ORDER = [
    "oven", "pressure", "ricecooker", "freezer", "microwave",
    "mixer", "blender", "pengisar", "grillpan", "waffle", "takoyaki",
    "kuali", "periuk", "kukus", "loyang", "acuan",
]

COMPILED = {k: re.compile(v) for k, v in PATTERNS.items()}


def wired_keywords():
    return set(KW2KEY)


def candidates(recipe):
    """Wired product keys triggered by this recipe's method text, best-first."""
    method = " ".join((recipe.get("steps") or []) + (recipe.get("tips") or [])).lower()
    if not method:
        return []
    return [k for k in ORDER if COMPILED[k].search(method)]


def _hash(*parts):
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest(), 16)


def build_creative(key, slug, slot):
    """
    Attach per-link copy + all 3 links with a rotated row order.

    Returns dict with 'rows': list of 3 dicts, each carrying that link's own
    copy block. rows[0] is the visual primary.
    """
    p = DATA[key]
    links = p["links"]
    slots = COPYBANK.blocks(key)

    rot = _hash(slug, slot, "rot") % 3
    order = list(range(3))
    order = order[rot:] + order[:rot]

    rows = []
    for pos in order:
        s = slots[pos]
        rows.append({
            "aff": pos + 1,              # which affiliate link (1..3)
            "url": links[pos],
            "hook": s["hook"],
            "promise": s["promise"],
            "btn": s["btn"],
            "note": s.get("note", ""),
            "src": s["src"],
        })

    return {
        "key": key,
        "label_bm": p["label_bm"],
        "label": COPYBANK.label(key),
        "search_bm": p["search_bm"],
        "search_en": p["search_en"],
        "rows": rows,
        "primary": rows[0],
        "rotation": rot,
        "all_links": links,
        "hrefs": [r["url"] for r in rows],
    }


def pick(recipe, slug, slot, exclude=()):
    """
    Deterministic pick. Returns None when nothing wired matches, or when the
    caller's `exclude` set already covers every candidate (one-ad-per-page rule).
    """
    cands = [c for c in candidates(recipe) if c not in exclude]
    if not cands:
        return None
    h = _hash(slug, slot)

    # R2 / K2 / S1 / K3 prefer a product different from R1
    if slot in ("R2", "K2", "K3", "S1") and len(cands) > 1:
        first = pick(recipe, slug, "R1")
        if first:
            rest = [c for c in cands if c != first["key"]]
            if rest:
                cands = rest

    return build_creative(cands[h % len(cands)], slug, slot)


def page_ads(recipe, slug, variant_map):
    """
    Resolve every ad slot for ONE page, honouring the one-ad-per-page rule.

    variant_map: {"R1": "three", "R2": "compact", ...}

    Returns list of (slot, creative) in slot order. If the recipe triggers only
    one wired product, only the FIRST slot in order renders; the rest are
    suppressed so the same product never appears twice on a page.
    """
    n_cands = len(candidates(recipe))
    rendered = []
    used = set()

    for slot in variant_map:
        if n_cands <= 1 and rendered:
            break  # one ad per page
        c = pick(recipe, slug, slot, exclude=used)
        if c:
            used.add(c["key"])
            rendered.append((slot, c))
    return rendered


if __name__ == "__main__":
    import collections
    REC = json.load(open(BASE / "src/content_fix.json"))

    served = collections.Counter()
    none = 0
    rotspread = collections.Counter()
    for slug, rec in REC.items():
        vm = {"R1": "three", "R2": "compact"}
        ads = page_ads(rec, slug, vm)
        if not ads:
            none += 1
        for slot, c in ads:
            served[c["key"]] += 1
            rotspread[c["rotation"]] += 1

    total = len(REC)
    print(f"recipes: {total}")
    print(f"recipes with >=1 ad: {total-none} ({100*(total-none)/total:.1f}%)")
    print(f"recipes with no ad:  {none} ({100*none/total:.1f}%)")
    print(f"\nads rendered: {sum(served.values())}")
    print("\nper-product impressions:")
    for k, n in served.most_common():
        print(f"  {n:4d}  {k:12s} {DATA[k]['label_bm']}")
    print("\nrow-1 rotation spread:", dict(sorted(rotspread.items())))

    # fairness: how often is each aff link in row 1?
    aff1 = collections.Counter()
    for slug, rec in REC.items():
        for slot, c in page_ads(rec, slug, {"R1": "three"}):
            aff1[c["primary"]["aff"]] += 1
    print("row-1 position by affiliate link:", dict(sorted(aff1.items())))
