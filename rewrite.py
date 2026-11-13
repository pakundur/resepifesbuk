"""Rewrite recipe copy with DeepSeek: human-sounding, SEO-tuned, BM-first.

Reads src/recipes_clean.json, writes src/rewrite.json keyed by slug.

What it generates per recipe:
  - headline      : <=60 chars, dish name first, one specific hook, no emoji,
                    no "Resepi Mudah & Sedap" tail
  - meta_desc     : 150-158 chars, complete sentence, real reason to click
  - intro         : 2-3 sentences, specific to THIS dish (texture, technique,
                    when Malaysians cook it) - no generic filler
  - steps         : cleaned imperative steps (only rewritten if source is messy)

Design notes:
  - Temperature 0.8 for variety across 748 pages, but the prompt pins the dish
    name and forbids inventing ingredients or quantities. Accuracy beats flair:
    the site is a recipe archive, so invented facts are unacceptable.
  - Resume-safe: skips slugs already in rewrite.json, so a killed run restarts
    where it stopped.
  - Concurrency 6: DeepSeek tolerates it and 748 calls finish in ~15 min.

Usage:
  python rewrite.py --limit 5        # test batch
  python rewrite.py                  # full run (resume-safe)
"""
import json, os, re, sys, time, asyncio, random

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
OUT = os.path.join(ROOT, "src", "rewrite.json")
ENV = os.path.expanduser("~/.hermes/.env")

MAX_CONC = 6
MODEL = "deepseek-chat"

SYSTEM = """Anda penulis kandungan resepi Malaysia yang berpengalaman 15 tahun untuk blog masakan. \
Anda menulis dalam Bahasa Melayu yang natural, hangat dan manusiawi - seperti kawan yang berkongsi \
resepi kegemaran, bukan seperti robot atau penulis iklan.

PERATURAN KETAT:
1. JANGAN reka bahan, kuantiti, masa memasak atau fakta yang tiada dalam data yang diberi.
2. JANGAN guna frasa klise ini: "Selamat mencuba", "Gerenti jadi", "Confirm sedap", \
"Rahsia yang anda perlu tahu", "pasti memikat selera", "tidak hairanlah".
3. JANGAN guna emoji dalam headline.
4. JANGAN guna em dash (—). Guna koma atau noktah.
5. Tulis ayat pelbagai panjang. Ada ayat pendek 3-5 patah perkataan. Ada yang panjang.
6. Bunyi seperti orang Malaysia menulis: guna "kita", "jangan risau", "memang", "cuma", \
"kalau", "kena" dengan kadar yang natural. Jangan berlebihan sampai jadi slanga.
7. Nama hidangan MESTI ada dalam headline dan biar kekal tepat seperti asal.
8. Headline guna Title Case yang konsisten: huruf besar pada setiap perkataan utama. \
Jangan campur huruf besar dan kecil merata-rata.
9. meta_desc mesti ayat lengkap yang tamat dengan noktah. Jangan tinggalkan ayat tergantung.

Balas HANYA dengan JSON yang sah, tiada teks lain:
{"headline": "...", "meta_desc": "...", "intro": "...", "steps": ["...", "..."]}"""


def load_env():
    if not os.path.exists(ENV):
        return
    for line in open(ENV, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def build_prompt(r):
    ings = "\n".join("- " + i for i in r["ingredients"][:40])
    steps = []
    for s in r["steps"]:
        if "h" in s:
            steps.append("[subjudul] " + s["h"])
        elif "t" in s:
            steps.append(s["t"])
    steps_txt = "\n".join(f"{n+1}. {s}" for n, s in enumerate(steps[:25]) if not s.startswith("[subjudul]"))
    tips = "\n".join("- " + t for t in r.get("tips", [])[:6])
    cat = r["cats"][0] if r["cats"] else "Masakan"

    return f"""Resepi: {r['title']}
Kategori: {cat}

BAHAN-BAHAN:
{ings}

CARA PENYEDIAAN (asal, mungkin bersepah):
{steps_txt if steps_txt else '(tiada langkah jelas - bina semula daripada bahan)'}

{f'TIPS ASAL:{chr(10)}{tips}' if tips else ''}

Tulis semula:
- headline: maksimum 60 aksara, nama hidangan di depan, satu tarikan khusus tentang hidangan ini. Tiada emoji. Tiada "Resepi Mudah & Sedap".
- meta_desc: 150-158 aksara, satu atau dua ayat lengkap, beri sebab untuk klik. Jangan potong ayat.
- intro: 2-3 ayat tentang hidangan INI khususnya (tekstur, teknik, bila orang masak). Jangan generik.
- steps: langkah memasak yang bersih dan logik, ayat arahan, satu tindakan utama satu langkah. Buang hashtag dan tanda "Selamat Mencuba"."""


async def call_one(client, r, sem, results, done, total):
    import httpx
    async with sem:
        prompt = build_prompt(r)
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.8,
            "max_tokens": 1400,
            "response_format": {"type": "json_object"},
        }
        for attempt in range(3):
            try:
                resp = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
                             "Content-Type": "application/json"},
                    json=payload, timeout=120,
                )
                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                txt = resp.json()["choices"][0]["message"]["content"]
                data = json.loads(txt)
                # validate
                hl = str(data.get("headline", "")).strip()
                md = str(data.get("meta_desc", "")).strip()
                intro = str(data.get("intro", "")).strip()
                steps = [str(s).strip() for s in data.get("steps", []) if str(s).strip()]
                if not hl or not md or not intro:
                    raise ValueError("missing field")
                results[r["slug"]] = {
                    "headline": hl, "meta_desc": md, "intro": intro, "steps": steps,
                }
                done[0] += 1
                if done[0] % 25 == 0:
                    print(f"  {done[0]}/{total} done", flush=True)
                    save(results)
                return
            except Exception as e:
                if attempt == 2:
                    print(f"  FAIL {r['slug'][:50]}: {str(e)[:120]}", flush=True)
                    results[r["slug"]] = {"error": str(e)[:200]}
                    return
                await asyncio.sleep(2 ** attempt)


def save(results):
    tmp = OUT + ".tmp"
    json.dump(results, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, OUT)


async def main():
    import httpx
    load_env()
    if "DEEPSEEK_API_KEY" not in os.environ:
        sys.exit("DEEPSEEK_API_KEY not found")

    recs = json.load(open(SRC, encoding="utf-8"))
    results = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    # drop previous errors so they retry
    results = {k: v for k, v in results.items() if "error" not in v}

    todo = [r for r in recs if r["slug"] not in results]
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
        todo = todo[:limit]

    print(f"{len(recs)} recipes | already done {len(results)} | todo {len(todo)}")
    if not todo:
        return

    sem = asyncio.Semaphore(MAX_CONC)
    done = [0]
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[call_one(client, r, sem, results, done, len(todo)) for r in todo])

    save(results)
    ok = sum(1 for v in results.values() if "error" not in v)
    print(f"\nsaved {ok} rewrites -> {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
