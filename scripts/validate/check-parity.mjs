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
for (const file of walk(DERIVED).sort()) {
  const rel = relative(ROOT, file).replace(/\\/g, "/");
  const data = JSON.parse(readFileSync(file, "utf8"));
  const ic = data.initial_conditions ?? {};
  data.graphs.forEach((g, gi) => {
    if (!g.closed_form || !g.series) return;
    const params = g.closed_form_params;
    const { t, t_max, ...rest } = g.series; // rest = {x, v, a}
    for (const [name, expr] of Object.entries(g.closed_form)) {
      if (!(name in rest)) continue;
      let fn;
      try {
        fn = compile(expr, params);
      } catch (e) {
        fail(`${rel} graphs[${gi}].closed_form.${name}: cannot compile '${expr}' — ${e.message}`);
        continue;
      }
      const expected = rest[name];
      for (let i = 0; i < t.length; i++) {
        const args = params.map((p) => (p === "t" ? t[i] : (ic[p] ?? g.params?.[p]?.default)));
        if (args.some((a) => a === undefined)) {
          fail(`${rel} graphs[${gi}].${name}: no value for a closed_form parameter`);
          break;
        }
        const got = fn(...args);
        const want = expected[i];
        const diff = Math.abs(got - want);
        if (diff > ATOL + RTOL * Math.abs(want)) {
          fail(`${rel} graphs[${gi}].${name}[${i}] (t=${t[i]}): JS ${got} vs SymPy ${want} (Δ=${diff.toExponential(2)})`);
          break;
        }
        count++;
      }
    }
  });
}

if (errors.length) {
  console.error(`\nPARITY CHECK FAILED (${errors.length}):`);
  for (const e of errors) console.error("  - " + e);
  process.exit(1);
}
console.log(`OK: ${count} closed-form sample(s) match SymPy within ${ATOL}+${RTOL}·|v|.`);
