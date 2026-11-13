#!/usr/bin/env python3
"""
Raster mock of the three ad variants, built with PIL at 2x for retina clarity.
No browser available on this device, so this is a faithful hand-render of the
CSS box model: same paddings, sizes, colours and type scale.

Renders:
  mock_a_three.png   — Varian Tiga Pintu (Kuali leper, 3 links, 3 copy)
  mock_b_compact.png — Varian Padat
  mock_c_bar.png     — Varian Bar (320 wide mobile + 728 wide desktop)
  mock_all.png       — all three stacked, as a delivered preview sheet
"""
import sys, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import ads_wired2, ad_art

OUT = BASE / "ad_preview"
OUT.mkdir(exist_ok=True)

S = 2  # supersample factor

TERRA = (194, 94, 58)
TERRA_D = (163, 74, 44)
CREAM = (253, 246, 240)
CREAM_D = (240, 224, 210)
INK = (43, 35, 32)
MUTED = (92, 79, 71)
CHIP = (241, 228, 216)
CHIPINK = (94, 70, 58)
ROWBG = (251, 243, 236)
WHITE = (255, 255, 255)
NOTEC = (138, 122, 112)

FONT_DIRS = [
    "/system/fonts",
    "/data/data/com.termux/files/usr/share/fonts/TTF",
    "/data/data/com.termux/files/usr/share/fonts/truetype",
]


def find_font(candidates):
    for d in FONT_DIRS:
        for c in candidates:
            p = Path(d) / c
            if p.exists():
                return str(p)
    return None


SERIF_B = find_font(["NotoSerif-Bold.ttf", "DejaVuSerif-Bold.ttf", "RobotoSerif-Bold.ttf"])
SERIF_I = find_font(["NotoSerif-Italic.ttf", "DejaVuSerif-Italic.ttf",
                     "RobotoSerif-Italic.ttf", "NotoSerif-BoldItalic.ttf"]) or SERIF_B
SANS = find_font(["Roboto-Regular.ttf", "DejaVuSans.ttf", "NotoSans-Regular.ttf"])
SANS_B = find_font(["Roboto-Bold.ttf", "DejaVuSans-Bold.ttf", "NotoSans-Bold.ttf"])
SANS_M = find_font(["Roboto-Medium.ttf", "DejaVuSans.ttf", "NotoSans-Medium.ttf"]) or SANS


