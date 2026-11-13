# Ad Placement Plan — resepifesbuk.com

Prepared for Md Saiful Azri · 2026-11-13
Site: https://resepifesbuk.com · 805 pages · 748 recipes · 21 categories

---

## 0. Read this first — the popup requirement conflicts with policy

You asked for **1 popup ad every 1 minute**. I have to flag this before anything else,
because it is the one item in your request that can get the site penalised rather than monetised.

**AdSense Program Policy — Ad placement policies (support.google.com/adsense/answer/1346295):**

> "Publishers are not permitted to place Google ads on sites which have **more than three
> pop-ups**. If pop-ups are displayed on a site, they may not **interfere with site navigation**,
> change user preferences, initiate downloads, or distribute viruses."

**AdSense Program policies — Site behavior:**

> "Sites may not change user preferences, redirect users to unwanted websites, initiate downloads,
> include malware or contain **pop-ups or pop-unders that interfere with site navigation**."

### What "1 popup per minute" actually produces

A user who stays 5 minutes on your recipe site would receive **5 full-screen popups**.
That is already over the 3-popup ceiling — and it is per *session*, so the fourth one is
the policy breach that risks account suspension, not a warning.

The practical outcome on a Malaysian mobile connection:

- A 20-minute browse → **20 popups**
- Every one of them a Google ad served from a site that violates placement policy
- Your AdSense account is the asset at risk, and it is **one strike, whole-account**
  (per the AdSense closure policy, not per-page)

### The legitimate version of what you're asking for

You almost certainly want **the revenue effect** of popups, not the mechanics. There are three
compliant ways to get it, ranked by how well they convert:

| Approach | Format | Frequency | Policy status | Realistic RPM effect |
|---|---|---|---|---|
| **A. AdSense Vignette** (recommended) | Full-screen interstitial, Google native | Cap **1 per 10 min** (GAM default, was lowered from 60 min in Nov 2024) | Fully compliant — Google's own format | Highest single-format lift |
| **B. Scroll-triggered in-content interstitial** | Your own overlay, 1 per session | **1 per session, 5s minimum dwell**, dismissible | Compliant if ≤3/session and doesn't block nav | Moderate but safe |
| **C. Anchor (sticky bottom) ad** | Google native, 320×50 | Persistent | Compliant, explicitly supported | Steady RPM, low annoyance |

**My recommendation: use A, not a hand-rolled popup timer.** Vignette is Google's own interstitial,
it is served through Auto ads, it respects Google's frequency governance automatically, and
**it cannot be the thing that gets you suspended** — because Google itself is deciding when it fires.

Do **not** build a `setInterval(..., 60000)` popup. Beyond the policy issue, an ad rendered in a
`setInterval` popup is a **"floating box script"**, which is explicitly named in the AdSense
prohibited list:

> "Place ads in a floating box script." — AdSense Program policies

### The one thing that would make even Vignette unsafe

Google's **spam policy on intrusive interstitials**. If a popup covers content immediately after
a user arrives from Google Search, it can reduce ranking. Vignettes are designed to fire
**between page loads**, not on arrival — so leave them at Google's default trigger. Do not add
on-load triggers to force them earlier.

**Deferred decision needed from you:** approve Vignette (A) as the popup mechanic. If you
insist on the 60-second timer anyway, I will not implement it on an AdSense-monetised site —
the risk is your whole account, and it is not recoverable.

---

## 1. Site anatomy — what we are placing into

Measured from the built HTML, not assumed.

### Homepage (`/`)
| Section | Height | Content |
|---|---|---|
| `.hero.sky-field` | ~70vh | H1, lede, search entry |
| Section 2 | — | 12 recipe cards (3 images `fetchpriority=high`) |
| Section 3 (`cream-deep`) | — | Category grid, 21 tiles |
| Footer | — | Links, attribution |

Total: 22.0 KB gzipped, 588 visible words, 12 images, 2 scripts.

### Category page (`/kategori/<slug>/`)
| Section | Content |
|---|---|
| Breadcrumb + H1 + intro | `Resepi <category>` |
| Card grid | N recipe cards |
| Pagination | `/halaman/N/` |

Total: ~10 KB, 0 images above fold (cards lazy-load), 1 script.

### Search page (`/cari/`)
Standalone template, 6.5 KB, **no ads planned here** — see § 5.

### Recipe page (`/resepi/<slug>/`)
| Section | Class | Content |
|---|---|---|
| Hero | `.recipe-head` | H1, facts strip, hero image |
| Intro | `.recipe-intro` | 1 paragraph |
| Share bar | `.share-bar` | 4 anchor buttons |
| Ingredients | `.recipe-cols` left | `<ul>` list |
| Steps | `.recipe-cols` right | `<ol>`, ~5–7 steps |
| Tips | `.tips-box` | `<ul>` |
| Source note | `.source-note` | 1 paragraph |
| Related | `.related-block` | 4 links |

479 visible words. **This is your highest-value page type** — it is where purchase intent lives
(you already have the Shopee keyword data showing 772 product-recipe pairs).

---

