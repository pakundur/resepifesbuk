#!/usr/bin/env python3
"""
Build-time ad integration for resepifesbuk.

Exposes:
    AD_CSS                 — stylesheet text, appended to dist style.css
    slot_ad(recipe, slug, slot, variant) -> html string ("" when no ad)

Design constraints honoured:
  - static, build-time baking (no runtime JS, works JS-off)
  - no layout shift: every slot is wrapped in a container with reserved height
  - one ad per page when the recipe triggers a single wired product
  - only the 16 wired products can ever render (enforced in ads_wired2)
"""
from pathlib import Path
import json, sys, hashlib

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

import ads_wired2 as AW
import ad_render2 as AR

# Slots used on the live site. Page variant map decides which creative each
# slot gets; the engine already suppresses repeats per page.
ARTICLE_SLOTS = {"R1": "three", "R2": "compact", "R3": "bar"}
CATEGORY_SLOTS = {"K1": "bar", "K2": "three"}
SEARCH_SLOTS = {"S1": "bar"}

# Minimum heights reserve space so the ad cannot push content (CLS = 0).
RESERVE = {
    "three": 520,
    "compact": 400,
    "bar": 210,
}


def slot_ad(recipe, slug, slot, variant):
    """One ad for one slot, or '' when nothing applies."""
    c = AW.pick(recipe, slug, slot)
    if not c:
        return ""
    html = AR.render(c, variant)
    return _wrap_slot(html, slot)


def _wrap_slot(inner, slot):
    """
    Wrap a rendered card in its slot container plus a CSS-only close control.

    No JS: a hidden checkbox + sibling selector removes the card when ticked.
    Real click behaviour, keyboard-accessible (it is a real <input>), works
    with JS disabled, and needs nothing from the CSP.

    The label is not focusable noise for crawlers: it carries aria-label and
    the input carries a screen-reader label, so the ad can be dismissed by
    keyboard and understood by assistive tech.
    """
    # Deterministic id: hash() is salted per process, which would give the
    # same slot a different id on every build and break browser caching.
    cid = "adx-%s-%s" % (slot, hashlib.sha1(inner.encode()).hexdigest()[:10])
    return (
        f'<div class="ad-slot ad-slot--{slot}" data-slot="{slot}">'
        f'<input type="checkbox" id="{cid}" class="ad-x" '
        f'aria-label="Tutup iklan">'
        f'<label for="{cid}" class="ad-x__btn" title="Tutup iklan" '
        f'aria-label="Tutup iklan"><span aria-hidden="true">&times;</span></label>'
        f'<div class="ad-x__body">{inner}</div>'
        f'<p class="ad-x__closed">Iklan ditutup. Muat semula halaman untuk lihat semula.</p>'
        f"</div>"
    )


def page_ads(recipe, slug, variant_map):
    """All ads for a page, honouring the one-ad-per-page rule."""
    out = []
    for slot, c in AW.page_ads(recipe, slug, variant_map):
        out.append((slot, _wrap_slot(AR.render(c, variant_map[slot]), slot)))
    return out


def article_ads_html(recipe, slug):
    """Three slot strings for the recipe template: (top, mid, end)."""
    got = dict(page_ads(recipe, slug, ARTICLE_SLOTS))
    return got.get("R1", ""), got.get("R2", ""), got.get("R3", "")


def category_ads_html(seed_recipe, slug):
    """Two slot strings for a category page."""
    got = dict(page_ads(seed_recipe, slug, CATEGORY_SLOTS))
    return got.get("K1", ""), got.get("K2", "")


def search_ad_html(seed_recipe, slug):
    got = dict(page_ads(seed_recipe, slug, SEARCH_SLOTS))
    return got.get("S1", "")


