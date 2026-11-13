import { useEffect, useRef, useState } from "react";

/* Expanding grid: cells light up in a wave from the centre, like Trajectory's hero */
function ExpandingGrid() {
  const COLS = 16;
  const ROWS = 9;
  const cells = COLS * ROWS;
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 3800);
    return () => clearInterval(id);
  }, []);

  const cx = (COLS - 1) / 2;
  const cy = (ROWS - 1) / 2;

  const items = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const dist = Math.hypot(c - cx, (r - cy) * 1.35);
      const delay = dist * 78 + (tick * 137) % 400;
      const seed = (r * 31 + c * 17 + tick) % 23;
      const tint = seed === 0 ? "tint" : seed === 5 ? "tint2" : seed === 11 ? "tint3" : "";
      items.push(
        <div
          key={`${r}-${c}-${tick}`}
          className={`grid-cell ${tint}`}
          style={{
            animation: `cellIn 1200ms cubic-bezier(0.22,1,0.36,1) ${delay}ms forwards`,
            opacity: 0,
          }}
        />
      );
    }
  }

  return (
    <>
      <style>{`
        @keyframes cellIn {
          0%   { opacity: 0; transform: scale(0.7); }
          55%  { opacity: 1; transform: scale(1); }
          100% { opacity: var(--cell-end, 0.9); transform: scale(1); }
        }
        @media (prefers-reduced-motion: reduce) {
          @keyframes cellIn { 0%,100% { opacity: 0.9; transform: scale(1); } }
        }
      `}</style>
      <div
        className="grid-stage pointer-events-none select-none"
        style={{ "--cols": COLS, gridTemplateRows: `repeat(${ROWS}, 1fr)` }}
        aria-hidden="true"
      >
        {items}
      </div>
    </>
  );
}

/* 3D-ish paper airplane in CSS transforms — no WebGL needed */
function PaperPlane() {
  const ref = useRef(null);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const y = window.scrollY;
        if (ref.current) {
          const rot = -6 + Math.min(y / 28, 16);
          const tx = Math.min(y / 12, 70);
          const ty = -Math.min(y / 9, 150);
          ref.current.style.transform = `translate3d(${tx}px, ${ty}px, 0) rotate(${rot}deg)`;
        }
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => { window.removeEventListener("scroll", onScroll); cancelAnimationFrame(raf); };
  }, []);

  return (
    <div className="pointer-events-none absolute inset-0 z-10 hidden md:block" aria-hidden="true">
      <div className="plane-shadow absolute left-[58%] top-[46%] h-7 w-36 rounded-[50%] bg-[#6b5a4a] blur-md" />
      <div ref={ref} className="plane-wrap absolute left-[56%] top-[34%]">
        <svg width="150" height="118" viewBox="0 0 150 118" fill="none">
          <defs>
            <linearGradient id="pg1" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="100%" stopColor="#efe4d6" />
            </linearGradient>
            <linearGradient id="pg2" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#d9c9b4" />
              <stop offset="100%" stopColor="#c2ad94" />
            </linearGradient>
          </defs>
          {/* main wing */}
          <path d="M6 58 L140 10 L72 74 Z" fill="url(#pg1)" stroke="#c9b8a3" strokeWidth="1" strokeLinejoin="round" />
          {/* under wing */}
          <path d="M72 74 L140 10 L82 96 Z" fill="url(#pg2)" stroke="#b8a48c" strokeWidth="1" strokeLinejoin="round" />
          {/* keel */}
          <path d="M72 74 L82 96 L64 88 Z" fill="#e8dccd" stroke="#c9b8a3" strokeWidth="0.8" strokeLinejoin="round" />
          {/* crease */}
          <path d="M72 74 L140 10" stroke="#cbb9a2" strokeWidth="0.9" strokeDasharray="3 3" opacity="0.75" />
        </svg>
      </div>
    </div>
  );
}

function Stat({ value, label, sub, delay }) {
  return (
    <div className="reveal" style={{ "--d": `${delay}ms` }}>
      <div className="display text-[2.1rem] leading-none sm:text-[2.5rem]">{value}</div>
      <div className="mt-2 text-[12.5px] font-medium text-[var(--color-ink)]">{label}</div>
      <div className="mt-0.5 text-[11.5px] text-[var(--color-ink-mute)]">{sub}</div>
    </div>
  );
}

export default function Hero({ total, onExplore }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 60);
    return () => clearTimeout(t);
  }, []);

  return (
    <section id="top" className="relative overflow-hidden pt-[68px]">
      {/* expanding grid backdrop */}
      <div className="absolute inset-0 top-[68px] opacity-[0.55]">
        <ExpandingGrid />
      </div>
      <PaperPlane />

      <div className="relative z-20 mx-auto max-w-[1180px] px-5 pb-16 pt-16 sm:px-8 sm:pt-24">
        <div className={`max-w-[720px] transition-all duration-1000 ${mounted ? "translate-y-0 opacity-100" : "translate-y-5 opacity-0"}`}>
          <div className="eyebrow mb-5 flex items-center gap-2.5">
            <span className="inline-block h-px w-7 bg-[var(--color-terracotta)]" />
            Koleksi Resepi · {total} Hidangan
          </div>

          <h1 className="display text-[2.7rem] leading-[0.94] sm:text-[4.2rem] lg:text-[4.9rem]">
            Setiap resepi,<br />
            <em>sudah diuji.</em>
          </h1>

          <p className="mt-6 max-w-[34rem] text-[15.5px] leading-relaxed text-[var(--color-ink-soft)] sm:text-[16.5px]">
            Bahan-bahan tepat, langkah demi langkah, dan tip yang benar-benar
            membantu. Tiada tekaan — hanya masakan yang anda boleh ulang
            dengan yakin.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <button
              onClick={onExplore}
              className="group inline-flex items-center gap-2 rounded-full bg-[var(--color-ink)] px-6 py-3.5 text-[14px] font-medium text-[var(--color-cream)] transition-all hover:-translate-y-0.5 hover:shadow-[0_16px_32px_-12px_rgba(26,24,21,0.5)]"
            >
              Lihat Koleksi
              <svg viewBox="0 0 24 24" className="h-4 w-4 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </button>
            <a
              href="#cara"
              className="inline-flex items-center gap-2 rounded-full border border-[var(--color-line)] bg-white/60 px-6 py-3.5 text-[14px] font-medium text-[var(--color-ink)] backdrop-blur-sm transition-all hover:border-[var(--color-ink-mute)]"
            >
              Cara Guna
            </a>
          </div>

          <div className="mt-14 grid grid-cols-2 gap-x-6 gap-y-8 border-t border-[var(--color-line)] pt-8 sm:grid-cols-4">
            <Stat value={total} label="Resepi penuh" sub="Bahan & langkah" delay={80} />
            <Stat value="9" label="Kategori" sub="Ayam ke minuman" delay={160} />
            <Stat value="210+" label="Bahan tersenarai" sub="Sukatan tepat" delay={240} />
            <Stat value="100%" label="Percuma" sub="Tiada daftar" delay={320} />
          </div>
        </div>
      </div>

      {/* fade to content */}
      <div className="relative z-20 h-24 bg-gradient-to-b from-transparent to-[var(--color-cream)]" />
    </section>
  );
}
