// check-prose-links.mjs — a dangling in-prose formula link breaks the build (ADR-0030).
//
// Authored prose may tag an inline-math span with a reference formula id, written adjacent: `$\tau = RC$@{em-rc-charge}`.
// inline() (src/lib/katex.js) turns the tag into a link + hover preview to that formula's reference entry. The
// mapping is AUTHORED, so a typo'd or stale id would silently produce a dead link. This gate scans the committed
// solution JSON (authored lesson prose) and the authored Astro pages for `@{id}` tokens and FAILS THE BUILD if any
// id is not a real formula in formulas.json. Runs over committed output, so CI enforces it (CI runs no Python).
// The `@{` anchor never matches Astro/JS `${...}` interpolation.

import { readdirSync, statSync, readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, relative, join } from "node:path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const FORMULAS = resolve(ROOT, "derived/reference/formulas.json");
// Two authored forms of a formula link: the `$…$@{id}` prose tag (interpreted by inline()) and a hand-written
// `data-fid="id"` anchor (used where prose is built directly in Astro, e.g. the guide's tex() spans). Both must
// resolve to a real formula. The `@{` / quoted-attribute anchors never match Astro/JS `${…}` interpolation.
const PATTERNS = [/@\{([a-z0-9-]+)\}/g, /data-fid="([a-z0-9-]+)"/g];

if (!existsSync(FORMULAS)) {
  console.error(`PROSE-LINK CHECK FAILED: ${FORMULAS} not found — run \`npm run produce\` first.`);
  process.exit(1);
}
const validIds = new Set(JSON.parse(readFileSync(FORMULAS, "utf8")).formulas.map((f) => f.id));

function walk(dir, ext) {
  const out = [];
  if (!existsSync(dir)) return out;
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...walk(p, ext));
    else if (name.endsWith(ext)) out.push(p);
  }
  return out;
}

const files = [
  ...walk(resolve(ROOT, "derived"), ".solution.json"),
  ...walk(resolve(ROOT, "src/pages"), ".astro"),
];

const errors = [];
let tokens = 0;
for (const file of files) {
  const rel = relative(ROOT, file).replace(/\\/g, "/");
  const lines = readFileSync(file, "utf8").split(/\r?\n/);
  lines.forEach((line, i) => {
    for (const pat of PATTERNS) {
      for (const m of line.matchAll(pat)) {
        tokens++;
        if (!validIds.has(m[1])) {
          errors.push(`${rel}:${i + 1}  unknown formula id "${m[1]}"  — must match a reference/formulas/*.formula.toml id`);
        }
      }
    }
  });
}

if (errors.length) {
  console.error(`\nPROSE-LINK CHECK FAILED (${errors.length} dangling token(s)):`);
  for (const e of errors) console.error("  - " + e);
  process.exit(1);
}
console.log(`OK: ${tokens} in-prose formula token(s) all resolve to a known formula.`);
