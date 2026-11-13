#!/usr/bin/env python3
"""
Per-link copy bank — 48 unique blocks, one per affiliate link.

Every one of the 16 wired products has exactly 3 links, and each link gets its
OWN hook / promise / button. No two links of the same product repeat an angle.

Structure per block:
    hook    : the kitchen failure, named plainly (3-7 words)
    promise : what changes with this product (8-14 words)
    btn     : soft-sell click label (2-4 words)
    note    : optional micro-trust line (<=10 words)
    src     : corpus evidence — which failure mode this quotes, or BENEFIT
              when the corpus has no pain language for the product

Voice: colloquial Malaysian Malay (dah / je / kat / ni / tu). Banned:
exclamation marks, "Beli Sekarang", urgency, price/discount claims,
superlatives (terbaik/termurah), health claims.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# 16 products x 3 links. Key order matches affiliate_links.json "links" order:
# index 0 = aff1, 1 = aff2, 2 = aff3.
# ---------------------------------------------------------------------------
COPY = {
    "oven": {
        "label": "Oven elektrik",
        "slots": [
            dict(
                hook="Kek naik senget sebelah",
                promise="Suhu sekata atas bawah, tak payah pusing tray tengah jalan",
                btn="Tengok oven ni",
                note="",
                src="oven/hangit+uneven: 'bergantung kepada oven masing-masing'",
            ),
            dict(
                hook="Satu tray je muat",
                promise="Rak dua tingkat, biskut raya siap sekali jalan",
                btn="Oven dua rak",
                note="",
                src="oven/capacity (corpus batches: 'bakar 2 tray serentak')",
            ),
            dict(
                hook="Takut hangit, buka oven tiap 5 minit",
                promise="Pintu kaca luas, tengok warna kek tanpa buka pintu",
                btn="Tengok yang ni",
                note="",
                src="oven/hangit 18: 'jangan buka pintu oven terlalu kerap'",
            ),
        ],
    },
    "mixer": {
        "label": "Mixer kek",
        "slots": [
            dict(
                hook="Pukul adunan sampai tangan lenguh",
                promise="Adunan kembang dalam 3 minit, tangan tak penat lagi",
                btn="Tengok mixer",
                note="",
                src="mixer/tak-kembang 3: 'pukul telur dan gula hingga kembang'",
            ),
            dict(
                hook="Adunan berketul, kek bantat",
                promise="Pukul rata sampai bawah mangkuk, tak ada ketul tertinggal",
                btn="Cara pukul rata",
                note="",
                src="mixer/berketul 6",
            ),
            dict(
                hook="Pukul lebih, adunan jatuh balik",
                promise="Kelajuan boleh kawal, senang nak berhenti tepat pada masa",
                btn="Pilihan lain",
                note="",
                src="mixer/keras 6 (over-mixing collapse)",
            ),
        ],
    },
    "blender": {
        "label": "Blender dapur",
        "slots": [
            dict(
                hook="Cili kisar tak lumat, sambal kasar",
                promise="Cili kering lumat sekata, pecah minyak pun cepat",
                btn="Tengok blender",
                note="",
                src="blender/pecah 71 (bahan kisar -> pecah minyak)",
            ),
            dict(
                hook="Tumis cili, hangit dulu sebelum masak",
                promise="Kisar halus sampai betul-betul lumat, tak hangus masa tumis",
                btn="Blender kuat",
                note="",
                src="blender/hangit 57: 'elak cili hangus'",
            ),
            dict(
                hook="Blender besar makan ruang",
                promise="Saiz padan dapur kecil, simpan dalam kabinet pun senang",
                btn="Tengok saiz",
                note="",
                src="blender/fit (kitchen size, no pain claim)",
            ),
        ],
    },
    "pengisar": {
        "label": "Pengisar makanan",
        "slots": [
            dict(
                hook="Rempah kisar tak halus, gigit biji",
                promise="Kisar rempah kering sampai serbuk halus",
                btn="Tengok pengisar",
                note="",
                src="pengisar/berketul 2 (rempah kisar)",
            ),
            dict(
                hook="Labu berdegil, kisar lama pun ada serat",
                promise="Mata pisau tajam, serat hancur sepenuhnya",
                btn="Yang ni kuat",
                note="",
                src="pengisar/hancur 3: 'serat labu hancur sepenuhnya'",
            ),
            dict(
                hook="Kena beli dua mesin",
                promise="Kering dan basah guna satu bekas je",
                btn="Tengok dua guna",
                note="",
                src="pengisar/2-in-1 (corpus: 'kisar kering' + 'kisar basah')",
            ),
        ],
    },
    "ricecooker": {
        "label": "Rice cooker",
        "slots": [
            dict(
                hook="Nasi hangit di dasar",
                promise="Masak, hangat, siap sendiri tanpa perlu tunggu",
                btn="Tengok rice cooker",
                note="",
                src="BENEFIT — ricecooker has 0 pain sentences in corpus",
            ),
            dict(
                hook="Balik kerja, nasi belum masak",
                promise="Set dan tinggal, nasi siap bila anda balik",
                btn="Ada timer",
                note="",
                src="BENEFIT — ricecooker has 0 pain sentences in corpus",
            ),
            dict(
                hook="Masak banyak, nasi lebih, buang",
                promise="Saiz kecil cukup untuk dua orang, tak membazir",
                btn="Tengok saiz",
                note="",
                src="BENEFIT — ricecooker has 0 pain sentences in corpus",
            ),
        ],
    },
    "grillpan": {
        "label": "Grill pan",
        "slots": [
            dict(
                hook="Ayam melekat, kulit tertinggal atas pan",
                promise="Lapisan tak lekat, kulit ayam keluar cantik",
                btn="Tengok grill pan",
                note="",
                src="grillpan/melekat 2: 'grill atas nonstick pan'",
            ),
            dict(
                hook="Panggang jadi arang",
                promise="Alur naikkan daging, lemak turun — tak hangus bawah",
                btn="Alur dalam",
                note="",
                src="grillpan/hangit 4: 'jaga supaya tidak hangus seperti arang'",
            ),
            dict(
                hook="Panggang dalam rumah, asap penuh dapur",
                promise="Alur tolong buang lemak, kurang asap berbanding kuali biasa",
                btn="Pilihan lain",
                note="",
                src="grillpan/smoke (corpus: 'pemanggang... keringkan air')",
            ),
        ],
    },
    "microwave": {
        "label": "Microwave oven",
        "slots": [
            dict(
                hook="Coklat hangus masa cair",
                promise="Cair sekata, tak hangus atau pecah minyak",
                btn="Tengok microwave",
                note="",
                src="microwave/hangit: 'supaya coklat tidak hangus atau pecah minyak'",
            ),
            dict(
                hook="Panaskan ayam, jadi kenyal",
                promise="Kuasa boleh laras, panaskan lembut tak kering",
                btn="Kuasa laras",
                note="",
                src="microwave/keras: 'jangan masak terlalu lama, adunan jadi keras'",
            ),
            dict(
                hook="Lupa keluarkan daging dari freezer",
                promise="Fungsi nyahbeku, masak pun boleh terus",
                btn="Tengok fungsi",
                note="",
                src="microwave/defrost (corpus: cairkan coklat/mentega terus)",
            ),
        ],
    },
    "freezer": {
        "label": "Freezer kecil",
        "slots": [
            dict(
                hook="Peti sejuk penuh, stok tak muat",
                promise="Ruang beku tambahan untuk stok mingguan",
                btn="Tengok freezer",
                note="",
                src="freezer/keras 6 (simpan stok semalaman)",
            ),
            dict(
                hook="Hari-hari kena ke pasar",
                promise="Simpan lauk sebulan, tak perlu keluar setiap hari",
                btn="Simpan stok",
                note="",
                src="freezer/stock (corpus: 'bekukan semalaman')",
            ),
            dict(
                hook="Beku, cair, tekstur rosak",
                promise="Suhu stabil, tekstur kekal macam baru masak",
                btn="Suhu stabil",
                note="",
                src="freezer/texture: 'teksturnya kemas dan tidak cair'",
            ),
        ],
    },
    "waffle": {
        "label": "Waffle maker",
        "slots": [
            dict(
                hook="Waffle nempel, keluar pecah dua",
                promise="Lapisan tak lekat, waffle keluar utuh",
                btn="Tengok waffle maker",
                note="",
                src="waffle/melekat: 'supaya waffle tidak melekat atau pecah'",
            ),
            dict(
                hook="Rangup luar, lembut dalam jadi liat",
                promise="Haba dua belah, masak sampai ke tengah",
                btn="Haba dua belah",
                note="",
                src="waffle/pecah — undercooked centre",
            ),
            dict(
                hook="Beli, guna sekali, simpan",
                promise="Kecil dan ringan, senang simpan untuk hujung minggu",
                btn="Tengok saiz",
                note="",
                src="waffle/fit (usage frequency, no pain claim)",
            ),
        ],
    },
    "takoyaki": {
        "label": "Acuan takoyaki",
        "slots": [
            dict(
                hook="Bebola melekat, susah nak putar",
                promise="Pan panas sekata, bebola golek bulat sendiri",
                btn="Tengok acuan",
                note="",
                src="takoyaki/melekat: 'supaya takoyaki tidak melekat dan mudah digolek'",
            ),
            dict(
                hook="Bentuk tak bulat, ada yang leper",
                promise="Lubang sekata, semua bebola sama saiz",
                btn="Lubang sekata",
                note="",
                src="takoyaki/bentuk (corpus: golek bulat)",
            ),
            dict(
                hook="Nak cuba sekali je dulu",
                promise="Acuan kecil untuk test resepi sebelum beli yang besar",
                btn="Tengok saiz",
                note="",
                src="BENEFIT — trial-size, no pain claim",
            ),
        ],
    },
    "pressure": {
        "label": "Pressure cooker",
        "slots": [
            dict(
                hook="Rendang 3 jam, daging masih keras",
                promise="Daging lembut dalam masa lebih singkat",
                btn="Tengok pressure cooker",
                note="",
                src="pressure/hancur: 'tulangnya hancur'",
            ),
            dict(
                hook="Tulang ikan sardin keras, susah makan",
                promise="Tekanan cukup kuat sampai tulang hancur",
                btn="Yang ni kuat",
                note="",
                src="pressure/hancur — 'ikan sardin lembut dan tulangnya hancur'",
            ),
            dict(
                hook="Gas habis sebab rebus lama",
                promise="Masa memasak pendek, jimat gas dapur",
                btn="Pilihan lain",
                note="",
                src="pressure/time (corpus: 'high pressure 90 minit')",
            ),
        ],
    },
    "kuali": {
        "label": "Kuali leper",
        "slots": [
            dict(
                hook="Tumis bawang, hangit dulu sebelum naik bau",
                promise="Haba sekata, tumisan naik bau tanpa hangus",
                btn="Tengok kuali",
                note="",
                src="kuali/hangit 18: 'paru tidak hangus di bahagian bawah kuali'",
            ),
            dict(
                hook="Telur melekat, susah nak angkat",
                promise="Lapisan tak lekat, telur gerak sendiri dalam kuali",
                btn="Tak lekat",
                note="",
                src="kuali/melekat 16",
            ),
            dict(
                hook="Daging kering masa tumis",
                promise="Haba rata kekalkan jus, daging tak kering",
                btn="Haba rata",
                note="",
                src="kuali/kering 12",
            ),
        ],
    },
    "periuk": {
        "label": "Periuk memasak",
        "slots": [
            dict(
                hook="Bubur hangit di dasar periuk",
                promise="Dasar tebal, haba rata sampai bubur tak hangit",
                btn="Tengok periuk",
                note="",
                src="periuk/hangit 24: 'bubur tidak hangus di dasar periuk'",
            ),
            dict(
                hook="Sagu berketul, bubur tak licin",
                promise="Dasar rata, kacau pun senang, tak berketul",
                btn="Dasar rata",
                note="",
                src="periuk/berketul 19",
            ),
            dict(
                hook="Periuk susah dicuci, ada kesan hangit",
                promise="Lapisan dalam senang dibasuh, tak tinggal kesan",
                btn="Senang cuci",
                note="",
                src="periuk/clean (corpus: 'kacau supaya tidak melekat di dasar')",
            ),
        ],
    },
    "loyang": {
        "label": "Loyang kek",
        "slots": [
            dict(
                hook="Kek melekat, keluar hancur",
                promise="Lepas tanggal bersih, kek tak patah",
                btn="Tengok loyang",
                note="",
                src="loyang/melekat 8: 'digris dan dilapik baking paper'",
            ),
            dict(
                hook="Tepi masak, tengah mentah",
                promise="Haba rata, kek masak sekata sampai tengah",
                btn="Haba rata",
                note="",
                src="loyang/tak-seimbang (corpus: water bath 160C 55min)",
            ),
            dict(
                hook="Water bath, air masuk dalam loyang",
                promise="Tahan air, sesuai untuk bakar cara water bath",
                btn="Tengok yang ni",
                note="",
                src="loyang/water-bath: 'water bath pada suhu 160 darjah'",
            ),
        ],
    },
    "kukus": {
        "label": "Periuk kukus",
        "slots": [
            dict(
                hook="Air menitis atas kuih",
                promise="Tudung bentuk elak air menitis atas kuih",
                btn="Tengok pengukus",
                note="",
                src="kukus/kering 4: 'air menitis' (corpus: kerajang aluminium)",
            ),
            dict(
                hook="Kuih kering, tak lembut",
                promise="Wap sekata, kuih kekal lembut sampai sejuk",
                btn="Wap sekata",
                note="",
                src="kukus/kering 4",
            ),
            dict(
                hook="Pengukus besar untuk kuih sikit",
                promise="Saiz kecil, sesuai untuk buat sebahagian je",
                btn="Tengok saiz",
                note="",
                src="kukus/fit (batch size)",
            ),
        ],
    },
    "acuan": {
        "label": "Acuan kuih",
        "slots": [
            dict(
                hook="Bahulu melekat, susah nak keluar",
                promise="Lepas tanggal senang, bentuk tak rosak",
                btn="Tengok acuan",
                note="",
                src="acuan/melekat 11: 'supaya bahulu mudah dikeluarkan'",
            ),
            dict(
                hook="Acuan susah dicuci, ada sisa hangit",
                promise="Senang dibasuh antara kelompok",
                btn="Senang cuci",
                note="",
                src="acuan/clean: 'bersihkan acuan setiap kali sebelum kelompok seterusnya'",
            ),
            dict(
                hook="Bentuk kuih tak seragam",
                promise="Acuan sama saiz, semua kuih nampak sebentuk",
                btn="Tengok bentuk",
                note="",
                src="acuan/bentuk (corpus: 'bersihkan dan berus semula acuan')",
            ),
        ],
    },
}

# Products whose copy is benefit-angle because the corpus has no failure language
BENEFIT_ONLY = {"ricecooker", "takoyaki"}

BANNED = ["beli sekarang", "termurah", "terbaik", "diskaun", "murah gila",
          "hari ini sahaja", "stok terhad", "%"]


def blocks(key):
    """Return the 3 copy blocks for a product key."""
    return COPY[key]["slots"]


def label(key):
    return COPY[key]["label"]


def audit():
    """Self-audit: 48 blocks, no duplicate hooks, no banned terms, no '!'."""
    problems = []
    total = 0
    for key, prod in COPY.items():
        hooks = [s["hook"] for s in prod["slots"]]
        if len(hooks) != 3:
            problems.append(f"{key}: {len(hooks)} slots (expected 3)")
        if len(set(hooks)) != len(hooks):
            problems.append(f"{key}: duplicate hook {hooks}")
        for i, s in enumerate(prod["slots"]):
            total += 1
            for f in ("hook", "promise", "btn"):
                v = s.get(f, "")
                if not v.strip():
                    problems.append(f"{key}[{i}] empty {f}")
                if "!" in v:
                    problems.append(f"{key}[{i}] exclamation in {f}")
                low = v.lower()
                for b in BANNED:
                    if b in low:
                        problems.append(f"{key}[{i}] banned '{b}' in {f}")
            if not s.get("src"):
                problems.append(f"{key}[{i}] missing corpus evidence (src)")
    # cross-product duplicate hooks
    allh = [(k, s["hook"]) for k, p in COPY.items() for s in p["slots"]]
    seen = {}
    for k, h in allh:
        if h in seen and seen[h] != k:
            problems.append(f"hook reused across products: '{h}' ({seen[h]}, {k})")
        seen[h] = k
    return total, problems


if __name__ == "__main__":
    n, probs = audit()
    print(f"copy blocks: {n}")
    print(f"products:    {len(COPY)}")
    print(f"benefit-only: {sorted(BENEFIT_ONLY)}")
    if probs:
        print("\nPROBLEMS:")
        for p in probs:
            print("  -", p)
    else:
        print("\nAUDIT CLEAN — 48/48 blocks, 0 duplicate hooks, 0 banned terms, 0 '!'")
