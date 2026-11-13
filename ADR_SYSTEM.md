# Ad System — Stage 1 (engine, art, cards)

Built 2026-11-14. No popup. No homepage ads. No runtime JS.

---

## What exists now

| File | Purpose |
|---|---|
| `ads.py` | Trigger engine — picks one product per slot from the recipe's own text |
| `ad_art.py` | 142 procedural SVG illustrations, site palette |
| `ad_render.py` | Card renderer (3 layouts) + preview page builder |
| `ad_preview/index.html` | Live preview of every card variant |
| `static/ads/*.svg` | 143 written SVG files, 490 bytes avg |

Rebuild: `python3 ad_art.py && python3 ad_render.py`

---

## Trigger priority — the core design decision

Commodities fire on almost every page, so a naive "highest count wins" rule would
show **Garam** on 495 pages and turn the ads into wallpaper nobody sees.

Ladder, highest first:

1. **appliance** — oven, steamer, air fryer, blender (11 keywords)
2. **equipment** — kuali, loyang, pengukus, pisau (14 keywords)
3. **specific** — horlicks, sos tiram, rempah kurma
4. **commodity** — garam, gula, bawang (last resort only)

Result across 748 recipes:

| Tier | Recipes |
|---|---|
| specific | 354 |
| equipment | 247 |
| appliance | 134 |
| commodity | **12 (1.6%)** |
| no ad | 1 |

Commodity went from what would have been ~66% of pages down to 1.6%.

**Two different sources are scanned:**
- ingredients → consumables
- steps + tips → equipment and appliances (a recipe says "panaskan kuali"
  but never lists kuali as an ingredient — counting from ingredients undercounts badly)

## Determinism

`pick_ad()` hashes `slug|slot`, so a recipe always shows the same ad.
Cacheable, and the card never swaps mid-scroll. R1 and R2 are forced to differ
(5 recipes have only one candidate, so they repeat — unavoidable).

## Unit-homonym guard

`cawan` appears in "2 cawan tepung" as a **measurement**, not a product. Same for
`sudu`, `tin`, `botol`. Without the guard the engine advertised a measuring cup on
dozens of pages. The guard requires product context before a cup keyword can fire.

---

## Card design

Reference: Pixlpin ad gallery (Hyperice, "Meet"). What was actually usable —
two of the four images were Premiere Pro screenshots, not ad creatives.

**Taken from the reference:** one focal mark, generous negative space, restrained palette.

**Added back (deliberately):** the commercial payload — product name, one benefit
line, a soft action cue, and a **Ditaja** chip. Brand-awareness ads carry none of
these because they are paid per impression. An affiliate card paid per click needs
all of them inside two seconds.

### Three layouts

| Layout | Used in | Size |
|---|---|---|
| `.ad-card` vertical | R1, R2 (article) | 300×250 mobile / 336×280 desktop |
| `.ad-bar` horizontal | K1, K3, S1 | 320×100 mobile / 728×90 desktop |
| `.ad-grid` card | K2 (kategori grid) | native 268px, matches `minmax(268px,1fr)` |

### Soft CTA variants

Per your request — no hard sell anywhere in the system.

| # | CTA | Tone |
|---|---|---|
| A | Kalau nak tengok pilihan | conditional |
| B | Ada yang macam ni | pointing |
| C | Boleh tengok di sini | permission |
| D | Yang biasa digunakan | social proof |
| E | *(none)* | pure information |

No exclamation marks, no "BELI SEKARANG", no urgency or stock-pressure language
anywhere in the 108 copy entries.

### Ditaja

Every card carries a `DITAJA` chip — warm chip, dark text (`#6E5548` on `#F1E4D8`),
weight 800. This is not stylistic: Malaysia's Consumer Protection (Electronic Trade
Transactions) Regulations 2012 require disclosure of commercial intent, and an
affiliate ad that reads as editorial is an offence, not just a policy breach.

---

## Accessibility / correctness

- `rel="sponsored nofollow noopener"` on every link
- `target="_blank"` with `noopener` (no reverse tabnabbing)
- SVG has `role="img"` + `aria-label`
- Icon block fixed at 92×92 so cards align regardless of illustration shape
- CSS `min-height:120px` reserves space → **zero CLS**

---

## Known gaps — read before Stage 3

1. **Copy and art are now 100% complete.** 130 keywords, 141 copy entries,
   142 illustrations. Zero placeholder slots across all 1,496 ad slots.

2. **Some icons still share a base form** — the 13 sauce bottles share a bottle
   outline, the 3 noodles share a nest, the 4 herbs share a sprig. This is
   correct at category level; they differ by colour and label motif. Every card
   prints the product name, so identification never depends on the icon alone.

3. **Contrast rule learned the hard way:** pale fills (`#FDF6F0`, cream) vanish on
   the cream card background. Every light-bodied container now carries a
   `stroke="#A34A2C" stroke-opacity=".4"` outline. New icons must follow this.

4. **No Shopee links yet** — `href="#"`. Deliberate: you're supplying these.
   Gate #27 must fail the build while any card still has `href="#"`.

5. **Not wired into `build_static.py`** — nothing is on the live site. Stage 3.

6. **2 slots get no ad** (`resepi-aiskrim-goreng-viral`-type items with only one
   candidate). Correct behaviour; leave it.

---

## Stage 2 / 3, when you're ready

**Stage 2** — fill the 24 missing copy entries, strengthen the weak illustrations.

**Stage 3** — wire into `build_static.py`:
- R1 after `.recipe-intro`, R2 after step 3 inside `.recipe-cols`
- K1 under H1, K2 after 4th card in `.grid`, S1 below results
- CSS: `.ad-slot{min-height:250px}` + desktop overrides
- Gates **#23–#27**:
  - #23 every page type has its planned slot count
  - #24 every slot has reserved min-height
  - #25 no `.ad-slot` above `<h1>`
  - #26 no `.ad-slot` inside `.recipe-cols` ingredients column
  - #27 build fails if any ad `href` is still `#`
