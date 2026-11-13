"""Rewrite fully-Indonesian source recipes into Malaysian Malay.

One source recipe (Soto Ayam Terlajak Sedap) is written in Indonesian end to
end -- `merica`, `kemiri`, `lembar`, `tiriskan`, `di suwir2`, `bumbu blender`,
`kecap`, `tauge`, `kerupuk`, `wortel`. A blind word swap produces broken Malay,
so the whole recipe is rewritten by an LLM with a hard rule that quantities and
ingredient names must not change.

Writes into src/content_fix.json so the build picks it up. Then rebuild.
"""
import json, os, re, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(ROOT, "src", "content_fix.json")
CLEAN = os.path.join(ROOT, "src", "recipes_clean.json")
ENV = os.path.expanduser("~/.hermes/.env")
MODEL = "deepseek-chat"

TARGETS = ["resepi-soto-ayam-terlajak-sedap"]

SYSTEM = """Anda editor resepi bahasa Melayu Malaysia. Teks ini ditulis dalam Bahasa Indonesia
sepenuhnya. Tulis semula dalam Bahasa Melayu Malaysia yang santai tetapi betul.

KAMUS WAJIB:
  merica -> lada sulah          kemiri -> buah keras
  ketumbar -> ketumbar          jintan -> jintan
  tiriskan -> toskan            di suwir2 / disuwir -> carik
  bumbu -> rempah               bumbu blender -> rempah kisar
  kecap manis -> kicap manis    tauge -> taugeh
  kerupuk -> keropok            wortel -> lobak merah
  kobis -> kobis                lembar -> helai
  sendok teh -> sudu teh        sendok -> sudu
  siung -> ulas                 batang (serai) -> batang
  royco ayam -> Royco ayam      irisan -> hirisan
  di rebus -> direbus           di goreng -> digoreng
  di tumis -> ditumis           di kasih -> diberi
  di skip -> dilangkau          di sesuaikan -> disesuaikan
  aja -> sahaja                 biar -> biar
  kalau mau -> kalau nak        masing-masing -> masing-masing
  diblender -> dikisar          d perah -> diperah
  Icip2 -> Rasa secukupnya      trus -> terus
  santan kenal -> santan kental (jika pekat)

PERATURAN KETAT:
1. JANGAN ubah SEBARANG sukatan: "2 liter", "10 biji", "1/2 sudu teh", "2 cm" kekal.
2. JANGAN tambah bahan yang tiada dalam asal. JANGAN buang bahan.
3. Nama jenama (Royco) kekal.
4. Buang aksara pelik seperti \\u0002.
5. Setiap baris bahan mesti bahan sahaja. Setiap langkah mesti satu arahan sahaja.
6. Gaya santai Melayu Malaysia boleh guna "nak", "je", "dah" tetapi BUKAN Indonesia.
7. Hasilkan TIPS MASAKAN 2-3 baris khusus untuk soto ayam ini (petua praktikal,
   bukan cerita). Contoh sudut: rebus ayam kampung lama sikit supaya kuah manis,
   tumis rempah sampai pecah minyak supaya tak langu, hirisan kobis buang tulang.

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
    fx = json.load(open(FIX, encoding="utf-8")) if os.path.exists(FIX) else {}
    clean = json.load(open(CLEAN, encoding="utf-8"))
    by = {r["slug"]: r for r in clean}

    for slug in TARGETS:
        r = by.get(slug)
        if not r:
            print("MISSING", slug)
            continue
        body = ("BAHAN:\n" + "\n".join(str(x) for x in r.get("ingredients", []))
                + "\n\nLANGKAH:\n"
                + "\n".join((s.get("t") if isinstance(s, dict) else str(s))
                            for s in r.get("steps", [])))
        payload = {"model": MODEL,
                   "messages": [{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": body}],
                   "temperature": 0.2, "max_tokens": 2000,
                   "response_format": {"type": "json_object"}}
        headers = {"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}",
                   "Content-Type": "application/json"}
        async with httpx.AsyncClient() as client:
            r2 = await client.post("https://api.deepseek.com/chat/completions",
                                   json=payload, headers=headers, timeout=180)
            got = json.loads(r2.json()["choices"][0]["message"]["content"])
        ing = [re.sub(r"[\x00-\x08\x0b-\x1f]", "", str(x)).strip() for x in got.get("ingredients", [])]
        stp = [re.sub(r"[\x00-\x08\x0b-\x1f]", "", str(x)).strip() for x in got.get("steps", [])]
        tip = [re.sub(r"[\x00-\x08\x0b-\x1f]", "", str(x)).strip() for x in got.get("tips", [])]
        ing = [x for x in ing if x and not re.fullmatch(r"[^\w]+", x)]
        stp = [x for x in stp if x]
        tip = [x for x in tip if x]
        if len(ing) < 8 or len(stp) < 6 or not tip:
            print("REJECT (too short)", slug, len(ing), len(stp), len(tip))
            continue
        fx[slug] = {"ingredients": ing, "steps": stp, "tips": tip}
        print(f"OK {slug}: {len(ing)} bahan, {len(stp)} langkah, {len(tip)} tips")
        print("  sample ing:", ing[:3])
        print("  sample step:", stp[0])
        print("  sample tip:", tip[0])

    json.dump(fx, open(FIX, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print("written", FIX)


if __name__ == "__main__":
    asyncio.run(main())
