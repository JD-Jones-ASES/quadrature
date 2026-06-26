# AGENTS.md — what this is & how to work it

Entry point for anyone (human or coding agent) opening this repo cold. Start here, then read
[`ROADMAP.md`](./ROADMAP.md) for where the build is, [`DECISIONS.md`](./DECISIONS.md) for why it is the
way it is, and [`docs/architecture.md`](./docs/architecture.md) for the pipeline in detail.

## What this is

**Quadrature** — a dual **algebra-based / calculus-based** physics course where *the verification system is
the product*. One build-time **SymPy** program is the single source of truth: it solves each scenario in the
algebra register, derives it in the calculus register, **proves the two agree** (`simplify(algebra −
calculus) == 0`), checks every expression is dimensionally homogeneous, and exports a cheap closed form the
browser can evaluate. The learner is never *told* the registers agree — SymPy proves it, and the proof is the
artifact.

**The thesis.** The stacked **x–t / v–t / a–t** motion graph is the pivot between the two registers: the
*slope* of the upper graph is the *value* of the lower; the *area* under the lower is the *change* in the
upper. Slope is the derivative; area is the integral. The constant-acceleration algebra formulas
(`v = v₀ + at`, `x = x₀ + v₀t + ½at²`) are those integrals with the integrand frozen to a constant — they are
**quadratures**: integrals already evaluated.

Be honest about the relationship — it has **three regimes**, and the slogan "algebra is just calculus done" is
only true in the first (see `regime` in the schema and [`docs/regime-map.md`](./docs/regime-map.md)):
1. **Algebra = calculus evaluated** (constant acceleration).
2. **Calculus does what algebra cannot** (non-constant forces: drag, springs, gravitation vs r).
3. **Algebra-only** (fluids, thermo, waves/optics, modern — no calculus-based counterpart).

It is **provider-agnostic**: it must not name any specific course, exam, or standards body. A build gate
enforces this (`scripts/validate/scan-text.mjs`). Public language is "algebra-based physics" /
"calculus-based physics" / topic names. The course-framed founding brief is gitignored (`PROJECT_BRIEF.md`).

## Tech stack

- **Astro 7**, `output: "static"`, `trailingSlash: "always"` — pages in `src/pages/`, chrome in `src/layouts/`
  + `src/components/`. Base path `/quadrature` (preview from `/` with `LOCAL_ROOT=1`).
- **Svelte 5** islands (`src/islands/`, runes), hydrated `client:visible`. The player runs no Python and no
  Matplotlib; interactive graphs evaluate the exported closed form in JS.
- **KaTeX** for math, rendered at build time (a `check:katex` gate proves every string renders).
- **Python 3.14 + SymPy 1.14.0** via **uv** — the producer (`producer/`). Runs locally, never in CI.
- **Matplotlib** renders static graph SVGs at build time (committed under `derived/assets/graphs/`).
- **Ajv** JSON-Schema validation (`schemas/`, draft 2020-12, `additionalProperties:false`). The build fails loud.
- No database, no server, no client-side Python. Generated data is committed.

## Build & run

```bash
npm install                # Node >= 22
npm run prepare:data       # producer -> derived/*.json + SVGs, then ALL gates (run locally)
npm run dev:preview        # local dev server served from / (convenient for previewing)
npm run build              # the Node gates, then astro build -> dist/  (this is what CI runs)

uv --project producer run pytest   # the producer's physics cross-checks (the heart; keep it green)
```

`prepare:data` regenerates the committed `derived/` from `problems/` + `reference/` via the SymPy producer,
then runs the gates. **CI does NOT run Python** — `npm run build` runs the Node gates (schema + parity +
KaTeX + scan) over the committed JSON, then a pure `astro build`. So: edit a problem/formula →
`prepare:data` locally → commit the regenerated `derived/` → push.

## How it works (the factory invariant)

```
problems/<topic>/*.problem.toml ─┐
reference/formulas/*.formula.toml ┼─►  SymPy producer (uv, LOCAL)  ─►  derived/<topic>/*.solution.json
                                 ─┘    solve + derive + PROVE +          derived/reference/formulas.json
                                       unit-check + closed form +        derived/reference/concept-graph.json
                                       sample points + Matplotlib SVG    derived/assets/graphs/*.svg  (COMMITTED)
                                                                              │
                                          Ajv + parity + katex + scan ───────┤  (fail loud)
                                                                              ▼
                                          Astro + Svelte player (steps the JSON; runs no Python/Matplotlib)
```

- **The producer** (`producer/src/quadrature_producer/`) is a pure function from a problem/formula spec to a
  verified, schema-shaped object. It **refuses to emit** any solution whose algebra=calculus proof or unit
  check fails — that is "verification breaks the build" at the source. Module map in
  [`docs/architecture.md`](./docs/architecture.md).
