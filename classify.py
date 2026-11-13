"""LLM classifier: ONE category per recipe, decided from the headline/dish identity.

Reads  src/recipes_clean.json
Writes src/cats.json   {slug: {"cat": "...", "dish": "...", "conf": 0-3}}

Why one category:
  The previous scheme (primary + secondary from title/ingredients) produced
  cross-category drift: "Pulut Mangga" filed under Nasi, "Pizza Kuali" under
  Daging. A recipe is a DISH, and a dish belongs to exactly one family. The
  ingredient list is evidence, not identity - a chicken curry is Ayam even
  though it has potatoes, santan and serai.

Resume-safe: skips slugs already present in the output file.
Usage:  python classify.py [--limit N]
"""
import json, os, sys, re, asyncio, random

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
RW = os.path.join(ROOT, "src", "rewrite.json")
OUT = os.path.join(ROOT, "src", "cats.json")
ENV = os.path.expanduser("~/.hermes/.env")

MAX_CONC = 6
MODEL = "deepseek-chat"

TAXONOMY = {
    "Nasi": "nasi, nasi lemak, nasi goreng, nasi kerabu, nasi arab, biryani, nasi ayam, nasi minyak, nasi kunyit, pulut kuning (hidang bersama lauk), lemang, ketupat, nasi impit, lontong",
    "Mee & Bihun": "mee, mi, bihun, kuey teow, laksa, kolok, wantan mee, char kway teow, mee sup, mee goreng, mee kari, soto (mee), maggi, pasta, spaghetti, makaroni",
    "Roti & Pastri": "roti, roti canai, roti jala, murtabak, capati, puri, pizza, pau, bao, buns, donut, bomboloni, croissant, sandwich, wrap, tortilla, pita",
    "Ayam": "masakan yang hidangan UTAMA-nya ayam (kari ayam, ayam masak merah, ayam percik, ayam goreng, ayam bakar, satay ayam, rendang ayam, sup ayam)",
    "Daging": "masakan yang hidangan UTAMA-nya daging lembu/kambing (rendang daging, daging masak hitam, sup daging, steak, kambing bakar, kurma daging)",
    "Ikan": "masakan yang hidangan UTAMA-nya ikan (ikan bakar, ikan masak lemak, pindang, ikan goreng, salmon, tuna, tenggiri, siakap)",
    "Udang": "udang, prawn, harimau, lobster",
    "Ketam": "ketam, crab, masakan utama ketam (crabstick sahaja BUKAN ketam)",
    "Sotong": "sotong, squid, cumi",
    "Kerang & Siput": "kerang, kupang, lala, siput, belangkas, scallop, mussels, clams",
    "Perut & Organ": "perut, hati, paru, usus, ginjal, organ, innards",
    "Sayur": "sayur, ulam, salad, kobis, kangkung, terung, bendi, tauhu, tempe, ulam-ulaman, vegetarian",
    "Sup & Bening": "sup sayur / sup campur / sup tanpa protein jelas (sup brokoli, sup kentang, sup telur, sup sayur). Sup yang proteinnya jelas (sup ayam, sup daging, sup udang, sup ikan) ikut kategori protein itu.",
    "Sambal & Sos": "sambal sahaja, sambal tumis kosong, sambal belacan, sos cili, sambal nasi lemak - bukan lauk berprotein",
    "Kuih": "kuih tradisional Melayu/nyonya (kuih talam, kuih lapis, onde-onde, karipap, seri muka, kuih koci, apam, cucur, kuih bakar, tepung bungkus)",
    "Kek": "kek, cake, cheesecake, brownies, muffin, cupcake, kek lapis, kek coklat, kek cheese, tiramisu",
    "Biskut & Biskut Raya": "biskut, cookies, biscotti, semperit, tart nenas, samperit, makmur, biskut raya, crackers",
    "Bubur": "bubur, porridge, congee, bubur kacang, bubur pulut hitam, bubur lambuk, bubur cha cha",
    "Puding & Pencuci Mulut": "puding, pudding, agar-agar, jelly, panna cotta, pulut mangga, mango sticky rice, sago, dessert sejuk, ais krim buatan sendiri, mousse",
    "Minuman": "minuman, air, jus, smoothie, latte, teh, kopi, sirap, bandung, cendol, bubur cha cha minuman, milkshake, mocktail",
}

