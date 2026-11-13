#!/usr/bin/env python3
"""Raster the REAL footer from dist/ using the REAL dist/style.css."""
import re, sys
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from PIL import Image, ImageDraw, ImageFont
import os

DIST = BASE / "dist"
OUT = BASE / "ad_preview"
h = (DIST / "index.html").read_text(encoding="utf-8")
foot = h[h.find("<footer"):h.find("</footer>")]
css = (DIST / "style.css").read_text(encoding="utf-8")


def varname(n, fb):
    m = re.search(rf"--{n}:\s*([^;]+);", css)
    return m.group(1).strip() if m else fb


def hexrgb(s):
    s = s.strip()
    if s.startswith("#") and len(s) == 7:
        return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))
    return (40, 40, 40)


CREAM = hexrgb(varname("cream", "#faf7f2"))
CREAM_DEEP = hexrgb(varname("cream-deep", "#f3ede2"))
INK_SOFT = hexrgb(varname("ink-soft", "#47403a"))
INK_MUTE = hexrgb(varname("ink-mute", "#7d736a"))
LINE = hexrgb(varname("line", "#e3d9c9"))

FONT = "/system/fonts/Roboto-Regular.ttf"
FONTB = "/system/fonts/Roboto-Bold.ttf"
FONTM = "/system/fonts/Roboto-Medium.ttf"
for f_ in (FONT, FONTB, FONTM):
    if not os.path.exists(f_):
        print("missing", f_)


def F(p, s):
    try:
        return ImageFont.truetype(p, int(s))
    except Exception:
        return ImageFont.load_default()


S = 2
W = 1180 * S
PAD = 20 * S
GAP = 40 * S
cols = [("Tentang Resepi Fesbuk", "text"), ("Maklumat", "links"), ("Pautan", "links")]
# grid-template-columns: 1.6fr 1fr 1fr
avail = W - PAD * 2 - GAP * 2
unit = avail / (1.6 + 1 + 1)
widths = [unit * 1.6, unit, unit]

desc = ("Koleksi resepi Malaysia yang mudah diikuti: bahan jelas, "
        "langkah demi langkah dan tips untuk berjaya kali pertama.")
links = {
    "Maklumat": ["Tentang Kami", "Pendedahan Affiliate", "RSS Feed"],
    "Pautan": ["Semua Resepi", "Semua Kategori", "Cari Resepi"],
}

fH = F(FONTM, 11.2 * S)
fA = F(FONT, 14.4 * S)
fB = F(FONT, 14.4 * S)
fDesc = F(FONT, 14.4 * S)

H = 300 * S
img = Image.new("RGB", (W, H), CREAM_DEEP)
d = ImageDraw.Draw(img)
d.line([0, 0, W, 0], fill=LINE, width=S)

x = PAD
for (name, kind), cw in zip(cols, widths):
    y = 34 * S
    d.text((x, y), name.upper(), font=fH, fill=INK_MUTE)
    y += 30 * S
    if kind == "text":
        words = desc.split()
        line, lines = "", []
        for wd in words:
            t = (line + " " + wd).strip()
            if d.textlength(t, font=fDesc) <= min(cw, 40 * 7.2 * S):
                line = t
            else:
                lines.append(line)
                line = wd
        if line:
            lines.append(line)
        for ln in lines:
            d.text((x, y), ln, font=fDesc, fill=INK_SOFT)
            y += 23 * S
    else:
        for lk in links[name]:
            d.text((x, y), lk, font=fA, fill=INK_SOFT)
            y += 23 * S
    x += cw + GAP

# footer base
d.line([PAD, H - 62 * S, W - PAD, H - 62 * S], fill=LINE, width=S)
d.text((PAD, H - 44 * S), "\u00a9 2026 Resepi Fesbuk. Hak cipta terpelihara.", font=fB, fill=INK_MUTE)
t2 = "Resepi Malaysia untuk semua."
d.text((W - PAD - d.textlength(t2, font=fB), H - 44 * S), t2, font=fB, fill=INK_MUTE)

p = OUT / "live_footer.png"
img.save(p)
print("wrote", p, img.size)
