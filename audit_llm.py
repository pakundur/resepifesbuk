"""LLM content audit: Bahasa Melayu quality, Indonesian leakage, schema sanity.

Runs on the BUILT pages so it judges what Google and readers actually see.

For each sampled recipe it asks the model to act as a Malaysian copy editor and
return structured findings:
  - indonesian : words/phrases that are Indonesian rather than Malaysian Malay
  - shortform  : abbreviations that should be spelled out
  - schema     : anything factually wrong in the visible copy vs the schema
                 (e.g. recipeCategory that contradicts the dish)

Outputs a JSON report so fixes can be applied selectively rather than by
rewriting everything blindly.

Usage: python audit_llm.py [--sample N]
"""
import json, os, re, sys, asyncio, glob, html, random

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(ROOT, "src", "llm_audit.json")
ENV = os.path.expanduser("~/.hermes/.env")
MAX_CONC, MODEL = 6, "deepseek-chat"

# Indonesian markers that are wrong in Malaysian Malay
ID_WORDS = ["banget", "pisan", "udah", "bisa", "gimana", "kalo", "doang", "emang",
            "bikin", "cuma", "dapet", "gak", "nggak", "aja", "sih", "deh", "kok",
            "bawang bombay", "kentang putih", "gula putih", "santan kelapa",
            "aer", "pisang ambon", "cabai", "saus", "wortel", "tomat", "seledri"]

SYSTEM = """Anda editor bahasa Melayu Malaysia yang berpengalaman. Anda menyemak teks resepi.

Tugas: kenal pasti masalah bahasa dan laporkan dalam JSON. JANGAN tulis semula teks penuh.

Kategori masalah. PENTING: hanya laporkan yang BENAR-BENAR salah.

1. "indonesian" - HANYA perkataan Indonesia yang jelas salah dalam BM.
   SALAH: banget, udah, gimana, doang, emang, bikin (utk "buat"), wortel
   (utk "lobak merah"), cabai (utk "cili"), saus (utk "sos"), aduk (utk "kacau").
   JANGAN laporkan perkataan ini kerana ia BETUL dalam bahasa Melayu Malaysia:
   - tomato, kentang, bawang merah, bawang putih, gula pasir, santan, kelapa
   - resepi, resipi, fesbuk, nak, tak, dah, je, pun, dia, ni, tu, kita, awak
   - nama jenama: Maggi, Adabi, Nestum, Oreo, Horlicks, Milo, GoodDay
   - istilah teknikal yang tiada padanan: mozzarella, parmesan, blender, oven
   Senarai ini KOSONG jika tiada perkataan Indonesia sebenar.

2. "shortform" - HANYA singkatan tulisan pendek, bukan perkataan penuh.
   SALAH: yg, dgn, utk, nk, sbb, tp, xde, blh, sgt, mcm, dpt, jd, kalo, smpi, takde
   JANGAN laporkan: dah, je, nak, tak, ni, tu, pun, dia - ini bahasa Melayu
   santai yang BETUL dan dibenarkan. Kami mahu bunyi natural, bukan formal.

3. "broken" - HANYA ayat yang benar-benar tergantung tanpa noktah, atau ayat
   yang bercampur Bahasa Inggeris penuh yang tidak boleh difahami.
   JANGAN laporkan ayat santai yang gramatis. "Sesuai sangat kalau kita nak buat
   stok awal sebelum musim raya tiba" adalah ayat SEMPURNA, bukan broken.

Balas JSON sah sahaja:
{"indonesian": ["..."], "shortform": ["..."], "broken": ["..."], "ok": true/false}
Jika tiada masalah, pulangkan senarai kosong dan "ok": true."""


def load_env():
    for line in open(ENV, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def page_text(path):
    s = open(path, encoding="utf-8", errors="ignore").read()
    # visible copy only: drop head, scripts, svg, nav/footer chrome
    m = re.search(r"<main[^>]*>(.*?)</main>", s, re.S)
    body = m.group(1) if m else s
    body = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", body, flags=re.S | re.I)
    txt = html.unescape(re.sub(r"<[^>]+>", " ", body))
    return re.sub(r"\s+", " ", txt).strip()


async def one(client, slug, txt, sem, res, done, total):
    async with sem:
        payload = {"model": MODEL,
                   "messages": [{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": txt[:4000]}],
                   "temperature": 0.0, "max_tokens": 400,
                   "response_format": {"type": "json_object"}}
        headers = {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
                   "Content-Type": "application/json"}
        for attempt in range(3):
            try:
                r = await client.post("https://api.deepseek.com/chat/completions",
                                      json=payload, headers=headers, timeout=90)
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP {r.status_code}")
                res[slug] = json.loads(r.json()["choices"][0]["message"]["content"])
                break
            except Exception as e:
                if attempt == 2:
                    res[slug] = {"error": str(e)[:120]}
                else:
                    await asyncio.sleep(2)
    done[0] += 1
    if done[0] % 25 == 0 or done[0] == total:
        json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"  {done[0]}/{total}", flush=True)


async def main():
    import httpx
    load_env()
    files = sorted(glob.glob(os.path.join(DIST, "resepi", "*", "index.html")))
    sample = None
    if "--sample" in sys.argv:
        sample = int(sys.argv[sys.argv.index("--sample") + 1])
        random.seed(42)
        files = random.sample(files, min(sample, len(files)))
    res = {}
    print(f"auditing {len(files)} pages", flush=True)
    sem = asyncio.Semaphore(MAX_CONC)
    done = [0]
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one(client, f.split(os.sep)[-2], page_text(f), sem, res, done, len(files))
                               for f in files])
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    id_hits = sum(1 for v in res.values() if v.get("indonesian"))
    sf_hits = sum(1 for v in res.values() if v.get("shortform"))
    br_hits = sum(1 for v in res.values() if v.get("broken"))
    print(f"\npages with Indonesian words : {id_hits}")
    print(f"pages with shortforms       : {sf_hits}")
    print(f"pages with broken sentences : {br_hits}")
    for k, v in list(res.items()):
        if v.get("indonesian"):
            print(f"  ID {k}: {v['indonesian'][:4]}")
            break


if __name__ == "__main__":
    asyncio.run(main())
