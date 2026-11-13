#!/usr/bin/env python3
"""
Build the Shopee Malaysia affiliate keyword workbook from the resepifesbuk corpus.

Sources of signal:
  1. ingredient lists  -> consumables (sos cili, tepung, gula ...)
  2. steps + tips text -> equipment & appliances (kuali, periuk, oven, blender ...)
  3. recipe category   -> appliance suggestions (aiskrim -> ice cream maker)

Output: shopee_affiliate_keywords.xlsx (multi-sheet)
"""
import json, re, collections
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE = Path(__file__).resolve().parent
DATA = json.load(open(BASE / "src/content_fix.json"))
CATS = json.load(open(BASE / "src/cats.json"))

# slug -> (dish name, category)
META = {}
for slug in DATA:
    v = CATS.get(slug) or {}
    META[slug] = {
        "dish": v.get("dish") or slug.replace("resepi-", "").replace("-", " ").title(),
        "cat": v.get("cat") or "Lain",
    }

OUT_JSON = BASE / "shopee_keywords.json"

# ============================================================ keyword dictionary
# (regex, canonical product name, subcategory, kind, shopee_search_hint)
# kind: ingredient | equipment | appliance | packaging
TERMS = [
    # ---------------- APPLIANCES (highest commission value) ----------------
    (r"\bair\s*fryer\b|\bairfryer\b", "Air Fryer", "appliance",
     "appliance", "air fryer"),
    (r"\boven\b|\bketuhar\b", "Oven / Ketuhar", "appliance",
     "appliance", "oven elektrik"),
    (r"\bmicrowave\b", "Microwave", "appliance", "appliance", "microwave oven"),
    (r"\brice\s*cooker\b|\bperiuk\s*nasi\b", "Rice Cooker (Periuk Nasi Elektrik)",
     "appliance", "appliance", "rice cooker"),
    (r"\bblender\b", "Blender", "appliance", "appliance", "blender dapur"),
    (r"\bpengisar\b", "Pengisar / Grinder", "appliance", "appliance", "pengisar makanan"),
    (r"\bmixer\b|\bpengadun\b", "Mixer / Pengadun", "appliance", "appliance", "mixer kek"),
    (r"\bwhisk\b", "Whisk / Pengocok", "equipment", "equipment", "whisk tangan"),
    (r"\bice\s*cream\s*maker\b|\bmesin\s*aiskrim\b", "Ice Cream Maker",
     "appliance", "appliance", "ice cream maker"),
    (r"\btoaster\b", "Toaster", "appliance", "appliance", "toaster 2 slice"),
    (r"\bcerek\s*elektrik\b|\bkettle\b", "Electric Kettle", "appliance",
     "appliance", "electric kettle"),
    (r"\bslow\s*cooker\b", "Slow Cooker", "appliance", "appliance", "slow cooker"),
    (r"\bpressure\s*cooker\b|\bperiuk\s*tekanan\b", "Pressure Cooker",
     "appliance", "appliance", "pressure cooker"),
    (r"\bwaffle\b", "Waffle Maker", "appliance", "appliance", "waffle maker"),
    (r"\btakoyaki\b", "Acuan Takoyaki", "appliance", "appliance", "acuan takoyaki"),
    (r"\byogurt\s*maker\b", "Yogurt Maker", "appliance", "appliance", "yogurt maker"),
    (r"\bgrill\b|\bpemanggang\b", "Grill Pan / Pemanggang", "appliance",
     "appliance", "grill pan"),
    (r"\bpengukus\s*elektrik\b", "Pengukus Elektrik (Electric Steamer)",
     "appliance", "appliance", "pengukus elektrik"),
    (r"\bfreezer\b", "Freezer / Peti Sejuk Beku", "appliance", "appliance",
     "freezer kecil"),

    # ---------------- COOKWARE ----------------
    (r"\bkuali\b", "Kuali", "periuk-kuali", "equipment", "kuali leper"),
    (r"\bperiuk\b", "Periuk", "periuk-kuali", "equipment", "periuk memasak"),
    (r"\bbelanga\b", "Periuk Belanga", "periuk-kuali", "equipment", "periuk belanga"),
    (r"\bloyang\b", "Loyang / Acuan Kek", "acuan", "equipment", "loyang kek"),
    (r"\bacuan\b", "Acuan Kuih / Kek", "acuan", "equipment", "acuan kuih"),
    (r"\bpengukus\b|\bkukus\b", "Pengukus (Kukusan)", "periuk-kuali",
     "equipment", "periuk kukus"),
    (r"\bsteamer\b", "Steamer", "periuk-kuali", "equipment", "steamer dapur"),

    # ---------------- KNIVES & PREP ----------------
    (r"\bpisau\b", "Pisau Dapur", "pisau", "equipment", "pisau dapur set"),
    (r"\btalenan\b|\bpapan\s*pemotong\b", "Papan Pemotong / Talenan", "pisau",
     "equipment", "papan pemotong"),
    (r"\bparut\b", "Pemarut (Grater)", "alat-dapur", "equipment", "pemarut kelapa"),
    (r"\blesung\b", "Lesung Batu", "alat-dapur", "equipment", "lesung batu"),
    (r"\btapis\b|\bpenapis\b", "Penapis / Strainer", "alat-dapur", "equipment",
     "penapis dapur"),
    (r"\bspatula\b", "Spatula", "alat-dapur", "equipment", "spatula silikon"),
    (r"\bsenduk\b", "Senduk", "alat-dapur", "equipment", "senduk kayu"),
    (r"\bgunting\b", "Gunting Dapur", "pisau", "equipment", "gunting dapur"),
    (r"\bpenimbang\b", "Penimbang Dapur (Kitchen Scale)", "alat-dapur",
     "equipment", "penimbang digital dapur"),
    (r"\btermometer\b", "Termometer Dapur", "alat-dapur", "equipment",
     "termometer dapur"),
    (r"\bpiping\s*bag\b|\bnozel\b", "Piping Bag + Nozel", "acuan", "equipment",
     "piping bag set"),

    # ---------------- PACKAGING ----------------
    (r"\bbekas\b", "Bekas Makanan / Container", "packaging", "packaging",
     "bekas makanan plastik"),
    (r"\btupperware\b", "Tupperware", "packaging", "packaging", "tupperware set"),
    (r"\bbotol\b", "Botol Kaca / Plastik", "packaging", "packaging", "botol kaca"),
    (r"\bfoil\b", "Aluminium Foil", "packaging", "packaging", "aluminium foil"),
    (r"\bcling\s*wrap\b|\bplastik\s*wrap\b", "Plastik Pembalut / Cling Wrap",
     "packaging", "packaging", "cling wrap"),
    (r"\bkertas\s*pembakar\b|\bbaking\s*paper\b", "Kertas Pembakar", "packaging",
     "packaging", "baking paper"),
    (r"\blidi\b", "Lidi Sate", "packaging", "packaging", "lidi sate"),
    (r"\bcawan\b", "Cawan / Paper Cup", "packaging", "packaging", "cawan kertas"),

    # ---------------- SAUCES / CONDIMENTS ----------------
    (r"\bsos\s*cili\b", "Sos Cili", "sos", "ingredient", "sos cili"),
    (r"\bsos\s*tomato\b", "Sos Tomato", "sos", "ingredient", "sos tomato"),
    (r"\bsos\s*tiram\b", "Sos Tiram", "sos", "ingredient", "sos tiram"),
    (r"\bsos\s*ikan\b", "Sos Ikan", "sos", "ingredient", "sos ikan"),
    (r"\bsos\s*lada\s*hitam\b", "Sos Lada Hitam", "sos", "ingredient",
     "sos lada hitam"),
    (r"\bsos\s*thai\b", "Sos Thai", "sos", "ingredient", "sos cili thai"),
    (r"\bmayonis\b|\bmayonnaise\b", "Mayonis", "sos", "ingredient", "mayonis"),
    (r"\bkicap\b", "Kicap", "sos", "ingredient", "kicap manis"),
    (r"\bcuka\b", "Cuka", "sos", "ingredient", "cuka makan"),
    (r"\bsambal\b", "Sambal (Pes)", "sos", "ingredient", "sambal siap"),
    (r"\bsos\b", "Sos (Umum)", "sos", "ingredient", "sos pelbagai"),

    # ---------------- DRY GOODS ----------------
    (r"\btepung\s*gandum\b", "Tepung Gandum", "tepung", "ingredient",
     "tepung gandum"),
    (r"\btepung\s*beras\b", "Tepung Beras", "tepung", "ingredient", "tepung beras"),
    (r"\btepung\s*pulut\b", "Tepung Pulut", "tepung", "ingredient", "tepung pulut"),
    (r"\btepung\s*jagung\b", "Tepung Jagung", "tepung", "ingredient",
     "tepung jagung"),
    (r"\btepung\s*kastard\b", "Tepung Kastard", "tepung", "ingredient",
     "tepung kastard"),
    (r"\btepung\b", "Tepung (Umum)", "tepung", "ingredient", "tepung serbaguna"),
    (r"\bberas\s*pulut\b|\bpulut\b", "Beras Pulut", "beras", "ingredient",
     "beras pulut"),
    (r"\bberas\b", "Beras", "beras", "ingredient", "beras wangi"),
    (r"\bbihun\b", "Bihun", "mee", "ingredient", "bihun"),
    (r"\bmee\b|\bmi\b", "Mee", "mee", "ingredient", "mee kuning"),
    (r"\bkuetiau\b|\bkuey\s*teow\b", "Kuetiau", "mee", "ingredient", "kuetiau"),
    (r"\bpasta\b|\bspaghetti\b|\bmacaroni\b", "Pasta / Spaghetti", "mee",
     "ingredient", "spaghetti"),
    (r"\bgula\s*melaka\b|\bgula\s*kabung\b", "Gula Melaka", "gula-garam",
     "ingredient", "gula melaka"),
    (r"\bgula\b", "Gula", "gula-garam", "ingredient", "gula pasir"),
    (r"\bgaram\b", "Garam", "gula-garam", "ingredient", "garam halus"),

    # ---------------- SPICES ----------------
    (r"\bserbuk\s*kari\b|\brempah\s*kari\b", "Serbuk Kari", "rempah",
     "ingredient", "serbuk kari"),
    (r"\brempah\s*sup\b", "Serbuk Rempah Sup", "rempah", "ingredient",
     "rempah sup"),
    (r"\brempah\s*kurma\b", "Rempah Kurma", "rempah", "ingredient", "rempah kurma"),
    (r"\bkunyit\b", "Serbuk Kunyit", "rempah", "ingredient", "serbuk kunyit"),
    (r"\bcili\s*boh\b|\bcili\s*kisar\b|\bcili\s*giling\b", "Cili Kisar / Cili Boh",
     "rempah", "ingredient", "cili boh"),
    (r"\blada\s*hitam\b", "Lada Hitam", "rempah", "ingredient", "lada hitam"),
    (r"\blada\s*putih\b", "Lada Putih", "rempah", "ingredient", "lada putih"),
    (r"\bketumbar\b", "Serbuk Ketumbar", "rempah", "ingredient", "serbuk ketumbar"),
    (r"\bjintan\b", "Jintan", "rempah", "ingredient", "jintan manis"),
    (r"\bbunga\s*lawang\b", "Bunga Lawang", "rempah", "ingredient", "bunga lawang"),
    (r"\bcengkih\b", "Bunga Cengkih", "rempah", "ingredient", "bunga cengkih"),
    (r"\bkayu\s*manis\b", "Kayu Manis", "rempah", "ingredient", "kayu manis"),
    (r"\bpelaga\b", "Buah Pelaga", "rempah", "ingredient", "buah pelaga"),
    (r"\brempah\b", "Rempah (Umum)", "rempah", "ingredient", "rempah ratus"),

    # ---------------- FRESH ----------------
    (r"\bbawang\s*putih\b", "Bawang Putih", "sayur", "ingredient", "bawang putih"),
    (r"\bbawang\s*merah\b|\bbawang\s*kecil\b", "Bawang Merah", "sayur",
     "ingredient", "bawang merah"),
    (r"\bbawang\s*besar\b|\bbawang\s*holland\b", "Bawang Besar", "sayur",
     "ingredient", "bawang besar"),
    (r"\bbawang\b", "Bawang", "sayur", "ingredient", "bawang"),
    (r"\bhalia\b", "Halia", "sayur", "ingredient", "halia"),
    (r"\blengkuas\b", "Lengkuas", "sayur", "ingredient", "lengkuas"),
    (r"\bserai\b", "Serai", "sayur", "ingredient", "serai"),
    (r"\bdaun\s*kari\b", "Daun Kari", "sayur", "ingredient", "daun kari"),
    (r"\bpandan\b", "Daun Pandan", "sayur", "ingredient", "daun pandan"),
    (r"\bdaun\s*sup\b", "Daun Sup", "sayur", "ingredient", "daun sup"),
    (r"\bdaun\s*bawang\b", "Daun Bawang", "sayur", "ingredient", "daun bawang"),
    (r"\blimau\s*purut\b", "Limau Purut", "sayur", "ingredient", "limau purut"),
    (r"\blimau\s*nipis\b", "Limau Nipis", "sayur", "ingredient", "limau nipis"),
    (r"\blimau\b", "Limau", "sayur", "ingredient", "limau"),
    (r"\btomato\b", "Tomato", "sayur", "ingredient", "tomato"),
    (r"\bkentang\b", "Kentang", "sayur", "ingredient", "ubi kentang"),
    (r"\blobak\s*merah\b", "Lobak Merah", "sayur", "ingredient", "lobak merah"),
    (r"\bcili\s*api\b|\bcili\s*padi\b", "Cili Api", "sayur", "ingredient",
     "cili api"),
    (r"\bcili\b", "Cili", "sayur", "ingredient", "cili merah"),
    (r"\bjagung\b", "Jagung", "sayur", "ingredient", "jagung manis"),
    (r"\bcendawan\b", "Cendawan", "sayur", "ingredient", "cendawan"),
    (r"\bbrokoli\b", "Brokoli", "sayur", "ingredient", "brokoli"),

    # ---------------- PROTEIN ----------------
    (r"\bdaging\s*kisar\b|\bdaging\s*cincang\b", "Daging Kisar", "protein",
     "ingredient", "daging kisar"),
    (r"\bdaging\b", "Daging", "protein", "ingredient", "daging lembu"),
    (r"\bayam\b", "Ayam", "protein", "ingredient", "ayam segar"),
    (r"\budang\b", "Udang", "protein", "ingredient", "udang"),
    (r"\bikan\b", "Ikan", "protein", "ingredient", "ikan segar"),
    (r"\bsotong\b", "Sotong", "protein", "ingredient", "sotong"),
    (r"\btelur\b", "Telur", "protein", "ingredient", "telur ayam"),
    (r"\btahu\b", "Tahu", "protein", "ingredient", "tahu"),
    (r"\btempe\b", "Tempe", "protein", "ingredient", "tempe"),

    # ---------------- DAIRY / BAKING ----------------
    (r"\bmentega\b|\bbutter\b", "Mentega", "dairy", "ingredient", "mentega"),
    (r"\bmarjerin\b", "Marjerin", "dairy", "ingredient", "marjerin"),
    (r"\bsusu\s*pekat\b", "Susu Pekat Manis", "dairy", "ingredient",
     "susu pekat manis"),
    (r"\bsusu\b", "Susu", "dairy", "ingredient", "susu segar"),
    (r"\bcream\s*cheese\b|\bkrim\s*keju\b", "Cream Cheese", "dairy",
     "ingredient", "cream cheese"),
    (r"\bwhipping\s*cream\b|\bkrim\b", "Whipping Cream", "dairy", "ingredient",
     "whipping cream"),
    (r"\bkeju\b", "Keju", "dairy", "ingredient", "keju cheddar"),
    (r"\byogurt\b", "Yogurt", "dairy", "ingredient", "yogurt"),
    (r"\bserbuk\s*penaik\b|\bbaking\s*powder\b", "Serbuk Penaik", "baking",
     "ingredient", "baking powder"),
    (r"\bsoda\s*bikarbonat\b|\bbaking\s*soda\b", "Soda Bikarbonat", "baking",
     "ingredient", "baking soda"),
    (r"\bvanila\b", "Esens Vanila", "baking", "ingredient", "esens vanila"),
    (r"\bagar-agar\b", "Agar-Agar", "baking", "ingredient", "agar-agar"),
    (r"\bgelatin\b", "Gelatin", "baking", "ingredient", "gelatin"),
    (r"\bragi\b|\byeast\b", "Ragi (Yeast)", "baking", "ingredient", "ragi"),
    (r"\bpewarna\b", "Pewarna Makanan", "baking", "ingredient", "pewarna makanan"),
    (r"\bgula\s*aising\b", "Gula Aising", "baking", "ingredient", "gula aising"),
    (r"\bkoko\b|\bcocoa\b", "Serbuk Koko", "baking", "ingredient", "serbuk koko"),
    (r"\bcoklat\b", "Coklat Masakan", "baking", "ingredient", "coklat masakan"),
    (r"\bhorlicks\b", "Horlicks", "minuman", "ingredient", "horlicks"),
    (r"\bmilo\b", "Milo", "minuman", "ingredient", "milo"),
    (r"\bnescafe\b|\bkopi\b", "Kopi / Nescafe", "minuman", "ingredient", "nescafe"),
    (r"\bsantan\b", "Santan", "ingredient", "ingredient", "santan"),
    (r"\bkelapa\s*parut\b", "Kelapa Parut", "ingredient", "ingredient",
     "kelapa parut"),
    (r"\bbadam\b|\balmond\b", "Badam", "ingredient", "ingredient", "badam"),
    (r"\bkismis\b", "Kismis", "ingredient", "ingredient", "kismis"),
    (r"\boreo\b", "Biskut Oreo", "ingredient", "ingredient", "oreo"),
    (r"\bbiskut\b", "Biskut", "ingredient", "ingredient", "biskut"),
    (r"\bminyak\b", "Minyak Masak", "ingredient", "ingredient", "minyak masak"),
]

