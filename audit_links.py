"""Audit the internal link graph for false positives.

Independent of how links were built: re-derives compatibility from the data
and flags any pairing a reader would consider wrong.

Rules for a link to be CORRECT:
  R1 same category                          -> always ok
  R2 same meal family (lauk/karbo/manisan)  -> ok
  R3 same core dish name (variant/keeper)   -> always ok
  R4 'next' navigation link                 -> exempt (not a recommendation)

Anything else is a false positive.
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
LINKS = os.path.join(ROOT, "src", "links.json")

FAMILY = {
    "lauk": {"Ayam", "Daging", "Ikan", "Udang", "Sotong", "Ketam", "Perut",
             "Belangkas", "Kerang / Kupang / Lala / Siput", "Sayur", "Sambal", "Sup"},
    "karbo": {"Nasi", "MiNoodles", "Roti", "Bubur"},
    "manisan": {"Kuih", "Kek", "Biskut", "Puding"},
    "minuman": {"Minuman"},
}
CAT2FAM = {c: f for f, cs in FAMILY.items() for c in cs}


def core(title):
    t = re.sub(r"^resepi\s+|^resipi\s+", "", title.lower())
    t = t.split(":")[0].split(" - ")[0]
    t = re.sub(r"\b(original|ala|paling|mudah|sedap|simple|gerenti|confirm|style|"
               r"versi|resepi|resipi|dari|yang|best|senang|mewah|premium|kedai|"
               r"restoran|hotel|viral|lazat)\b", "", t)
    return " ".join(re.sub(r"[^a-z ]", " ", t).split()[:3])


def main():
    recs = {r["slug"]: r for r in json.load(open(SRC, encoding="utf-8"))}
    links = json.load(open(LINKS, encoding="utf-8"))

    cat = {s: (r["cats"][0] if r["cats"] else "?") for s, r in recs.items()}
    fam = {s: CAT2FAM.get(c) for s, c in cat.items()}
    dish = {s: core(r["title"]) for s, r in recs.items()}

    fps, reason = [], collections.Counter()
    checked = 0
    for src, items in links.items():
        for it in items:
            tgt = it["slug"]
            if tgt not in recs:
                fps.append((src, tgt, "dangling"))
                reason["dangling"] += 1
                continue
            if it["why"] == "next":
                continue
            checked += 1
            if cat[src] == cat[tgt]:
                reason["same-category"] += 1
                continue
            if fam[src] and fam[src] == fam[tgt]:
                reason["same-family"] += 1
                continue
            if dish[src] and dish[src] == dish[tgt]:
                reason["same-dish"] += 1
                continue
            fps.append((src, tgt, it["why"]))
            reason["FALSE-POSITIVE"] += 1

    print(f"links checked (excluding 'next'): {checked}")
    print(f"  same category : {reason['same-category']}")
    print(f"  same family   : {reason['same-family']}")
    print(f"  same dish     : {reason['same-dish']}")
    print(f"  FALSE POSITIVE: {reason['FALSE-POSITIVE']}")

    if fps:
        print(f"\n{len(fps)} false positives:")
        for s, t, w in fps[:30]:
            print(f"  [{cat[s]}] {recs[s]['title'][:45]}")
            print(f"     -> [{cat[t]}] {recs[t]['title'][:50]}   ({w})")
        sys.exit(1)

    # per-page minimum
    thin = [(s, len(v)) for s, v in links.items() if len(v) < 3]
    if thin:
        print(f"\n{len(thin)} pages with <3 links: {thin[:10]}")
        sys.exit(1)

    print("\nNO FALSE POSITIVES. Every cross-category link is same-family or same-dish.")


if __name__ == "__main__":
    main()