def F(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def wrap(text, font, maxw, draw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, text, font, fill, x, y, maxw, lh):
    for ln in wrap(text, font, maxw, draw):
        draw.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y


def disc(draw, W):
    f = F(SANS_B, 9.5 * S)
    tw = draw.textlength("DIT AJA", font=f)  # trailing-space trick
    label = "DIT AJA".replace(" ", "")
    tw = draw.textlength(label, font=f)
    padx, pady = 8 * S, 5 * S
    bw, bh = tw + padx * 2, 9.5 * S + pady * 2
    x2, y2 = W - 12 * S, 11 * S
    draw.rounded_rectangle([x2 - bw, y2, x2, y2 + bh], radius=5 * S,
                           fill=CHIP, outline=(230, 210, 189), width=max(1, S))
    draw.text((x2 - bw + padx, y2 + pady), label, font=f, fill=CHIPINK)


def header(draw, x, y, W, label, art_size, kicker=True):
    """kicker + product name. Icon area left blank-with-plate."""
    px = 18 * S
    if kicker:
        fk = F(SANS_B, 9.5 * S)
        draw.text((x + px + art_size + 11 * S, y + 15 * S), "SHOPEE MALAYSIA", font=fk, fill=TERRA)
        fn = F(SERIF_B, 15.5 * S)
        draw.text((x + px + art_size + 11 * S, y + 27 * S), label, font=fn, fill=INK)
        return y + 48 * S
    return y


def plate(draw, x, y, size, key=None):
    """Draw the REAL SVG illustration if a key is given, else a neutral plate."""
    if key is not None:
        import io
        import cairosvg
        from PIL import Image as _I
        KW = {"oven": "Oven / Ketuhar", "periuk": "Periuk", "blender": "Blender",
              "acuan": "Acuan Kuih / Kek", "kuali": "Kuali", "mixer": "Mixer / Pengadun",
              "kukus": "Pengukus (Kukusan)", "loyang": "Loyang / Acuan Kek",
              "ricecooker": "Rice Cooker (Periuk Nasi Elektrik)",
              "grillpan": "Grill Pan / Pemanggang", "microwave": "Microwave",
              "freezer": "Freezer / Peti Sejuk Beku", "waffle": "Waffle Maker",
              "takoyaki": "Acuan Takoyaki", "pressure": "Pressure Cooker",
              "pengisar": "Pengisar / Grinder"}
        try:
            svg = ad_art.illustration_for(KW[key]).replace(' width="96" height="96"', "")
            if "viewBox" not in svg:
                svg = svg.replace("<svg ", '<svg viewBox="0 0 96 96" ', 1)
            png = cairosvg.svg2png(bytestring=svg.encode(),
                                   output_width=int(size), output_height=int(size),
                                   background_color="#FDF6F0")
            im = _I.open(io.BytesIO(png)).convert("RGB")
            draw._image.paste(im, (int(x), int(y)))
            return
        except Exception:
            pass
    draw.rounded_rectangle([x, y, x + size, y + size], radius=size * 0.18,
                           fill=(238, 226, 214), outline=(224, 208, 192), width=max(1, S))
    f = F(SANS_B, size * 0.30)
    t = "SVG"
    tw = draw.textlength(t, font=f)
    draw.text((x + (size - tw) / 2, y + size * 0.34), t, font=f, fill=(190, 165, 145))


def arrow(draw, x, y, size, color=WHITE):
    w = max(2, int(1.4 * S))
    draw.line([x, y, x + size, y], fill=color, width=w)
    draw.line([x + size * 0.45, y - size * 0.38, x + size, y], fill=color, width=w)
    draw.line([x + size * 0.45, y + size * 0.38, x + size, y], fill=color, width=w)


# ------------------------------------------------------------------ THREE
def mock_three(c, width=440):
    W = width * S
    pad = 18 * S
    num_lh = 14.5 * S * 1.3
    prom_lh = 12.5 * S * 1.55
    maxw = W - pad * 2 - 25 * S

    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    fhook = F(SERIF_I, 14.5 * S)
    fprom = F(SANS, 12.5 * S)
    fbtn = F(SANS_B, 12 * S)

    row_h = []
    for r in c["rows"]:
        hl = len(wrap(r["hook"], fhook, maxw, probe))
        pl = len(wrap(r["promise"], fprom, maxw, probe))
        h = 13 * S + max(17 * S, hl * num_lh) + 4 * S + pl * prom_lh + 9 * S + 31 * S + 13 * S
        row_h.append(h)

    head_h = 48 * S + 13 * S
    note_h = 11 * S + 15 * S + 14 * S
    H = int(head_h + sum(row_h) + note_h)

    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=16 * S, outline=CREAM_D, width=S)

    header(d, 0, 0, W, c["label"], 38 * S)
    plate(d, pad, 15 * S, 38 * S, c['key'])
    disc(d, W)

    y = head_h
    for i, r in enumerate(c["rows"]):
        d.line([0, y, W, y], fill=CREAM_D, width=S)
        ty = y + 13 * S
        # number
        cy = ty + 8.5 * S
        d.ellipse([pad, cy - 8.5 * S, pad + 17 * S, cy + 8.5 * S], fill=TERRA)
        fnum = F(SANS_B, 9.5 * S)
        nw = d.textlength(str(i + 1), font=fnum)
        d.text((pad + (17 * S - nw) / 2, cy - 5.2 * S), str(i + 1), font=fnum, fill=WHITE)
        # hook
        hook_lines = wrap(r["hook"], fhook, maxw, d)
        hy = ty
        for ln in hook_lines:
            d.text((pad + 25 * S, hy), ln, font=fhook, fill=INK)
            hy += num_lh
        py = max(ty + 17 * S, ty + len(hook_lines) * num_lh) + 4 * S
        py = draw_wrapped(d, r["promise"], fprom, MUTED, pad + 25 * S, py, maxw, prom_lh)
        # button
        by = py + 9 * S
        bw = d.textlength(r["btn"], font=fbtn) + 24 * S + 22 * S
        d.rounded_rectangle([pad + 25 * S, by, pad + 25 * S + bw, by + 31 * S],
                            radius=8 * S, fill=TERRA)
        d.text((pad + 25 * S + 12 * S, by + 8.5 * S), r["btn"], font=fbtn, fill=WHITE)
        arrow(d, pad + 25 * S + 12 * S + d.textlength(r["btn"], font=fbtn) + 7 * S,
              by + 15 * S, 11 * S)
        y += row_h[i]

    # note
    fn = F(SANS, 10 * S)
    d.text((pad, y + 11 * S), "Pautan rakan kongsi. Harga dan stok boleh berubah.",
           font=fn, fill=NOTEC)
    return img


