"""Verify the LIVE site (not the local build). Run after deploy."""
import urllib.request, urllib.error, json, re, sys, random

BASE = "https://resepifesbuk-git.pages.dev"
fails = []


def get(path, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(BASE + path, headers={"User-Agent": "verify/1.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, ""
        except Exception:
            if a == tries - 1:
                return 0, ""
    return 0, ""


def check(cond, msg):
    if not cond:
        fails.append(msg)
    print(("  PASS  " if cond else "  FAIL  ") + msg)


print("=== core routes ===")
for p in ["/", "/resepi/", "/kategori/", "/cari/", "/tentang/",
          "/sitemap.xml", "/robots.txt", "/feed.xml", "/style.css",
          "/icon-512.png", "/og-default.jpg", "/favicon.svg"]:
    st, body = get(p)
    check(st == 200 and len(body) > 0, f"{p} -> HTTP {st} ({len(body)} bytes)")

print("\n=== deep links (previously 404 on GitHub Pages SPA) ===")
sample = [
    "/resepi/2020-04-resepi-nasi-goreng-bombay-telur-mata/",
    "/kategori/nasi/",
    "/halaman/2/",
    "/halaman/17/",
]
for p in sample:
    st, body = get(p)
    check(st == 200, f"{p} -> HTTP {st}")

print("\n=== SEO head on live recipe page ===")
st, body = get("/resepi/2020-04-resepi-nasi-goreng-bombay-telur-mata/")
check(st == 200, "recipe page reachable")
if body:
    check(bool(re.search(r"<title>[^<]{10,}</title>", body)), "has non-trivial <title>")
    check('rel="canonical"' in body, "has canonical")
    check('href="https://resepifesbuk.com/' in body, "canonical points at production domain")
    check('name="description"' in body, "has meta description")
    check('property="og:image"' in body, "has og:image")
    check('name="twitter:card"' in body, "has twitter card")
    check('hreflang="ms-MY"' in body, "has hreflang ms-MY")
    check(bool(re.search(r"<h1[ >]", body)), "has H1")
    # JSON-LD
    blocks = re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', body, re.S)
    types = []
    for b in blocks:
        for line in [x for x in b.split("\n") if x.strip()]:
            try:
                types.append(json.loads(line).get("@type"))
            except Exception:
                fails.append("invalid JSON-LD on recipe page")
    check("Recipe" in types, f"has Recipe schema (found: {types})")
    check("BreadcrumbList" in types, "has BreadcrumbList schema")
    # real content
    txt = re.sub(r"<[^>]+>", " ", body)
    check(len(txt.split()) > 200, f"substantive content ({len(txt.split())} words)")
    check("Bahan-bahan" in body, "renders ingredients section")
    check("Cara Penyediaan" in body, "renders steps section")
    # images stay on Google
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', body)
    check(all("blogger.googleusercontent" in i for i in imgs if i.startswith("http")),
          f"all {len(imgs)} images hosted on Google")

print("\n=== sitemap integrity ===")
st, sm = get("/sitemap.xml")
locs = re.findall(r"<loc>(.*?)</loc>", sm)
check(len(locs) > 700, f"sitemap has {len(locs)} URLs")
check(all(u.startswith("https://resepifesbuk.com") for u in locs), "all sitemap URLs use production domain")
check(sum(1 for u in locs if "/resepi/" in u) >= 700, "sitemap covers 700+ recipes")

print("\n=== 404 handling ===")
st, _ = get("/this-page-does-not-exist-xyz/")
check(st == 404, f"unknown path returns 404 (got {st})")

print("\n" + "=" * 50)
if fails:
    print(f"FAILED: {len(fails)} check(s)")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("ALL LIVE CHECKS PASSED")
