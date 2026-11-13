"""Parse raw Blogger HTML into structured recipe records.

Three content formats exist across 748 posts:
  A) Modern:  <h2>🛒 Bahan-Bahan...</h2> + <ul><li>  (139 posts)
  B) Mid:     <div dir="auto"><b><u>Bahan Bahan...</u></b></div> + plain <div> lines (268)
  C) Old:     bold/underline headings in <p>/<div>, free-form text lines (375)

Strategy: flatten the HTML into an ordered list of (text, is_heading) lines and
classify by keyword. Headings are detected by format markers OR by keyword +
short length. This is format-agnostic and survives all three.
"""
import json, re, html, os

SRC = os.path.expanduser("~/resepifesbuk/src/posts_full.json")
OUT = os.path.expanduser("~/resepifesbuk/src/recipes_clean.json")

posts = json.load(open(SRC))

# ---- keyword sets (BM recipe vocabulary) ----
RE_ING = re.compile(r"(bahan[\s-]*bahan|bahan-bahannya|bahannya|bahan\s|bahan:|keperluan|ingredients)", re.I)
RE_STEP = re.compile(r"(cara\s*(buat|masak|membuat|memasak|menyedia|penyediaan|penyedian|menghasilkan)|caranya|cara-cara|cara\s*menyediakan|langkah|step|arahan|how\s*to|kaedah)", re.I)
RE_TIP = re.compile(r"(tips?|tip\s|rahsia|nota|panduan)", re.I)


