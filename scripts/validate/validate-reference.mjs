// validate-reference.mjs — gate for the formula reference + concept graph. Validates
// derived/reference/formulas.json and concept-graph.json against their schemas, then checks the
// graph is well-formed: every node id is a known formula, every edge endpoint resolves, and every
// formula declaring a derivation was machine-verified. Fails loud (exit 1).

import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, join } from "node:path";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const ajv = new Ajv({ allErrors: true });
addFormats(ajv);

const errors = [];
const fail = (m) => errors.push(m);

const formulasPath = resolve(ROOT, "derived/reference/formulas.json");
const graphPath = resolve(ROOT, "derived/reference/concept-graph.json");
if (!existsSync(formulasPath) || !existsSync(graphPath)) {
  console.error("reference not built — run `npm run produce` first");
  process.exit(1);
}

const formulasSchema = JSON.parse(readFileSync(resolve(ROOT, "schemas/formula.schema.json"), "utf8"));
const graphSchema = JSON.parse(readFileSync(resolve(ROOT, "schemas/concept-graph.schema.json"), "utf8"));
const validateFormulas = ajv.compile(formulasSchema);
const validateGraph = ajv.compile(graphSchema);

const formulas = JSON.parse(readFileSync(formulasPath, "utf8"));
const graph = JSON.parse(readFileSync(graphPath, "utf8"));

if (!validateFormulas(formulas)) for (const e of validateFormulas.errors) fail(`formulas.json${e.instancePath} ${e.message}`);
if (!validateGraph(graph)) for (const e of validateGraph.errors) fail(`concept-graph.json${e.instancePath} ${e.message}`);

if (errors.length === 0) {
  const fids = new Set(formulas.formulas.map((f) => f.id));
  // node ids are formulas
  for (const n of graph.nodes) if (!fids.has(n.id)) fail(`concept-graph node '${n.id}' is not a known formula`);
  // edge endpoints resolve
  const nodeIds = new Set(graph.nodes.map((n) => n.id));
  for (const e of graph.edges) {
    if (!nodeIds.has(e.source)) fail(`edge source '${e.source}' is not a node`);
    if (!nodeIds.has(e.target)) fail(`edge target '${e.target}' is not a node`);
  }
  // declared derivations were verified
  for (const f of formulas.formulas)
    if (f.derivation && f.verified.derivation !== true)
      fail(`formula '${f.id}' declares a derivation but verified.derivation is not true`);
  // every formula.lessons entry names a real lesson ROUTE slug (not the problem id) — otherwise the
  // reference's "used in" link renders as dead plain text instead of a link.
  const slugs = new Set();
  const walk = (d) => { for (const n of readdirSync(d)) { const p = join(d, n); statSync(p).isDirectory() ? walk(p) : n.endsWith(".solution.json") && slugs.add(JSON.parse(readFileSync(p, "utf8")).slug); } };
  walk(resolve(ROOT, "derived"));
  for (const f of formulas.formulas)
    for (const slug of f.lessons ?? [])
      if (!slugs.has(slug)) fail(`formula '${f.id}' lists lesson '${slug}' which is not a real lesson slug (use the solution's route slug, not the problem id)`);
}

if (errors.length) {
  console.error(`\nREFERENCE VALIDATION FAILED (${errors.length}):`);
  for (const e of errors) console.error("  - " + e);
  process.exit(1);
}
console.log(`OK: ${formulas.formulas.length} formula(s), ${graph.nodes.length} node(s), ${graph.edges.length} edge(s) valid.`);
