// Build-time view prep: deep-render LaTeX to HTML so the player islands receive ready-to-display HTML and
// never ship KaTeX to the browser. Two kinds of math:
//   - display equations (the `latex` fields)            -> tex()    -> *Html
//   - inline math inside prose/claims/labels ($...$)    -> inline() -> *Html
import { inline, tex } from "./katex.js";

// Units are stored in SymPy-parseable source form (`m/s**2`, `N*m**2/C**2`); prettify for DISPLAY only —
// `**n` → Unicode superscript, `*` → middle dot. (Do NOT route units through inline()/emphasize(): the `**`
// would be mangled into <strong>.) Keep the source form internally so the producer/units checker still parses it.
const SUP = { "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹", "-": "⁻" };
export function prettyUnit(u) {
  if (!u) return u;
  return String(u)
    .replace(/\*\*(-?\d+)/g, (_, n) => [...n].map((c) => SUP[c] ?? c).join(""))
    .replace(/\*/g, "·");
}

const step = (st) => ({
  ...st,
  labelHtml: inline(st.label),
  latexHtml: tex(st.latex),
  proseHtml: inline(st.prose),
});

export function renderSolution(sol) {
  const s = structuredClone(sol);
  s.scenarioHtml = inline(s.scenario);
  // The player renders scenarioHtml, never the raw scenario; drop the raw copy so authoring markup (the
  // adjacent formula-id tags, $…$) never ships in the island's hydration props (ADR-0030). meta description
  // is built from the original prop in [slug].astro, not from this view.
  delete s.scenario;
  s.assumptions = (s.assumptions ?? []).map((a) => ({ ...a, claimHtml: inline(a.claim) }));

  s.algebra.steps = s.algebra.steps.map(step);
  s.calculus.steps = s.calculus.steps.map(step);

  for (const k of Object.keys(s.algebra.result)) {
    const r = s.algebra.result[k];
    r.labelHtml = inline(r.label);
    r.unit = prettyUnit(r.unit);
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
  if (s.practice) {
    s.practice = s.practice.map((q) => ({
      ...q,
      promptHtml: inline(q.prompt),
      asksHtml: inline(q.asks),
      answer: { ...q.answer, unit: prettyUnit(q.answer.unit), symbolicHtml: q.answer.symbolic_latex ? tex(q.answer.symbolic_latex, false) : null },
      choices: q.choices.map((c) => ({
        ...c,
        displayHtml: inline(c.display),
        misconceptionHtml: c.misconception ? inline(c.misconception) : null,
      })),
      algebra_steps: (q.algebra_steps ?? []).map(step),
      calculus_steps: (q.calculus_steps ?? []).map(step),
    }));
  }
  return s;
}

export function renderFormula(f) {
  return { ...f, latexHtml: tex(f.latex), nameHtml: inline(f.name) };
}
