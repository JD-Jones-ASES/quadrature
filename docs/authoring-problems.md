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
model = "constant-accel"          # the producer model: constant-accel | shm | linear-drag (see producer/models/)
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

## Then wire the page

Add `src/pages/lessons/<slug>.astro`: import the committed `solution.json`, mount the player
(`<SolutionPlayer solution={...} client:visible />`), and write a short first-principles framing. The lesson
links to its formulas via `formulas_used`.