def clean_text(s):
    s = re.sub(r"<script[^>]*>.*?</script>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<style[^>]*>.*?</style>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</(p|div|li|h\d|tr)>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    return s


def to_lines(content):
    """Flatten HTML into ordered lines, each tagged bold if it was a bold/heading block."""
    # mark heading-ish containers with a sentinel before stripping tags
    c = content
    # <h1..h6> always heading
    c = re.sub(r"<h([1-6])[^>]*>(.*?)</h\1>", lambda m: "\x01" + m.group(2) + "\x02", c, flags=re.S | re.I)
    # <b>/<strong>/<u> containing short text -> heading candidate
    c = re.sub(r"<(b|strong|u)[^>]*>(.*?)</\1>",
               lambda m: ("\x01" + m.group(2) + "\x02") if len(clean_text(m.group(2)).strip()) < 90 and clean_text(m.group(2)).strip()
               else m.group(2),
               c, flags=re.S | re.I)
    raw = clean_text(c)

    lines = []
    for ln in raw.split("\n"):
        heading = False
        if "\x01" in ln:
            heading = True
            ln = ln.replace("\x01", "").replace("\x02", "")
        ln = ln.strip()
        if not ln:
            continue
        lines.append((ln, heading))
    return lines


def classify(text, heading):
    """Return 'ingredients'|'steps'|'tips'|'substep'|'subhead'|None."""
    t = text.strip().rstrip(":").strip()
    low = t.lower()
    if len(t) > 100:
        return None
    # Numbered sub-headings FIRST: "1. Menyediakan Bahan Perencah" contains
    # "bahan" but is a step heading, not an ingredients section. Order matters.
    if re.match(r"^\d+\s*[\.\)]\s*\S", t):
        return "substep"
    if RE_ING.search(low) and not RE_STEP.search(low):
        # Guard: "Kacau semua bahan sehingga sebati..." is a METHOD sentence that
        # mentions ingredients, not an ingredients heading. Real ingredient
        # headings are short and don't start with a cooking verb.
        IMPERATIVE = re.match(
            r"^(kacau|masukkan|panaskan|tumis|gaul|kukus|rebus|goreng|bakar|tuang|campur|"
            r"satukan|letak|angkat|tapis|toskan|rendam|potong|hiris|kisar|sejukkan|hidang)", low)
        if not IMPERATIVE or len(t) > 60:
            return "ingredients"
    if RE_STEP.search(low):
        return "steps"
    if RE_TIP.search(low) and len(t) < 70:
        return "tips"
    # "Bahagian 1: Lapisan Bawah (Pandan)" heads a PART whose following bullets
    # are that part's ingredients; the method follows under "Cara Menyediakan:".
    if re.match(r"^(bahagian|fasa|peringkat)\s*\d*", low):
        return "ingredients"
    if re.match(r"^(langkah|step)\s*\d*", low):
        return "steps"
    # Short emoji-led sub-headings: "🥬 Bahan Utama:", "🌶️ Bahan Tumbuk:"
    if heading and len(t) < 60 and re.match(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF]", t):
        # an emoji heading mentioning a cooking verb is a step heading
        if re.search(r"(masak|tumis|goreng|kacau|rebus|kukus|bakar|sejukkan|siap|gaul|tuang|lapis)", low):
            return "steps"
        return "subhead"
    return None


def parse(content):
    lines = to_lines(content)
    ing, steps, tips, intro = [], [], [], []
    cur = None
    saw_section = False

    for text, heading in lines:
        kind = classify(text, heading)
        if kind in ("ingredients", "steps", "tips"):
            cur = kind
            saw_section = True
            continue
        if kind in ("substep", "subhead"):
            # keep the sub-heading as a visible line inside the active section
            if cur == "steps" and kind == "substep":
                steps.append(("#", text))
            continue
        if re.match(r"^https?://", text):
            continue
        if len(text) < 2:
            continue
        if cur == "ingredients":
            ing.append(text)
        elif cur == "steps":
            steps.append(text)
        elif cur == "tips":
            tips.append(text)
        elif cur is None:
            if len(text) > 40:
                intro.append(text)

    return ing, steps, tips, " ".join(intro)[:600], saw_section


def first_image(content):
    m = re.search(r'<img[^>]+src="([^"]+)"', content, flags=re.I)
    return m.group(1) if m else ""


def img_big(url):
    if not url:
        return ""
    return re.sub(r"/s\d+(-c)?/", "/s1600/", url)


def slug_from_url(url):
    m = re.search(r"/(\d{4})/(\d{2})/([^/]+?)\.html", url)
    if not m:
        return re.sub(r"[^a-z0-9]+", "-", url.lower())[-60:]
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


records = []
for p in posts:
    content = p.get("content", "")
    ing, steps, tips, intro, saw = parse(content)

    # last-resort: keep the page useful rather than empty
    if not ing and not steps:
        body = clean_text(content)
        blocks = [b.strip() for b in body.split("\n") if len(b.strip()) > 3]
        ing = blocks[:12]
        steps = blocks[12:24]

    # ---- fallback: recipes with ingredients but no detected steps ----
    # 145 of 748 legacy posts put the method in plain <div> text with headings
    # that are neither bold nor <h2>. Recover by scanning the raw line stream for
    # imperative cooking sentences after the ingredient block.
    if ing and not steps:
        raw_lines = [l.strip() for l in clean_text(content).split("\n") if l.strip()]
        VERB = re.compile(r"\b(masukkan|panaskan|tumis|kacau|gaul|kukus|rebus|goreng|bakar|tuang|"
                          r"sejukkan|simpulkan|bentuk|celup|angkat|toskan|tapis|rendam|potong|"
                          r"hiris|kisar|satukan|campur|letak|siapkan|hidang|sedia|perasakan)\b", re.I)
        for l in raw_lines:
            if len(l) < 25 or l in ing:
                continue
            if VERB.search(l) and not re.match(r"^[\d½¼¾]", l):
                steps.append({"t": l})
    if ing and not steps:
        blocks = [b.strip() for b in clean_text(content).split("\n") if len(b.strip()) > 30]
        for b in blocks:
            if b not in ing:
                steps.append({"t": b})
            if len(steps) >= 8:
                break

    cats = [c for c in p.get("cats", []) if not c.lower().startswith("resepi")]
    # normalise steps: ("#", subheading) tuples -> dicts, plain strings -> dicts
    norm_steps = []
    for s in steps:
        if isinstance(s, dict):
            norm_steps.append(s)
        elif isinstance(s, tuple):
            norm_steps.append({"h": s[1]})
        elif isinstance(s, str) and s.strip():
            norm_steps.append({"t": s.strip()})
    records.append({
        "slug": slug_from_url(p["url"]),
        "title": p["title"],
        "url": p["url"],
        "published": p.get("published", ""),
        "updated": p.get("updated", ""),
        "cats": cats,
        "img": img_big(first_image(content) or p.get("thumb", "")),
        "intro": intro,
        "ingredients": ing,
        "steps": norm_steps,
        "tips": tips,
        "n_ing": len(ing),
        "n_steps": sum(1 for s in norm_steps if "t" in s),
        "parsed": saw,
    })

json.dump(records, open(OUT, "w"), ensure_ascii=False)
print(f"parsed {len(records)} recipes -> {OUT}")
print(f"with sections:   {sum(1 for r in records if r['parsed'])}")
print(f"missing ing:     {sum(1 for r in records if r['n_ing']==0)}")
print(f"missing steps:   {sum(1 for r in records if r['n_steps']==0)}")
print(f"avg ingredients: {sum(r['n_ing'] for r in records)/len(records):.1f}")
print(f"avg steps:       {sum(r['n_steps'] for r in records)/len(records):.1f}")
print(f"with tips:       {sum(1 for r in records if r['tips'])}")
print(f"missing image:   {sum(1 for r in records if not r['img'])}")
