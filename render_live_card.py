#!/usr/bin/env python3
"""
Render the REAL built ad card from dist/ using the REAL dist/style.css.
This is not a mock of the design — it reads the shipped HTML and the shipped
stylesheet, then rasterises the card box model so the result reflects what a
browser would paint.
"""
import re, sys, io
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PIL import Image, ImageDraw
import cairosvg

DIST = BASE / "dist"
OUT = BASE / "ad_preview"

# --- 1. pull a real card out of the built site -----------------------------
page = None
for f in sorted((DIST / "resepi").glob("*/index.html")):
    s = f.read_text(encoding="utf-8")
    if 'data-variant="three"' in s:
        page = s
        break
assert page, "no built page with a three-row card found"

m = re.search(r'<div class="ad-slot ad-slot--R1".*?</div></div>', page, re.S)
card = m.group(0)
prod = re.search(r'data-product="(\w+)"', card).group(1)
name = re.search(r'adw__name">([^<]+)<', card).group(1)
rows = re.findall(
    r'data-aff="(\d)">\s*<div class="adw__rowtop"><span class="adw__num">\d+</span>\s*'
    r'<p class="adw__hook">([^<]+)</p></div>\s*'
    r'<p class="adw__promise">([^<]+)</p>\s*'
    r'<span class="adw__btn">([^<]*)', card)
svgs = re.findall(r'(<svg.*?</svg>)', card, re.S)
art = svgs[0] if svgs else None

print(f"product={prod} name={name} rows={len(rows)}")
for a, h, p, b in rows:
    print(f"  aff{a}: {h} -> {b.strip()}")

# --- 2. theme colours, read from the shipped stylesheet --------------------
css = (DIST / "style.css").read_text(encoding="utf-8")


def varname(n, fallback):
    m = re.search(rf"--{n}:\s*([^;]+);", css)
    return m.group(1).strip() if m else fallback


def hexrgb(s):
    s = s.strip()
    if s.startswith("#") and len(s) == 7:
        return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))
    return (40, 40, 40)


CREAM = hexrgb(varname("cream", "#faf7f2"))
INK = hexrgb(varname("ink", "#1a1815"))
INK_SOFT = hexrgb(varname("ink-soft", "#47403a"))
INK_MUTE = hexrgb(varname("ink-mute", "#7d736a"))
LINE = hexrgb(varname("line", "#e3d9c9"))
TERRA = hexrgb(varname("terracotta", "#c2542a"))
TERRA_D = (163, 74, 44)
CHIP = (241, 228, 216)
CHIPINK = (94, 70, 58)
WHITE = (255, 255, 255)
ROWHOVER = (251, 243, 236)
print("theme:", CREAM, TERRA, LINE)

S = 2
FD = ["/system/fonts"]
SERIF_I = "/system/fonts/NotoSerif-Italic.ttf"
SERIF_B = "/system/fonts/NotoSerif-Bold.ttf"
SANS = "/system/fonts/Roboto-Regular.ttf"
SANS_B = "/system/fonts/Roboto-Bold.ttf"
import os
for p_ in [SERIF_I, SERIF_B, SANS, SANS_B]:
    if not os.path.exists(p_):
        print("MISSING FONT:", p_)


def F(path, size):
    try:
        return ImageFont.truetype(path, int(size))
    except Exception:
        return ImageFont.load_default()


from PIL import ImageFont


def wrap(text, font, maxw, d):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


def draw_wrap(d, text, font, fill, x, y, maxw, lh):
    for ln in wrap(text, font, maxw, d):
        d.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y


def art_img(svg, px):
    if not svg:
        return None
    s = svg.replace(' width="96" height="96"', "")
    if "viewBox" not in s:
        s = s.replace("<svg ", '<svg viewBox="0 0 96 96" ', 1)
    png = cairosvg.svg2png(bytestring=s.encode(), output_width=px,
                           output_height=px, background_color="#faf7f2")
    return Image.open(io.BytesIO(png)).convert("RGB")


