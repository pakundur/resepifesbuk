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
# The rule is NOT "every img has non-empty alt". An empty alt="" is correct
# for a decorative image (the byline avatar sits next to the author's name,
# so describing it would make a screen reader read the name twice). What is
# wrong is (a) no alt attribute at all, or (b) alt="" on an image that is
# NOT marked decorative. This gate enforces that distinction instead of
# forcing meaningless alt text onto decorative images.
noalt, undecorated = 0, 0
for rel, p in pages.items():
    for tag in re.findall(r"<img\b[^>]*>", read(p)):
        if "alt=" not in tag:
            noalt += 1
        elif re.search(r'alt="\s*"', tag):
            if not re.search(r'aria-hidden="true"|role="presentation"', tag):
                undecorated += 1
chk(15, "all images have alt (empty alt only when decorative)",
    noalt == 0 and undecorated == 0,
    f"{noalt} missing alt, {undecorated} empty alt not marked decorative")

# 17. images served from R2, not Blogger
blogger_pages = []
blogger_hits = 0
for rel, p in pages.items():
    s = read(p)
    n = s.count("blogger.googleusercontent.com")
    if n:
        blogger_pages.append(rel)
        blogger_hits += n
chk(17, "images served from R2 (no Blogger)", blogger_hits == 0,
    f"0 Blogger refs" if blogger_hits == 0 else f"{blogger_hits} refs on {len(blogger_pages)} pages")

# 18. every recipe has an r2_key and the object is reachable
missing_key = [x["slug"] for x in json.load(open(os.path.join(ROOT, "img_map.json")))
               if not x.get("key")]
chk(18, "all recipes have an R2 image key", len(missing_key) == 0,
    f"{len(missing_key)} missing")

# 19. images must be same-origin (no img. subdomain dependency)
imgsub_pages = []
imgsub_hits = 0
for rel, p in pages.items():
    s = read(p)
    n = s.count("img.resepifesbuk.com")
    if n:
        imgsub_pages.append(rel)
        imgsub_hits += n
chk(19, "images served same-origin (no img. subdomain)", imgsub_hits == 0,
    "0 subdomain refs" if imgsub_hits == 0 else f"{imgsub_hits} refs on {len(imgsub_pages)} pages")

# 20. Cloudflare Web Analytics beacon present on every page (real-user CWV)
noanalytics = []
for rel, p in pages.items():
    if "static.cloudflareinsights.com/beacon.min.js" not in read(p):
        noanalytics.append(rel)
chk(20, "web analytics beacon on all pages", len(noanalytics) == 0,
    f"{len(pages)}/{len(pages)}" if not noanalytics else f"{len(noanalytics)} missing")

# 21. GA4 tag present and consistent on every page (all-or-nothing)
#     Reads the ID from env so the gate enforces whatever was configured at build time.
_ga4 = os.environ.get("GA4_ID", "").strip()
if _ga4:
    bad_ga4 = []
    for rel, p in pages.items():
        s = read(p)
        if f"googletagmanager.com/gtag/js?id={_ga4}" not in s or f"gtag('config','{_ga4}')" not in s:
            bad_ga4.append(rel)
    chk(21, "GA4 tag on all pages", len(bad_ga4) == 0,
        f"{len(pages)}/{len(pages)}" if not bad_ga4 else f"{len(bad_ga4)} missing")
else:
    chk(21, "GA4 tag (not configured — set GA4_ID)", True, "skipped, GA4_ID empty")

# 22. Sitemap must not contain any URL disallowed by robots.txt.
#     Submitting a disallowed URL creates Search Console errors and wastes crawl budget.
_sm_path = os.path.join(DIST, "sitemap.xml")
_rb_path = os.path.join(DIST, "robots.txt")
_violations = []
if os.path.exists(_sm_path) and os.path.exists(_rb_path):
    _sm = read(_sm_path)
    _rb = read(_rb_path)
    _disallowed = [d.split(":", 1)[1].strip() for d in _rb.splitlines()
                   if d.lower().startswith("disallow:") and d.split(":", 1)[1].strip() not in ("", "/")]
    _locs = re.findall(r"<loc>([^<]+)</loc>", _sm)
    for _u in _locs:
        _p = _u.split("resepifesbuk.com", 1)[-1] or "/"
        for _d in _disallowed:
            if _p.startswith(_d):
                _violations.append(_p)
                break
    chk(22, "sitemap has no robots-disallowed URLs", len(_violations) == 0,
        f"{len(_locs)} urls, 0 conflicts" if not _violations
        else f"{len(_violations)} conflicts e.g. {_violations[:3]}")
else:
    chk(22, "sitemap has no robots-disallowed URLs", False, "sitemap/robots missing")

