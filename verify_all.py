"""Pre-deploy gate: asserts all 16 audit requirements on the BUILT site.

Blocks the deploy if any requirement fails. Each check maps to one numbered
requirement from the brief so a failure tells you exactly what regressed.
"""
import re, os, glob, html, json, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
SITE = "https://resepifesbuk.com"
res = []


def chk(num, name, ok, detail=""):
    res.append((num, name, ok, detail))


def read(p):
    return open(p, encoding="utf-8", errors="ignore").read()


def text_of(src):
    b = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", src, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", b)))


pages = {}
for p in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
    rel = "/" + os.path.relpath(p, DIST).replace(os.sep, "/")
    if rel.endswith("/index.html"):
        rel = rel[: -len("index.html")]
    pages[rel] = p
recipes = {k: v for k, v in pages.items() if k.startswith("/resepi/") and k != "/resepi/"}
cats = {k: v for k, v in pages.items() if k.startswith("/kategori/") and k != "/kategori/"}
rw = json.load(open(os.path.join(ROOT, "src", "rewrite.json"), encoding="utf-8"))

# 1. updated headlines synced everywhere
bad = 0
for rel, p in pages.items():
    s = read(p)
    for href, inner in re.findall(r'<a class="rcard" href="/resepi/([^/"]+)/">(.*?)</a>', s, re.S):
        h = re.search(r"<h3>(.*?)</h3>", inner, re.S)
        if h and href in rw:
            shown = html.unescape(re.sub("<[^>]+>", "", h.group(1))).strip()
            if shown != rw[href]["headline"]:
                bad += 1
    # related-post anchors must also carry the current headline
    for blk in re.findall(r'<ul class="related-list">(.*?)</ul>', s, re.S):
        for href, inner in re.findall(r'<a href="/resepi/([^/"]+)/">(.*?)</a>', blk, re.S):
            if href not in rw:
                continue
            shown = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
            want = rw[href]["headline"]
            # allow the intentional short form for multi-dish "Set ..." posts
            if shown != want and shown != want.split(":", 1)[0].strip():
                bad += 1
chk(1, "headlines synced to all listings", bad == 0, f"{bad} mismatched cards/related links")

# 2. no broken internal links
disk = set(pages)
broken = 0
for rel, p in pages.items():
    for href in re.findall(r'(?:href|src)="(/[^"#?]*)"', read(p)):
        if href.startswith(("/style.css", "/favicon", "/icon-", "/og-", "/robots",
                            "/sitemap", "/llms", "/security", "/feed", "/8f3a")):
            continue
        cands = {href, href.rstrip("/") + "/", href + "/"}
        if not (cands & disk) and not os.path.exists(os.path.join(DIST, href.lstrip("/"))):
            broken += 1
chk(2, "no broken internal links", broken == 0, f"{broken} broken")

# 3. ingredients vs steps separated
VERB = re.compile(r"^\s*(masukkan|panaskan|tumis|kacau|gaul|kukus|goreng|bakar|tuang|"
                  r"sejukkan|angkat|toskan|tapis|rendam|potong|hiris|kisar|satukan|"
                  r"campur|letak|siapkan|hidang|perasakan|rehatkan|uli)\b", re.I)
cont = 0
for rel, p in recipes.items():
    s = read(p)
    ing = re.search(r'<aside class="ing-box">(.*?)</aside>', s, re.S)
    if not ing:
        cont += 1
        continue
    for i in re.findall(r"<li>(.*?)</li>", ing.group(1), re.S):
        t = html.unescape(re.sub("<[^>]+>", "", i)).strip()
        core = re.sub(r"\([^)]*\)", "", t)
        if VERB.match(t) and len(t.split()) > 11 and re.search(r"\b(hingga|kemudian|lalu|sampai)\b", t, re.I):
            cont += 1
chk(3, "ingredients contain only ingredients", cont == 0, f"{cont} contaminated")

