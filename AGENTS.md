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
.github/workflows/deploy.yml   push to main -> Node gates + astro build -> GitHub Pages (LIVE, auto-deploys)
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
  (`equivalence`, parity-verified); a **numerically-integrated** path (quadratic drag, or an elliptical orbit)
  has no closed form, so the producer integrates by RK4, verifies it (converged + EOM residual / energy +
  angular-momentum conservation + closure), refuses to emit on failure, and ships `frames` re-gated in CI by
  `check-trajectory.mjs` (a `frame:"orbit"` branch handles centred orbits). See `projectile.py` / `orbit.py`.
  **Energy-exchange models** carry an `EnergyPlot` (`ke_expr`/`pe_expr` over a cursor): the KE/PE bars trade
  while the Total stays flat. Wired exactly like the area instrument (parity-verified closed forms, `kind:"energy"`,
  `EnergyBars.svelte`); proof `governing` (the conserved energy is the first integral of `F=ma`). See
  `energy_conservation.py`. To add an energy lesson, copy it: build `ke_expr`, `pe_expr`, the `EnergyPlot`, and
  the conservation proof checks — no schema/gate/frontend change.
  **Collision models** (ADR-0018) carry a `CollisionPlot` — a **before/after** two-state bars instrument
  (`kind:"collision"`, `Collision.svelte`): the closed-form final velocities `v1f`/`v2f` of a 1D two-body
  collision over a **restitution cursor `e`** (0=inelastic … 1=elastic), with `m2`/`v1`/`v2` as `constants`
  (exported as `consts` for the island). The momentum total bar is pinned at every `e`; the KE total bar
  collapses as `e→0`, the gap shaded as lost energy. Parity-verified `v1f,v2f` (axis `u`=e), proof `governing`
  (momentum conservation is the time-integral of Newton's third law). See `collision.py`; a second collision
  lesson is model + spec + test.

**Authoring math.** Display equations use the `latex` field (rendered as a block). Inline math inside any
prose / claim / label / scenario / misconception is written with `$...$` (e.g. `the period $T = 2\pi/\omega$`)
and rendered by KaTeX at build time. The `check:katex` gate validates **both**. Keep modeling-assumption
prose in `$...$` too so it reads crisply.

**Two frontend gotchas when rendering authored text** (both bit twice — check them on any new page/island that
shows authored prose):
- **Run prose through `inline()`** (from `src/lib/katex.js`), don't print it raw. The `check:katex` gate proves
  the strings *render*, but it does **not** check that a given page actually calls the renderer — a page that
  prints `{solution.scenario}` or `{a.claim}` directly will show literal `$…$`. The detail pages go through
  `lib/view.js` (`renderSolution`), which `inline()`s scenario / steps / results / proof / misconception /
  **assumptions**; any *other* surface (e.g. the lessons index) must call `inline()` itself and emit with
  `set:html`.
- **The Astro whitespace gotcha:** prose that wraps a line right before an inline element drops the joining
  space — `…in the\n<a>reference</a>` renders as "thereference". Put `{" "}` before the wrapped element (or keep
  it on the same line). Grep for a word at end-of-line followed by a line starting `<a`/`<strong>`/`<code>`/`{`.

The producer engine should rarely change. If it must, add a physics cross-check in `producer/tests/` and keep
`uv --project producer run pytest` green.

## Current state

See [`ROADMAP.md`](./ROADMAP.md) and the latest [`docs/sessions/`](./docs/sessions/) log. **Phase 0 is
complete and reviewed**; **Phase 1 (mechanics)** is in progress, **Phase 2 (E&M)** is deepening (capacitor,
Coulomb PE, **RC charging**, **line-charge field** + a reference cluster), and **Phase 3 (thermo, fluids, and
now opened modern)** is deepening. The site is **live and public** at https://jd-jones-ases.github.io/quadrature/
(push to `main` auto-deploys). Shipped: **32 lessons** across 12 units — free fall, **projectile (drag-free)**,
**incline with friction** (`a=g(sinθ−μcosθ)`, opens Dynamics), **rotational kinematics**, and the **circular
orbit** (regime 1, trajectory on a centred frame — `v=√(μ/R)`, Kepler's `T²∝R³`); SHM, terminal velocity, the
damped oscillator, **work–energy**, **projectile with quadratic drag**, **impulse–momentum**, **gravitational
potential energy**, **energy in a capacitor**, **electric potential energy**, **RC charging** (the 2-panel
stack — `I` is the slope of `Q`), **the field of a charged rod** (`∫kλ/x² dx`, where algebra runs out)
(regime 2, E&M), **moment of inertia** (`∫r² dm`), **rotational work–energy** (`∫τ dθ → ½Iω²`), **hydrostatic
force on a wall** (`∫ρg w h dh`), **Torricelli / a draining tank** (energy bars, `v=√(2gh)`, opens fluid
dynamics), the **elliptical orbit** (numerical — Kepler's three laws from `r̈=−μr/r³`), **conservation of
energy** (energy bars — path-independent `v=√(2gH)`), **collisions / momentum** (before/after collision bars),
and **radioactive decay** (the N / dN/dt 2-panel stack, `dN/dt=−λN`, opens Modern) (regime 2); **isothermal**,
**adiabatic**, and **isobaric PV-work** (regime 3); **LC oscillation** and **Faraday induction** (the electrical
spring and the AC generator, 2-panel stack); **standing waves** (the spatial-mode instrument — opens Waves &
optics, ADR-0023); and **thin-lens optics** (the ray-diagram instrument — the geometric second register,
ADR-0024) — plus an **82-formula reference spanning all five domains** (mechanics incl.
fluids & rotation, E&M incl. magnetism, thermo, waves & optics, modern) and an 82-node / 125-edge concept graph,
all SymPy-verified. The producer is a model registry (`constant-accel`, `shm`, `linear-drag`, `damped-shm`,
`work-energy`, `pv-work`, `projectile`, `impulse`, `rotation`, `gravity-pe`, `capacitor-energy`, `adiabatic`,
`moment-of-inertia`, `coulomb-pe`, `hydrostatic-force`, `rotational-work`, `orbit`, `energy-conservation`,
`collision`, `rc-charging`, `incline-friction`, `decay`, `torricelli`, `line-charge-field`, `lc-oscillation`,
`isobaric-work`, `faraday-induction`, `standing-wave`, `thin-lens`). The concept-graph
nodes have **clean Unicode labels**, a **domain-clustered layout** (ADR-0020), and pan/zoom + click-select +
drag-to-reposition. **Verified practice (ADR-0022, "solve it three ways")** rides on every lesson; some
regime-3 lessons override the second-register label (`calculus.register_label`, e.g. thin lens → "Ray diagram"),
and authored prose supports `**bold**`/`*italic*` markdown in `inline()` (ADR-0024). **The reference RHS is
still 100% generated from the verified `expr`, but now correctly (ADR-0025): a per-`[variables]` `latex` glyph
feeds `sp.latex(symbol_names=…)` so ASCII names (`lam`/`dPhidt`/`di`) print as λ/dΦ/dt/dᵢ, and a `LatexPrinter`
subclass orders factors/terms by the author's written order (`E=mc²`, `F=qvB`, not SymPy's sort) without ever
rebuilding the expression. A new gate `check-latex-quality.mjs` fails the build on any leaked multi-char ASCII
run — typography breaks the build the way a bad unit does. `kin-a-const` carries a `note` caption framing `a=a`
as the seed of the integral ladder.**

**Frontend rendering (ADR-0019): the interactive graph islands' scoped CSS is delivered via
`svelte({ compilerOptions: { css: "injected" } })` in `astro.config.mjs`.** Without it, Astro only delivers the
*top-level* island's CSS, and *child* graph islands (GraphStack/AreaPlot/Trajectory/EnergyBars/Collision/
StandingWave/Lens) render with default **black** SVG fills — do not remove it. The site declares `color-scheme: light dark` (Base.astro
meta + portal.css) and has a full dark theme; static Matplotlib posters sit on a fixed-light `.svgwrap` figure
card. **Verify graph colors with `getComputedStyle().fill/stroke`, not just DOM geometry** — colors were the one
thing prior paint-checks missed.

Graphs come in seven instruments: the **temporal stack** (`kind:"stack"`, modes `static` | `interactive` |
`sampled`; **generalized to N panels** beyond x/v/a via `Scenario.panels`, ADR-0021 — used by RC charging,
decay, LC, Faraday), the **area/integral instrument** (`kind:"area"`, ADR-0014 — area under `f(u)` = the
accumulated integral `g(u)`, off the time axis), the **2D trajectory instrument** (`kind:"trajectory"`,
ADR-0015 — the path y vs x; drag-free is exact/interactive, quadratic drag is numerically integrated; a centred
`frame:"orbit"` draws closed orbits, ADR-0016), the **energy-exchange bars** (`kind:"energy"`, ADR-0017 — KE/PE
bars that trade as a cursor moves while the Total stays flat; an `EnergyPlot` carrying `ke_expr`/`pe_expr`, wired
like the area instrument), the **before/after collision bars** (`kind:"collision"`, ADR-0018 — momentum bars
equal before/after at every restitution `e`, KE bars equal only when elastic; a `CollisionPlot` carrying the
final velocities `v1f`/`v2f`), the **standing-wave spatial modes** (`kind:"standing"`, ADR-0023 — y(x)=A·sin(nπx/L)
over a discrete integer mode cursor n; nodes pinned as n changes), and the **thin-lens ray diagram**
(`kind:"lens"`, ADR-0024 — a lens with d_o as cursor; the three principal rays are drawn and clipped
to the viewport, and the image flips real↔virtual as d_o crosses f; the **same instrument handles a diverging
lens with f<0** — always virtual/upright/reduced — via sign-general ray directions and computed image-character
prose, no engine change). The last five all reuse the canonical `u` axis, so the **parity oracle re-checks them
with no gate change**.
Proof kinds: `equivalence` (regime 1) · `governing` (regime-2 ODE / numerical motion / a conserved first
integral / a collision conservation law / a wave-equation mode / a thin-lens ray construction) · `integral`
(area instrument).

## Where this might go next (paths for a future session)

Pick a track; each is independent and lands on the proven engine. Resume from the newest session log
([`docs/sessions/2026-06-26.md`](./docs/sessions/), bottom). **Already done** (don't redo): work–energy,
impulse, gravitational PE, **energy in a capacitor**, **electric potential energy** (Coulomb), **moment of
inertia**, **rotational work–energy**, **hydrostatic force on a wall** (all area instrument); projectile
drag-free + quadratic drag and the **circular + elliptical orbit** (trajectory); **conservation of energy**
(energy-bars); rotational kinematics (stack); **isothermal + adiabatic PV-work** (thermo). The **reference now
spans all five domains** (70 formulas: mechanics incl. fluids & rotation, E&M
incl. magnetism, thermo, waves/optics, modern) — breadth-fill track 3 below is largely discharged; what remains
is per-domain *depth* and a couple of small, well-scoped engine extensions, flagged below.

1. **Mechanics breadth that needs a SMALL engine extension** (highest-value next):
   - **Orbits — DONE** (both circular regime-1 + elliptical regime-2, `orbit.py`). The trajectory instrument
     has a centred `frame:"orbit"` (equal-aspect, central body/focus, a producer-supplied `view_half`) in both
     `render_trajectory` and `Trajectory.svelte` (with an interactive *and* a sampled branch). The circular
     case reuses `kind:"trajectory"` + the parity gate; the elliptical case RK4-integrates `r̈=−μr/r³`, verifies
     **energy + angular-momentum conservation + closure** (refusing to emit otherwise), and is re-gated in CI by
     a `check-trajectory.mjs` `frame==="orbit"` branch (closes · encircles the focus once · `e=0` is a circle ·
     equal periods). Kepler's three laws all fall out. (A future polish: animate the satellite around the orbit
     to *show* equal-areas-in-equal-times, rather than stating it.)
   - **Collisions / momentum — DONE** (ADR-0018, `collision.py`, the `kind:"collision"` before/after bars). A 1D
     two-body collision with the **restitution `e` as the cursor**: momentum bars equal before/after at every
     `e`, KE bars equal only when elastic, the lost KE shaded. Proof `governing` (momentum conservation = the
     time-integral of Newton's third law; the KE deficit is `½μ(1−e²)(Δv)²`). New `CollisionPlot` +
     `Collision.svelte` + `render_collision` + `collision_series`/`consts` schema, parity-verified `v1f,v2f`,
     no new gate. A future second collision lesson (head-on with opposite signs, or a 2D oblique collision)
     would be model + spec + test.
2. **More area-instrument lessons (zero engine change — model + spec + test)** — Coulomb PE and rotational work
   are now **done** (`coulomb_pe.py`, `rotational_work.py`); still open: **isobaric** PV-work (the trivial
   rectangle, completes the PV-process trio), and later E&M field integrals (`∫E·dl`, `∫dq/r²`) and a
   continuous-charge field (`∫dq/r²`). Copy `work_energy.py` / `capacitor_energy.py` / `gravity_pe.py` /
   `coulomb_pe.py` / `hydrostatic_force.py` / `moment_of_inertia.py`. **Watch the dimensionless-parameter trap**: a free dimensionless
   slider that lands in a denominator (e.g. `1/(γ−1)`) makes the build-time `check_homogeneous` divide by zero
   when it collapses units — bake such a parameter to its value and slide a *dimensionful* one instead (see
   `adiabatic.py`). Likewise, identities with a `symbol**symbol` power must certify in a *symbolic* tier
   (`simplify`/`conds='none'`); the numeric proof tier exact-evaluates `Rational**Rational` and can `MemoryError`.
3. **Reference breadth into other domains** — *largely done* (28 → 56). Remaining depth: E&M magnetism /
   induction / Gauss, the rest of thermo & optics, nuclear. Pure authored+verified data: add
   `reference/formulas/*.formula.toml` with the right `domain` (it color-codes the concept-graph node, all five
   already supported in the frontend). No engine change.
4. **E&M (Phase 2)** — *opened* (capacitor-energy lesson + the 9-formula E&M cluster: Coulomb, field, potential,
   PE, capacitance, energy, Ohm, power, RC). Next dual-register lessons: an **RC charging** lesson — but the
   temporal stack is hard-wired to three panels (x/v/a); RC is a two-quantity (Q, I) derivative pair, so it
   needs either a 2-panel stack variant or a reframe onto the area instrument. Then magnetism, induction, and a
   continuous-charge field integral (`∫dq/r²`) on the area instrument.
5. **The §8 interlinking backbone** — hover-to-reference from any formula token in a lesson, and formula→lesson
   navigation, so the reference becomes the site's navigational spine (brief §8). Frontend work over the
   existing `formulas.json` + `concept-graph.json` (now 56 nodes — denser, more useful as a spine).

The ADR-0012 parked question (a no-closed-form `sampled` region) is **resolved** (ADR-0015): the
quadratic-drag trajectory is numerically integrated by RK4, each frame producer-verified (converged + EOM
residual + recovers the exact parabola at zero drag) and CI re-gated by `check-trajectory.mjs`, with the
slider snapping between frames over a single parameter. No continuous interpolation-error gate was needed —
the committed sample density only sets drawing smoothness; the physics accuracy is the producer's converged
solution.