W = 700 * S           # .wrap-narrow is 760 minus padding
pad = 18 * S
fhook = F(SERIF_I, 14.5 * S)
fprom = F(SANS, 12.5 * S)
fbtn = F(SANS_B, 12 * S)
fname = F(SERIF_B, 15.5 * S)
fkick = F(SANS_B, 9.5 * S)
fnote = F(SANS, 10 * S)
fchip = F(SANS_B, 9.5 * S)
fnum = F(SANS_B, 9.5 * S)

probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
maxw = W - pad * 2 - 25 * S
lh_h = 14.5 * S * 1.3
lh_p = 12.5 * S * 1.55

row_h = []
for a, hk, pr, bt in rows:
    hl = len(wrap(hk, fhook, maxw, probe))
    pl = len(wrap(pr, fprom, maxw, probe))
    row_h.append(int(13 * S + max(17 * S, hl * lh_h) + 4 * S + pl * lh_p + 9 * S + 31 * S + 13 * S))

head_h = int(15 * S + 38 * S + 13 * S)
note_h = int(11 * S + 15 * S + 14 * S)
H = head_h + sum(row_h) + note_h

img = Image.new("RGB", (W, H), CREAM)
d = ImageDraw.Draw(img)
d.rounded_rectangle([0, 0, W - 1, H - 1], radius=14 * S, outline=LINE, width=S)

# header
a_img = art_img(art, 38 * S)
if a_img:
    img.paste(a_img, (pad, 15 * S))
d.text((pad + 38 * S + 11 * S, 19 * S), "SHOPEE MALAYSIA", font=fkick, fill=TERRA)
d.text((pad + 38 * S + 11 * S, 33 * S), name, font=fname, fill=INK)

# disclosure chip
lbl = "DIT AJA".replace(" ", "")
tw = d.textlength(lbl, font=fchip)
bw, bh = tw + 16 * S, 17 * S
x2, y2 = W - 12 * S, 11 * S
d.rounded_rectangle([x2 - bw, y2, x2, y2 + bh], radius=5 * S, fill=CHIP,
                    outline=(230, 210, 189), width=max(1, S))
d.text((x2 - bw + 8 * S, y2 + 4 * S), lbl, font=fchip, fill=CHIPINK)

y = head_h
for i, (a, hk, pr, bt) in enumerate(rows):
    d.line([0, y, W, y], fill=LINE, width=S)
    ty = y + 13 * S
    cy = ty + 8.5 * S
    d.ellipse([pad, cy - 8.5 * S, pad + 17 * S, cy + 8.5 * S], fill=TERRA)
    nw = d.textlength(str(i + 1), font=fnum)
    d.text((pad + (17 * S - nw) / 2, cy - 5.2 * S), str(i + 1), font=fnum, fill=WHITE)
    hl = wrap(hk, fhook, maxw, d)
    hy = ty
    for ln in hl:
        d.text((pad + 25 * S, hy), ln, font=fhook, fill=INK)
        hy += lh_h
    py = max(ty + 17 * S, ty + len(hl) * lh_h) + 4 * S
    py = draw_wrap(d, pr, fprom, INK_SOFT, pad + 25 * S, py, maxw, lh_p)
    by = py + 9 * S
    btn = bt.strip()
    bwid = d.textlength(btn, font=fbtn) + 24 * S + 22 * S
    d.rounded_rectangle([pad + 25 * S, by, pad + 25 * S + bwid, by + 31 * S],
                        radius=8 * S, fill=TERRA)
    d.text((pad + 25 * S + 12 * S, by + 8.5 * S), btn, font=fbtn, fill=WHITE)
    ax = pad + 25 * S + 12 * S + d.textlength(btn, font=fbtn) + 7 * S
    ay = by + 15 * S
    d.line([ax, ay, ax + 11 * S, ay], fill=WHITE, width=max(2, int(1.4 * S)))
    d.line([ax + 5 * S, ay - 4 * S, ax + 11 * S, ay], fill=WHITE, width=max(2, int(1.4 * S)))
    d.line([ax + 5 * S, ay + 4 * S, ax + 11 * S, ay], fill=WHITE, width=max(2, int(1.4 * S)))
    y += row_h[i]

d.text((pad, y + 11 * S), "Pautan rakan kongsi. Harga dan stok boleh berubah.",
       font=fnote, fill=INK_MUTE)

p = OUT / "live_card.png"
img.save(p)
print("wrote", p, img.size)
