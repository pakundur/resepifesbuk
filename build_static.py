"""Static site generator for Resepi Fesbuk.

Emits real .html files (no SPA, no client-side routing) so every URL is
indexable and returns HTTP 200 with full content. Images stay hosted on
blogger.googleusercontent.com per requirement.

Output layout (Cloudflare Pages friendly):
  dist/index.html
  dist/resepi/<slug>/index.html
  dist/kategori/<slug>/index.html
  dist/kategori/index.html
  dist/halaman/<n>/index.html
  dist/resepi/index.html
  dist/sitemap.xml, robots.txt, feed.xml, 404.html
  dist/style.css, dist/fonts/*
"""
import json, os, re, html, shutil, hashlib, datetime
from urllib.parse import quote

from share import share_html

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
DIST = os.path.join(ROOT, "dist")
STATIC = os.path.join(ROOT, "static")

SITE_URL = "https://resepifesbuk.com"
SITE_NAME = "Resepi Fesbuk"
SITE_TAGLINE = "Koleksi Resepi Malaysia"
SITE_DESC = ("Koleksi 748 resepi Malaysia yang mudah diikuti. Ada nasi, mee, lauk, kuih, "
             "kek dan minuman. Langkah bergambar, bahan lengkap, tips masakan.")
PER_PAGE = 24

TODAY = datetime.date.today().isoformat()

recipes = json.load(open(SRC))

# ---- LLM rewrite layer (optional; falls back to source copy) ----
# src/rewrite.json is produced by rewrite.py: {slug: {headline, meta_desc,
# intro, steps}}. Missing slugs keep their original copy so a partial run
# still builds a complete site.
RW_PATH = os.path.join(ROOT, "src", "rewrite.json")
REWRITE = json.load(open(RW_PATH, encoding="utf-8")) if os.path.exists(RW_PATH) else {}
REWRITE = {k: v for k, v in REWRITE.items() if "error" not in v}

# ---- single-category assignment (LLM, from dish identity) ----
# src/cats.json is produced by classify.py: {slug: {cat, dish, conf}}. Exactly
# ONE category per recipe. It overrides the Blogger labels, which were dirty
# (Pulut Mangga was filed under Nasi; Pizza Kuali under Daging).
CATS_PATH = os.path.join(ROOT, "src", "cats.json")
CAT_OF = json.load(open(CATS_PATH, encoding="utf-8")) if os.path.exists(CATS_PATH) else {}

# ---- LLM content repair (ingredient/step split + tips) ----
# src/content_fix.json is produced by fix_content.py. It supersedes the parsed
# ingredients/steps/tips wherever the parser had leaked method text into the
# ingredient list, or the ingredient list into the steps, or tips were missing.
FIX_PATH = os.path.join(ROOT, "src", "content_fix.json")
CONTENT_FIX = json.load(open(FIX_PATH, encoding="utf-8")) if os.path.exists(FIX_PATH) else {}
CONTENT_FIX = {k: v for k, v in CONTENT_FIX.items() if "error" not in v}

# ---- internal link graph ----
LINKS_PATH = os.path.join(ROOT, "src", "links.json")
LINKS = json.load(open(LINKS_PATH, encoding="utf-8")) if os.path.exists(LINKS_PATH) else {}
BY_SLUG = {r["slug"]: r for r in recipes}

# ---- category page copy (unique per category, not boilerplate) ----
CAT_COPY_PATH = os.path.join(ROOT, "src", "cat_copy.json")
CAT_COPY = json.load(open(CAT_COPY_PATH, encoding="utf-8")) if os.path.exists(CAT_COPY_PATH) else {}

print(f"rewrites loaded: {len(REWRITE)}/{len(recipes)}")
print(f"link graph loaded: {len(LINKS)} pages")
print(f"category copy loaded: {len(CAT_COPY)}")
print(f"content repairs loaded: {len(CONTENT_FIX)}")
_missing_cat = [r["slug"] for r in recipes if not (CAT_OF.get(r["slug"]) or {}).get("cat")]
print(f"single-category assignments: {len(recipes)-len(_missing_cat)}/{len(recipes)}")


# ---------------------------------------------------------------- helpers
def esc(s):
    return html.escape(str(s), quote=True)


def slugify(s):
    s = str(s).lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s).strip("-")
    return s or "lain"


def cat_slug(c):
    return slugify(c)


def clean_meta(s, n=158):
    """Meta description: strip hashtags/emoji noise, trim to ~158 chars at a word.

    Budgets against the ESCAPED length, because entities like &amp; and &#x27;
    expand after html.escape and can push an otherwise-valid string past the
    ~165-char practical limit search engines display.
    """
    s = re.sub(r"#\w+", "", s or "")
    s = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", s)
    # neutralise quotes/apostrophes that balloon into entities
    s = s.replace('"', "'").replace("\u201c", "'").replace("\u201d", "'")
    s = re.sub(r"\s+", " ", s).strip()
    if len(html.escape(s)) <= n:
        return s
    # trim word by word until the escaped form fits
    words = s.split(" ")
    while words and len(html.escape(" ".join(words) + "…")) > n:
        words.pop()
    return " ".join(words).rstrip(",.;:") + "…"


def fit_title(s, lo=30, hi=60, suffix=" | Resepi Fesbuk"):
    """Clamp a <title> into Google's 30-60 char band.

    Google truncates around 60 chars on desktop and rewrites longer titles,
    losing the message we wrote. The brand suffix is the first thing to drop
    because Google appends/recognises the site name anyway.
    """
    s = re.sub(r"\s+", " ", s or "").strip()
    if len(s) <= hi and len(s) >= lo:
        return s
    if len(s) > hi:
        # drop the brand suffix first
        if s.endswith(suffix):
            core = s[: -len(suffix)]
            if lo <= len(core) <= hi:
                return core
            s = core
        if len(s) > hi:
            words = s.split(" ")
            while words and len(" ".join(words)) > hi:
                words.pop()
            s = " ".join(words).rstrip(" ,.;:-")
            if s.lower().endswith(" resid"):        # never end mid-word
                s = s[: s.rfind(" ")].rstrip(" ,.;:-")
    if len(s) < lo:
        pad = " | Resepi Fesbuk"
        if not s.endswith(pad) and len(s + pad) <= hi:
            s = s + pad
    return s


def fit_desc(s, lo=120, hi=158):
    """Clamp a meta description into 120-158 chars, ending on a full sentence."""
    s = clean_meta(re.sub(r"#\w+", "", s or ""), hi).strip()
    if len(s) < lo:
        extra = (" Koleksi resepi Malaysia dengan bahan penuh, "
                 "langkah penyediaan jelas dan tips berguna.")
        while len(s) < lo and extra:
            s = (s.rstrip() + extra).strip()
            extra = extra[:-1] if len(s) > hi else ""
            if len(s) > hi:
                s = clean_meta(s, hi)
                break
    return s


