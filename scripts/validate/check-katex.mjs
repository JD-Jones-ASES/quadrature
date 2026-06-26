// check-katex.mjs — every LaTeX string in the derived JSON must render. KaTeX runs at build time;
// a string that throws here would silently break a lesson or the reference. Fails loud (exit 1).

import { readdirSync, statSync, readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, relative, join } from "node:path";
import katex from "katex";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const DERIVED = resolve(ROOT, "derived");

const errors = [];
const fail = (m) => errors.push(m);

function walk(dir, suffix) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...walk(p, suffix));
    else if (name.endsWith(suffix)) out.push(p);
  }
  return out;
}

let count = 0;
function tryRender(latex, where) {
  try {
    katex.renderToString(latex, { throwOnError: true, displayMode: true });
    count++;
  } catch (e) {
    fail(`${where}: KaTeX cannot render ${JSON.stringify(latex)} — ${e.message}`);
  }
}

// solutions: algebra + calculus steps, and result symbolic_latex
for (const file of walk(DERIVED, ".solution.json").sort()) {
  const rel = relative(ROOT, file).replace(/\\/g, "/");
  const d = JSON.parse(readFileSync(file, "utf8"));
  d.algebra.steps.forEach((s, i) => tryRender(s.latex, `${rel} algebra.steps[${i}]`));
  d.calculus.steps.forEach((s, i) => tryRender(s.latex, `${rel} calculus.steps[${i}]`));
  for (const [k, r] of Object.entries(d.algebra.result))
    if (r.symbolic_latex) tryRender(r.symbolic_latex, `${rel} result.${k}`);
}

// reference: each formula's generated LaTeX
const formulasPath = resolve(DERIVED, "reference/formulas.json");
if (existsSync(formulasPath)) {
  const f = JSON.parse(readFileSync(formulasPath, "utf8"));
  for (const fm of f.formulas) tryRender(fm.latex, `formulas.json ${fm.id}`);
}

if (errors.length) {
  console.error(`\nKATEX CHECK FAILED (${errors.length}):`);
  for (const e of errors) console.error("  - " + e);
  process.exit(1);
}
console.log(`OK: ${count} LaTeX string(s) render.`);
