"""Generate unique category-page intros (21 pages) with DeepSeek.

Category hub pages currently carry one boilerplate sentence
("Semua resepi X dalam koleksi..."), which is thin duplicated content across
21 pages and adds nothing for a reader. This generates a real 2-3 sentence
intro per category, plus a distinct SEO title and meta description.

Output: src/cat_copy.json  {category: {title, meta_desc, intro}}
"""
import json, os, re, asyncio, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
OUT = os.path.join(ROOT, "src", "cat_copy.json")
ENV = os.path.expanduser("~/.hermes/.env")
MODEL = "deepseek-chat"

SYSTEM = """Anda penulis kandungan blog masakan Malaysia. Anda menulis Bahasa Melayu natural \
dan manusiawi, seperti kawan berkongsi pengalaman dapur, bukan penulis iklan.

PERATURAN:
1. Jangan reka fakta, statistik atau sejarah yang tidak pasti.
2. Jangan guna: "Selamat mencuba", "Gerenti", "pasti memikat", "tidak hairanlah".
3. Jangan guna em dash. Jangan guna emoji.
4. Ayat pelbagai panjang. Ada pendek, ada panjang.
5. Sebut nama kategori dan beberapa contoh hidangan sebenar yang diberi.

Balas HANYA JSON: {"title": "...", "meta_desc": "...", "intro": "..."}"""


def load_env():
    if not os.path.exists(ENV):
        return
    for line in open(ENV, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


async def main():
    import httpx
    load_env()
    recs = json.load(open(SRC, encoding="utf-8"))
    by_cat = collections.defaultdict(list)
    for r in recs:
        by_cat[r["cats"][0] if r["cats"] else "Sayur"].append(r["title"])

    results = {}
    async with httpx.AsyncClient() as client:
        for cat, titles in sorted(by_cat.items()):
            sample = "\n".join("- " + t for t in titles[:12])
            prompt = f"""Kategori: {cat}
Jumlah resepi dalam kategori ini: {len(titles)}
Contoh hidangan:
{sample}

Tulis:
- title: maksimum 60 aksara, mesti ada perkataan "Resepi" dan nama kategori.
- meta_desc: 150-158 aksara, ayat lengkap, sebut jenis hidangan dalam kategori.
- intro: 2-3 ayat untuk pembuka halaman kategori. Terangkan apa yang menyatukan hidangan dalam kategori ini dan bila orang Malaysia selalu masak. Biar khusus, bukan generik."""
            try:
                r = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"},
                    json={"model": MODEL, "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": prompt}],
                        "temperature": 0.8, "max_tokens": 600,
                        "response_format": {"type": "json_object"}},
                    timeout=120,
                )
                d = r.json()["choices"][0]["message"]["content"]
                results[cat] = json.loads(d)
                print(f"  ok {cat}: {results[cat]['title'][:50]}")
            except Exception as e:
                print(f"  FAIL {cat}: {str(e)[:100]}")

    json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nsaved {len(results)} category copies -> {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
