# Changelog

Notable changes, newest first. Architecture rationale lives in [`DECISIONS.md`](./DECISIONS.md); the phase
plan in [`ROADMAP.md`](./ROADMAP.md).

## [Unreleased] — Phase 1: full mechanics (in progress)

- **Mechanics breadth on the proven instruments (no engine change — model + spec + test):**
  - **Impulse–momentum** (regime 2, area instrument on the *time* axis): the shaded area under a force–time
    pulse is the impulse $\int F\,dt$, whose slope is the force and which equals the change in momentum — the
    time-axis sibling of work–energy. Reuses `AreaPlot`.
  - **Rotational kinematics** (regime 1, temporal stack with θ/ω/α labels): the rotational equations are the
    straight-line ones relabeled; the timeless equation $\omega^2=\omega_0^2+2\alpha\Delta\theta$ falls out of
    the integrals. Reuses `GraphStack`.
- **The trajectory instrument — 2D projectile** (ADR-0015): a new `kind:"trajectory"` graph (the path y vs x,
  carried by a `TrajectoryPlot`), with a `Trajectory.svelte` island and `render_trajectory`.
  - **Drag-free lesson** (regime 1, exact): each component is constant-acceleration motion; the path is an
    exact parabola (interactive launch-angle/speed sliders, parity-verified), and the memorized range/height/
    flight-time formulas fall out of the component integrals.
  - **Quadratic-drag lesson** (regime 2, **numerical** — resolves the ADR-0012 parked question): m v̇=mg−b|v|v
    has no closed form, so the producer integrates by RK4 and ships frames the slider snaps between (with the
    drag-free parabola overlaid). New verification model: the producer refuses to emit unless the path is
    RK4-converged, satisfies the equation-of-motion residual, and recovers the exact parabola at b=0; a new
    **`check-trajectory.mjs`** gate re-checks the committed points in CI (structure + b=0-parabola +
    range monotonic in drag).
- **The integral instrument off the time axis** (ADR-0014): a general `kind:"area"` graph where the shaded
  **area under a curve `f(u)` is the accumulated integral `g(u)=∫f du`**, whose slope is `f` — the
  slope↔value / area↔change thesis on *any* axis, not just time. New: an `AreaPlot` on the `Scenario` (the
  temporal `x/v/a` become optional), an `area_series {u,f,g,u_max}` schema shape, a third proof kind
  **`integral`** (FTC slope, area=integral, the memorized result falls out, constant-integrand→rectangle),
  `graph.render_area` + an `AreaPlot.svelte` island with a draggable cursor, and axis-agnostic parity +
  solution gates. Reuses the 1e-9 parity oracle untouched.
- **Work–energy lesson** (`∫F dx`, regime 2, mechanics): the work is the area under the F–x curve, its slope
  is the force, and SymPy proves that area equals the kinetic energy gained (½mv² falls out of the integral);
  the constant-force case collapses to the rectangle W=Fd.
- **Isothermal PV-work lesson** (`∫P dV`, regime 3, thermo — opens Phase 3): the *same* instrument on the
  volume axis, built with **no engine changes** — only a model, a spec, and a test — the demonstration that
  the hard instrument makes a new domain's lessons simple. Reference breadth started in thermo (ideal-gas law,
  isothermal work); concept graph 26 → 28 nodes.
- Regime-2 architecture: generalized the producer to ODE models (a model registry), generalized the proof
  block (`equivalence` | `governing`), and added the back-substitution verification model (ADR-0013).
- Interactivity policy resolved (ADR-0012): regime 2 stays `interactive` where the closed form is JS-cheap;
  `sampled` mode reserved for the no-closed-form minority.
- Two regime-2 lessons, fully verified and interactive: **simple harmonic motion** and **terminal velocity
  (linear drag)**. Dynamic `[slug]` lesson route + a `/lessons/` index.
- **Sampled graph mode** (ADR-0012 refinement) + the **damped oscillator** lesson: the under→critical→over
  transition, where the solution's form changes at critical damping. The damping slider snaps between
  discrete, exact, individually parity-verified frames. Governing proof covers all three forms + the energy
  dissipation rate dE/dt = −b v².
- Reference breadth-fill (ADR-0007): 3 → 26 mechanics formulas (dynamics, momentum, energy, circular,
  rotation, gravitation, damping), each SymPy-unit-verified; concept graph now 26 nodes / 25 edges.
- Post-Phase-0 polish: fixed four Astro whitespace-gotcha dropped spaces; Matplotlib figure QC pass
  (per-panel limits, annotation bboxes, a–t panel scaled to include y=0).

## Phase 0 — vertical slice (complete, awaiting publish)

The end-to-end instrument on one scenario: vertical motion under constant gravity.

- Repo scaffold: Astro 7 + Svelte 5 + KaTeX player, a SymPy (uv) producer, Ajv + parity + scan Node gates,
  GitHub Pages workflow (Pages disabled until review).
- Documentation/governance system seeded: AGENTS.md, DECISIONS.md (ADR-0001…0011), ROADMAP.md, this changelog,
  `docs/` (architecture, authoring-problems, authoring-formulas, regime-map, house-conventions, SOURCES), and
  a per-session log under `docs/sessions/`.
- Provider-agnostic from day one: founding brief renamed `QUADRATURE_BRIEF.md → PROJECT_BRIEF.md` (gitignored)
  and a `scan-text.mjs` build gate.
- Licensing: MIT (code) + CC BY-SA 4.0 (content).