def scrub(s, keep_period=False):
    """Remove auto-blog boilerplate and AI tells from any body string.

    The legacy Blogger posts ended with "Selamat mencuba..", "Jangan lupa
    share..", hashtag strings and em dashes, and some of that landed inside
    ingredient lists rather than the tips. Cleaning at render time catches
    every field at once instead of patching each one separately.
    """
    orig = s
    s = str(s or "")
    s = re.sub(r"#[\w\u00C0-\u024F]{2,}", " ", s)          # hashtags
    s = re.sub(r"(?i)\bselamat\s+mencuba+\w*\b[!.]*", " ", s)
    s = re.sub(r"(?i)\b(tak\s+rugi\s+tau+|janji\s+sodap+)\w*\b[.!]*", " ", s)
    s = re.sub(r"(?i)\bjangan\s+lupa\s+(share|kongsi)\w*\b[.!]*", " ", s)
    s = re.sub(r"(?i)\bpasti\s+menjadi\s+rebutan\b[^.]*\.?", " ", s)
    s = re.sub(r"(?i)\bhashtags?\s*:.*$", " ", s)
    s = re.sub(r"[—–]", ", ", s)
    s = re.sub(r"\s*\.\s*\.+\s*$", "", s)                 # trailing dot runs
    s = re.sub(r"\s+", " ", s).strip(" ,;:-")
    # keep a single terminal period if the original had one -- tips read as
    # sentences, and stripping the full stop leaves them dangling.
    if keep_period and s and not s.endswith((".", "!", "?")) and re.search(r"[.!?]\s*$", str(orig or "")):
        s += "."
    return s


def iso_date(s):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s or "")
    return m.group(0) if m else TODAY


def derive_time(steps):
    """Sum only durations the recipe actually states. Returns ISO-8601 or None.

    Google treats prepTime/cookTime as optional. Inventing a fixed "PT15M" for
    a rendang and a salad alike is inaccurate markup, so we publish a duration
    only when the source text gives one. Multiple mentions are summed, capped at
    12 hours to ignore obvious outliers.
    """
    txt = " ".join(str(s.get("t", "")) if isinstance(s, dict) else str(s) for s in steps)
    total = 0
    for n, unit in re.findall(r"(\d{1,3})\s*(minit|min|jam|hour|hrs?)\b", txt, re.I):
        v = int(n)
        total += v * 60 if unit.lower().startswith(("jam", "hour", "hr")) else v
    if total <= 0 or total > 720:
        return None
    h, m = divmod(total, 60)
    return f"PT{h}H{m}M" if h and m else (f"PT{h}H" if h else f"PT{m}M")


def headline_of(r):
    """The one headline used everywhere: rewritten copy when available."""
    return (REWRITE.get(r["slug"]) or {}).get("headline") or r["title"]


def alt_text(r):
    """Descriptive, non-duplicative alt text.

    Repeating <title> verbatim as alt adds nothing for screen readers or image
    search. Compose "<dish> - <category> Malaysia" from the clean headline so
    the alt describes the photo's subject without echoing the page title.
    """
    h = (REWRITE.get(r["slug"]) or {}).get("headline") or r["title"]
    dish = re.split(r"[:,(]", h)[0].strip()
    dish = re.sub(r"\s*[-–—]\s*Resepi Mudah.*$", "", dish, flags=re.I)
    cat = r.get("cat1") or ""
    alt = f"{dish}, resepi {cat} Malaysia" if cat else dish
    return re.sub(r"\s+", " ", alt).strip()[:125]


IMG_BASE = "https://resepifesbuk.com/img"

# Cloudflare Web Analytics — free, cookie-free, real-user Core Web Vitals.
# Injected once via footer_html() so it lands on every generated page.
CF_ANALYTICS = (
    "<script defer src='https://static.cloudflareinsights.com/beacon.min.js' "
    "data-cf-beacon='{\"token\": \"fee36023b04d44c1812b25ad01f3787d\"}'></script>"
)

# Google Analytics 4 — standard (free) property.
# SET THIS to your Measurement ID from GA4 > Admin > Data Streams > your web stream.
# Format: G-XXXXXXXXXX. Left empty = no GA4 tag emitted (build stays green).
GA4_ID = os.environ.get("GA4_ID", "").strip()

GA4_HTML = ""
if GA4_ID:
    GA4_HTML = (
        f"<script async src='https://www.googletagmanager.com/gtag/js?id={GA4_ID}'></script>"
        "<script>window.dataLayer=window.dataLayer||[];"
        "function gtag(){dataLayer.push(arguments);}"
        "gtag('js',new Date());"
        f"gtag('config','{GA4_ID}');</script>"
    )

# slug -> R2 object key (SEO filename). Produced by mk_imgmap.py.
IMG_KEY_OF = {}
_img_map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img_map.json")
if os.path.exists(_img_map_path):
    for _e in json.load(open(_img_map_path)):
        IMG_KEY_OF[_e["slug"]] = _e["key"]


def thumb(url, w=600):
    """Blogger CDN size param -> width variant for cards (legacy path)."""
    if not url:
        return ""
    return re.sub(r"/s\d+(-c)?/", f"/w{w}-h{w*0.75:.0f}-c/", url)


def big(url):
    if not url:
        return ""
    return re.sub(r"/s\d+(-c)?/", "/s1600/", url)


def img_url(r):
    """R2-hosted image URL for a recipe (fallback: original source URL)."""
    key = r.get("r2_key") or IMG_KEY_OF.get(r.get("slug"))
    if key:
        return f"{IMG_BASE}/{key}"
    return big(r.get("img") or "")


# normalise recipe fields
for r in recipes:
    r["published_d"] = iso_date(r.get("published"))
    r["updated_d"] = iso_date(r.get("updated")) or r["published_d"]
    llm_cat = (CAT_OF.get(r["slug"]) or {}).get("cat")
    r["cat1"] = llm_cat or (r["cats"][0] if r["cats"] else "Lain-lain")
    r["cats"] = [r["cat1"]]          # single category, everywhere
    r["cat_slug"] = cat_slug(r["cat1"])
    r["r2_key"] = IMG_KEY_OF.get(r["slug"]) or None
    if not r.get("intro"):
        r["intro"] = clean_meta(
            "Resepi " + re.sub(r"^Resepi\s+", "", r["title"], flags=re.I)
            + ". Bahan-bahan lengkap dan cara penyediaan langkah demi langkah.", 240)
    r["meta_desc"] = clean_meta(r["intro"], 158)
    # apply the LLM content repair: clean ingredient/step split + guaranteed tips
    _fx = CONTENT_FIX.get(r["slug"])
    if _fx:
        if _fx.get("ingredients"):
            r["ingredients"] = _fx["ingredients"]
        if len(_fx.get("steps") or []) >= 2:
            r["steps"] = [{"t": s} for s in _fx["steps"]]
        if _fx.get("tips"):
            r["tips"] = _fx["tips"]
        # counts must follow the repaired lists, or the cards and schema lie
        r["n_ing"] = len(r["ingredients"])
        r["n_steps"] = len([s for s in r["steps"] if s.get("t")])

