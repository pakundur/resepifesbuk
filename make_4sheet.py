#!/usr/bin/env python3
"""Build the 4-product comparison sheet. Run with the project's python3."""
import sys, json
from pathlib import Path
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import ads_wired2, mock_render as MR
from PIL import Image, ImageDraw

REC = json.load(open(BASE / "src/content_fix.json"))
picks = ["oven", "periuk", "blender", "acuan"]
imgs = []
for key in picks:
    slug = next((s for s, r in REC.items() if key in ads_wired2.candidates(r)), None)
    c = ads_wired2.build_creative(key, slug, "R1")
    imgs.append((key, slug, MR.mock_three(c, 440)))

S = MR.S
pad = 24 * S
colw = max(i[2].width for i in imgs)
rowh = max(i[2].height for i in imgs)
W = colw * 2 + pad * 3
H = (rowh + 62 * S) * 2 + pad * 2 + 80 * S
M = Image.new("RGB", (W, H), (252, 248, 244))
d = ImageDraw.Draw(M)
ft = MR.F(MR.SERIF_B, 20 * S)
fl = MR.F(MR.SANS_B, 10 * S)
fs = MR.F(MR.SANS, 11.5 * S)
d.text((pad, 18 * S), "Copy unik setiap pautan — 4 produk berbeza", font=ft, fill=MR.INK)
d.text((pad, 46 * S),
       "Setiap pautan menyerang masalah dapur yang lain. Hook diambil dari bahasa kegagalan dalam 748 resepi.",
       font=fs, fill=(107, 90, 80))
for i, (key, slug, img) in enumerate(imgs):
    cx = pad + (i % 2) * (colw + pad)
    cy = 80 * S + (i // 2) * (rowh + 62 * S)
    d.text((cx, cy), f"VARIAN TIGA PINTU — {key.upper()}", font=fl, fill=(154, 127, 114))
    d.text((cx, cy + 15 * S), f"resepi: {slug[:46]}", font=fs, fill=(154, 127, 114))
    M.paste(img, (cx, cy + 32 * S))
p = MR.OUT / "mock_4products.png"
M.save(p)
print(p, p.stat().st_size, M.size)
