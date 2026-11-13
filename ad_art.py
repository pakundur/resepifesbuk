#!/usr/bin/env python3
"""
Procedural SVG illustrations for the ad cards, in the resepifesbuk palette.

Why SVG not AI images:
  - The site theme is terracotta #C25E3A on cream #FDF6F0 with pastel accents.
    Every illustration here uses those exact tokens, so a card never looks pasted in.
  - ~1-3 KB each, gzip to a few hundred bytes, infinitely sharp, no network request.
  - Deterministic: same product = same picture, forever. No model drift.
  - An AI image of "a kuali" that renders a wok turned inside out is worse than
    no image at all, and there is no image model on this device anyway.

Style rule taken from the Pixlpin references (Hyperice, "Meet"):
  ONE focal silhouette, generous negative space, restrained palette, no clutter.
  The illustration is a mark, not a photograph.
"""
from pathlib import Path

TERRA = "#C25E3A"
TERRA_D = "#A34A2C"
CREAM = "#FDF6F0"
CREAM_D = "#F5E8DC"
SKY = "#CFE3EC"
SKY_D = "#A9C9D9"
GREEN = "#B9CDB4"
INK = "#2B2320"

BASE = Path(__file__).resolve().parent
OUT = BASE / "static" / "ads"
OUT.mkdir(parents=True, exist_ok=True)

# 96x96 viewBox, centred, ~60% fill so it breathes inside the card.
HEAD = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" '
        'role="img" aria-label="{label}" width="96" height="96">')


def svg(label, body):
    return HEAD.format(label=label) + body + "</svg>"


# ------------------------------------------------------------------ primitives
def _wok(label):
    """Kuali — shallow wok, two loop ears, clearly deeper than a frying pan.

    Geometry note: the bowl must be drawn FIRST, then the rim ellipse on top
    filled with a LIGHT tone so it reads as the pan's inner surface catching
    light. A dark rim on a dark body reads as a hollow black cavity, and two
    cream dots inside it read as eyes (a smiling face). Highlight is a single
    soft streak, not two dots.
    """
    return svg(label, f"""
<path d="M12 40 q36 40 72 0 q-6 26 -36 26 q-30 0 -36 -26 z" fill="{TERRA_D}"/>
<path d="M12 40 q36 40 72 0 q-4 12 -36 12 q-32 0 -36 -12 z" fill="{TERRA}"/>
<ellipse cx="48" cy="40" rx="36" ry="9" fill="{CREAM_D}"/>
<ellipse cx="48" cy="40" rx="30" ry="6.2" fill="{CREAM}"/>
<path d="M12 40 q-9-5-1-11" stroke="{INK}" stroke-width="4.2" fill="none" stroke-linecap="round"/>
<path d="M84 40 q9-5 1-11" stroke="{INK}" stroke-width="4.2" fill="none" stroke-linecap="round"/>
<path d="M28 40 q20-4 40 0" stroke="{TERRA_D}" stroke-width="1.8" fill="none"
      opacity=".45" stroke-linecap="round"/>
""")


def _tray(label):
    """Loyang — rectangular baking tin seen at an angle, with depth walls.

    A loyang is ONE open rectangular pan. It must never look like the acuan
    tray (which has multiple small wells) — keep the interior flat and empty,
    with a single parchment-paper liner line.
    """
    return svg(label, f"""
<path d="M18 34 L62 24 L82 34 L38 46 Z" fill="{CREAM_D}"/>
<path d="M18 34 v22 l20 12 v-22 z" fill="{TERRA_D}"/>
<path d="M38 46 v22 l44-12 V34 z" fill="{TERRA}"/>
<path d="M24 38 l38-9" stroke="{CREAM}" stroke-width="1.6" opacity=".55"/>
<path d="M44 49 l30-8" stroke="{CREAM}" stroke-width="1.4" opacity=".3"/>
""")


def _mould_tray(label):
    """Acuan kuih — mould tray with visible individual wells.

    Differentiated from loyang by MULTIPLE circular wells on the top face.
    Without the wells the two icons are indistinguishable at 96px.
    """
    return svg(label, f"""
<path d="M14 38 L54 26 L86 38 L46 50 Z" fill="{CREAM_D}"/>
<path d="M14 38 v16 l32 14 v-16 z" fill="{TERRA_D}"/>
<path d="M46 50 v16 l40-12 V38 z" fill="{TERRA}"/>
<ellipse cx="41" cy="40" rx="7.5" ry="4.2" fill="{CREAM}"/>
<ellipse cx="41" cy="40" rx="5.2" ry="2.6" fill="{SKY}"/>
<ellipse cx="60" cy="38" rx="7.5" ry="4.2" fill="{CREAM}"/>
<ellipse cx="60" cy="38" rx="5.2" ry="2.6" fill="{SKY}"/>
<ellipse cx="32" cy="46" rx="7.5" ry="4.2" fill="{CREAM}"/>
<ellipse cx="32" cy="46" rx="5.2" ry="2.6" fill="{SKY}"/>
""")


def _board(label):
    """Talenan — board with handle hole, wood grain, and a knife cut."""
    return svg(label, f"""
<path d="M20 30 h44 a8 8 0 0 1 8 8 v34 a8 8 0 0 1 -8 8 H20 a8 8 0 0 1 -8-8 V38 a8 8 0 0 1 8-8 z" fill="{TERRA_D}"/>
<circle cx="24" cy="42" r="4.5" fill="{CREAM}"/>
<path d="M14 58 h58 M14 66 h58 M14 50 h40" stroke="{TERRA}" stroke-width="2" opacity=".45"/>
<circle cx="56" cy="62" r="7" fill="{GREEN}"/>
<circle cx="54" cy="60" r="2" fill="{CREAM}" opacity=".7"/>
""")


def _mixer(label):
    """Pengadun — stand mixer: heavy base, arched neck over a bowl, beater.

    Face-avoidance rule: no isolated light dot on the body (reads as an eye),
    and the beater must enter the bowl, not hover above it. The neck arc stays
    open on the left so the silhouette reads "mixer", not "bird".
    """
    return svg(label, f"""
<rect x="20" y="74" width="56" height="9" rx="4.5" fill="{TERRA_D}"/>
<path d="M28 74 v-18 q0-24 24-24 h8 q8 0 8 8 v34" fill="{TERRA}"/>
<rect x="60" y="36" width="16" height="10" rx="4" fill="{TERRA_D}"/>
<path d="M68 46 v10" stroke="{INK}" stroke-width="3.4" stroke-linecap="round"/>
<path d="M68 56 v6" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>
<ellipse cx="66" cy="70" rx="17" ry="8" fill="{SKY}"/>
<path d="M49 70 a17 8 0 0 0 34 0" fill="{SKY_D}"/>
<path d="M52 62 v8 M80 62 v8" stroke="{TERRA_D}" stroke-width="2.4" stroke-linecap="round"/>
<rect x="26" y="64" width="9" height="5" rx="2" fill="{CREAM_D}"/>
""")


def _scale(label):
    """Penimbang — platform scale with a raised weighing plate and readout."""
    return svg(label, f"""
<rect x="16" y="46" width="64" height="8" rx="4" fill="{SKY_D}"/>
<path d="M24 54 h48 v22 a6 6 0 0 1 -6 6 H30 a6 6 0 0 1 -6-6 z" fill="{TERRA}"/>
<rect x="32" y="60" width="32" height="13" rx="2.5" fill="{CREAM}"/>
<path d="M38 66 h7 M50 66 h4" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>
<circle cx="24" cy="70" r="2.5" fill="{CREAM}" opacity=".7"/>
<path d="M30 36 q10-8 20 0" stroke="{TERRA_D}" stroke-width="2.5" fill="none" opacity=".5"/>
""")


def _grill(label):
    """Pemanggang — square grill pan with distinct raised ridges."""
    return svg(label, f"""
<path d="M14 36 h56 a6 6 0 0 1 6 6 v18 a6 6 0 0 1 -6 6 H14 a6 6 0 0 1 -6-6 V42 a6 6 0 0 1 6-6 z" fill="{TERRA}"/>
<path d="M18 40 v22 M28 40 v22 M38 40 v22 M48 40 v22 M58 40 v22" stroke="{INK}" stroke-width="3" opacity=".55" stroke-linecap="round"/>
<rect x="76" y="44" width="14" height="7" rx="3.5" fill="{INK}"/>
<path d="M26 28 q5-5 0-11 M44 28 q5-5 0-11" stroke="{SKY_D}" stroke-width="2.5" fill="none" opacity=".65" stroke-linecap="round"/>
""")


def _coconut(label):
    """Kelapa parut — halved coconut shell with shredded strands."""
    return svg(label, f"""
<path d="M24 46 a24 24 0 0 0 48 0 z" fill="{TERRA_D}"/>
<ellipse cx="48" cy="46" rx="24" ry="7" fill="{CREAM}"/>
<path d="M34 42 q4-10 10-6 M44 40 q4-10 10-5 M54 42 q4-9 9-4" stroke="{CREAM_D}" stroke-width="2.6"
      fill="none" stroke-linecap="round"/>
<path d="M24 46 a24 24 0 0 0 48 0" fill="none" stroke="{TERRA}" stroke-width="2.5"/>
""")