# ---------------------------------------------------------------- COMPACT
def mock_compact(c, width=440):
    W = width * S
    pad = 18 * S
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    fhook = F(SERIF_I, 14.5 * S)
    fprom = F(SANS, 12.5 * S)
    fbtn = F(SANS_B, 12 * S)
    fmini = F(SANS_B, 12.5 * S)

    maxw = W - pad * 2 - 25 * S
    r0 = c["rows"][0]
    hl = len(wrap(r0["hook"], fhook, maxw, probe))
    pl = len(wrap(r0["promise"], fprom, maxw, probe))
    big_h = 13 * S + max(17 * S, hl * 14.5 * S * 1.3) + 4 * S + pl * 12.5 * S * 1.55 + 9 * S + 31 * S + 13 * S
    mini_h = []
    for r in c["rows"][1:]:
        t = f"{r['hook']} — {r['btn']}"
        ml = len(wrap(t, fmini, W - pad * 2 - 26 * S - 20 * S, probe))
        mini_h.append(max(1, ml) * 12.5 * S * 1.35 + 20 * S)

    head_h = 48 * S + 13 * S
    note_h = 11 * S + 15 * S + 14 * S
    H = int(head_h + big_h + sum(mini_h) + note_h)

    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=16 * S, outline=CREAM_D, width=S)
    header(d, 0, 0, W, c["label"], 30 * S)
    plate(d, pad, 15 * S, 30 * S, c['key'])
    disc(d, W)

    y = head_h
    d.line([0, y, W, y], fill=CREAM_D, width=S)
    ty = y + 13 * S
    cy = ty + 8.5 * S
    d.ellipse([pad, cy - 8.5 * S, pad + 17 * S, cy + 8.5 * S], fill=TERRA)
    fnum = F(SANS_B, 9.5 * S)
    nw = d.textlength("1", font=fnum)
    d.text((pad + (17 * S - nw) / 2, cy - 5.2 * S), "1", font=fnum, fill=WHITE)
    hook_lines = wrap(r0["hook"], fhook, maxw, d)
    hy = ty
    for ln in hook_lines:
        d.text((pad + 25 * S, hy), ln, font=fhook, fill=INK)
        hy += 14.5 * S * 1.3
    py = max(ty + 17 * S, ty + len(hook_lines) * 14.5 * S * 1.3) + 4 * S
    py = draw_wrapped(d, r0["promise"], fprom, MUTED, pad + 25 * S, py, maxw, 12.5 * S * 1.55)
    by = py + 9 * S
    bw = d.textlength(r0["btn"], font=fbtn) + 46 * S
    d.rounded_rectangle([pad + 25 * S, by, pad + 25 * S + bw, by + 31 * S], radius=8 * S, fill=TERRA)
    d.text((pad + 25 * S + 12 * S, by + 8.5 * S), r0["btn"], font=fbtn, fill=WHITE)
    arrow(d, pad + 25 * S + 12 * S + d.textlength(r0["btn"], font=fbtn) + 7 * S, by + 15 * S, 11 * S)
    y += big_h

    for i, r in enumerate(c["rows"][1:]):
        d.line([0, y, W, y], fill=CREAM_D, width=S)
        cy = y + mini_h[i] / 2
        d.ellipse([pad, cy - 8.5 * S, pad + 17 * S, cy + 8.5 * S], fill=TERRA)
        tt = str(i + 2)
        nw = d.textlength(tt, font=fnum)
        d.text((pad + (17 * S - nw) / 2, cy - 5.2 * S), tt, font=fnum, fill=WHITE)
        t = f"{r['hook']} — {r['btn']}"
        lines = wrap(t, fmini, W - pad * 2 - 26 * S - 22 * S, d)
        ly = cy - len(lines) * 12.5 * S * 1.35 / 2
        for ln in lines:
            d.text((pad + 26 * S, ly), ln, font=fmini, fill=TERRA_D)
            ly += 12.5 * S * 1.35
        arrow(d, W - pad - 12 * S, cy, 10 * S, TERRA_D)
        y += mini_h[i]

    d.text((pad, y + 11 * S), "Pautan rakan kongsi. Harga dan stok boleh berubah.",
           font=F(SANS, 10 * S), fill=NOTEC)
    return img