recipes.sort(key=lambda x: (x["published_d"], x["title"]), reverse=True)

# category index
CATS = {}
for r in recipes:
    CATS.setdefault(r["cat1"], []).append(r)
CATS = dict(sorted(CATS.items(), key=lambda kv: -len(kv[1])))


# ---------------------------------------------------------------- css hash
css_path = os.path.join(STATIC, "style.css")
css = open(css_path, encoding="utf-8").read()
CSS_HASH = hashlib.sha256(css.encode()).hexdigest()[:10]


# ---------------------------------------------------------------- templates
def head(title, desc, canonical, og_type="website", og_img="", published=None,
         updated=None, extra_ld=None, is_recipe=False, prev_url=None, next_url=None):
    """Complete <head> with canonical, OG, Twitter, geo, and JSON-LD."""
    img = og_img or f"{SITE_URL}/og-default.jpg"
    title = fit_title(title)
    desc = fit_desc(desc)
    ld = ""

    # WebSite (+ SearchAction) on every page
    website_ld = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "alternateName": "Resepi Fesbuk Malaysia",
        "url": SITE_URL,
        "inLanguage": "ms-MY",
        "description": SITE_DESC,
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL,
                      "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/icon-512.png"}},
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint",
                       "urlTemplate": f"{SITE_URL}/cari/?q={{search_term_string}}"},
            "query-input": "required name=search_term_string",
        },
    }
    # Organization as its own object: Google reads this for the logo and for
    # publisher attribution. Nesting it inside WebSite is legal but weaker.
    org_ld = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{SITE_URL}/#organization",
        "name": SITE_NAME,
        "alternateName": "Resepi Fesbuk Malaysia",
        "url": SITE_URL,
        "logo": {
            "@type": "ImageObject",
            "url": f"{SITE_URL}/icon-512.png",
            "width": 512,
            "height": 512,
        },
        "description": SITE_DESC,
        "foundingLocation": {"@type": "Place", "name": "Malaysia"},
        "knowsLanguage": "ms-MY",
    }
    # Emit each schema object in its OWN <script> block. Concatenating them into
    # one block produces invalid JSON (multiple root objects) and Google then
    # discards ALL structured data on the page.
    ld_objs = [website_ld, org_ld]
    if extra_ld:
        ld_objs += (extra_ld if isinstance(extra_ld, list) else [extra_ld])
    ld = "\n".join(
        '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"
        for obj in ld_objs if obj
    )

    robots = "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
    return f"""<!doctype html>
<html lang="ms-MY" prefix="og: https://ogp.me/ns#">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<meta name="googlebot" content="{robots}">
<link rel="canonical" href="{esc(canonical)}">
<link rel="alternate" hreflang="ms-MY" href="{esc(canonical)}">
<link rel="alternate" hreflang="x-default" href="{esc(canonical)}">

<!-- Geo -->
<meta name="geo.region" content="MY">
<meta name="geo.placename" content="Malaysia">
<meta name="language" content="Malay">
<meta name="author" content="{SITE_NAME}">

<!-- Open Graph -->
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:locale" content="ms_MY">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(img)}">
<meta property="og:image:alt" content="{esc(title)}">
{"<meta property='article:published_time' content='" + published + "'>" if published else ""}
{"<meta property='article:modified_time' content='" + updated + "'>" if updated else ""}

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="twitter:image" content="{esc(img)}">

<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="/style.css?v={CSS_HASH}">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME} RSS" href="{SITE_URL}/feed.xml">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icon-512.png">

{ld}
</head>
<body>
"""


def header_html():
    return f"""<header class="site-header">
  <div class="wrap">
    <a class="brand" href="/">{SITE_NAME.split()[0]} <em>{SITE_NAME.split()[1]}</em></a>
    <nav class="site-nav" aria-label="Navigasi utama">
      <a href="/resepi/">Semua Resepi</a>
      <a href="/kategori/">Kategori</a>
      <a href="/cari/" class="hide-sm">Cari</a>
      <a href="/tentang/" class="hide-sm">Tentang</a>
    </nav>
  </div>
</header>
"""


def footer_html():
    top_cats = list(CATS.items())[:8]
    cat_links = "\n".join(
        f'        <li><a href="/kategori/{cat_slug(c)}/">{esc(c)}</a> <span style="color:var(--ink-mute);font-size:.8em">({len(v)})</span></li>'
        for c, v in top_cats)
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <h4>Tentang {SITE_NAME}</h4>
        <p class="footer-about">{SITE_DESC}</p>
      </div>
      <div>
        <h4>Kategori Popular</h4>
        <ul>
{cat_links}
        </ul>
      </div>
      <div>
        <h4>Pautan</h4>
        <ul>
          <li><a href="/resepi/">Semua Resepi</a></li>
          <li><a href="/kategori/">Semua Kategori</a></li>
          <li><a href="/cari/">Cari Resepi</a></li>
          <li><a href="/tentang/">Tentang Kami</a></li>
          <li><a href="/feed.xml">RSS Feed</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-base">
      <span>&copy; {datetime.date.today().year} {SITE_NAME}. Hak cipta terpelihara.</span>
      <span>Resepi Malaysia untuk semua.</span>
    </div>
  </div>
</footer>
{CF_ANALYTICS}
{GA4_HTML}
"""


def card(r, eager=False):
    ing = r["n_ing"]
    stp = r["n_steps"]
    meta_bits = []
    if ing:
        meta_bits.append(f"{ing} bahan")
    if stp:
        meta_bits.append(f"{stp} langkah")
    meta = " &middot; ".join(meta_bits)
    loading = "" if eager else ' loading="lazy"'
    fetch = ' fetchpriority="high"' if eager else ""
    return f"""<a class="rcard" href="/resepi/{r['slug']}/">
  <div class="rcard-img">
    <img src="{esc(img_url(r))}" alt="{esc(alt_text(r))}" width="600" height="450"{loading}{fetch} decoding="async">
  </div>
  <div class="rcard-body">
    <span class="rcard-cat">{esc(r['cat1'])}</span>
    <h3>{esc(headline_of(r))}</h3>
    <p>{esc(clean_meta(r['intro'], 120))}</p>
    <div class="rcard-foot">{meta}</div>
  </div>
