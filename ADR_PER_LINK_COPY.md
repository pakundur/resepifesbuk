# Per-link copy system (ADR v2)

Date: 2026-11-14
Supersedes: the single-copy-per-product model in `ads_wired.py` / `ad_render_wired.py`

## Decision

Every one of the **48 affiliate links** (16 products × 3 links) carries its **own**
copy block: its own hook, promise and button. Three links inside one card attack
three different kitchen problems instead of repeating one headline.

## Why

The previous build attached one copy pair per *product* and put all three links
under it. Links 2 and 3 had no individual reason to be clicked — they existed to
carry links, not to earn clicks. Giving each link its own problem statement and
its own button means every link can be promoted on its own merit.

## Files

| File | Role |
|---|---|
| `ad_copy_per_link.py` | The 48 copy blocks as data + `audit()`. Every block carries a `src` field naming its corpus evidence, or `BENEFIT` when the corpus has no failure language. |
| `ads_wired2.py` | Engine. Trigger scan, specificity ordering, one-ad-per-page guard, per-row link rotation. |
| `ad_render2.py` | Three variants: `three` (Tiga Pintu), `compact` (Padat), `bar`. Emits inline CSS. |
| `verify_ads.py` | Gates 23–31. Exit 1 on failure. |
| `PLAN_PER_LINK_COPY.md` | The approved plan, including the 48 blocks and corpus evidence table. |
| `mock_render.py` | Raster mock (PIL) — no browser on device. Renders real SVG art. |
| `make_4sheet.py` | 4-product comparison sheet. |

## Card anatomy (Varian Tiga Pintu)

```
[Ditaja]                          <- mandatory disclosure chip
[icon] SHOPEE MALAYSIA
       Kuali leper
────────────────────────────────
(1) Tumis bawang, hangit dulu sebelum naik bau
    Haba sekata, tumisan naik bau tanpa hangus
    [Tengok kuali →]
────────────────────────────────
(2) Telur melekat, susah nak angkat
    Lapisan tak lekat, telur gerak sendiri
    [Tak lekat →]
────────────────────────────────
(3) Daging kering masa tumis
    Haba rata kekalkan jus, daging tak kering
    [Haba rata →]
────────────────────────────────
Pautan rakan kongsi. Harga dan stok boleh berubah.
```

Each row is an `<a rel="sponsored nofollow noopener" target="_blank" data-aff="N">`.

## Rotation

Row order rotates per recipe by `sha256(slug|slot|rot) % 3`, so aff1 is not
always row 1. Measured: **183 / 154 / 182** across the three links. Stable per
recipe, so pages remain cacheable.

## One ad per page

303 recipes (40.5%) trigger exactly **one** wired product. On those pages only
the first slot renders; the rest are suppressed. Two ads for the same product on
one page reads as spam. 229 recipes (30.6%) trigger nothing and show no ad.

## Copy rules enforced by gates

- No exclamation marks anywhere.
- No hard-sell: `beli sekarang`, `termurah`, `terbaik`, `diskaun`, `%`, urgency.
- Every hook traceable to corpus failure language, or flagged `BENEFIT`.
- No duplicate hook within a product, or across products.
- All three links present, distinct, sponsored, on every card.
- DITAJA chip + disclosure note on every card.

## Corpus evidence (why these hooks exist)

Failure-language frequency inside recipes mentioning each product:

- kuali: hangit 18, melekat 16, kering 12
- periuk: hangit 24, berketul 19
- oven: hangit 18, keras 3
- loyang: melekat 8, hancur 5
- kukus: kering 4, hancur 3
- mixer: berketul 6, keras 6, tak-kembang 3
- blender: pecah 71, kering 57, mentah 43
- acuan: melekat 11
- grillpan: hangit 4, melekat 2
- freezer: keras 6
- microwave: hangit, keras
- pressure: hancur 1
- waffle: melekat, pecah
- takoyaki: melekat
- pengisar: hancur 3, berketul 2
- **ricecooker: 0** → benefit-angle copy only, no failure claim

## Illustration rules learned

- **Never** place an isolated light dot on a dark body — reads as an eye, makes a face.
- Rim/cavity areas need a LIGHT fill; a dark ellipse over a dark body reads as a hole.
- Two products sharing one builder will be indistinguishable (`_tray` was used for
  both loyang and acuan; `_blender` for both blender and pengisar; `_pot` for both
  periuk and pressure cooker). Each wired product needs a dedicated builder.
- Bar variant must stack the button below the text under 420px — side-by-side
  overlaps at 320px.

## Status

Stage 3 (copy + variants + gates) **complete**: 9/9 ad gates pass, 802 cards
rendered, 48/48 links in use.
**Not yet wired into `build_static.py`** — nothing is live.
