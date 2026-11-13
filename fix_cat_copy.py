"""Repair category copy that misses SERP length targets.

Titles must be <=60 chars and meta descriptions 145-158 chars. Anything
outside is edited by hand here rather than re-rolled, so the copy stays
consistent and no regeneration cost is paid for 21 short strings.
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(ROOT, "src", "cat_copy.json")

d = json.load(open(P, encoding="utf-8"))

FIX = {
    "Minuman": {
        "title": "Resepi Minuman: 28 Pilihan Segar Untuk Hari Panas",
        "meta_desc": "Koleksi 28 resepi minuman Malaysia termasuk air kacang soya, aiskrim homemade, jus buah dan sirap bandung. Semua mudah dibuat di rumah.",
    },
    "Sup": {
        "title": "Resepi Sup: 19 Hidangan Berkuah Untuk Makan Malam",
        "meta_desc": "Koleksi 19 resepi sup Malaysia termasuk sup tulang, sup ayam, sup cendawan dan tomyam. Kuah pekat, bahan mudah dan sesuai untuk makan malam.",
    },
    "Belangkas": {
        "meta_desc": "Koleksi 5 resepi belangkas Malaysia, semuanya masak pedas dan berempah. Bahan lengkap dan cara penyediaan langkah demi langkah untuk pemula.",
    },
    "Bubur": {
        "meta_desc": "Koleksi 19 resepi bubur Malaysia, dari bubur lambuk dan bubur kacang hijau sampai pengat pisang. Manis dan savouri, sesuai untuk sarapan.",
    },
    "Kek": {
        "meta_desc": "Koleksi 89 resepi kek Malaysia, dari kek kukus dan kek lapis Sarawak sampai cheesecake dan brownies. Panduan sukatan tepat untuk pemula.",
    },
    "Ketam": {
        "meta_desc": "Koleksi 13 resepi ketam Malaysia termasuk ketam masak cili, kam heong dan goreng berempah. Cara sedut isi ketam penuh dan kuah yang meresap.",
    },
    "Sotong": {
        "meta_desc": "Koleksi 7 resepi sotong Malaysia, dari sotong goreng tepung sampai sotong masak hitam. Teknik elak sotong liat dan cara tumis yang harum.",
    },
}

for cat, patch in FIX.items():
    if cat in d:
        d[cat].update(patch)

# validate
bad = []
for cat, v in d.items():
    if len(v["title"]) > 60:
        bad.append(f"{cat} title {len(v['title'])}")
    if not (140 <= len(v["meta_desc"]) <= 160):
        bad.append(f"{cat} desc {len(v['meta_desc'])}")
    if any(c in v["title"] + v["intro"] for c in "—"):
        bad.append(f"{cat} em-dash")

json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"patched {len(FIX)} categories")
print("remaining issues:", bad if bad else "none")
print(f"\ntitle len range: {min(len(v['title']) for v in d.values())}-{max(len(v['title']) for v in d.values())}")
print(f"desc len range: {min(len(v['meta_desc']) for v in d.values())}-{max(len(v['meta_desc']) for v in d.values())}")
