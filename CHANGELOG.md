# Changelog

Notable changes, newest first. Architecture rationale lives in [`DECISIONS.md`](./DECISIONS.md); the phase
plan in [`ROADMAP.md`](./ROADMAP.md).

## [Unreleased] — Phase 1: full mechanics (in progress)

- **Fixes — inline-math rendering + a whitespace gotcha:**
  - The **lessons index** printed each scenario raw, so its `$…$` showed literally; it now renders through the
    same build-time KaTeX path (`inline()`) as the detail pages.
  - The **modeling-assumptions list** on every lesson page rendered `{a.claim}` raw, so authored `$…$` in
    assumptions showed literally; `renderSolution` now builds `claimHtml` and the player emits it.
  - Two **dropped spaces** from the Astro line-wrap-before-inline-element gotcha ("thereference" on the lessons
    index, "thechange" on the home page) — fixed with `{" "}`. A durable note is now in AGENTS.md.
- **Moment of inertia** (regime 2, rotation — area instrument on a *mass-distribution* axis, no engine change):
  the algebra course hands you a *table* of moments ($\tfrac13ML^2$, $\tfrac12MR^2$, $MR^2$); calculus makes
  them all from one integral $I=\int r^2\,dm$. With the rod's mass at density $\lambda=M/L$, the integrand is
  $dI/dr=\lambda r^2$ (a parabola), the shaded area is $I(r)=\tfrac13\lambda r^3$, and at the tip it is the
  memorized $\tfrac13ML^2$; concentrating all the mass at one radius (a hoop) collapses the integral to the
  rectangle $MR^2$. SymPy proves all four. ($I=0.96$ kg·m² for a 2 kg, 1.2 m rod.)
- **Reference depth — opened E&M magnetism + rounded out rotation & optics** (56 → 65 formulas; graph
  56 → 65 nodes / 89 edges): magnetism (Lorentz force, force on a wire, field of a long wire, magnetic flux,
  motional EMF), rotation (rod & disk moments, parallel-axis theorem), and Snell's law of refraction. Every
  domain now has multiple formulas; E&M induction is seeded via motional EMF.
- **Opened Phase 2 (E&M) and deepened Phase 3 (thermo) — two more area-instrument lessons, no engine change
  (model + spec + test):**
  - **Energy in a capacitor** (regime 2, E&M — *opens Phase 2*): the area instrument on the **charge** axis.
    As charge accumulates the voltage rises as $V(q)=q/C$, and the shaded area under that line is the stored
    energy $U=\int_0^Q V\,dq = \tfrac12 CV^2$ — a triangle, not a rectangle. SymPy proves the memorized
    $\tfrac12 CV^2$ falls out of the integral; the constant-voltage (battery) case is the rectangle $VQ$,
    twice the energy — the classic "where did half the energy go." Reuses `AreaPlot`. ($U=10$ J at $V=200$ V.)
  - **Adiabatic PV-work** (regime 3, thermo): the same area instrument on the **volume** axis as the isotherm,
    but along the steeper adiabat $P=P_1(V_1/V)^\gamma$. The area is the work $W=(P_1V_1-P_2V_2)/(\gamma-1)$,
    which SymPy recovers (general $\gamma$, certified symbolically); because no heat enters, the gas cools,
    $T_2/T_1=(V_1/V_2)^{\gamma-1}$. The cursor sweeps volume, the $P_1$ slider scales the curve. ($W\approx89$ J
    for a $1\to3$ L diatomic expansion, less than the isotherm.)
- **Reference breadth-fill across all remaining domains** (ADR-0007; pure authored + SymPy-verified data,
  no engine change): **28 → 56 formulas**, concept graph **28 → 56 nodes / 73 edges**, lighting up the regime
  map beyond mechanics —
  - **E&M (9):** Coulomb's law, point-charge field & potential, electric PE, capacitance, capacitor energy,
    Ohm's law, electrical power, the RC time constant.
  - **Thermo (6):** first law, specific heat, monatomic internal energy, adiabatic work & the $PV^\gamma$
    relation, Carnot efficiency.
  - **Fluids (4, mechanics domain):** hydrostatic pressure, buoyancy, continuity, Bernoulli.
  - **Waves & optics (5):** wave speed, period/frequency, wave on a string, the thin-lens equation,
    magnification.
  - **Modern (4):** photon energy, de Broglie wavelength, mass–energy, the photoelectric effect.
  - Each formula's LaTeX is generated from its SymPy expression, its units are dimensionally checked, and its
    typed concept-graph edges cross-link the domains (Coulomb↔gravitation, RC↔linear drag, capacitor↔spring,
    de Broglie↔momentum, photon↔period).
- **Producer**: model registry now 12 (`+capacitor-energy`, `+adiabatic`); 44 → 52 pytest cross-checks.
  All six gates green (parity 4188 samples, KaTeX 530 strings, scan clean).
- **Published.** The repo is public and the site is **live** at https://jd-jones-ases.github.io/quadrature/
  (GitHub Pages, GitHub Actions source). Every push to `main` runs the Node gates + `astro build` and
  auto-deploys; a gate failure fails the deploy. (Repo renamed to lowercase `quadrature` so the Pages path
  matches the Astro `base`.)
- **Concept-graph nodes are click-to-select AND drag-to-reposition** (pointer events; the frozen build-time
  layout is the initial state, so SSR is unchanged).
- **Mechanics breadth on the proven instruments (no engine change — model + spec + test):**
  - **Impulse–momentum** (regime 2, area instrument on the *time* axis): the shaded area under a force–time
    pulse is the impulse $\int F\,dt$, whose slope is the force and which equals the change in momentum — the
    time-axis sibling of work–energy. Reuses `AreaPlot`.
  - **Rotational kinematics** (regime 1, temporal stack with θ/ω/α labels): the rotational equations are the
    straight-line ones relabeled; the timeless equation $\omega^2=\omega_0^2+2\alpha\Delta\theta$ falls out of
    the integrals. Reuses `GraphStack`.
  - **Gravitational potential energy** (regime 2, area instrument on the radial axis): PE is the area under
    $F=GMm/r^2$, and because that area to infinity *converges*, the escape energy $GMm/R$ is finite (proven
    via `sympy.limit`); near the surface it collapses to the $mgh$ rectangle. Reuses `AreaPlot`.
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
