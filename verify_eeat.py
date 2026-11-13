#!/usr/bin/env python3
"""
EEAT gates 39-45 against the BUILT output.

These enforce the trust signals that were missing before:
  - every recipe names a real Person author (not a bare Organization)
  - that author resolves to a page that exists
  - every page offers a contact route and a link to the author/disclosure pages
  - author pages state the pen-name disclosure (honesty requirement)
  - no author bio claims credentials the site cannot back

Run standalone: python3 verify_eeat.py
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DIST = BASE / "dist"
sys.path.insert(0, str(BASE))

import authors as AUTH

results = []


def gate(num, name, ok, detail=""):
    results.append((num, name, ok, detail))


def rd(p):
    return p.read_text(encoding="utf-8", errors="ignore")


recipe_pages = sorted((DIST / "resepi").glob("*/index.html"))
all_html = sorted(DIST.rglob("*.html"))

# ---------------------------------------------------------------- gate 39
# Every recipe's schema author is a Person with a resolvable @id/url, and the
# name matches one of the declared personas. Organization-only author is the
# exact weakness this work exists to fix.
bad39 = []
for p in recipe_pages:
    h = rd(p)
    rel = str(p.relative_to(DIST))
    found = False
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            d = json.loads(block)
        except Exception:
            continue
        if d.get("@type") != "Recipe":
            continue
        a = d.get("author") or {}
        if isinstance(a, list):
            a = a[0] if a else {}
        if a.get("@type") != "Person":
            bad39.append(f"{rel}: author type={a.get('@type')}")
            break
        if a.get("name") not in {v["name"] for v in AUTH.PERSONAS.values()}:
            bad39.append(f"{rel}: unknown author {a.get('name')!r}")
            break
        if "/penulis/" not in (a.get("url") or ""):
            bad39.append(f"{rel}: author url missing")
            break
        found = True
        break
    if not found and not any(rel in x for x in bad39):
        bad39.append(f"{rel}: no Recipe schema")

gate(39, "Every recipe names a Person author (no Organization-only)",
     not bad39 and len(recipe_pages) > 700,
     f"{len(recipe_pages)} recipes, {len(bad39)} bad: {bad39[:3]}")

# ---------------------------------------------------------------- gate 40
# The author named in schema must own the recipe's category, and that author
# page must exist in the build.
bad40 = []
for p in recipe_pages:
    h = rd(p)
    rel = str(p.relative_to(DIST))
    m = re.search(r'<a href="(/penulis/([a-z-]+)/)">([^<]+)</a>', h)
    if not m:
        bad40.append(f"{rel}: no byline link")
        continue
    url, key, name = m.group(1), m.group(2), m.group(3)
    if key not in AUTH.PERSONAS:
        bad40.append(f"{rel}: unknown persona {key}")
        continue
    if AUTH.PERSONAS[key]["name"] != name:
        bad40.append(f"{rel}: name/key mismatch {name}!={key}")
    if not (DIST / "penulis" / key / "index.html").exists():
        bad40.append(f"{rel}: author page missing for {key}")

gate(40, "Byline links to an existing author page with matching name",
     not bad40, f"{len(bad40)} bad: {bad40[:3]}")

# ---------------------------------------------------------------- gate 41
# Contact route reachable from every page: a link to /hubungi/ (or a mailto).
# AND every page links to the author hub or disclosure page.
bad41 = []
for p in all_html:
    h = rd(p)
    rel = str(p.relative_to(DIST))
    if "/hubungi/" not in h and "mailto:hello@resepifesbuk.com" not in h:
        bad41.append(f"{rel}: no contact route")
    if "/penulis/" not in h and "/pendedahan-affiliate/" not in h:
        bad41.append(f"{rel}: no author/disclosure link")
    if "/polisi-privasi/" not in h:
        bad41.append(f"{rel}: no privacy policy link")

gate(41, "Contact route + trust links on every page",
     not bad41, f"{len(bad41)} issues: {bad41[:3]}")

# ---------------------------------------------------------------- gate 42
# The autor hub must carry the pen-name disclosure. This is the honesty
# requirement: these are pen names and the site says so.
hub = DIST / "penulis" / "index.html"
hub_txt = rd(hub) if hub.exists() else ""
gate(42, "Author hub discloses that these are pen names",
     hub.exists() and "nama pena" in hub_txt.lower(),
     "hub missing or no 'nama pena' disclosure")

# ---------------------------------------------------------------- gate 43
# No fabricated credentials anywhere in the author pages. The bios are built
# from demonstrable facts only, so these claim-words must not appear.
BANNED = ["ijazah", "sarjana muda", "diploma", "sijil", "certified",
          "certification", "chef", "cikgu masakan", "20 tahun", "10 tahun",
          "anugerah", "award", "universiti", "college", "sekolah masakan"]
bad43 = []
for p in sorted((DIST / "penulis").rglob("index.html")):
    low = rd(p).lower()
    for w in BANNED:
        if w in low:
            bad43.append(f"{p.parent.name}: claims {w!r}")

gate(43, "Author bios contain no fabricated credentials",
     not bad43, "; ".join(bad43[:4]))

# ---------------------------------------------------------------- gate 44
# The byline (author) must be visible in the HTML body, not only in schema.
# The modification date is deliberately NOT shown to readers (owner decision
# 2026-11-14): dates live in schema, sitemap and feed only. Gate 47 covers
# the machine-readable side, so this gate must NOT require a visible <time>.
bad44 = []
for p in recipe_pages:
    h = rd(p)
    rel = str(p.relative_to(DIST))
    if 'class="byline"' not in h:
        bad44.append(f"{rel}: no visible byline")
    elif "Oleh" not in h:
        bad44.append(f"{rel}: byline has no author name")
    elif "Dikemas kini" in h:
        bad44.append(f"{rel}: hidden modification date is still rendered")

gate(44, "Visible author byline; 'Dikemas kini' date suppressed from page",
     not bad44, f"{len(bad44)} bad: {bad44[:3]}")

# ---------------------------------------------------------------- gate 45
# Author pages are in the sitemap and carry Person schema.
sm = rd(DIST / "sitemap.xml") if (DIST / "sitemap.xml").exists() else ""
bad45 = []
for key in AUTH.PERSONAS:
    if f"/penulis/{key}/" not in sm:
        bad45.append(f"{key} not in sitemap")
    fp = DIST / "penulis" / key / "index.html"
    if not fp.exists():
        bad45.append(f"{key} page missing")
        continue
    h = rd(fp)
    if '"@type": "Person"' not in h:
        bad45.append(f"{key} no Person schema")
if "/penulis/" not in sm:
    bad45.append("hub not in sitemap")

gate(45, "Author pages in sitemap with Person schema",
     not bad45, "; ".join(bad45[:4]))

# ---------------------------------------------------------------- gate 46
# Avatar assets must actually exist in the build. A 404 avatar is the exact
# bug this gate exists for: the files were copied to dist/img/penulis/, which
# the Pages Function proxies to R2, so every byline image 404'd in production
# while the build reported success.
bad46 = []
for key, p in AUTH.PERSONAS.items():
    ap = p["avatar"].lstrip("/")
    fp = DIST / ap
    if not fp.exists():
        bad46.append(f"{key}: {p['avatar']} missing from dist")
    elif fp.stat().st_size < 200:
        bad46.append(f"{key}: {p['avatar']} suspiciously small")
# and the path must NOT sit under /img/, which is R2-proxied
for key, p in AUTH.PERSONAS.items():
    if p["avatar"].startswith("/img/"):
        bad46.append(f"{key}: avatar under /img/ is R2-proxied")

gate(46, "Author avatar assets exist and are not R2-proxied",
     not bad46, "; ".join(bad46[:4]))

# ---------------------------------------------------------------- report
if __name__ == "__main__":
    print("=" * 68)
    print("EEAT GATES 39-45")
    print("=" * 68)
    fails = 0
    for num, name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        print(f"  #{num} [{mark}] {name}")
        if not ok:
            fails += 1
            print(f"        {detail}")
    print("-" * 68)
    print(f"  {len(results)-fails}/{len(results)} eeat gates pass")
    sys.exit(1 if fails else 0)