COMPILED = [(re.compile(p, re.I), c, sub, kind, hint) for p, c, sub, kind, hint in TERMS]

# ===================================================== appliance suggestion rules
# recipe category / dish keyword -> suggested big-ticket machine
APPLIANCE_RULES = [
    (r"ais\s*krim|ice\s*cream|kulfi|gelato|sundae", "Ice Cream Maker / Mesin Aiskrim",
     "aiskrim"),
    (r"kek|cupcake|muffin|brownies|puding|tart|cheesecake|sponge|chiffon|lapis|bakar",
     "Oven Elektrik / Ketuhar", "kek-bakar"),
    (r"biskut|cookie|semperit|kuih raya|makmur", "Oven Elektrik + Mixer (Pengadun)",
     "biskut"),
    (r"roti|donut|donat|pau|bun|bagel|pizza", "Bread Maker / Mesin Roti", "roti"),
    (r"yogurt|yoghurt", "Yogurt Maker", "yogurt"),
    (r"waffle|pancake|lempeng", "Waffle Maker", "waffle"),
    (r"takoyaki", "Acuan Takoyaki", "takoyaki"),
    (r"mee|mi\b|kuetiau|pasta|bihun", "Mesin Pembuat Mee / Pasta Maker", "mee"),
    (r"jagung|grill|bbq|bakar|satay", "Grill Pan / Pemanggang Elektrik", "grill"),
    (r"sambal|cili|kisar|blend", "Blender / Pengisar", "blender"),
    (r"sup|rebus|stew|kari|rendang|kurma", "Pressure Cooker / Slow Cooker", "sup"),
    (r"nasi|biryani|lemak", "Rice Cooker (Periuk Nasi Elektrik)", "nasi"),
    (r"kukus|kuih|lapis|hokkaido", "Pengukus Elektrik (Steamer)", "kukus"),
    (r"goreng|gorengan|keropok", "Air Fryer / Deep Fryer", "goreng"),
    (r"kerepek|kering|jeruk|dehydrat", "Food Dehydrator", "dehydrator"),
    (r"ais|minuman|juice|smoothie|laici|bandung", "Blender + Ice Crusher", "minuman"),
    (r"bakar|roast|ayam golek", "Oven Konveksi / Air Fryer Oven", "bakar"),
]
APPLIANCE_RX = [(re.compile(p, re.I), name, key) for p, name, key in APPLIANCE_RULES]


