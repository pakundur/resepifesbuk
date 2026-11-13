"""Fix Indonesian vocabulary that the full-site LLM audit found in body text.

The audit of all 748 built pages returned real Indonesian words that survived
the earlier copy-layer pass because they live in the repaired ingredients,
steps and tips rather than in the headline/intro/meta:

  cabai -> cili          cabe -> cili           bikin -> buat
  merica -> lada         kemiri -> buah keras   diramas -> digaul
  dihaluskan -> dikisar halus                   gaul (fine in BM, keep)

This pass rewrites the affected LINES with an LLM so the sentence stays
grammatical — a blind word swap would produce "cili kering yang dikisar" in one
place and awkward phrasing in another. Only lines containing a known Indonesian
term are sent, so the call volume is tiny.

Reads/writes src/content_fix.json. Then re-run build + verify_all.py.
"""
import json, os, re, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(ROOT, "src", "content_fix.json")
RW = os.path.join(ROOT, "src", "rewrite.json")
ENV = os.path.expanduser("~/.hermes/.env")
MODEL, MAX_CONC = "deepseek-chat", 6

ID_PAT = re.compile(
    r"\b(cabai|cabe|bikin|merica|kemiri|diramas|dihaluskan|ketumbar bubuk|"
    r"bawang bombay|kentang putih|gula putih|wortel|udah|banget|"
    r"gimana|doang|emang|pisan|saus|aduk|belado|berlado|diblend|"
    r"daun jeruk|jeruk nipis|kecap)\b", re.I)

# written shortforms that must be spelled out (NOT colloquial-but-correct words)
SHORT_PAT = re.compile(r"\b(yg|dgn|utk|sbb|tp|takde|xde|blh|sgt|mcm|dpt|jd|"
                       r"kalo|smpi|jgn)\b", re.I)

SYSTEM = """Anda editor bahasa Melayu Malaysia. Teks ini mengandungi perkataan Indonesia
dan singkatan tulisan pendek.

Tukar perkataan Indonesia kepada Melayu Malaysia:
  cabai / cabe -> cili          bikin -> buat
  merica -> lada                kemiri -> buah keras
  diramas -> digaul             dihaluskan -> dikisar halus
  bawang bombay -> bawang besar kentang putih -> kentang
  gula putih -> gula pasir      wortel -> lobak merah
  udah -> sudah                 banget / pisan -> sangat
  saus -> sos                   aduk -> kacau
  belado / berlado -> berlada   diblend / blend -> dikisar
  daun jeruk -> daun limau purut
  jeruk nipis -> limau nipis     kecap -> kicap
  diblend -> dikisar           belado / berlado -> berlada

Tukar singkatan kepada perkataan penuh:
  yg -> yang        dgn -> dengan       utk -> untuk
  sbb -> sebab      tp -> tapi          takde -> tiada
  xde -> tiada      blh -> boleh        sgt -> sangat
  mcm -> macam      dpt -> dapat        jd -> jadi
  kalo -> kalau     smpi -> sampai      jgn -> jangan

PERATURAN:
1. JANGAN ubah sukatan, nama bahan lain, atau maksud ayat.
2. Kekalkan struktur ayat dan gaya santai Melayu yang sedia ada.
3. Nama jenama (Adabi, Maggi, Nestum, Oreo) jangan diusik.
4. Ayat mesti kekal gramatis selepas penggantian.

Balas JSON sahaja: {"lines": ["baris dibetulkan", "..."]}"""


def load_env():
    for line in open(ENV, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def collect(fx, rw):
    hits = []
    for slug, v in fx.items():
        for field in ("ingredients", "steps", "tips"):
            for ln in v.get(field, []):
                if ID_PAT.search(ln) or SHORT_PAT.search(ln):
                    hits.append((slug, field, ln))
    for slug, v in rw.items():
        for field in ("headline", "intro", "meta_desc"):
            t = v.get(field, "")
            if ID_PAT.search(t) or SHORT_PAT.search(t):
                hits.append((slug, field, t))
    return hits


async def batch_call(client, batch, out):
    lines = [h[2] for h in batch]
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
                new = re.sub(r"^\d+[.)]\s*", "", str(new).strip())
                if new and len(new) >= max(3, int(len(old) * 0.5)):
                    out.append((slug, field, old, new))
            return
        except Exception:
            if attempt == 2:
                return
            await asyncio.sleep(2)


async def main():
    import httpx
    load_env()
    fx = json.load(open(FIX, encoding="utf-8"))
    rw = json.load(open(RW, encoding="utf-8"))
    hits = collect(fx, rw)
    print(f"lines with Indonesian terms: {len(hits)}")
    if not hits:
        return

    out = []
    sem = asyncio.Semaphore(MAX_CONC)

    async def run(b):
        async with sem:
            await batch_call(client, b, out)

    batches = [hits[i:i + 20] for i in range(0, len(hits), 20)]
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[run(b) for b in batches])

    for slug, field, old, new in out:
        if slug in fx and field in ("ingredients", "steps", "tips"):
            fx[slug][field] = [new if x == old else x for x in fx[slug][field]]
        elif slug in rw and field in ("headline", "intro", "meta_desc"):
            rw[slug][field] = new

    json.dump(fx, open(FIX, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(rw, open(RW, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    left = collect(fx, rw)
    print(f"rewritten: {len(out)} | remaining: {len(left)}")
    for s, f, l in left[:6]:
        print("  still:", s[:36], f, l[:60])


if __name__ == "__main__":
    asyncio.run(main())
