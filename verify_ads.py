#!/usr/bin/env python3
"""
Ad-system QA gates 23-31 for the per-link copy system.

Run standalone: python3 verify_ads.py
Exits 1 on any failure. Designed to be called from verify_all.py / build.sh.
"""
import json, re, sys, html, collections
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

import ad_copy_per_link as CB
import ads_wired2 as AW
import ad_render2 as AR

REC = json.load(open(BASE / "src/content_fix.json"))
LINKS = json.loads((BASE / "affiliate_links.json").read_text())["products"]

SLOTS = {"R1": "three", "R2": "compact", "R3": "bar"}

results = []


def gate(num, name, ok, detail=""):
    results.append((num, name, ok, detail))


# ---------------------------------------------------------------- gate 23
# Every one of the 48 link-copy blocks is complete.
g23 = []
for key, prod in CB.COPY.items():
    for i, s in enumerate(prod["slots"]):
        for f in ("hook", "promise", "btn", "src"):
            if not str(s.get(f, "")).strip():
                g23.append(f"{key}[aff{i+1}] empty {f}")
gate(23, "48/48 link copies complete (hook+promise+btn+src)", not g23,
     "; ".join(g23[:4]))

# ---------------------------------------------------------------- gate 24
# No two links of the same product share a hook.
g24 = []
for key, prod in CB.COPY.items():
    hooks = [s["hook"].lower().strip() for s in prod["slots"]]
    if len(set(hooks)) != 3:
        g24.append(f"{key}: duplicate hook")
allhooks = [s["hook"].lower().strip() for p in CB.COPY.values() for s in p["slots"]]
dupes = [h for h, n in collections.Counter(allhooks).items() if n > 1]
gate(24, "No duplicate hooks (within or across products)", not g24 and not dupes,
     "; ".join(g24 + dupes[:3]))

# ---------------------------------------------------------------- gate 25
# Zero exclamation marks anywhere in copy.
g25 = []
for key, prod in CB.COPY.items():
    for i, s in enumerate(prod["slots"]):
        for f in ("hook", "promise", "btn", "note"):
            if "!" in str(s.get(f, "")):
                g25.append(f"{key}[{i}].{f}")
gate(25, "Zero exclamation marks in any copy field", not g25, "; ".join(g25[:4]))

# ---------------------------------------------------------------- gate 26
# Zero banned hard-sell terms.
g26 = []
for key, prod in CB.COPY.items():
    for i, s in enumerate(prod["slots"]):
        blob = " ".join(str(s.get(f, "")) for f in ("hook", "promise", "btn", "note")).lower()
        for b in CB.BANNED:
            if b in blob:
                g26.append(f"{key}[{i}] '{b}'")
gate(26, "Zero banned hard-sell terms", not g26, "; ".join(g26[:4]))

# ---------------------------------------------------------------- gate 27
# Every hook carries corpus evidence, or is explicitly flagged BENEFIT.
g27 = []
for key, prod in CB.COPY.items():
    for i, s in enumerate(prod["slots"]):
        src = s.get("src", "")
        if not src:
            g27.append(f"{key}[{i}] no src")
        elif src.startswith("BENEFIT"):
            if key not in CB.BENEFIT_ONLY:
                g27.append(f"{key}[{i}] claims BENEFIT but product has pain data")
gate(27, "Every hook sourced to corpus evidence or flagged BENEFIT", not g27,
     "; ".join(g27[:4]))

# ---------------------------------------------------------------- gate 28
# Every rendered card carries exactly 3 distinct real links, all rel=sponsored.
g28 = []
checked = 0
for key in AW.ORDER:
    slug = next((s for s, r in REC.items() if key in AW.candidates(r)), None)
    if not slug:
        continue
    c = AW.build_creative(key, slug, "R1")
    for v in ("three", "compact", "bar"):
        h = AR.render(c, v)
        hrefs = re.findall(r'https://s\.shopee\.com\.my/[A-Za-z0-9]+', h)
        rel = h.count('rel="sponsored nofollow noopener"')
        checked += 1
        if len(hrefs) != 3 or len(set(hrefs)) != 3:
            g28.append(f"{key}/{v}: {len(hrefs)} links ({len(set(hrefs))} distinct)")
        if rel != 3:
            g28.append(f"{key}/{v}: {rel} rel=sponsored (need 3)")
gate(28, f"All 3 links present+distinct+sponsored per card ({checked} combos)",
     not g28, "; ".join(g28[:4]))

# ---------------------------------------------------------------- gate 29
# No page renders the same product twice.
g29 = []
dup_pages = 0
for slug, rec in REC.items():
    ads = AW.page_ads(rec, slug, SLOTS)
    keys = [c["key"] for _, c in ads]
    if len(keys) != len(set(keys)):
        dup_pages += 1
        if len(g29) < 3:
            g29.append(slug)
gate(29, "No page shows two ads for the same product", dup_pages == 0,
     f"{dup_pages} pages; e.g. {', '.join(g29)}")

# ---------------------------------------------------------------- gate 30
# All 48 supplied links are used, and every rendered href is one of them.
supplied = {u for p in LINKS.values() for u in p["links"]}
rendered = set()
for slug, rec in REC.items():
    for slot, c in AW.page_ads(rec, slug, SLOTS):
        rendered.update(c["hrefs"])
orphan = rendered - supplied
unused = supplied - rendered
gate(30, "Every rendered link is a supplied link; all 48 used",
     not orphan and not unused,
     f"orphan={len(orphan)} unused={sorted(unused)[:3]}")

# ---------------------------------------------------------------- gate 31
# IKLAN disclosure present on every rendered card. (Renamed from DITAJA —
# see the CPETTR commercial-intent disclosure requirement.)
g31 = []
cards = 0
for slug, rec in REC.items():
    for slot, h in AR.render_page(rec, slug, SLOTS):
        cards += 1
        if ">Iklan<" not in h:
            g31.append(f"{slug}/{slot}")
        if "Pautan rakan kongsi" not in h:
            g31.append(f"{slug}/{slot} missing disclosure note")
gate(31, f"IKLAN chip + disclosure note on every card ({cards} cards)",
     not g31, "; ".join(g31[:4]))

# ---------------------------------------------------------------- report
if __name__ == "__main__":
    print("=" * 68)
    print("AD SYSTEM GATES 23-31")
    print("=" * 68)
    fails = 0
    for num, name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        print(f"  #{num} [{mark}] {name}")
        if not ok:
            fails += 1
            print(f"        {detail}")
    print("-" * 68)
    print(f"  {len(results)-fails}/{len(results)} ad gates pass")
    sys.exit(1 if fails else 0)