</a>"""


def write(path, content):
    full = os.path.join(DIST, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------------- pages
# Wipe dist first: renamed/removed categories used to leave orphan page
# directories behind, which then got deployed as duplicate thin pages.
if os.path.isdir(DIST):
    shutil.rmtree(DIST)
os.makedirs(DIST, exist_ok=True)

# ---- home ----
home_cards = "\n".join(card(r, eager=(i < 3)) for i, r in enumerate(recipes[:12]))
cat_tiles = "\n".join(
    f'<a class="cat-card" href="/kategori/{cat_slug(c)}/"><span>{esc(c)}</span><span class="n">{len(v)}</span></a>'
    for c, v in CATS.items())

home_ld = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "name": f"{SITE_NAME}: {SITE_TAGLINE}",
    "url": SITE_URL + "/",
    "description": SITE_DESC,
    "inLanguage": "ms-MY",
    "isPartOf": {"@type": "WebSite", "url": SITE_URL},
    "about": {"@type": "Thing", "name": "Resepi masakan Malaysia"},
    "mainEntity": {
        "@type": "ItemList",
        "numberOfItems": len(recipes),
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1,
             "url": f"{SITE_URL}/resepi/{r['slug']}/", "name": r["title"]}
            for i, r in enumerate(recipes[:12])
        ],
    },
}

write("index.html", head(
    f"{SITE_NAME}: {SITE_TAGLINE} | 748 Resepi Mudah & Sedap",
    f"Koleksi {len(recipes)} resepi Malaysia: nasi, mee, lauk, kuih, kek & minuman. "
    f"Bahan lengkap, langkah bergambar dan tips masakan untuk semua peringkat.",
    SITE_URL + "/", og_img=img_url(recipes[0]), extra_ld=home_ld) + header_html() + f"""
<main>
  <section class="hero sky-field">
    <div class="wrap">
      <span class="eyebrow">{len(recipes)} Resepi &middot; {len(CATS)} Kategori</span>
      <h1 class="display">Masak <em>sedap</em><br>setiap hari.</h1>
      <p class="lede">Resepi Malaysia yang sudah dicuba ramai. Bahan senang cari, langkah jelas, dan tips yang benar-benar membantu.</p>
      <div class="search-box">
        <input type="search" id="q" placeholder="Cari resepi… (cth: nasi goreng, kuih, ayam)" aria-label="Cari resepi">
      </div>
      <div class="hero-meta">Tekan Enter untuk cari</div>
    </div>
  </section>

  <section style="padding-top:20px">
    <div class="wrap">
      <div class="center" style="margin-bottom:34px">
        <span class="eyebrow">Terus ke kategori</span>
      </div>
      <div class="cat-grid">
{cat_tiles}
      </div>
    </div>
  </section>

  <section style="background:var(--cream-deep)">
    <div class="wrap">
      <div style="display:flex;justify-content:space-between;align-items:flex-end;gap:20px;flex-wrap:wrap;margin-bottom:34px">
        <div>
          <span class="eyebrow">Terbaru</span>
          <h2 class="mt-0">Resepi pilihan</h2>
        </div>
        <a href="/resepi/" style="font-weight:500;font-size:.92rem">Lihat semua {len(recipes)} resepi &rarr;</a>
      </div>
      <div class="grid">
{home_cards}
      </div>
    </div>
  </section>
</main>
""" + footer_html() + "<script>document.getElementById('q').addEventListener('keydown',function(e){if(e.key==='Enter'){var v=this.value.trim();if(v)location.href='/cari/?q='+encodeURIComponent(v);}});</script>\n</body>\n</html>\n")

print("home ok")


# ---- recipe detail pages ----
RECIPE_URLS = []

for idx, r in enumerate(recipes):
    url = f"/resepi/{r['slug']}/"
    canon = SITE_URL + url
    RECIPE_URLS.append((canon, r["updated_d"], r["title"]))

    # ---- apply LLM rewrite if present ----
    rw = REWRITE.get(r["slug"])
    headline = rw["headline"] if rw else r["title"]
    meta_desc = rw["meta_desc"] if rw else r["meta_desc"]
    intro_txt = scrub(rw["intro"] if rw else r["intro"])

    # rewritten steps replace the parsed ones when the LLM produced a usable list
    page_steps = r["steps"]
    if rw and len(rw.get("steps", [])) >= 2:
        page_steps = [{"t": s} for s in rw["steps"]]

    # ingredients
    if r["ingredients"]:
        _ings = [x for x in (scrub(i) for i in r["ingredients"]) if len(x) >= 2]
        ing_html = "\n".join(f"<li>{esc(i)}</li>" for i in _ings)
        ing_block = f"""<aside class="ing-box">
  <h2>Bahan-bahan</h2>
  <ul>{ing_html}</ul>
</aside>"""
    else:
        ing_block = '<aside class="ing-box"><h2>Bahan-bahan</h2><p style="font-size:.9rem;color:var(--ink-mute)">Lihat penerangan penuh di bawah.</p></aside>'

    # steps
    step_items = []
    n = 0
    for s in page_steps:
        if "h" in s:
            step_items.append(f'<li><span class="substep">{esc(scrub(s["h"]))}</span></li>')
        else:
            n += 1
            _t = scrub(s["t"])
            if _t:
                step_items.append(f"<li>{esc(_t)}</li>")
    steps_html = "\n".join(step_items) if step_items else "<li>Lihat nota penyediaan di bawah.</li>"

    tips_html = ""
    # Scrub Blogger boilerplate out of tips: hashtag strings, "Selamat mencuba",
    # and the sign-off sentences that were pasted at the end of every post.
    # These are AI/auto-blog tells and they were never cleaned in the base data.
    _tips = []
    for t in r["tips"]:
        t = scrub(t, keep_period=True)
        if len(t) >= 25:
            _tips.append(t)
    if _tips:
        tl = "\n".join(f"<li>{esc(t)}</li>" for t in _tips)
        tips_html = f"""<div class="tips-box">
  <h2>Tips Masakan</h2>
  <ul>{tl}</ul>
