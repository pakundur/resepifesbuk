"""Verify the generated static site: SEO, schema, canonicals, links."""
import os, re, json, sys, glob, html
from collections import Counter

DIST = os.path.expanduser("~/resepifesbuk/dist")
SITE = "https://resepifesbuk.com"

fails = []
warns = []


def check(cond, msg, hard=True):
    if not cond:
        (fails if hard else warns).append(msg)
    return cond


pages = glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True)
print(f"pages found: {len(pages)}")

no_title = no_desc = no_canon = no_h1 = no_ld = bad_jsonld = 0
titles = Counter()
descs = Counter()
canons = Counter()
schemas = Counter()
long_desc = 0

for p in pages:
    s = open(p, encoding="utf-8").read()
    rel = os.path.relpath(p, DIST)

    t = re.search(r"<title>(.*?)</title>", s, re.S)
    if not t or not t.group(1).strip():
        no_title += 1
    else:
        titles[t.group(1).strip()] += 1

    d = re.search(r'<meta name="description" content="(.*?)">', s, re.S)
    if not d or not d.group(1).strip():
        no_desc += 1
    else:
        descs[d.group(1)] += 1
        if len(d.group(1)) > 165:
            long_desc += 1

    c = re.search(r'<link rel="canonical" href="(.*?)">', s)
    if not c:
        no_canon += 1
    else:
        canons[c.group(1)] += 1
        check(c.group(1).startswith(SITE), f"{rel}: canonical not absolute site URL ({c.group(1)})")

    if not re.search(r"<h1[ >]", s):
        no_h1 += 1

    # JSON-LD blocks
    blocks = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', s, re.S)
    if not blocks:
        no_ld += 1
    else:
        for b in blocks:
            # file may contain several concatenated JSON objects separated by newline
            for line in [x for x in b.split("\n") if x.strip()]:
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        schemas[obj.get("@type", "?")] += 1
                except Exception as e:
                    bad_jsonld += 1
                    if bad_jsonld < 4:
                        print(f"  BAD JSON-LD in {rel}: {str(e)[:90]}")

print(f"\n--- head integrity ---")
print(f"missing title:       {no_title}")
print(f"missing description: {no_desc}")
print(f"missing canonical:   {no_canon}")
print(f"missing h1:          {no_h1}")
print(f"missing JSON-LD:     {no_ld}")
print(f"invalid JSON-LD:     {bad_jsonld}")
print(f"desc > 165 chars:    {long_desc}")

dup_t = [(k, v) for k, v in titles.items() if v > 1]
dup_d = [(k, v) for k, v in descs.items() if v > 1]
dup_c = [(k, v) for k, v in canons.items() if v > 1]
print(f"\nduplicate titles:       {len(dup_t)}")
print(f"duplicate descriptions: {len(dup_d)}")
print(f"duplicate canonicals:   {len(dup_c)}")
for k, v in dup_t[:4]:
    print(f"   x{v}  {k[:80]}")
for k, v in dup_c[:4]:
    print(f"   x{v}  {k[:80]}")

print(f"\n--- schema types ---")
for k, v in schemas.most_common():
    print(f"  {k:20s} {v}")

check(no_title == 0, f"{no_title} pages missing title")
check(no_desc == 0, f"{no_desc} pages missing description")
check(no_canon == 0, f"{no_canon} pages missing canonical")
check(no_h1 == 0, f"{no_h1} pages missing h1")
check(no_ld == 0, f"{no_ld} pages missing JSON-LD")
check(bad_jsonld == 0, f"{bad_jsonld} invalid JSON-LD blocks")
check(len(dup_c) == 0, f"{len(dup_c)} duplicate canonicals")
check(len(dup_t) == 0, f"{len(dup_t)} duplicate titles", hard=False)

print("\n--- internal link check (sample 60 pages) ---")
import random
random.seed(7)
sample = random.sample(pages, min(60, len(pages)))
bad_links = 0
checked = 0
for p in sample:
    s = open(p, encoding="utf-8").read()
    for href in re.findall(r'href="(/[^"#?]*)"', s):
        if href.startswith("//") or href.endswith((".xml", ".css", ".js", ".svg", ".png")):
            continue
        checked += 1
        target = href.strip("/")
        cand = os.path.join(DIST, target, "index.html") if target else os.path.join(DIST, "index.html")
        if not os.path.exists(cand) and not os.path.exists(os.path.join(DIST, target)):
            bad_links += 1
            if bad_links < 6:
                print(f"  BROKEN {href}  (from {os.path.relpath(p, DIST)})")
print(f"  checked {checked} links, broken {bad_links}")

print("\n--- image URLs (must stay on Blogger/Google) ---")
img_hosts = Counter()
for p in pages[:120]:
    s = open(p, encoding="utf-8").read()
    for src in re.findall(r'<img[^>]+src="([^"]+)"', s):
        m = re.match(r"https?://([^/]+)/", src)
        if m:
            img_hosts[m.group(1)] += 1
for h, n in img_hosts.most_common():
    print(f"  {h:40s} {n}")
check(all("googleusercontent" in h for h in img_hosts), "non-Google image hosts present")

print("\n--- recipe page content sanity ---")
rp = glob.glob(os.path.join(DIST, "resepi", "*", "index.html"))
print(f"recipe pages: {len(rp)}")
thin = 0
for p in rp:
    s = open(p, encoding="utf-8").read()
    text = re.sub(r"<[^>]+>", " ", s)
    words = len(text.split())
    if words < 200:
        thin += 1
print(f"pages under 200 words: {thin}")

print("\n=== RESULT ===")
if fails:
    print(f"FAIL ({len(fails)}):")
    for f in fails[:30]:
        print("  -", f)
else:
    print("ALL HARD CHECKS PASSED")
if warns:
    print(f"\nwarnings ({len(warns)}):")
    for w in warns[:10]:
        print("  -", w)
sys.exit(1 if fails else 0)