def _icecream(label):
    """Mesin aiskrim — countertop machine with a paddle, not a cone."""
    return svg(label, f"""
<rect x="18" y="30" width="60" height="46" rx="8" fill="{TERRA}"/>
<rect x="24" y="36" width="30" height="8" rx="3" fill="{CREAM}"/>
<rect x="24" y="50" width="48" height="20" rx="6" fill="{SKY}"/>
<circle cx="48" cy="60" r="7" fill="{CREAM}"/>
<path d="M48 53 v14 M41 60 h14" stroke="{TERRA_D}" stroke-width="2.2" stroke-linecap="round"/>
<rect x="62" y="36" width="10" height="8" rx="3" fill="{TERRA_D}"/>
""")


def _loaf(label):
    """Roti — domed loaf with scored top, on a board."""
    return svg(label, f"""
<path d="M18 58 q0-24 30-24 q30 0 30 24 v10 q0 6-6 6 H24 q-6 0-6-6 z" fill="{TERRA}"/>
<path d="M30 48 q6-8 10 0 M46 44 q6-8 10 0 M60 48 q5-7 9 0"
      stroke="{CREAM}" stroke-width="2.6" fill="none" stroke-linecap="round" opacity=".8"/>
<rect x="14" y="74" width="68" height="6" rx="3" fill="{TERRA_D}"/>
""")


def _waffle(label):
    """Waffle maker — clamshell appliance with grid plate, not a bare waffle."""
    return svg(label, f"""
<path d="M16 40 h64 v12 H16 z" fill="{TERRA_D}"/>
<path d="M18 52 h60 v18 a6 6 0 0 1 -6 6 H24 a6 6 0 0 1 -6-6 z" fill="{TERRA}"/>
<path d="M26 58 h44 v12 H26 z" fill="{CREAM}"/>
<path d="M34 58 v12 M44 58 v12 M54 58 v12 M62 58 v12" stroke="{TERRA_D}" stroke-width="1.8" opacity=".7"/>
<path d="M26 64 h44" stroke="{TERRA_D}" stroke-width="1.8" opacity=".7"/>
<circle cx="72" cy="46" r="3" fill="{CREAM}"/>
""")


def _oven(label):
    """Oven — freestanding oven with hob rings on top and a window."""
    return svg(label, f"""
<rect x="14" y="20" width="68" height="62" rx="7" fill="{TERRA}"/>
<rect x="14" y="20" width="68" height="16" rx="7" fill="{TERRA_D}"/>
<circle cx="30" cy="28" r="4.5" fill="{INK}" opacity=".65"/>
<circle cx="46" cy="28" r="4.5" fill="{INK}" opacity=".65"/>
<circle cx="66" cy="28" r="5" fill="{CREAM}"/>
<circle cx="66" cy="28" r="2" fill="{TERRA_D}"/>
<rect x="22" y="44" width="52" height="26" rx="4" fill="{CREAM}"/>
<rect x="26" y="48" width="44" height="14" rx="2" fill="{SKY}"/>
<rect x="22" y="74" width="52" height="3" rx="1.5" fill="{CREAM_D}"/>
""")


def _plate(label):
    """Generic — plate with fork, reads as 'food' cleanly."""
    return svg(label, f"""
<ellipse cx="42" cy="54" rx="28" ry="26" fill="{CREAM_D}"/>
<ellipse cx="42" cy="54" rx="19" ry="17" fill="{CREAM}"/>
<ellipse cx="42" cy="54" rx="9" ry="8" fill="{TERRA}" opacity=".85"/>
<path d="M78 28 v34 M78 28 v12 q0 4-4 4 M78 28 v12 q0 4 4 4"
      stroke="{TERRA_D}" stroke-width="2.6" fill="none" stroke-linecap="round"/>
""")


def _pot(label, body_col):
    """Periuk — pot with lid, handles and a steam knob."""
    return svg(label, f"""
<rect x="20" y="44" width="56" height="32" rx="7" fill="{body_col}"/>
<rect x="14" y="38" width="68" height="9" rx="4.5" fill="{TERRA_D}"/>
<path d="M14 46 q-7 2 0 12" stroke="{INK}" stroke-width="3.5" fill="none" stroke-linecap="round"/>
<path d="M82 46 q7 2 0 12" stroke="{INK}" stroke-width="3.5" fill="none" stroke-linecap="round"/>
<circle cx="48" cy="36" r="4" fill="{INK}"/>
<path d="M24 60 q24 8 48 0" stroke="{CREAM}" stroke-width="2.5" fill="none" opacity=".35"/>
""")


def _pressure_cooker(label):
    """Periuk tekanan — pressure cooker: TALL body, clamped lid, weighted valve.

    Differences from _pot must be legible at 96px:
      - taller body (pressure cookers are tall, not wide)
      - two visible CLAMPS on the sides of the lid
      - a WEIGHTED ROCKER valve on top (not a plain round knob)
    Without those three cues it is just another pot.
    """
    return svg(label, f"""
<rect x="22" y="40" width="52" height="38" rx="8" fill="{TERRA}"/>
<rect x="16" y="32" width="64" height="10" rx="5" fill="{TERRA_D}"/>
<rect x="26" y="31" width="10" height="12" rx="3" fill="{INK}"/>
<rect x="60" y="31" width="10" height="12" rx="3" fill="{INK}"/>
<path d="M42 30 v-8 h12 v8 z" fill="{TERRA_D}"/>
<rect x="40" y="14" width="16" height="7" rx="3.5" fill="{INK}"/>
<path d="M56 17 h9" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>
<path d="M18 50 q-6 3 0 12" stroke="{INK}" stroke-width="3.5" fill="none" stroke-linecap="round"/>
<path d="M78 50 q6 3 0 12" stroke="{INK}" stroke-width="3.5" fill="none" stroke-linecap="round"/>
<path d="M30 58 q18 6 36 0" stroke="{CREAM}" stroke-width="2.4" fill="none" opacity=".4"/>
""")


def _bottle(label, col):
    """Sauce bottle — for sos / kicap / cuka."""
    return svg(label, f"""
<rect x="40" y="16" width="16" height="8" rx="3" fill="{TERRA_D}"/>
<path d="M40 24 h16 v10 q10 6 10 20 v24 q0 6-6 6 H36 q-6 0-6-6 V54 q0-14 10-20 z" fill="{col}" stroke="{TERRA_D}" stroke-width="2" stroke-opacity=".45"/>
<rect x="30" y="54" width="36" height="18" rx="3" fill="{CREAM}" opacity=".92"/>
<path d="M36 60 h24 M36 66 h16" stroke="{TERRA_D}" stroke-width="2" stroke-linecap="round"/>
""")


def _jar(label, col, motif="spice"):
    """
    Jar — differentiated by MOTIF, not just colour.
    A wall of identical jars tells the reader nothing; the little glyph on the
    label is what separates 'serbuk kari' from 'gula melaka' at a glance.
    """
    motifs = {
        "spice": f'<path d="M40 52 q8-10 16 0 q-8 10-16 0 z" fill="{TERRA_D}"/>'
                 f'<path d="M56 52 q6-4 8 0" stroke="{TERRA_D}" stroke-width="1.8" fill="none"/>',
        "sugar": f'<path d="M42 52 l4-5 4 5 4-5 4 5" stroke="{TERRA_D}" stroke-width="2"'
                 f' fill="none" stroke-linecap="round" stroke-linejoin="round"/>',
        "butter": f'<rect x="40" y="49" width="16" height="9" rx="2" fill="{TERRA_D}"/>'
                  f'<path d="M40 52 h16" stroke="{CREAM}" stroke-width="1.4"/>',
        "malt": f'<circle cx="48" cy="53" r="5" fill="{TERRA_D}"/>'
                f'<path d="M48 48 v10 M43 53 h10" stroke="{CREAM}" stroke-width="1.6"/>',
        "cocoa": f'<path d="M42 56 q6-11 12 0 z" fill="{TERRA_D}"/>'
                 f'<path d="M48 45 v4" stroke="{TERRA_D}" stroke-width="2" stroke-linecap="round"/>',
        "coffee": f'<path d="M41 50 h12 v8 a4 4 0 0 1-4 4 h-4 a4 4 0 0 1-4-4 z" fill="{TERRA_D}"/>'
                  f'<path d="M53 52 q5 0 5 3 t-5 3" stroke="{TERRA_D}" stroke-width="1.8" fill="none"/>',
        "liquid": f'<path d="M41 53 q7-7 14 0" stroke="{TERRA_D}" stroke-width="2.2"'
                  f' fill="none" stroke-linecap="round"/>',
    }
    m = motifs.get(motif, motifs["spice"])
    return svg(label, f"""
<rect x="30" y="16" width="36" height="8" rx="4" fill="{TERRA_D}"/>
<rect x="28" y="24" width="40" height="56" rx="8" fill="{col}" stroke="{TERRA_D}" stroke-width="2" stroke-opacity=".4"/>
<rect x="33" y="44" width="30" height="20" rx="3" fill="{CREAM}" opacity=".94"/>
{m}
""")


