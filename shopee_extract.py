#!/usr/bin/env python3
"""
Extract Shopee-affiliate product keywords from the resepifesbuk corpus.

Outputs one row per normalized product keyword with:
  keyword      - canonical purchasable item (BM, as searched on Shopee MY)
  alias        - raw forms seen in recipes (top few)
  count        - number of recipes whose ingredient list mentions it
  mentions     - raw mention count (multiple lines in same recipe)
  category     - equipment | ingredient | appliance | packaging
  subcategory  - finer grouping (e.g. periuk, pisau, rempah)
  recipe_cat   - dominant recipe category it appears in
  example_recipe / example_url
"""
import json, re, csv, collections, unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA = json.load(open(BASE / "src/content_fix.json"))
CATS = json.load(open(BASE / "src/cats.json"))


def recipe_cat(slug):
    v = CATS.get(slug)
    if isinstance(v, dict):
        return v.get("cat") or "Lain"
    return v or "Lain"


# ---------------------------------------------------------------- normalising
QTY_WORDS = r"""
secubit|secawan|sudu besar|sudu kecil|sudu teh|sudu makan|sudu|
cawan|gelas|botol|paket|bungkus|ketul|biji|ulas|inci|keping|helai|
batang|ruas|potong|genggam|tin|kotak|kampit|gantang|liter|ml|gram|kg|
satu|dua|tiga|empat|lima|enam|tujuh|lapan|sembilan|sepuluh|setengah|
sukuan|separuh|secukup rasa|secukupnya|secukup|sedikit|sikit|serbuk|
iaitu|atau|dan|serta|-|–|,|\(|\)|/|%
"""
QTY_RE = re.compile(r"\b(?:" + QTY_WORDS + r")\b", re.I)
NUM_RE = re.compile(r"\b\d+([.,]\d+)?\b")
DESC_RE = re.compile(
    r"\b(?:yang|yg|untuk|utk|siap|dihiris|hiris|dicincang|cincang|ditumbuk|"
    r"dikisar|kisar|dipotong|potong|dibuang|buang|dibersihkan|bersih|"
    r"optional|pilihan|kalau|jika|nak|lebih|kurang|besar|kecil|sederhana)\b",
    re.I,
)