# -------------------------------------------------------------------- BAR
def _chip_layout(d, rows, falt, pad, W, S):
    """Pre-compute chip positions and total height so nothing clips."""
    placed = []
    cx = pad
    cy = 0
    rowmax = 24 * S
    for r in rows:
        t = r["hook"]
        cw = d.textlength(t, font=falt) + 16 * S
        if cw > W - pad * 2:
            cw = W - pad * 2
        if cx + cw > W - pad:
            cx = pad
            cy += rowmax + 6 * S
        placed.append((cx, cy, cw, t))
        cx += cw + 6 * S
    total = cy + rowmax
    return placed, total


def mock_bar(c, width=340):
    W = width * S
    pad = 15 * S
    narrow = width < 420
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    fhook = F(SERIF_I, 13 * S)
    fprom = F(SANS, 11.5 * S)
    fbtn = F(SANS_B, 11.5 * S)
    falt = F(SANS_B, 10.5 * S)

    r0 = c["rows"][0]
    head_h = 12 * S + 26 * S + 6 * S
    btnw = probe.textlength(r0["btn"], font=fbtn) + 34 * S

    # Narrow: button goes on its own line below the text (no side-by-side).
    # Wide: true two-column bar.
    if narrow:
        txtw2 = W - pad * 2
    else:
        txtw2 = W - pad * 2 - btnw - 14 * S

    hl = len(wrap(r0["hook"], fhook, txtw2, probe))
    pl = len(wrap(r0["promise"], fprom, txtw2, probe))
    text_h = hl * 13 * S * 1.25 + 3 * S + pl * 11.5 * S * 1.5
    body_h = text_h + 6 * S
    if narrow:
        body_h += 30 * S + 8 * S   # button on its own row

    placed, chips_h = _chip_layout(probe, c["rows"][1:], falt, pad, W, S)
    alt_h = 10 * S + chips_h + 12 * S
    H = int(head_h + body_h + alt_h)

    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, W - 1, H - 1], radius=16 * S, outline=CREAM_D, width=S)
    header(d, 0, 0, W, c["label"], 26 * S)
    plate(d, pad, 12 * S, 26 * S, c['key'])
    disc(d, W)

    y = head_h
    hy = y
    for ln in wrap(r0["hook"], fhook, txtw2, d):
        d.text((pad, hy), ln, font=fhook, fill=INK)
        hy += 13 * S * 1.25
    draw_wrapped(d, r0["promise"], fprom, MUTED, pad, hy + 3 * S, txtw2, 11.5 * S * 1.5)

    if narrow:
        btny = y + text_h + 6 * S
        d.rounded_rectangle([pad, btny, pad + btnw, btny + 30 * S], radius=8 * S, fill=TERRA)
        d.text((pad + 10 * S, btny + 8 * S), r0["btn"], font=fbtn, fill=WHITE)
        arrow(d, pad + 10 * S + d.textlength(r0["btn"], font=fbtn) + 6 * S,
              btny + 15 * S, 10 * S)
    else:
        btny = y + 1 * S
        d.rounded_rectangle([W - pad - btnw, btny, W - pad, btny + 30 * S], radius=8 * S, fill=TERRA)
        d.text((W - pad - btnw + 10 * S, btny + 8 * S), r0["btn"], font=fbtn, fill=WHITE)
        arrow(d, W - pad - btnw + 10 * S + d.textlength(r0["btn"], font=fbtn) + 6 * S,
              btny + 15 * S, 10 * S)

    y += body_h
    cy0 = y + 10 * S
    for cx, cy, cw, t in placed:
        d.rounded_rectangle([cx, cy0 + cy, cx + cw, cy0 + cy + 24 * S], radius=6 * S,
                            fill=ROWBG, outline=CREAM_D, width=max(1, S))
        d.text((cx + 8 * S, cy0 + cy + 6 * S), t, font=falt, fill=TERRA_D)
    return img


