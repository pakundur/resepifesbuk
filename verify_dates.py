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
Gate 48: the date is NOT shown to readers ("Dikemas kini" suppressed), and the
         sitemap carries it in a valid W3C-datetime form that agrees with
         schema. Sitemap lastmod must include a time component.
Gate 49: datePublished stays genuinely varied and is NOT rewritten to the
         content-revision date (96 distinct values from the Blogger export).
Gate 50: feed.xml <pubDate>/<lastBuildDate> are RFC-822 (RSS 2.0 requires it;
         ISO-8601 is invalid there and readers drop it).
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
    g48b = g50 = 0
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

        # --- gate 48a: the date must NOT be rendered to readers ---
        if "Dikemas kini" in html:
            fails.append(f"48 {slug}: 'Dikemas kini' still visible on the page")
            g48 += 1
        elif re.search(r'<time datetime="\d{4}-\d{2}-\d{2}"', html):
            fails.append(f"48 {slug}: stray visible <time> date in body")
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

    # --- gate 48b: sitemap lastmod format + agreement with schema ---
    sm_path = os.path.join(DIST, "sitemap.xml")
    if not os.path.exists(sm_path):
        fails.append("48 sitemap.xml missing")
        g48b += 1
    else:
        smx = open(sm_path, encoding="utf-8").read()
        if 'xmlns:news=' not in smx:
            fails.append("48 sitemap missing news namespace declaration")
            g48b += 1
        lastmods = re.findall(r'<lastmod>([^<]+)</lastmod>', smx)
        pubdates = re.findall(r'<news:publication_date>([^<]+)</news:publication_date>', smx)
        if not lastmods:
            fails.append("48 sitemap has no <lastmod> entries")
            g48b += 1
        # W3C datetime: YYYY-MM-DDThh:mm:ss+hh:mm — time component REQUIRED here
        W3C = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$')
        bad_fmt = [x for x in lastmods if not W3C.match(x)]
        if bad_fmt:
            fails.append(f"48 {len(bad_fmt)} sitemap <lastmod> not W3C datetime "
                         f"(no time component?): e.g. {bad_fmt[:2]}")
            g48b += 1
        bad_pub = [x for x in pubdates if not W3C.match(x)]
        if bad_pub:
            fails.append(f"48 {len(bad_pub)} <news:publication_date> not W3C datetime: "
                         f"{bad_pub[:2]}")
            g48b += 1
        # recipe entries must carry BOTH dates
        n_recipe_urls = smx.count("/resepi/")
        if len(pubdates) < n_recipe_urls * 0.9:
            fails.append(f"48 only {len(pubdates)} publication_dates for "
                         f"{n_recipe_urls} recipe URLs — publish date missing")
            g48b += 1
        # lastmod must agree with schema (compare date part)
        lm_dates = {x[:10] for x in lastmods if W3C.match(x)}
        if lm_dates and CONTENT_REVISED not in lm_dates:
            fails.append(f"48 sitemap lastmod {sorted(lm_dates)[:3]} does not include "
                         f"CONTENT_REVISED {CONTENT_REVISED}")
            g48b += 1
        if any(d > "2026-11-30" for d in lm_dates):
            fails.append("48 sitemap lastmod contains an implausibly recent date")
            g48b += 1
    if g48b:
        g48 += g48b

    # --- gate 50: RSS pubDate must be RFC-822, not ISO-8601 ---
    fd_path = os.path.join(DIST, "feed.xml")
    if not os.path.exists(fd_path):
        fails.append("50 feed.xml missing")
        g50 += 1
    else:
        fdx = open(fd_path, encoding="utf-8").read()
        # RFC-1123: 'Wed, 28 Jan 2026 00:00:00 +0800'
        RFC = re.compile(r'^[A-Z][a-z]{2}, \d{2} [A-Z][a-z]{2} \d{4} '
                         r'\d{2}:\d{2}:\d{2} [+-]\d{4}$')
        for tag in ("pubDate", "lastBuildDate"):
            vals = re.findall(rf'<{tag}>([^<]+)</{tag}>', fdx)
            if not vals:
                fails.append(f"50 feed has no <{tag}>")
                g50 += 1
                continue
            bad = [v for v in vals if not RFC.match(v)]
            if bad:
                fails.append(f"50 <{tag}> not RFC-822 (RSS 2.0 requires it): "
                             f"e.g. {bad[:2]}")
                g50 += 1
        if "<pubDate>" not in fdx:
            fails.append("50 feed has no <pubDate> on items")
            g50 += 1

    print("=" * 72)
    print("DATE GATES 47-50 (truthful, correctly-formatted dates)")
    print("=" * 72)
    print(f"  #47 [{'PASS' if not g47 else 'FAIL'}] dateModified == {CONTENT_REVISED} "
          f"on all recipes, never future, never before datePublished")
    print(f"  #48 [{'PASS' if not g48 else 'FAIL'}] date hidden from readers; "
          f"sitemap lastmod is W3C datetime and agrees with schema")
    print(f"  #49 [{'PASS' if not g49 else 'FAIL'}] datePublished stays varied "
          f"({len(published)} distinct) and is not collapsed into dateModified")
    print(f"  #50 [{'PASS' if not g50 else 'FAIL'}] feed pubDate/lastBuildDate "
          f"are RFC-822 (RSS 2.0 requirement)")
    print("-" * 72)
    for m in fails[:25]:
        print("   ", m)
    if len(fails) > 25:
        print(f"    ... and {len(fails)-25} more")
    if fails:
        print(f"   {len(fails)} failure(s) across {n_recipe} recipe pages")
        sys.exit(1)
    print(f"   4/4 date gates pass ({n_recipe} recipe pages)")
    sys.exit(0)


if __name__ == "__main__":
    main()
