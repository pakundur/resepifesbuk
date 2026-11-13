"""Raster mock of the FAB stack in both states, drawn with the real CSS
values so the geometry can be checked without a browser (none exists on
this ARM64 device).

Draws on a cream page background at a realistic phone width so the
bottom-right placement and the fan's upward growth are verifiable.
"""
from PIL import Image, ImageDraw
import math, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ad_preview")
os.makedirs(OUT, exist_ok=True)

CREAM = (250, 247, 242)
CREAM_DEEP = (243, 237, 226)
INK = (26, 24, 21)
INK_MUTE = (125, 115, 106)
LINE = (227, 217, 201)
TERRA = (194, 84, 42)
PANDAN = (74, 107, 74)

W, H = 390, 780          # iPhone-ish viewport
SCALE = 2                # render at 2x for crispness
S = SCALE


def rounded(d, box, r, fill, outline=None, width=1):
    d.rounded_rectangle([c * S for c in box], radius=r * S, fill=fill,
                        outline=outline, width=width * S)


def glyph_share(d, cx, cy, col):
    """Material 'share' node icon: 3 dots joined."""
    r = 2.6 * S
    pts = [(cx - 3.4 * S, cy), (cx + 3.4 * S, cy - 3.4 * S), (cx + 3.4 * S, cy + 3.4 * S)]
    for a, b in [(0, 1), (0, 2)]:
        d.line([pts[a], pts[b]], fill=col, width=int(1.6 * S))
    for p in pts:
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)


def glyph_close(d, cx, cy, col):
    l = 4.2 * S
    w = int(2.0 * S)
    d.line([(cx - l, cy - l), (cx + l, cy + l)], fill=col, width=w)
    d.line([(cx - l, cy + l), (cx + l, cy - l)], fill=col, width=w)


def glyph_up(d, cx, cy, col):
    d.polygon([(cx, cy - 4.6 * S), (cx - 5.0 * S, cy + 1.4 * S), (cx + 5.0 * S, cy + 1.4 * S)], fill=col)
    d.rectangle([cx - 2.0 * S, cy + 1.4 * S, cx + 2.0 * S, cy + 4.6 * S], fill=col)


def glyph_dot(d, cx, cy, col, name):
    """Stand-in for each brand glyph: a filled circle with a letter."""
    d.ellipse([cx - 5.2 * S, cy - 5.2 * S, cx + 5.2 * S, cy + 5.2 * S], fill=col)


def draw_page(d, label):
    d.rectangle([0, 0, W * S, H * S], fill=CREAM)
    # fake content lines to give the FAB context
    y = 26
    for i in range(16):
        w = 300 if i % 4 else 220
        d.rounded_rectangle([20 * S, y * S, (20 + w) * S, (y + 7) * S],
                            radius=3 * S, fill=CREAM_DEEP)
        y += 20
    d.text((20 * S, 6 * S), label, fill=INK_MUTE)


def render(open_state: bool, fname: str):
    img = Image.new("RGB", (W * S, H * S), CREAM)
    d = ImageDraw.Draw(img)
    draw_page(d, "expanded" if open_state else "collapsed (default)")

    right = 16 if W > 560 else 12
    bottom = 16 if W > 560 else 12
    gap = 10 if W > 560 else 8
    btn = 48 if W > 560 else 44
    item = 44 if W > 560 else 42
    fan_gap = 8

    # back-to-top button, bottom right
    top_y = H - bottom - btn
    bx0 = W - right - btn
    rounded(d, (bx0, top_y, bx0 + btn, top_y + btn), btn / 2, (255, 255, 255), LINE, 1)
    glyph_up(d, bx0 + btn / 2, top_y + btn / 2, INK)

    # share button sits above it
    sh_y = top_y - gap - btn
    sh_col = INK if open_state else (255, 255, 255)
    sh_fg = CREAM if open_state else INK
    rounded(d, (bx0, sh_y, bx0 + btn, sh_y + btn), btn / 2, sh_col, sh_col if open_state else LINE, 1)
    if open_state:
        glyph_close(d, bx0 + btn / 2, sh_y + btn / 2, sh_fg)
    else:
        glyph_share(d, bx0 + btn / 2, sh_y + btn / 2, sh_fg)

    if open_state:
        # fan grows upward from just above the share button
        labels = ["WhatsApp", "Telegram", "Facebook", "X", "Pinterest", "Threads", "Email", "Salin pautan"]
        cols = [(37, 211, 102), (34, 158, 217), (24, 119, 242), (0, 0, 0),
                (230, 0, 35), (0, 0, 0), (125, 115, 106), TERRA]
        y = sh_y - fan_gap - item
        # fan order bottom-up is whatsapp..copy, so draw reversed
        for i in range(len(labels) - 1, -1, -1):
            ix0 = W - right - btn / 2 - item / 2
            rounded(d, (ix0, y, ix0 + item, y + item), item / 2, (255, 255, 255), LINE, 1)
            glyph_dot(d, ix0 + item / 2, y + item / 2, cols[i], labels[i])
            # tooltip to the left
            tw = len(labels[i]) * 5.2 + 16
            tx1 = ix0 - 10
            ty = y + item / 2
            rounded(d, (tx1 - tw, ty - 9, tx1, ty + 9), 6, INK, None, 1)
            d.text((tx1 - tw + 8, ty - 5), labels[i], fill=CREAM)
            y -= (item + fan_gap)

    img.save(os.path.join(OUT, fname), quality=95)
    print("wrote", fname)


render(False, "fab_collapsed.png")
render(True, "fab_open.png")