def sheet():
    """Assemble the delivered preview sheet."""
    REC = json.load(open(BASE / "src/content_fix.json"))
    kuali_slug = next(s for s, r in REC.items()
                      if "kuali" in ads_wired2.candidates(r) and len(ads_wired2.candidates(r)) >= 2)
    c = ads_wired2.build_creative("kuali", kuali_slug, "R1")

    a = mock_three(c, 440)
    b = mock_compact(c, 440)
    cn = mock_bar(c, 340)
    cd = mock_bar(c, 728)

    a.save(OUT / "mock_a_three.png")
    b.save(OUT / "mock_b_compact.png")
    cn.save(OUT / "mock_c_bar_320.png")
    cd.save(OUT / "mock_c_bar_728.png")

    # composed sheet
    pad = 26 * S
    colw = max(a.width, b.width)
    W = colw + 24 * S + cd.width + pad * 2
    H = max(a.height + b.height + 40 * S, cd.height + cn.height + 70 * S) + pad * 2 + 60 * S

    M = Image.new("RGB", (W, H), (252, 248, 244))
    d = ImageDraw.Draw(M)
    ft = F(SERIF_B, 21 * S)
    fs = F(SANS, 12 * S)
    fl = F(SANS_B, 10 * S)

    d.text((pad, 20 * S), "Copy unik setiap pautan — Kuali leper", font=ft, fill=INK)
    d.text((pad, 50 * S), "3 pautan afiliasi, 3 masalah dapur berbeza, 3 butang sendiri.",
           font=fs, fill=(107, 90, 80))

    y0 = 84 * S
    d.text((pad, y0), "VARIAN TIGA PINTU", font=fl, fill=(154, 127, 114))
    M.paste(a, (pad, y0 + 16 * S))
    d.text((pad, y0 + 16 * S + a.height + 26 * S), "VARIAN PADAT", font=fl, fill=(154, 127, 114))
    M.paste(b, (pad, y0 + 16 * S + a.height + 42 * S))

    rx = pad + colw + 24 * S
    d.text((rx, y0), "VARIAN BAR — 728×90 desktop", font=fl, fill=(154, 127, 114))
    M.paste(cd, (rx, y0 + 16 * S))
    d.text((rx, y0 + 16 * S + cd.height + 22 * S), "VARIAN BAR — 320 mobile", font=fl, fill=(154, 127, 114))
    M.paste(cn, (rx, y0 + 16 * S + cd.height + 38 * S))

    M.save(OUT / "mock_all.png")
    return OUT / "mock_all.png", a, b, cn, cd


if __name__ == "__main__":
    p, a, b, cn, cd = sheet()
    print("sheet:", p, p.stat().st_size)
    print("three:  ", a.size)
    print("compact:", b.size)
    print("bar320: ", cn.size)
    print("bar728: ", cd.size)