def _jar_butter(label, col):
    """Butter tub — squat tub, clearly not a spice jar."""
    return svg(label, f"""
<rect x="20" y="40" width="56" height="10" rx="4" fill="{TERRA_D}"/>
<path d="M24 50 h48 v24 a6 6 0 0 1 -6 6 H30 a6 6 0 0 1 -6-6 z" fill="{col}"/>
<rect x="32" y="56" width="32" height="14" rx="3" fill="{CREAM}" opacity=".94"/>
<rect x="38" y="60" width="20" height="6" rx="1.5" fill="{TERRA_D}"/>
""")


def _bag(label, col):
    """Flour/rice bag — gusseted sack with a folded top and weight block."""
    return svg(label, f"""
<path d="M28 28 h40 l-3 52 q-1 6-7 6 H38 q-6 0-7-6 z" fill="{col}" stroke="{TERRA_D}" stroke-width="2" stroke-opacity=".4"/>
<path d="M28 28 q20-8 40 0 v5 q-20-6-40 0 z" fill="{TERRA_D}"/>
<rect x="36" y="44" width="24" height="22" rx="3" fill="{CREAM}" opacity=".9"/>
<path d="M40 51 h16 M40 58 h10" stroke="{TERRA_D}" stroke-width="2" stroke-linecap="round"/>
<path d="M31 36 v42" stroke="{CREAM}" stroke-width="1.6" opacity=".35"/>
""")


def _egg(label):
    """Egg — shell with highlight and a crack-free clean silhouette."""
    return svg(label, f"""
<path d="M48 20 q-24 0 -24 36 q0 24 24 24 q24 0 24-24 q0-36 -24-36 z" fill="{CREAM_D}"/>
<path d="M48 20 q-24 0 -24 36 q0 24 24 24 q24 0 24-24 q0-36 -24-36 z"
      fill="none" stroke="{TERRA_D}" stroke-width="2" opacity=".4"/>
<ellipse cx="40" cy="44" rx="6" ry="9" fill="{CREAM}" opacity=".85"/>
""")


def _mortar(label):
    """Lesung batu — stone mortar bowl with pestle, no handles."""
    return svg(label, f"""
<path d="M22 50 h52 q-2 30 -26 30 q-24 0 -26-30 z" fill="{TERRA_D}"/>
<ellipse cx="48" cy="50" rx="26" ry="8" fill="{CREAM_D}"/>
<ellipse cx="48" cy="50" rx="19" ry="5" fill="{TERRA_D}"/>
<path d="M60 40 l14-22" stroke="{TERRA}" stroke-width="7" stroke-linecap="round"/>
<circle cx="75" cy="16" r="4" fill="{TERRA}"/>
""")


def _cup(label):
    """Cawan kertas — tapered paper cup with lid and sleeve."""
    return svg(label, f"""
<path d="M30 32 h36 l-5 48 q-1 6-7 6 H42 q-6 0-7-6 z" fill="{CREAM_D}"/>
<path d="M30 32 h36 l-1 8 H31 z" fill="{TERRA_D}"/>
<rect x="33" y="44" width="30" height="16" fill="{TERRA}" opacity=".9"/>
<path d="M27 28 h42" stroke="{TERRA_D}" stroke-width="4" stroke-linecap="round"/>
""")


def _machine(label, kind):
    """Small appliance box — used for ice cream / bread makers."""
    if kind == "icecream":
        return svg(label, f"""
<rect x="14" y="30" width="68" height="46" rx="9" fill="{TERRA}"/>
<rect x="20" y="36" width="34" height="7" rx="3" fill="{CREAM}"/>
<rect x="20" y="48" width="56" height="22" rx="7" fill="{SKY}"/>
<path d="M48 50 q-8 10 0 18 q8-8 0-18 z" fill="{CREAM}"/>
<circle cx="66" cy="40" r="4" fill="{TERRA_D}"/>
""")
    # bread maker: box with a loaf-shaped window
    return svg(label, f"""
<rect x="14" y="26" width="68" height="50" rx="9" fill="{TERRA}"/>
<rect x="20" y="33" width="56" height="26" rx="6" fill="{CREAM}"/>
<path d="M30 53 q0-12 18-12 q18 0 18 12 z" fill="{TERRA_D}" opacity=".85"/>
<rect x="20" y="63" width="30" height="6" rx="3" fill="{TERRA_D}"/>
<circle cx="66" cy="66" r="3.5" fill="{CREAM}"/>
""")


def _grater(label):
    """Pemarut — box grater with punched holes."""
    return svg(label, f"""
<path d="M34 20 h28 l6 56 H28 z" fill="{CREAM_D}"/>
<path d="M34 20 h14 l-6 56 H28 z" fill="{TERRA_D}" opacity=".18"/>
<circle cx="44" cy="34" r="2.4" fill="{TERRA_D}" opacity=".55"/>
<circle cx="54" cy="40" r="2.4" fill="{TERRA_D}" opacity=".55"/>
<circle cx="46" cy="48" r="2.4" fill="{TERRA_D}" opacity=".55"/>
<circle cx="56" cy="56" r="2.4" fill="{TERRA_D}" opacity=".55"/>
<circle cx="48" cy="64" r="2.4" fill="{TERRA_D}" opacity=".55"/>
<path d="M34 20 h28" stroke="{TERRA}" stroke-width="3.5" stroke-linecap="round"/>
""")


def _cloth(label):
    """Kertas pembakar / foil / cling wrap — a rolled sheet."""
    return svg(label, f"""
<rect x="18" y="34" width="60" height="30" rx="4" fill="{CREAM_D}"/>
<path d="M26 34 v30 M34 34 v30 M42 34 v30 M50 34 v30 M58 34 v30 M66 34 v30"
      stroke="{TERRA_D}" stroke-width="1.6" opacity=".35"/>
<rect x="18" y="30" width="60" height="7" rx="3.5" fill="{TERRA}"/>
<path d="M78 40 v18" stroke="{TERRA_D}" stroke-width="4" stroke-linecap="round"/>
""")


def _foil(label):
    """Aluminium foil — reflective roll with a torn edge."""
    return svg(label, f"""
<rect x="16" y="32" width="58" height="28" rx="4" fill="{SKY_D}"/>
<path d="M22 32 v28 M30 32 v28 M38 32 v28 M46 32 v28" stroke="{CREAM}" stroke-width="1.8" opacity=".6"/>
<path d="M74 32 l6 6 -6 6 6 6 -6 6" stroke="{SKY_D}" stroke-width="3" fill="none"/>
""")


def _scale_old(label, col):
    return _scale(label)



def _knife(label):
    """Pisau — chef blade with bolster and riveted handle."""
    return svg(label, f"""
<rect x="10" y="50" width="28" height="10" rx="5" fill="{INK}"/>
<circle cx="18" cy="55" r="1.8" fill="{CREAM}" opacity=".8"/>
<circle cx="26" cy="55" r="1.8" fill="{CREAM}" opacity=".8"/>
<rect x="38" y="48" width="6" height="14" rx="2" fill="{TERRA_D}"/>
<path d="M44 50 L84 38 L86 45 Q64 58 44 59 Z" fill="{TERRA}"/>
<path d="M47 55 L80 45" stroke="{CREAM}" stroke-width="1.8" opacity=".75"/>
""")


def _steamer(label):
    """Pengukus — two stacked bamboo tiers with lid and steam."""
    return svg(label, f"""
<path d="M32 46 q10-9 20 0" stroke="{SKY_D}" stroke-width="3" fill="none" stroke-linecap="round" opacity=".7"/>
<path d="M40 34 q8-8 16 0" stroke="{SKY_D}" stroke-width="3" fill="none" stroke-linecap="round" opacity=".45"/>
<path d="M22 54 h52 a4 4 0 0 1 4 4 v8 H18 v-8 a4 4 0 0 1 4-4 z" fill="{TERRA_D}"/>
<rect x="18" y="68" width="60" height="12" rx="3" fill="{TERRA}"/>
<path d="M26 74 h44" stroke="{CREAM}" stroke-width="2" opacity=".45"/>
<rect x="18" y="82" width="60" height="6" rx="3" fill="{TERRA_D}"/>
""")


def _blender(label):
    """Blender — tall tapered jug, lid, motor base with dial."""
    return svg(label, f"""
<rect x="36" y="12" width="24" height="6" rx="3" fill="{TERRA_D}"/>
<path d="M32 18 h32 l-4 40 h-24 z" fill="{SKY}"/>
<path d="M37 27 q11 8 22 0" stroke="{CREAM}" stroke-width="2.5" fill="none" opacity=".9"/>
<path d="M39 42 q9 6 18 0" stroke="{CREAM}" stroke-width="2" fill="none" opacity=".6"/>
<rect x="28" y="58" width="40" height="7" rx="3" fill="{TERRA_D}"/>
<rect x="31" y="65" width="34" height="19" rx="5" fill="{TERRA}"/>
<circle cx="48" cy="74" r="5" fill="{CREAM}"/>
<path d="M48 71 v6" stroke="{TERRA_D}" stroke-width="2" stroke-linecap="round"/>
""")


