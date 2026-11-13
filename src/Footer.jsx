import { useEffect, useRef } from "react";
import { useReveal } from "./RecipeGrid.jsx";

export default function Footer({ onOpen, recipes }) {
  const ref = useReveal("footer");
  const pick = recipes.slice(0, 5);

  return (
    <footer id="tentang" ref={ref} className="relative overflow-hidden">
      {/* marquee of categories */}
      <div className="marquee border-y border-[var(--color-line)] bg-[var(--color-cream-deep)]/70 py-3.5">
        <div className="marquee-track">
          {[0, 1].map((k) => (
            <div key={k} className="flex shrink-0 items-center gap-6 pr-6" aria-hidden={k === 1}>
              {["Ayam", "Daging", "Ikan", "Sup", "Kuih", "Kek", "Nasi", "Mee", "Minuman", "Sayur", "Biskut", "Sambal"].map((c) => (
                <span key={c} className="flex items-center gap-6">
                  <span className="font-mono text-[10.5px] uppercase tracking-[0.2em] text-[var(--color-ink-mute)]">
                    {c}
                  </span>
                  <span className="h-1 w-1 rounded-full bg-[var(--color-terracotta)]/45" />
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>

      <div className="mx-auto max-w-[1180px] px-5 py-16 sm:px-8 sm:py-20">
        <div className="grid gap-12 md:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
          <div>
            <h2 className="reveal display max-w-[18ch] text-[2rem] leading-[1.02] sm:text-[2.8rem]">
              Masak dengan <em>yakin</em>, bukan cuba-cuba.
            </h2>
            <p className="reveal mt-5 max-w-[38ch] text-[14px] leading-relaxed text-[var(--color-ink-soft)]" style={{ "--d": "90ms" }}>
              Koleksi resepi Malaysia yang lengkap dengan sukatan dan langkah
              sebenar. Percuma, tanpa iklan yang mengganggu.
            </p>
            <a
              href="https://www.resepifesbuk.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="reveal mt-7 inline-flex items-center gap-2 rounded-full bg-[var(--color-ink)] px-6 py-3 text-[13.5px] font-medium text-[var(--color-cream)] transition-transform hover:-translate-y-0.5"
              style={{ "--d": "160ms" }}
            >
              Lawati Resepi Fesbuk
              <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M7 17L17 7M17 7H8M17 7v9" />
              </svg>
            </a>
          </div>

          <div className="reveal" style={{ "--d": "140ms" }}>
            <div className="eyebrow mb-4">Popular</div>
            <ul className="space-y-0.5">
              {pick.map((r) => (
                <li key={r.url}>
                  <button
                    onClick={() => onOpen(r)}
                    className="group flex w-full items-center gap-3 rounded-lg px-1 py-2.5 text-left transition-colors hover:bg-[var(--color-cream-deep)]"
                  >
                    <img
                      src={r.img}
                      alt=""
                      loading="lazy"
                      className="h-9 w-9 shrink-0 rounded-md object-cover"
                    />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[12.5px] font-medium text-[var(--color-ink)]">
                        {r.name.replace(/^Resepi\s+/i, "")}
                      </span>
                      <span className="block truncate text-[11px] text-[var(--color-ink-mute)]">
                        {r.cats.slice(0, 2).join(" · ")}
                      </span>
                    </span>
                    <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 shrink-0 text-[var(--color-line)] transition-all group-hover:translate-x-0.5 group-hover:text-[var(--color-terracotta)]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <path d="M9 6l6 6-6 6" />
                    </svg>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-14 flex flex-col items-start justify-between gap-4 border-t border-[var(--color-line)] pt-7 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2">
            <span className="grid h-6 w-6 place-items-center rounded-full bg-[var(--color-ink)] text-[var(--color-cream)]">
              <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M4 11h16M5 11a4 4 0 0 0 4 5h6a4 4 0 0 0 4-5M8 7c0-1 1-1.5 1-2.5M12 7c0-1 1-1.5 1-2.5M16 7c0-1 1-1.5 1-2.5" />
              </svg>
            </span>
            <span className="text-[12.5px] font-medium">
              Resepi<span className="text-[var(--color-terracotta)]">Fesbuk</span>
            </span>
          </div>
          <p className="max-w-[46ch] text-[11.5px] leading-relaxed text-[var(--color-ink-mute)]">
            Demo reka bentuk. Semua resepi, gambar dan kandungan asal milik{" "}
            <a
              href="https://www.resepifesbuk.com/"
              target="_blank"
              rel="noopener noreferrer"
              className="underline decoration-[var(--color-line)] underline-offset-2 hover:text-[var(--color-ink)]"
            >
              resepifesbuk.com
            </a>
            .
          </p>
        </div>
      </div>
    </footer>
  );
}
