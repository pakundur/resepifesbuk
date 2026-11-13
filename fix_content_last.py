"""Last-resort repair for the handful of recipes the batch pass could not split.

These posts were mangled badly by the legacy parser: the ingredient list and the
method were interleaved so thoroughly that the batch prompt could not recover a
usable split (it returned 0 ingredients or 1 step).

This script sends the ORIGINAL post text to the model with no assumed structure
at all — it must read the post like a human and decide what is an ingredient and
what is a step. Same accuracy rule: no invented ingredients.
"""
import json, os, re, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
RAW = os.path.join(ROOT, "src", "posts_full.json")
OUT = os.path.join(ROOT, "src", "content_fix.json")
ENV = os.path.expanduser("~/.hermes/.env")
MODEL = "deepseek-chat"

TARGETS = ["resepi-kek-marble-terbaik", "resepi-kek-milo-mudah",
           "resepi-kerabu-kerang-marvellous", "resepi-air-asam-power",
           "resepi-kari-ayam-hijau-power"]

SYSTEM = """Anda tukang masak Malaysia yang menulis semula resepi lama yang bersepah.

Anda diberi teks mentah sebuah post resepi. Teks ini mungkin tidak tersusun:
bahan dan langkah bercampur, ada singkatan, ada hashtag.

Tugas anda:
1. Baca seluruh teks dan faham hidangannya.
2. Keluarkan SENARAI BAHAN yang lengkap dengan sukatan jika ada.
3. Keluarkan LANGKAH memasak yang logik dan tersusun.
4. Tulis 2-3 TIPS praktikal.

PERATURAN:
- JANGAN reka bahan yang tiada dalam teks. Jika teks menyebut bahan, ambil.
- Jika sukatan tiada, tulis nama bahan sahaja.
- LANGKAH mesti ayat arahan, Bahasa Melayu Malaysia penuh (bukan singkatan,
  bukan Indonesia). "dah"->"sudah", "je"->"sahaja", "cabai"->"cili".
- Jika teks hanya ada bahan tanpa langkah jelas, bina langkah yang munasabah
  daripada cara hidangan itu biasanya dimasak, TAPI jangan tambah bahan baharu.
- Buang hashtag, emoji dan "Selamat mencuba".

Balas JSON sahaja:
{"ingredients": ["..."], "steps": ["..."], "tips": ["..."]}"""


def load_env():
    for line in open(ENV, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def main():
    import httpx
    load_env()
    recs = {r["slug"]: r for r in json.load(open(SRC, encoding="utf-8"))}
    raw = {}
    for p in json.load(open(RAW, encoding="utf-8")):
        m = re.search(r"/(\d{4})/(\d{2})/([^/]+?)\.html", p.get("url", ""))
        if m:
            key = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            txt = re.sub(r"<[^>]+>", " ", p.get("content", ""))
            raw[key] = re.sub(r"\s+", " ", txt)
    res = json.load(open(OUT, encoding="utf-8"))

    headers = {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
               "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        for slug in TARGETS:
            r = recs.get(slug)
            if not r:
                print(f"skip {slug}: not found")
                continue
            body = raw.get(slug, "")
            if not body:
                body = " ".join(str(x) for x in r["ingredients"] + r["steps"])
            prompt = f"Hidangan: {r['title']}\n\nTEKS MENTAH:\n{body[:3500]}"
            for attempt in range(4):
                try:
                    resp = await client.post(
                        "https://api.deepseek.com/chat/completions", headers=headers, timeout=120,
                        json={"model": MODEL,
                              "messages": [{"role": "system", "content": SYSTEM},
                                           {"role": "user", "content": prompt}],
                              "temperature": 0.1, "max_tokens": 1600,
                              "response_format": {"type": "json_object"}})
                    o = json.loads(resp.json()["choices"][0]["message"]["content"])
                    ings = [str(x).strip() for x in o.get("ingredients", []) if str(x).strip()]
                    sts = [str(x).strip() for x in o.get("steps", []) if str(x).strip()]
                    tps = [str(x).strip() for x in o.get("tips", []) if str(x).strip()]
                    if not ings or len(sts) < 2:
                        raise ValueError(f"ing={len(ings)} steps={len(sts)}")
                    res[slug] = {"ingredients": ings, "steps": sts, "tips": tps}
                    print(f"OK {slug}: {len(ings)} ing, {len(sts)} steps, {len(tps)} tips")
                    break
                except Exception as e:
                    if attempt == 3:
                        print(f"FAIL {slug}: {e}")
                    else:
                        await asyncio.sleep(2)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"total now: {len(res)}")


if __name__ == "__main__":
    asyncio.run(main())
