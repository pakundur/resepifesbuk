#!/usr/bin/env python3
"""
FAB QA gates 32-36: floating share fan + back-to-top on the built output.

Checks the SHIPPED dist/ HTML, not the generator, so a template change that
renders nothing still fails here.

Run standalone: python3 verify_fab.py
Exits 1 on any failure.
"""
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIST = BASE / "dist"

results = []


def gate(num, name, ok, detail=""):
    results.append((num, name, ok, detail))


# Sample pages across every template that should carry the FAB.
SAMPLES = [
    "index.html",
    "resepi/index.html",
    "kategori/index.html",
    "tentang/index.html",
    "pendedahan-affiliate/index.html",
]

recipe_pages = sorted((DIST / "resepi").glob("*/index.html"))
cat_pages = sorted((DIST / "kategori").glob("*/index.html"))
all_pages = ([DIST / p for p in SAMPLES if (DIST / p).exists()]
             + recipe_pages + cat_pages)

missing_file = [str(p.relative_to(DIST)) for p in all_pages if not p.exists()]

# ---------------------------------------------------------------- gate 32
# Every page carries exactly one FAB root, one share trigger, one top button.
# Scans ALL built HTML (not a sample) so a template that skips the footer
# cannot silently ship without the stack.
no_fab, multi_fab, no_share, no_top = [], [], [], []
all_html = sorted(DIST.rglob("*.html"))
checked = 0
for p in all_html:
    checked += 1
    h = p.read_text(encoding="utf-8", errors="ignore")
    rel = str(p.relative_to(DIST))
    n_root = len(re.findall(r'<div class="fab" id="fab"', h))
    if n_root == 0:
        no_fab.append(rel)
    elif n_root > 1:
        multi_fab.append(rel)
    if 'id="fab-share"' not in h:
        no_share.append(rel)
    if 'id="fab-top"' not in h:
        no_top.append(rel)

gate(32, "FAB root + share trigger + top button on every built page",
     not (no_fab or multi_fab or no_share or no_top) and checked >= 800,
     f"checked={checked} missing={len(no_fab)} {no_fab[:3]} "
     f"dup={len(multi_fab)} noshare={len(no_share)} notop={len(no_top)}")

# ---------------------------------------------------------------- gate 33
# Fan is collapsed by default: aria-expanded=false, fan aria-hidden=true,
# and all fan items are removed from the tab order.
bad_collapse = []
for p in all_pages:
    if not p.exists():
        continue
    h = p.read_text(encoding="utf-8", errors="ignore")
    rel = str(p.relative_to(DIST))
    if 'aria-expanded="false"' not in h:
        bad_collapse.append(f"{rel}: aria-expanded not false")
    if 'id="fab-fan" aria-hidden="true"' not in h:
        bad_collapse.append(f"{rel}: fan not aria-hidden")
    # every fan item must carry tabindex="-1" until JS opens the fan
    fan = re.search(r'<div class="fab__fan".*?</div>\s*<button class="fab__btn fab__btn--share"',
                    h, re.S)
    if not fan:
        bad_collapse.append(f"{rel}: fan block not parsable")
        continue
    n_items = len(re.findall(r'class="fab__item', fan.group(0)))
    n_ti = len(re.findall(r'tabindex="-1"', fan.group(0)))
    if n_items != n_ti:
        bad_collapse.append(f"{rel}: {n_items} items but {n_ti} tabindex=-1")

gate(33, "Share fan collapsed by default (aria + tab order)",
     not bad_collapse, "; ".join(bad_collapse[:4]))

# ---------------------------------------------------------------- gate 34
# All 8 destinations present, each with a real share endpoint and the
# sponsored/nofollow hardening on outbound links.
EXPECT = ["whatsapp", "telegram", "facebook", "x", "pinterest",
          "threads", "email", "copy"]
bad_fan = []
for p in all_pages:
    if not p.exists():
        continue
    h = p.read_text(encoding="utf-8", errors="ignore")
    rel = str(p.relative_to(DIST))
    for key in EXPECT:
        if f"fab__item--{key}" not in h:
            bad_fan.append(f"{rel}: missing {key}")
    # outbound anchors must be sponsored
    anchors = re.findall(r'<a class="fab__item[^>]*>', h)
    for a in anchors:
        if 'rel="noopener nofollow"' not in a:
            bad_fan.append(f"{rel}: fan anchor without noopener nofollow")
            break
    if re.search(r'href=""|href="#"', " ".join(anchors)):
        bad_fan.append(f"{rel}: placeholder href in fan")

