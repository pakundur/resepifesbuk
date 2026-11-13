"""Dish-led category classifier for resepifesbuk.

Blogger labels are dirty: 85 posts carry a category with zero supporting
evidence (bread tagged 'Daging', mango sticky rice tagged 'Mee'). This module
replaces them with rules that answer one question: WHAT IS THE RECIPE FOR?

Design:
  - PRIMARY  = decided by TITLE first (title states the dish), ingredient
               fallback only when the title is silent.
  - SECONDARY = protein/technique cues found in ingredients, capped at 3.
  - Ingredient scans alone are NOT trusted for the primary: 'ikan bilis' is a
    condiment in most sambals, so a naive scan files half the sambal corpus as
    a fish dish. 28 of 68 'ikan' hits were bilis/masin only.

Usage:  python categorize.py [--csv] [--apply]
"""
import json, re, os, sys, csv, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")

# Ordered: first match wins. Most specific families first so that
# 'kek lapis' -> Kek (not Kuih) and 'biskut tart nenas' -> Biskut (not Kuih).
RULES = [
    ("Biskut", r"\b(biskut|biscuit|cookies?|semperit|tart nenas|almond london|cornflakes?|"
               r"makmur|honey corn|nestum|swiss tart|egg tart|macaroon|congo bars|bar\b|truffles)\b"),
    ("Kek", r"\b(kek\b|cake|brownies?|cheesecake|muffin|cupcake|chiffon|sponge|shortcake|"
            r"pavlova|creme brulee|creme brule|swiss roll|fruit cake|butter cake)\b"),
    ("Kuih", r"\b(kuih|talam|onde[- ]?onde|bingka|karipap|popia|apam|bahulu|cucur|kaswi|sago|"
             r"hoen kwe|seri muka|kuih lapis|kuba|mochi|putu|tepung pelita|wajik|dodol|lepat|"
             r"badak berendam|getuk|tepung bungkus|tosei|dorayaki|takoyaki|churros|cakoi|seri ayu)\b"),
    ("Bubur", r"\b(bubur|porridge|pengat|pulut hitam|bubur lambuk)\b"),
    # Puding/kastard/telur dishes must resolve BEFORE Minuman, else 'susu' in the
    # ingredient list files a plate of puding pisang as a drink.
    ("Puding", r"\b(puding|pudding|kastard|custard|karamel|caramel)\b"),
    ("Kuih", r"\b(cream horn|telur dadar|omelette|telur matahari|keledek ketuk|"
             r"chocolate rice bubble|cornflake madu|keju blueberry)\b"),
    # Bare 'air' is too greedy ('air asam', 'air fryer'); require a drink word around it.
    ("Minuman", r"\b(minuman|jus\b|juice|teh\b|kopi|milo|smoothie|sirap|laici|cendol|"
                r"aiskrim|milkshake|mocktail|mojito|bandung|taufufa|dagolna|koktail|katira|"
                r"air\s+(kelapa|tebu|bandung|laici|limau|manggis|sirap|soya|jagung|kacang|"
                r"buah|naga|mata|kucing|batu))\b"),
    ("MiNoodles", r"\b(mee\b|mee |bihun|mihun|laksa|laksam|maggi|pasta|spaghetti|kuey teow|"
                  r"kwetiau|jjajangmyeon|kolok|soto|yee mee|wantan|char kway|fettucine|macaroni|"
                  r"makaroni|lasagna|lasagne|suhun|mee hoon|tomyam)\b"),
    ("Roti", r"\b(roti|bread|pau\b|bun\b|donut|bomboloni|canai|naan|toast|pizza|pide|bagel|"
             r"croissant|wrap|lempeng|capati|sandwich|scone|pancake|murtabak|cheesy boat|"
             r"dim sum|sushi|yong tau fu)\b"),
    ("Nasi", r"\b(nasi|beriani|briyani|pulut\b|ketupat|lemang|lontong)\b"),
    ("Sup", r"\b(sup\b|soup|bakso|gear box)\b"),
    ("Sambal", r"\b(sambal|sos\b|sauce|kuah shell out|chutney|acar|kimchi|serunding)\b"),
    ("Belangkas", r"\b(belangkas)\b"),
    ("Perut", r"\b(perut|paru|tetel|usus|babat)\b"),
    ("Ketam", r"\b(ketam|crab|lobster)\b"),
    ("Sotong", r"\b(sotong|squid)\b"),
    ("Udang", r"\b(udang|prawn|shrimp)\b"),
    ("Kerang / Kupang / Lala / Siput", r"\b(kerang|kupang|lala|siput|sedut)\b"),
    ("Ikan", r"\b(ikan|fish|tenggiri|kembung|sardin|kerisi|senangin|bawal|selar|tilapia|keli|"
             r"siakap|pari|tongkol|tuna|cencaru|salmon|dory|patin|botok)\b"),
    ("Ayam", r"\b(ayam|chicken)\b"),
    ("Daging", r"\b(daging|beef|kambing|lembu|mutton|lamb|rendang|dendeng|bistik|steak|burger|"
               r"sosej|meatball)\b"),
    ("Sayur", r"\b(sayur|kangkung|sawi|kobis|terung|bendi|pucuk|kailan|brokoli|labu|ubi|bayam|"
              r"cendawan|petola|timun|salad|taugeh|jagung|betik|nangka|dhal|dalca|paprik|tempe|"
              r"tauhu|kerabu|ulaman|ulam)\b"),
]

