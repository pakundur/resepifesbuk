// Executes the REAL FAB_JS string against a minimal DOM stub.
// Proves toggle, aria, tabindex, Escape, outside-click and scroll behaviour
// without a browser (none exists for ARM64 Termux).
import { execSync } from 'child_process';

const py = execSync(
  `python3 -c "import fab,json;print(json.dumps(fab.FAB_JS))"`,
  { cwd: process.cwd() }
).toString();
const FAB_JS = JSON.parse(py);

// ---- minimal DOM ----
class El {
  constructor(tag, attrs = {}) {
    this.tag = tag; this.attrs = { ...attrs }; this.children = [];
    this.classes = new Set((attrs.class || '').split(/\s+/).filter(Boolean));
    this.listeners = {}; this.tabIndex = attrs.tabindex !== undefined ? Number(attrs.tabindex) : 0;
    this.focused = false;
  }
  get classList() {
    const s = this.classes;
    return {
      add: c => s.add(c),
      remove: c => s.delete(c),
      contains: c => s.has(c),
      toggle: (c, on) => { if (on === undefined) on = !s.has(c); on ? s.add(c) : s.delete(c); return on; },
    };
  }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  addEventListener(t, fn) { (this.listeners[t] ||= []).push(fn); }
  contains(x) {
    // Real DOM contains() walks the whole subtree, not just direct children.
    if (x === this) return true;
    return this.children.some(c => c.contains(x));
  }
  querySelectorAll(sel) {
    const cls = sel.replace(/^\./, '');
    return this.children.filter(c => c.classes.has(cls));
  }
  focus() { this.focused = true; }
  click() { (this.listeners.click || []).forEach(f => f({ preventDefault() {}, target: this })); }
  fire(t, ev = {}) { (this.listeners[t] || []).forEach(f => f({ preventDefault() {}, ...ev })); }
}

const fab = new El('div', { id: 'fab' });
const btn = new El('button', { id: 'fab-share', 'aria-expanded': 'false' });
const fan = new El('div', { id: 'fab-fan', 'aria-hidden': 'true' });
const top = new El('a', { id: 'fab-top', href: '#top' });
const items = Array.from({ length: 8 }, () => new El('a', { class: 'fab__item', tabindex: '-1' }));
items.forEach(it => fan.children.push(it));
fab.children.push(fan, btn, top);

const byId = { fab, 'fab-share': btn, 'fab-fan': fan, 'fab-top': top };
const docListeners = {};
global.document = {
  getElementById: id => byId[id] ?? null,
  addEventListener: (t, fn) => (docListeners[t] ||= []).push(fn),
  body: { appendChild() {}, removeChild() {} },
  execCommand: () => true,
  createElement: () => new El('input'),
};
global.window = { matchMedia: () => ({ matches: false }), scrollTo: () => { global.__scrolled = true; } };
global.history = { replaceState: () => {} };
global.location = { href: 'https://resepifesbuk.com/x/', pathname: '/x/', search: '' };
Object.defineProperty(global, 'navigator', {
  value: { clipboard: { writeText: () => Promise.resolve() } },
  configurable: true,
});
global.setTimeout = (f) => { f(); return 0; };

const code = FAB_JS.replace(/^<script>/, '').replace(/<\/script>$/, '');
eval(code);

const fireDoc = (t, ev) => (docListeners[t] || []).forEach(f => f({ preventDefault() {}, ...ev }));
let pass = 0, fail = 0;
const t = (name, cond) => { cond ? (pass++, console.log('  PASS', name)) : (fail++, console.log('  FAIL', name)); };

console.log('initial state');
t('fab not open', !fab.classList.contains('is-open'));
t('aria-expanded=false', btn.getAttribute('aria-expanded') === 'false');
t('fan aria-hidden=true', fan.getAttribute('aria-hidden') === 'true');
t('all 8 items tabindex=-1', items.every(i => i.tabIndex === -1));

console.log('after trigger click');
btn.click();
t('fab is-open', fab.classList.contains('is-open'));
t('aria-expanded=true', btn.getAttribute('aria-expanded') === 'true');
t('fan aria-hidden=false', fan.getAttribute('aria-hidden') === 'false');
t('all 8 items tabindex=0', items.every(i => i.tabIndex === 0));

console.log('after second click (close)');
btn.click();
t('closed again', !fab.classList.contains('is-open'));
t('items back to tabindex=-1', items.every(i => i.tabIndex === -1));

console.log('Escape closes');
btn.click();
fireDoc('keydown', { key: 'Escape' });
t('escape closed it', !fab.classList.contains('is-open'));
t('focus returned to trigger', btn.focused === true);

console.log('outside click closes');
btn.click();
fireDoc('click', { target: new El('p') });
t('outside click closed it', !fab.classList.contains('is-open'));

console.log('inside click does NOT close');
btn.click();
fireDoc('click', { target: items[0] });
t('inside click kept it open', fab.classList.contains('is-open'));

console.log('back-to-top scrolls');
top.fire('click');
t('window.scrollTo called', global.__scrolled === true);

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
