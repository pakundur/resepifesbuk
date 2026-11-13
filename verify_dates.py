#!/usr/bin/env python3
"""EEAT gates 47-49: modification dates must be truthful.

The site's recipe text was rewritten corpus-wide on 2026-11-13 (Indonesian->BM
localisation, produce terms, punctuation repair, step fixes). Blogger's own
`updated` field reflects the ORIGINAL blog edit, so emitting it would show
"last updated May 2026" on pages edited yesterday.

The corresponding failure mode is the opposite: bumping every page to "now" on
each build, or collapsing datePublished into dateModified. Both are the
signature of date manipulation and both are gated here.

Gate 47: schema dateModified == CONTENT_REVISED on every recipe, and it is
         never in the future, never older than datePublished.
Gate 48: visible "Dikemas kini" <time> matches schema exactly (a mismatch means
         users and crawlers see different dates).
Gate 49: datePublished stays genuinely varied and is NOT rewritten to the
         content-revision date (96 distinct values from the Blogger export).
"""
import glob
import json
import os
import re
import sys
from collections import Counter

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
CONTENT_REVISED = "2026-11-13"
fails = []


def ld_blocks(html):
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            yield json.loads(m.group(1))
        except Exception:
            continue


def find_recipe_ld(html):
    for d in ld_blocks(html):
        if isinstance(d, dict) and d.get("@type") == "Recipe":
            return d
    return None


def main():
    files = sorted(glob.glob(os.path.join(DIST, "resepi", "*", "index.html")))
    if len(files) < 700:
        fails.append(f"47 only {len(files)} recipe pages found (expected ~748)")
        files = files  # keep going for a useful report

    g47 = g48 = g49 = 0
    published = Counter()
    n_recipe = 0

    for f in files:
        slug = os.path.basename(os.path.dirname(f))
        html = open(f, encoding="utf-8").read()
        ld = find_recipe_ld(html)
        if not ld:
            fails.append(f"47 {slug}: no Recipe JSON-LD")
            continue
        n_recipe += 1

        dm = ld.get("dateModified")
        dp = ld.get("datePublished")
        if dp:
            published[dp] += 1

        # --- gate 47 ---
        if dm != CONTENT_REVISED:
            fails.append(f"47 {slug}: dateModified={dm!r}, expected {CONTENT_REVISED}")
            g47 += 1
        elif dm > "2026-11-30":
            fails.append(f"47 {slug}: dateModified {dm} is implausibly recent (bumped?)")
            g47 += 1
        elif dp and dm < dp:
            fails.append(f"47 {slug}: dateModified {dm} is before datePublished {dp}")
            g47 += 1

        # --- gate 48: visible date must equal schema date ---
        vis = re.search(r'<time datetime="([^"]+)">[^<]*</time>', html)
        if not vis:
            fails.append(f"48 {slug}: no visible <time> element")
            g48 += 1
        elif vis.group(1) != dm:
            fails.append(f"48 {slug}: visible {vis.group(1)} != schema {dm}")
            g48 += 1

    # --- gate 49: datePublished must stay varied, not collapse to the revision date ---
    if len(published) < 20:
        fails.append(f"49 datePublished has only {len(published)} distinct values "
                     f"(expected many, from Blogger export) — dates may have been rewritten")
        g49 += 1
    if published.get(CONTENT_REVISED, 0) > 5:
        fails.append(f"49 {published[CONTENT_REVISED]} recipes share datePublished="
                     f"{CONTENT_REVISED} — published/modified appear collapsed")
        g49 += 1

    print("=" * 68)
    print("EEAT GATES 47-49 (truthful modification dates)")
    print("=" * 68)
    print(f"  #47 [{'PASS' if not g47 else 'FAIL'}] dateModified == {CONTENT_REVISED} "
          f"on all recipes, never future, never before datePublished")
    print(f"  #48 [{'PASS' if not g48 else 'FAIL'}] visible 'Dikemas kini' date matches schema date")
    print(f"  #49 [{'PASS' if not g49 else 'FAIL'}] datePublished stays varied "
          f"({len(published)} distinct) and is not collapsed into dateModified")
    print("-" * 68)
    for m in fails[:25]:
        print("   ", m)
    if len(fails) > 25:
        print(f"    ... and {len(fails)-25} more")
    print(f"   {3 if not fails else 3} gates checked against {n_recipe} recipe pages")
    if fails:
        print(f"   {len(fails)} failure(s)")
        sys.exit(1)
    print("   3/3 date gates pass")
    sys.exit(0)


if __name__ == "__main__":
    main()
