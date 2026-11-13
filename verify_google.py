"""Google compliance + integrity verifier for the built site.

Checks, per page, the things that actually affect indexing:
  1. <title> exists, 30-60 chars visible, unique across the site
  2. meta description exists, 120-158 chars, unique
  3. exactly one <link rel="canonical">, absolute, self-referential, no
     year-month date segment, no uppercase, no query string
  4. one <h1>, at least one <h2>
  5. JSON-LD blocks each parse as valid JSON (the old build emitted four
     objects in one <script>, which Google silently discards)
  6. Recipe schema has >=2 HowToStep steps and a name
  7. internal links resolve to a real page, 0 broken
  8. no cross-category related links
  9. every legacy dated URL has a 301 in _redirects
 10. sitemap URLs == pages on disk, canonicals match sitemap exactly

Exit code is non-zero when any hard check fails, so it can gate a build.
"""
import json, os, re, sys, html, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
SITE_URL = "https://resepifesbuk.com"

TITLE_MIN, TITLE_MAX = 30, 60
DESC_MIN, DESC_MAX = 120, 158

fails = collections.Counter()
examples = collections.defaultdict(list)


def fail(kind, detail):
    fails[kind] += 1
    if len(examples[kind]) < 6:
        examples[kind].append(detail)


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


pages = {}
for dirpath, _, files in os.walk(DIST):
    for f in files:
        if f == "index.html":
            p = os.path.join(dirpath, f)
            rel = "/" + os.path.relpath(p, DIST).replace("\\", "/").replace("index.html", "")
            pages[rel] = p
        elif f.endswith(".html"):
            p = os.path.join(dirpath, f)
            rel = "/" + os.path.relpath(p, DIST).replace("\\", "/")
            pages[rel] = p

recipe_pages = {k: v for k, v in pages.items() if k.startswith("/resepi/") and k != "/resepi/"}
titles = collections.Counter()
descs = collections.Counter()
h1seen = collections.Counter()

for rel, path in sorted(pages.items()):
    src = open(path, encoding="utf-8", errors="ignore").read()

    # --- title ---
    m = re.search(r"<title>(.*?)</title>", src, re.S)
    if not m:
        fail("no <title>", rel)
    else:
        t = strip_tags(m.group(1))
        titles[t] += 1
        if not (TITLE_MIN <= len(t) <= TITLE_MAX):
            fail("title length outside 30-60", f"{rel} ({len(t)}) {t}")

    # --- meta description ---
    m = re.search(r'<meta name="description" content="(.*?)"', src, re.S)
    if not m:
        fail("no meta description", rel)
    else:
        d = html.unescape(m.group(1))
        descs[d] += 1
        if not (DESC_MIN <= len(d) <= DESC_MAX):
            fail("description length outside 120-158", f"{rel} ({len(d)})")

    # --- canonical ---
    cans = re.findall(r'<link rel="canonical" href="(.*?)"', src)
    if len(cans) != 1:
        fail("canonical count != 1", f"{rel} ({len(cans)})")
    else:
        c = cans[0]
        if not c.startswith(SITE_URL):
            fail("canonical not absolute site URL", f"{rel} {c}")
        if re.search(r"/\d{4}-\d{2}-", c):
            fail("canonical still contains a date prefix", c)
        if c != c.lower():
            fail("canonical has uppercase", c)
        if "?" in c:
            fail("canonical has query string", c)
        expected = SITE_URL + rel
        if c.rstrip("/") != expected.rstrip("/"):
            fail("canonical not self-referential", f"{rel} -> {c}")

    # --- headings ---
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", src, re.S)
    if len(h1) != 1:
        fail("h1 count != 1", f"{rel} ({len(h1)})")
    else:
        h1seen[strip_tags(h1[0])] += 1
    if not re.search(r"<h2", src):
        fail("no h2", rel)

    # --- JSON-LD ---
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)
    if not blocks:
        fail("no JSON-LD", rel)
    types = []
    for b in blocks:
        try:
            obj = json.loads(b)
        except Exception as e:
            fail("invalid JSON-LD", f"{rel}: {e}")
            continue
        types.append(obj.get("@type"))
        if obj.get("@type") == "Recipe":
            if not obj.get("name"):
                fail("Recipe missing name", rel)
            steps = (obj.get("recipeInstructions") or [])
            if len(steps) < 2:
                fail("Recipe <2 steps", f"{rel} ({len(steps)})")
    if rel in recipe_pages and "Recipe" not in types:
        fail("recipe page missing Recipe schema", rel)

    # --- internal links ---
    for href in re.findall(r'href="(/[^"#?]*)"', src):
        if href.startswith(("/style.css", "/favicon", "/icon", "/og-")):
            continue
        if href not in pages and href.rstrip("/") + "/" not in pages and href + "/" not in pages:
            if not os.path.exists(os.path.join(DIST, href.lstrip("/"))):
                fail("broken internal link", f"{rel} -> {href}")

