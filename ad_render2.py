#!/usr/bin/env python3
"""
Creative renderer v2 — per-link copy, three-row card.

VARIAN "TIGA PINTU" (three):
    Full card. Header (icon + product name + Ditaja) then three rows.
    Each row = one affiliate link = one kitchen problem = its own button.
    Equal visual weight so no link is structurally starved of clicks.

VARIAN "PADAT" (compact):
    For second/mid slots. Row 1 expanded, rows 2-3 one line each, still with
    their own hook text as the click label (never "Pilihan 2").

VARIAN "BAR" (bar):
    Narrow K1 bar. One rotated row + one button.

Every row is an <a> with rel="sponsored nofollow noopener" target="_blank".
Soft-sell only: no exclamation marks, no urgency, no price claims.
"""
import json, html, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import ads_wired2, ad_art

OUT = BASE / "ad_preview"
OUT.mkdir(exist_ok=True)

ARROW = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path d="M4 12h15M12 5l7 7-7 7"/></svg>')

REL = 'rel="sponsored nofollow noopener" target="_blank"'

CSS = """
.adw{--terra:#C25E3A;--terra-d:#A34A2C;--cream:#FDF6F0;--cream-d:#F0E0D2;
 --ink:#2B2320;--muted:#5C4F47;--chip:#F1E4D8;--chipink:#6E5548;--rowbg:#FBF3EC;
 font-family:Georgia,'Times New Roman',serif;color:var(--ink);background:var(--cream);
 border:1px solid var(--cream-d);border-radius:16px;position:relative;
 overflow:hidden;display:block;transition:border-color .18s ease}
.adw:hover{border-color:#DCC9B8}
.adw *{box-sizing:border-box}

/* disclosure chip — mandatory on every variant */
.adw__disc{position:absolute;top:11px;right:12px;z-index:3;
 font-family:system-ui,-apple-system,'Segoe UI',sans-serif;font-size:9.5px;
 letter-spacing:.09em;text-transform:uppercase;color:#5E463A;font-weight:800;
 background:var(--chip);padding:4px 8px;border-radius:5px;line-height:1;
 border:1px solid #E6D2BD}

/* header */
.adw__head{display:flex;align-items:center;gap:11px;padding:15px 18px 13px}
.adw__art{flex:none;display:grid;place-items:center}
.adw__art svg{display:block}
.adw__name{font-size:15.5px;font-weight:700;margin:0;letter-spacing:-.01em;line-height:1.2}
.adw__kick{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;font-size:9.5px;
 letter-spacing:.13em;text-transform:uppercase;color:var(--terra);font-weight:800;
 margin:0 0 3px}

/* rows */
.adw__rows{display:flex;flex-direction:column}
.adw__row{display:block;text-decoration:none;color:var(--ink);
 padding:13px 18px;border-top:1px solid var(--cream-d);position:relative;
 transition:background .15s ease}
.adw__row:hover{background:var(--rowbg)}
.adw__rowtop{display:flex;align-items:center;gap:8px;margin:0 0 4px}
.adw__num{font-family:system-ui,sans-serif;font-size:9.5px;font-weight:800;color:#fff;
 background:var(--terra);border-radius:50%;width:17px;height:17px;display:grid;
 place-items:center;flex:none;line-height:1}
.adw__hook{font-size:14.5px;font-weight:600;font-style:italic;line-height:1.25;
 letter-spacing:-.01em;margin:0;flex:1}
.adw__promise{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;font-size:12.5px;
 line-height:1.5;color:var(--muted);margin:0 0 9px;padding-left:25px;max-width:52ch}
.adw__btn{display:inline-flex;align-items:center;gap:6px;margin-left:25px;
 background:var(--terra);color:#fff;font-family:system-ui,sans-serif;font-size:12px;
 font-weight:700;padding:7px 13px;border-radius:8px;white-space:nowrap;
 transition:background .15s ease}
.adw__row:hover .adw__btn{background:var(--terra-d)}
.adw__btn svg{width:12px;height:12px;flex:none}
.adw__note{font-family:system-ui,sans-serif;font-size:10px;color:#8A7A70;margin:11px 0 0;
 padding:0 18px 14px;line-height:1.45}
.adwbar__note{margin:0;padding:0 15px 12px}

/* compact rows 2-3 */
.adw__mini{display:flex;align-items:center;gap:9px;text-decoration:none;color:var(--terra-d);
 padding:10px 18px;border-top:1px solid var(--cream-d);
 font-family:system-ui,sans-serif;font-size:12.5px;font-weight:600}
.adw__mini:hover{background:var(--rowbg)}
.adw__minihook{flex:1;line-height:1.3}
.adw__mini svg{width:11px;height:11px;flex:none}

/* bar */
.adwbar{padding:0}
.adwbar .adw__head{padding:12px 15px 0}
.adwbar__body{padding:0 15px 4px 15px}
.adwbar__txt{min-width:0}
.adwbar__hook{font-size:13px;font-weight:600;font-style:italic;margin:0 0 3px;line-height:1.25}
.adwbar__prom{font-family:system-ui,sans-serif;font-size:11.5px;color:var(--muted);
 margin:0;line-height:1.45}
.adwbar__btn{display:inline-flex;align-items:center;gap:5px;background:var(--terra);color:#fff;
 font-family:system-ui,sans-serif;font-size:11.5px;font-weight:700;padding:8px 12px;
 border-radius:8px;text-decoration:none;white-space:nowrap}
.adwbar__btn svg{width:11px;height:11px}
.adwbar__alts{display:flex;gap:6px;padding:8px 15px 13px;flex-wrap:wrap}
.adwbar__alt{font-family:system-ui,sans-serif;font-size:10.5px;font-weight:600;
 color:var(--terra-d);background:var(--rowbg);border:1px solid var(--cream-d);
 border-radius:6px;padding:5px 8px;text-decoration:none;line-height:1.3}
.adwbar__alt:hover{border-color:var(--terra)}

/* NARROW (mobile bar): stack the button under the text — never side-by-side,
   it overlaps at <420px. Chips wrap naturally on their own line. */
@media (max-width:419px){
 .adwbar__body{display:block}
 .adwbar__btn{margin-top:8px}
}

/* WIDE (desktop 728x90): button rides right of the text block. */
@media (min-width:420px){
 .adwbar__body{display:flex;align-items:flex-start;gap:12px}
 .adwbar__txt{flex:1}
 .adwbar__btn{flex:none;margin-top:1px}
}
"""

