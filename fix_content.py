"""LLM repair of ingredient/step separation, per recipe.

WHY
parse.py heuristics cannot reliably tell an ingredient line from a method line
in legacy Blogger posts. Two failure modes survived every rule-based pass:
  A. method sentences sitting inside Bahan-bahan ("Masukkan serbuk rempah sup..")
  B. the whole ingredient list sitting inside Cara Penyediaan (16 steps like
     "1 kg ubi kayu (dikisar & ditapis)")

The LLM reads BOTH blocks plus the original post text and returns a clean split.
It may reclassify and reformat, but it must NOT invent an ingredient that is not
present in the source — same accuracy rule as rewrite.py.

Also generates "tips" for recipes that have none (user requirement: every recipe
has Tips Masakan).

Input : src/recipes_clean.json  (ingredients, steps, tips, post text)
Output: src/content_fix.json  {slug: {ingredients:[], steps:[], tips:[]}}

Usage: python fix_content.py [--limit N]
"""
import json, os, re, sys, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
RAW = os.path.join(ROOT, "src", "posts_full.json")
OUT = os.path.join(ROOT, "src", "content_fix.json")
ENV = os.path.expanduser("~/.hermes/.env")

MAX_CONC, MODEL = 6, "deepseek-chat"

SYSTEM = """Anda editor resepi Malaysia yang teliti. Tugas anda memisahkan BAHAN dan LANGKAH,
kemudian menulis tips.

PERATURAN KETAT:
1. BAHAN = hanya nama bahan + sukatan. MESTI tiada kata kerja arahan.
   SALAH: "Masukkan serbuk rempah sup dan tumis hingga pecah minyak"
   BETUL: "Serbuk rempah sup - 2 sudu besar"
2. LANGKAH = ayat arahan memasak, satu tindakan utama satu langkah, bermula dengan kata kerja.
   SALAH: "1 kg ubi kayu"
   BETUL: "Kisar ubi kayu yang telah dikupas sehingga halus, kemudian tapis."
3. JANGAN reka bahan atau sukatan yang tiada dalam teks asal. Jika sukatan tiada, tulis nama bahan sahaja.
4. Jika teks asal meletakkan senarai bahan di dalam bahagian langkah, pindahkan ke BAHAN.
5. Jika ada baris yang bukan bahan dan bukan langkah (cth hashtag, "Selamat mencuba"), buang.
6. Bahasa Melayu Malaysia yang natural (BUKAN Indonesia). Tulis perkataan PENUH, jangan singkatan.
   Tukar SEMUA bentuk pendek: "x payah"->"tak payah", "xde"->"tiada", "nk"->"nak",
   "dgn"->"dengan", "utk"->"untuk", "sbb"->"sebab", "tp"->"tapi", "je"->"sahaja",
   "dah"->"sudah", "yg"->"yang", "kat"->"di", "blh"->"boleh", "takde"->"tiada",
   "sgt"->"sangat", "mcm"->"macam", "bg"->"bagi", "skit"->"sikit", "dpt"->"dapat",
   "jd"->"jadi", "kalo"->"kalau", "kecik"->"kecil", "smpi"->"sampai".
   TAPI jangan jadi formal atau kaku. Bahasa santai yang betul tetap dibenarkan:
   "jangan risau", "memang sedap", "cuma kena hati-hati" semuanya bagus.
   Perkataan Indonesia yang mesti ditukar: "bawang merah" (bukan "bawang bombay"),
   "santan" (bukan "santan kelapa" berulang), "gula pasir" (bukan "gula putih"),
   "kentang" (bukan "kentang putih"), "air" (bukan "aer"), "sudah" (bukan "udah"),
   "bisa"->"boleh/guna", "banget"->"sangat", "pisan"->"sangat", "yg"->"yang".
7. TIPS: 2-3 tips praktikal khusus untuk hidangan ini (teknik, kesilapan biasa,
   cara simpan). Jika teks asal sudah ada tips, kekalkan maksudnya dan kemaskan bahasanya.
   Jangan tips generik seperti "guna bahan segar".

Balas HANYA JSON sah:
{"ingredients": ["..."], "steps": ["..."], "tips": ["..."]}"""