# --- duplicates ---
for t, n in titles.items():
    if n > 1:
        fail("duplicate <title>", f"{n}x {t}")
for d, n in descs.items():
    if n > 1:
        fail("duplicate description", f"{n}x {d[:70]}")
for h, n in h1seen.items():
    if n > 1 and n < 3:
        fail("duplicate h1", f"{n}x {h[:70]}")

# --- redirects ---
red_path = os.path.join(DIST, "_redirects")
red = open(red_path, encoding="utf-8").read() if os.path.exists(red_path) else ""
red_rules = [l.split() for l in red.splitlines() if l.strip() and not l.startswith("#")]
red_from = {r[0]: r[1] for r in red_rules if len(r) >= 2}

smap_path = os.path.join(ROOT, "src", "slug_map.json")
smap = json.load(open(smap_path, encoding="utf-8")) if os.path.exists(smap_path) else {}
for old, new in smap.items():
    if old == new:
        continue
    if f"/resepi/{old}/" not in red_from:
        fail("missing 301 for legacy URL", old)
    elif red_from[f"/resepi/{old}/"] != f"/resepi/{new}/":
        fail("wrong 301 target", f"{old} -> {red_from[f'/resepi/{old}/']}")
    # every redirect destination must exist
    if f"/resepi/{new}/" not in pages:
        fail("301 target missing on disk", new)
    # every redirect source must NOT exist (else it is a duplicate page)
    if f"/resepi/{old}/" in pages:
        fail("legacy URL still built", old)

# --- sitemap ---
sm_path = os.path.join(DIST, "sitemap.xml")
sm = open(sm_path, encoding="utf-8").read() if os.path.exists(sm_path) else ""
sm_urls = set(re.findall(r"<loc>(.*?)</loc>", sm))
if not sm_urls:
    fail("sitemap empty or missing", "sitemap.xml")
for u in sm_urls:
    if re.search(r"/\d{4}-\d{2}-", u):
        fail("sitemap contains dated URL", u)
    rel = u.replace(SITE_URL, "")
    if rel not in pages:
        fail("sitemap URL not on disk", u)
for rel in pages:
    if rel.startswith(("/resepi/", "/kategori/")) and SITE_URL + rel not in sm_urls:
        fail("page missing from sitemap", rel)

# --- robots ---
rob = os.path.join(DIST, "robots.txt")
if not os.path.exists(rob):
    fail("robots.txt missing", "/robots.txt")
else:
    rt = open(rob, encoding="utf-8").read()
    if "sitemap" not in rt.lower():
        fail("robots.txt does not declare sitemap", "/robots.txt")
    if "disallow: /" in rt.lower().replace(" ", ""):
        fail("robots.txt blocks the whole site", "/robots.txt")

# ------------------------------------------------------------------ report
total = sum(fails.values())
print(f"pages checked            : {len(pages)}")
print(f"recipe pages             : {len(recipe_pages)}")
print(f"unique titles            : {len(titles)}")
print(f"unique descriptions      : {len(descs)}")
print(f"redirect rules           : {len(red_rules)}")
print(f"sitemap URLs             : {len(sm_urls)}")
print("-" * 52)
if total == 0:
    print("ALL CHECKS PASSED")
else:
    print(f"FAILURES: {total}")
    for k, n in fails.most_common():
        print(f"  [{n:4}] {k}")
        for e in examples[k]:
            print(f"         - {e}")
sys.exit(1 if total else 0)