def _grinder(label):
    """Pengisar — compact dry/wet grinder: squat motor base + shallow bowl.

    Must NOT look like the blender. The blender has a TALL tapered jug; this
    has a LOW wide bowl and no long jug, which is what a food grinder is.
    """
    return svg(label, f"""
<rect x="24" y="58" width="48" height="24" rx="6" fill="{TERRA}"/>
<rect x="30" y="64" width="14" height="5" rx="2.5" fill="{CREAM_D}"/>
<circle cx="60" cy="70" r="6" fill="{CREAM}"/>
<path d="M60 67 v6 M57 70 h6" stroke="{TERRA_D}" stroke-width="1.8" stroke-linecap="round"/>
<rect x="30" y="52" width="36" height="7" rx="3" fill="{TERRA_D}"/>
<path d="M28 52 q0-20 20-20 q20 0 20 20 z" fill="{SKY}"/>
<ellipse cx="48" cy="33" rx="20" ry="5" fill="{SKY_D}"/>
<path d="M39 46 q9 5 18 0" stroke="{CREAM}" stroke-width="2" fill="none" opacity=".75"/>
<circle cx="48" cy="28" r="3" fill="{CREAM}" opacity=".85"/>
""")


# ---------------------------------------------------------- second wave builders
# Every keyword gets its OWN silhouette. Sharing a builder meant Spatula,
# Scissors and Satay-stick all rendered as the same chef's knife, and every
# protein rendered as the same plate. That reads as broken, not minimal.

def _spatula(label):
    """Spatula — flat slotted head with an offset neck."""
    return svg(label, f"""
<path d="M28 22 h26 a6 6 0 0 1 6 6 v22 a6 6 0 0 1 -6 6 H28 a6 6 0 0 1 -6-6 V28 a6 6 0 0 1 6-6 z" fill="{TERRA}"/>
<path d="M32 32 h18 M32 40 h18 M32 48 h18" stroke="{CREAM}" stroke-width="2.6" stroke-linecap="round" opacity=".85"/>
<path d="M54 44 q14 6 14 20 v14" stroke="{INK}" stroke-width="6" fill="none" stroke-linecap="round"/>
""")


def _scissors(label):
    """Gunting — two crossed blades with finger loops."""
    return svg(label, f"""
<path d="M30 20 L66 62" stroke="{TERRA}" stroke-width="7" stroke-linecap="round"/>
<path d="M66 20 L30 62" stroke="{TERRA_D}" stroke-width="7" stroke-linecap="round"/>
<circle cx="24" cy="70" r="9" fill="none" stroke="{INK}" stroke-width="4.5"/>
<circle cx="72" cy="70" r="9" fill="none" stroke="{INK}" stroke-width="4.5"/>
<circle cx="48" cy="41" r="3" fill="{INK}"/>
""")


def _skewer(label):
    """Lidi sate — stick threaded with three pieces of meat."""
    return svg(label, f"""
<path d="M14 74 L82 22" stroke="{CREAM_D}" stroke-width="4" stroke-linecap="round"/>
<rect x="26" y="52" width="16" height="14" rx="4" fill="{TERRA}" transform="rotate(-35 34 59)"/>
<rect x="41" y="40" width="16" height="14" rx="4" fill="{TERRA_D}" transform="rotate(-35 49 47)"/>
<rect x="56" y="28" width="16" height="14" rx="4" fill="{TERRA}" transform="rotate(-35 64 35)"/>
""")


def _strainer(label):
    """Penapis — mesh sieve with handle and rim."""
    return svg(label, f"""
<path d="M20 40 h52 q-6 26 -26 26 q-20 0 -26-26 z" fill="{CREAM_D}"/>
<path d="M20 40 h52" stroke="{TERRA_D}" stroke-width="5" stroke-linecap="round"/>
<path d="M30 48 h32 M34 55 h24" stroke="{TERRA_D}" stroke-width="1.8" opacity=".55"/>
<rect x="72" y="36" width="16" height="6" rx="3" fill="{INK}"/>
<circle cx="36" cy="52" r="1.6" fill="{TERRA_D}" opacity=".7"/>
<circle cx="44" cy="56" r="1.6" fill="{TERRA_D}" opacity=".7"/>
<circle cx="52" cy="52" r="1.6" fill="{TERRA_D}" opacity=".7"/>
""")


def _ladle(label):
    """Senduk — ladle with a long hooked handle."""
    return svg(label, f"""
<path d="M28 44 a20 20 0 0 0 40 0 z" fill="{TERRA}"/>
<ellipse cx="48" cy="44" rx="20" ry="6" fill="{TERRA_D}"/>
<path d="M68 42 q10-6 8-18" stroke="{INK}" stroke-width="6" fill="none" stroke-linecap="round"/>
<path d="M34 50 a15 12 0 0 0 28 0" fill="{CREAM}" opacity=".25"/>
""")


def _chicken(label):
    """Ayam — whole bird silhouette."""
    return svg(label, f"""
<path d="M22 58 q0-24 22-24 q10 0 14 6 q6-10 16-6 q-8 6-6 14 q10 6 8 18 q-16 10-30 8 q-22 2-24-16 z" fill="{TERRA}"/>
<circle cx="30" cy="44" r="2.6" fill="{INK}"/>
<path d="M22 52 q-8 0-10 6" stroke="{TERRA_D}" stroke-width="3" fill="none" stroke-linecap="round"/>
""")


def _meat(label):
    """Daging — thick cut of meat with marbling."""
    return svg(label, f"""
<path d="M24 42 q4-16 22-16 q22 0 24 18 q2 22-22 24 q-26 2-24-26 z" fill="{TERRA}"/>
<path d="M36 40 q10-6 20 0 M34 52 q12-5 24 0 M38 62 q10-4 18 0"
      stroke="{CREAM}" stroke-width="2.4" fill="none" stroke-linecap="round" opacity=".75"/>
""")


def _fish(label):
    """Ikan — whole fish with tail and fin."""
    return svg(label, f"""
<path d="M18 50 q18-20 44-6 q8-8 16-6 l-6 12 l6 12 q-8 2-16-6 q-26 14-44-6 z" fill="{SKY_D}"/>
<circle cx="32" cy="46" r="2.8" fill="{INK}"/>
<path d="M42 44 q8-8 6-12 M42 56 q8 8 6 12" stroke="{SKY}" stroke-width="2.4" fill="none" opacity=".8"/>
""")


def _shrimp(label):
    """Udang — curled prawn."""
    return svg(label, f"""
<path d="M64 28 q-30 0-30 24 q0 18 20 20" stroke="{TERRA}" stroke-width="10" fill="none" stroke-linecap="round"/>
<path d="M60 26 q10 2 12 10" stroke="{TERRA_D}" stroke-width="3" fill="none" stroke-linecap="round"/>
<circle cx="40" cy="44" r="2.6" fill="{INK}"/>
<path d="M52 74 l-6 10 M58 72 l-2 12" stroke="{TERRA_D}" stroke-width="2.4" stroke-linecap="round"/>
""")


def _squid(label):
    """Sotong — body with tentacles."""
    return svg(label, f"""
<path d="M48 16 q16 0 16 24 q0 16-16 22 q-16-6-16-22 q0-24 16-24 z" fill="{TERRA}"/>
<path d="M36 62 q-4 12-10 16 M44 64 q-2 14-6 18 M52 64 q2 14 6 18 M60 62 q4 12 10 16"
      stroke="{TERRA_D}" stroke-width="3.4" fill="none" stroke-linecap="round"/>
<circle cx="42" cy="34" r="2.4" fill="{INK}"/>
<circle cx="54" cy="34" r="2.4" fill="{INK}"/>
""")


def _tofu(label):
    """Tahu — pale cube block with cut face."""
    return svg(label, f"""
<path d="M22 40 L48 28 L74 40 L48 54 Z" fill="{CREAM}"/>
<path d="M22 40 v22 l26 13 v-21 z" fill="{CREAM_D}"/>
<path d="M48 54 v21 l26-13 V40 z" fill="#E8DCCB"/>
<path d="M34 46 l10-5" stroke="{TERRA_D}" stroke-width="1.6" opacity=".4"/>
""")


def _tempeh(label):
    """Tempe — slab with visible bean speckles and a wrapped edge."""
    return svg(label, f"""
<rect x="20" y="34" width="56" height="34" rx="4" fill="{CREAM_D}"/>
<rect x="20" y="34" width="56" height="10" rx="4" fill="{CREAM}"/>
<g fill="{TERRA_D}" opacity=".55">
<circle cx="30" cy="52" r="2.6"/><circle cx="38" cy="60" r="2.4"/>
<circle cx="46" cy="50" r="2.6"/><circle cx="54" cy="58" r="2.4"/>
<circle cx="62" cy="50" r="2.6"/><circle cx="70" cy="58" r="2.2"/>
<circle cx="34" cy="44" r="2.2"/><circle cx="52" cy="42" r="2.2"/>
</g>
""")


