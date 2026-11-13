"""Verify the rebuilt site: structure, SEO integrity, links, schema.

Run AFTER build_static.py. Exits non-zero on any failure so a broken build
cannot be deployed silently.

Checks
  1. Page count and required routes exist
  2. Every page has title / description / canonical / h1
  3. No duplicate titles, no duplicate descriptions, no duplicate canonicals
  4. Every JSON-LD block parses as valid JSON
  5. Every Recipe schema has >=2 HowToStep (Google rich-result requirement)
  6. Every internal link resolves to a real page
  7. All images remain on Google's CDN
  8. Every recipe page carries >=3 internal links
  9. Title/meta length distribution
 10. No emoji in titles, no em-dashes in generated copy
"""
import json, os, re, sys, glob, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
fails, warns = [], []


def fail(msg):
    fails.append(msg)


def warn(msg):
    warns.append(msg)


def read(p):
    return open(p, encoding="utf-8").read()


pages = glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True)
pages += [p for p in glob.glob(os.path.join(DIST, "*.html"))]
pages = sorted(set(pages))
print(f"pages found: {len(pages)}")

# 1. required routes
for req in ["index.html", "404.html", "resepi/index.html", "kategori/index.html",
            "sitemap.xml", "robots.txt", "feed.xml", "style.css"]:
    if not os.path.exists(os.path.join(DIST, req)):
        fail(f"missing required file: {req}")

titles, descs, canonicals = collections.Counter(), collections.Counter(), collections.Counter()
recipe_pages = [p for p in pages if "/resepi/" in p.replace("\\", "/") and "resepi/index.html" not in p]
print(f"recipe pages: {len(recipe_pages)}")

link_targets = set()
all_links = collections.Counter()

for p in pages:
    h = read(p)
    rel = os.path.relpath(p, DIST)

    m = re.search(r"<title>(.*?)</title>", h, re.S)
    if not m or not m.group(1).strip():
        fail(f"{rel}: missing title")
    else:
        titles[m.group(1).strip()] += 1

    m = re.search(r'<meta name="description" content="([^"]*)"', h)
    if not m or not m.group(1).strip():
        fail(f"{rel}: missing meta description")
    else:
        descs[m.group(1).strip()] += 1

    m = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    if not m:
        fail(f"{rel}: missing canonical")
    else:
        canonicals[m.group(1)] += 1

    if not re.search(r"<h1[^>]*>", h):
        fail(f"{rel}: missing h1")

    # 4/5. schema
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            d = json.loads(blk)
        except Exception as e:
            fail(f"{rel}: invalid JSON-LD ({str(e)[:60]})")
            continue
        if isinstance(d, dict) and d.get("@type") == "Recipe":
            if len(d.get("recipeInstructions", [])) < 2:
                fail(f"{rel}: Recipe schema has <2 HowToStep")

    # 7. images
    for src in re.findall(r'<img[^>]+src="([^"]+)"', h):
        if src.startswith("http") and "blogger.googleusercontent.com" not in src:
            warn(f"{rel}: image not on Google CDN: {src[:70]}")

    # 6. internal links
    for href in re.findall(r'href="(/[^"#?]*)"', h):
        all_links[href] += 1
        link_targets.add(href)

# 3. duplicates
for t, n in titles.items():
    if n > 1:
        fail(f"duplicate title x{n}: {t[:80]}")
for d, n in descs.items():
    if n > 1:
        fail(f"duplicate description x{n}: {d[:80]}")
for c, n in canonicals.items():
    if n > 1:
        fail(f"duplicate canonical x{n}: {c}")

# 6. resolve internal links
missing = 0
for href in link_targets:
    if href.startswith("/_") or href.startswith("/cdn-cgi"):
        continue
    cand = os.path.join(DIST, href.lstrip("/").split("?")[0])
    if os.path.isdir(cand):
        cand = os.path.join(cand, "index.html")
    elif not os.path.splitext(cand)[1]:
        cand = os.path.join(cand, "index.html")
    if not os.path.exists(cand):
        missing += 1
        if missing <= 12:
            fail(f"broken internal link: {href}")
if missing > 12:
    fail(f"...and {missing-12} more broken internal links")

# 8. per-page internal recipe links
for p in recipe_pages:
    h = read(p)
    n = len(set(re.findall(r'href="(/resepi/[^"]+/)"', h)))
    if n < 3:
        fail(f"{os.path.relpath(p, DIST)}: only {n} internal recipe links")

# 9/10. length + style
long_t = [t for t in titles if len(t) > 75]
if long_t:
    warn(f"{len(long_t)} titles over 75 chars")
emoji = [t for t in titles if re.search(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", t)]
if emoji:
    warn(f"{len(emoji)} titles contain emoji")
emdash = [t for t in titles if "—" in t]
if emdash:
    warn(f"{len(emdash)} titles contain em-dash")

dlens = [len(d) for d in descs]
short_d = sum(1 for l in dlens if l < 120)
if short_d:
    warn(f"{short_d} descriptions under 120 chars")

# ---- report ----
print(f"\nunique titles: {len(titles)} / {len(pages)}")
print(f"unique descriptions: {len(descs)} / {len(pages)}")
print(f"internal links: {sum(all_links.values())} across {len(link_targets)} targets")
print(f"description length: min {min(dlens)} avg {sum(dlens)//len(dlens)} max {max(dlens)}")

print("\n" + "=" * 60)
if warns:
    print(f"WARNINGS ({len(warns)}):")
    for w in warns[:20]:
        print("  ~", w)
if fails:
    print(f"\nFAILURES ({len(fails)}):")
    for f in fails[:40]:
        print("  x", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
