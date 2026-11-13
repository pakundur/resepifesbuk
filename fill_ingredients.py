"""Fill ingredient lists for recipes where the source HTML had none.

25 posts parsed with zero ingredients (old Blogger posts with no section
markup). The main rewrite already produced clean steps for them, but a Recipe
page with no `recipeIngredient` cannot earn a rich result and reads broken.

This makes a narrow second LLM call per recipe: given the title, the original
raw text and the already-generated steps, extract ONLY a clean ingredient
list. Explicitly forbidden from inventing quantities that are not in the text.

Output is merged into src/recipes_clean.json (field: ingredients).
Usage:  python fill_ingredients.py [--apply]
"""
import json, os, re, sys, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "recipes_clean.json")
RW = os.path.join(ROOT, "src", "rewrite.json")
ENV = os.path.expanduser("~/.hermes/.env")
MODEL = "deepseek-chat"

SYSTEM = """Anda penyunting resepi Malaysia. Tugas anda HANYA menyenaraikan bahan-bahan.

PERATURAN KETAT:
1. Senaraikan HANYA bahan yang benar-benar disebut dalam teks yang diberi.
2. JANGAN reka bahan atau kuantiti yang tiada dalam teks.
3. Jika kuantiti tiada dalam teks, tulis bahan itu tanpa kuantiti (cth: "Garam secukup rasa").
4. Satu bahan satu baris. Tiada ayat arahan. Tiada perkataan "masukkan", "panaskan", "tumis".
5. Kekalkan format biasa resepi Malaysia: "200g tepung gandum", "3 ulas bawang putih".

Balas HANYA JSON: {"ingredients": ["...", "..."]}"""


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
    rw = json.load(open(RW, encoding="utf-8"))
    todo = [r for r in recs if not r["ingredients"]]
    print(f"recipes needing ingredients: {len(todo)}")
    if not todo:
        return

    async with httpx.AsyncClient() as client:
        for r in todo:
            v = rw.get(r["slug"], {})
            steps_txt = "\n".join(f"- {s}" for s in v.get("steps", []))
            prompt = f"""Hidangan: {r['title']}
Kategori: {r['cats'][0] if r['cats'] else 'Masakan'}

LANGKAH MEMASAK (rujukan, bahan disebut dalam langkah ini):
{steps_txt if steps_txt else '(tiada)'}

Teks asal mentah (mungkin bersepah):
{' '.join(r['ingredients']) if r['ingredients'] else ''}

Senaraikan semula bahan-bahan yang disebut dalam langkah dan teks di atas."""
            try:
                resp = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers={"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"},
                    json={"model": MODEL, "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": prompt}],
                        "temperature": 0.3, "max_tokens": 800,
                        "response_format": {"type": "json_object"}},
                    timeout=120,
                )
                d = json.loads(resp.json()["choices"][0]["message"]["content"])
                ings = [str(i).strip() for i in d.get("ingredients", []) if str(i).strip()]
                if len(ings) >= 2:
                    r["ingredients"] = ings
                    r["n_ing"] = len(ings)
                    print(f"  ok {len(ings):2d} {r['title'][:52]}")
                else:
                    print(f"  LOW {len(ings)} {r['title'][:52]}")
            except Exception as e:
                print(f"  FAIL {r['title'][:40]}: {str(e)[:80]}")

    left = sum(1 for r in recs if not r["ingredients"])
    print(f"\nstill zero-ingredient: {left}")
    if "--apply" in sys.argv:
        json.dump(recs, open(SRC, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"applied -> {SRC}")
    else:
        print("(dry run — pass --apply)")


if __name__ == "__main__":
    asyncio.run(main())
