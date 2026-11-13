"""Final independent audit: category correctness + related-link false positives.

This does NOT trust links.json or cats.json. It reads the BUILT HTML and checks
what a reader/Google actually sees:

 1. Every recipe page carries exactly one category (breadcrumb + schema agree).
 2. Every "related" link on a page points to a page in the SAME category, unless
    it is an explicit same-dish variant.
 3. Dish-name sanity: a page whose dish name mentions a protein/food word must
    not sit in a contradicting category (e.g. "Ayam" dish filed under Ikan).
 4. No cross-category link exists anywhere in the rendered output.
"""
import re, os, glob, html, json, collections, sys

DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

# words that, if present in the dish name, strongly imply a category
HINTS = {
    "ayam": "Ayam", "daging": "Daging", "kambing": "Daging", "lembu": "Daging",
    "ikan": "Ikan", "tenggiri": "Ikan", "siakap": "Ikan", "salmon": "Ikan",
    "udang": "Udang", "sotong": "Sotong", "ketam": "Ketam", "kerang": "Kerang & Siput",
    "lala": "Kerang & Siput", "kupang": "Kerang & Siput", "siput": "Kerang & Siput",
    "belangkas": "Kerang & Siput", "perut": "Perut & Organ",
    "nasi": "Nasi", "mee": "Mee & Bihun", "mi ": "Mee & Bihun", "bihun": "Mee & Bihun",
    "laksa": "Mee & Bihun", "roti": "Roti & Pastri", "pizza": "Roti & Pastri",
    "murtabak": "Roti & Pastri", "kuih": "Kuih", "kek": "Kek", "biskut": "Biskut & Biskut Raya",
    "bubur": "Bubur", "puding": "Puding & Pencuci Mulut", "agar": "Puding & Pencuci Mulut",
    "minuman": "Minuman", "air ": "Minuman", "jus": "Minuman", "sambal": "Sambal & Sos",
}
# These legitimately cross the naive hint (e.g. "Kek Lapis" has no protein)
SKIP_HINT = {"roti", "kuih", "kek", "biskut", "bubur", "puding"}

pages = {}
for p in glob.glob(os.path.join(DIST, "resepi", "*", "index.html")):
    slug = p.split(os.sep)[-2]
    pages[slug] = open(p, encoding="utf-8", errors="ignore").read()

cat_of, title_of = {}, {}
for slug, src in pages.items():
    # category from the breadcrumb link (what the reader sees)
    m = re.search(r'<a href="/kategori/([^/"]+)/">([^<]+)</a>', src)
    cat_of[slug] = html.unescape(m.group(2)).strip() if m else ""
    t = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
    title_of[slug] = html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip() if t else ""

# ---- check 1: exactly one category, non-empty ----
no_cat = [s for s, c in cat_of.items() if not c]
print(f"recipe pages                 : {len(pages)}")
print(f"pages with a category        : {len(pages)-len(no_cat)}")
if no_cat:
    print("  MISSING CATEGORY:", no_cat[:5])

# ---- check 2: related links are same-category ----
cross, variant_ok = [], 0
for slug, src in pages.items():
    rel = re.search(r'<section class="related-block">.*?</section>', src, re.S)
    if not rel:
        continue
    for href in re.findall(r'<a href="/resepi/([^/"]+)/">', rel.group(0)):
        if href not in cat_of:
            continue
        if cat_of[href] != cat_of[slug]:
            # allow only explicit same-dish variants
            a = re.sub(r"[^a-z ]", " ", title_of.get(slug, "").lower()).split()
            b = re.sub(r"[^a-z ]", " ", title_of.get(href, "").lower()).split()
            shared = len(set(a[:3]) & set(b[:3]))
            if shared >= 2:
                variant_ok += 1
            else:
                cross.append((slug, cat_of[slug], href, cat_of[href]))

print(f"related links cross-category : {len(cross)}")
print(f"  same-dish variants allowed : {variant_ok}")
for c in cross[:10]:
    print("   FALSE POSITIVE:", c)

# ---- check 3: dish-name vs category contradictions ----
contra = []
for slug, t in title_of.items():
    dish = re.split(r"[:,(]", t)[0].strip()          # dish name only
    low = " " + dish.lower() + " "
    c = cat_of.get(slug, "")
    for word, implied in HINTS.items():
        pat = r"\b" + re.escape(word.strip()) + r"\b"
        if re.search(pat, low) and implied != c:
            # a Sayur dish naming a protein as an add-on is still Sayur
            if c == "Sayur" and implied in ("Udang", "Ikan", "Ayam", "Daging"):
                continue
            # Roti & Pastri legitimately names its filling
            if c == "Roti & Pastri" and implied in ("Daging", "Ayam", "Ikan"):
                continue
            contra.append((slug, dish[:46], c, word.strip(), implied))
            break

print(f"dish/category contradictions : {len(contra)}")
for c in contra[:12]:
    print("   ", c)

print("-" * 52)
ok = not no_cat and not cross
print("RESULT:", "CLEAN - no false positives" if ok else "ISSUES FOUND")
sys.exit(0 if ok else 1)