- **The content layer** (`problems/*.problem.toml`, `reference/formulas/*.formula.toml`) is authored: the
  scenario, initial conditions, the **model assumptions** (so the honesty badges are authored, not inferred),
  the unknowns, the graphs, and the static-vs-interactive decision per graph.
- **The player** (`src/islands/`) is a dumb stepper: the four registers (scenario · algebra · calculus ·
  graph), honesty badges, the misconception register, and the graph stack (static SVG or interactive closed
  form). It executes no Python.

## Repo map

```
problems/<topic>/    AUTHORED scenario TOML (ICs, assumptions, unknowns, graphs, misconception, regime)
reference/formulas/  AUTHORED formula entries (+ typed concept-graph edges) — the breadth layer
producer/            the SymPy producer: a uv package; src/quadrature_producer/*.py + tests/
derived/             GENERATED, COMMITTED, schema-valid: solution.json, reference/*.json, assets/graphs/*.svg
schemas/             JSON-Schema contracts (draft 2020-12, additionalProperties:false)
scripts/validate/    Node gates: validate-solutions, validate-reference, check-parity, check-katex, scan-text
src/                 Astro app: pages/, layouts/, components/, islands/ (Svelte), lib/, styles/
docs/                architecture, authoring-problems, authoring-formulas, regime-map, house-conventions, SOURCES, sessions/
.github/workflows/deploy.yml   push to main -> Node gates + astro build -> GitHub Pages (Pages disabled until reviewed)
```

## Honesty model (two axes, non-negotiable)

Carried intact from the sibling portals. Shown to the reader as badges; never mixed in the data.

1. **Machine-derived?** — produced and checked by SymPy: the algebra solve, the calculus derivation, the
   equivalence proof, the unit check, the closed-form export. These are *derived*; the proof detail is shown,
   not asserted.
2. **Faithful physical model?** — the **author-asserted** axis: `g = −10` (a deliberate simplification of
   9.81 for clean arithmetic), "neglect air resistance," "point mass," "frictionless." These are **disclosed,
   not discharged** — the reader can check the math against SymPy but takes the modeling assumptions on the
   same footing as any physics text. Authored in the spec's `assumptions[]` with `kind:"model"`, and they
   **never** appear inside the derivation record.

