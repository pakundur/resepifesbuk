import { JSDOM } from "jsdom";
import fs from "node:fs";
import path from "node:path";

const dist = path.resolve("dist");
const html = fs.readFileSync(path.join(dist, "index.html"), "utf8");

// Polyfills the app needs
const dom = new JSDOM(html, { runScripts: "outside-only", url: "https://example.com/" });
const { window } = dom;
window.ResizeObserver = class { observe(){} unobserve(){} disconnect(){} };
window.IntersectionObserver = class {
  constructor(cb){ this.cb = cb; }
  observe(el){ this.cb([{ isIntersecting: true, target: el }], this); }
  unobserve(){} disconnect(){}
};
window.matchMedia = window.matchMedia || (() => ({
  matches: false, media: "", addListener(){}, removeListener(){},
  addEventListener(){}, removeEventListener(){}, dispatchEvent(){ return false; },
}));
window.requestAnimationFrame = (cb) => setTimeout(() => cb(Date.now()), 0);
window.cancelAnimationFrame = (id) => clearTimeout(id);
window.scrollTo = () => {};

// Load built bundle.
// The HTML src carries the deploy base (e.g. "/resepifesbuk/assets/x.js" in CI,
// "/assets/x.js" locally). Strip the base so the path resolves inside dist/.
const rawSrc = html.match(/src="([^"]+\.js)"/)[1];
const base = process.env.GITHUB_ACTIONS ? "/resepifesbuk/" : "/";
const jsFile = rawSrc.startsWith(base) ? rawSrc.slice(base.length) : rawSrc.replace(/^\//, "");
const bundlePath = path.join(dist, jsFile);
if (!fs.existsSync(bundlePath)) {
  console.log(`FATAL: bundle not found.\n  src=${rawSrc}\n  base=${base}\n  resolved=${bundlePath}`);
  const listing = [];
  (function walk(d) {
    for (const f of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, f.name);
      if (f.isDirectory()) walk(p); else listing.push(path.relative(dist, p));
    }
  })(dist);
  console.log("  dist contents:", listing.join(", "));
  process.exit(1);
}
const bundle = fs.readFileSync(bundlePath, "utf8");

let errors = [];
window.addEventListener("error", (e) => errors.push("window.error: " + e.message));
const origError = console.error;
console.error = (...a) => { errors.push("console.error: " + a.join(" ")); };

try {
  window.eval(bundle);
} catch (e) {
  errors.push("EVAL THROW: " + e.message + "\n" + (e.stack || "").split("\n").slice(0,4).join("\n"));
}

await new Promise((r) => setTimeout(r, 1500));
console.error = origError;

const doc = window.document;
const root = doc.getElementById("root");
const text = (root?.textContent || "").replace(/\s+/g, " ").trim();

const results = [];
const check = (name, cond, extra = "") => {
  results.push({ name, pass: !!cond, extra });
};

check("root exists", !!root);
check("root has children", root && root.children.length > 0, `children=${root?.children.length}`);
check("rendered text > 800 chars", text.length > 800, `chars=${text.length}`);
check("no runtime errors", errors.length === 0, errors.slice(0,3).join(" | "));

// Content markers — real data must appear
const markers = [
  "Resepi Fesbuk",
  "Setiap resepi",
  "Lihat Koleksi",
  "Koleksi",
  "Cara Guna",
  "Masak dengan",
];
for (const m of markers) {
  check(`marker "${m}"`, text.includes(m));
}

// Real recipes rendered as cards
const cards = doc.querySelectorAll("article.rcard");
check("recipe cards rendered", cards.length >= 20, `count=${cards.length}`);

// A specific real recipe title must be present
const realTitle = "Nasi Goreng Bombay";
check(`real recipe "${realTitle}"`, text.includes(realTitle));

// Images present with real blogger URLs
const imgs = [...doc.querySelectorAll("img")].filter(i => i.src.includes("blogger.googleusercontent.com"));
check("real recipe images", imgs.length >= 20, `count=${imgs.length}`);

// Filter pills
const pills = doc.querySelectorAll("button.pill");
check("filter pills", pills.length >= 8, `count=${pills.length}`);

// Stats present
check("stat: resepi penuh", text.includes("Resepi penuh"));

// Report
let fails = 0;
for (const r of results) {
  if (!r.pass) fails++;
  console.log(`${r.pass ? "PASS" : "FAIL"}  ${r.name}${r.extra ? "  [" + r.extra + "]" : ""}`);
}
console.log("\n" + "=".repeat(56));
console.log(`RESULT: ${results.length - fails}/${results.length} passed`);
if (errors.length) {
  console.log("\nERRORS (" + errors.length + "):");
  errors.slice(0, 6).forEach(e => console.log("  - " + e.slice(0, 260)));
}
console.log("\nPREVIEW:", text.slice(0, 400));
process.exit(fails > 0 ? 1 : 0);
