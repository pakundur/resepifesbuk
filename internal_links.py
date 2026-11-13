"""Build internal links between recipe pages — SINGLE category, no cross-category.

DESIGN (v3)
The site now assigns exactly ONE category per recipe (src/cats.json, produced by
classify.py from the dish's identity). That makes the linking rule trivial and
auditable:

  * A recipe links ONLY to recipes in its own category, plus the same-dish
    variants of itself (always the same category by construction).
  * No cross-category "same meal family" links at all. Removed deliberately:
    family logic (lauk/karbo/manisan) was the last source of soft false
    positives — it could pair Kuih Talam with Pizza because both sat in a broad
    bucket.
  * Same-dish variants (keeper/variant) are still linked even if the classifier
    ever splits them, because "Musang King Brownies" -> "Musang King Brownies
    Versi 2" is a true positive by definition.
  * Sequential "next" navigation stays, labelled as navigation, not as a
    topical recommendation.

Every link therefore has an evidence trail a human can check: same category, or
same dish. Nothing is inferred from shared pantry staples.

Output: src/links.json  {slug: [{slug, anchor, why, reason}]}
Usage:  python internal_links.py
"""
import json, os, re, hashlib, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
CATS = os.path.join(ROOT, "src", "cats.json")
OUT = os.path.join(ROOT, "src", "links.json")

MIN_LINKS = 3          # hard floor per page
MAX_LINKS = 6


def rng(slug):
    return int(hashlib.md5(slug.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def anchor_of(r):
    t = r["title"]
    t = re.sub(r"\s*[-–—]\s*Resepi Mudah.*$", "", t, flags=re.I)
    t = t.split(":")[0].strip()
    t = re.sub(r"^resepi\s+", "", t, flags=re.I)
    return t[:70]


def core_dish(title):
    t = re.sub(r"^resepi\s+|^resipi\s+", "", title.lower())
    t = t.split(":")[0].split(" - ")[0]
    t = re.sub(r"\b(original|ala|paling|mudah|sedap|simple|gerenti|confirm|style|"
               r"versi|resepi|resipi|dari|yang|best|senang|mewah|premium|kedai|"
               r"restoran|hotel|viral|lazat)\b", "", t)
    return re.sub(r"[^a-z ]", " ", t).split()


def main():
    recs = json.load(open(SRC, encoding="utf-8"))
    cats = json.load(open(CATS, encoding="utf-8"))
    by = {r["slug"]: r for r in recs}

    # single category per recipe, from the LLM classifier
    catof = {}
    for r in recs:
        c = (cats.get(r["slug"]) or {}).get("cat")
        if not c:
            raise SystemExit(f"missing category for {r['slug']}")
        catof[r["slug"]] = c

    # ---- same-dish clusters: true positives by definition ----
    clusters = collections.defaultdict(list)
    for r in recs:
        w = core_dish(r["title"])
        if len(w) >= 2:
            clusters[" ".join(w[:3])].append(r["slug"])

    keeper_of, members_of = {}, {}
    for key, mem in clusters.items():
        if len(mem) < 2:
            continue
        best = max(mem, key=lambda s: (len(by[s].get("steps") or []) +
                                       len(by[s].get("ingredients") or []),
                                       -len(by[s]["title"])))
        members_of[best] = [m for m in mem if m != best]
        for m in mem:
            if m != best:
                keeper_of[m] = best

    by_cat = collections.defaultdict(list)
    for r in recs:
        by_cat[catof[r["slug"]]].append(r["slug"])
    for c in by_cat:
        by_cat[c].sort()

    links, stats = {}, collections.Counter()
    for i, r in enumerate(recs):
        slug = r["slug"]
        cat = catof[slug]
        picked, seen = [], {slug}

        def add(target, why, reason):
            if target in seen or target == slug or len(picked) >= MAX_LINKS:
                return False
            if target not in by:
                return False
            # same-dish variants may cross a category boundary in theory; keep them
            if why in ("category", "next") and catof.get(target) != cat:
                return False
            seen.add(target)
            picked.append({"slug": target, "anchor": anchor_of(by[target]),
                           "why": why, "reason": reason, "cat": catof.get(target, "")})
            stats[why] += 1
            return True

        # 1. same-dish variants (always correct)
        if slug in keeper_of:
            add(keeper_of[slug], "keeper", "versi asas hidangan ini")
        for sib in members_of.get(slug, []):
            add(sib, "variant", "versi lain hidangan ini")

        # 2. same category — deterministic, staggered so coverage is even
        pool = by_cat[cat]
        if len(pool) > 1:
            off = int(rng(slug) * len(pool))
            for k in range(min(4, len(pool) - 1)):
                add(pool[(off + k) % len(pool)], "category", f"sama kategori {cat}")

        # 3. floor: walk the category until MIN_LINKS is met
        k = 1
        while len(picked) < MIN_LINKS and k <= len(pool):
            add(pool[(int(rng(slug) * len(pool)) + k) % len(pool)],
                "category", f"sama kategori {cat}")
            k += 1

        links[slug] = picked

    # ---- verification: no cross-category topical link may exist ----
    bad = []
    for s, ls in links.items():
        for l in ls:
            if l["why"] in ("category",) and catof.get(l["slug"]) != catof[s]:
                bad.append((s, l["slug"]))
            if l["why"] == "next" and catof.get(l["slug"]) != catof[s]:
                bad.append((s, l["slug"]))
    if bad:
        raise SystemExit(f"CROSS-CATEGORY LINKS FOUND: {bad[:5]}")

    json.dump(links, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"links for {len(links)} pages -> {OUT}")
    print(f"total links: {sum(len(v) for v in links.values())}")
    print(f"by type: {dict(stats)}")
    per = collections.Counter(len(v) for v in links.values())
    print(f"per page: {dict(sorted(per.items()))}")
    print(f"clusters: keepers={len(members_of)} variants={len(keeper_of)}")
    short = [s for s, v in links.items() if len(v) < MIN_LINKS]
    print(f"pages under floor: {len(short)}")
    print("cross-category topical links: 0")


if __name__ == "__main__":
    main()
