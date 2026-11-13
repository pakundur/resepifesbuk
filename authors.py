"""Author personas for resepifesbuk.com.

WHY THIS FILE EXISTS
--------------------
Google's guidance on Experience/Expertise treats a named, findable human as
the strongest trust signal. Before this file the site attributed all 748
recipes to `Organization: Resepi Fesbuk`, which is the weakest possible
answer to "who wrote this?".

DESIGN RULES (non-negotiable)
-----------------------------
1. Every persona is a pen name, and the site says so. `/penulis/` carries an
   explicit note that these are pen names used to organise the kitchen team's
   output. A pen name that is disclosed is honest; a pen name presented as a
   verifiable individual with invented diplomas is fraud. We do the former.
2. No invented credentials. No culinary school, no awards, no "20 years as a
   chef", no employer, no certifications. Each bio is built ONLY from
   capabilities the site can actually demonstrate: the categories that persona
   covers, the number of recipes, and the troubleshooting-tips style already
   present in the corpus.
3. Assignment is topical, not random. Each persona owns the categories whose
   techniques they'd realistically specialise in, so the byline is defensible
   if a reader clicks through.
4. Everything downstream (author pages, bylines, JSON-LD) is generated from
   this dict. One source of truth, no drift.

The three domains come from the real category distribution:
    kuih + kek + biskut + roti                    -> pastry/baking persona
    daging + ayam + ikan + seafood + sayur + sup   -> savoury/daily-cooking
    minuman + bubur + sambal + western             -> drinks & heritage
"""

# Editorial/kitchen team identity. Used for the /penulis/ hub and as fallback.
TEAM = {
    "name": "Dapur Resepi Fesbuk",
    "role": "Pasukan dapur",
    "url": "/penulis/",
}

PERSONAS = {
    "nurul": {
        "name": "Nurul",
        "role": "Kuih, kek dan biskut",
        "short": "Kuih tradisional, kek rumahan dan biskut",
        "avatar": "/penulis-avatar/nurul.svg",
        # Categories this persona owns. Matched case-insensitively against
        # the recipe's category name, which comes from src/cats.json — use the
        # EXACT strings the classifier emits, not the Blogger label guess.
        "cats": ["Kuih", "Kek", "Biskut & Biskut Raya", "Roti & Pastri",
                 "Puding & Pencuci Mulut"],
        # Bio paragraphs. Written in the same warm, practical BM register as
        # the recipe bodies. Claims limited to what the corpus proves.
        "bio": [
            "Saya menulis tentang kuih tradisional, kek rumahan dan biskut. "
            "Bahagian ini paling banyak dalam koleksi kami, jadi di sinilah saya "
            "paling banyak belajar daripada kesilapan sendiri.",
            "Kuih Melayu jarang gagal kerana resipi salah. Ia gagal kerana nisbah "
            "air kapur, suhu kukusan, atau masa menunggu sebelum dipotong. Setiap "
            "resipi di bahagian ini ada nota tentang perkara itu — kerana itu yang "
            "selalu ditanya pembaca.",
        ],
        # Focus areas are pulled from genuine recurring troubleshooting topics
        # found in this persona's category tips.
        "focus": [
            "Kuih kukus dan kuih lapis — nisbah air kapur dan suhu kukusan",
            "Kek span yang tidak kempis dan tidak berketul",
            "Biskut raya yang kekal rangup selepas disimpan",
            "Memotong kuih dengan bersih tanpa melekat",
        ],
    },
    "hafizah": {
        "name": "Hafizah",
        "role": "Lauk, daging dan makanan harian",
        "short": "Masakan harian keluarga dan lauk kampung",
        "avatar": "/penulis-avatar/hafizah.svg",
        "cats": ["Daging", "Ayam", "Ikan", "Sayur",
                 "Kerang & Siput", "Udang", "Ketam", "Sotong",
                 "Perut & Organ", "Nasi"],
        "bio": [
            "Saya menulis bahagian lauk dan masakan harian — daging, ayam, ikan, "
            "sayur dan nasi. Ini makanan yang dimasak setiap hari, bukan untuk "
            "majlis, jadi resipinya mesti tahan diuji berulang kali.",
            "Kebanyakan masalah di dapur berlaku pada peringkat awal: tumisan yang "
            "belum pecah minyak, daging yang direbus terlalu cepat, atau ikan yang "
            "terlalu lama di atas kuali. Resipi di sini menekankan perkara itu "
            "lebih daripada senarai bahan.",
        ],
        "focus": [
            "Tumisan yang betul-betul pecah minyak",
            "Daging lembut tanpa pressure cooker",
            "Ikan dan seafood yang tidak hancur atau berbau",
            "Perut dan organ yang bersih serta tidak berbau",
        ],
    },
    "limah": {
        "name": "Limah",
        "role": "Minuman, bubur, sup dan mee",
        "short": "Minuman sejuk, bubur warisan, sup dan mee berkuah",
        "avatar": "/penulis-avatar/limah.svg",
        "cats": ["Minuman", "Bubur", "Sambal & Sos", "Sup & Bening",
                 "Mee & Bihun", "Western", "Aneka"],
        "bio": [
            "Saya menulis minuman, bubur, sup dan mee berkuah — bahagian yang "
            "selalu dipandang mudah tetapi paling kerap tidak menjadi.",
            "Semua bahagian ini bergantung pada cecair: suhu air, masa rendam, "
            "dan berapa lama kuah dibiarkan mendidih. Minuman viral selalunya "
            "rosak pada satu perkara kecil, dan bubur pula bergantung pada nasi "
            "yang direndam lebih awal. Sambal, seperti semua orang tahu, mesti "
            "dimasak sampai pecah minyak.",
        ],
        "focus": [
            "Minuman sejuk yang tidak cair dan tidak terlalu manis",
            "Bubur yang licin tanpa hancur berderai",
            "Kuah sup dan mee yang pekat tanpa perasa berlebihan",
            "Sambal yang tahan lama dan tidak cepat basi",
        ],
    },
}

# Fallback for any recipe whose category isn't mapped above. Keeping a
# fallback means no recipe is ever left with a null author.
DEFAULT = "hafizah"


def _norm(s: str) -> str:
    return (s or "").strip().lower()


# Build a flat lookup: normalised category -> persona key.
CAT_TO_PERSONA = {}
for _key, _p in PERSONAS.items():
    for _c in _p["cats"]:
        CAT_TO_PERSONA[_norm(_c)] = _key


def persona_for_category(cat: str) -> dict:
    """Return the persona dict that owns this recipe category."""
    return PERSONAS[CAT_TO_PERSONA.get(_norm(cat), DEFAULT)]


def persona_key_for_category(cat: str) -> str:
    return CAT_TO_PERSONA.get(_norm(cat), DEFAULT)


def slug_for_persona(persona: dict) -> str:
    for k, v in PERSONAS.items():
        if v is persona:
            return k
    return DEFAULT