def appliance_for(slug, dish, cat):
    blob = f"{slug} {dish} {cat}"
    out = []
    for rx, name, key in APPLIANCE_RX:
        if rx.search(blob):
            out.append((name, key))
    return out


# ============================================================ aggregation
agg = collections.defaultdict(lambda: {
    "recipes": set(), "mentions": 0, "aliases": collections.Counter(),
    "cats": collections.Counter(), "example": None, "field": set(),
})

CLEAN_RE = re.compile(r"[^\w\s%.\-]", re.U)
QTY_RE = re.compile(
    r"\b(?:\d+([.,]\d+)?|secubit|secawan|sudu\s*(?:besar|kecil|teh|makan)|"
    r"cawan|gelas|botol|paket|bungkus|ketul|biji|ulas|inci|keping|helai|"
    r"batang|ruas|genggam|tin|kotak|gram|kg|ml|liter|satu|dua|tiga|empat|"
    r"lima|enam|tujuh|lapan|sembilan|sepuluh|setengah|sukuan|separuh|"
    r"secukup\s*rasa|secukupnya|secukup|sedikit|sikit)\b", re.I)


def norm(s):
    s = s.lower()
    s = QTY_RE.sub(" ", s)
    s = CLEAN_RE.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


for slug, rec in DATA.items():
    meta = META[slug]
    cat = meta["cat"]
    seen = set()

    fields = {
        "ingredient": rec.get("ingredients") or [],
        "steps": rec.get("steps") or [],
        "tips": rec.get("tips") or [],
    }

    for field, lines in fields.items():
        for line in lines:
            low = line.lower()
            text = norm(line) if field == "ingredient" else low
            for rx, canon, sub, kind, hint in COMPILED:
                if not rx.search(text):
                    continue
                # equipment/appliance must come from steps or tips, not ingredients
                if kind in ("equipment", "appliance", "packaging") and field == "ingredient":
                    continue
                if canon in seen and field == "ingredient":
                    # allow same canonical from steps to add mention count
                    pass
                a = agg[canon]
                a["subcategory"] = sub
                a["kind"] = kind
                a["hint"] = hint
                a["mentions"] += 1
                a["recipes"].add(slug)
                a["aliases"][line.strip()[:70]] += 1
                a["cats"][cat] += 1
                a["field"].add(field)
                if a["example"] is None:
                    a["example"] = slug
                seen.add(canon)

