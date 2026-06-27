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
| `models/` | The model registry — one module per scenario type, each `build(spec) -> Scenario`. Temporal-stack models: `constant_accel` (regime 1, `equivalence`), `shm` / `linear_drag` / `damped_shm` (regime 2, `governing`). Area-instrument models: `work_energy` / `pv_work` (proof kind `integral`, carry an `AreaPlot`). Trajectory models: `projectile` (drag-free is exact/`equivalence`; quadratic drag is numerically integrated, `governing`). `base.py` holds the `Scenario`, `AreaPlot`, and `TrajectoryPlot` contracts. |
| `kinematics.py` | The constant-accel physics: builds `a(t)`, `v(t)=∫a dt`, `x(t)=∫v dt` symbolically and the constant-`a` algebra relations. |
| `solve.py` | Algebra register: solve the kinematic relations + ICs for the requested unknowns (time-to-apex, max height, flight time, impact velocity). Produces stepped algebra. |
| `derive.py` | Calculus register: the stepped `a→v→x` derivation, with the algebra formula shown *emerging* from `∫v dt`. |
| `emit.py` | Closed-form export to JS-evaluable text (`jscode`) **and** high-precision sample points (the parity oracle). Two paths: the temporal stack (`x/v/a` over `t`) and the area instrument (`f/g` over the canonical axis `u` — the model's axis symbol is normalized to `u`). Ported from Mechanic's `emit_js.py`. |
| `graph.py` | Matplotlib static SVGs: `render_stack` (x–t/v–t/a–t), `render_area` (the integrand/accumulated figure), and `render_trajectory` (the projectile path y vs x, with the drag-free parabola overlaid on the drag case). |
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
- `proof` — `{ kind, heading, checked_by:"sympy", holds:true, detail, checks[] }`: the shown proof.
  `kind` is `equivalence` (regime-1 algebra==calculus), `governing` (regime-2 ODE back-substitution, ADR-0013),
  or `integral` (the area instrument: FTC slope, area=integral, memorized-result-falls-out, ADR-0014).
- `units_check` — `{ checked_by:"sympy", holds:true }`.
- `graphs[]` — one of six instruments: the **temporal stack** (`kind:"stack"`, `series` of `t/x/v/a`, or N
  arbitrary panels, ADR-0021), the **area instrument** (`kind:"area"`, `series` of `u/f/g`, a `cursor`), the
  **trajectory** (`kind:"trajectory"`, `series` of `t/x/y`; drag-free `interactive`, quadratic drag `sampled`
  `frames` + a `reference`), the **energy bars** (`kind:"energy"`, `u/ke/pe`), the **collision bars**
  (`kind:"collision"`, before/after over a restitution cursor), and the **standing-wave** spatial viewer
  (`kind:"standing"`, ADR-0023 — `series` of `u/y` with an integer mode slider and a `modes[]` harmonic table).
  Each carries `svg` (static poster), and where a closed form exists `closed_form` + `closed_form_params` (+
  `params` when interactive), plus `annotate[]`.
- `misconception` — `{ claim, refuted_by }`: the wrong belief and what kills it.
- `formulas_used[]` — ids linking into the reference.
- `practice[]` (optional, ADR-0022) — "solve it three ways" questions. Each `{ id, asks, prompt, answer, choices[]
  }` plus optional `algebra_steps[]`/`calculus_steps[]` (reused `$defs/step` from the lesson's registers). The
  `answer` is a verified result (or a SymPy expression) and each `choice` is the answer or a distractor
  *machine-derived from a named misconception* and proven finite + distinct from the answer at build time
  (`practice.py`, re-checked by `check-parity.mjs`). The player reveals; it computes and stores nothing.

## The closed-form contract (interactivity without Python)

For `mode:"interactive"` graphs the producer emits `closed_form` as JS-evaluable strings (e.g.
`x: "x0 + v0*t - 5*t**2"`) plus `params` ranges. The player evaluates these in JS as sliders move — no SymPy
and no Matplotlib in the browser. `check-parity.mjs` re-evaluates the exported form at the embedded
`series` sample points and fails on relative error > 1e-9, so the JS the browser runs is proven to reproduce
SymPy's numbers (ADR-0010). The gate is axis-agnostic: it reads the axis key (`t` for the stack, `u` for the
area instrument) from the series and resolves every other closed-form param from `params`/initial conditions.

## The integral instrument — "area = integral" off the time axis (ADR-0014)

The stacked x–t/v–t/a–t graph is one instance of a more general pivot: the *slope* of one curve is the value
of another, and the *area* under one is the change in another. An **area graph** (`kind:"area"`) carries that
pivot on any axis `u` (position, volume, …): an integrand `f(u)` and its accumulated integral
`g(u) = ∫_{u0}^{u} f du`. The shaded area under `f` up to a draggable **cursor** *is* `g`; the slope of `g`
*is* `f`. A model produces one by returning a `Scenario` with the temporal fields `None` and an `AreaPlot`
set (`models/base.py`). The proof kind is `integral`: `g'(u)=f`, `g=∫f du`, the memorized result falls out of
the integral, and the constant-integrand case collapses to a rectangle (the regime-1 quadrature, on the work
axis). The static poster is `render_area`; the island is `AreaPlot.svelte`. Worked examples: `work_energy`
(`∫F dx → ½mv²`) and `pv_work` (`∫P dV → nRT ln(V₂/V₁)`) — the same instrument on two different axes.

## The trajectory instrument — 2D motion, exact and numerical (ADR-0015)

Projectile motion is two independent 1D motions superposed, drawn as the path y vs x (`kind:"trajectory"`,
carried by a `TrajectoryPlot`). **Drag-free** is exact: x(t)=v₀cosθ·t and y(t)=v₀sinθ·t+½gt² are polynomials,
so the graph is `interactive` (launch-angle/speed sliders, parity-verified), and the memorized range/height/
flight-time formulas fall out of the component integrals (proof `equivalence`, regime 1). **Quadratic drag**
(m v̇=mg−b|v|v) has no closed form: the producer integrates it by fixed-step RK4 and ships `frames` of sample
points the slider snaps between (over the drag coefficient), with the drag-free parabola as a `reference`
overlay. Its verification is the ADR-0010 split for a numerical solution — the producer refuses to emit unless
the path is **RK4-converged** (halving the step moves the range < 1 mm), **satisfies the equation-of-motion
residual**, and **recovers the exact parabola at b=0**; `check-trajectory.mjs` re-gates the committed points in
CI (structure + the b=0-parabola cross-check + range monotonic in drag). This resolves the ADR-0012 parked
question for its motivating case.

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
(`SolutionPlayer`, `GraphStack` for the temporal stack, `AreaPlot` for the integral instrument, `Trajectory`
for the 2D path, `ConceptGraph`) are dumb steppers/renderers over the committed JSON.

## Build gates (`scripts/validate/`, Node — run in CI)

| Gate | Checks |
|---|---|
| `validate-solutions.mjs` | Ajv schema + honesty cross-checks (proof `checked_by=="sympy"`; assumptions `kind:"model"`). |
| `validate-reference.mjs` | Ajv schema for `formulas.json` + `concept-graph.json`; edge endpoints resolve; edge types valid. |
| `check-parity.mjs` | JS closed form reproduces the SymPy `series` sample points (rel. err ≤ 1e-9). |
| `check-trajectory.mjs` | Numerically-integrated paths (no closed form): committed points are structurally sound, the b=0 frame matches the exact parabola, and range is monotonic in drag (ADR-0015). |
| `check-katex.mjs` | Every LaTeX string renders via `katex.renderToString`. |
| `scan-text.mjs` | No course/exam/standards-body terms in shipped text. |