def _nuts(label):
    """Badam — three almonds."""
    return svg(label, f"""
<ellipse cx="36" cy="44" rx="10" ry="16" fill="{TERRA_D}" transform="rotate(-22 36 44)"/>
<ellipse cx="58" cy="40" rx="10" ry="16" fill="{TERRA}" transform="rotate(18 58 40)"/>
<ellipse cx="47" cy="66" rx="10" ry="16" fill="#B07B4A" transform="rotate(-6 47 66)"/>
<path d="M36 34 q2 10 0 20 M58 30 q-2 10 0 20" stroke="{CREAM}" stroke-width="1.6" opacity=".5"/>
""")


def _raisins(label):
    """Kismis — cluster of small dried fruit."""
    return svg(label, f"""
<circle cx="38" cy="46" r="9" fill="{TERRA_D}"/>
<circle cx="56" cy="42" r="8" fill="#6B4A2F"/>
<circle cx="50" cy="60" r="9.5" fill="{TERRA}"/>
<circle cx="34" cy="62" r="7" fill="#8A5A38"/>
<circle cx="64" cy="58" r="6.5" fill="{TERRA_D}"/>
<circle cx="35" cy="43" r="2.4" fill="{CREAM}" opacity=".5"/>
<circle cx="47" cy="57" r="2.6" fill="{CREAM}" opacity=".5"/>
""")


def _cookie(label):
    """Biskut — round biscuit with chips."""
    return svg(label, f"""
<circle cx="48" cy="50" r="28" fill="#D9A96B"/>
<circle cx="48" cy="50" r="28" fill="none" stroke="{TERRA_D}" stroke-width="2" opacity=".5"/>
<g fill="{TERRA_D}" opacity=".8">
<circle cx="38" cy="40" r="3.2"/><circle cx="56" cy="38" r="3"/>
<circle cx="48" cy="52" r="3.4"/><circle cx="34" cy="56" r="3"/>
<circle cx="60" cy="58" r="3.2"/>
</g>
""")


def _cheese(label):
    """Keju — wedge with holes."""
    return svg(label, f"""
<path d="M18 58 L48 26 L84 44 L84 58 Z" fill="#EFC96A"/>
<path d="M18 58 h66 v14 H18 z" fill="#DDB347"/>
<g fill="{TERRA_D}" opacity=".45">
<circle cx="46" cy="48" r="4"/><circle cx="64" cy="52" r="3.2"/><circle cx="34" cy="62" r="3"/>
</g>
""")


def _yogurt(label):
    """Yogurt — squat tub with a spoon standing in it."""
    return svg(label, f"""
<path d="M26 42 h44 l-4 34 a6 6 0 0 1 -6 5 H36 a6 6 0 0 1 -6-5 z" fill="#F4EAD6"/>
<path d="M26 42 h44 l-4 34 a6 6 0 0 1 -6 5 H36 a6 6 0 0 1 -6-5 z" fill="none" stroke="{TERRA_D}" stroke-width="2.2" opacity=".5"/>
<path d="M26 42 h44" stroke="{TERRA}" stroke-width="4.5" stroke-linecap="round"/>
<ellipse cx="48" cy="42" rx="22" ry="5" fill="{CREAM_D}"/>
<path d="M58 20 v22" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>
<ellipse cx="58" cy="44" rx="6" ry="4" fill="{INK}"/>
""")


def _pipingbag(label):
    """Piping bag — cone with a nozzle tip."""
    return svg(label, f"""
<path d="M26 22 L70 22 L52 74 L44 74 Z" fill="{CREAM_D}"/>
<path d="M26 22 L70 22" stroke="{TERRA_D}" stroke-width="5" stroke-linecap="round"/>
<path d="M44 74 h8 l-2 10 h-4 z" fill="{TERRA}"/>
<path d="M34 34 q14 6 28 0 M38 46 q10 5 20 0" stroke="{TERRA_D}" stroke-width="1.8" opacity=".45" fill="none"/>
""")


def _wrap(label):
    """Plastik pembalut — roll with a pulled sheet."""
    return svg(label, f"""
<rect x="16" y="30" width="52" height="20" rx="10" fill="{SKY_D}"/>
<circle cx="58" cy="40" r="9" fill="{CREAM}"/>
<path d="M16 50 v18 q0 4 4 4 h34 v-22" fill="{CREAM_D}" opacity=".85"/>
<path d="M20 20 h48" stroke="{TERRA_D}" stroke-width="3" stroke-linecap="round" opacity=".6"/>
""")


def _ricecooker(label):
    """Periuk nasi — rice cooker with a domed lid."""
    return svg(label, f"""
<path d="M20 48 q0-18 28-18 q28 0 28 18 v14 a8 8 0 0 1 -8 8 H28 a8 8 0 0 1 -8-8 z" fill="{TERRA}"/>
<path d="M20 48 q0-16 28-16 q28 0 28 16 z" fill="{CREAM_D}"/>
<rect x="40" y="20" width="16" height="8" rx="4" fill="{INK}"/>
<circle cx="66" cy="52" r="4" fill="{CREAM}"/>
<rect x="34" y="56" width="28" height="8" rx="2" fill="{CREAM}" opacity=".6"/>
""")


def _kettle(label):
    """Cerek elektrik — kettle with spout and handle."""
    return svg(label, f"""
<path d="M28 44 q0-16 20-16 q20 0 20 16 v20 a6 6 0 0 1 -6 6 H34 a6 6 0 0 1 -6-6 z" fill="{TERRA}"/>
<path d="M40 28 h16" stroke="{TERRA_D}" stroke-width="5" stroke-linecap="round"/>
<path d="M28 46 l-12-8 v12 z" fill="{TERRA_D}"/>
<path d="M68 44 q12 6 0 24" stroke="{INK}" stroke-width="5" fill="none" stroke-linecap="round"/>
""")


def _microwave(label):
    """Microwave — wide box with door window and keypad."""
    return svg(label, f"""
<rect x="12" y="30" width="72" height="40" rx="6" fill="{TERRA}"/>
<rect x="18" y="36" width="44" height="28" rx="3" fill="{SKY}"/>
<rect x="64" y="36" width="14" height="10" rx="2" fill="{CREAM}"/>
<circle cx="71" cy="56" r="4" fill="{CREAM}"/>
<path d="M22 42 h36" stroke="{CREAM}" stroke-width="2" opacity=".6"/>
""")


def _freezer(label):
    """Peti sejuk beku — upright freezer with a snowflake."""
    return svg(label, f"""
<rect x="24" y="16" width="48" height="66" rx="6" fill="{SKY}"/>
<rect x="24" y="16" width="48" height="22" rx="6" fill="{SKY_D}"/>
<path d="M48 48 v22 M40 53 L56 65 M56 53 L40 65" stroke="{CREAM}" stroke-width="2.6" stroke-linecap="round"/>
<rect x="62" y="24" width="4" height="10" rx="2" fill="{CREAM}"/>
""")


def _tray_takoyaki(label):
    """Acuan takoyaki — cast tray of round wells."""
    return svg(label, f"""
<rect x="14" y="30" width="68" height="40" rx="6" fill="{INK}" opacity=".8"/>
<g fill="{TERRA}">
<circle cx="30" cy="42" r="7"/><circle cx="48" cy="42" r="7"/><circle cx="66" cy="42" r="7"/>
<circle cx="30" cy="58" r="7"/><circle cx="48" cy="58" r="7"/><circle cx="66" cy="58" r="7"/>
</g>
""")


def _mayo(label):
    """Mayonis — squeeze bottle with a nozzle."""
    return svg(label, f"""
<path d="M42 14 h12 v10 h-12 z" fill="{TERRA_D}"/>
<path d="M38 26 h20 q10 8 10 24 v24 q0 6-6 6 H34 q-6 0-6-6 V50 q0-16 10-24 z" fill="#F2E4C9"/>
<path d="M38 26 h20 q10 8 10 24 v24 q0 6-6 6 H34 q-6 0-6-6 V50 q0-16 10-24 z" fill="none" stroke="{TERRA_D}" stroke-width="2.2" opacity=".55"/>
<rect x="32" y="52" width="32" height="16" rx="3" fill="{TERRA}" opacity=".9"/>
<path d="M38 58 h20" stroke="{CREAM}" stroke-width="2.4" stroke-linecap="round"/>
""")


def _cuka(label):
    """Cuka — slim vinegar bottle with a narrow neck."""
    return svg(label, f"""
<rect x="42" y="12" width="12" height="8" rx="3" fill="{INK}"/>
<path d="M42 20 h12 v14 q12 8 12 26 v14 q0 6-6 6 H36 q-6 0-6-6 V60 q0-18 12-26 z" fill="#E3D9B8"/>
<rect x="32" y="56" width="32" height="16" rx="3" fill="{TERRA}" opacity=".85"/>
<path d="M38 63 h20" stroke="{CREAM}" stroke-width="2" stroke-linecap="round"/>
""")