# Canonical product map: ordered list of (compiled regex, canonical, subcategory, kind)
# kind: ingredient | equipment | appliance | packaging
CANON = [
    # ---------------- appliances / machines (high affiliate value) -------------
    (r"mesin aiskrim|ice cream maker|pembuat aiskrim", "Mesin Pembuat Aiskrim (Ice Cream Maker)", "appliance", "appliance"),
    (r"pengisar aiskrim", "Pengisar Aiskrim / Ice Cream Maker", "appliance", "appliance"),
    (r"air fryer|airfryer", "Air Fryer", "appliance", "appliance"),
    (r"oven", "Oven", "appliance", "appliance"),
    (r"microwave", "Microwave", "appliance", "appliance"),
    (r"periuk nasi|rice cooker", "Periuk Nasi Elektrik (Rice Cooker)", "appliance", "appliance"),
    (r"pressure cooker|periuk tekanan", "Pressure Cooker", "appliance", "appliance"),
    (r"slow cooker", "Slow Cooker", "appliance", "appliance"),
    (r"blender", "Blender", "appliance", "appliance"),
    (r"pengisar|food processor|processor makanan", "Pengisar / Food Processor", "appliance", "appliance"),
    (r"mixer|pengadun|stand mixer|hand mixer", "Mixer (Pengadun Kek)", "appliance", "appliance"),
    (r"ketuhar", "Ketuhar (Oven)", "appliance", "appliance"),
    (r"kuali leper|kuali tidak melekat|non ?stick", "Kuali Leper Tidak Melekat", "appliance", "appliance"),
    (r"grill|griller|pemanggang", "Pemanggang / Grill Pan", "appliance", "appliance"),
    (r"steamer|pengukus elektrik|pengukus", "Pengukus (Steamer)", "appliance", "appliance"),
    (r"toaster|pembakar roti", "Toaster", "appliance", "appliance"),
    (r"kettle|cerek elektrik|pemanas air", "Cerek Elektrik (Electric Kettle)", "appliance", "appliance"),
    (r"dapur elektrik|cooker hood|induksi", "Dapur Elektrik / Induksi", "appliance", "appliance"),
    (r"mesin roti|bread maker", "Bread Maker", "appliance", "appliance"),
    (r"mesin pembuat mee|pasta maker|mesin mee", "Mesin Pembuat Mee / Pasta Maker", "appliance", "appliance"),
    (r"dehydrator|pengering makanan", "Food Dehydrator", "appliance", "appliance"),
    (r"yogurt maker|pembuat yogurt", "Yogurt Maker", "appliance", "appliance"),
    (r"takoyaki", "Acuan Takoyaki", "appliance", "appliance"),
    (r"waffle", "Acuan Waffle / Waffle Maker", "appliance", "appliance"),
    (r"cawan kek|cawan muffin", "Cawan Kek / Cupcake Liner", "packaging", "packaging"),
    (r"模具|acuan kek|acuan kuih|loyang", "Acuan Kek / Loyang", "equipment", "equipment"),

    # ---------------- cookware (periuk / kuali) ----------------
    (r"periuk belanga|belanga", "Periuk Belanga", "periuk", "equipment"),
    (r"periuk tanah|lupakan", "Periuk Tanah / Lupakan", "periuk", "equipment"),
    (r"periuk kukus|periuk pengukus", "Periuk Pengukus", "periuk", "equipment"),
    (r"periuk", "Periuk", "periuk", "equipment"),
    (r"kuali", "Kuali", "kuali", "equipment"),
    (r"wok", "Wok / Kuali Besar", "kuali", "equipment"),
    (r"pan|frying pan|kuali leper", "Frying Pan", "kuali", "equipment"),
    (r"saucepan", "Saucepan", "periuk", "equipment"),
    (r"pot", "Pot Memasak", "periuk", "equipment"),
    (r"tutup periuk|penutup", "Tudung / Penutup Periuk", "periuk", "equipment"),

    # ---------------- knives & prep tools ----------------
    (r"pisau", "Pisau Dapur", "pisau", "equipment"),
    (r"papan pemotong|cutting board|talenan", "Papan Pemotong (Chopping Board)", "pisau", "equipment"),
    (r"pengasah pisau|knife sharpener", "Pengasah Pisau", "pisau", "equipment"),
    (r"peeler|pengupas", "Pengupas Kulit (Peeler)", "pisau", "equipment"),
    (r"gunting", "Gunting Dapur", "pisau", "equipment"),
    (r"parut|grater|pemarut", "Pemarut (Grater)", "equipment", "equipment"),
    (r"lesung|mortar", "Lesung Batu", "equipment", "equipment"),
    (r"penumbuk|tumbuk", "Penumbuk / Lesung", "equipment", "equipment"),
    (r"penapis|strainer|colander|tapis", "Penapis / Strainer", "equipment", "equipment"),
    (r"penyepit|tongs", "Penyepit (Tongs)", "equipment", "equipment"),
    (r"senduk", "Senduk", "equipment", "equipment"),
    (r"spatula|sudip", "Spatula / Sudip", "equipment", "equipment"),
    (r"whisk|pengocok", "Whisk / Pengocok", "equipment", "equipment"),
    (r"roller|penggelek|gelek", "Roller / Penggelek Doh", "equipment", "equipment"),
    (r"brush|berus", "Berus Marjerin / Brush", "equipment", "equipment"),
    (r"termometer|thermometer", "Termometer Dapur", "equipment", "equipment"),
    (r"penimbang|timbang dapur|scale", "Penimbang Dapur (Kitchen Scale)", "equipment", "equipment"),
    (r"cawan penyukat|measuring cup", "Cawan Penyukat", "equipment", "equipment"),
    (r"sudu penyukat|measuring spoon", "Sudu Penyukat", "equipment", "equipment"),
    (r"piping bag|nozel", "Piping Bag + Nozel", "equipment", "equipment"),
    (r"acuan", "Acuan Kuih / Kek", "equipment", "equipment"),

    # ---------------- packaging / serving ----------------
    (r"bekas makanan|container makanan|tupperware", "Bekas Makanan (Food Container)", "packaging", "packaging"),
    (r"plastik|beg plastik|wrap", "Plastik Pembalut / Cling Wrap", "packaging", "packaging"),
    (r"foil|aluminium foil", "Aluminium Foil", "packaging", "packaging"),
    (r"baking paper|kertas pembakar|kertas minyak", "Kertas Pembakar (Baking Paper)", "packaging", "packaging"),
    (r"botol", "Botol Kaca / Plastik", "packaging", "packaging"),
    (r"tin|tin sardin|tin susu|tin jagung", "Makanan Tin (Sardin / Susu / Jagung)", "ingredient", "ingredient"),
    (r"stapler|pita pelekat|tape", "Stapler / Pita Pelekat", "packaging", "packaging"),
    (r"label|sticker", "Label / Sticker Produk", "packaging", "packaging"),
    (r"lidi|satay stick", "Lidi Sate", "packaging", "packaging"),
    (r"kertas|paper cup", "Cawan Kertas / Cup", "packaging", "packaging"),

    # ---------------- sauces & condiments (sos cili etc.) ----------------
    (r"sos cili|chili sauce|cili sos", "Sos Cili", "sos", "ingredient"),
    (r"sos tomato|tomato sauce", "Sos Tomato", "sos", "ingredient"),
    (r"sos tiram|tiram", "Sos Tiram", "sos", "ingredient"),
    (r"sos ikan|fish sauce", "Sos Ikan", "sos", "ingredient"),
    (r"sos lada hitam|black pepper sauce", "Sos Lada Hitam", "sos", "ingredient"),
    (r"sos cili thai|thai sauce", "Sos Cili Thai", "sos", "ingredient"),
    (r"sos thai", "Sos Thai", "sos", "ingredient"),
    (r"mayonis|mayonnaise", "Mayonis", "sos", "ingredient"),
    (r"sos salad|thousand island", "Sos Salad / Thousand Island", "sos", "ingredient"),
    (r"cuka", "Cuka", "sos", "ingredient"),
    (r"kicap lemak|kicap manis", "Kicap Manis", "sos", "ingredient"),
    (r"kicap", "Kicap", "sos", "ingredient"),
    (r"sos", "Sos (Umum)", "sos", "ingredient"),
    (r"pes|paste", "Pes Makanan (Pes Cili / Pes Kari)", "sos", "ingredient"),
    (r"sambal", "Sambal (Pes)", "sos", "ingredient"),
    (r"madu|honey", "Madu", "ingredient", "ingredient"),
    (r"mentega kacang|peanut butter", "Mentega Kacang", "ingredient", "ingredient"),
    (r"jam|jelly|jem", "Jam / Jelly", "ingredient", "ingredient"),
    (r"coklat|chocolate", "Coklat Masakan", "ingredient", "ingredient"),
    (r"nutella", "Nutella", "ingredient", "ingredient"),

    # ---------------- dry goods / pantry ----------------
    (r"tepung gandum", "Tepung Gandum", "tepung", "ingredient"),
    (r"tepung beras", "Tepung Beras", "tepung", "ingredient"),
    (r"tepung pulut|tepung glutinous", "Tepung Pulut", "tepung", "ingredient"),
    (r"tepung jagung", "Tepung Jagung", "tepung", "ingredient"),
    (r"tepung ubi", "Tepung Ubi", "tepung", "ingredient"),
    (r"tepung kastard", "Tepung Kastard", "tepung", "ingredient"),
    (r"tepung", "Tepung (Umum)", "tepung", "ingredient"),
    (r"beras pulut|pulut", "Beras Pulut", "beras", "ingredient"),
    (r"beras basmati", "Beras Basmati", "beras", "ingredient"),
    (r"beras", "Beras", "beras", "ingredient"),
    (r"bihun", "Bihun", "mee", "ingredient"),
    (r"mee kuning|mi kuning", "Mee Kuning", "mee", "ingredient"),
    (r"mee", "Mee", "mee", "ingredient"),
    (r"mihun|meehun", "Mihun", "mee", "ingredient"),
    (r"kuetiau|kuey teow", "Kuetiau", "mee", "ingredient"),
    (r"pasta|spaghetti|macaroni", "Pasta / Spaghetti", "mee", "ingredient"),
    (r"gula pasir|gula kastor", "Gula Pasir / Kastor", "ingredient", "ingredient"),
    (r"gula melaka|gula kabung", "Gula Melaka", "ingredient", "ingredient"),
    (r"gula apong", "Gula Apong", "ingredient", "ingredient"),
    (r"gula", "Gula", "ingredient", "ingredient"),
    (r"garam", "Garam", "ingredient", "ingredient"),
    (r"serbuk kari|rempah kari", "Serbuk Kari", "rempah", "ingredient"),
    (r"serbuk rempah sup|rempah sup", "Serbuk Rempah Sup", "rempah", "ingredient"),
    (r"rempah kurma|kurma", "Rempah Kurma", "rempah", "ingredient"),
    (r"rempah ratus|rempah", "Rempah Ratus", "rempah", "ingredient"),
    (r"serbuk kunyit|kunyit", "Serbuk Kunyit", "rempah", "ingredient"),
    (r"serbuk cili|cili kisar|cili boh|cili giling", "Cili Kisar / Cili Boh", "rempah", "ingredient"),
    (r"serbuk lada hitam|lada hitam", "Lada Hitam", "rempah", "ingredient"),
    (r"lada putih", "Lada Putih", "rempah", "ingredient"),
    (r"lada sulah", "Lada Sulah", "rempah", "ingredient"),
    (r"serbuk ketumbar|ketumbar", "Serbuk Ketumbar", "rempah", "ingredient"),
    (r"jintan", "Jintan Manis / Jintan Putih", "rempah", "ingredient"),
    (r"bunga lawang", "Bunga Lawang", "rempah", "ingredient"),
    (r"bunga cengkih|cengkih", "Bunga Cengkih", "rempah", "ingredient"),
    (r"kayu manis", "Kayu Manis", "rempah", "ingredient"),
    (r"buah pelaga|pelaga", "Buah Pelaga", "rempah", "ingredient"),
    (r"emping|kerisik", "Kerisik", "ingredient", "ingredient"),
    (r"santan", "Santan (Kelapa)", "ingredient", "ingredient"),
    (r"kelapa parut|kelapa", "Kelapa Parut", "ingredient", "ingredient"),

    # ---------------- fresh produce ----------------
    (r"bawang putih", "Bawang Putih", "sayur", "ingredient"),
    (r"bawang merah|bawang kecil", "Bawang Merah", "sayur", "ingredient"),
    (r"bawang besar|bawang holland", "Bawang Besar", "sayur", "ingredient"),
    (r"bawang", "Bawang", "sayur", "ingredient"),
    (r"halia", "Halia", "sayur", "ingredient"),
    (r"lengkuas|galangal", "Lengkuas", "sayur", "ingredient"),
    (r"serai", "Serai", "sayur", "ingredient"),
    (r"daun kari", "Daun Kari", "sayur", "ingredient"),
    (r"daun pandan|pandan", "Daun Pandan", "sayur", "ingredient"),
    (r"daun sup", "Daun Sup", "sayur", "ingredient"),
    (r"daun bawang", "Daun Bawang", "sayur", "ingredient"),
    (r"daun ketumbar", "Daun Ketumbar", "sayur", "ingredient"),
    (r"daun salam", "Daun Salam", "sayur", "ingredient"),
    (r"daun kunyit", "Daun Kunyit", "sayur", "ingredient"),
    (r"daun limau", "Daun Limau Purut", "sayur", "ingredient"),
    (r"limau purut", "Limau Purut", "sayur", "ingredient"),
    (r"limau nipis", "Limau Nipis", "sayur", "ingredient"),
    (r"limau", "Limau", "sayur", "ingredient"),
    (r"tomato", "Tomato", "sayur", "ingredient"),
    (r"ubi kentang|kentang", "Kentang", "sayur", "ingredient"),
    (r"ubi keledek|keledek", "Keledek", "sayur", "ingredient"),
    (r"lobak merah|carrot", "Lobak Merah", "sayur", "ingredient"),
    (r"sawi|bayam|kangkung|sayur", "Sayur Hijau", "sayur", "ingredient"),
    (r"cili api|cili padi", "Cili Api", "sayur", "ingredient"),
    (r"cili besar|cili merah", "Cili Merah", "sayur", "ingredient"),
    (r"cili", "Cili", "sayur", "ingredient"),
    (r"jagung", "Jagung", "sayur", "ingredient"),
    (r"cendawan", "Cendawan", "sayur", "ingredient"),
    (r"brokoli", "Brokoli", "sayur", "ingredient"),

    # ---------------- protein ----------------
    (r"daging kisar|daging cincang", "Daging Kisar", "protein", "ingredient"),
    (r"daging", "Daging", "protein", "ingredient"),
    (r"ayam", "Ayam", "protein", "ingredient"),
    (r"udang", "Udang", "protein", "ingredient"),
    (r"ikan", "Ikan", "protein", "ingredient"),
    (r"sotong", "Sotong", "protein", "ingredient"),
    (r"ketam", "Ketam", "protein", "ingredient"),
    (r"telur", "Telur", "protein", "ingredient"),
    (r"tahu", "Tahu", "protein", "ingredient"),
    (r"tempe", "Tempe", "protein", "ingredient"),

    # ---------------- dairy / baking ----------------
    (r"mentega|butter", "Mentega", "dairy", "ingredient"),
    (r"marjerin|margarine", "Marjerin", "dairy", "ingredient"),
    (r"susu pekat manis|susu manis", "Susu Pekat Manis", "dairy", "ingredient"),
    (r"susu sejat|susu cair", "Susu Sejat", "dairy", "ingredient"),
    (r"susu tepung|susu serbuk|susu formula", "Susu Tepung", "dairy", "ingredient"),
    (r"susu", "Susu", "dairy", "ingredient"),
    (r"krim keju|cream cheese", "Cream Cheese", "dairy", "ingredient"),
    (r"krim|cream|whipping", "Krim Putar (Whipping Cream)", "dairy", "ingredient"),
    (r"keju|cheese", "Keju", "dairy", "ingredient"),
    (r"yogurt|yoghurt", "Yogurt", "dairy", "ingredient"),
    (r"serbuk penaik|baking powder", "Serbuk Penaik", "baking", "ingredient"),
    (r"soda bikarbonat|baking soda", "Soda Bikarbonat", "baking", "ingredient"),
    (r"esens vanila|vanilla", "Esens Vanila", "baking", "ingredient"),
    (r"agar-agar|agar", "Agar-Agar", "baking", "ingredient"),
    (r"gelatin", "Gelatin", "baking", "ingredient"),
    (r"jeli|jelly", "Serbuk Jeli", "baking", "ingredient"),
    (r"ragi|yeast", "Ragi (Yeast)", "baking", "ingredient"),
    (r"horlicks", "Horlicks", "ingredient", "ingredient"),
    (r"milo", "Milo", "ingredient", "ingredient"),
    (r"ovaltine", "Ovaltine", "ingredient", "ingredient"),
    (r"nescafe|kopi", "Kopi / Nescafe", "ingredient", "ingredient"),
    (r"teh", "Teh", "ingredient", "ingredient"),
    (r"coklat emulco|emulco", "Emulco Coklat", "baking", "ingredient"),
    (r"pewarna", "Pewarna Makanan", "baking", "ingredient"),
    (r"gula aising|icing sugar", "Gula Aising", "baking", "ingredient"),
    (r"cocoa|serbuk koko|koko", "Serbuk Koko", "baking", "ingredient"),
    (r"badam|almond", "Badam", "ingredient", "ingredient"),
    (r"kismis|raisin", "Kismis", "ingredient", "ingredient"),
    (r"kacang", "Kacang", "ingredient", "ingredient"),
    (r"oreo", "Biskut Oreo", "ingredient", "ingredient"),
    (r"biskut|biskut marie|marie", "Biskut", "ingredient", "ingredient"),
    (r"roti", "Roti", "ingredient", "ingredient"),
    (r"air", "Air", "ingredient", "ingredient"),
    (r"minyak", "Minyak Masak", "ingredient", "ingredient"),
]

