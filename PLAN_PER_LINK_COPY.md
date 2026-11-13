# Plan: unique copywriting per affiliate link (48 distinct creatives)

Date: 2026-11-14
Status: **PLAN — awaiting approval before code**
Scope: the 16 wired products only, 3 links each = **48 links, 48 unique copy blocks**

---

## 1. The problem with the current build

Right now `ads_wired.build_creative()` attaches ONE copy pair (`head`, `sub`) per
**product**, then puts three links under it:

```
Oven yang boleh diharap          <- one headline
Suhu sekata, kek naik cantik.    <- one subline
[Lihat di Shopee]  [Pilihan 2]  [Pilihan 3]
```

Two consequences the user is right to object to:

1. **All 3 links share one message.** A shopper reading "Suhu sekata, kek naik
   cantik" has no reason to click link 2 or link 3 over link 1. The two alt links
   are dead weight — they exist to carry links, not to earn clicks.
2. **The copy is generic.** "Periuk untuk masak harian / Tahan panas, senang
   dijaga" describes a category, not a problem. Nothing in it makes someone who
   is *currently stuck* stop scrolling.

**Fix:** every one of the 48 links gets its own copy block — its own hook, its own
kitchen problem, its own reason to click. Same product page pool, 48 different
doors into it.

---

## 2. Copy architecture — what makes a link earn a click

Each copy block has four fields, all BM colloquial (per site voice: `dah`, `je`,
`kat`, `ni`, `tu`, `korang`→`anda`):

| Field | Job | Limit | Example |
|---|---|---|---|
| `hook` | The kitchen failure, named plainly | 3–7 words | "Kuali je hangit bawah" |
| `promise` | What changes with this product | 8–14 words | "Haba sekata, tumis bawang tak hangus lagi" |
| `btn` | The click label (soft-sell) | 2–4 words | "Tengok kuali ni" |
| `note` | Optional micro-trust line | ≤10 words | "Pilihan ramai untuk dapur kecil" |

**Angle rule:** the three links for one product must attack three *different*
problems — not three rewrites of the same one. If oven link 1 is about uneven
heat, link 2 must be about something else (rack space, crust), link 3 about
something else again (baking without fear of burning).

**Failure-mode sourcing rule:** every problem must be traceable to language that
actually appears in our own 748 recipes. I mined the corpus; the evidence is in
§3. No invented pain, no invented claims.

**Banned:** exclamation marks, "Beli Sekarang", countdown/urgency, price claims,
discount numbers, superlatives ("terbaik", "termurah"), any health claim.

---

## 3. Real pain points found in our corpus (evidence)

Frequency of failure language inside the recipes that mention each product:

- **kuali** — hangit 18, melekat 16, kering 12 → *fish: "paru tidak hangus di bahagian bawah kuali"*
- **periuk** — hangit 24, berketul 19 → *fish: "bubur tidak hangus di dasar periuk", "sagu tidak berketul"*
- **oven** — hangit 18, keras 3 → *fish: "bergantung kepada oven masing-masing"* (temperature unreliability)
- **loyang** — melekat 8, hancur 5 → *fish: "loyang yang telah digris dan dilapik baking paper"*
- **kukus** — kering 4, hancur 3, tak-seimbang → *fish: "air menitis"*
- **mixer** — berketul 6, keras 6, tak-kembang 3 → *fish: "pukul telur dan gula hingga kembang"*
- **blender** — pecah 71, kering 57, mentah 43 → *fish: "cili kisar... elak cili hangus"*
- **acuan** — melekat 11 → *fish: "supaya bahulu mudah dikeluarkan dan tidak melekat"*
- **grillpan** — hangit 4, melekat 2 → *fish: "jaga supaya tidak hangus menjadi hitam seperti arang"*
- **freezer** — keras 6 → *fish: "teksturnya kemas dan tidak cair"*
- **microwave** — hangit, keras → *fish: "supaya coklat tidak hangus atau pecah minyak"*
- **pressure** — hancur 1 (tulang) → *fish: "tulangnya hancur"*
- **waffle** — melekat, pecah → *fish: "biarkan sekurang-kurangnya 5 minit supaya waffle tidak melekat"*
- **takoyaki** — melekat → *fish: "supaya takoyaki tidak melekat dan mudah digolek"*
- **pengisar** — hancur 3, berketul 2 → *fish: "serat labu hancur sepenuhnya"*
- **ricecooker** — 0 pain sentences in corpus → **no product-pain copy available; must use benefit angle, not failure angle** (honest constraint)

---

## 4. The 48 copy blocks