def _sauce_thai(label):
    """Sos Thai — bottle with a chili glyph."""
    return svg(label, f"""
<rect x="40" y="14" width="16" height="8" rx="3" fill="{TERRA_D}"/>
<path d="M40 22 h16 v10 q10 6 10 20 v24 q0 6-6 6 H36 q-6 0-6-6 V52 q0-14 10-20 z" fill="#D9533B"/>
<rect x="31" y="52" width="34" height="18" rx="3" fill="{CREAM}"/>
<path d="M40 56 q8-8 16 0 q-8 8-16 0 z" fill="#B03A2A"/>
""")


def _sambal(label):
    """Sambal — shallow bowl of chunky chili paste."""
    return svg(label, f"""
<path d="M24 46 a24 24 0 0 0 48 0 z" fill="{CREAM_D}"/>
<ellipse cx="48" cy="46" rx="24" ry="7" fill="#B03A2A"/>
<circle cx="38" cy="44" r="3" fill="{TERRA_D}"/>
<circle cx="54" cy="46" r="2.6" fill="{TERRA_D}"/>
<circle cx="46" cy="42" r="2.2" fill="#8A2A1E"/>
<path d="M24 46 a24 24 0 0 0 48 0" fill="none" stroke="{TERRA}" stroke-width="2.5"/>
""")


def _pasta(label):
    """Pasta — bundle of spaghetti tied with a band."""
    return svg(label, f"""
<path d="M34 24 q14 26 0 52 M44 20 q14 30 0 58 M54 20 q14 30 0 58 M64 24 q12 24 0 52"
      stroke="#E8C97A" stroke-width="4" fill="none" stroke-linecap="round"/>
<rect x="32" y="46" width="34" height="10" rx="3" fill="{TERRA}"/>
""")


def _noodles(label):
    """Mee / bihun / kuetiau — noodle nest."""
    return svg(label, f"""
<g stroke="#E8C97A" stroke-width="4" fill="none" stroke-linecap="round">
<path d="M22 40 q14-12 26 0 q12 12 26 0"/>
<path d="M22 50 q14-12 26 0 q12 12 26 0"/>
<path d="M22 60 q14-12 26 0 q12 12 26 0"/>
</g>
<rect x="20" y="66" width="56" height="6" rx="3" fill="{TERRA_D}" opacity=".5"/>
""")


def _mushroom(label):
    """Cendawan — cap and stem."""
    return svg(label, f"""
<path d="M20 50 q0-26 28-26 q28 0 28 26 z" fill="{TERRA_D}"/>
<path d="M38 50 h20 v20 q0 6-10 6 q-10 0-10-6 z" fill="{CREAM_D}"/>
<circle cx="36" cy="40" r="3" fill="{CREAM}" opacity=".6"/>
<circle cx="56" cy="36" r="2.6" fill="{CREAM}" opacity=".6"/>
""")


def _broccoli(label):
    """Brokoli — florets on a stalk."""
    return svg(label, f"""
<g fill="{GREEN}">
<circle cx="36" cy="36" r="11"/><circle cx="54" cy="32" r="10"/>
<circle cx="64" cy="44" r="9"/><circle cx="30" cy="48" r="9"/>
</g>
<path d="M44 50 q0 20 4 30" stroke="#8FAE87" stroke-width="8" fill="none" stroke-linecap="round"/>
""")


def _star_anise(label):
    """Bunga lawang — eight-point star."""
    return svg(label, f"""
<g fill="none" stroke="{TERRA_D}" stroke-width="3.4" stroke-linejoin="round">
<path d="M48 20 L54 40 L74 38 L58 52 L68 70 L48 58 L28 70 L38 52 L22 38 L42 40 Z"/>
</g>
<circle cx="48" cy="46" r="4" fill="{TERRA_D}"/>
""")


def _clove(label):
    """Bunga cengkih — nail-shaped buds."""
    return svg(label, f"""
<path d="M34 26 q4 20 6 30 q2 10-4 10 q-6 0-6-10 q0-14 4-30 z" fill="{TERRA_D}"/>
<path d="M62 22 q4 22 6 32 q2 10-4 10 q-6 0-6-10 q0-16 4-32 z" fill="#6B4A2F"/>
<circle cx="34" cy="24" r="5" fill="{TERRA}"/>
<circle cx="62" cy="20" r="5" fill="{TERRA_D}"/>
""")


def _cardamom(label):
    """Buah pelaga — three pods."""
    return svg(label, f"""
<ellipse cx="38" cy="46" rx="9" ry="18" fill="{GREEN}" transform="rotate(-18 38 46)"/>
<ellipse cx="60" cy="42" rx="9" ry="18" fill="#A9C49B" transform="rotate(20 60 42)"/>
<ellipse cx="50" cy="66" rx="8" ry="15" fill="#9BB07E" transform="rotate(-4 50 66)"/>
<path d="M38 32 v28 M60 28 v28" stroke="{CREAM}" stroke-width="1.4" opacity=".45"/>
""")


def _lime(label):
    """Limau — citrus half with segments."""
    return svg(label, f"""
<circle cx="46" cy="48" r="26" fill="#8FAE87"/>
<circle cx="46" cy="48" r="20" fill="{CREAM_D}"/>
<g stroke="#C6CE9E" stroke-width="2.4" fill="none">
<path d="M46 28 v40 M26 48 h40 M32 34 L60 62 M60 34 L32 62"/>
</g>
<circle cx="46" cy="48" r="4" fill="{CREAM}"/>
<path d="M72 26 q8 4 8 12" stroke="{GREEN}" stroke-width="3" fill="none" stroke-linecap="round"/>
""")


def _bakingcup(label):
    """Cawan kertas — fluted paper case."""
    return svg(label, f"""
<path d="M30 34 h36 l-6 44 q-1 6-7 6 H43 q-6 0-7-6 z" fill="{CREAM_D}"/>
<path d="M34 34 l-2 44 M42 34 l-1 44 M54 34 l1 44 M62 34 l2 44" stroke="{TERRA_D}" stroke-width="1.6" opacity=".4"/>
<path d="M28 30 h40 v6 H28 z" fill="{TERRA}"/>
""")


def _tupperware(label):
    """Bekas makanan — rectangular container with a clipping lid."""
    return svg(label, f"""
<rect x="18" y="34" width="60" height="10" rx="4" fill="{TERRA_D}"/>
<path d="M22 44 h52 v30 a6 6 0 0 1 -6 6 H28 a6 6 0 0 1 -6-6 z" fill="#E4D6C2"/>
<path d="M22 44 h52 v30 a6 6 0 0 1 -6 6 H28 a6 6 0 0 1 -6-6 z" fill="none" stroke="{TERRA_D}" stroke-width="2" stroke-opacity=".5"/>
<rect x="34" y="52" width="28" height="14" rx="2" fill="{CREAM}"/>
<rect x="18" y="30" width="10" height="14" rx="4" fill="{TERRA}"/>
<rect x="68" y="30" width="10" height="14" rx="4" fill="{TERRA}"/>
""")


def _cendol_cup(label):
    """Cawan — simple drinking cup with a straw."""
    return svg(label, f"""
<path d="M30 30 h36 l-6 50 q-1 6-7 6 H43 q-6 0-7-6 z" fill="{CREAM}"/>
<path d="M30 30 h36" stroke="{TERRA_D}" stroke-width="4" stroke-linecap="round"/>
<path d="M56 12 L48 44" stroke="{TERRA}" stroke-width="4" stroke-linecap="round"/>
""")


def _castard(label):
    """Tepung kastard — yellow powder bag, distinct from flour."""
    return svg(label, f"""
<path d="M28 30 h40 l-3 50 q-1 6-7 6 H38 q-6 0-7-6 z" fill="#F0E2A8"/>
<path d="M28 30 q20-8 40 0 v5 q-20-6-40 0 z" fill="{TERRA_D}"/>
<rect x="36" y="46" width="24" height="20" rx="3" fill="{CREAM}" opacity=".9"/>
<path d="M40 53 h16 M40 60 h10" stroke="#C9A94A" stroke-width="2" stroke-linecap="round"/>
""")


def _broth(label):
    """Beras — rice grains poured from a scoop."""
    return svg(label, f"""
<ellipse cx="44" cy="58" rx="24" ry="12" fill="{CREAM_D}"/>
<g fill="{CREAM}" stroke="{CREAM_D}" stroke-width="1">
<ellipse cx="34" cy="54" rx="5" ry="3" transform="rotate(-20 34 54)"/>
<ellipse cx="46" cy="52" rx="5" ry="3" transform="rotate(15 46 52)"/>
<ellipse cx="56" cy="58" rx="5" ry="3" transform="rotate(-10 56 58)"/>
<ellipse cx="42" cy="62" rx="5" ry="3" transform="rotate(20 42 62)"/>
</g>
<path d="M62 30 q10 4 6 16" stroke="{TERRA_D}" stroke-width="4" fill="none" stroke-linecap="round"/>
""")



def _tomato(label):
    """Tomato — round fruit with calyx."""
    return svg(label, f"""
<circle cx="48" cy="54" r="26" fill="#C94A3A"/>
<circle cx="40" cy="46" r="6" fill="{CREAM}" opacity=".28"/>
<path d="M48 30 q-8-6-14-2 q6 0 8 6 q-8-2-10 4 q8-2 12 2 q4-4 12-2 q-2-6-10-4 q2-6 8-6 q-6-4-14 2 z" fill="{GREEN}"/>
<path d="M48 28 v6" stroke="{GREEN}" stroke-width="3" stroke-linecap="round"/>
""")