The **misconception register** is the buggy-first analogue: a documented misconception (e.g. "a = 0 at the
apex") is shown, then refuted by the graph and the math rather than by assertion.

## House conventions (baked in everywhere)

Metric throughout; **g = −10 m/s²**; **up positive** (so g carries its negative sign — a top rigor target).
Sign rigor: an object speeds up exactly when v and a share a sign (`sign(v·a) > 0`). Full notation in
[`docs/house-conventions.md`](./docs/house-conventions.md).

## Deploy

Push to `main` → GitHub Actions runs the Node gates + `astro build` → GitHub Pages. Project base path is
`/quadrature` (the repo is named lowercase `quadrature` so the Pages path matches exactly). The repo is
**public** and Pages is **live** at https://jd-jones-ases.github.io/quadrature/ — every push to `main`
auto-deploys (the deploy fails loud if any gate fails).

## Extending Quadrature

Two independent tracks (decoupled by design — see ADR-0007): **lessons** go deep, the **reference** goes
broad. Adding either touches data, not the engine.

- **A lesson** → author `problems/<topic>/<slug>.problem.toml` (set its `model`), run `npm run prepare:data`.
  The dynamic route `src/pages/lessons/[slug].astro` and the `/lessons/` index pick it up automatically — no
  per-lesson page to write. See [`docs/authoring-problems.md`](./docs/authoring-problems.md).
- **A reference formula** → author `reference/formulas/<id>.formula.toml` (+ its typed edges), run
  `npm run prepare:data`. The reference sheet and concept graph regenerate from SymPy. See
  [`docs/authoring-formulas.md`](./docs/authoring-formulas.md).
- **A new physics model** (e.g. projectile-2D, collisions) → add `producer/src/quadrature_producer/models/
  <name>.py` exposing `build(spec) -> Scenario`, register it in `models/__init__.py`, add a physics
  cross-check in `producer/tests/`. Regime-1 models prove `equivalence`; regime-2 ODE models prove `governing`
  (back-substitute into the equation of motion); **integral / area-instrument models** (ADR-0014) prove
  `integral` (FTC slope, area=integral, the memorized result falls out, constant-integrand→rectangle) and
  return a `Scenario` carrying an `AreaPlot` with the temporal `x/v/a` left `None`. See `models/base.py` for
  the `Scenario` + `AreaPlot` contracts, and `work_energy.py` / `pv_work.py` as worked examples (an `∫F dx`
  and an `∫P dV` lesson on the *same* instrument, different axes — no engine change between them).
  **Trajectory / vector models** (ADR-0015) carry a `TrajectoryPlot`: drag-free is an exact closed-form path
  (`equivalence`, parity-verified); a **numerically-integrated** path (quadratic drag) has no closed form, so
  the producer integrates by RK4, verifies it (converged + EOM residual + recovers the exact case), refuses to
  emit on failure, and ships `frames` re-gated in CI by `check-trajectory.mjs`. See `projectile.py`.

**Authoring math.** Display equations use the `latex` field (rendered as a block). Inline math inside any
prose / claim / label / scenario / misconception is written with `$...$` (e.g. `the period $T = 2\pi/\omega$`)
and rendered by KaTeX at build time. The `check:katex` gate validates **both**. Keep modeling-assumption
prose in `$...$` too so it reads crisply.

The producer engine should rarely change. If it must, add a physics cross-check in `producer/tests/` and keep
`uv --project producer run pytest` green.

## Current state

See [`ROADMAP.md`](./ROADMAP.md) and the latest [`docs/sessions/`](./docs/sessions/) log. **Phase 0 is
complete and reviewed**; **Phase 1 (mechanics)** is in progress and **Phase 3 (thermo) is seeded**. The site
is **live and public** at https://jd-jones-ases.github.io/quadrature/ (push to `main` auto-deploys). Shipped:
11 lessons — free fall, **projectile (drag-free)**, and **rotational kinematics** (regime 1); SHM, terminal
velocity, the damped oscillator, **work–energy**, **projectile with quadratic drag**, **impulse–momentum**,
and **gravitational potential energy** (regime 2); and **isothermal PV-work** (regime 3) — plus a 28-formula
reference (mechanics + two thermo) and concept graph, all SymPy-verified. The producer is a model registry
(`constant-accel`, `shm`, `linear-drag`, `damped-shm`, `work-energy`, `pv-work`, `projectile`, `impulse`,
`rotation`, `gravity-pe`). The concept-graph nodes are click-to-select and drag-to-reposition. The site is
public and auto-deploys on every push to `main`. Graphs come as the **temporal stack** (`kind:"stack"`, modes `static` | `interactive` |
`sampled`), the **area/integral instrument** (`kind:"area"`, ADR-0014 — area under `f(u)` = the accumulated
integral `g(u)`, off the time axis), or the **2D trajectory instrument** (`kind:"trajectory"`, ADR-0015 — the
path y vs x; drag-free is exact/interactive, quadratic drag is numerically integrated). Proof kinds:
`equivalence` (regime 1) · `governing` (regime-2 ODE / numerical motion) · `integral` (area instrument). Pages
stays disabled until the owner publishes.

## Where this might go next (paths for a future session)

Pick a track; each is independent and lands on the proven engine. Resume from the newest session log.

1. **More area-instrument lessons (the cheap downstream of ADR-0014)** — the integral instrument now exists, so
   any "area under a curve = accumulated integral" lesson is just a model + spec + test, no engine change:
   gravitational PE (`∫F dr`), impulse–momentum (`∫F dt`), more thermo PV processes (isobaric, adiabatic), and
   later E&M potential/field integrals (`∫E·dl`, `∫dq/r²`). This is the highest-leverage breadth track.
2. **Reference breadth into other domains** — E&M, the rest of thermo, waves/optics, modern (ADR-0007, toward
   the complete formula sheet). Pure authored+verified data: add `reference/formulas/*.formula.toml` with the
   right `domain` (it color-codes the concept-graph node). No engine change.
3. **More regime-1 / regime-2 mechanics lessons** — energy conservation, collisions/momentum, rotation,
   gravitation/orbits. Reuse an existing model where the physics fits; the trajectory + numerical-RK4 pattern
   (ADR-0015) now covers any new no-closed-form motion (anharmonic oscillators, non-1/r² orbits).
4. **The §8 interlinking backbone** — hover-to-reference from any formula token in a lesson, and formula→lesson
   navigation, so the reference becomes the site's navigational spine (brief §8). Frontend work over the
   existing `formulas.json` + `concept-graph.json`.
5. **Polish / publish prep** — when the owner is ready: enable GitHub Pages, run the deploy, write a `/about`
   page, and do a `/ship`-style validation sweep.

The ADR-0012 parked question (a no-closed-form `sampled` region) is **resolved** (ADR-0015): the
quadratic-drag trajectory is numerically integrated by RK4, each frame producer-verified (converged + EOM
residual + recovers the exact parabola at zero drag) and CI re-gated by `check-trajectory.mjs`, with the
slider snapping between frames over a single parameter. No continuous interpolation-error gate was needed —
the committed sample density only sets drawing smoothness; the physics accuracy is the producer's converged
solution.