</div>"""

    # breadcrumb — ends at category; post title intentionally excluded
    bc_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Utama", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "Resepi", "item": SITE_URL + "/resepi/"},
            {"@type": "ListItem", "position": 3, "name": r["cat1"], "item": f"{SITE_URL}/kategori/{r['cat_slug']}/"},
        ],
    }

    # Recipe schema — the big SEO/rich-result win
    recipe_ld = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": headline,
        "headline": headline[:110],
        "description": meta_desc,
        "url": canon,
        "image": [img_url(r)],
        "author": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
        "publisher": {"@type": "Organization", "name": SITE_NAME,
                      "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/icon-512.png"}},
        "datePublished": r["published_d"],
        "dateModified": r["updated_d"],
        "inLanguage": "ms-MY",
        "recipeCategory": r["cat1"],
        "recipeCuisine": "Malaysian",
        "keywords": ", ".join([r["cat1"], "resepi Malaysia", "masakan Malaysia"]),
    }
    # only publish a duration when the recipe states one (no fabricated times)
    _t = derive_time(page_steps)
    if _t:
        recipe_ld["totalTime"] = _t
    if r["ingredients"]:
        recipe_ld["recipeIngredient"] = r["ingredients"][:60]
    plain_steps = [s["t"] for s in page_steps if "t" in s]
    if plain_steps:
        recipe_ld["recipeInstructions"] = [
            {"@type": "HowToStep", "position": i + 1, "text": t}
            for i, t in enumerate(plain_steps[:40])
        ]
    if r["n_ing"] and len(plain_steps) >= 2:
        agg = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": headline[:110],
            "description": meta_desc,
            "datePublished": r["published_d"],
            "dateModified": r["updated_d"],
            "author": {"@type": "Organization", "name": SITE_NAME},
            "publisher": {"@type": "Organization", "name": SITE_NAME,
                          "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/icon-512.png"}},
            "mainEntityOfPage": {"@type": "WebPage", "@id": canon},
            "image": [img_url(r)],
        }
    else:
        agg = None

    lds = [bc_ld, recipe_ld] + ([agg] if agg else [])

    facts = []
    if r["n_ing"]:
        facts.append(f"{r['n_ing']} bahan")
    if r["n_steps"]:
        facts.append(f"{r['n_steps']} langkah")
    facts.append(f"{r['cat1']}")
    facts_html = "".join(f'<span class="fact">{esc(f)}</span>' for f in facts)

    page = head(
        f"{headline} | {SITE_NAME}",
        meta_desc,
        canon,
        og_type="article",
        og_img=img_url(r),
        published=r["published_d"] + "T00:00:00+08:00",
        updated=r["updated_d"] + "T00:00:00+08:00",
        extra_ld=lds,
        is_recipe=True,
    )
    page += header_html()
    # related links (internal link graph) — rendered before footer so the
    # crawl path sits inside the article body, not in boilerplate
    rel = LINKS.get(r["slug"], [])
    rel_html = ""
    if rel:
        items = "\n".join(
            f'<li><a href="/resepi/{esc(l["slug"])}/">{esc(l["anchor"])}</a></li>'
            for l in rel if l["slug"] in BY_SLUG
        )
        rel_html = f"""<section class="related-block">
  <h2>Resepi lain yang anda boleh cuba</h2>
  <ul class="related-list">{items}</ul>
</section>"""

    page += f"""<main>
<article>
  <div class="wrap-narrow recipe-head">
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="/">Utama</a><span aria-hidden="true">/</span>
      <a href="/resepi/">Resepi</a><span aria-hidden="true">/</span>
      <span aria-current="page">{esc(r['cat1'])}</span>
    </nav>

    <h1 class="display">{esc(headline)}</h1>
    <div class="recipe-facts">{facts_html}</div>

    <img class="recipe-hero-img" src="{esc(img_url(r))}" alt="{esc(alt_text(r))}" width="1200" height="800" fetchpriority="high" decoding="async">
  </div>

  <div class="wrap-narrow">
    <p class="recipe-intro">{esc(intro_txt)}</p>
    {share_html(headline, canon)}

    <div class="recipe-cols">
      {ing_block}
      <div>
        <h2> Cara Penyediaan</h2>
        <ol class="steps">
          {steps_html}
        </ol>
        {tips_html}
      </div>
    </div>

    <div class="source-note">
      <p>Resepi ini diterbitkan untuk pembaca {SITE_NAME}. Kalau ia berhasil di dapur anda, kongsikan dengan keluarga dan rakan.</p>
    </div>
    {rel_html}
  </div>
</article>
</main>
"""
    page += footer_html()
    page += "</body>\n</html>\n"
    write(f"resepi/{r['slug']}/index.html", page)

print(f"recipe pages ok: {len(recipes)}")


# ---- recipe index (paginated) ----
total_pages = (len(recipes) + PER_PAGE - 1) // PER_PAGE
for p in range(1, total_pages + 1):
    chunk = recipes[(p - 1) * PER_PAGE: p * PER_PAGE]
    cards = "\n".join(card(r) for r in chunk)
    canon = f"{SITE_URL}/halaman/{p}/" if p > 1 else f"{SITE_URL}/resepi/"
    title = f"Semua Resepi, Halaman {p} daripada {total_pages}" if p > 1 else f"Semua Resepi ({len(recipes)})"
    ld = {"@context": "https://schema.org", "@type": "CollectionPage",
          "name": title, "url": canon, "inLanguage": "ms-MY",
          "isPartOf": {"@type": "WebSite", "url": SITE_URL}}
    prev_link = ""
    next_link = ""
    if p > 1:
        prev_link = f'<link rel="prev" href="{SITE_URL}/halaman/{p-1}/">' if p > 2 else f'<link rel="prev" href="{SITE_URL}/resepi/">'
    if p < total_pages:
        next_link = f'<link rel="next" href="{SITE_URL}/halaman/{p+1}/">'

    # pager
    pg = []
    if p > 1:
        prev_href = "/resepi/" if p == 2 else f"/halaman/{p-1}/"
        pg.append(f'<a href="{prev_href}">&larr; Sebelum</a>')
    for i in range(1, total_pages + 1):
        if i == p:
            pg.append(f'<span class="current" aria-current="page">{i}</span>')
        elif i <= 2 or i > total_pages - 2 or abs(i - p) <= 1:
            href = "/resepi/" if i == 1 else f"/halaman/{i}/"
            pg.append(f'<a href="{href}">{i}</a>')
        elif abs(i - p) == 2:
            pg.append('<span class="gap">…</span>')
    if p < total_pages:
        pg.append(f'<a href="/halaman/{p+1}/">Seterusnya &rarr;</a>')
    pager = f'<nav class="pager" aria-label="Navigasi halaman">{"".join(pg)}</nav>'

    page = head(title + f" | {SITE_NAME}",
                f"Halaman {p} daripada {total_pages} senarai lengkap {len(recipes)} resepi "
                f"Malaysia, bahan penuh dan cara penyediaan langkah demi langkah. Halaman ini "
                f"himpun resepi untuk semua selera, dari menu harian sampai juadah majlis.",
                canon, og_img=img_url(chunk[0]) if chunk else "", extra_ld=ld)
    page = page.replace("</head>", prev_link + next_link + "\n</head>") if (prev_link or next_link) else page
    page += header_html() + f"""<main>