def load_env():
    for line in open(ENV, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def steps_txt(r):
    out = []
    for s in r.get("steps", []):
        if isinstance(s, dict):
            if s.get("h"):
                out.append("[subjudul] " + s["h"])
            elif s.get("t"):
                out.append(s["t"])
        else:
            out.append(str(s))
    return out


def needs_fix(r):
    """Only spend an LLM call where the mechanical audit found a problem."""
    ing = r.get("ingredients") or []
    sts = steps_txt(r)
    VERB = re.compile(r"\b(masukkan|panaskan|tumis|kacau|gaul|kukus|goreng|bakar|tuang|"
                      r"sejukkan|angkat|toskan|tapis|rendam|potong|hiris|kisar|satukan|"
                      r"campur|letak|siapkan|hidang|perasakan|rehat|uli)\b", re.I)
    if not ing:
        return True                      # empty ingredient box
    for i in ing:
        if len(str(i)) > 140 or (VERB.search(str(i)) and len(str(i).split()) > 9):
            return True                  # method inside ingredients
    if len([s for s in sts if not s.startswith("[subjudul]")]) < 2:
        return True                      # no usable steps
    if not r.get("tips"):
        return True                      # needs tips
    return False


def build_prompt(r, raw_text):
    ing = "\n".join(f"- {i}" for i in (r.get("ingredients") or [])[:40]) or "(kosong)"
    sts = "\n".join(f"{n}. {s}" for n, s in enumerate(steps_txt(r)[:40])) or "(kosong)"
    tips = "\n".join(f"- {t}" for t in (r.get("tips") or [])[:8]) or "(tiada)"
    return f"""Hidangan: {r['title']}

BAHAGIAN "BAHAN" SEMASA (mungkin tercemar dengan langkah):
{ing}

BAHAGIAN "LANGKAH" SEMASA (mungkin mengandungi senarai bahan):
{sts}

TIPS SEMASA:
{tips}

TEKS ASAL PENUH (rujukan utama, jangan cipta fakta luar dari ini):
\"\"\"{raw_text[:3000]}\"\"\"

Pisahkan semula dengan betul dan tulis tips."""


async def one(client, r, raw_text, sem, res, done, total):
    async with sem:
        payload = {"model": MODEL,
                   "messages": [{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": build_prompt(r, raw_text)}],
                   "temperature": 0.2, "max_tokens": 1800,
                   "response_format": {"type": "json_object"}}
        headers = {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
                   "Content-Type": "application/json"}
        for attempt in range(4):
            try:
                resp = await client.post("https://api.deepseek.com/chat/completions",
                                         json=payload, headers=headers, timeout=120)
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code}")
                o = json.loads(resp.json()["choices"][0]["message"]["content"])
                ings = [str(x).strip() for x in (o.get("ingredients") or []) if str(x).strip()]
                sts = [str(x).strip() for x in (o.get("steps") or []) if str(x).strip()]
                tps = [str(x).strip() for x in (o.get("tips") or []) if str(x).strip()]
                if not ings or len(sts) < 2:
                    raise ValueError(f"bad split ing={len(ings)} steps={len(sts)}")
                res[r["slug"]] = {"ingredients": ings, "steps": sts, "tips": tps}
                break
            except Exception as e:
                if attempt == 3:
                    res[r["slug"]] = {"error": str(e)[:150]}
                else:
                    await asyncio.sleep(2 * (attempt + 1))
    done[0] += 1
    if done[0] % 20 == 0 or done[0] == total:
        json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"  {done[0]}/{total}", flush=True)


async def main():
    import httpx
    load_env()
    recs = json.load(open(SRC, encoding="utf-8"))
    raw = {}
    if os.path.exists(RAW):
        for p in json.load(open(RAW, encoding="utf-8")):
            m = re.search(r"/(\d{4})/(\d{2})/([^/]+?)\.html", p.get("url", ""))
            if m:
                raw[f"{m.group(1)}-{m.group(2)}-{m.group(3)}"] = re.sub(
                    r"<[^>]+>", " ", p.get("content", ""))
    res = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    res = {k: v for k, v in res.items() if "error" not in v}

    todo = [r for r in recs if r["slug"] not in res and needs_fix(r)]
    if "--limit" in sys.argv:
        todo = todo[: int(sys.argv[sys.argv.index("--limit") + 1])]
    print(f"fixing {len(todo)} of {len(recs)} (done: {len(res)})", flush=True)
    if todo:
        sem = asyncio.Semaphore(MAX_CONC)
        done = [0]
        async with httpx.AsyncClient() as client:
            await asyncio.gather(*[one(client, r, raw.get(r["slug"], ""), sem, res, done, len(todo))
                                   for r in todo])
        json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    bad = [k for k, v in res.items() if "error" in v]
    print(f"DONE {len(res)} written, {len(bad)} failed")


if __name__ == "__main__":
    asyncio.run(main())
