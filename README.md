# Resepi Fesbuk — Design Demo

A design-forward demo for [resepifesbuk.com](https://www.resepifesbuk.com/), built on the
visual language of the [Trajectory AI landing page](https://pixlpin.com/d/trajectory-ai-continual-learning-landing-page)
by Mason Price.

**Live:** https://pakundur.github.io/resepifesbuk/

## What this is

A static React demo that re-skins a Malaysian recipe collection in Trajectory's design
language — warm cream palette, Fraunces serif display type, pastel sky gradients, an
expanding-grid hero with a CSS paper airplane, scroll-reveal cards, and a technical
flow diagram.

**All content is real.** 25 recipes scraped from the live resepifesbuk.com Blogger feed:
titles, categories, ingredients, cooking steps, tips, and images. Nothing is placeholder
text or invented copy.

## Design decisions

Inspired by — not copied from — the Trajectory landing page:

| Trajectory element | How it's reinterpreted here |
|---|---|
| Expanding grid hero | 16×9 cell grid that lights in a radial wave from centre |
| 3D paper airplane through pastel clouds | Pure-CSS 2.5D plane, scroll-parallaxed via `transform`, no WebGL |
| Serif display type | Fraunces variable, `SOFT 0 / WONK 1`, italic terracotta accents |
| Scrollytelling technical diagrams | Animated 4-node flow diagram synced to step selection |
| Interactive feature cards | Recipe cards → modal with ingredient checklist |

Deliberately **not** copied: Trajectory's brand, copy, logos, or layout structure. The
Typography and colour logic are the borrowed parts.

## Data pipeline

The site is driven by `src/recipes.json`, generated from Blogger's public JSON feed:

```
https://www.resepifesbuk.com/feeds/posts/default?alt=json&max-results=25
```

Extraction handled three heading variants in the wild (`Cara Penyediaan`, `Cara Membuat`,
`Cara Memasak`) and two ingredient-heading variants (`Bahan-Bahan`, `Keperluan Bahan-Bahan`).
Quantity detection covers integer, decimal, and vulgar-fraction forms (`1 kg`, `4 ½ cawan`,
`½ sudu besar`).

**Extracted:** 25 recipes · 210 ingredients · 103 steps · 25 images.

Images are hot-linked from `blogger.googleusercontent.com` at `/s800/`. No images are
redistributed in this repo.

## Stack

React 19 · Vite 8 · Tailwind CSS 4 · zero runtime dependencies beyond React.

No animation library — all motion is CSS transitions/keyframes plus one `requestAnimationFrame`
scroll handler. `prefers-reduced-motion` is respected throughout.

## Run locally

```bash
npm install
npm run dev      # http://localhost:5174
npm run build    # -> dist/
```

## Tests

Two headless jsdom suites run against the **built** bundle:

```bash
node smoke.mjs     # 15 checks — render, content markers, real data, images, filters
node interact.mjs  # 12 checks — modal open/close, ingredient toggle, scroll lock, filtering
```

Both pass 15/15 and 12/12 respectively.

## Deploy

GitHub Actions on push to `main` → builds → publishes to Pages.

`vite.config.js` sets `base: "/resepifesbuk/"` only when `GITHUB_ACTIONS=true`, so local
dev stays at `/` while Pages resolves assets correctly. Skipping this yields a blank white
page with a green build — the classic Pages failure mode.

## Attribution

All recipes, images, and written content © [Resepi Fesbuk](https://www.resepifesbuk.com/).
This is an unaffiliated design demo. Design direction inspired by Trajectory AI (Mason Price).