<section style="padding-bottom:30px">
  <div class="wrap">
    <span class="eyebrow">Koleksi Lengkap</span>
    <h1 class="display">Semua <em>resepi</em></h1>
    <p class="lede" style="max-width:60ch">{len(recipes)} resepi Malaysia, disusun dari yang terbaru. Halaman {p} daripada {total_pages}.</p>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <h2 class="sr-only">Senarai resepi halaman {p}</h2>
    <div class="grid">
{cards}
    </div>
    {pager}
  </div>
</section>
</main>
""" + footer_html() + "</body>\n</html>\n"

    if p == 1:
        write("resepi/index.html", page)
    else:
        write(f"halaman/{p}/index.html", page)

print(f"recipe index ok: {total_pages} pages")


# ---- category pages ----
for c, items in CATS.items():
    cs = cat_slug(c)
    canon = f"{SITE_URL}/kategori/{cs}/"
    cards = "\n".join(card(r) for r in items)
    cc = CAT_COPY.get(c, {})
    cat_title = cc.get("title") or f"Resepi {c}: {len(items)} Pilihan Mudah"
    cat_desc = cc.get("meta_desc") or (
        f"Koleksi {len(items)} resepi {c} Malaysia dengan bahan lengkap, "
        f"langkah jelas dan tips masakan.")
    cat_intro = cc.get("intro") or (
        f"Semua resepi {c} dalam koleksi {SITE_NAME}, disusun supaya senang dicari.")

    # ItemList: tells Google this page is an ordered collection of recipes and
    # which URLs belong to it. Without it a category page is just a link dump.
    _items = [{
        "@type": "ListItem",
        "position": i + 1,
        "url": f"{SITE_URL}/resepi/{r['slug']}/",
        "name": (REWRITE.get(r["slug"]) or {}).get("headline") or r["title"],
    } for i, r in enumerate(items[:60])]

    ld = [{
        "@context": "https://schema.org", "@type": "CollectionPage",
        "@id": canon + "#collection",
        "name": cat_title, "url": canon, "inLanguage": "ms-MY",
        "description": cat_desc,
        "isPartOf": {"@type": "WebSite", "url": SITE_URL},
        "numberOfItems": len(items),
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(items),
            "itemListElement": _items,
        },
    }, {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Utama", "item": SITE_URL + "/"},
            {"@type": "ListItem", "position": 2, "name": "Kategori", "item": SITE_URL + "/kategori/"},
            {"@type": "ListItem", "position": 3, "name": c, "item": canon},
        ],
    }]
    page = head(f"{cat_title} | {SITE_NAME}",
                cat_desc,
                canon, og_img=img_url(items[0]), extra_ld=ld)
    page += header_html() + f"""<main>
<section style="padding-bottom:30px">
  <div class="wrap">
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="/">Utama</a><span aria-hidden="true">/</span>
      <a href="/kategori/">Kategori</a><span aria-hidden="true">/</span>
      <span aria-current="page">{esc(c)}</span>
    </nav>
    <span class="eyebrow">{len(items)} Resepi</span>
    <h1 class="display">Resepi <em>{esc(c)}</em></h1>
    <p class="lede" style="max-width:68ch">{esc(cat_intro)}</p>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <h2 class="sr-only">Senarai resepi {esc(c)}</h2>
    <div class="grid">
{cards}
    </div>
  </div>
</section>
</main>
""" + footer_html() + "</body>\n</html>\n"
    write(f"kategori/{cs}/index.html", page)

print(f"category pages ok: {len(CATS)}")


# ---- category index ----
cat_tiles = "\n".join(
    f'<a class="cat-card" href="/kategori/{cat_slug(c)}/"><span>{esc(c)}</span><span class="n">{len(v)}</span></a>'
    for c, v in CATS.items())
page = head(f"Semua Kategori Resepi | {SITE_NAME}",
            f"{len(CATS)} kategori resepi Malaysia: nasi, mee, lauk, kuih, kek, minuman dan banyak lagi.",
            SITE_URL + "/kategori/",
            og_img=img_url(recipes[0]),
            extra_ld={"@context": "https://schema.org", "@type": "CollectionPage",
                      "name": "Kategori Resepi", "url": SITE_URL + "/kategori/",
                      "inLanguage": "ms-MY"})
page += header_html() + f"""<main>
<section>
  <div class="wrap">
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="/">Utama</a><span aria-hidden="true">/</span>
      <span aria-current="page">Kategori</span>
    </nav>
    <span class="eyebrow">{len(CATS)} Kategori</span>
    <h1 class="display">Semua <em>kategori</em></h1>
    <p class="lede" style="max-width:60ch">Pilih kategori untuk terus jumpa resepi yang anda cari.</p>
    <h2 class="sr-only">Senarai kategori resepi</h2>
    <div class="cat-grid" style="margin-top:40px">
{cat_tiles}
    </div>
  </div>
</section>
</main>
""" + footer_html() + "</body>\n</html>\n"
write("kategori/index.html", page)
print("category index ok")


# ---- search page ----
page = head(f"Cari Resepi Mengikut Bahan Atau Nama Hidangan | {SITE_NAME}",
            f"Cari dalam {len(recipes)} resepi Malaysia mengikut nama bahan atau hidangan.",
            SITE_URL + "/cari/", extra_ld={"@context": "https://schema.org", "@type": "SearchResultsPage"})
page += header_html() + f"""<main>
<section>
  <div class="wrap-narrow center">
    <h1 class="display">Cari <em>resepi</em></h1>
    <p class="lede">Taip nama hidangan atau bahan, contohnya nasi goreng, ayam atau kuih.</p>
    <div class="search-box">
      <input type="search" id="q" placeholder="Cari resepi…" aria-label="Cari resepi" autofocus>
    </div>
  </div>
</section>
<section style="padding-top:0">
  <div class="wrap">
    <h2 class="sr-only">Hasil carian</h2>
    <div id="out" class="grid"></div>
  </div>
</section>
</main>
<script>
/* Index is fetched on first keystroke, not inlined: keeping it out of the HTML
   cuts the page from 356KB to ~6KB and it is cached separately for a year. */
