"""Build internal links between the 748 recipe pages.

Before this module every recipe page was an orphan: 748 pages, 0 internal
links. Google needs crawl paths and topical clustering, so each page gets
4-6 contextual links chosen by four independent signals:

  1. CLUSTER KEEPER  - for near-duplicate dishes, variants link UP to the
                       strongest page in the cluster. This consolidates
                       ranking signal instead of splitting it, which is the
                       whole anti-cannibalization strategy.
  2. CATEGORY SIBLINGS - 2 pages from the same primary category.
  3. SHARED INGREDIENTS - pages sharing distinctive ingredients (santan,
                       kukus, rempah) - real topical relevance, not random.
  4. NEXT RECIPE      - sequential flow so every page is reachable.

Anchor text is the target's dish name, never "click here". Links are
deterministic (seeded by slug) so rebuilds are byte-identical.

Usage:  python internal_links.py   ->  src/links.json  {slug: [{slug, anchor, why}]}
"""
import json, os, re, hashlib, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
OUT = os.path.join(ROOT, "src", "links.json")

# Distinctive ingredients that indicate real culinary kinship.
SIGNATURE = [
    "santan", "kukus", "goreng", "tumis", "rebus", "bakar", "rendang", "kari",
    "sambal", "belacan", "serai", "pandan", "gula melaka", "kelapa", "ubi",
    "tepung beras", "sagu", "agar-agar", "cendol", "durian", "nangka", "petai",
    "tempe", "tauhu", "kangkung", "petola", "labu", "keledek", "santan pekat",
]


def sigs(r):
    txt = " ".join(r["ingredients"]).lower()
    return {s for s in SIGNATURE if s in txt}


def rng(slug):
    """Deterministic pseudo-random 0..1 from slug, so rebuilds are stable."""
    return int(hashlib.md5(slug.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def title_anchor(r):
    """Use the dish name as anchor text - strip the marketing tail."""
    t = r["title"]
    t = re.sub(r"\s*[-–—]\s*Resepi Mudah.*$", "", t, flags=re.I)
    t = t.split(":")[0].strip()
    return t[:70]


def core_dish(title):
    t = re.sub(r"^resepi\s+|^resipi\s+", "", title.lower())
    t = t.split(":")[0].split(" - ")[0]
    t = re.sub(r"\b(original|ala|paling|mudah|sedap|simple|gerenti|confirm|style|"
               r"versi|resepi|resipi|dari|yang|best|senang|mewah|premium|kedai|"
               r"restoran|hotel)\b", "", t)
    return re.sub(r"[^a-z ]", " ", t).split()


def main():
    recs = json.load(open(SRC, encoding="utf-8"))
    by_slug = {r["slug"]: r for r in recs}

    # ---- 1. cluster detection (near-duplicate dishes) ----
    clusters = collections.defaultdict(list)
    for r in recs:
        w = core_dish(r["title"])
        if len(w) >= 2:
            clusters[" ".join(w[:3])].append(r["slug"])

    keeper_of = {}
    cluster_members = {}
    for key, members in clusters.items():
        if len(members) < 2:
            continue
        # keeper = most complete recipe (ingredients + steps), tie-break oldest published
        best = max(members, key=lambda s: (by_slug[s]["n_ing"] + by_slug[s]["n_steps"],
                                           -len(by_slug[s]["title"])))
        cluster_members[best] = [m for m in members if m != best]
        for m in members:
            if m != best:
                keeper_of[m] = best

    # ---- 2. signature ingredients ----
    sig_index = collections.defaultdict(list)
    for r in recs:
        for s in sigs(r):
            sig_index[s].append(r["slug"])

    by_cat = collections.defaultdict(list)
    for r in recs:
        by_cat[r["cats"][0] if r["cats"] else "Sayur"].append(r["slug"])

    links = {}
    for i, r in enumerate(recs):
        slug = r["slug"]
        picked = []
        seen = {slug}

        def add(target, why):
            if target in seen or len(picked) >= 6:
                return
            seen.add(target)
            picked.append({"slug": target, "anchor": title_anchor(by_slug[target]), "why": why})

        # 1. cluster keeper / siblings (strongest anti-cannibalization signal)
        if slug in keeper_of:
            add(keeper_of[slug], "keeper")
        for sib in cluster_members.get(slug, []):
            add(sib, "variant")

        # 2. category siblings, rotated deterministically
        cat = r["cats"][0] if r["cats"] else "Sayur"
        pool = [s for s in by_cat[cat] if s != slug]
        if pool:
            off = int(rng(slug) * len(pool))
            for k in range(min(2, len(pool))):
                add(pool[(off + k) % len(pool)], "category")

        # 3. shared signature ingredients (real topical relevance)
        mine = sigs(r)
        if mine:
            scored = collections.Counter()
            for s in mine:
                for cand in sig_index[s]:
                    if cand != slug:
                        scored[cand] += 1
            for cand, n in scored.most_common(6):
                if n >= 2:
                    add(cand, "ingredient")

        # 4. sequential next so no page is a dead end
        add(recs[(i + 1) % len(recs)]["slug"], "next")

        # 5. hard floor: every page must carry >=3 internal links. Walks forward
        # through the catalogue until the minimum is met, so thin categories
        # (Minuman, Kek) never leave a page with 2 links and no crawl path.
        k = 2
        while len(picked) < 3 and k < len(recs):
            add(recs[(i + k) % len(recs)]["slug"], "fallback")
            k += 1

        links[slug] = picked

    json.dump(links, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    counts = collections.Counter(len(v) for v in links.values())
    whys = collections.Counter(w["why"] for v in links.values() for w in v)
    print(f"links built for {len(links)} pages -> {OUT}")
    print(f"links per page: {dict(sorted(counts.items()))}")
    print(f"link types: {dict(whys)}")
    print(f"cluster keepers: {len(cluster_members)}  variants linked up: {len(keeper_of)}")
    total = sum(len(v) for v in links.values())
    print(f"total internal links: {total}")
    assert all(len(v) >= 3 for v in links.values()), "some page has <3 links"


if __name__ == "__main__":
    main()