RULES = """Anda penganalisis hidangan Malaysia. Tugas: tentukan SATU kategori untuk satu resepi.

Prinsip:
1. Kategori ikut IDENTITI HIDANGAN (apa yang orang panggil hidangan itu), BUKAN bahan tepinya.
   - "Pulut Mangga" = pencuci mulut Thai -> "Puding & Pencuci Mulut" (bukan Nasi, walaupun guna pulut).
   - "Nasi Goreng Bombay" = nasi -> "Nasi" (bukan Ayam, walaupun ada telur/ayam).
   - "Pizza Kuali" = roti/pastri -> "Roti & Pastri".
   - "Kari Ayam dengan Kentang" = "Ayam" (protein utama tetap ayam).
   - "Sambal Tumis Ikan Bilis" = "Sambal & Sos" (sambal itu hidangannya).
   - "Nasi Lemak Sambal Sotong" = "Nasi" (nasi lemak yang menjadi hidangan).
2. Sup: jika protein UTAMA jelas (Sup Ayam, Sup Daging, Sup Udang, Sup Ikan, Sup Sotong, Sup Ketam), letak di bawah kategori PROTEIN itu. Hanya sup sayur / sup campur / sup tanpa protein jelas masuk "Sup & Bening". Contoh: "Sup Udang Thai" -> "Udang", bukan "Sup & Bening".
3. Kuih vs Kek vs Biskut: kuih = tradisional dikukus/dibungkus; kek = dibakar dalam acuan; biskut = kepingan rangup.
4. Jangan sekali-kali letak lebih daripada satu kategori.

Balas HANYA JSON sah: {"cat": "<satu kategori tepat dari senarai>", "dish": "<nama hidangan ringkas 2-5 patah>", "conf": <1-3>}"""


def load_env():
    if not os.path.exists(ENV):
        return
    for line in open(ENV, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def load_json(p, default):
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            return default
    return default


def build_prompt(r):
    rw = RW.get(r["slug"], {})
    headline = rw.get("headline") or r.get("title") or ""
    ings = "; ".join(i for i in r.get("ingredients", [])[:12])
    tax = "\n".join(f"- {k}: {v}" for k, v in TAXONOMY.items())
    return f"""Judul asal: {r.get('title','')}
Headline SEO: {headline}
Kategori Blogger (boleh salah, abaikan jika bercanggah): {', '.join(r.get('cats') or []) or '(tiada)'}
Bahan utama: {ings}

SENARAI KATEGORI SAH (pilih tepat satu, ejaan mesti sama):
{tax}

Tentukan kategori."""


async def call_one(client, r, sem, results, done, total):
    import httpx
    async with sem:
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": RULES},
                {"role": "user", "content": build_prompt(r)},
            ],
            "temperature": 0.0,
            "max_tokens": 120,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
                   "Content-Type": "application/json"}
        for attempt in range(4):
            try:
                resp = await client.post("https://api.deepseek.com/chat/completions",
                                         json=payload, headers=headers, timeout=90)
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code} {resp.text[:160]}")
                txt = resp.json()["choices"][0]["message"]["content"]
                obj = json.loads(txt)
                cat = (obj.get("cat") or "").strip()
                if cat not in TAXONOMY:
                    # fuzzy fix
                    low = cat.lower()
                    cat = next((k for k in TAXONOMY if k.lower() == low), None) or \
                          next((k for k in TAXONOMY if k.lower() in low or low in k.lower()), "")
                if not cat:
                    raise ValueError(f"bad cat {obj.get('cat')!r}")
                results[r["slug"]] = {
                    "cat": cat,
                    "dish": (obj.get("dish") or "").strip()[:60],
                    "conf": int(obj.get("conf") or 2),
                }
                break
            except Exception as e:
                if attempt == 3:
                    results[r["slug"]] = {"cat": "", "dish": "", "conf": 0,
                                          "err": str(e)[:200]}
                else:
                    await asyncio.sleep(2 * (attempt + 1))
    done[0] += 1
    if done[0] % 25 == 0 or done[0] == total:
        json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"  {done[0]}/{total}", flush=True)


async def main():
    import httpx
    load_env()
    recipes = load_json(SRC, [])
    global RW
    RW = load_json(RW, {})
    results = load_json(OUT, {})
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    todo = [r for r in recipes if r["slug"] not in results]
    if limit:
        todo = todo[:limit]
    print(f"classifying {len(todo)} of {len(recipes)} (already done: {len(results)})", flush=True)
    sem = asyncio.Semaphore(MAX_CONC)
    done = [len(results)]
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[call_one(client, r, sem, results, done, len(recipes))
                               for r in todo])
    json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    bad = [k for k, v in results.items() if not v.get("cat")]
    print(f"DONE {len(results)} written, {len(bad)} failed")


if __name__ == "__main__":
    asyncio.run(main())