Format: `hook` → `promise` (btn)

### Oven elektrik (oven)
- **aff1** Uneven heat — "Kek naik senget sebelah" → "Suhu sekata atas bawah, tak payah pusing tray tengah jalan" (Tengok oven ni)
- **aff2** Spare space — "Satu tray je muat" → "Rak dua tingkat, biskut raya siap sekali jalan" (Oven dua rak)
- **aff3** Burn fear — "Takut hangit, buka oven tiap 5 minit" → "Pintu kaca luas, tengok warna kek tanpa buka pintu" (Tengok yang ni)

### Mixer kek (mixer)
- **aff1** Arm fatigue — "Pukul adunan sampai tangan lenguh" → "Adunan kembang dalam 3 minit, tangan tak penat lagi" (Tengok mixer)
- **aff2** Lumpy batter — "Adunan berketul, kek bantat" → "Pukul rata sampai bawah mangkuk, tak ada ketul tertinggal" (Cara pukul rata)
- **aff3** Over/under whipping — "Pukul lebih, adunan jatuh balik" → "Kelajuan boleh kawal, senang nak berhenti tepat pada masa" (Pilihan lain)

### Blender dapur (blender)
- **aff1** Chunky sambal — "Cili kisar tak lumat, sambal kasar" → "Cili kering lumat sekata, pecah minyak pun cepat" (Tengok blender)
- **aff2** Burnt paste — "Tumis cili, hangit dulu sebelum masak" → "Kisar halus sampai betul-betul lumat, tak hangus masa tumis" (Blender kuat)
- **aff3** Small kitchen — "Blender besar makan ruang" → "Saiz padan dapur kecil, simpan dalam kabinet pun senang" (Tengok saiz)

### Pengisar makanan (pengisar)
- **aff1** Coarse grind — "Rempah kisar tak halus, gigit biji" → "Kisar rempah kering sampai serbuk halus" (Tengok pengisar)
- **aff2** Fibrous ingredients — "Labu berdegil, kisar lama pun ada serat" → "Mata pisau tajam, serat hancur sepenuhnya" (Yang ni kuat)
- **aff3** Wet and dry in one — "Kena beli dua mesin" → "Kering dan basah guna satu bekas je" (Tengok dua guna)

### Rice cooker (ricecooker)
- **aff1** Rice burns at the bottom — "Nasi hangit di dasar" → "Masak, hangat, siap sendiri tanpa perlu tunggu" (Tengok rice cooker)
- **aff2** Timing — "Balik kerja, nasi belum masak" → "Set dan tinggal, nasi siap bila anda balik" (Ada timer)
- **aff3** Small household — "Masak banyak, nasi lebih, buang" → "Saiz kecil cukup untuk dua orang, tak membazir" (Tengok saiz)

### Grill pan (grillpan)
- **aff1** Sticking — "Ayam melekat, kulit tertinggal atas pan" → "Lapisan tak lekat, kulit ayam keluar cantik" (Tengok grill pan)
- **aff2** Charring — "Panggang jadi arang" → "Alur naikkan daging, lemak turun — tak hangus bawah" (Alur dalam)
- **aff3** Smoke in kitchen — "Panggang dalam rumah, asap penuh dapur" → "Alur tolong buang lemak, kurang asap berbanding kuali biasa" (Pilihan lain)

### Microwave oven (microwave)
- **aff1** Chocolate seizing — "Coklat hangus masa cair" → "Cair sekata, tak hangus atau pecah minyak" (Tengok microwave)
- **aff2** Reheating rubber chicken — "Panaskan ayam, jadi kenyal" → "Kuasa boleh laras, panaskan lembut tak kering" (Kuasa laras)
- **aff3** Defrost shortcut — "Lupa keluarkan daging dari freezer" → "Fungsi nyahbeku, masak pun boleh terus" (Tengok fungsi)

### Freezer kecil (freezer)
- **aff1** Stock overflow — "Peti sejuk penuh, stok tak muat" → "Ruang beku tambahan untuk stok mingguan" (Tengok freezer)
- **aff2** Daily market trips — "Hari-hari kena ke pasar" → "Simpan lauk sebulan, tak perlu keluar setiap hari" (Simpan stok)
- **aff3** Texture loss — "Beku, cair, tekstur rosak" → "Suhu stabil, tekstur kekal macam baru masak" (Suhu stabil)

