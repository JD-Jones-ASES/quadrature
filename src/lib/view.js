// Build-time view prep: deep-render every LaTeX string in a solution / formula to HTML, so the player
// islands receive ready-to-display HTML and never ship KaTeX to the browser.
import { tex } from "./katex.js";

export function renderSolution(sol) {
  const s = structuredClone(sol);
  s.algebra.steps = s.algebra.steps.map((st) => ({ ...st, latexHtml: tex(st.latex) }));
  s.calculus.steps = s.calculus.steps.map((st) => ({ ...st, latexHtml: tex(st.latex) }));
  for (const k of Object.keys(s.algebra.result)) {
    const r = s.algebra.result[k];
    if (r.symbolic_latex) r.symbolicHtml = tex(r.symbolic_latex, false);
  }
  return s;
}

export function renderFormula(f) {
  return { ...f, latexHtml: tex(f.latex) };
}
