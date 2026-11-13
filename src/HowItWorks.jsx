import { useEffect, useRef, useState } from "react";
import { useReveal } from "./RecipeGrid.jsx";

const STEPS = [
  {
    n: "01",
    title: "Pilih hidangan",
    body: "Tap mana-mana kad untuk buka resepi penuh. Setiap satu ada senarai bahan yang tepat dan langkah yang jelas — tiada anggaran kabur.",
    label: "Koleksi",
  },
  {
    n: "02",
    title: "Sediakan bahan",
    body: "Tanda bahan yang sudah ada di dapur. Senarai anda bergerak sendiri, jadi anda tak perlu fikir dua kali di pasar.",
    label: "Bahan",
  },
  {
    n: "03",
    title: "Ikut langkah",
    body: "Masak mengikut urutan yang telah diuji. Setiap langkah ditulis oleh orang yang benar-benar memasaknya, bukan dijana.",
    label: "Langkah",
  },
  {
    n: "04",
    title: "Hidang & ulang",
    body: "Simpan resepi yang menjadi. Kali seterusnya, anda masak dengan yakin — bukan cuba-cuba.",
    label: "Hidang",
  },
];

/* Animated flow diagram — nodes light up in sequence */
function FlowDiagram({ activeIdx }) {
  const nodes = [
    { x: 50, y: 34, label: "Pilih" },
    { x: 186, y: 86, label: "Sedia" },
    { x: 122, y: 168, label: "Masak" },
    { x: 244, y: 218, label: "Hidang" },
  ];
  const path = `M${nodes[0].x} ${nodes[0].y} L${nodes[1].x} ${nodes[1].y} L${nodes[2].x} ${nodes[2].y} L${nodes[3].x} ${nodes[3].y}`;

  return (
    <svg viewBox="0 0 300 260" className="h-full w-full" aria-hidden="true">
      <path d={path} fill="none" className="diag-line" />
      {nodes.map((n, i) => (
        <g key={i}>
          <circle
            cx={n.x}
            cy={n.y}
            r={i === activeIdx ? 15 : 11}
            fill={i === activeIdx ? "var(--color-terracotta)" : "var(--color-cream)"}
            stroke={i === activeIdx ? "var(--color-terracotta)" : "var(--color-line)"}
            strokeWidth="1.5"
            style={{ transition: "all 500ms cubic-bezier(0.22,1,0.36,1)" }}
          />
          <circle cx={n.x} cy={n.y} r="3.4" fill={i === activeIdx ? "#fff" : "var(--color-ink-mute)"} className={i === activeIdx ? "" : "diag-node"} />
          <text
            x={n.x + (i % 2 ? 22 : -22)}
            y={n.y + 4}
            textAnchor={i % 2 ? "start" : "end"}
            className="font-mono"
            fontSize="9.5"
            fill={i === activeIdx ? "var(--color-ink)" : "var(--color-ink-mute)"}
            style={{ transition: "fill 400ms" }}
          >
            {n.label}
          </text>
        </g>
      ))}
    </svg>
  );
}

export default function HowItWorks() {
  const [idx, setIdx] = useState(0);
  const ref = useReveal("how");
  const timer = useRef(null);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    timer.current = setInterval(() => setIdx((i) => (i + 1) % STEPS.length), 2600);
    return () => clearInterval(timer.current);
  }, []);

  return (
    <section id="cara" ref={ref} className="relative border-y border-[var(--color-line)] bg-[var(--color-cream-deep)]/60">
      <div className="mx-auto max-w-[1180px] px-5 py-20 sm:px-8 sm:py-28">
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.72fr)] lg:gap-16">
          <div>
            <div className="reveal eyebrow mb-3">Cara Guna</div>
            <h2 className="reveal display mb-4 max-w-[16ch] text-[2rem] sm:text-[2.9rem]" style={{ "--d": "60ms" }}>
              Empat langkah, <em>tiada tekaan</em>
            </h2>
            <p className="reveal mb-10 max-w-[38ch] text-[14.5px] leading-relaxed text-[var(--color-ink-soft)]" style={{ "--d": "120ms" }}>
              Dari pilih hidangan sampai ke meja — semuanya dalam satu aliran
              yang mudah diikuti.
            </p>

            <div className="space-y-1">
              {STEPS.map((s, i) => (
                <button
                  key={s.n}
                  onMouseEnter={() => setIdx(i)}
                  onFocus={() => setIdx(i)}
                  onClick={() => setIdx(i)}
                  className={`reveal group flex w-full items-start gap-4 rounded-xl border px-4 py-4 text-left transition-all duration-500 ${
                    idx === i
                      ? "border-[var(--color-line)] bg-white shadow-[0_10px_30px_-16px_rgba(120,72,40,0.35)]"
                      : "border-transparent hover:bg-white/50"
                  }`}
                  style={{ "--d": `${180 + i * 70}ms` }}
                  aria-pressed={idx === i}
                >
                  <span
                    className={`mt-0.5 font-mono text-[11px] font-semibold transition-colors ${
                      idx === i ? "text-[var(--color-terracotta)]" : "text-[var(--color-ink-mute)]"
                    }`}
                  >
                    {s.n}
                  </span>
                  <span className="min-w-0">
                    <span className="block text-[14.5px] font-semibold tracking-tight text-[var(--color-ink)]">
                      {s.title}
                    </span>
                    <span
                      className={`mt-1 block text-[13px] leading-relaxed transition-all duration-500 ${
                        idx === i ? "text-[var(--color-ink-soft)]" : "text-[var(--color-ink-mute)]"
                      }`}
                    >
                      {s.body}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Diagram panel */}
          <div className="reveal lg:sticky lg:top-24 lg:self-start" style={{ "--d": "260ms" }}>
            <div className="rounded-[16px] border border-[var(--color-line)] bg-white p-6 shadow-[0_18px_50px_-30px_rgba(120,72,40,0.4)]">
              <div className="mb-4 flex items-center justify-between">
                <span className="font-mono text-[10.5px] uppercase tracking-widest text-[var(--color-ink-mute)]">
                  Aliran
                </span>
                <span className="rounded-full bg-[var(--color-cream-deep)] px-2.5 py-1 font-mono text-[10px] text-[var(--color-ink-soft)]">
                  {STEPS[idx].label}
                </span>
              </div>
              <div className="aspect-[300/260]">
                <FlowDiagram activeIdx={idx} />
              </div>
              <div className="mt-4 border-t border-[var(--color-line)] pt-4">
                <div className="text-[12.5px] font-medium text-[var(--color-ink)]">{STEPS[idx].title}</div>
                <div className="mt-1 font-mono text-[10.5px] text-[var(--color-ink-mute)]">
                  langkah {idx + 1} / {STEPS.length}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