### Waffle maker (waffle)
- **aff1** Sticking and tearing — "Waffle nempel, keluar pecah dua" → "Lapisan tak lekat, waffle keluar utuh" (Tengok waffle maker)
- **aff2** Soggy centre — "Rangup luar, lembut dalam jadi liat" → "Haba dua belah, masak sampai ke tengah" (Haba dua belah)
- **aff3** Special-occasion only — "Beli, guna sekali, simpan" → "Kecil dan ringan, senang simpan untuk hujung minggu" (Tengok saiz)

### Acuan takoyaki (takoyaki)
- **aff1** Sticking balls — "Bebola melekat, susah nak putar" → "Pan panas sekata, bebola golek bulat sendiri" (Tengok acuan)
- **aff2** Uneven shape — "Bentuk tak bulat, ada yang leper" → "Lubang sekata, semua bebola sama saiz" (Lubang sekata)

### Pressure cooker (pressure)
- **aff1** Tough meat — "Rendang 3 jam, daging masih keras" → "Daging lembut dalam masa lebih singkat" (Tengok pressure cooker)
- **aff2** Fish bones — "Tulang ikan sardin keras, susah makan" → "Tekanan cukup kuat sampai tulang hancur" (Yang ni kuat)

### Kuali leper (kuali)
- **aff1** Burning at the bottom — "Tumis bawang, hangit dulu sebelum naik bau" → "Haba sekata, tumisan naik bau tanpa hangus" (Tengok kuali)
- **aff2** Sticking — "Telur melekat, susah nak angkat" → "Lapisan tak lekat, telur gerak sendiri dalam kuali" (Tak lekat)
- **aff3** Dry stir-fry — "Daging kering masa tumis" → "Haba rata kekalkan jus, daging tak kering" (Haba rata)

### Periuk memasak (periuk)
- **aff1** Burnt base — "Bubur hangit di dasar periuk" → "Dasar tebal, haba rata sampai bubur tak hangit" (Tengok periuk)
- **aff2** Lumpy porridge — "Sagu berketul, bubur tak licin" → "Dasar rata, kacau pun senang, tak berketul" (Dasar rata)
- **aff3** Stained pot — "Periuk susah dicuci, ada kesan hangit" → "Lapisan dalam senang dibasuh, tak tinggal kesan" (Senang cuci)

### Loyang kek (loyang)
- **aff1** Sticking cake — "Kek melekat, keluar hancur" → "Lepas tanggal bersih, kek tak patah" (Tengok loyang)
- **aff2** Uneven bake — "Tepi masak, tengah mentah" → "Haba rata, kek masak sekata sampai tengah" (Haba rata)
- **aff3** Water bath setup — "Water bath, air masuk dalam loyang" → "Tahan air, sesuai untuk bakar cara water bath" (Tengok yang ni)

### Periuk kukus (kukus)
- **aff1** Water dripping — "Air menitis atas kuih" → "Tudung bentuk elak air menitis atas kuih" (Tengok pengukus)
- **aff2** Dry kuih — "Kuih kering, tak lembut" → "Wap sekata, kuih kekal lembut sampai sejuk" (Wap sekata)
- **aff3** Small batch — "Pengukus besar untuk kuih sikit" → "Saiz kecil, sesuai untuk buat sebahagian je" (Tengok saiz)

### Acuan kuih (acuan)
- **aff1** Sticking bahulu — "Bahulu melekat, susah nak keluar" → "Lepas tanggal senang, bentuk tak rosak" (Tengok acuan)
- **aff2** Cleaning — "Acuan susah dicuci, ada sisa hangit" → "Senang dibasuh antara kelompok" (Senang cuci)

---

## 5. How the three links appear in one card

The user wants all 3 links promoted. Three options, and my recommendation:

| Option | What the shopper sees | Verdict |
|---|---|---|
| 1. Three buttons, one headline | 3 buttons under 1 copy | ✗ rejected — same reason as today |
| 2. One primary + "2 pilihan lain" that expand | 1 headline, 2 links hidden behind a toggle | ✗ needs JS, hidden links rarely clicked |
| **3. Three titled rows, each with own copy** | 3 mini-ads stacked in one card | **✓ recommended** |

**Recommended card (Varian "Tiga Pintu"):**

```
┌─────────────────────────────────────────┐
│  Iklan · Ditaja                         │
│  [icon]  Kuali leper                    │
│  ─────────────────────────────────────  │
│  1  Kuali je hangit bawah               │
│     Haba sekata, tumis bawang tak       │
│     hangus lagi          Tengok kuali → │
│  ─────────────────────────────────────  │
│  2  Telur melekat, susah angkat         │
│     Lapisan tak lekat, telur gerak      │
│     sendiri dalam kuali                  │
│                        Tak lekat →      │
│  ─────────────────────────────────────  │
│  3  Daging kering masa tumis            │
│     Haba rata kekalkan jus, tak kering  │
│                        Haba rata →      │
│  ─────────────────────────────────────  │
│  Pautan rakan kongsi. Harga boleh ubah. │
└─────────────────────────────────────────┘
```