## 2. Page-by-page placement plan

Rule applied everywhere: **no ad above the H1**, **no ad inside the ingredients list or the
first 2 steps**, and **nothing that shifts layout** (CLS is already a risk — see § 6).

### 2.1 Homepage

| # | Slot | Position | Format | Size | Why |
|---|---|---|---|---|---|
| H1 | After hero, before card grid | Below the fold boundary | Responsive display | 336×280 mobile / 728×90 desktop | First content scroll; user has seen the H1 and the purpose |
| H2 | Between card grid and category grid | Mid-page | In-feed (native) | Matches card width | Looks like another recipe card — highest CTR placement on a listing page |
| H3 | Above footer | Bottom | Responsive display | 336×280 / 970×250 | Exit-intent zone, zero CLS impact |

**Do not** put an ad inside the hero. It would break the design and be the first thing a
search visitor sees (intrusive-interstitial risk).

### 2.2 Category page

| # | Slot | Position | Format | Why |
|---|---|---|---|---|
| K1 | After H1 + intro, before card grid | Top of listing | Responsive display | Reachable, but content intent already established |
| K2 | Injected after the **4th card** in the grid | In-feed | In-feed native | Genuinely native — a grid of cards is the one place an in-feed unit is invisible |
| K3 | After pagination | Bottom | Responsive display | Cheap impression, no layout cost |

On paginated pages (`/halaman/N/`), keep the **same** K1/K2/K3 slots so ad density per
pageview is constant. Do not add extra units on deep pagination — that is the classic
"ad-heavy thin page" pattern.

### 2.3 Recipe page — the money page

| # | Slot | Position | Format | Why |
|---|---|---|---|---|
| R1 | After `.recipe-intro`, **before** `.recipe-cols` | Just above ingredients | Responsive display | User has decided to cook; ad is contextually adjacent to ingredients |
| R2 | **Inside** the steps column, after step 3 | In-content | In-article native | Highest-value slot on the site. Reader is mid-recipe, dwell time is long |
| R3 | Between `.tips-box` and `.source-note` | Near end | Responsive display | Reader finished; no content is being obstructed |
| R4 | Inside `.related-block`, after the 2nd related link | In-feed | In-feed native | Cross-sell; low value but free |

**R2 is the single most important slot on the entire site.** It sits at the moment of maximum
attention. Combined with the Shopee affiliate link on the same page, you get an ad impression
*and* an affiliate click from the same session.

**Never** place an ad between the ingredient list and the steps — that is exactly where a cook
looks back and forth. Breaking that flow is what makes recipe sites feel hostile.

### 2.4 Search page (`/cari/`)

**No ads.** Reasons:
1. Zero content — AdSense explicitly forbids ads on "non-content-based pages"
2. It is `noindex`-classified and low traffic (2 pageviews in the analytics sample)
3. The page is a client-side search UI; injecting ads into a results re-render causes layout jank

If search ever gets real traffic, revisit with a single unit below the results.

---

## 3. Density budget

Derived from page word count. Industry guidance is roughly **1 ad unit per 150–200 words**
of substantive content, capped by user experience.

| Page type | Words | Max units | Planned | Density | Verdict |
|---|---|---|---|---|---|
| Homepage | 588 | 3 | 3 | 1 : 196 | At cap — hold |
| Category | 161 | 1 (formula would say 1) | 3 | 1 : 54 | **Over formula, justified** — it is a listing, not prose; card grids carry the density |
| Recipe | 479 | 3 | 4 | 1 : 120 | Slightly over — R4 is low-impact, monitor |
| Search | — | 0 | 0 | — | Correct |

If Search Console later shows a mobile UX or ranking dip, **remove R4 first**, then H3.
Those are the two least-valuable units on the site.

---

## 4. Implementation — technical requirements

These are non-negotiable given the current configuration.

### 4.1 CSP must be updated or the ads will not render

Current `_headers` CSP:

```
script-src 'self' 'unsafe-inline' https://static.cloudflareinsights.com https://www.googletagmanager.com
```

AdSense needs **all** of these added:

```
script-src  ... https://pagead2.googlesyndication.com https://tpc.googlesyndication.com
            https://fundingchoicesmessages.google.com
connect-src ... https://pagead2.googlesyndication.com https://googleads.g.doubleclick.net
            https://*.doubleclick.net
img-src     ... https://pagead2.googlesyndication.com https://*.g.doubleclick.net
            data:
frame-src   https://googleads.g.doubleclick.net https://tpc.googlesyndication.com
            https://www.google.com
```

**A missing `frame-src` is the #1 cause of "ad slot renders blank"** on a CSP-hardened site.
Your CSP is currently strict — this is a real risk, not a theoretical one.

### 4.2 CLS prevention — reserve space

Every slot must have a **fixed min-height** in CSS *before* the ad loads:

```css
.ad-slot { min-height: 280px; }          /* mobile */
@media (min-width: 768px) { .ad-slot { min-height: 90px; } }
```