let IDX = null;
const inp = document.getElementById('q'), out = document.getElementById('out');
async function ensureIdx() {{
  if (IDX) return IDX;
  const r = await fetch('/search-index.json', {{ cache: 'force-cache' }});
  IDX = await r.json();
  return IDX;
}}
async function run() {{
  const q = (inp.value || '').toLowerCase().trim();
  if (!q) {{ out.innerHTML = ''; return; }}
  await ensureIdx();
  const hits = IDX.filter(x => x.t.toLowerCase().includes(q) || x.d.toLowerCase().includes(q) || x.c.toLowerCase().includes(q)).slice(0, 48);
  out.innerHTML = hits.length ? hits.map(x => `<a class="rcard" href="` + '/resepi/' + x.s + '/' + `"><div class="rcard-img"><img src="${{x.i}}" alt="${{x.t.replace(/"/g,'&quot;')}}" loading="lazy" width="600" height="450"></div><div class="rcard-body"><span class="rcard-cat">${{x.c}}</span><h3>${{x.t}}</h3><p>${{x.d}}</p></div></a>`).join('') : '<p class="empty">Tiada resepi dijumpai. Cuba kata kunci lain.</p>';
}}
const params = new URLSearchParams(location.search);
if (params.get('q')) {{ inp.value = params.get('q'); }}
inp.addEventListener('input', run); run();
</script>
{CF_ANALYTICS}
{GA4_HTML}
</body>
</html>
"""
write("cari/index.html", page)
print("search ok")


# ---- about page ----
page = head(f"Tentang {SITE_NAME} | Koleksi Resepi Malaysia",
            f"Tentang {SITE_NAME}, koleksi {len(recipes)} resepi Malaysia yang dikongsikan untuk semua pembaca.",
            SITE_URL + "/tentang/",
            extra_ld={"@context": "https://schema.org", "@type": "AboutPage",
                      "name": f"Tentang {SITE_NAME}", "url": SITE_URL + "/tentang/",
                      "inLanguage": "ms-MY"})
page += header_html() + f"""<main>
<article class="wrap-narrow" style="padding:64px 20px">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="/">Utama</a><span aria-hidden="true">/</span>
    <span aria-current="page">Tentang</span>
  </nav>
  <h1 class="display">Tentang <em>{SITE_NAME}</em></h1>
  <p class="recipe-intro">{SITE_NAME} ialah koleksi resepi Malaysia yang mudah diikuti, dari masakan harian keluarga hingga kuih tradisional. Setiap resepi disertakan senarai bahan yang jelas, langkah penyediaan demi langkah, dan tips yang membantu anda berjaya kali pertama.</p>
  <h2>Apa yang kami kongsikan</h2>
  <ul>
    <li><strong>{len(recipes)} resepi</strong> dalam {len(CATS)} kategori: nasi, mee, lauk, sayur, sup, kuih, kek, biskut dan minuman.</li>
    <li><strong>Bahan lengkap</strong> dengan sukatan yang jelas.</li>
    <li><strong>Langkah demi langkah</strong> untuk setiap hidangan.</li>
    <li><strong>Tips masakan</strong> daripada pengalaman sebenar.</li>
  </ul>
  <h2>Untuk siapa</h2>
  <p>Sesiapa yang mahu memasak di rumah: pelajar, ibu bapa sibuk, atau sesiapa yang baru berjinak dengan dapur. Resepi kami ditulis dengan bahasa yang senang difahami, tanpa andaian bahawa anda sudah berpengalaman.</p>
  <h2>Hubungi</h2>
  <p>Ada soalan atau cadangan? Kami amat menghargai maklum balas daripada pembaca.</p>
</article>
</main>
""" + footer_html() + "</body>\n</html>\n"
write("tentang/index.html", page)
print("about ok")


# ---- 404 ----
page = head(f"Halaman Tidak Dijumpai | Resepi Fesbuk",
            "Halaman yang anda cari tidak wujud atau telah dipindahkan. Kembali ke senarai "
            "resepi Malaysia kami untuk bahan penuh, langkah penyediaan dan tips memasak "
            "yang senang diikuti di rumah.",
            SITE_URL + "/404.html")
page += header_html() + f"""<main>
<section class="center" style="padding:110px 20px">
  <div class="wrap-narrow">
    <h1 class="display">404</h1>
    <p class="lede">Maaf, halaman ini tidak dijumpai.</p>
    <h2 style="font-size:1.05rem;margin:26px 0 8px">Apa yang boleh anda buat</h2>
    <p>Cuba cari hidangan yang anda mahu, atau terus ke kategori kegemaran.</p>
    <p><a href="/resepi/" style="font-weight:600">Lihat semua resepi &rarr;</a></p>
    <p style="margin-top:10px"><a href="/cari/">Cari ikut nama atau bahan &rarr;</a></p>
    <p style="margin-top:24px"><a href="/">Kembali ke utama</a></p>
  </div>
</section>
</main>
""" + footer_html() + "</body>\n</html>\n"
write("404.html", page)


# ---- sitemap.xml ----
urls = [(SITE_URL + "/", TODAY, "1.0", "daily"),
        (SITE_URL + "/resepi/", TODAY, "0.9", "daily"),
        (SITE_URL + "/kategori/", TODAY, "0.8", "weekly"),
        (SITE_URL + "/cari/", TODAY, "0.4", "monthly"),
        (SITE_URL + "/tentang/", TODAY, "0.4", "monthly")]
for c in CATS:
    urls.append((f"{SITE_URL}/kategori/{cat_slug(c)}/", TODAY, "0.7", "weekly"))
# NOTE: paginated /halaman/N/ pages are deliberately EXCLUDED from the sitemap.
# robots.txt Disallows /halaman/, and submitting a URL you also disallow produces
# "Submitted URL blocked by robots.txt" errors in Search Console. They stay
# crawlable for link equity but must never appear here. Gate #22 enforces this.
for canon, mod, _t in RECIPE_URLS:
    urls.append((canon, mod, "0.8", "monthly"))

sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for loc, mod, pri, freq in urls:
    sm.append(f"  <url>\n    <loc>{esc(loc)}</loc>\n"
              f"    <lastmod>{mod}</lastmod>\n"
              f"    <changefreq>{freq}</changefreq>\n"
              f"    <priority>{pri}</priority>\n  </url>")
sm.append("</urlset>")
write("sitemap.xml", "\n".join(sm))
print(f"sitemap ok: {len(urls)} urls")


# ---- robots.txt ----
write("robots.txt", f"""User-agent: *
Allow: /
Disallow: /halaman/

# Paginated index pages duplicate the /resepi/ listing and are kept out of the
# index to avoid thin near-duplicate pages, but they stay crawlable so link
# equity flows through the pagination chain.

