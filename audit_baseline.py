"""Baseline audit of the BUILT site — mechanical checks, no LLM.

Covers: headline sync, broken links, ingredient/step separation, sitemap sync,
category meta quality, image alt coverage, schema presence per page type.
"""
import re, os, glob, html, json, collections, sys

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
SITE = "https://resepifesbuk.com"
fails = collections.Counter()
ex = collections.defaultdict(list)


def fail(k, d):
    fails[k] += 1
    if len(ex[k]) < 5:
        ex[k].append(d)


def body_text(src):
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

# expected title/meta per recipe slug (from rewrite.json, the source of truth)
ROOT = os.path.dirname(os.path.abspath(__file__))
rw = json.load(open(os.path.join(ROOT, "src", "rewrite.json"), encoding="utf-8"))

# ---------- 1. headline sync: every listing must show the updated headline ----------
for rel, path in pages.items():
    src = open(path, encoding="utf-8", errors="ignore").read()
    # cards + related links render an anchor whose text should match the target's h1
    for href, text in re.findall(r'<a[^>]+href="(/resepi/[^"]+)"[^>]*>(.*?)</a>', src, re.S):
        slug = href.strip("/").split("/")[-1]
        if slug not in rw:
            continue
        shown = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text))).strip()
        # anchors are intentionally shortened (dish name only); flag only if the
        # shown text shares NO word with the real headline
        head = rw[slug]["headline"].lower()
        words = [w for w in re.findall(r"[a-z]{4,}", shown.lower())]
        if words and not any(w in head for w in words):
            fail("listing anchor unrelated to headline", f"{rel} -> {shown[:40]}")

# ---------- 2. broken links ----------
disk = set(pages)
for rel, path in pages.items():
    src = open(path, encoding="utf-8", errors="ignore").read()
    for href in re.findall(r'(?:href|src)="(/[^"#?]*)"', src):
        if href.startswith(("/style.css", "/favicon", "/icon-", "/og-", "/robots", "/sitemap", "/llms", "/security", "/feed")):
            continue
        cands = {href, href.rstrip("/") + "/", href + "/"}
        if not (cands & disk) and not os.path.exists(os.path.join(DIST, href.lstrip("/"))):
            fail("broken internal link", f"{rel} -> {href}")

# ---------- 3. ingredients vs steps separation ----------
VERB = re.compile(r"\b(masukkan|panaskan|tumis|kacau|gaul|kukus|goreng|bakar|tuang|"
                  r"sejukkan|angkat|toskan|tapis|rendam|potong|hiris|kisar|satukan|"
                  r"campur|letak|siapkan|hidang|perasakan|rehatkan|uli|bentukkan)\b", re.I)
for rel, path in recipes.items():
    src = open(path, encoding="utf-8", errors="ignore").read()
    ing = re.search(r'<aside class="ing-box">(.*?)</aside>', src, re.S)
    stp = re.search(r'<(?:ol|ul) class="steps">(.*?)</(?:ol|ul)>', src, re.S)
    if not stp:
        stp = re.search(r'Cara Penyediaan.*?<ol[^>]*>(.*?)</ol>', src, re.S)
    if ing:
        items = re.findall(r"<li>(.*?)</li>", ing.group(1), re.S)
        if not items:
            fail("ingredient box empty", rel)
        for i in items:
            t = re.sub(r"<[^>]+>", "", i).strip()
            # strip a trailing/inline prep note, which is legitimate style
            core = re.sub(r"\([^)]*\)", "", t)          # (kisar halus)
            core = re.sub(r"\s*[-–]\s*[a-z ]{2,30}$", "", core)  # "- hiris"
            if len(core) > 120:
                fail("ingredient line too long (likely method)", f"{rel}: {t[:70]}")
            # contamination = starts with an imperative verb AND reads as a
            # full instruction (a connective or a second clause present)
            starts_verb = bool(re.match(r"^\s*" + VERB.pattern.strip("\\b()"), t, re.I))
            long_enough = len(t.split()) > 11
            has_clause = bool(re.search(r"\b(hingga|sehingga|kemudian|lalu|sambil|"
                                        r"sebentar|sampai|tadi|tadi\.|dan tumis)\b", t, re.I))
            if starts_verb and long_enough and has_clause:
                fail("method sentence inside ingredients", f"{rel}: {t[:70]}")
    if stp:
        items = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<li>(.*?)</li>", stp.group(1), re.S)]
        if len(items) < 2:
            fail("fewer than 2 steps", f"{rel}: {len(items)}")

