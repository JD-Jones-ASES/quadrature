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

// inline math: every $...$ segment inside a prose/claim/label string must render too
function tryInline(s, where) {
  if (!s) return;
  for (const p of String(s).split(/(\$[^$]+\$)/g)) {
    if (p.length > 2 && p.startsWith("$") && p.endsWith("$")) {
      try {
        katex.renderToString(p.slice(1, -1), { throwOnError: true, displayMode: false });
        count++;
      } catch (e) {
        fail(`${where}: inline math ${JSON.stringify(p)} — ${e.message}`);
      }
    }
  }
}

// solutions: display equations + all inline-math-bearing fields
for (const file of walk(DERIVED, ".solution.json").sort()) {
  const rel = relative(ROOT, file).replace(/\\/g, "/");
  const d = JSON.parse(readFileSync(file, "utf8"));
  tryInline(d.scenario, `${rel} scenario`);
  d.algebra.steps.forEach((s, i) => {
    tryRender(s.latex, `${rel} algebra.steps[${i}]`);
    tryInline(s.label, `${rel} algebra.steps[${i}].label`);
    tryInline(s.prose, `${rel} algebra.steps[${i}].prose`);
  });
  d.calculus.steps.forEach((s, i) => {
    tryRender(s.latex, `${rel} calculus.steps[${i}]`);
    tryInline(s.label, `${rel} calculus.steps[${i}].label`);
    tryInline(s.prose, `${rel} calculus.steps[${i}].prose`);
  });
  for (const [k, r] of Object.entries(d.algebra.result)) {
    if (r.symbolic_latex) tryRender(r.symbolic_latex, `${rel} result.${k}`);
    tryInline(r.label, `${rel} result.${k}.label`);
  }
  tryInline(d.proof.heading, `${rel} proof.heading`);
  tryInline(d.proof.detail, `${rel} proof.detail`);
  d.proof.checks.forEach((c, i) => tryInline(c.claim, `${rel} proof.checks[${i}]`));
  if (d.misconception) {
    tryInline(d.misconception.claim, `${rel} misconception.claim`);
    tryInline(d.misconception.refuted_by, `${rel} misconception.refuted_by`);
  }
  if (d.sign_analysis) {
    tryInline(d.sign_analysis.rule, `${rel} sign_analysis.rule`);
    d.sign_analysis.segments.forEach((g, i) => tryInline(g.state, `${rel} sign_analysis.segments[${i}]`));
  }
  // practice questions (ADR-0022): prompts, the answer's symbolic form, each choice's misconception, and the
  // reused algebra/calculus step-throughs must all render.
  (d.practice ?? []).forEach((q, qi) => {
    tryInline(q.prompt, `${rel} practice[${qi}].prompt`);
    tryInline(q.asks, `${rel} practice[${qi}].asks`);
    if (q.answer.symbolic_latex) tryRender(q.answer.symbolic_latex, `${rel} practice[${qi}].answer`);
    q.choices.forEach((c, ci) => {
      tryInline(c.display, `${rel} practice[${qi}].choices[${ci}].display`);
      tryInline(c.misconception, `${rel} practice[${qi}].choices[${ci}].misconception`);
    });
    [["algebra_steps", q.algebra_steps], ["calculus_steps", q.calculus_steps]].forEach(([key, steps]) => {
      (steps ?? []).forEach((s, si) => {
        tryRender(s.latex, `${rel} practice[${qi}].${key}[${si}]`);
        tryInline(s.label, `${rel} practice[${qi}].${key}[${si}].label`);
        tryInline(s.prose, `${rel} practice[${qi}].${key}[${si}].prose`);
      });
    });
  });
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
