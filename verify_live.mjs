import { JSDOM } from "jsdom";
import fs from "node:fs";

const BASE = "https://pakundur.github.io/resepifesbuk";
const results = [];
const check = (n, c, e = "") => results.push({ n, pass: !!c, e });

// 1. Fetch live index
const html = await (await fetch(BASE + "/")).text();
check("live index served", html.length > 400, `${html.length} chars`);

// 2. Fetch the live bundle
const jsSrc = html.match(/src="([^"]+\.js)"/)[1];
const jsUrl = new URL(jsSrc, BASE).href;
const jsRes = await fetch(jsUrl);
const js = await jsRes.text();
check("live bundle 200", jsRes.status === 200, `status=${jsRes.status}`);
check("live bundle non-trivial", js.length > 200000, `${js.length} chars`);

// 3. Fetch live CSS
const cssHref = html.match(/href="([^"]+\.css)"/)[1];
const cssRes = await fetch(new URL(cssHref, BASE).href);
const css = await cssRes.text();
check("live CSS 200", cssRes.status === 200, `status=${cssRes.status}`);
check("live CSS has custom classes", css.includes("grid-stage") && css.includes("sky-field") && css.includes("rcard"));

// 4. Execute the LIVE bundle in jsdom
const dom = new JSDOM(html, { runScripts: "outside-only", url: BASE + "/" });
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

let errs = [];
window.addEventListener("error", (e) => errs.push(e.message));
const origErr = console.error;
console.error = (...a) => errs.push(a.join(" "));

try {
  window.eval(js);
} catch (e) {
  errs.push("THROW: " + e.message);
}
await new Promise(r => setTimeout(r, 1600));
console.error = origErr;

const doc = window.document;
const text = (doc.getElementById("root")?.textContent || "").replace(/\s+/g, " ").trim();

check("app mounted from live bundle", text.length > 800, `${text.length} chars`);
check("no runtime errors", errs.length === 0, errs.slice(0,2).join(" | "));
check("renders hero headline", text.includes("Setiap resepi"));
check("renders real recipe", text.includes("Nasi Goreng Bombay"));
check("renders 25 cards", doc.querySelectorAll("article.rcard").length === 25, `count=${doc.querySelectorAll("article.rcard").length}`);
check("renders filter pills", doc.querySelectorAll("button.pill").length === 9);

// 5. Verify a real recipe image is reachable
const firstImg = doc.querySelector("article.rcard img")?.src;
const imgRes = await fetch(firstImg, { method: "HEAD" });
check("live recipe image loads", imgRes.status === 200, `${imgRes.status} ${firstImg?.slice(-30)}`);

let fails = 0;
for (const r of results) {
  if (!r.pass) fails++;
  console.log(`${r.pass ? "PASS" : "FAIL"}  ${r.n}${r.e ? "  [" + r.e + "]" : ""}`);
}
console.log("\n" + "=".repeat(52));
console.log(`LIVE SITE: ${results.length - fails}/${results.length} passed`);
if (errs.length) { console.log("\nERRORS:"); errs.slice(0,4).forEach(e => console.log("  - " + e.slice(0,200))); }
console.log("\nRENDERED:", text.slice(0, 320));
process.exit(fails ? 1 : 0);
