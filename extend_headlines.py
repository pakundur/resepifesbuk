"""Extend short headlines to the 50-60 char SEO sweet spot.

Rewrites ONLY headlines currently under 50 chars, because Google renders about
60 chars on desktop and these were leaving visible SERP real estate unused.
Hard constraints kept from rewrite.py:
  - dish name stays first and must remain verbatim
  - no invented facts, no emoji, no em dash, no canned tails
  - result MUST land in 50-60 chars or the original is kept

Resume-safe via src/headline_ext.json. Merges results back into src/rewrite.json.

Usage: python extend_headlines.py [--limit N]
"""
import json, os, re, sys, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
RW = os.path.join(ROOT, "src", "rewrite.json")
OUT = os.path.join(ROOT, "src", "headline_ext.json")
ENV = os.path.expanduser("~/.hermes/.env")

MAX_CONC, MODEL = 6, "deepseek-chat"
LO, HI = 50, 60
TARGET_LO, TARGET_HI = 52, 59   # aim mid-band so off-by-one never breaches

SYSTEM = """Anda editor SEO untuk blog resepi Malaysia. Tugas anda memanjangkan headline \
supaya mencapai 50-60 aksara tanpa hilang maksud.

PERATURAN:
1. Nama hidangan MESTI kekal di depan, ejaan tepat seperti asal. Jangan tukar nama hidangan.
2. JANGAN reka fakta, bahan, kuantiti atau masa yang tiada dalam data.
3. Tiada emoji. Tiada em dash. Tiada "Resepi Mudah & Sedap", "Gerenti", "Confirm Sedap", "Selamat Mencuba".
4. Panjangkan dengan satu tarikan KONKRIT tentang hidangan ini: tekstur, teknik, asal, bila orang masak, apa yang buat ia berbeza. Bukan pujian kosong.
5. Panjang ayat akhir MESTI 50 hingga 60 aksara termasuk ruang.
6. Title Case konsisten pada perkataan utama.
7. JANGAN ulang perkataan yang sudah ada melampaui batas. Bunyinya natural, bukan dipaksa.

Balas HANYA JSON: {"headline": "..."}"""


def load_env():
    for line in open(ENV, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def build_prompt(r, cur):
    ings = "; ".join(r.get("ingredients", [])[:10])
    return f"""Nama hidangan: {r['title'].split(':')[0]}
Kategori: {r['cats'][0] if r.get('cats') else ''}
Bahan utama: {ings}

Headline sekarang ({len(cur)} aksara): {cur}

Panjangkan kepada 50-60 aksara. Kekalkan nama hidangan di depan."""


async def one(client, r, cur, sem, res, done, total):
    async with sem:
        payload = {"model": MODEL,
                   "messages": [{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": build_prompt(r, cur)}],
                   "temperature": 0.4, "max_tokens": 120,
                   "response_format": {"type": "json_object"}}
        headers = {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
                   "Content-Type": "application/json"}
        for attempt in range(4):
            try:
                resp = await client.post("https://api.deepseek.com/chat/completions",
                                         json=payload, headers=headers, timeout=60)
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code}")
                txt = resp.json()["choices"][0]["message"]["content"]
                new = (json.loads(txt).get("headline") or "").strip()
                new = re.sub(r"[—–]", ",", new)
                new = re.sub(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]", "", new).strip()
                # dish name must survive near the front (within first 4 words)
                dish = re.sub(r"^resepi\s+", "", r["title"].split(":")[0], flags=re.I).strip()
                head_words = " ".join(new.lower().split()[:4])
                if dish.lower() not in new.lower() and dish.lower() not in head_words:
                    raise ValueError("dish name missing")
                if not new.lower().startswith(dish.lower().split()[0]):
                    raise ValueError("dish first word changed")
                if not (48 <= len(new) <= 62):
                    raise ValueError(f"length {len(new)}")
                res[r["slug"]] = new
                break
            except Exception as e:
                if attempt == 3:
                    res[r["slug"]] = None
                    print(f"  skip {r['slug'][:40]}: {e}", flush=True)
                else:
                    await asyncio.sleep(1.5 * (attempt + 1))
    done[0] += 1
    if done[0] % 25 == 0 or done[0] == total:
        json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"  {done[0]}/{total}", flush=True)


async def main():
    import httpx
    load_env()
    recs = json.load(open(SRC, encoding="utf-8"))
    rw = json.load(open(RW, encoding="utf-8"))
    by = {r["slug"]: r for r in recs}
    res = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}

    todo = [s for s, v in rw.items()
            if len(v.get("headline", "")) < LO and s not in res and s in by]
    if "--limit" in sys.argv:
        todo = todo[:int(sys.argv[sys.argv.index("--limit") + 1])]
    print(f"extending {len(todo)} headlines under {LO} chars", flush=True)
    if todo:
        sem = asyncio.Semaphore(MAX_CONC)
        done = [0]
        async with httpx.AsyncClient() as client:
            await asyncio.gather(*[one(client, by[s], rw[s]["headline"], sem, res, done, len(todo))
                                   for s in todo])
        json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    # merge: only accept valid in-band results
    applied = 0
    for s, h in res.items():
        if h and s in rw and 48 <= len(h) <= 62:
            rw[s]["headline"] = h
            applied += 1
    json.dump(rw, open(RW, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    errs = [k for k, v in res.items() if v is None]
    print(f"applied {applied} | skipped {len(errs)}")
    lens = [len(v["headline"]) for v in rw.values()]
    inband = sum(1 for n in lens if LO <= n <= HI)
    print(f"in 50-60 band: {inband}/{len(lens)} | over 60: {sum(1 for n in lens if n > 60)}")


if __name__ == "__main__":
    asyncio.run(main())
