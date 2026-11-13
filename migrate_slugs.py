"""Migrate recipe slugs to clean SEO URLs: strip the Blogger year-month prefix.

  OLD  2020-04-resepi-nasi-goreng-bombay-telur-mata
  NEW  resepi-nasi-goreng-bombay-telur-mata

Date prefixes are Blogger artefacts with zero SEO value and they make URLs
look stale. Collisions happen when the same dish was posted twice in different
months; the richer version (more steps, then more ingredients) keeps the clean
slug, the thinner one gets a variant suffix so NOTHING is deleted or merged.

Outputs:
  src/recipes_clean.json  slug fields rewritten in place (backup .pre_slug.json)
  src/slug_map.json       {old_slug: new_slug}  -> used for 301 redirects
"""
import json, os, re, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
MAP = os.path.join(ROOT, "src", "slug_map.json")
BAK = os.path.join(ROOT, "src", "recipes_clean.pre_slug.json")

recs = json.load(open(SRC, encoding="utf-8"))
if not os.path.exists(BAK):
    json.dump(recs, open(BAK, "w", encoding="utf-8"), ensure_ascii=False)


def strip_date(s):
    return re.sub(r"^\d{4}-\d{2}-", "", s)


def trim(s, n=60):
    """Keep slugs <=60 chars, cutting on a word boundary."""
    if len(s) <= n:
        return s
    cut = s[:n]
    if "-" in cut:
        cut = cut[:cut.rfind("-")]
    return cut.strip("-")


# score = richer page wins the clean slug
def score(r):
    return (len(r.get("steps") or []), len(r.get("ingredients") or []))


groups = collections.defaultdict(list)
for r in recs:
    groups[trim(strip_date(r["slug"]))].append(r)

slug_map, used = {}, set()
for base, members in groups.items():
    members.sort(key=score, reverse=True)
    for i, r in enumerate(members):
        new = base if i == 0 else f"{base}-versi-{i+1}"
        while new in used:
            new += "-alt"
        used.add(new)
        slug_map[r["slug"]] = new
        r["slug"] = new

for r in recs:
    if len(r["slug"]) > 60:
        raise SystemExit(f"slug too long: {r['slug']}")

json.dump(recs, open(SRC, "w", encoding="utf-8"), ensure_ascii=False)
json.dump(slug_map, open(MAP, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

changed = sum(1 for o, n in slug_map.items() if o != n)
print(f"recipes {len(recs)} | slugs rewritten {changed} | unique {len(used)}")
longest = max(recs, key=lambda r: len(r["slug"]))
print(f"longest slug {len(longest['slug'])}: {longest['slug']}")
for base, m in groups.items():
    if len(m) > 1:
        print(f"  collision resolved: {base} -> {[r['slug'] for r in m]}")
