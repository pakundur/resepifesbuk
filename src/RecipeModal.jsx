import { useEffect, useRef, useState } from "react";

export default function RecipeModal({ recipe, onClose }) {
  const cardRef = useRef(null);
  const closeRef = useRef(null);
  const [checked, setChecked] = useState({});

  // Focus trap + restore
  useEffect(() => {
    const prev = document.activeElement;
    closeRef.current?.focus();
    const onKey = (e) => {
      if (e.key !== "Tab" || !cardRef.current) return;
      const f = cardRef.current.querySelectorAll(
        'a[href], button:not([disabled]), input, [tabindex]:not([tabindex="-1"])'
      );
      if (!f.length) return;
      const first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      if (prev && prev.focus) prev.focus();
    };
  }, []);

  const toggle = (i) => setChecked((c) => ({ ...c, [i]: !c[i] }));
  const allIngs = recipe.ings.length;
  const doneIngs = Object.values(checked).filter(Boolean).length;

  return (
    <div
      className="modal-scrim fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-6"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-modal="true"
      aria-labelledby="recipe-title"
    >
      <div
        ref={cardRef}
        className="modal-card relative flex max-h-[92vh] w-full max-w-[860px] flex-col overflow-hidden rounded-t-[20px] bg-[var(--color-cream)] shadow-2xl sm:rounded-[20px]"
      >
        <button
          ref={closeRef}
          onClick={onClose}
          className="absolute right-3 top-3 z-20 grid h-9 w-9 place-items-center rounded-full bg-[var(--color-cream)]/92 text-[var(--color-ink)] shadow-sm backdrop-blur transition-transform hover:scale-105"
          aria-label="Tutup"
        >
          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>

        <div className="thin-scroll overflow-y-auto overscroll-contain">
          {/* Hero image */}
          <div className="relative aspect-[16/9] w-full overflow-hidden bg-[var(--color-cream-deep)]">
            <img src={recipe.img} alt={recipe.name} className="h-full w-full object-cover" />
            <div className="absolute inset-0 bg-gradient-to-t from-[var(--color-ink)]/72 via-transparent to-transparent" />
            <div className="absolute inset-x-0 bottom-0 p-5 sm:p-7">
              <div className="mb-2 flex flex-wrap gap-1.5">
                {recipe.cats.slice(0, 3).map((c) => (
                  <span key={c} className="rounded-full bg-white/92 px-2.5 py-0.5 text-[10.5px] font-medium text-[var(--color-ink)]">
                    {c}
                  </span>
                ))}
              </div>
              <h2 id="recipe-title" className="display text-[1.6rem] leading-tight text-white sm:text-[2.1rem]">
                {recipe.name.replace(/^Resepi\s+/i, "")}
              </h2>
            </div>
          </div>

          <div className="p-5 sm:p-7">
            {recipe.sub && (
              <p className="mb-6 border-l-2 border-[var(--color-terracotta)] pl-4 text-[14px] italic leading-relaxed text-[var(--color-ink-soft)]">
                {recipe.sub}
              </p>
            )}

            <div className="grid gap-8 md:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
              {/* Ingredients */}
              <div>
                <div className="mb-3 flex items-baseline justify-between">
                  <h3 className="text-[13px] font-semibold uppercase tracking-wider text-[var(--color-ink)]">
                    Bahan-Bahan
                  </h3>
                  <span className="font-mono text-[10.5px] text-[var(--color-ink-mute)]">
                    {doneIngs}/{allIngs}
                  </span>
                </div>
                <div className="mb-3 h-1 w-full overflow-hidden rounded-full bg-[var(--color-line)]">
                  <div
                    className="h-full rounded-full bg-[var(--color-terracotta)] transition-all duration-500"
                    style={{ width: `${allIngs ? (doneIngs / allIngs) * 100 : 0}%` }}
                  />
                </div>
                <ul className="space-y-0.5">
                  {recipe.ings.map((ing, i) => (
                    <li key={i}>
                      <button
                        onClick={() => toggle(i)}
                        className="flex w-full items-start gap-2.5 rounded-lg px-1.5 py-2 text-left transition-colors hover:bg-[var(--color-cream-deep)]"
                        aria-pressed={!!checked[i]}
                      >
                        <span
                          className={`mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded border transition-all ${
                            checked[i]
                              ? "border-[var(--color-terracotta)] bg-[var(--color-terracotta)]"
                              : "border-[var(--color-line)] bg-white"
                          }`}
                        >
                          {checked[i] && (
                            <svg viewBox="0 0 24 24" className="h-2.5 w-2.5 text-white" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round">
                              <path d="M5 13l4 4L19 7" />
                            </svg>
                          )}
                        </span>
                        <span
                          className={`text-[13px] leading-snug transition-all ${
                            checked[i]
                              ? "text-[var(--color-ink-mute)] line-through decoration-[var(--color-line)]"
                              : "text-[var(--color-ink-soft)]"
                          }`}
                        >
                          {ing}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Steps */}
              <div>
                <h3 className="mb-3 text-[13px] font-semibold uppercase tracking-wider text-[var(--color-ink)]">
                  Cara Penyediaan
                </h3>
                <ol className="space-y-4">
                  {recipe.steps.map((s, i) => (
                    <li key={i} className="flex gap-3">
                      <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full border border-[var(--color-line)] bg-white font-mono text-[11px] font-semibold text-[var(--color-terracotta)]">
                        {i + 1}
                      </span>
                      <p className="text-[13px] leading-relaxed text-[var(--color-ink-soft)]">{s}</p>
                    </li>
                  ))}
                </ol>

                {recipe.tips?.length > 0 && (
                  <div className="mt-6 rounded-xl border border-[var(--color-line)] bg-white p-4">
                    <div className="mb-2 flex items-center gap-1.5 text-[11.5px] font-semibold uppercase tracking-wider text-[var(--color-terracotta)]">
                      <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      Tip
                    </div>
                    <ul className="space-y-2">
                      {recipe.tips.map((t, i) => (
                        <li key={i} className="text-[12.5px] leading-relaxed text-[var(--color-ink-soft)]">
                          {t}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-7 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--color-line)] pt-5">
              <span className="text-[11.5px] text-[var(--color-ink-mute)]">
                Diterbitkan {recipe.date}
              </span>
              <a
                href={recipe.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-ink)] px-4 py-2.5 text-[12.5px] font-medium text-[var(--color-cream)] transition-transform hover:-translate-y-0.5"
              >
                Resepi penuh
                <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                  <path d="M7 17L17 7M17 7H8M17 7v9" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
