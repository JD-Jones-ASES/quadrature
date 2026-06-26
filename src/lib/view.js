// Build-time view prep: deep-render LaTeX to HTML so the player islands receive ready-to-display HTML and
// never ship KaTeX to the browser. Two kinds of math:
//   - display equations (the `latex` fields)            -> tex()    -> *Html
//   - inline math inside prose/claims/labels ($...$)    -> inline() -> *Html
import { inline, tex } from "./katex.js";

const step = (st) => ({
  ...st,
  labelHtml: inline(st.label),
  latexHtml: tex(st.latex),
  proseHtml: inline(st.prose),
});

export function renderSolution(sol) {
  const s = structuredClone(sol);
  s.scenarioHtml = inline(s.scenario);
  s.assumptions = (s.assumptions ?? []).map((a) => ({ ...a, claimHtml: inline(a.claim) }));

  s.algebra.steps = s.algebra.steps.map(step);
  s.calculus.steps = s.calculus.steps.map(step);

  for (const k of Object.keys(s.algebra.result)) {
    const r = s.algebra.result[k];
    r.labelHtml = inline(r.label);
    if (r.symbolic_latex) r.symbolicHtml = tex(r.symbolic_latex, false);
  }

  s.proof.headingHtml = inline(s.proof.heading);
  s.proof.detailHtml = inline(s.proof.detail);
  s.proof.checks = s.proof.checks.map((c) => ({ ...c, claimHtml: inline(c.claim) }));

  if (s.misconception) {
    s.misconception.claimHtml = inline(s.misconception.claim);
    s.misconception.refutedHtml = inline(s.misconception.refuted_by);
  }
  if (s.sign_analysis) {
    s.sign_analysis.ruleHtml = inline(s.sign_analysis.rule);
    s.sign_analysis.segments = s.sign_analysis.segments.map((g) => ({ ...g, stateHtml: inline(g.state) }));
  }
  return s;
}

export function renderFormula(f) {
  return { ...f, latexHtml: tex(f.latex), nameHtml: inline(f.name) };
}
