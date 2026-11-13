"""Renders /penulis/ hub and /penulis/<key>/ persona pages.

TRUST DESIGN
------------
These pages exist to answer "who wrote this?" for Google and for readers.
That only works if they are true. So:

  * The hub carries an explicit disclosure that these are pen names used by
    the kitchen team. Disclosed pen names are legitimate author attribution;
    pen names dressed up as verifiable individuals are not.
  * No bio claims a school, employer, award, certification or year count.
    Each claim maps to something the site can demonstrate (categories
    covered, number of recipes, the troubleshooting-tip style).
  * Person schema carries name, jobTitle, description, image, url and
    knowsAbout — the fields we can actually substantiate. It deliberately
    omits sameAs to social profiles (none exist) because an empty or fake
    sameAs is worse than none.
"""
import json

from authors import PERSONAS, TEAM, persona_key_for_category as _key_for_cat


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def counts_by_persona(cats_of: dict) -> dict:
    """cats_of: {slug: category_name} -> {persona_key: n_recipes}"""
    out = {k: 0 for k in PERSONAS}
    for cat in cats_of.values():
        out[_key_for_cat(cat)] += 1
    return out


def person_schema(key: str, p: dict, site_url: str, n_recipes: int) -> dict:
    """Person JSON-LD built from substantiable fields only."""
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "@id": f"{site_url}/penulis/{key}/#person",
        "name": p["name"],
        "jobTitle": p["role"],
        "description": p["short"],
        "url": f"{site_url}/penulis/{key}/",
        "image": {"@type": "ImageObject", "url": site_url + p["avatar"]},
        "worksFor": {"@type": "Organization",
                     "name": "Resepi Fesbuk", "url": site_url},
        # knowsAbout is the topical claim; it is backed by the categories
        # this persona actually authors.
        "knowsAbout": p["cats"],
        "knowsLanguage": "ms-MY",
    }


def _avatar(p: dict) -> str:
    return (f'<img class="pa-avatar" src="{p["avatar"]}" width="96" height="96" '
            f'alt="{_esc(p["name"])}" loading="lazy">')


def persona_page(key: str, p: dict, site_url: str, n_recipes: int,
                 recent: list, others: dict) -> str:
    """Body HTML for one persona page. `recent` = [(title, url, cat)]."""
    bio = "".join(f"<p>{_esc(x)}</p>" for x in p["bio"])
    focus = "".join(f"<li>{_esc(x)}</li>" for x in p["focus"])
    recs = "".join(
        f'<li><a href="{u}">{_esc(t)}</a> <span class="pa-cat">{_esc(c)}</span></li>'
        for t, u, c in recent)
    other_links = "".join(
        f'<li><a href="/penulis/{k}/">{_esc(v["name"])}</a> — {_esc(v["role"])}</li>'
        for k, v in others.items())

    return f"""<main>
<section>
  <div class="wrap-narrow">
    <nav class="breadcrumb" aria-label="Breadcrumb">
      <a href="/">Utama</a> / <a href="/penulis/">Penulis</a> / {_esc(p["name"])}
    </nav>
    <div class="pa-head">
      {_avatar(p)}
      <div>
        <h1 class="display">{_esc(p["name"])}</h1>
        <p class="pa-role">{_esc(p["role"])}</p>
        <p class="pa-meta">{n_recipes} resepi ditulis</p>
      </div>
    </div>
    <div class="pa-bio">{bio}</div>

    <h2 class="pa-h2">Fokus</h2>
    <ul class="pa-focus">{focus}</ul>

    <h2 class="pa-h2">Resepi terkini oleh {_esc(p["name"])}</h2>
    <ul class="pa-list">{recs}</ul>
    <p class="pa-more"><a href="/resepi/">Lihat semua resepi &rarr;</a></p>

    <h2 class="pa-h2">Penulis lain</h2>
    <ul class="pa-list">{other_links}</ul>

    <div class="source-note">
      <p>Nama ini ialah nama pena yang digunakan oleh pasukan dapur kami untuk
      menyusun penulisan mengikut bidang. <a href="/penulis/">Ketahui lebih lanjut</a>.</p>
    </div>
  </div>
</section>
</main>"""


def hub_page(site_url: str, counts: dict, total_recipes: int) -> str:
    cards = []
    for k, p in PERSONAS.items():
        n = counts.get(k, 0)
        cards.append(f"""
    <a class="pa-card" href="/penulis/{k}/">
      {_avatar(p)}
      <h2>{_esc(p["name"])}</h2>
      <p class="pa-role">{_esc(p["role"])}</p>
      <p class="pa-meta">{n} resepi</p>
      <p class="pa-short">{_esc(p["short"])}</p>
    </a>""")
    return f"""<main>
<section>
  <div class="wrap-narrow">
    <nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Utama</a> / Penulis</nav>
    <h1 class="display">Penulis <em>dapur kami</em></h1>
    <p class="lede">Tiga penulis, tiga bidang. Setiap resepi di laman ini ditulis
    oleh salah seorang daripada mereka, mengikut jenis masakan.</p>

    <div class="pa-grid">{"".join(cards)}
    </div>

    <h2 class="pa-h2">Tentang nama-nama ini</h2>
    <p>Nama-nama di atas ialah <strong>nama pena</strong>. Pasukan dapur kami
    menggunakannya supaya penulisan boleh disusun mengikut bidang — kuih dan kek,
    lauk harian, serta minuman dan sup. Kami memilih untuk menyatakannya secara
    terbuka kerana kami mahu anda tahu dengan siapa anda membaca, bukan menganggap
    ia nama individu tertentu.</p>
    <p>Setiap halaman penulis menyenaraikan kategori yang ditulis oleh mereka
    dan bilangan resepi. Itu adalah rekod sebenar laman ini, bukan dakwaan
    kelayakan. Kami tidak membuat tuntutan tentang latar belakang formal,
    tempat kerja atau sebarang pengiktirafan — kerana tiada apa yang boleh
    kami buktikan di sana.</p>
    <p>Ada soalan tentang sesebuah resepi? <a href="/hubungi/">Hubungi kami</a>.</p>
  </div>
</section>
</main>"""
