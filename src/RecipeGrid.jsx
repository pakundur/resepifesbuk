import { useEffect, useRef } from "react";

/* Scroll reveal observer — shared hook */
export function useReveal(dep) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const nodes = el.querySelectorAll(".reveal:not(.in)");
    if (!nodes.length) return;

    if (!("IntersectionObserver" in window)) {
      nodes.forEach((n) => n.classList.add("in"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );
    nodes.forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, [dep]);
  return ref;
}

function Card({ r, i, onOpen }) {
  const primary = r.cats[0] || "Resepi";
  return (
    <article
      className="rcard reveal group flex cursor-pointer flex-col overflow-hidden rounded-[14px]"
      style={{ "--d": `${Math.min(i, 9) * 55}ms` }}
      onClick={() => onOpen(r)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onOpen(r); }
      }}
      role="button"
      tabIndex={0}
      aria-label={`Buka resepi ${r.name}`}
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-[var(--color-cream-deep)]">
        <img
          src={r.img}
          alt={r.name}
          loading={i < 4 ? "eager" : "lazy"}
          decoding="async"
          className="h-full w-full object-cover"
          onError={(e) => {
            e.currentTarget.style.display = "none";
            e.currentTarget.parentElement.classList.add("grid", "place-items-center");
          }}
        />
        <span className="absolute left-2.5 top-2.5 rounded-full bg-white/92 px-2.5 py-1 text-[10.5px] font-medium tracking-wide text-[var(--color-ink)] backdrop-blur-sm">
          {primary}
        </span>
        {r.steps.length > 0 && (
          <span className="absolute right-2.5 top-2.5 rounded-full bg-[var(--color-ink)]/85 px-2.5 py-1 text-[10.5px] font-medium text-[var(--color-cream)] backdrop-blur-sm">
            {r.steps.length} langkah
          </span>
        )}
      </div>

      <div className="flex flex-1 flex-col p-4">
        <h3 className="text-[15px] font-semibold leading-snug tracking-tight text-[var(--color-ink)]">
          {r.name.replace(/^Resepi\s+/i, "")}
        </h3>
        {r.sub && (
          <p className="mt-1.5 line-clamp-2 text-[12.5px] leading-relaxed text-[var(--color-ink-mute)]">
            {r.sub}
          </p>
        )}
        <div className="mt-auto flex items-center justify-between border-t border-[var(--color-line)] pt-3 text-[11.5px] text-[var(--color-ink-mute)]">
          <span>{r.ings.length} bahan</span>
          <span className="inline-flex items-center gap-1 font-medium text-[var(--color-terracotta)] transition-transform group-hover:translate-x-0.5">
            Lihat
            <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </span>
        </div>
      </div>
    </article>
  );
}

export default function RecipeGrid({ groups, active, setActive, recipes, total, query, setQuery, onOpen }) {
  const ref = useReveal(`${active}|${query}`);

  return (
    <div ref={ref}>
      <div className="reveal mb-7 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="eyebrow mb-2">Koleksi</div>
          <h2 className="display text-[2rem] sm:text-[2.6rem]">
            Pilih ikut <em>selera</em>
          </h2>
        </div>
        <div className="text-[12.5px] text-[var(--color-ink-mute)]">
          {recipes.length} daripada {total} resepi
          {query && (
            <button
              onClick={() => setQuery("")}
              className="ml-2 underline decoration-[var(--color-line)] underline-offset-2 hover:text-[var(--color-ink)]"
            >
              kosongkan carian
            </button>
          )}
        </div>
      </div>

      <div className="reveal thin-scroll -mx-5 mb-8 overflow-x-auto px-5 pb-2 sm:mx-0 sm:px-0">
        <div className="flex gap-2">
          {groups.map((g) => (
            <button
              key={g.id}
              className="pill rounded-full px-3.5 py-2 text-[12.5px] font-medium"
              data-on={active === g.id}
              onClick={() => setActive(g.id)}
            >
              {g.label}
            </button>
          ))}
        </div>
      </div>

      {recipes.length === 0 ? (
        <div className="reveal rounded-[14px] border border-dashed border-[var(--color-line)] bg-white/50 px-6 py-16 text-center">
          <p className="display text-[1.5rem]">Tiada resepi ditemui</p>
          <p className="mt-2 text-[13px] text-[var(--color-ink-mute)]">
            Cuba kategori lain atau kosongkan carian.
          </p>
          <button
            onClick={() => { setActive("semua"); setQuery(""); }}
            className="mt-5 rounded-full bg-[var(--color-ink)] px-5 py-2.5 text-[13px] font-medium text-[var(--color-cream)]"
          >
            Tunjuk semua
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {recipes.map((r, i) => (
            <Card key={r.url} r={r} i={i} onOpen={onOpen} />
          ))}
        </div>
      )}
    </div>
  );
}