# Protein cues for SECONDARY tags only (never the primary).
# A secondary protein tag is only awarded when the protein appears in the
# INGREDIENT LIST (not the title or method) — otherwise 'ayam' in a step
# sentence tags a beef rendang as chicken too, and vice versa.
PROTEIN_SECONDARY = [
    ("Ayam", r"\bayam\b"),
    ("Daging", r"\b(daging|kambing|lembu)\b"),
    ("Udang", r"\budang\b"),
    ("Sotong", r"\bsotong\b"),
    ("Ketam", r"\bketam\b"),
    ("Ikan", r"\b(ikan|tenggiri|kembung|sardin)\b"),
    ("Kerang / Kupang / Lala / Siput", r"\b(kerang|lala|siput|kupang)\b"),
]

# Technique categories only earn a secondary slot when the title says so.
TECH_SECONDARY = [("Sup", r"\b(sup|soup)\b"), ("Sambal", r"\b(sambal|sos|sauce)\b")]


def _body(r):
    """Ingredients + method, used only as a last-resort primary fallback."""
    steps = r["steps"]
    return " ".join(r["ingredients"] + [s.get("t", "") + s.get("h", "") for s in steps]).lower()


def _ingredients_only(r):
    """Ingredient list only. Method text is deliberately excluded from tag
    decisions — a step like 'masukkan daging' appears in dozens of unrelated
    recipes, so scanning it over-tags beef onto chicken and bread dishes."""
    return " ".join(r["ingredients"]).lower()


def classify(r):
    title = r["title"].lower()
    body = _body(r)
    ings = _ingredients_only(r)
    hay = title + " " + body

    hits = [cat for cat, rx in RULES if re.search(rx, title)]
    source = "title"
    if not hits:
        hits = [cat for cat, rx in RULES if re.search(rx, hay)]
        source = "ingredients"
    if not hits:
        hits = ["Sayur"]
        source = "fallback"

    primary = hits[0]
    secondary = []
    for cat, rx in PROTEIN_SECONDARY:
        if cat != primary and cat not in secondary and re.search(rx, ings):
            secondary.append(cat)
    for cat, rx in TECH_SECONDARY:
        if cat != primary and cat not in secondary and re.search(rx, title):
            secondary.append(cat)

    return primary, secondary[:3], source


def main():
    recs = json.load(open(SRC, encoding="utf-8"))
    out = []
    for r in recs:
        primary, secondary, source = classify(r)
        out.append({
            "slug": r["slug"],
            "title": r["title"],
            "old_cats": r["cats"],
            "primary": primary,
            "secondary": secondary,
            "decided_by": source,
            "changed": (not r["cats"]) or (r["cats"][0] != primary),
        })

    if "--csv" in sys.argv:
        path = os.path.join(ROOT, "category_review.csv")
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["slug", "title", "old_categories", "new_primary",
                        "new_secondary", "decided_by", "changed"])
            for x in out:
                w.writerow([x["slug"], x["title"], " | ".join(x["old_cats"]),
                            x["primary"], " | ".join(x["secondary"]),
                            x["decided_by"], "YES" if x["changed"] else ""])
        print(f"review CSV -> {path}")

    if "--apply" in sys.argv:
        by_slug = {x["slug"]: x for x in out}
        for r in recs:
            m = by_slug[r["slug"]]
            r["cats"] = [m["primary"]] + m["secondary"]
        json.dump(recs, open(SRC, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"applied categories to {len(recs)} recipes -> {SRC}")

    c = collections.Counter(x["primary"] for x in out)
    print(f"\n{len(out)} recipes")
    print(f"changed primary: {sum(1 for x in out if x['changed'])}")
    print(f"decided by title: {sum(1 for x in out if x['decided_by']=='title')}")
    print(f"decided by ingredients: {sum(1 for x in out if x['decided_by']=='ingredients')}")
    print(f"fallback: {sum(1 for x in out if x['decided_by']=='fallback')}\n")
    for k, n in c.most_common():
        print(f"  {n:4d}  {k}")


if __name__ == "__main__":
    main()