def _potato(label):
    """Kentang — lumpy tuber with eyes."""
    return svg(label, f"""
<path d="M24 44 q2-18 24-18 q24 0 26 20 q2 22-24 24 q-28 2-26-26 z" fill="#C9A76B"/>
<path d="M24 44 q2-18 24-18 q24 0 26 20 q2 22-24 24 q-28 2-26-26 z"
      fill="none" stroke="#A8854E" stroke-width="2" opacity=".55"/>
<g fill="#8C6B3F" opacity=".7">
<circle cx="38" cy="42" r="2.4"/><circle cx="58" cy="50" r="2.2"/>
<circle cx="46" cy="60" r="2.4"/><circle cx="62" cy="38" r="1.8"/>
</g>
""")


def _carrot(label):
    """Lobak merah — tapered root with fronds."""
    return svg(label, f"""
<path d="M40 34 q18 0 18 10 q0 26-14 44 q-6-18-10-44 q-2-10 6-10 z" fill="#D9702F"/>
<path d="M44 46 h12 M42 56 h12 M44 66 h8" stroke="{CREAM}" stroke-width="1.8" opacity=".5" stroke-linecap="round"/>
<path d="M46 32 q-4-12-12-16 M48 32 q0-14 4-18 M50 32 q8-12 14-14"
      stroke="{GREEN}" stroke-width="3.4" fill="none" stroke-linecap="round"/>
""")


def _corn(label):
    """Jagung — cob with husk leaves."""
    return svg(label, f"""
<ellipse cx="48" cy="50" rx="15" ry="30" fill="#E8C24E"/>
<g stroke="#C9A02F" stroke-width="1.4" opacity=".7">
<path d="M38 34 h20 M36 44 h24 M36 54 h24 M38 64 h20"/>
<path d="M44 30 v42 M52 30 v42"/>
</g>
<path d="M33 40 q-14 6-16 26 q12 2 18-10 z" fill="{GREEN}"/>
<path d="M63 40 q14 6 16 26 q-12 2-18-10 z" fill="#8FAE87"/>
""")


def _leafy(label):
    """Daun — leafy sprig, used for pandan / curry leaf / sup / bawang."""
    return svg(label, f"""
<path d="M48 82 q-2-34 0-52" stroke="#6E8B5E" stroke-width="3.4" fill="none" stroke-linecap="round"/>
<path d="M48 60 q-20-4-24-18 q18 0 24 12 z" fill="{GREEN}"/>
<path d="M48 46 q20-4 24-18 q-18 0-24 12 z" fill="#8FAE87"/>
<path d="M48 34 q-16-4-18-14 q14 0 18 9 z" fill="#A9C49B"/>
""")


# keyword -> (svg builder, aria label)
ILLUSTRATIONS = {
    # appliances
    "Oven / Ketuhar": (_oven, "Oven"),
    "Pengukus Elektrik (Electric Steamer)": (_steamer, "Pengukus elektrik"),
    "Air Fryer": (_oven, "Air fryer"),
    "Blender": (_blender, "Blender"),
    "Pengisar / Grinder": (_grinder, "Pengisar"),
    "Mixer / Pengadun": (_mixer, "Mixer"),
    "Rice Cooker (Periuk Nasi Elektrik)": (_ricecooker, "Periuk nasi"),
    "Pressure Cooker": (_pressure_cooker, "Periuk tekanan"),
    "Slow Cooker": (_pot, "Slow cooker"),
    "Bread Maker / Mesin Roti": (lambda l: _machine(l,"bread"), "Mesin roti"),
    "Waffle Maker": (_waffle, "Acuan waffle"),
    "Ice Cream Maker": (lambda l: _machine(l,"icecream"), "Mesin aiskrim"),
    "Yogurt Maker": (lambda l: _machine(l,"icecream"), "Yogurt maker"),
    "Grill Pan / Pemanggang": (_grill, "Pemanggang"),
    "Toaster": (_loaf, "Pembakar roti"),
    "Electric Kettle": (_kettle, "Cerek elektrik"),
    "Microwave": (_microwave, "Microwave"),
    "Freezer / Peti Sejuk Beku": (_freezer, "Peti sejuk beku"),
    "Acuan Takoyaki": (_tray_takoyaki, "Acuan takoyaki"),

    # equipment
    "Kuali": (_wok, "Kuali"),
    "Periuk": (_pot, "Periuk"),
    "Periuk Belanga": (_pot, "Periuk belanga"),
    "Loyang / Acuan Kek": (_tray, "Loyang kek"),
    "Acuan Kuih / Kek": (_mould_tray, "Acuan kuih"),
    "Pengukus (Kukusan)": (_steamer, "Pengukus"),
    "Pisau Dapur": (_knife, "Pisau dapur"),
    "Papan Pemotong / Talenan": (_board, "Papan pemotong"),
    "Pemarut (Grater)": (_grater, "Pemarut"),
    "Lesung Batu": (_mortar, "Lesung batu"),
    "Penapis / Strainer": (_strainer, "Penapis"),
    "Spatula": (_spatula, "Spatula"),
    "Senduk": (_ladle, "Senduk"),
    "Gunting Dapur": (_scissors, "Gunting dapur"),
    "Penimbang Dapur (Kitchen Scale)": (_scale, "Penimbang dapur"),
    "Termometer Dapur": (_scale, "Termometer"),
    "Piping Bag + Nozel": (_pipingbag, "Piping bag"),
    "Bekas Makanan / Container": (_tupperware, "Bekas makanan"),
    "Tupperware": (_tupperware, "Bekas makanan"),
    "Botol Kaca / Plastik": (_bottle, "Botol"),
    "Aluminium Foil": (_foil, "Aluminium foil"),
    "Plastik Pembalut / Cling Wrap": (_wrap, "Plastik pembalut"),
    "Kertas Pembakar": (_cloth, "Kertas pembakar"),
    "Lidi Sate": (_skewer, "Lidi sate"),
    "Cawan / Paper Cup": (_bakingcup, "Cawan"),

    # sauces
    "Sos Tiram": (_bottle, "Sos tiram"),
    "Sos Cili": (_bottle, "Sos cili"),
    "Sos Tomato": (_bottle, "Sos tomato"),
    "Sos Lada Hitam": (_bottle, "Sos lada hitam"),
    "Sos Thai": (_sauce_thai, "Sos thai"),
    "Sos Ikan": (_bottle, "Sos ikan"),
    "Mayonis": (_mayo, "Mayonis"),
    "Kicap": (_bottle, "Kicap"),
    "Cuka": (_cuka, "Cuka"),
    "Sambal (Pes)": (_sambal, "Sambal"),
    "Sos (Umum)": (_bottle, "Sos"),

    # dry goods
    "Tepung Gandum": (_bag, "Tepung gandum"),
    "Tepung Beras": (_bag, "Tepung beras"),
    "Tepung Pulut": (_bag, "Tepung pulut"),
    "Tepung Jagung": (_bag, "Tepung jagung"),
    "Tepung Kastard": (_castard, "Tepung kastard"),
    "Tepung (Umum)": (_bag, "Tepung"),
    "Beras": (_broth, "Beras"),
    "Beras Pulut": (_broth, "Beras pulut"),
    "Gula": (lambda l: _jar(l, COLOURS.get("Gula","#EFE6D2"), "sugar"), "Gula"),
    "Gula Melaka": (lambda l: _jar(l, COLOURS.get("Gula Melaka","#B07B4A"), "sugar"), "Gula melaka"),
    "Gula Aising": (lambda l: _jar(l, COLOURS.get("Gula Aising","#EFE6D2"), "sugar"), "Gula aising"),
    "Garam": (lambda l: _jar(l, COLOURS.get("Garam","#EDE7DC"), "sugar"), "Garam"),
    "Minyak Masak": (_bottle, "Minyak masak"),
    "Mentega": (_jar_butter, "Mentega"),
    "Marjerin": (_jar_butter, "Marjerin"),
    "Susu Pekat Manis": (lambda l: _jar(l, COLOURS.get("Susu Pekat Manis","#E4C98F"), "liquid"), "Susu pekat"),
    "Cream Cheese": (lambda l: _jar(l, COLOURS.get("Cream Cheese","#F4EEDD"), "liquid"), "Cream cheese"),
    "Whipping Cream": (_bottle, "Krim putar"),
    "Keju": (_cheese, "Keju"),
    "Yogurt": (_yogurt, "Yogurt"),
    "Santan": (_bottle, "Santan"),
    "Kelapa Parut": (_coconut, "Kelapa parut"),
    "Serbuk Penaik": (lambda l: _jar(l, "#EFEAD9", "spice"), "Serbuk penaik"),
    "Soda Bikarbonat": (lambda l: _jar(l, "#EFEAD9", "spice"), "Soda bikarbonat"),
    "Esens Vanila": (_bottle, "Esens vanila"),
    "Agar-Agar": (_bag, "Agar-agar"),
    "Gelatin": (_bag, "Gelatin"),
    "Ragi (Yeast)": (_bag, "Ragi"),
    "Pewarna Makanan": (_bottle, "Pewarna"),
    "Serbuk Koko": (_bag, "Serbuk koko"),
    "Coklat Masakan": (lambda l: _jar(l, COLOURS.get("Coklat Masakan","#6B4226"), "cocoa"), "Coklat"),
    "Horlicks": (lambda l: _jar(l, COLOURS.get("Horlicks","#C8A06A"), "malt"), "Horlicks"),
    "Milo": (lambda l: _jar(l, COLOURS.get("Milo","#7A5234"), "cocoa"), "Milo"),
    "Kopi / Nescafe": (lambda l: _jar(l, COLOURS.get("Kopi / Nescafe","#5A3E2B"), "coffee"), "Kopi"),
    "Badam": (_nuts, "Badam"),
    "Kismis": (_raisins, "Kismis"),
    "Biskut": (_cookie, "Biskut"),
    "Biskut Oreo": (_cookie, "Biskut"),

    # spices
    "Serbuk Kari": (lambda l: _jar(l, COLOURS.get("Serbuk Kari","#C88A3E"), "spice"), "Serbuk kari"),
    "Rempah Kurma": (lambda l: _jar(l, COLOURS.get("Rempah Kurma","#C88A3E"), "spice"), "Rempah kurma"),
    "Serbuk Rempah Sup": (lambda l: _jar(l, COLOURS.get("Serbuk Rempah Sup","#C88A3E"), "spice"), "Rempah sup"),
    "Cili Kisar / Cili Boh": (lambda l: _jar(l, COLOURS.get("Cili Kisar / Cili Boh","#D9533B"), "spice"), "Cili boh"),
    "Serbuk Kunyit": (lambda l: _jar(l, COLOURS.get("Serbuk Kunyit","#E0A93B"), "spice"), "Kunyit"),
    "Lada Hitam": (lambda l: _jar(l, COLOURS.get("Lada Hitam","#4A4038"), "spice"), "Lada hitam"),
    "Lada Putih": (lambda l: _jar(l, COLOURS.get("Lada Putih","#E3DCCB"), "spice"), "Lada putih"),
    "Serbuk Ketumbar": (lambda l: _jar(l, COLOURS.get("Serbuk Ketumbar","#B79A5E"), "spice"), "Ketumbar"),
    "Jintan": (lambda l: _jar(l, COLOURS.get("Jintan","#8C6B3F"), "spice"), "Jintan"),
    "Bunga Lawang": (_star_anise, "Bunga lawang"),
    "Bunga Cengkih": (_clove, "Cengkih"),
    "Kayu Manis": (lambda l: _jar(l, COLOURS.get("Kayu Manis","#A9723F"), "spice"), "Kayu manis"),
    "Buah Pelaga": (_cardamom, "Buah pelaga"),
    "Rempah (Umum)": (lambda l: _jar(l, COLOURS.get("Rempah (Umum)","#C88A3E"), "spice"), "Rempah"),

    # protein / produce
    "Telur": (_egg, "Telur"),
    "Ayam": (_chicken, "Ayam"),
    "Daging": (_meat, "Daging"),
    "Daging Kisar": (_meat, "Daging kisar"),
    "Ikan": (_fish, "Ikan"),
    "Udang": (_shrimp, "Udang"),
    "Sotong": (_squid, "Sotong"),
    "Tahu": (_tofu, "Tahu"),
    "Tempe": (_tempeh, "Tempe"),
    "Tomato": (_tomato, "Tomato"),
    "Kentang": (_potato, "Kentang"),
    "Lobak Merah": (_carrot, "Lobak merah"),
    "Jagung": (_corn, "Jagung"),
    "Cendawan": (_mushroom, "Cendawan"),
    "Brokoli": (_broccoli, "Brokoli"),
    "Bawang": (lambda l: _jar(l, "#E4D3C0", "liquid"), "Bawang"),
    "Bawang Putih": (lambda l: _jar(l, "#EFE6D2", "liquid"), "Bawang putih"),
    "Bawang Merah": (lambda l: _jar(l, "#C97B6B", "liquid"), "Bawang merah"),
    "Bawang Besar": (lambda l: _jar(l, "#E4D3C0", "liquid"), "Bawang besar"),
    "Halia": (lambda l: _jar(l, "#D8C08A", "liquid"), "Halia"),
    "Serai": (lambda l: _jar(l, "#C6CE9E", "liquid"), "Serai"),
    "Lengkuas": (lambda l: _jar(l, "#D8C08A", "liquid"), "Lengkuas"),
    "Cili": (lambda l: _jar(l, "#D9533B", "spice"), "Cili"),
    "Cili Api": (lambda l: _jar(l, "#C43A28", "spice"), "Cili api"),
    "Daun Pandan": (_leafy, "Daun pandan"),
    "Daun Kari": (_leafy, "Daun kari"),
    "Daun Sup": (_leafy, "Daun sup"),
    "Daun Bawang": (_leafy, "Daun bawang"),
    "Limau": (_lime, "Limau"),
    "Limau Purut": (_lime, "Limau purut"),
    "Limau Nipis": (_lime, "Limau nipis"),
    "Bihun": (_noodles, "Bihun"),
    "Mee": (_noodles, "Mee"),
    "Kuetiau": (_noodles, "Kuetiau"),
    "Pasta / Spaghetti": (_pasta, "Pasta"),
}

