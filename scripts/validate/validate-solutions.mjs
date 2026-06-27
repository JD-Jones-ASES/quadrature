// validate-solutions.mjs — the build gate for shipped solution objects. Validates every committed
// derived/<topic>/<slug>.solution.json against schemas/solution.schema.json, then enforces the honesty
// cross-checks that keep a polished, interactive page from implying a guarantee SymPy never produced:
//   - the equivalence proof must be checked_by "sympy" and hold (every identity true);
//   - the unit check must be checked_by "sympy" and hold;
//   - every assumption is kind "model" (author-asserted, disclosed — never machine-derived);
//   - interactive graphs carry params + a closed form; the file path matches the declared topic/slug.
// Fails loud (exit 1).

import { readdirSync, statSync, readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, relative, join } from "node:path";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const DERIVED = resolve(ROOT, "derived");

const ajv = new Ajv({ allErrors: true });
addFormats(ajv);
const schema = JSON.parse(readFileSync(resolve(ROOT, "schemas/solution.schema.json"), "utf8"));
const validate = ajv.compile(schema);

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

// the reference, if built, lets us check formulas_used resolve
let knownFormulaIds = null;
const formulasPath = resolve(DERIVED, "reference/formulas.json");
if (existsSync(formulasPath)) {
  knownFormulaIds = new Set(JSON.parse(readFileSync(formulasPath, "utf8")).formulas.map((f) => f.id));
}

let files = [];
try {
  files = walk(DERIVED).filter((p) => !p.includes(`${join("reference")}`));
} catch {
  fail(`derived/ not found — run \`npm run produce\` first`);
}
if (files.length === 0 && errors.length === 0) fail("no *.solution.json found under derived/");

const ids = new Map();
for (const file of files.sort()) {
  const rel = relative(ROOT, file).replace(/\\/g, "/");
  let data;
  try {
    data = JSON.parse(readFileSync(file, "utf8"));
  } catch (e) {
    fail(`${rel}: invalid JSON — ${e.message}`);
    continue;
  }
  if (!validate(data)) {
    for (const e of validate.errors) fail(`${rel}${e.instancePath} ${e.message}`);
    continue;
  }

  if (ids.has(data.id)) fail(`${rel}: duplicate id '${data.id}' (also in ${ids.get(data.id)})`);
  else ids.set(data.id, rel);

  // path matches declared topic/slug
  if (!rel.endsWith(`derived/${data.topic}/${data.slug}.solution.json`))
    fail(`${rel}: file path does not match topic/slug '${data.topic}/${data.slug}'`);

  // honesty cross-checks
  if (!(data.proof.checked_by === "sympy" && data.proof.holds === true))
    fail(`${rel}: proof must be checked_by 'sympy' and hold`);
  if (data.proof.checks.some((c) => c.holds !== true))
    fail(`${rel}: a proof check does not hold`);
  if (!(data.units_check.checked_by === "sympy" && data.units_check.holds === true))
    fail(`${rel}: units_check must be checked_by 'sympy' and hold`);
  for (const a of data.assumptions)
    if (a.kind !== "model") fail(`${rel}: assumption '${a.claim}' must be kind 'model'`);

  // graph integrity — axis-agnostic: every value array matches the axis array (t for the stack, u for area)
  const seriesLensOk = (s) => {
    const axis = "u" in s ? s.u : s.t;
    if (!Array.isArray(axis)) return false;
    return Object.values(s).every((v) => !Array.isArray(v) || v.length === axis.length);
  };
  data.graphs.forEach((g, i) => {
    if (g.mode === "interactive" && !g.params)
      fail(`${rel}: graphs[${i}] is interactive but has no params`);
    if (g.mode === "sampled") {
      if (!g.frames?.length) fail(`${rel}: graphs[${i}] is sampled but has no frames`);
      g.frames?.forEach((fr, fi) => {
        if (!seriesLensOk(fr.series)) fail(`${rel}: graphs[${i}].frames[${fi}].series length mismatch`);
      });
    } else if (!seriesLensOk(g.series)) {
      fail(`${rel}: graphs[${i}].series length mismatch (x/v/a vs t)`);
    }
    if (g.svg && !existsSync(resolve(DERIVED, g.svg)))
      fail(`${rel}: graphs[${i}].svg '${g.svg}' not found in derived/`);
  });

  // formulas_used resolve (if the reference is built)
  if (knownFormulaIds)
    for (const fid of data.formulas_used)
      if (!knownFormulaIds.has(fid))
        fail(`${rel}: formulas_used '${fid}' has no reference entry`);

  // practice questions (ADR-0022): unique ids, exactly one correct choice, finite numeric values
  if (data.practice) {
    const pids = new Set();
    for (const q of data.practice) {
      if (pids.has(q.id)) fail(`${rel}: duplicate practice id '${q.id}'`);
      pids.add(q.id);
      const correct = q.choices.filter((c) => c.correct === true);
      if (correct.length !== 1)
        fail(`${rel}: practice '${q.id}' must have exactly one correct choice (has ${correct.length})`);
      if (!Number.isFinite(q.answer.value))
        fail(`${rel}: practice '${q.id}' answer value is not finite`);
      for (const [ci, c] of q.choices.entries())
        if (!Number.isFinite(c.value)) fail(`${rel}: practice '${q.id}' choice[${ci}] value is not finite`);
    }
  }
}

if (errors.length) {
  console.error(`\nSOLUTION VALIDATION FAILED (${errors.length}):`);
  for (const e of errors) console.error("  - " + e);
  process.exit(1);
}
console.log(`OK: ${files.length} solution(s) valid (${ids.size} unique ids).`);
