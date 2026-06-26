# Architecture

The factory, in detail. See [`AGENTS.md`](../AGENTS.md) for the orientation and [`DECISIONS.md`](../DECISIONS.md)
for rationale. The schemas in `schemas/` are the single source of truth for data shapes; this doc narrates them.

## Pipeline

```
problems/<topic>/*.problem.toml ─┐
reference/formulas/*.formula.toml ┼─►  SymPy producer (uv, LOCAL)  ─►  derived/  (committed, schema-valid)
                                 ─┘                                        Astro + Svelte player (steps JSON)
```

Two entry points into the same producer package:
- `build-problems` → reads `problems/**/*.problem.toml`, emits `derived/<topic>/<slug>.solution.json` and any
  static `derived/assets/graphs/*.svg`.
- `build-reference` → reads `reference/formulas/*.formula.toml`, emits `derived/reference/formulas.json` and
  `derived/reference/concept-graph.json` (with a frozen force layout).

The producer **refuses to emit** an object whose equivalence proof or unit check fails. That is the local
"verification breaks the build" (ADR-0010); CI re-gates the committed output with Node-only checks.

## Producer module map (`producer/src/quadrature_producer/`)

| Module | Responsibility |
|---|---|
| `__init__.py` | `BuildError` — a loud, named build failure (must identify the problem/step). |
| `dims.py` | Dimensional homogeneity via `sympy.physics.units` (SI 7-vector). Ported from Mechanic. A non-homogeneous expression fails the build. |
| `prove.py` | `tiered_zero` — prove an expression is identically zero (`simplify` → `equals` → `exp`-rewrite → high-precision numeric sampling). Ported from Mechanic's `verify.py`. The algebra=calculus proof runs through this. |
| `kinematics.py` | The physics model: builds `a(t)`, `v(t)=∫a dt`, `x(t)=∫v dt` symbolically and the constant-`a` algebra relations. |
| `solve.py` | Algebra register: solve the kinematic relations + ICs for the requested unknowns (time-to-apex, max height, flight time, impact velocity). Produces stepped algebra. |
| `derive.py` | Calculus register: the stepped `a→v→x` derivation, with the algebra formula shown *emerging* from `∫v dt`. |
| `emit.py` | Closed-form export to JS-evaluable text (`jscode` + `cse` + auto-guards) **and** high-precision sample points (the parity oracle). Ported from Mechanic's `emit_js.py`. |
| `graph.py` | Matplotlib stacked x–t/v–t/a–t SVG for static graphs; sample arrays for the schema. |
| `reference.py` | Formula-reference producer: unit check + derivation verification (e.g. `diff(x,t)==v`), LaTeX generated from the SymPy expr, typed edges, and the frozen concept-graph layout. |
| `build.py` | Orchestrators `build_problems()` / `build_reference()` + the `build-problems` / `build-reference` console entry points. Validates output against the JSON schemas before writing. |

## The solution object (`schemas/solution.schema.json`)

One validated object per scenario (brief §6). Shape (see the schema for the contract):

- `id`, `title`, `scenario` — identity + the question.
- `regime` (1|2|3) — which algebra↔calculus relationship this is (ADR-0006).
- `constants` — house constants in play (`{ "g": -10 }`).
- `assumptions[]` — author-asserted model assumptions (`{ claim, kind:"model" }`); drives the faithful-model
  badge; **never** referenced inside the derivation record.
- `algebra` — `{ steps[], result{} }`: the stepped algebra solution + named results.
- `calculus` — `{ steps[] }`: the stepped `a→v→x` derivation, with the algebra formula emerging.
- `equivalence_proof` — `{ checked_by:"sympy", holds:true, detail }`: the proof that algebra == calculus.
- `units_check` — `{ checked_by:"sympy", holds:true }`.
- `graphs[]` — each: `kind:"stack"`, `mode:"static"|"interactive"`, `series` (sampled t/x/v/a),
  `svg` (for static), `closed_form` + `params` (for interactive), `annotate[]`.
- `misconception` — `{ claim, refuted_by }`: the wrong belief and what kills it.
- `formulas_used[]` — ids linking into the reference.

## The closed-form contract (interactivity without Python)

For `mode:"interactive"` graphs the producer emits `closed_form` as JS-evaluable strings (e.g.
`x: "x0 + v0*t - 5*t**2"`) plus `params` ranges. The player evaluates these in JS as sliders move — no SymPy
and no Matplotlib in the browser. `check-parity.mjs` re-evaluates the exported form at the embedded
`series` sample points and fails on relative error > 1e-9, so the JS the browser runs is proven to reproduce
SymPy's numbers (ADR-0010).

## The reference + concept graph (`schemas/formula.schema.json`, `concept-graph.schema.json`)

A formula node carries its rendered LaTeX **and** the SymPy expr it came from (no transcription typos), its
dimensional-consistency check, its variables (each with units), its assumptions/domain-of-validity, its
derivation with the relationship SymPy-verified, its algebra/calculus dual, the graph that visualizes it, and
the lessons that use it. The concept graph's nodes are formulas/quantities; edges are **typed**
(`derived-from`, `integral-of`/`derivative-of`, `special-case-of`, `assumes`, `related-to`) and color-coded by
domain. Layout is computed deterministically by the producer and frozen into the JSON (ADR-0008).

## Rendering

KaTeX renders all math at build time (in Astro components / from the emitted LaTeX). `check-katex.mjs` proves
every LaTeX string in the derived JSON renders before the site builds. The player islands
(`SolutionPlayer`, `GraphStack`, `ConceptGraph`) are dumb steppers/renderers over the committed JSON.

## Build gates (`scripts/validate/`, Node — run in CI)

| Gate | Checks |
|---|---|
| `validate-solutions.mjs` | Ajv schema + honesty cross-checks (proof `checked_by=="sympy"`; assumptions `kind:"model"`). |
| `validate-reference.mjs` | Ajv schema for `formulas.json` + `concept-graph.json`; edge endpoints resolve; edge types valid. |
| `check-parity.mjs` | JS closed form reproduces the SymPy `series` sample points (rel. err ≤ 1e-9). |
| `check-katex.mjs` | Every LaTeX string renders via `katex.renderToString`. |
| `scan-text.mjs` | No course/exam/standards-body terms in shipped text. |