Each row = one link = one problem = one button. All three get equal visual
weight, so no link is structurally starved of clicks. The card is honest about
being an ad (single "Ditaja" chip at top applies to all three rows).

**Where each variant goes:**
- **R1 / K2** — the full three-row card (Varian "Tiga Pintu")
- **R2 / K3 / S1** — compact: row 1 expanded, rows 2–3 collapsed to one-line links with their own hook text (not "Pilihan 2" — the hook *is* the label)
- **K1** — narrow bar: one hook + one button, rotating which of the 3 shows (stable per slug)

---

## 6. Click-share fairness

With three links per card, if row 1 always reads best, rows 2–3 starve. Two fixes,
both free:

1. **Rotate row order per recipe** by stable slug hash (already proven: 183/154/182
   split across 3 links). Row 1 is a different link on different pages.
2. **Rotate which product gets the slot** (existing `pick()` logic) so product
   exposure stays balanced: kuali 1084, periuk 707, oven 506 … takoyaki 5.

Row-order rotation is new. It means link 1 ≠ always aff1, which is what the
current code does per-card but not per-row.

---

## 7. Honest constraints I must design around

| Constraint | Number | Design response |
|---|---|---|
| Recipes triggering **no** wired product | **229 / 748 (30.6%)** | No ad. Don't backfill with unrelated products — that would break "only this". |
| Recipes triggering **exactly 1** product | **303 (40.5%)** | R1 and R2 on the same page would show the *same product*. Fix: show only one ad per page when only 1 candidate, OR let R2 show a different *link* of the same product with different copy. **Recommended: one ad per page in that case** — two ads for one product looks spammy. |
| 3+ candidates | 67 recipes | Full two-slot behaviour, guaranteed different products. |
| ricecooker has **zero** pain language in corpus | 0 | Copy uses benefit angle only, no failure claim. Stated honestly. |
| takoyaki triggers on **5** impressions total | 5 | Keep wired (user supplied it), just accept it barely shows. |
| pressure triggers 7, waffle 7 | 7 each | Same — wired but low exposure. Not a bug, a corpus fact. |

**Implication for §5:** on the 303 single-candidate pages, the "3 rows" card shows
3 *different links of the same product*. That's acceptable and honest (it's the
same product family, 3 seller options) — but it must NOT be paired with a second
ad slot on the same page. So: R2 suppressed when R1 rendered and only one
candidate exists.

---

## 8. QA gates to add (build fails if any fails)

| # | Gate | Threshold |
|---|---|---|
| 23 | Every rendered link has non-empty `hook`, `promise`, `btn` | 48/48 products×links |
| 24 | No two links of the same product share a `hook` | 0 duplicates |
| 25 | Zero exclamation marks in any copy field | 0 |
| 26 | Zero banned terms (beli sekarang, termurah, terbaik, diskaun, % ) | 0 |
| 27 | Every `hook` traceable to a corpus failure mode, or flagged benefit-only | 48/48 audited |
| 28 | All 3 links present and distinct per card | 100% of rendered cards |
| 29 | No page shows 2 ads for the same product | 0 |
| 30 | `rel="sponsored nofollow noopener"` on all 48 links | 100% |
| 31 | DITAJA chip on every card | 100% |

---

## 9. Work order (once approved)

1. Write `ad_copy_per_link.py` — 48 blocks as data, with corpus-evidence field per block.
2. Rewrite `ad_render_wired.py` — three-row card + compact variants reading per-link copy.
3. Patch `ads_wired.py` — per-row link rotation; suppress R2 on single-candidate pages.
4. Build preview HTML + raster mock, visually verify all 16 products.
5. Add gates 23–31 to `verify_all.py`, run full 31-gate build.
6. **Not** wire into `build_static.py` until you separately approve placement.

---

## 10. What I need from you

1. **Approve the three-row card** (§5) — or say if you prefer one headline + 3 buttons.
2. **Approve one-ad-per-page rule** for the 303 single-product recipes (§7) — this is the
   one place where "promote all 3 links" and "don't look spammy" collide.
3. **Confirm the copy voice** in §4 — if any hook sounds off (too casual, too salesy),
   tell me which product and I'll rewrite that block only.
4. Rice cooker has no corpus pain language — OK to run **benefit-angle copy** for it?