# ---------- 10. sitemap sync ----------
sm = open(os.path.join(DIST, "sitemap.xml"), encoding="utf-8").read()
sm_urls = set(re.findall(r"<loc>(.*?)</loc>", sm))
for rel in pages:
    if rel in ("/404.html",) or rel.startswith("/halaman/"):
        continue
    if SITE + rel not in sm_urls and not any(u.rstrip("/") == (SITE + rel).rstrip("/") for u in sm_urls):
        fail("page missing from sitemap", rel)
for u in sm_urls:
    rel = u.replace(SITE, "")
    if rel not in pages:
        fail("sitemap URL not on disk", u)
    # every sitemap URL must be the canonical of a real page
    if rel in pages:
        s = open(pages[rel], encoding="utf-8", errors="ignore").read()
        cm = re.search(r'rel="canonical" href="([^"]+)"', s)
        if cm and cm.group(1).rstrip("/") != u.rstrip("/"):
            fail("canonical != sitemap URL", f"{rel}: {cm.group(1)}")

# ---------- 14. category meta ----------
for rel, path in cats.items():
    s = open(path, encoding="utf-8", errors="ignore").read()
    t = re.search(r"<title>(.*?)</title>", s, re.S)
    d = re.search(r'<meta name="description" content="(.*?)"', s)
    if not t or not (30 <= len(html.unescape(t.group(1))) <= 60):
        fail("category title length", f"{rel}: {len(html.unescape(t.group(1))) if t else 0}")
    if not d or not (120 <= len(html.unescape(d.group(1))) <= 158):
        fail("category description length", f"{rel}: {len(html.unescape(d.group(1))) if d else 0}")

# ---------- 15. image alt ----------
for rel, path in pages.items():
    s = open(path, encoding="utf-8", errors="ignore").read()
    for tag in re.findall(r"<img\b[^>]*>", s):
        if 'alt="' not in tag:
            fail("img without alt", f"{rel}: {tag[:80]}")
        elif re.search(r'alt="\s*"', tag):
            fail("img with empty alt", f"{rel}: {tag[:80]}")

# ---------- 6. schema per page type ----------
for rel, path in pages.items():
    s = open(path, encoding="utf-8", errors="ignore").read()
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    if not blocks:
        fail("no JSON-LD", rel)
        continue
    types = []
    for b in blocks:
        try:
            o = json.loads(b)
            types.append(o.get("@type"))
        except Exception as e:
            fail("invalid JSON-LD", f"{rel}: {e}")
    if rel.startswith("/resepi/") and rel != "/resepi/" and "Recipe" not in types:
        fail("recipe page missing Recipe", rel)
    if rel == "/" and not ({"WebSite", "CollectionPage"} & set(types)):
        fail("home missing WebSite/CollectionPage", rel)
    if rel.startswith("/kategori/") and rel != "/kategori/" and "CollectionPage" not in types:
        fail("category missing CollectionPage", rel)
    if rel.startswith("/halaman/") or rel == "/resepi/":
        if "CollectionPage" not in types:
            fail("paginated index missing CollectionPage", rel)

print(f"pages        : {len(pages)}")
print(f"recipes      : {len(recipes)}")
print(f"categories   : {len(cats)}")
print(f"sitemap URLs : {len(sm_urls)}")
print("-" * 50)
if not fails:
    print("BASELINE: all mechanical checks pass")
else:
    print(f"ISSUES: {sum(fails.values())}")
    for k, n in fails.most_common():
        print(f"  [{n:4}] {k}")
        for e in ex[k]:
            print(f"        - {e}")
sys.exit(1 if fails else 0)
