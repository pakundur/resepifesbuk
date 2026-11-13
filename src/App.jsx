import { useEffect, useRef, useState, useMemo, useCallback } from "react";
import RECIPES from "./recipes.json";
import Hero from "./Hero.jsx";
import RecipeGrid from "./RecipeGrid.jsx";
import RecipeModal from "./RecipeModal.jsx";
import HowItWorks from "./HowItWorks.jsx";
import Footer from "./Footer.jsx";

/* ---------- Category taxonomy ---------- */
const GROUPS = [
  { id: "semua", label: "Semua", match: () => true },
  { id: "ayam", label: "Ayam", match: (c) => c.includes("Ayam") },
  { id: "daging", label: "Daging", match: (c) => c.includes("Daging") },
  { id: "ikan", label: "Ikan & Seafood", match: (c) => c.some((x) => ["Ikan", "Udang", "Sotong", "Ketam"].includes(x)) },
  { id: "sayur", label: "Sayur", match: (c) => c.includes("Sayur") },
  { id: "sup", label: "Sup", match: (c) => c.includes("Sup") },
  { id: "nasi", label: "Nasi & Mee", match: (c) => c.some((x) => ["Nasi", "Mee"].includes(x)) },
  { id: "kuih", label: "Kuih & Kek", match: (c) => c.some((x) => ["Kuih", "Kek", "Biskut", "Roti"].includes(x)) },
  { id: "minuman", label: "Minuman", match: (c) => c.includes("Minuman") },
];

export default function App() {
  const [active, setActive] = useState("semua");
  const [query, setQuery] = useState("");
  const [openRecipe, setOpenRecipe] = useState(null);

  const filtered = useMemo(() => {
    const g = GROUPS.find((x) => x.id === active) || GROUPS[0];
    const q = query.trim().toLowerCase();
    return RECIPES.filter((r) => {
      if (!g.match(r.cats)) return false;
      if (!q) return true;
      return (
        r.name.toLowerCase().includes(q) ||
        r.sub.toLowerCase().includes(q) ||
        r.ings.some((i) => i.toLowerCase().includes(q))
      );
    });
  }, [active, query]);

  // Lock scroll while modal open
  useEffect(() => {
    document.body.style.overflow = openRecipe ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [openRecipe]);

  // Esc closes modal
  useEffect(() => {
    const fn = (e) => e.key === "Escape" && setOpenRecipe(null);
    window.addEventListener("keydown", fn);
    return () => window.removeEventListener("keydown", fn);
  }, []);

  return (
    <div className="sky-field min-h-screen">
      <Nav onSearch={setQuery} query={query} />
      <Hero total={RECIPES.length} onExplore={() => {
        document.getElementById("koleksi")?.scrollIntoView({ behavior: "smooth" });
      }} />

      <section id="koleksi" className="relative mx-auto max-w-[1180px] px-5 pb-24 pt-6 sm:px-8">
        <RecipeGrid
          groups={GROUPS}
          active={active}
          setActive={setActive}
          recipes={filtered}
          total={RECIPES.length}
          query={query}
          setQuery={setQuery}
          onOpen={setOpenRecipe}
        />
      </section>

      <HowItWorks />
      <Footer onOpen={setOpenRecipe} recipes={RECIPES} />

      {openRecipe && <RecipeModal recipe={openRecipe} onClose={() => setOpenRecipe(null)} />}
    </div>
  );
}

/* ================= NAV ================= */
function Nav({ onSearch, query }) {
  const [solid, setSolid] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const fn = () => setSolid(window.scrollY > 30);
    fn();
    window.addEventListener("scroll", fn, { passive: true });
    return () => window.removeEventListener("scroll", fn);
  }, []);

  const links = [
    { href: "#koleksi", label: "Koleksi" },
    { href: "#cara", label: "Cara Guna" },
    { href: "#tentang", label: "Tentang" },
  ];

  return (
    <header
      className={`fixed inset-x-0 top-0 z-40 transition-all duration-500 ${
        solid
          ? "border-b border-[var(--color-line)] bg-[var(--color-cream)]/88 backdrop-blur-xl"
          : "border-b border-transparent"
      }`}
    >
      <div className="mx-auto flex h-[68px] max-w-[1180px] items-center justify-between gap-4 px-5 sm:px-8">
        <a href="#top" className="group flex items-center gap-2.5" aria-label="Resepi Fesbuk">
          <span className="grid h-8 w-8 place-items-center rounded-full bg-[var(--color-ink)] text-[var(--color-cream)]">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M4 11h16M5 11a4 4 0 0 0 4 5h6a4 4 0 0 0 4-5M8 7c0-1 1-1.5 1-2.5M12 7c0-1 1-1.5 1-2.5M16 7c0-1 1-1.5 1-2.5" />
            </svg>
          </span>
          <span className="text-[15px] font-semibold tracking-tight">
            Resepi<span className="text-[var(--color-terracotta)]">Fesbuk</span>
          </span>
        </a>

        <nav className="hidden items-center gap-7 md:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-[13.5px] text-[var(--color-ink-soft)] transition-colors hover:text-[var(--color-ink)]"
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <label className="hidden items-center gap-2 rounded-full border border-[var(--color-line)] bg-white/70 px-3.5 py-2 transition-colors focus-within:border-[var(--color-ink-mute)] sm:flex">
            <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 text-[var(--color-ink-mute)]" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
            </svg>
            <input
              value={query}
              onChange={(e) => onSearch(e.target.value)}
              placeholder="Cari resepi…"
              className="w-32 bg-transparent text-[13px] outline-none placeholder:text-[var(--color-ink-mute)] lg:w-44"
              aria-label="Cari resepi"
            />
          </label>
          <a
            href="https://www.resepifesbuk.com/"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-full bg-[var(--color-ink)] px-4 py-2 text-[13px] font-medium text-[var(--color-cream)] transition-transform hover:-translate-y-0.5"
          >
            Blog Asal
          </a>
          <button
            onClick={() => setOpen(!open)}
            className="grid h-9 w-9 place-items-center rounded-full border border-[var(--color-line)] md:hidden"
            aria-label="Menu"
            aria-expanded={open}
          >
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
          </button>
        </div>
      </div>

      {open && (
        <div className="border-t border-[var(--color-line)] bg-[var(--color-cream)] px-5 py-3 md:hidden">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="block py-2.5 text-[14px] text-[var(--color-ink-soft)]"
            >
              {l.label}
            </a>
          ))}
          <label className="mt-2 flex items-center gap-2 rounded-full border border-[var(--color-line)] bg-white px-3.5 py-2.5">
            <svg viewBox="0 0 24 24" className="h-4 w-4 text-[var(--color-ink-mute)]" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
            </svg>
            <input
              value={query}
              onChange={(e) => onSearch(e.target.value)}
              placeholder="Cari resepi…"
              className="w-full bg-transparent text-[13px] outline-none"
            />
          </label>
        </div>
      )}
    </header>
  );
}