DISCLOSURE = '<span class="adw__disc" title="Iklan berbayar">Ditaja</span>'
NOTE = "Pautan rakan kongsi. Harga dan stok boleh berubah."


def _art(key, size):
    svg = ad_art.illustration_for(
        {"oven": "Oven / Ketuhar", "mixer": "Mixer / Pengadun", "blender": "Blender",
         "pengisar": "Pengisar / Grinder",
         "ricecooker": "Rice Cooker (Periuk Nasi Elektrik)",
         "grillpan": "Grill Pan / Pemanggang", "microwave": "Microwave",
         "freezer": "Freezer / Peti Sejuk Beku", "waffle": "Waffle Maker",
         "takoyaki": "Acuan Takoyaki", "pressure": "Pressure Cooker", "kuali": "Kuali",
         "periuk": "Periuk", "loyang": "Loyang / Acuan Kek",
         "kukus": "Pengukus (Kukusan)", "acuan": "Acuan Kuih / Kek"}[key])
    svg = svg.replace(' width="96" height="96"', "")
    return svg.replace("<svg ", f'<svg width="{size}" height="{size}" ', 1)


def _head(c, art_size=34):
    return f"""<div class="adw__head">
    <div class="adw__art">{_art(c['key'], art_size)}</div>
    <div><p class="adw__kick">Shopee Malaysia</p>
    <h3 class="adw__name">{html.escape(c['label'])}</h3></div>
  </div>"""