Without this, every ad unit injects layout shift and your Lighthouse CLS (already unmeasured
because I could not run Lighthouse) degrades further. Given you already have 745 KB of
unoptimised images in the LCP path, do not add CLS on top.

### 4.3 Build-time injection, not runtime

Your site is static, generated by `build_static.py`. Ad slots should be **emitted by the
generator** in the `head()` / template functions — not injected by a JS library. Reasons:

- Static markup means the slot exists in the HTML (no JS-dependent layout)
- You keep full control of placement per page type
- No Auto-ads "helpfully" relocating units into your ingredients list

**Use Auto ads OFF; use manual ad units.** Auto ads on a recipe site will place a unit inside
the ingredients table and inside the steps list, which is precisely what §2 forbids.

### 4.4 New build gates

Add to `verify_all.py` so a broken ad config can never deploy:

| Gate | Assertion |
|---|---|
| #23 | Every page type contains its planned number of `.ad-slot` elements |
| #24 | Every `.ad-slot` has `min-height` set (grep the CSS) |
| #25 | CSP contains `googlesyndication.com` in `script-src`, `frame-src`, `img-src`, `connect-src` |
| #26 | No `.ad-slot` appears above the `<h1>` |
| #27 | No `.ad-slot` appears inside `.recipe-cols` |

Gate #26 and #27 are the ones that stop a well-meaning future edit from wrecking the UX.

---

## 5. Rollout order

Do not do all four page types at once. Each stage is a measurement point.

| Stage | Scope | Units | Wait | Decide on |
|---|---|---|---|---|
| **1** | Recipe pages only (R1 + R2) | 2 | 14 days | RPM, bounce rate, GA4 engagement |
| **2** | + R3, R4 | 4 | 14 days | Does recipe bounce rate move? |
| **3** | Category pages (K1–K3) | 3 | 14 days | Listing RPM vs recipe RPM |
| **4** | Homepage (H1–H3) + Vignette on | 3 | 14 days | Vignette frequency vs session duration |

**Recipe pages first** because: highest traffic, highest intent, and the R2 slot is where you
learn whether in-article native works on your audience before committing to it site-wide.

**Vignette last** (Stage 4) because it has the largest single effect on user experience. If
session duration drops hard at Stage 4, you can turn it off and keep everything else.

---

## 6. Measurement — what to watch

You already have both analytics stacks live (Cloudflare Web Analytics + GA4 `G-HBY3W85QCB`).

| Metric | Source | Threshold to act |
|---|---|---|
| Session duration | GA4 | −25% vs baseline → cut a unit |
| Bounce rate | GA4 | +10pp → cut R4/H3 first |
| Pages/session | GA4 | −20% → check Vignette frequency |
| RPM by page type | AdSense | Compare recipe vs category |
| CLS (field) | Cloudflare Web Analytics | >0.1 → fix reserved space |

**Establish a 7-day pre-ad baseline starting today.** You currently have 23 real pageviews
recorded — that is far too small a sample to detect anything. Either wait for traffic to grow,
or add the units and measure against month-over-month rather than day-over-day.

---

## 7. Honest risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AdSense rejects the site (insufficient original content) | **Medium** | Blocks all revenue | Your recipes are rewritten, not scraped — but 748 auto-LLM-generated pages **will** be scrutinised under the "little or no original content" policy |
| Popup timer causes suspension | **High if implemented as asked** | Total account loss | Use Vignette, not a timer |
| CSP blocks ads → blank slots | **High** | Silent zero revenue | Gate #25 |
| CLS from unreserved slots | High | Ranking + UX | §4.2 |
| Ads depress CWV on a site with 745 KB LCP images | Medium | Compounding | Fix images first (previous report) |
| Auto ads relocate units into ingredient lists | Medium | UX damage | Keep Auto ads off |

### The uncomfortable one

AdSense approval is **not guaranteed**. Google's spam policy explicitly names
*"affiliate programs with little or no original content"* and *"doorway pages created just for
search engines."* You have 748 pages that are machine-generated rewrites of Blogger posts.
That is defensible as **a curated, rewritten, structured recipe collection** — but it is also
exactly the profile a reviewer flags.

**Recommendation: apply for AdSense with 20–30 of your best recipe pages indexed and ranking,
not on day one.** Get Search Console indexing established first (you have not yet submitted
the sitemap). Approval on a site with real organic traffic and clean CWV is far more likely.

---

## 8. What I need from you

1. **Approve Vignette vs the 60-second timer** (§0) — this blocks Stage 4
2. **Confirm Shopee affiliate or AdSense first** — running both on the same page is allowed, but
   the recipe page gets crowded fast; you may want Shopee on recipe pages and AdSense on
   listing pages
3. **AdSense account status** — do you have one approved already, or is this a fresh application?
4. **Proceed order** — do you want me to build Stage 1 (recipe pages, R1+R2, CSP + gates) now?

---

*Sources: AdSense Program policies (updated 2026-08-04); AdSense Ad placement policies
(answer/1346295); GAM Interstitial default cap change 2024-11-04; AdSense vignette frequency
configurable 1min–1hr since Oct 2023; Google Search intrusive interstitial guidance.*
