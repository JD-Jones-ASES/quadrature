// check-parity.mjs — the parity oracle, and CI's verification hook without Python (ADR-0010).
// For every interactive/closed-form graph, re-evaluate the exported JS closed form at the embedded
// SymPy sample points (series). The values the BROWSER will compute must reproduce SymPy's values
// within tolerance — so the JS that drives the sliders is proven to match the symbolic math.
// Fails loud (exit 1).

import { readdirSync, statSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, relative, join } from "node:path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const DERIVED = resolve(ROOT, "derived");
const ATOL = 1e-6;
const RTOL = 1e-9;

const errors = [];
const fail = (m) => errors.push(m);

function walk(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else if (name.endsWith(".solution.json")) out.push(p);
  }
  return out;
}

function compile(expr, params) {
  // Controlled, build-time-only eval of our own generated jscode (Math.* is available globally).
  return new Function(...params, `"use strict"; return (${expr});`);
}

let count = 0;
function checkUnit(label, closedForm, params, series, paramValue, axisKey = "t") {
  // The axis is t for the x–t/v–t/a–t stack, u for the area instrument (ADR-0014). rest = the value
  // series keyed by the closed-form names (x/v/a, or f/g).
  const axis = series[axisKey];
  const rest = { ...series };
  delete rest[axisKey];
  delete rest[axisKey + "_max"];
  for (const [name, expr] of Object.entries(closedForm)) {
    if (!(name in rest)) continue;
    let fn;
    try {
      fn = compile(expr, params);
    } catch (e) {
      fail(`${label}.closed_form.${name}: cannot compile '${expr}' — ${e.message}`);
      continue;
    }
    const expected = rest[name];
    for (let i = 0; i < axis.length; i++) {
      const args = params.map((p) => (p === axisKey ? axis[i] : paramValue(p)));
      if (args.some((a) => a === undefined)) {
        fail(`${label}.${name}: no value for a closed_form parameter`);
        break;
      }
      const got = fn(...args);
      const want = expected[i];
      if (Math.abs(got - want) > ATOL + RTOL * Math.abs(want)) {
        fail(`${label}.${name}[${i}] (t=${t[i]}): JS ${got} vs SymPy ${want} (Δ=${Math.abs(got - want).toExponential(2)})`);
        break;
      }
      count++;
    }
  }
}

for (const file of walk(DERIVED).sort()) {
  const rel = relative(ROOT, file).replace(/\\/g, "/");
  const data = JSON.parse(readFileSync(file, "utf8"));
  const ic = data.initial_conditions ?? {};
  data.graphs.forEach((g, gi) => {
    const axisKey = g.series?.u !== undefined ? "u" : "t";
    if (g.closed_form && g.series)
      checkUnit(`${rel} graphs[${gi}]`, g.closed_form, g.closed_form_params, g.series,
                (p) => ic[p] ?? g.params?.[p]?.default, axisKey);
    if (g.frames)
      g.frames.forEach((fr, fi) => {
        // numerical (no-closed-form) frames — e.g. the quadratic-drag trajectory — carry only sample points;
        // they are verified by the accuracy gate, not the closed-form parity oracle.
        if (!fr.closed_form) return;
        checkUnit(`${rel} graphs[${gi}].frames[${fi}]`, fr.closed_form, fr.closed_form_params, fr.series,
                  () => undefined);
      });
  });

  // practice answers (ADR-0022): re-assert the producer's invariant without Python — every answer and choice
  // value is finite, and every distractor is distinct from the correct answer.
  (data.practice ?? []).forEach((q) => {
    const a = q.answer.value;
    if (!Number.isFinite(a)) fail(`${rel} practice '${q.id}': answer value not finite`);
    q.choices.forEach((c, ci) => {
      if (!Number.isFinite(c.value)) fail(`${rel} practice '${q.id}' choice[${ci}]: value not finite`);
      if (c.correct !== true && Math.abs(c.value - a) <= ATOL + RTOL * Math.abs(a))
        fail(`${rel} practice '${q.id}' choice[${ci}]: distractor ${c.value} collides with answer ${a}`);
    });
    count++;
  });
}

if (errors.length) {
  console.error(`\nPARITY CHECK FAILED (${errors.length}):`);
  for (const e of errors) console.error("  - " + e);
  process.exit(1);
}
console.log(`OK: ${count} closed-form sample(s) match SymPy within ${ATOL}+${RTOL}·|v|.`);