# ------------------------------------------------------------- TIGA PINTU
def variant_three(c):
    rows = "".join(f"""<a class="adw__row" href="{html.escape(r['url'])}" {REL}
   data-aff="{r['aff']}">
    <div class="adw__rowtop"><span class="adw__num">{i+1}</span>
      <p class="adw__hook">{html.escape(r['hook'])}</p></div>
    <p class="adw__promise">{html.escape(r['promise'])}</p>
    <span class="adw__btn">{html.escape(r['btn'])} {ARROW}</span>
  </a>""" for i, r in enumerate(c["rows"]))

    return f"""<div class="adw" data-product="{c['key']}" data-variant="three">
  {DISCLOSURE}
  {_head(c, 38)}
  <div class="adw__rows">{rows}</div>
  <p class="adw__note">{NOTE}</p>
</div>"""


# ----------------------------------------------------------------- PADAT
def variant_compact(c):
    r0 = c["rows"][0]
    mini = "".join(f"""<a class="adw__mini" href="{html.escape(r['url'])}" {REL}
   data-aff="{r['aff']}"><span class="adw__num">{i+2}</span>
   <span class="adw__minihook">{html.escape(r['hook'])} — {html.escape(r['btn'])}</span>
   {ARROW}</a>""" for i, r in enumerate(c["rows"][1:]))

    return f"""<div class="adw" data-product="{c['key']}" data-variant="compact">
  {DISCLOSURE}
  {_head(c, 30)}
  <a class="adw__row" href="{html.escape(r0['url'])}" {REL} data-aff="{r0['aff']}">
    <div class="adw__rowtop"><span class="adw__num">1</span>
      <p class="adw__hook">{html.escape(r0['hook'])}</p></div>
    <p class="adw__promise">{html.escape(r0['promise'])}</p>
    <span class="adw__btn">{html.escape(r0['btn'])} {ARROW}</span>
  </a>
  {mini}
  <p class="adw__note">{NOTE}</p>
</div>"""


# ------------------------------------------------------------------- BAR
def variant_bar(c):
    r0 = c["rows"][0]
    alts = "".join(f"""<a class="adwbar__alt" href="{html.escape(r['url'])}" {REL}
   data-aff="{r['aff']}">{html.escape(r['hook'])}</a>"""
                   for r in c["rows"][1:])

    return f"""<div class="adw adwbar" data-product="{c['key']}" data-variant="bar">
  {DISCLOSURE}
  {_head(c, 26)}
  <div class="adwbar__body">
    <div class="adwbar__txt">
      <p class="adwbar__hook">{html.escape(r0['hook'])}</p>
      <p class="adwbar__prom">{html.escape(r0['promise'])}</p>
    </div>
    <a class="adwbar__btn" href="{html.escape(r0['url'])}" {REL} data-aff="{r0['aff']}">
      {html.escape(r0['btn'])} {ARROW}</a>
  </div>
  <div class="adwbar__alts">{alts}</div>
  <p class="adw__note adwbar__note">{NOTE}</p>
</div>"""


VARIANTS = {"three": variant_three, "compact": variant_compact, "bar": variant_bar}


def render(c, variant="three"):
    return VARIANTS[variant](c)


def render_page(recipe, slug, variant_map):
    out = []
    for slot, c in ads_wired2.page_ads(recipe, slug, variant_map):
        out.append((slot, render(c, variant_map[slot])))
    return out


