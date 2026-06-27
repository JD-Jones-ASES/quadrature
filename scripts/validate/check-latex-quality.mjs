// check-latex-quality.mjs — typography breaks the build the way a bad unit does (ADR-0025).
//
// The reference RHS is GENERATED from each formula's verified SymPy expression. SymPy symbols are named in
// plain ASCII so they sympify (`lam`, `dPhidt`, `di`); a presentation layer maps each to a proper glyph
// (λ, dΦ/dt, dᵢ). The semantic gates (parity, units) are blind to typography — they pass identically whether
// a symbol prints as λ or "lam". This gate closes that hole: it fails the build if any generated formula
// LaTeX still contains a leaked multi-character ASCII run that isn't a known function or an author-declared
// glyph. Runs over the committed JSON, so CI enforces it even though CI runs no Python. Fails loud (exit 1).

import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const FORMULAS = resolve(ROOT, "derived/reference/formulas.json");

// LaTeX commands / function names that legitimately spell out >=2 letters.
const KNOWN = new Set([
  "sin", "cos", "tan", "sec", "csc", "cot", "sinh", "cosh", "tanh",
  "exp", "log", "ln", "sqrt", "frac", "arcsin", "arccos", "arctan", "operatorname",
  "cdot", "left", "right", "max", "min",
  "alpha", "beta", "gamma", "delta", "Delta", "epsilon", "varepsilon", "zeta", "eta", "theta",
  "iota", "kappa", "lambda", "nu", "xi", "pi", "rho", "sigma", "tau", "upsilon", "phi", "varphi",
  "chi", "psi", "omega", "Phi", "Omega", "Gamma", "Lambda", "Sigma", "Theta", "Pi", "Psi", "mu",
]);

const errors = [];

function leakedRuns(latex, glyphs) {
  let s = latex;
  // 1) remove author-declared glyph strings first (e.g. \frac{d\Phi}{dt}) so legit notation like the
  //    differential `dt`/`dI` inside them is not mistaken for a leak. Longest-first to avoid partial chews.
  for (const g of [...glyphs].sort((a, b) => b.length - a.length)) {
    if (g) s = s.split(g).join(" ");
  }
  // 2) drop the CONTENTS of \text{…}/\mathrm{…}/\mathcal{…}/\mathbf{…}/\operatorname{…} — author labels.
  s = s.replace(/\\(?:text|mathrm|mathcal|mathbf|operatorname)\s*\{[^{}]*\}/g, " ");
  // 3) turn remaining \command into a bare word so the allowlist can clear it.
  s = s.replace(/\\[A-Za-z]+/g, (m) => " " + m.slice(1) + " ");
  // 4) strip sub/superscript markers and structural punctuation.
  s = s.replace(/[_^{}()\\]/g, " ");
  // 5) anything left that is a run of >=2 ASCII letters and not a known word is a leaked symbol name.
  return [...new Set((s.match(/[A-Za-z]{2,}/g) ?? []).filter((r) => !KNOWN.has(r)))];
}

if (!existsSync(FORMULAS)) {
  console.error(`LATEX-QUALITY CHECK FAILED: ${FORMULAS} not found — run \`npm run produce\` first.`);
  process.exit(1);
}

const { formulas } = JSON.parse(readFileSync(FORMULAS, "utf8"));
let count = 0;
for (const f of formulas) {
  const glyphs = Object.values(f.variables ?? {}).map((v) => v.latex).filter(Boolean);
  const leaks = leakedRuns(f.latex, glyphs);
  if (leaks.length) {
    errors.push(`${f.id}: leaked ASCII symbol name(s) ${JSON.stringify(leaks)} in ${JSON.stringify(f.latex)} ` +
      `— give each leaking symbol a \`latex\` glyph in reference/formulas/${f.id}.formula.toml`);
  }
  count++;
}

if (errors.length) {
  console.error(`\nLATEX-QUALITY CHECK FAILED (${errors.length}):`);
  for (const e of errors) console.error("  - " + e);
  process.exit(1);
}
console.log(`OK: ${count} formula LaTeX string(s) are leak-free.`);
