# Authoring a problem (lesson)

A lesson is a `problems/<topic>/<slug>.problem.toml` spec. The producer does the math and emits a verified
`derived/<topic>/<slug>.solution.json`; you never write the solution by hand. The schema is
`schemas/solution.schema.json`; the authoring fields are below. After editing, run `npm run prepare:data`.

## Spec fields

```toml
id = "freefall-throw-up"          # stable, kebab-case, unique
title = "A ball thrown straight up"
topic = "freefall"                # directory under problems/ and derived/
slug = "throw-up"                 # file stem; the page is /lessons/<slug>/
model = "constant-accel"          # model: constant-accel | shm | linear-drag | damped-shm | work-energy | pv-work | projectile
regime = 1                        # 1 = algebra is calculus evaluated | 2 = calculus does more | 3 = algebra-only
scenario = "A ball leaves your hand at 20 m/s upward from 1.5 m. How high does it go, and when does it land?"

[constants]
g = -10                           # house convention; up positive (see docs/house-conventions.md)

[initial_conditions]
x0 = 1.5                          # metres
v0 = 20                           # m/s, up positive

[[assumptions]]                   # author-asserted model assumptions -> the faithful-model badge
claim = "no air resistance"
kind = "model"
[[assumptions]]
claim = "g = -10 m/s^2 (simplified from 9.81)"
kind = "model"

unknowns = ["apex_time", "max_height", "flight_time", "impact_velocity"]   # what the algebra register solves

[[graphs]]
kind = "stack"                    # stacked x-t / v-t / a-t, shared time axis
mode = "interactive"             # static -> Matplotlib SVG | interactive -> JS closed form | sampled -> precomputed pts (ADR-0012)
annotate = ["slope_of_x_is_v", "area_under_v_is_displacement", "a_nonzero_at_apex"]
[graphs.params.v0]               # only for interactive graphs: the slider ranges
min = 5
max = 30
default = 20
[graphs.params.x0]
min = 0
max = 5
default = 1.5

[misconception]                   # the buggy-first analogue (brief §4); optional but encouraged
claim = "At the top of the trajectory, acceleration is zero."
refuted_by = "graph:v-t slope unchanged at v=0"

formulas_used = ["kin-x-of-t", "kin-v-of-t"]   # ids that link into the reference (§8)
```

## Rules the producer enforces (build fails otherwise)

- **The algebra and calculus answers must agree** — `simplify(algebra − calculus) == 0`, proven by
  `prove.tiered_zero`. If they don't, your model is inconsistent; the producer refuses to emit.
- **Every expression must be dimensionally homogeneous** (`dims.check_homogeneous`).
- **Interactivity must earn its place** (ADR-0009): use `mode:"interactive"` only when sweeping a parameter
  reveals co-motion a static frame can't. Otherwise `static`.
- **Assumptions are disclosed, not discharged**: they describe the *model*, never the math, and never appear in
  the derivation record.
- **Provider-agnostic**: no course/exam/standards-body names anywhere (`scan-text.mjs`).

## Regime-2 scenarios (non-constant acceleration)

Set `model` to a regime-2 model and `regime = 2`. The spec carries that model's parameters instead of
`constants`/`initial_conditions` only — see the model module in `producer/models/` for its required fields
(e.g. `shm` takes `m`, `k`, `x0`, `v0`; `linear-drag` takes `m`, `b`, `v0`). The producer then proves the
**governing** way (ADR-0013): the closed form solves the equation of motion, the initial conditions hold, an
invariant holds (energy conserved, or the terminal/equilibrium limit), and any memorized algebra result falls
out of the calculus solution. Graphs are usually `interactive` (the closed forms are JS-cheap: cos, exp,
tanh); reserve `sampled` for a model with no elementary closed form.

## Area / integral lessons (off the time axis, ADR-0014)

Some lessons are not about motion over *time* but about an **accumulated integral over another variable** —
work as the area under a force–displacement curve (`∫F dx`), or PV-work as the area under a pressure–volume
curve (`∫P dV`). These use an **area instrument** instead of the x–t/v–t/a–t stack: the shaded area under a
curve `f(u)` is the accumulated integral `g(u)`, whose slope is `f`.

Author one by choosing an area-instrument model (`work-energy`, `pv-work`) and a single `kind:"area"` graph:

```toml
model = "work-energy"             # or pv-work; returns a Scenario carrying an AreaPlot (no x/v/a)
regime = 2                        # 2 for a variable force; 3 for a thermo PV process (calculus underpinning)

[parameters]                      # the model's parameters (see the model module for required fields)
m = 2                             # work-energy: m, b, d (+ optional x_window)
b = 8
d = 1.5

[[graphs]]
kind = "area"                     # the integral instrument; mode is forced to interactive
mode = "interactive"
annotate = ["area_is_work", "slope_is_force"]
```

The producer emits a draggable **cursor** (the upper limit of integration), the `f` and `g` closed forms, and
the `u/f/g` sample series — all parity-verified at 1e-9 like any interactive graph. The proof kind is
`integral` (FTC slope, area = integral, the memorized result falls out, constant-integrand → rectangle). To
add a *new* area model (e.g. gravitational PE `∫F dr`, impulse `∫F dt`), copy `models/work_energy.py`: build
`f_expr`, `g_expr`, the `AreaPlot`, and the four `integral` proof checks — no schema, gate, or frontend change
is needed.

## Trajectory lessons — 2D projectile (ADR-0015)

The `projectile` model draws the path **y vs x** (`kind:"trajectory"`) and dispatches on the parameters:

```toml
model = "projectile"
regime = 1                        # drag-free: exact, interactive

[parameters]
v0 = 20                           # m/s launch speed
theta = 40                        # degrees above horizontal
g = -10
# (no b_values) -> exact closed-form parabola; sliders for launch angle and speed

[[graphs]]
kind = "trajectory"
mode = "interactive"
```

Add `b_values` to get the **quadratic-drag** lesson (regime 2): the producer integrates m v̇=mg−b|v|v by RK4
(there is no closed form), verifies the result (converged + equation-of-motion residual + recovers the exact
parabola at b=0) and refuses to emit on failure, then ships `frames` the slider snaps between with the
drag-free parabola overlaid. Use `mode = "sampled"` for that graph. The committed numerical points are
re-checked in CI by `check-trajectory.mjs`:

```toml
regime = 2
[parameters]
v0 = 30
theta = 45
g = -10
m = 1
b_values = [0, 0.005, 0.01, 0.02, 0.04]   # kg/m; b=0 recovers the exact parabola

[[graphs]]
kind = "trajectory"
mode = "sampled"
```

## The page is automatic

There is no per-lesson page to write: the dynamic route `src/pages/lessons/[slug].astro` renders every
committed `solution.json`, and `/lessons/` lists them. Just author the spec, run `npm run prepare:data`, and
the lesson appears. The page shows a regime-appropriate framing, the player, the static figure, and the
`formulas_used` links.

## Math in prose

Write inline math in `scenario`, step prose, and `misconception` with `$...$` (e.g. `$v = v_0 + at$`); it is
KaTeX-rendered at build time and validated by `check:katex`. Units like "m/s²" can stay as plain text.