print(f"keywords: {len(agg)}")

rows = []
for canon, a in agg.items():
    cat_top = a["cats"].most_common(1)[0][0] if a["cats"] else ""
    ex = a["example"]
    rows.append({
        "keyword": canon,
        "kind": a["kind"],
        "subcategory": a["subcategory"],
        "recipe_count": len(a["recipes"]),
        "mention_count": a["mentions"],
        "top_recipe_category": cat_top,
        "shopee_search": a["hint"],
        "example_recipe": META[ex]["dish"] if ex else "",
        "example_url": f"https://resepifesbuk.com/resepi/{ex}/" if ex else "",
        "source_fields": ", ".join(sorted(a["field"])),
        "aliases": "; ".join(x for x, _ in a["aliases"].most_common(3)),
    })

rows.sort(key=lambda r: (-r["recipe_count"], -r["mention_count"]))

# ===================================================== appliance suggestions
app_suggest = collections.defaultdict(lambda: {"recipes": [], "maker": ""})
for slug, rec in DATA.items():
    meta = META[slug]
    for name, key in appliance_for(slug, meta["dish"], meta["cat"]):
        app_suggest[name]["maker"] = key
        app_suggest[name]["recipes"].append((slug, meta["dish"], meta["cat"]))

app_rows = []
for name, d in app_suggest.items():
    n = len(d["recipes"])
    cats = collections.Counter(c for _, _, c in d["recipes"]).most_common(3)
    top = sorted(d["recipes"], key=lambda x: x[1])[:3]
    app_rows.append({
        "suggested_appliance": name,
        "matching_recipes": n,
        "pct_of_corpus": round(100 * n / len(DATA), 1),
        "top_recipe_categories": ", ".join(f"{c} ({k})" for c, k in cats),
        "example_recipe_1": top[0][1] if len(top) > 0 else "",
        "example_recipe_1_url": f"https://resepifesbuk.com/resepi/{top[0][0]}/" if len(top) > 0 else "",
        "example_recipe_2": top[1][1] if len(top) > 1 else "",
        "example_recipe_3": top[2][1] if len(top) > 2 else "",
    })
app_rows.sort(key=lambda r: -r["matching_recipes"])

json.dump(rows, open(OUT_JSON, "w"), ensure_ascii=False, indent=1)
json.dump(app_rows, open(BASE / "shopee_appliances.json", "w"), ensure_ascii=False, indent=1)
print("wrote", OUT_JSON.name, "and shopee_appliances.json")
print("appliance suggestions:", len(app_rows))
for r in app_rows[:8]:
    print("  ", r["matching_recipes"], r["suggested_appliance"])
