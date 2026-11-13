#!/usr/bin/env python3
"""Render the Shopee affiliate workbook (xlsx) from the extracted JSON."""
import json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE = Path(__file__).resolve().parent
rows = json.load(open(BASE / "shopee_keywords.json"))
apps = json.load(open(BASE / "shopee_appliances.json"))
data = json.load(open(BASE / "src/content_fix.json"))

OUT = Path.home() / "shopee_affiliate_keywords.xlsx"

NAVY = "1F3864"
TERRA = "C25E3A"
CREAM = "FDF6F0"
LIGHT = "F2F2F2"

hf = Font(bold=True, color="FFFFFF", size=10, name="Calibri")
hfill = PatternFill("solid", fgColor=NAVY)
tfill = PatternFill("solid", fgColor=TERRA)
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
wrap = Alignment(wrap_text=True, vertical="top")
num = Alignment(horizontal="center", vertical="center")


def style_header(ws, ncols, row=1, fill=hfill):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.fill = fill
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cell.border = border
    ws.row_dimensions[row].height = 32


def autosize(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


wb = Workbook()

# ---------------------------------------------------------------- 1. README
ws = wb.active
ws.title = "README"
ws.sheet_view.showGridLines = False
ws["A1"] = "Shopee Malaysia Affiliate — Keyword & Product Plan"
ws["A1"].font = Font(bold=True, size=16, color=NAVY)
ws["A2"] = "resepifesbuk.com · 748 recipes · BM recipe site"
ws["A2"].font = Font(size=11, italic=True, color=TERRA)

lines = [
    ("", ""),
    ("What this workbook is", ""),
    ("", "Every purchasable item mentioned inside the 748 published recipes, counted, "
         "normalised and ranked — so you know which affiliate links to place first."),
    ("", ""),
    ("How counts work", ""),
    ("", "recipe_count  = number of recipes that mention the item (unique recipes)."),
    ("", "mention_count = total mentions across the corpus (a recipe can say 'gula' 4x)."),
    ("", "Rank on recipe_count — that is reach. Use mention_count for intensity."),
    ("", ""),
    ("Where the signal comes from", ""),
    ("", "Ingredients are only comparable after normalising (qty, 'secukup rasa', dashes)."),
    ("", "Equipment/appliances are counted from STEPS + TIPS text, not ingredients —"),
    ("", "a recipe says 'panaskan kuali' but never lists kuali as an ingredient."),
    ("", ""),
    ("Sheets", ""),
    ("", "1. Keywords              — all 132 product keywords, ranked high→low"),
    ("", "2. Appliances            — machines suggested by recipe type"),
    ("", "3. Everyday Supplies     — the ~15 items that recur in almost every recipe"),
    ("", "4. Content-Affiliate Map — which recipes to put which link on"),
    ("", "5. Search Query Bank     — ready-to-paste Shopee search strings"),
    ("", "6. Method                — exact method + caveats"),
    ("", ""),
    ("Priority strategy", ""),
    ("", "1. Appliances first — highest commission per sale (RM80–600 per unit)."),
    ("", "2. Everyday supplies second — high volume, tiny commission, but they convert"),
    ("", "   on every page and cost you nothing to place."),
    ("", "3. Link the item ON the recipe that uses it — a 'kuali' link on a recipe that"),
    ("", "   says 'panaskan kuali' converts far better than a generic sidebar banner."),
]
r = 3
for a, b in lines:
    ws.cell(row=r, column=1, value=a).font = Font(bold=True, size=11, color=NAVY if a else "000000")
    ws.cell(row=r, column=2, value=b).alignment = Alignment(wrap_text=True, vertical="top")
    r += 1
ws.column_dimensions["A"].width = 26
ws.column_dimensions["B"].width = 92

# ---------------------------------------------------------------- 2. Keywords
ws = wb.create_sheet("Keywords")
ws.sheet_view.showGridLines = False
heads = ["Rank", "Keyword (product)", "Type", "Sub-category",
         "Recipe count", "Mention count", "Coverage %",
         "Top recipe category", "Shopee search string",
         "Example recipe", "Source", "Variants seen in recipes"]
ws.append(heads)
style_header(ws, len(heads))

total = len(data)
for i, x in enumerate(rows, start=1):
    ws.append([
        i, x["keyword"], x["kind"], x["subcategory"],
        x["recipe_count"], x["mention_count"],
        round(100 * x["recipe_count"] / total, 1),
        x["top_recipe_category"], x["shopee_search"],
        x["example_recipe"], x["source_fields"], x["aliases"],
    ])

autosize(ws, [6, 30, 12, 16, 10, 10, 11, 20, 26, 34, 16, 44])
for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
    for c in row:
        c.border = border
        c.font = Font(size=9)
        if c.column in (1, 5, 6, 7):
            c.alignment = num
        elif c.column in (2, 10, 12, 9):
            c.alignment = wrap
    if row[0].row % 2 == 0:
        for c in row:
            c.fill = PatternFill("solid", fgColor="F7F9FC")
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:{get_column_letter(len(heads))}{ws.max_row}"

# colour-code type
TYPECOL = {"appliance": "FFE0B2", "equipment": "C8E6C9",
           "packaging": "E1BEE7", "ingredient": "FFFFFF"}
for i, x in enumerate(rows, start=2):
    ws.cell(row=i, column=3).fill = PatternFill("solid", fgColor=TYPECOL.get(x["kind"], "FFFFFF"))

# ---------------------------------------------------------------- 3. Appliances
ws = wb.create_sheet("Appliances")
ws.sheet_view.showGridLines = False
ws["A1"] = "Machines & appliances suggested by recipe type"
ws["A1"].font = Font(bold=True, size=14, color=NAVY)
ws["A2"] = ("Ranked by how many recipes in the corpus would justify owning the machine. "
            "Highest affiliate value — RM80–600 per unit sale.")
ws["A2"].font = Font(size=10, italic=True, color=TERRA)
ws["A2"].alignment = Alignment(wrap_text=True)
ws.merge_cells("A2:J2")
ws.row_dimensions[2].height = 30

heads = ["Rank", "Suggested appliance", "Matching recipes", "% of corpus",
         "Top recipe categories", "Example recipe 1", "Example recipe 2",
         "Example recipe 3", "URL (example 1)", "Notes"]
ws.append([])
ws.append(heads)
hdr = ws.max_row
style_header(ws, len(heads), row=hdr)

NOTES = {
    "Oven Elektrik / Ketuhar": "Covers cakes, cookies, baked kuih, roasts. Mid-range RM200–500.",
    "Pengukus Elektrik (Steamer)": "Kuih, pau, dim sum. Cheap entry RM40–120.",
    "Bread Maker / Mesin Roti": "Roti, donut, pau, pizza. RM150–400.",
    "Oven Elektrik + Mixer (Pengadun)": "Bundle upsell — cookies need both. High basket value.",
    "Air Fryer / Deep Fryer": "Trending MY item. Very high search volume on Shopee.",
    "Rice Cooker (Periuk Nasi Elektrik)": "Near-universal household item, low commission but huge volume.",
    "Pressure Cooker / Slow Cooker": "Rendang, kari, sup. RM100–350.",
    "Blender / Pengisar": "Sambal, cili kisar, smoothies. RM80–300.",
}
total = len(data)
for i, a in enumerate(apps, start=1):
    ws.append([
        i, a["suggested_appliance"], a["matching_recipes"], a["pct_of_corpus"],
        a["top_recipe_categories"], a["example_recipe_1"], a["example_recipe_2"],
        a["example_recipe_3"], a["example_recipe_1_url"],
        NOTES.get(a["suggested_appliance"], ""),
    ])
autosize(ws, [6, 34, 11, 10, 34, 30, 30, 30, 46, 44])
for row in ws.iter_rows(min_row=hdr + 1, max_row=ws.max_row):
    for c in row:
        c.border = border
        c.font = Font(size=9)
        if c.column in (1, 3, 4):
            c.alignment = num
        else:
            c.alignment = wrap
ws.freeze_panes = f"A{hdr+1}"
ws.auto_filter.ref = f"A{hdr}:{get_column_letter(len(heads))}{ws.max_row}"

# ---------------------------------------------------------------- 4. Supplies
ws = wb.create_sheet("Everyday Supplies")
ws.sheet_view.showGridLines = False
ws["A1"] = "Everyday supplies — appears in most recipes"
ws["A1"].font = Font(bold=True, size=14, color=NAVY)
ws["A2"] = ("These recur across the whole corpus. Low commission per sale, but they convert "
            "on every single page. Place them as inline text links, not banners.")
ws["A2"].font = Font(size=10, italic=True, color=TERRA)
ws["A2"].alignment = Alignment(wrap_text=True)
ws.merge_cells("A2:F2")
ws.row_dimensions[2].height = 30

heads = ["Rank", "Supply", "Recipes using it", "% of all recipes",
         "Mentions", "Shopee search"]
ws.append([])
ws.append(heads)
hdr = ws.max_row
style_header(ws, len(heads), row=hdr)

core = [x for x in rows if x["recipe_count"] >= 60 and x["kind"] == "ingredient"]
for i, x in enumerate(core, start=1):
    ws.append([i, x["keyword"], x["recipe_count"],
               round(100 * x["recipe_count"] / total, 1),
               x["mention_count"], x["shopee_search"]])
autosize(ws, [6, 32, 16, 16, 12, 30])
for row in ws.iter_rows(min_row=hdr + 1, max_row=ws.max_row):
    for c in row:
        c.border = border
        c.font = Font(size=10)
        if c.column in (1, 3, 4, 5):
            c.alignment = num
ws.freeze_panes = f"A{hdr+1}"

# ---------------------------------------------------------------- 5. Content map
ws = wb.create_sheet("Content-Affiliate Map")
ws.sheet_view.showGridLines = False
ws["A1"] = "Which link goes on which recipe"
ws["A1"].font = Font(bold=True, size=14, color=NAVY)
ws["A2"] = ("Every equipment/appliance keyword, the recipes that mention it, and the "
            "exact URL to place the link on. This is your placement list.")
ws["A2"].font = Font(size=10, italic=True, color=TERRA)
ws.merge_cells("A2:E2")
ws.row_dimensions[2].height = 26

heads = ["Product to link", "Type", "Recipe that mentions it", "Recipe URL", "Mention text"]
ws.append([])
ws.append(heads)
hdr = ws.max_row
style_header(ws, len(heads), row=hdr)

import re
META = {}
cats = json.load(open(BASE / "src/cats.json"))
for slug in data:
    v = cats.get(slug) or {}
    META[slug] = v.get("dish") or slug

PLACE = [
    (r"\bkuali\b", "Kuali"),
    (r"\bperiuk\b", "Periuk"),
    (r"\boven\b|\bketuhar\b", "Oven / Ketuhar"),
    (r"\bloyang\b", "Loyang / Acuan Kek"),
    (r"\bblender\b", "Blender"),
    (r"\bpengukus\b|\bkukus\b", "Pengukus (Kukusan)"),
    (r"\bpisau\b", "Pisau Dapur"),
    (r"\bmixer\b|\bpengadun\b", "Mixer / Pengadun"),
    (r"\bair\s*fryer\b", "Air Fryer"),
    (r"\brice\s*cooker\b|\bperiuk\s*nasi\b", "Rice Cooker"),
    (r"\bparut\b", "Pemarut (Grater)"),
    (r"\blesung\b", "Lesung Batu"),
    (r"\btalenan\b|\bpapan\s*pemotong\b", "Papan Pemotong"),
]
PRX = [(re.compile(p, re.I), n) for p, n in PLACE]

seen_pairs = set()
map_rows = []
for slug, rec in data.items():
    blob_lines = (rec.get("steps") or []) + (rec.get("tips") or [])
    blob = " ".join(blob_lines)
    for rx, name in PRX:
        if not rx.search(blob):
            continue
        key = (name, slug)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        snippet = ""
        for ln in blob_lines:
            if rx.search(ln):
                snippet = ln.strip()[:110]
                break
        map_rows.append((name, "equipment", slug, snippet))

map_rows.sort(key=lambda x: (x[0], x[2]))
for name, typ, slug, snippet in map_rows:
    ws.append([name, typ, META.get(slug, slug),
               f"https://resepifesbuk.com/resepi/{slug}/", snippet])
autosize(ws, [26, 12, 42, 52, 62])
for row in ws.iter_rows(min_row=hdr + 1, max_row=ws.max_row):
    for c in row:
        c.border = border
        c.font = Font(size=9)
        c.alignment = wrap
ws.freeze_panes = f"A{hdr+1}"
ws.auto_filter.ref = f"A{hdr}:{get_column_letter(len(heads))}{ws.max_row}"
print("content map rows:", len(map_rows))

# ---------------------------------------------------------------- 6. Search bank
ws = wb.create_sheet("Search Query Bank")
ws.sheet_view.showGridLines = False
ws["A1"] = "Ready-to-paste Shopee search strings"
ws["A1"].font = Font(bold=True, size=14, color=NAVY)
ws["A2"] = "Copy these into Shopee MY search to find products for the affiliate link."
ws["A2"].font = Font(size=10, italic=True, color=TERRA)

heads = ["Priority", "Product", "Type", "Shopee search string (BM)", "Alt search (EN)"]
ws.append([])
ws.append(heads)
hdr = ws.max_row
style_header(ws, len(heads), row=hdr)

EN = {
    "Kuali": "frying pan", "Periuk": "cooking pot", "Oven / Ketuhar": "electric oven",
    "Loyang / Acuan Kek": "cake mould", "Blender": "kitchen blender",
    "Pengukus (Kukusan)": "steamer pot", "Pisau Dapur": "kitchen knife",
    "Mixer / Pengadun": "hand mixer", "Air Fryer": "air fryer",
    "Rice Cooker (Periuk Nasi Elektrik)": "rice cooker",
    "Pemarut (Grater)": "cheese grater", "Lesung Batu": "stone mortar",
    "Papan Pemotong / Talenan": "chopping board",
    "Ice Cream Maker": "ice cream maker", "Bread Maker / Mesin Roti": "bread maker",
    "Pengukus Elektrik (Electric Steamer)": "electric steamer",
    "Pressure Cooker": "pressure cooker", "Slow Cooker": "slow cooker",
    "Waffle Maker": "waffle maker", "Yogurt Maker": "yogurt maker",
    "Electric Kettle": "electric kettle", "Toaster": "toaster",
    "Grill Pan / Pemanggang": "grill pan", "Microwave": "microwave oven",
    "Minyak Masak": "cooking oil", "Garam": "salt", "Gula": "sugar",
    "Sos Cili": "chili sauce", "Sos Tiram": "oyster sauce",
    "Kicap": "soy sauce", "Tepung Gandum": "wheat flour",
}

prio = {"appliance": "1 - HIGH", "equipment": "2 - MEDIUM", "packaging": "3 - LOW",
        "ingredient": "4 - VOLUME"}
bank = sorted(rows, key=lambda x: (prio.get(x["kind"], "9"), -x["recipe_count"]))
for x in bank:
    ws.append([prio.get(x["kind"], ""), x["keyword"], x["kind"],
               x["shopee_search"], EN.get(x["keyword"], x["shopee_search"])])
autosize(ws, [12, 34, 12, 34, 30])
for row in ws.iter_rows(min_row=hdr + 1, max_row=ws.max_row):
    for c in row:
        c.border = border
        c.font = Font(size=9)
        c.alignment = wrap
ws.freeze_panes = f"A{hdr+1}"
ws.auto_filter.ref = f"A{hdr}:{get_column_letter(len(heads))}{ws.max_row}"

# ---------------------------------------------------------------- 7. Method
ws = wb.create_sheet("Method")
ws.sheet_view.showGridLines = False
ws["A1"] = "Method & caveats"
ws["A1"].font = Font(bold=True, size=14, color=NAVY)
m = [
    ("Corpus", "748 published recipes from src/content_fix.json (the file that generates the live site)."),
    ("Ingredient scan", "Every ingredient line, lowercased, quantities stripped "
                        "(numbers, secubit, sudu besar, secukup rasa ...), then matched "
                        "against an ordered product dictionary (most specific first)."),
    ("Equipment scan", "Steps + tips text only. Ingredient lists almost never mention "
                       "cookware, so counting equipment from ingredients would undercount badly."),
    ("Deduplication", "A recipe counts once per product even if it says 'gula' four times. "
                      "mention_count still records all four."),
    ("Threshold", "132 keywords survived. Very rare one-off items were dropped from ranking "
                  "but remain in the corpus."),
    ("Caveat 1", "Counts measure MENTION, not purchase intent. 'Air' (water) appears in "
                 "hundreds of recipes but is not an affiliate opportunity — ignored."),
    ("Caveat 2", "Generic 'Bawang', 'Cili' etc. aggregate several variants (merah/besar/api "
                 "are split out separately where the text supports it)."),
    ("Caveat 3", "Appliance suggestions are a heuristic mapping recipe-type → machine "
                 "(aiskrim→ice cream maker). They are marketing suggestions, not claims "
                 "that the recipe requires the machine."),
    ("Caveat 4", "Commission rates are set by Shopee and change. Verify the current rate in "
                 "the Shopee Affiliate dashboard before pricing a campaign."),
    ("Rebuild", "python3 shopee_keywords.py && python3 shopee_xlsx.py"),
]
r = 3
for a, b in m:
    ws.cell(row=r, column=1, value=a).font = Font(bold=True, size=10, color=NAVY)
    c = ws.cell(row=r, column=2, value=b)
    c.alignment = Alignment(wrap_text=True, vertical="top")
    c.font = Font(size=10)
    r += 1
ws.column_dimensions["A"].width = 22
ws.column_dimensions["B"].width = 100

wb.save(OUT)
print("saved:", OUT)
print("sheets:", wb.sheetnames)
print("keyword rows:", len(rows))