CANON_C = [(re.compile(p, re.I), c, sub, kind) for p, c, sub, kind in CANON]


def clean_ingredient(raw: str) -> str:
    s = unicodedata.normalize("NFKC", raw).lower().strip()
    s = re.sub(r"\s*-\s*", " - ", s)
    s = NUM_RE.sub(" ", s)
    s = QTY_RE.sub(" ", s)
    s = DESC_RE.sub(" ", s)
    s = re.sub(r"[^\w\s\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def match_canon(text: str):
    """Return list of (canonical, subcategory, kind) matched, longest pattern first."""
    found = []
    remaining = text
    for rx, canon_name, sub, kind in CANON_C:
        if rx.search(remaining):
            found.append((canon_name, sub, kind, rx.pattern))
    return found


# ---------------------------------------------------------------- aggregation
agg = collections.defaultdict(lambda: {
    "recipes": set(), "mentions": 0, "alias": collections.Counter(),
    "recipe_cat": collections.Counter(), "example": None,
})

raw_counter = collections.Counter()

for slug, rec in DATA.items():
    ings = rec.get("ingredients") or []
    cat = recipe_cat(slug)
    seen_in_this_recipe = set()
    for ing in ings:
        norm = clean_ingredient(ing)
        if not norm:
            continue
        raw_counter[norm] += 1
        matched = match_canon(norm)
        # de-dup: keep most specific (first match by our ordered list = most specific)
        hit_names = set()
        for canon_name, sub, kind, _pat in matched:
            if canon_name in hit_names:
                continue
            hit_names.add(canon_name)
            a = agg[canon_name]
            a["subcategory"] = sub
            a["kind"] = kind
            a["mentions"] += 1
            a["recipes"].add(slug)
            a["alias"][ing.strip()] += 1
            a["recipe_cat"][cat] += 1
            if a["example"] is None:
                a["example"] = slug
        # generic fallback so nothing is lost
        if not matched:
            a = agg[norm]
            a.setdefault("subcategory", "lain")
            a.setdefault("kind", "ingredient")
            a["mentions"] += 1
            a["recipes"].add(slug)
            a["alias"][ing.strip()] += 1
            a["recipe_cat"][cat] += 1
            if a["example"] is None:
                a["example"] = slug

print(f"recipes: {len(DATA)}   canonical keywords: {len(agg)}")
json.dump({k: {"mentions": v["mentions"], "recipes": len(v["recipes"]),
               "subcategory": v.get("subcategory"), "kind": v.get("kind"),
               "recipe_cat": dict(v["recipe_cat"])}
           for k, v in agg.items()},
          open(BASE / "shopee_agg.json", "w"), ensure_ascii=False, indent=1)
print("wrote shopee_agg.json")
