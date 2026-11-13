"""Re-key the slug-indexed generated artifacts after a slug migration.

parse.py rebuilds src/recipes_clean.json from the raw Blogger posts on every
build, so the recipe slugs come back with their year-month prefix. The LLM
artifacts (cats.json, rewrite.json, links.json) were generated once against the
CLEAN slugs and are committed, so they must be mapped back onto whatever slug
the current recipes_clean.json uses.

This script is direction-agnostic: it compares slugs by their date-stripped
form. If every key already matches, it is a no-op. Safe to run every build.

Reads/writes: src/cats.json, src/rewrite.json, src/links.json
"""
import json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")


def strip_date(s):
    return re.sub(r"^\d{4}-\d{2}-", "", s)


def load(name, default):
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        return default, p
    return json.load(open(p, encoding="utf-8")), p


def save(obj, p):
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)


recs, _ = load("recipes_clean.json", [])
if not recs:
    raise SystemExit("recipes_clean.json missing — run parse.py first")

current = [r["slug"] for r in recs]
cur_set = set(current)

# base form -> actual current slug (unique by construction after migrate_slugs)
cur_by_base = {strip_date(s): s for s in current}

total_remapped = 0
for fname in ("cats.json", "rewrite.json"):
    data, path = load(fname, {})
    if not data:
        continue
    out, hit, miss = {}, 0, 0
    for k, v in data.items():
        if k in cur_set:
            out[k] = v
            continue
        tgt = cur_by_base.get(strip_date(k))
        if tgt:
            out[tgt] = v
            hit += 1
        else:
            miss += 1
    if hit:
        save(out, path)
    total_remapped += hit
    print(f"{fname}: remapped {hit}, kept {len(out)-hit}, dropped {miss}")

# links.json is keyed by slug AND has slug values inside each entry
links, lpath = load("links.json", {})
if links:
    out, hit, dropped = {}, 0, 0
    for k, v in links.items():
        nk = k if k in cur_set else cur_by_base.get(strip_date(k))
        if not nk:
            dropped += 1
            continue
        if nk != k:
            hit += 1
        nv = []
        for e in v:
            t = e.get("slug")
            nt = t if t in cur_set else cur_by_base.get(strip_date(t or ""))
            if nt:
                e = dict(e)
                e["slug"] = nt
                nv.append(e)
        out[nk] = nv
    save(out, lpath)
    total_remapped += hit
    print(f"links.json: remapped {hit}, dropped {dropped}")

print(f"total remapped: {total_remapped} (0 = already in sync)")