# --------------------------------------------------------------- preview
def build_preview():
    REC = json.load(open(BASE / "src/content_fix.json"))
    real = {}
    for slug, rec in REC.items():
        cands = ads_wired2.candidates(rec)
        for k in cands:
            if k not in real:
                real[k] = (slug, rec, k)

    blocks = []
    for key in ads_wired2.ORDER:
        if key not in real:
            continue
        slug, rec, _ = real[key]
        n_c = len(ads_wired2.candidates(rec))
        c = ads_wired2.build_creative(key, slug, "R1")
        blocks.append(f"""
<section class="demo">
  <h2>{html.escape(c['label'])}<span class="tag">{key}</span>
    <span class="tag alt">{n_c} produk dikesan</span></h2>
  <p class="src">Resepi sebenar: <code>{slug}</code></p>
  <div class="row">
    <div><p class="vl">Varian Tiga Pintu — 3 pautan, 3 copy</p>{variant_three(c)}</div>
    <div><p class="vl">Varian Padat — slot kedua</p>{variant_compact(c)}</div>
    <div class="narrow"><p class="vl">Varian Bar — 320×100 / 728×90</p>{variant_bar(c)}</div>
  </div>
</section>""")

    page = f"""<!doctype html>
<html lang="ms"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pratonton iklan — copy unik setiap pautan</title>
<meta name="robots" content="noindex,nofollow">
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#FCF8F4;color:#2B2320;padding:32px 20px 100px;
 font-family:system-ui,-apple-system,'Segoe UI',sans-serif}}
h1{{font-family:Georgia,serif;font-size:27px;font-weight:600;margin:0 0 8px;
 font-style:italic;letter-spacing:-.02em}}
.lede{{color:#6B5A50;font-size:14px;max-width:74ch;line-height:1.65;margin:0 0 8px}}
.lede b{{color:#2B2320}}
.meta{{color:#8A7A70;font-size:12.5px;margin:0 0 8px}}
.stats{{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0 36px}}
.stat{{background:#fff;border:1px solid #EFE3D8;border-radius:11px;padding:11px 15px;min-width:110px}}
.stat b{{display:block;font-size:20px;font-family:Georgia,serif;color:#C25E3A;line-height:1.1}}
.stat span{{font-size:11px;color:#8A7A70;letter-spacing:.03em}}
.demo{{border-top:1px solid #EFE3D8;padding:30px 0 10px}}
h2{{font-family:Georgia,serif;font-size:18px;font-weight:600;margin:0 0 5px;font-style:italic}}
.tag{{font-family:system-ui,sans-serif;font-size:9.5px;font-weight:700;letter-spacing:.08em;
 text-transform:uppercase;background:#F1E4D8;color:#6E5548;padding:3px 7px;border-radius:5px;
 vertical-align:middle;margin-left:7px}}
.tag.alt{{background:#E4EEF2;color:#3D5A66}}
.src{{font-size:11.5px;color:#8A7A70;margin:0 0 18px}}
.src code{{background:#F5E8DC;padding:2px 6px;border-radius:4px;font-size:11px}}
.row{{display:flex;gap:24px;flex-wrap:wrap;align-items:flex-start}}
.row>div{{flex:1;min-width:320px;max-width:440px}}
.row>div.narrow{{max-width:400px;flex:1 1 340px}}
.vl{{font-family:system-ui,sans-serif;font-size:10px;letter-spacing:.14em;
 text-transform:uppercase;color:#9A7F72;font-weight:700;margin:0 0 9px}}
{CSS}
</style></head><body>
<h1>Copy unik untuk setiap pautan afiliasi</h1>
<p class="lede">Setiap satu daripada <b>48 pautan</b> membawa copy sendiri — hook masalah
dapur, janji penyelesaian, dan butang sendiri. Tiga pautan dalam satu kad menyerang
<b>tiga masalah berbeza</b>, jadi tiada pautan yang jadi hiasan. Semua hook disandarkan
pada bahasa kegagalan yang memang ada dalam 748 resepi sendiri.</p>
<p class="meta">Hanya 16 produk berpaut. Resepi yang menyebut satu produk sahaja dapat
<b>satu iklan</b>, bukan dua iklan produk sama.</p>
<div class="stats">
  <div class="stat"><b>48</b><span>copy unik</span></div>
  <div class="stat"><b>16</b><span>produk</span></div>
  <div class="stat"><b>3</b><span>masalah per kad</span></div>
  <div class="stat"><b>519</b><span>resepi dapat iklan</span></div>
  <div class="stat"><b>183/154/182</b><span>baris-1 rotation</span></div>
</div>
{''.join(blocks)}
</body></html>"""
    p = OUT / "per_link.html"
    p.write_text(page)
    return p, len(blocks)


if __name__ == "__main__":
    p, n = build_preview()
    print("wrote", p)
    print("products:", n)
    print("size:", p.stat().st_size, "bytes")
