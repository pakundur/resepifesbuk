import { JSDOM } from "jsdom";
import fs from "node:fs";
import path from "node:path";

const dist = path.resolve("dist");
const html = fs.readFileSync(path.join(dist, "index.html"), "utf8");
const dom = new JSDOM(html, { runScripts: "outside-only", url: "https://example.com/" });
const { window } = dom;
window.ResizeObserver = class { observe(){} unobserve(){} disconnect(){} };
window.IntersectionObserver = class {
  constructor(cb){ this.cb = cb; }
  observe(el){ this.cb([{ isIntersecting: true, target: el }], this); }
  unobserve(){} disconnect(){}
};
window.matchMedia = window.matchMedia || (() => ({ matches:false, media:"", addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){} }));
window.requestAnimationFrame = (cb) => setTimeout(() => cb(Date.now()), 0);
window.cancelAnimationFrame = (id) => clearTimeout(id);
window.scrollTo = () => {};

// Resolve the bundle relative to the deploy base baked into index.html.
const rawSrc = html.match(/src="([^"]+\.js)"/)[1];
const base = process.env.GITHUB_ACTIONS ? "/resepifesbuk/" : "/";
const jsFile = rawSrc.startsWith(base) ? rawSrc.slice(base.length) : rawSrc.replace(/^\//, "");
window.eval(fs.readFileSync(path.join(dist, jsFile), "utf8"));
await new Promise(r => setTimeout(r, 900));

const doc = window.document;
const results = [];
const check = (n, c, e="") => results.push({ n, pass: !!c, e });

// --- Open first recipe card via click ---
const card = doc.querySelector("article.rcard");
check("found a card to click", !!card);

card.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
await new Promise(r => setTimeout(r, 500));

const modal = doc.querySelector('[role="dialog"]');
check("modal opened", !!modal);
const mText = (modal?.textContent || "").replace(/\s+/g, " ");

check("modal shows ingredients heading", mText.includes("Bahan-Bahan"));
check("modal shows steps heading", mText.includes("Cara Penyediaan"));

// Ingredient checkboxes
const ingBtns = modal ? modal.querySelectorAll('button[aria-pressed]') : [];
check("ingredient toggles rendered", ingBtns.length >= 5, `count=${ingBtns.length}`);

// Step numbers
const stepNums = modal ? modal.querySelectorAll("ol li") : [];
check("steps rendered", stepNums.length >= 3, `count=${stepNums.length}`);

// Toggle an ingredient and confirm state changed
if (ingBtns.length) {
  const before = ingBtns[0].getAttribute("aria-pressed");
  ingBtns[0].dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await new Promise(r => setTimeout(r, 150));
  const after = doc.querySelector('[role="dialog"] button[aria-pressed]').getAttribute("aria-pressed");
  check("ingredient toggle works", before !== after, `${before} -> ${after}`);
}

// Body scroll locked
check("body scroll locked while modal", doc.body.style.overflow === "hidden", `overflow=${doc.body.style.overflow}`);

// --- Close via Escape ---
doc.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
window.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape" }));
await new Promise(r => setTimeout(r, 400));
check("escape closed modal", !doc.querySelector('[role="dialog"]'));

// --- Filter interaction ---
const pills = [...doc.querySelectorAll("button.pill")];
const kuihPill = pills.find(p => p.textContent.trim() === "Kuih & Kek");
check("found Kuih pill", !!kuihPill);
if (kuihPill) {
  kuihPill.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await new Promise(r => setTimeout(r, 400));
  const afterCards = doc.querySelectorAll("article.rcard").length;
  check("filter changed card count", afterCards > 0 && afterCards < 25, `count=${afterCards}`);
  const allPill = [...doc.querySelectorAll("button.pill")].find(p => p.textContent.trim() === "Semua");
  allPill.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await new Promise(r => setTimeout(r, 400));
  check("reset filter restores all", doc.querySelectorAll("article.rcard").length === 25);
}

let fails = 0;
for (const r of results) {
  if (!r.pass) fails++;
  console.log(`${r.pass ? "PASS" : "FAIL"}  ${r.n}${r.e ? "  [" + r.e + "]" : ""}`);
}
console.log("\n" + "=".repeat(50));
console.log(`INTERACTION: ${results.length - fails}/${results.length} passed`);
process.exit(fails > 0 ? 1 : 0);