# AI / LLM crawlers: allowed. The content is original editorial work and we
# want it quotable with attribution back to the page.
User-agent: GPTBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: CCBot
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
""")

# ---- IndexNow key ----
# IndexNow lets Bing/Yandex/Naver re-crawl instantly on change instead of
# waiting for the next scheduled crawl. The key file must be served from the
# root and contain exactly the key.
INDEXNOW_KEY = "8f3a2b6c9d4e5f7a1b3c8d6e9f2a4b7c"
write(f"{INDEXNOW_KEY}.txt", INDEXNOW_KEY + "\n")
print("indexnow key written")

# ---- RSS feed ----
items = []
for r in recipes[:50]:
    items.append(f"""    <item>
      <title>{esc(headline_of(r))}</title>
      <link>{esc(SITE_URL)}/resepi/{r['slug']}/</link>
      <guid isPermaLink="true">{esc(SITE_URL)}/resepi/{r['slug']}/</guid>
      <pubDate>{r['published_d']}T00:00:00+08:00</pubDate>
      <category>{esc(r['cat1'])}</category>
      <description>{esc(r['meta_desc'])}</description>
    </item>""")
write("feed.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{SITE_NAME}: {SITE_TAGLINE}</title>
    <link>{SITE_URL}/</link>
    <description>{esc(SITE_DESC)}</description>
    <language>ms-MY</language>
    <lastBuildDate>{TODAY}T00:00:00+08:00</lastBuildDate>
    <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
{chr(10).join(items)}
  </channel>
</rss>
""")

# ---- assets ----
shutil.copy2(css_path, os.path.join(DIST, "style.css"))

# Search index as a separate, long-cacheable asset.
write("search-index.json", json.dumps(
    [{"t": headline_of(r), "s": r["slug"], "c": r["cat1"],
      "i": img_url(r), "d": clean_meta(r["intro"], 110)} for r in recipes],
    ensure_ascii=False, separators=(",", ":")))
print("search-index.json written")

# Cloudflare Pages control files must live in the publish directory
for cf_file in ("_headers", "_redirects"):
    src_cf = os.path.join(ROOT, cf_file)
    if os.path.exists(src_cf):
        shutil.copy2(src_cf, os.path.join(DIST, cf_file))

# ---- crawler / AI-discovery essentials ----
# llms.txt: how an LLM should read this site. security.txt: responsible
# disclosure. Served at both /security.txt and /.well-known/security.txt
# because the RFC 9116 canonical location is the .well-known path but older
# scanners still probe the root.
for _name, _dest in (("llms.txt", "llms.txt"),
                     ("security.txt", "security.txt"),
                     ("security.txt", ".well-known/security.txt")):
    _s = os.path.join(STATIC, _name)
    if os.path.exists(_s):
        _d = os.path.join(DIST, _dest)
        os.makedirs(os.path.dirname(_d), exist_ok=True)
        shutil.copy2(_s, _d)
        print(f"essentials: {_dest}")

# ---- 301 redirects: old dated URLs -> clean SEO URLs ----
# Slugs used to carry the Blogger year-month prefix (2020-04-resepi-...). That
# prefix is now stripped for SEO. Every legacy URL must 301 to its clean
# counterpart so the existing index and inbound links do not 404.
SLUG_MAP_PATH = os.path.join(ROOT, "src", "slug_map.json")
_redirect_lines = [
    "# Auto-generated by build_static.py from src/slug_map.json",
    "# Legacy Blogger-dated URLs -> clean canonical URLs (permanent).",
]
if os.path.exists(SLUG_MAP_PATH):
    _smap = json.load(open(SLUG_MAP_PATH, encoding="utf-8"))
    _n = 0
    for _old, _new in sorted(_smap.items()):
        if _old != _new:
            _redirect_lines.append(f"/resepi/{_old}/ /resepi/{_new}/ 301")
            _n += 1
    print(f"301 redirects written: {_n}")
# trailing-slash and uppercase .html legacy forms of the SAME clean slug are
# handled by Pages' automatic slash normalisation; nothing else is needed.
write("_redirects", "\n".join(_redirect_lines) + "\n")

# favicon.svg
write("favicon.svg", """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" rx="22" fill="#c2542a"/>
<text x="50" y="68" font-family="Georgia,serif" font-size="52" font-weight="bold" fill="#faf7f2" text-anchor="middle">R</text>
</svg>""")

# icon-512.png + og-default.jpg: referenced by JSON-LD publisher logo and OG tags.
# If they already exist in static/, copy them in — this keeps the build working on
# hosts without Pillow (e.g. Cloudflare's build image). Only generate with Pillow
# as a fallback when the prebuilt assets are absent.
_static_icon = os.path.join(STATIC, "icon-512.png")
_static_og = os.path.join(STATIC, "og-default.jpg")
if os.path.exists(_static_icon) and os.path.exists(_static_og):
    shutil.copy2(_static_icon, os.path.join(DIST, "icon-512.png"))
    shutil.copy2(_static_og, os.path.join(DIST, "og-default.jpg"))
    print("icon-512.png + og-default.jpg copied from static/")
else:
    try:
        from PIL import Image, ImageDraw, ImageFont
        im = Image.new("RGB", (512, 512), "#c2542a")
        d = ImageDraw.Draw(im)
        try:
            f = ImageFont.truetype("/system/fonts/DroidSerif-Bold.ttf", 290)
        except Exception:
            f = ImageFont.load_default()
        bbox = d.textbbox((0, 0), "R", font=f)
        d.text(((512 - (bbox[2] - bbox[0])) / 2 - bbox[0],
                (512 - (bbox[3] - bbox[1])) / 2 - bbox[1]), "R", font=f, fill="#faf7f2")
        im.save(os.path.join(DIST, "icon-512.png"))
        og = Image.new("RGB", (1200, 630), "#faf7f2")
        d2 = ImageDraw.Draw(og)
        d2.rectangle([0, 0, 1200, 12], fill="#c2542a")
        try:
            fb = ImageFont.truetype("/system/fonts/DroidSerif-Bold.ttf", 92)
            fs = ImageFont.truetype("/system/fonts/DroidSans.ttf", 38)
        except Exception:
            fb = fs = ImageFont.load_default()
        d2.text((90, 210), SITE_NAME, font=fb, fill="#1a1815")
        d2.text((90, 340), f"{len(recipes)} resepi Malaysia", font=fs, fill="#47403a")
        d2.text((90, 400), "Bahan lengkap - langkah jelas - tips masakan", font=fs, fill="#7d736a")
        og.save(os.path.join(DIST, "og-default.jpg"), quality=88)
        print("icon-512.png + og-default.jpg generated")
    except Exception as e:
        print(f"WARN: image generation skipped ({e})")

print("\n=== BUILD COMPLETE ===")
