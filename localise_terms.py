"""Localise leftover English terms in Malay recipe copy.

The LLM audit found English words sitting inside otherwise-Malay text:
"kitchen towel", "baking soda", "corn kernel", "paste", "blender". Some are
genuinely untranslatable brand/technical terms (mozzarella, baking powder is
commonly used), so this pass is deliberately narrow:

  - It targets a curated list of common English cooking words that DO have a
    natural Malay equivalent.
  - It rewrites the whole line so the result reads naturally, rather than
    swapping words mechanically.
  - It never touches ingredients it does not recognise.

Reads/writes src/content_fix.json (ingredients/steps/tips) and src/rewrite.json
(intro/meta). Idempotent: lines with no English term are left untouched.
"""
import json, os, re, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(ROOT, "src", "content_fix.json")
RW = os.path.join(ROOT, "src", "rewrite.json")
ENV = os.path.expanduser("~/.hermes/.env")
MODEL, MAX_CONC = "deepseek-chat", 6

# English terms with a natural Malay equivalent. Deliberately excludes words
# Malaysians legitimately use as-is (mozzarella, baking powder, blender is
# borderline but "pengisar" is the proper term).
EN2MY = {
    "kitchen towel": "tuala dapur",
    "aluminium foil": "kerajang aluminium",
    "baking soda": "soda bikarbonat",
    "baking powder": "serbuk penaik",
    "corn kernel": "biji jagung",
    "corn flour": "tepung jagung",
    "self-raising flour": "tepung naik sendiri",
    "plain flour": "tepung gandum",
    "ice cream": "ais krim",
    "spring onion": "daun bawang",
    "spring roll": "popia",
    "soy sauce": "kicap",
    "oyster sauce": "sos tiram",
    "sesame oil": "minyak bijan",
    "curry powder": "serbuk kari",
    "chilli powder": "serbuk cili",
    "pepper": "lada",
    "white pepper": "lada sulah",
    "sausage": "sosej",
    "cheese": "keju",
    "butter": "mentega",
    "cream cheese": "krim keju",
    "condensed milk": "susu pekat manis",
    "evaporated milk": "susu sejat",
    "whipping cream": "krim putar",
    "food colouring": "pewarna makanan",
    "vanilla essence": "esen vanila",
    "rose essence": "esen ros",
    "pandan paste": "pes pandan",
    "chicken stock": "stok ayam",
    "beef stock": "stok daging",
    "tomato sauce": "sos tomato",
    "chilli sauce": "sos cili",
    "blend": "kisar",
    "paste": "pes",
    "carrot": "lobak merah",
    "potato": "kentang",
    "onion": "bawang",
    "garlic": "bawang putih",
    "ginger": "halia",
}

PATTERN = re.compile(r"\b(" + "|".join(re.escape(k) for k in
                                       sorted(EN2MY, key=len, reverse=True)) + r")\b", re.I)

SYSTEM = """Anda editor resepi Malaysia. Teks ini bercampur Bahasa Melayu dengan perkataan Inggeris.

Tugas: tukar perkataan Inggeris itu kepada istilah Melayu yang biasa digunakan di dapur Malaysia.

PANDUAN:
- kitchen towel -> tuala dapur      baking soda -> soda bikarbonat
- baking powder -> serbuk penaik    corn kernel -> biji jagung
- aluminium foil -> kerajang aluminium
- corn flour -> tepung jagung      plain flour -> tepung gandum
- ice cream -> ais krim            spring onion -> daun bawang
- soy sauce -> kicap               oyster sauce -> sos tiram
- sesame oil -> minyak bijan       chilli powder -> serbuk cili
- white pepper -> lada sulah       condensed milk -> susu pekat manis
- food colouring -> pewarna makanan
- carrot -> lobak merah            potato -> kentang
- blend -> kisar                   paste -> pes

JANGAN tukar nama jenama (Adabi, Maggi, Nestum, Oreo, Horlicks).
JANGAN tukar istilah yang memang tiada padanan Melayu (mozzarella, parmesan).
Bahasa Melayu Malaysia, bukan Indonesia. Jangan ubah maksud atau sukatan.

Balas JSON sahaja: {"lines": ["baris yang telah dibetulkan", "..."]}"""


def load_env():
    for line in open(ENV, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def dirty_lines(fx):
    out = []
    for slug, v in fx.items():
        for field in ("ingredients", "steps", "tips"):
            for ln in v.get(field, []):
                if PATTERN.search(ln):
                    out.append((slug, field, ln))
    return out


async def localise_batch(client, batch, res):
    lines = [ln for _, _, ln in batch]
    payload = {"model": MODEL,
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": "\n".join(f"{i+1}. {l}" for i, l in enumerate(lines))}],
               "temperature": 0.1, "max_tokens": 1200,
               "response_format": {"type": "json_object"}}
    headers = {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
               "Content-Type": "application/json"}
    for attempt in range(3):
        try:
            r = await client.post("https://api.deepseek.com/chat/completions",
                                  json=payload, headers=headers, timeout=90)
            got = json.loads(r.json()["choices"][0]["message"]["content"]).get("lines", [])
            for (slug, field, old), new in zip(batch, got):
                new = str(new).strip()
                # keep the numbering prefix out, and never accept a blank
                new = re.sub(r"^\d+[.)]\s*", "", new)
                if new and len(new) >= max(3, len(old) * 0.5):
                    res.setdefault(slug, {}).setdefault(field, {})[old] = new
            return
        except Exception:
            if attempt == 2:
                return
            await asyncio.sleep(2)


async def main():
    import httpx
    load_env()
    fx = json.load(open(FIX, encoding="utf-8")) if os.path.exists(FIX) else {}
    dirty = dirty_lines(fx)
    print(f"lines containing English terms: {len(dirty)}")

    res = {}
    if dirty:
        batches = [dirty[i:i + 25] for i in range(0, len(dirty), 25)]
        sem = asyncio.Semaphore(MAX_CONC)

        async def run(b):
            async with sem:
                await localise_batch(client, b, res)

        async with httpx.AsyncClient() as client:
            await asyncio.gather(*[run(b) for b in batches])

    applied = 0
    for slug, fields in res.items():
        for field, repl in fields.items():
            lst = fx[slug].get(field, [])
            fx[slug][field] = [repl.get(x, x) for x in lst]
            applied += len(repl)
    json.dump(fx, open(FIX, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

    still = sum(1 for _, _, ln in dirty_lines(fx))
    print(f"rewritten lines: {applied} | still containing English terms: {still}")


if __name__ == "__main__":
    asyncio.run(main())