# Colour overrides where the generic builder needs a different fill.
COLOURS = {
    "Sos Cili": "#D9533B",
    "Sos Tomato": "#D9533B",
    "Sos Lada Hitam": "#5A4632",
    "Sos Tiram": "#6B4A2F",
    "Sos Thai": "#D9533B",
    "Sos Ikan": "#8A6A3B",
    "Kicap": "#4A342A",
    "Cuka": "#E3D9B8",
    "Mayonis": "#F2E9C9",
    "Minyak Masak": "#E8C97A",
    "Santan": "#EADFC6",
    "Whipping Cream": "#F4EFE2",
    "Gula Melaka": "#B07B4A",
    "Gula": "#EFE6D2",
    "Gula Aising": "#EFE6D2",
    "Garam": "#EDE7DC",
    "Tepung Gandum": "#E7D8BE",
    "Tepung Beras": "#EFEAD9",
    "Tepung Pulut": "#EFEAD9",
    "Tepung Jagung": "#F3EEDC",
    "Tepung Kastard": "#F0E2A8",
    "Beras": "#EFEAD9",
    "Beras Pulut": "#EFEAD9",
    "Mentega": "#EFD98A",
    "Marjerin": "#EFD98A",
    "Susu Pekat Manis": "#E4C98F",
    "Yogurt": "#F2EEE4",
    "Keju": "#EFC96A",
    "Cream Cheese": "#F4EEDD",
    "Serbuk Koko": "#7A5234",
    "Coklat Masakan": "#6B4226",
    "Horlicks": "#C8A06A",
    "Milo": "#7A5234",
    "Kopi / Nescafe": "#5A3E2B",
    "Agar-Agar": "#F0EAD9",
    "Gelatin": "#F0EAD9",
    "Ragi (Yeast)": "#E8DCC0",
    "Pewarna Makanan": "#E9A0B4",
    "Bihun": "#F0EAD9",
    "Mee": "#EFD98A",
    "Kuetiau": "#F0EAD9",
    "Pasta / Spaghetti": "#EFD98A",
    "Esens Vanila": "#C9973F",
}


def illustration_for(keyword):
    """Return SVG string for a keyword, falling back to a plate mark."""
    entry = ILLUSTRATIONS.get(keyword)
    if entry is None:
        return _plate("Dapur")
    builder, label = entry

    # Lambdas from the registry already close over their colour + motif.
    if builder.__name__ == "<lambda>":
        try:
            return builder(label)
        except TypeError:
            return _plate(label)

    # Factories that take (label, colour) or (label, kind)
    if builder is _jar_butter:
        return builder(label, COLOURS.get(keyword, TERRA_D))
    if builder is _pot:
        return builder(label, TERRA)
    if builder in (_jar, _bag, _bottle):
        col = COLOURS.get(keyword)
        if col:
            return builder(label, col)
        if builder is _bag:
            return builder(label, "#E7D8BE")
        if builder is _jar:
            return builder(label, TERRA_D)
        return builder(label, TERRA)
    # single-arg builders
    return builder(label)


def write_all():
    """Write one .svg per keyword into static/ads/. Returns count."""
    n = 0
    for kw in ILLUSTRATIONS:
        s = illustration_for(kw)
        safe = (kw.lower().replace(" / ", "-").replace(" ", "-")
                .replace("(", "").replace(")", "").replace("+", "")
                .replace("/", "-"))
        (OUT / f"{safe}.svg").write_text(s)
        n += 1
    return n


if __name__ == "__main__":
    n = write_all()
    total = sum(p.stat().st_size for p in OUT.glob("*.svg"))
    print(f"wrote {n} illustrations to {OUT}")
    print(f"total size: {total/1024:.1f} KB  (avg {total/n:.0f} bytes each)")