gate(34, "All 8 share destinations present + hardened links",
     not bad_fan, "; ".join(bad_fan[:5]))

# ---------------------------------------------------------------- gate 35
# Back-to-top resolves to a real anchor target: body#top must exist,
# otherwise the no-JS fallback is a dead link.
bad_top = []
for p in all_pages:
    if not p.exists():
        continue
    h = p.read_text(encoding="utf-8", errors="ignore")
    rel = str(p.relative_to(DIST))
    if '<body id="top">' not in h:
        bad_top.append(f"{rel}: no <body id='top'>")
    if 'href="#top"' not in h:
        bad_top.append(f"{rel}: no #top href")

gate(35, "Back-to-top anchor target exists on every page",
     not bad_top, "; ".join(bad_top[:4]))

# ---------------------------------------------------------------- gate 36
# "Salin pautan" must be icon-only in the in-flow share bar (user request:
# remove the text, keep the icon). The accessible name must survive.
bad_copy = []
for p in all_pages:
    if not p.exists():
        continue
    h = p.read_text(encoding="utf-8", errors="ignore")
    rel = str(p.relative_to(DIST))
    if "<span>Salin pautan</span>" in h:
        bad_copy.append(f"{rel}: text label still rendered")
    bar = re.search(r'<div class="share-bar[^"]*".*?</div>', h, re.S)
    if bar and 'class="share-btn share-copy"' in bar.group(0):
        btn = re.search(r'<button class="share-btn share-copy".*?</button>',
                        bar.group(0), re.S)
        if btn:
            b = btn.group(0)
            if 'aria-label="Salin pautan"' not in b:
                bad_copy.append(f"{rel}: copy button lost accessible name")
            if "sc-done" not in b:
                bad_copy.append(f"{rel}: copy button missing success icon")

gate(36, 'Copy link is icon-only with accessible name intact',
     not bad_copy, "; ".join(bad_copy[:4]))

# ---------------------------------------------------------------- gate 37
# CSS for the FAB actually shipped in the hashed stylesheet, and the
# referenced hash matches the written file.
css = (DIST / "style.css").read_text(encoding="utf-8", errors="ignore")
# .fab__btn--top intentionally has no rule of its own: it inherits the shared
# .fab__btn circle. Assert the shared rule exists plus the FAB-specific ones.
need = [".fab {", ".fab__fan", ".fab.is-open .fab__item", ".fab__tip",
        ".fab__btn {", ".share-copy .sc-done"]
absent = [n for n in need if n not in css]

import hashlib
ref = None
home = (DIST / "index.html").read_text(encoding="utf-8", errors="ignore")
m = re.search(r"style\.css\?v=([a-f0-9]+)", home)
actual = hashlib.sha256(css.encode()).hexdigest()[:10]
hash_ok = bool(m) and m.group(1) == actual
gate(37, "FAB CSS shipped and stylesheet hash matches",
     not absent and hash_ok,
     f"missing={absent} ref={m.group(1) if m else None} actual={actual}")

# ---------------------------------------------------------------- gate 38
# The FAB must not leak into machine-readable semantics: no share URL may
# appear inside JSON-LD, and the fan is not part of the recipe graph.
bad_schema = []
for p in recipe_pages[:80]:
    h = p.read_text(encoding="utf-8", errors="ignore")
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                            h, re.S):
        if "wa.me" in block or "sharer.php" in block or "t.me/" in block:
            bad_schema.append(str(p.relative_to(DIST)))
            break
gate(38, "No share URLs inside JSON-LD", not bad_schema,
     "; ".join(bad_schema[:3]))

# ---------------------------------------------------------------- report
if __name__ == "__main__":
    print("=" * 68)
    print("FAB GATES 32-38")
    print("=" * 68)
    fails = 0
    for num, name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        print(f"  #{num} [{mark}] {name}")
        if not ok:
            fails += 1
            print(f"        {detail}")
    print("-" * 68)
    print(f"  {len(results)-fails}/{len(results)} fab gates pass")
    sys.exit(1 if fails else 0)