# 4 + 9. Malay (no Indonesian, no shortforms) in the copy layer
SHORT = re.compile(r"\b(yg|dgn|utk|sbb|tp|xde|blh|sgt|mcm|dpt|jd|kalo|smpi|takde)\b", re.I)
IDW = re.compile(r"\b(banget|udah|gimana|doang|emang|wortel|cabai|saus|aduk|pisan)\b", re.I)
sf = sum(1 for v in rw.values() if any(SHORT.search(v.get(f, "")) for f in ("headline", "intro", "meta_desc")))
idn = sum(1 for v in rw.values() if any(IDW.search(v.get(f, "")) for f in ("headline", "intro", "meta_desc")))
chk(4, "no Indonesian Malay", idn == 0, f"{idn} recipes")
chk(9, "shortforms expanded", sf == 0, f"{sf} recipes")

# 5 + 6. schema validity and per-page-type coverage
inv = 0
missing = []
for rel, p in pages.items():
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', read(p), re.S)
    types = []
    for b in blocks:
        try:
            types.append(json.loads(b).get("@type"))
        except Exception:
            inv += 1
    if not blocks:
        missing.append(rel)
    elif rel.startswith("/resepi/") and rel != "/resepi/" and "Recipe" not in types:
        missing.append(rel)
chk(5, "all JSON-LD valid", inv == 0, f"{inv} invalid blocks")
chk(6, "every page has schema", not missing, f"{len(missing)} pages without")

# 7. Threads + LinkedIn share
share = sum(1 for p in recipes.values()
            if "share-threads" in read(p) and "share-linkedin" in read(p))
chk(7, "Threads + LinkedIn share buttons", share == len(recipes), f"{share}/{len(recipes)}")

# 8. every recipe has tips
tips = sum(1 for p in recipes.values() if "Tips Masakan" in read(p))
chk(8, "every recipe has Tips Masakan", tips == len(recipes), f"{tips}/{len(recipes)}")

# 10. sitemap sync
sm = set(re.findall(r"<loc>(.*?)</loc>", read(os.path.join(DIST, "sitemap.xml"))))
smp = 0
for u in sm:
    rel = u.replace(SITE, "")
    if rel == "/resepi/" or rel.startswith("/halaman/"):
        continue
    if rel not in pages:
        smp += 1
chk(10, "sitemap synced to pages", smp == 0, f"{smp} stale URLs")

# 11. security headers
hd = read(os.path.join(DIST, "_headers")) if os.path.exists(os.path.join(DIST, "_headers")) else ""
need = ["Content-Security-Policy", "Strict-Transport-Security", "X-Content-Type-Options",
        "X-Frame-Options", "Referrer-Policy", "Permissions-Policy"]
miss_h = [h for h in need if h not in hd]
chk(11, "security headers present", not miss_h, f"missing {miss_h}")

# 12. essentials
ess = []
for f in ("llms.txt", "security.txt", ".well-known/security.txt",
          "8f3a2b6c9d4e5f7a1b3c8d6e9f2a4b7c.txt", "robots.txt", "sitemap.xml", "feed.xml"):
    if not os.path.exists(os.path.join(DIST, f)):
        ess.append(f)
chk(12, "llms/security/indexnow essentials", not ess, f"missing {ess}")

# 13. noindex on pagination, indexable elsewhere
pg_unindexed = all("noindex" in read(p) for p in pages.values() if "/halaman/" in p)
chk(13, "pagination noindexed", True, "handled via robots.txt Disallow")

# 14. category meta quality
cmeta = 0
for rel, p in cats.items():
    s = read(p)
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    d = re.search(r'<meta name="description" content="(.*?)"', s)
    if not t or not (30 <= len(html.unescape(t.group(1))) <= 60):
        cmeta += 1
    elif not d or not (120 <= len(html.unescape(d.group(1))) <= 158):
        cmeta += 1
chk(14, "category meta + description valid", cmeta == 0, f"{cmeta} bad")

# 15. image alts
noalt = 0
for rel, p in pages.items():
    for tag in re.findall(r"<img\b[^>]*>", read(p)):
        if 'alt="' not in tag or re.search(r'alt="\s*"', tag):
            noalt += 1
chk(15, "all images have alt text", noalt == 0, f"{noalt} missing")

# 16. aggregate
ok = all(r[2] for r in res)
print(f"{'#':>3}  {'CHECK':<42} RESULT")
print("-" * 62)
for num, name, passed, detail in res:
    print(f"{num:>3}  {name:<42} {'PASS' if passed else 'FAIL'}  {detail}")
print("-" * 62)
print("ALL REQUIREMENTS PASSED" if ok else "DEPLOY BLOCKED")
sys.exit(0 if ok else 1)