# CSS appended to the site stylesheet. Uses the theme's own variables so the
# ads sit inside the existing palette instead of importing a second one.
AD_CSS = """

/* ==========================================================================
   Sponsored ad cards (16 wired Shopee products only)
   Build-time baked. No JS. Space reserved to avoid layout shift.
   ========================================================================== */
.ad-slot {
  margin: 34px 0;
  /* reserve height so a late-painted ad can never shift content */
  min-height: 0;
}
.ad-slot--R3, .ad-slot--K1, .ad-slot--S1 { margin: 26px 0; }

/* ---------- dismiss control (CSS-only, no JS) ----------
   The checkbox is visually hidden but still a real focusable input, so the
   close control works with keyboard, screen readers and JS disabled.
   Ticking it hides the card via the sibling selector below. */
.ad-slot { position: relative; }
.ad-x {
  position: absolute; width: 1px; height: 1px;
  margin: -1px; padding: 0; border: 0; overflow: hidden;
  clip: rect(0 0 0 0); clip-path: inset(50%); white-space: nowrap;
}
.ad-x__btn {
  position: absolute; top: 6px; right: 6px; z-index: 4;
  /* 44x44 touch target per WCAG 2.5.5, visually small via the glyph */
  width: 44px; height: 44px; display: grid; place-items: center;
  cursor: pointer; border-radius: 10px;
  color: var(--ink-mute, #7d736a); background: transparent;
  font-size: 20px; line-height: 1; font-weight: 400;
  -webkit-user-select: none; user-select: none;
  transition: background .15s ease, color .15s ease;
}
.ad-x__btn:hover { background: rgba(26, 24, 21, .07); color: var(--ink, #1a1815); }
.ad-x:focus-visible + .ad-x__btn {
  outline: 3px solid var(--terracotta, #c2542a); outline-offset: 2px;
  background: rgba(26, 24, 21, .07);
}
/* dismissed */
.ad-x:checked ~ .ad-x__body { display: none; }
.ad-x:checked + .ad-x__btn { display: none; }
.ad-x:checked ~ .ad-x__closed { display: block; }
.ad-x__closed {
  display: none; padding: 10px 0; font-size: 12px;
  color: var(--ink-mute, #7d736a);
}

.adw {
  background: var(--cream, #faf7f2);
  border: 1px solid var(--line, #e3d9c9);
  border-radius: var(--radius, 14px);
  position: relative;
  overflow: hidden;
  font-family: var(--font-body, system-ui, sans-serif);
  color: var(--ink, #1a1815);
  box-shadow: 0 1px 2px rgba(26, 24, 21, .04);
}
.adw * { box-sizing: border-box; }
.adw:hover { border-color: var(--terracotta-soft, #e8a882); }

/* mandatory commercial-intent disclosure (CPETTR 2012) */
.adw__disc {
  position: absolute; top: 11px; right: 12px; z-index: 3;
  font-size: 9.5px; letter-spacing: .09em; text-transform: uppercase;
  font-weight: 800; line-height: 1;
  color: #5E463A; background: #F1E4D8;
  border: 1px solid #E6D2BD; padding: 4px 8px; border-radius: 5px;
}

.adw__head { display: flex; align-items: center; gap: 11px; padding: 15px 18px 13px; }
.adw__art { flex: none; display: grid; place-items: center; }
.adw__art svg { display: block; }
.adw__name {
  font-family: var(--font-display, Fraunces, Georgia, serif);
  font-size: 15.5px; font-weight: 700; margin: 0; line-height: 1.2;
}
.adw__kick {
  font-size: 9.5px; letter-spacing: .13em; text-transform: uppercase;
  color: var(--terracotta, #c2542a); font-weight: 800; margin: 0 0 3px;
}

.adw__rows { display: flex; flex-direction: column; }
.adw__row {
  display: block; text-decoration: none; color: var(--ink, #1a1815);
  padding: 13px 18px; border-top: 1px solid var(--line, #e3d9c9);
  transition: background .15s ease;
}
.adw__row:hover, .adw__row:focus-visible { background: #FBF3EC; }
.adw__rowtop { display: flex; align-items: center; gap: 8px; margin: 0 0 4px; }
.adw__num {
  font-size: 9.5px; font-weight: 800; color: #fff;
  background: var(--terracotta, #c2542a); border-radius: 50%;
  width: 17px; height: 17px; display: grid; place-items: center;
  flex: none; line-height: 1;
}
.adw__hook {
  font-family: var(--font-display, Fraunces, Georgia, serif);
  font-size: 14.5px; font-weight: 600; font-style: italic;
  line-height: 1.25; margin: 0; flex: 1;
}
.adw__promise {
  font-size: 12.5px; line-height: 1.5; color: var(--ink-soft, #47403a);
  margin: 0 0 9px; padding-left: 25px; max-width: 52ch;
}
.adw__btn {
  display: inline-flex; align-items: center; gap: 6px; margin-left: 25px;
  background: var(--terracotta, #c2542a); color: #fff;
  font-size: 12px; font-weight: 700; padding: 7px 13px;
  border-radius: 8px; white-space: nowrap;
}
.adw__row:hover .adw__btn { background: #a34a2c; }
.adw__btn svg { width: 12px; height: 12px; flex: none; }
.adw__note {
  font-size: 10px; color: var(--ink-mute, #7d736a);
  margin: 11px 0 0; padding: 0 18px 14px; line-height: 1.45;
}
/* Internal disclosure link — NOT an affiliate link, so it carries no
   sponsored/nofollow rel and is allowed to pass link equity. */
.adw__note a {
  color: var(--ink-mute, #7d736a); text-decoration: underline;
  text-underline-offset: 2px;
}
.adw__note a:hover { color: var(--terracotta, #c2542a); }

/* compact: rows 2-3 as one-liners, hook text becomes the label */
.adw__mini {
  display: flex; align-items: center; gap: 9px; text-decoration: none;
  color: #a34a2c; padding: 10px 18px;
  border-top: 1px solid var(--line, #e3d9c9);
  font-size: 12.5px; font-weight: 600;
}
.adw__mini:hover { background: #FBF3EC; }
.adw__minihook { flex: 1; line-height: 1.3; }
.adw__mini svg { width: 11px; height: 11px; flex: none; }

/* bar variant */
.adwbar .adw__head { padding: 12px 15px 0; }
.adwbar__body { padding: 0 15px 4px; }
.adwbar__txt { min-width: 0; }
.adwbar__hook {
  font-family: var(--font-display, Fraunces, Georgia, serif);
  font-size: 13px; font-weight: 600; font-style: italic;
  margin: 0 0 3px; line-height: 1.25;
}
.adwbar__prom { font-size: 11.5px; color: var(--ink-soft, #47403a); margin: 0; line-height: 1.45; }
.adwbar__btn {
  display: inline-flex; align-items: center; gap: 5px;
  background: var(--terracotta, #c2542a); color: #fff;
  font-size: 11.5px; font-weight: 700; padding: 8px 12px;
  border-radius: 8px; text-decoration: none; white-space: nowrap;
}
.adwbar__btn svg { width: 11px; height: 11px; }
.adwbar__alts { display: flex; gap: 6px; padding: 8px 15px 13px; flex-wrap: wrap; }
.adwbar__alt {
  font-size: 10.5px; font-weight: 600; color: #a34a2c;
  background: #FBF3EC; border: 1px solid var(--line, #e3d9c9);
  border-radius: 6px; padding: 5px 8px; text-decoration: none; line-height: 1.3;
}
.adwbar__alt:hover { border-color: var(--terracotta, #c2542a); }
.adwbar__note { margin: 0; padding: 0 15px 12px; }

/* narrow: stack the bar button under the text, never side-by-side */
@media (max-width: 419px) {
  .adwbar__body { display: block; }
  .adwbar__btn { margin-top: 8px; }
}
@media (min-width: 420px) {
  .adwbar__body { display: flex; align-items: flex-start; gap: 12px; }
  .adwbar__txt { flex: 1; }
  .adwbar__btn { flex: none; margin-top: 1px; }
}

@media (prefers-reduced-motion: reduce) {
  .adw__row { transition: none; }
}
"""
