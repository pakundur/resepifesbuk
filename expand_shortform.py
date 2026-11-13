"""Expand Malay shortforms in headlines, intros and meta descriptions.

The content repair pass handled ingredients/steps/tips. This one targets the
LLM-written copy layer (rewrite.json), where colloquial shortforms survived:
"dah"->"sudah", "je"->"sahaja", "kat"->"di", "sbb"->"sebab", "yg"->"yang".

Why an LLM and not str.replace:
  "dah" is context-dependent. "dah sejuk" -> "sudah sejuk" is correct, but a
  blind replace would also mangle proper nouns. "je" must become "sahaja" in
  some places and "cuma" in others to keep the sentence natural. The model is
  told to keep the sentence length inside the SEO band, because the whole point
  of headlines is the 50-60 char target.

Reads/writes src/rewrite.json. Usage: python expand_shortform.py
"""
import json, os, re, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
RW = os.path.join(ROOT, "src", "rewrite.json")
ENV = os.path.expanduser("~/.hermes/.env")
MODEL, MAX_CONC = "deepseek-chat", 6

SHORTS = r"\b(dah|je|kat|sbb|dgn|utk|sgt|yg|nk|xde|blh|takde|mcm|dpt|jd|kalo|smpi)\b"

SYSTEM = """Anda editor bahasa Melayu Malaysia. Tugas: buang singkatan, kekalkan bunyi natural.

Tukar:
  dah -> sudah        je -> sahaja       kat -> di          sbb -> sebab
  dgn -> dengan       utk -> untuk       sgt -> sangat      yg -> yang
  nk -> nak            xde -> tiada       blh -> boleh       takde -> tiada
  mcm -> macam         dpt -> dapat       jd -> jadi         kalo -> kalau
  smpi -> sampai

PERATURAN:
1. JANGAN ubah maksud. JANGAN tambah fakta baharu.
2. Kekalkan panjang: headline mesti kekal 50-60 aksara (ini penting untuk SEO).
   Jika perlu, pendekkan perkataan lain supaya muat.
3. Jangan jadi formal atau kaku. "memang", "cuma", "jangan risau" masih OK.
4. Kekalkan tanda baca dan huruf besar pada nama hidangan.
5. Jika tiada singkatan, pulangkan teks asal tanpa perubahan.

Balas JSON sahaja: {"headline": "...", "intro": "...", "meta_desc": "..."}"""


def load_env():
    for line in open(ENV, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def has_short(v):
    return any(re.search(SHORTS, v.get(f, "") or "", re.I)
               for f in ("headline", "intro", "meta_desc"))


async def one(client, slug, v, sem, out, done, total):
    async with sem:
        prompt = (f"Headline ({len(v['headline'])} aksara): {v['headline']}\n"
                  f"Intro: {v.get('intro','')}\n"
                  f"Meta description ({len(v.get('meta_desc',''))} aksara): {v.get('meta_desc','')}")
        payload = {"model": MODEL,
                   "messages": [{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": prompt}],
                   "temperature": 0.2, "max_tokens": 700,
                   "response_format": {"type": "json_object"}}
        headers = {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
                   "Content-Type": "application/json"}
        for attempt in range(3):
            try:
                r = await client.post("https://api.deepseek.com/chat/completions",
                                      json=payload, headers=headers, timeout=90)
                o = json.loads(r.json()["choices"][0]["message"]["content"])
                nh = (o.get("headline") or v["headline"]).strip()
                # guard: never accept a headline that breaks the SEO band
                if not (30 <= len(nh) <= 60):
                    nh = v["headline"]
                out[slug] = {"headline": nh,
                             "intro": (o.get("intro") or v.get("intro", "")).strip(),
                             "meta_desc": (o.get("meta_desc") or v.get("meta_desc", "")).strip()}
                break
            except Exception as e:
                if attempt == 2:
                    out[slug] = None
                else:
                    await asyncio.sleep(2)
    done[0] += 1
    if done[0] % 20 == 0 or done[0] == total:
        print(f"  {done[0]}/{total}", flush=True)


async def main():
    import httpx
    load_env()
    rw = json.load(open(RW, encoding="utf-8"))
    todo = {k: v for k, v in rw.items() if has_short(v)}
    print(f"expanding shortforms in {len(todo)} recipes", flush=True)
    out, done = {}, [0]
    sem = asyncio.Semaphore(MAX_CONC)
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[one(client, k, v, sem, out, done, len(todo))
                               for k, v in todo.items()])

    applied = 0
    for k, v in out.items():
        if not v:
            continue
        rw[k]["headline"] = v["headline"]
        if v["intro"]:
            rw[k]["intro"] = v["intro"]
        if v["meta_desc"] and 120 <= len(v["meta_desc"]) <= 158:
            rw[k]["meta_desc"] = v["meta_desc"]
        applied += 1
    json.dump(rw, open(RW, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    left = sum(1 for v in rw.values() if has_short(v))
    print(f"applied {applied} | recipes still containing shortforms: {left}")
    lens = [len(v["headline"]) for v in rw.values()]
    print(f"headlines over 60: {sum(1 for n in lens if n > 60)}")


if __name__ == "__main__":
    asyncio.run(main())