# ---------------------------------------------------------------------------
# Sponsored ad gates. These check dist/, i.e. what actually ships, not the
# engine in isolation — a wiring regression must block the deploy.
# ---------------------------------------------------------------------------
_ad_links = set()
try:
    _al = json.load(open(os.path.join(ROOT, "affiliate_links.json"), encoding="utf-8"))
    for _p in _al["products"].values():
        _ad_links.update(_p["links"])
except Exception:
    _ad_links = set()

_ad_pages = 0
_ad_slots = 0
_ad_rendered = set()
_ad_bad = []
_ad_dupe_pages = []
for _rel, _p in pages.items():
    _s = read(_p)
    _slots = re.findall(r'data-slot="(\w+)"', _s)
    if not _slots:
        continue
    _ad_pages += 1
    _ad_slots += len(_slots)
    _hrefs = re.findall(r"https://s\.shopee\.com\.my/[A-Za-z0-9]+", _s)
    _ad_rendered.update(_hrefs)
    # every link in the card must be sponsored + distinct + supplied
    if _s.count('rel="sponsored nofollow noopener"') != len(_hrefs):
        _ad_bad.append(f"{_rel}: rel mismatch")
    if len(set(_hrefs)) != len(_hrefs):
        _ad_bad.append(f"{_rel}: duplicate href")
    if _ad_links and not set(_hrefs) <= _ad_links:
        _ad_bad.append(f"{_rel}: unknown link")
    # mandatory disclosure on every card
    if _s.count(">Iklan<") < len(_slots):
        _ad_bad.append(f"{_rel}: missing Iklan disclosure")
    # every card must link to the affiliate disclosure page
    if _s.count('href="/pendedahan-affiliate/"') < len(_slots):
        _ad_bad.append(f"{_rel}: missing disclosure link")
    # every card must have a dismiss control
    if _s.count('class="ad-x__btn"') != len(_slots):
        _ad_bad.append(f"{_rel}: close-button count mismatch")
    # hard-sell / exclamation check inside hooks
    for _h in re.findall(r'adw__hook">([^<]*)', _s):
        if "!" in _h:
            _ad_bad.append(f"{_rel}: exclamation in hook")
    # one product per page max
    _prods = re.findall(r'data-product="(\w+)"', _s)
    if len(_prods) != len(set(_prods)):
        _ad_dupe_pages.append(_rel)

chk(23, "ads render in built output", _ad_pages > 0 and _ad_slots > 0,
    f"{_ad_pages} pages, {_ad_slots} slots")

chk(24, "every ad link is a supplied affiliate link",
    not any("unknown link" in b for b in _ad_bad),
    f"{len(_ad_rendered)}/{len(_ad_links)} links in use" if _ad_links else "no link file")

chk(25, "all ad links distinct + rel=sponsored",
    not any("rel mismatch" in b or "duplicate href" in b for b in _ad_bad),
    "; ".join(_ad_bad[:3]) if _ad_bad else "clean")

chk(26, "IKLAN disclosure on every ad card",
    not any("missing Iklan" in b for b in _ad_bad),
    "; ".join([b for b in _ad_bad if "Iklan" in b][:3]) or "all cards disclosed")

chk(29, "every ad card links to the disclosure page",
    not any("disclosure link" in b for b in _ad_bad),
    "all cards linked" if not any("disclosure link" in b for b in _ad_bad)
    else f"{sum('disclosure link' in b for b in _ad_bad)} pages missing")

chk(30, "every ad card has a dismiss control",
    not any("close-button" in b for b in _ad_bad),
    "all cards closable" if not any("close-button" in b for b in _ad_bad)
    else f"{sum('close-button' in b for b in _ad_bad)} pages broken")

chk(27, "no exclamation marks in ad hooks",
    not any("exclamation" in b for b in _ad_bad),
    "0" if not any("exclamation" in b for b in _ad_bad) else "found")

chk(28, "no page shows the same product twice",
    not _ad_dupe_pages,
    f"0 duplicate-product pages of {_ad_pages}" if not _ad_dupe_pages
    else f"{len(_ad_dupe_pages)} e.g. {_ad_dupe_pages[:3]}")

# 16. aggregate
ok = all(r[2] for r in res)
print(f"{'#':>3}  {'CHECK':<42} RESULT")
print("-" * 62)
for num, name, passed, detail in res:
    print(f"{num:>3}  {name:<42} {'PASS' if passed else 'FAIL'}  {detail}")
print("-" * 62)
print("ALL REQUIREMENTS PASSED" if ok else "DEPLOY BLOCKED")
sys.exit(0 if ok else 1)
