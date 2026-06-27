# Changelog

Notable changes, newest first. Architecture rationale lives in [`DECISIONS.md`](./DECISIONS.md); the phase
plan in [`ROADMAP.md`](./ROADMAP.md).

## [Unreleased] — Phase 1: full mechanics (in progress)

- **The interlinking backbone — the reference becomes the navigational spine (brief §8, ADR-0026).** Frontend-only,
  no producer/schema/gate/data change (reuses `formulas.json` + a build-time lesson-slug→title map).
  - **Lesson → reference (hover opens the entry).** Each "Formulas used" chip shows the formula's name and a
    CSS-only hover/focus popover previewing its reference entry — the rendered LaTeX + "Valid when" — click still
    opens the full entry. Pure CSS, no hydration, keyboard-accessible.
  - **Reference entry → lessons** that use it (footer links with real lesson titles, plain-text fallback).
  - **Reference entry → derivation** target (linked to its `#id`, shown by name).
  - **Reference entry → its graph**: a `concept graph ↗` link to `/reference/graph/#<id>`; `ConceptGraph` now
    reads the URL hash on mount and **selects + centres** that node.
  - Not attempted (needs a design pass): tokenizing "any formula token" inside lesson prose, and a first-class
    algebra↔integral *dual* link.

- **Formula reference typography: generated RHS with physics glyphs + author order, gate-enforced (ADR-0025).**
  - **Root cause.** The reference RHS was `sp.latex(expr)`, so the ASCII symbol names chosen for `sympify`
    leaked onto the page (`\mathcal{E} = -dPhidt`, `N = N₀e^{-lam t}`, `v = √(FT/μ)`, `log`/`asin`), and SymPy's
    sort order replaced physics convention (`E = c²m`, `F_net = am`, `F = Bqv`, `-Tc/Th + 1`). The semantic
    gates are blind to typography, so this had no safety net. (Flagged by an external review of the live site.)
  - **Fix — still 100% machine-derived.** A per-symbol `latex` glyph in `[variables]` feeds
    `sp.latex(symbol_names=…)` (+ `ln_notation` / `inv_trig_style='full'` for `\ln` / `\arcsin`); the effective
    glyph is propagated to the output so the variable column also renders it. A `LatexPrinter` subclass orders
    Mul factors / Add terms by the author's written order — it only changes print order of the same evaluated
    expr (no rebuild, no artifacts, semantics identical by construction). 13 leaks + ~20 orderings fixed; the
    stale "log is the natural logarithm (ln)" apology removed.
  - **New gate `check:latex-quality`** (in `validate`, so CI-enforced): strips each formula's authored glyphs,
    `\text{}`/command/function tokens, then fails on any leftover ≥2-letter ASCII run — a leaked symbol name.
    "Typography breaks the build the way a bad unit does."
  - **The `a = a` seed.** `kin-a-const` gained an italic `note` caption framing it as the root of the integral
    ladder, rather than reading as a bare tautology; the graph node stays.

- **Thin-lens optics — a seventh graph instrument (the ray diagram), + practice fan-out (ADR-0024).**
  - **The 7th instrument, `kind:"lens"`** — the first *geometric construction*. A converging lens of fixed
    focal length f; the **object distance d_o is the cursor**, an **object height h_o** slider. `Lens.svelte`
    draws the three principal rays (with Liang–Barsky viewport clipping) and reads off the image, which flips
    **real/inverted ↔ virtual/upright/enlarged** as d_o crosses f (dashed backward rays in the virtual case).
    Model `thin_lens.py` (regime 3): parity-verified `d_i = d_o f/(d_o−f)`, `h_i`, `m`, over the canonical `u`
    axis (so the parity oracle re-checks it with no gate change); proof `governing` — the closed-form d_i
    satisfies the lens equation and the chief/parallel/focal ray constructions all agree (which *is* the lens
    equation). f is a fixed constant so the d_o=f singularity never moves; the sampler straddles it and fails
    loud on a hit.
  - **Honest second register.** Optics is geometry, not calculus, so the second register reads **"Ray diagram"** —
    a per-lesson `calculus.register_label` override threaded through the player and the practice step-throughs
    (default "Calculus").
  - **Markdown emphasis in authored prose (root-cause fix).** `inline()` was math-only, so the `**bold**` /
    `*italic*` carried pervasively in scenarios/steps/misconceptions rendered as **literal asterisks**. Added
    escape-then-emphasize (bold before italic; unmatched asterisks left literal; non-math segments only) — one
    function, fixes every authored surface.
  - **Practice fan-out (ADR-0022).** A second verified, misconception-distractored question on eight foundational
    lessons (projectile max height, energy mass-independence, impulse average-vs-peak force, collision KE lost,
    mass-spring max speed, orbit period, variable-force final speed, capacitor battery work) + the thin-lens
    lesson's own two.
  - **Diverging-lens variant (same instrument, f < 0).** The `thin-lens` model and `kind:"lens"` island
    generalize to a negative focal length with no engine change: the straddle guard is gated on f>0; the step
    prose and the island readout/chips are driven by the *computed* image character (the parallel-ray slope
    −hₒ/f diverges when f<0, focal labels use |f|, the lens glyph draws inward arrowheads, `render_lens` gained
    a virtual-image branch). New lesson *the diverging lens: one image, always virtual* (f=−1 → dᵢ=−0.6, m=0.4 —
    virtual, upright, reduced at every object distance) + two verified practice questions. Converging lesson
    regression-checked.
  - **32 lessons, 82-formula reference, 119 producer tests, all six gates green** (parity 6652, KaTeX 2590);
    production build clean (38 pages). Seven instruments now: stack · area · trajectory · energy bars ·
    collision bars · standing waves · thin-lens ray diagram (converging + diverging). Waves & optics has three
    lessons; the last domain gap on the engine is closed.

- **Site review pass — fixed the black graphs, reorganized lessons, rebuilt the concept graph, +5 lessons.**
  - **Graph rendering bug fixed (the marquee fix).** Every interactive graph instrument was rendering as solid
    black SVGs — broken in light mode (black-on-cream), invisible in dark. Root cause (ADR-0019): Astro
    delivered the scoped CSS of the *top-level* islands but not of the *child* graph islands (`GraphStack`,
    `AreaPlot`, `Trajectory`, `EnergyBars`, `Collision`), so they fell back to default black fills. Fixed at the
    source with `svelte({ compilerOptions: { css: "injected" } })` — one line, no island edits, and **full
    dark mode** then works via the existing `@media` variable swap. Declared `color-scheme: light dark` (meta +
    CSS) so force-dark browsers use the site's own themes; static Matplotlib posters sit on a fixed-light figure
    card so they read intentionally in dark mode. Verified live via computed styles in both themes across all
    five instruments. Polish: lesson "formulas used" now deep-link into the reference; `role="tabpanel"`;
    reference-table `aria-label`s.
  - **Lessons index reorganized into a read-in-order course sequence.** A presentation-only manifest
    (`src/lib/lessonOrder.js`) groups the lessons into **11 pedagogical units** (Kinematics → Dynamics → Energy →
    Momentum → Rotation → Oscillations → Gravitation → Fluids → Thermodynamics → E&M → Modern), regime demoted to
    a small badge. No producer/schema change; lessons absent from the manifest fall into a resilient trailing
    group.
  - **Concept graph rebuilt (ADR-0020).** Node labels were raw LaTeX (`\tau`, `\frac{1}{f}`, …) — now clean
    Unicode via a curated `_clean_label` map. The crowded 640×480 single-blob layout is now **domain-clustered**
    on a 900×640 canvas (each domain seeded into its own region), with an ink label halo, **pan/zoom** (node-drag
    preserved through the transform), and a domain color legend.
  - **N-panel temporal stack (ADR-0021)** — the x/v/a stack generalized to any number of derivative/integral
    panels (the x/v/a path is byte-unchanged), parity-verified with no new gate.
  - **Five new lessons** (26 total): **RC charging** (E&M, the 2-panel stack — *I* is the slope of *Q*, the RC
    ODE, τ=RC); **Newton's second law on an incline with friction** (opens the Dynamics unit — `a=g(sinθ−μcosθ)`,
    the mass cancels); **radioactive decay** (opens Modern — the N / dN/dt 2-panel stack, `dN/dt=−λN`);
    **Torricelli / draining tank** (opens fluid dynamics — energy bars, `v=√(2gh)`); **the field of a charged rod**
    (`∫kλ/x² dx` — the area instrument where algebra runs out and calculus is the only way). Reference grew to
    **74 formulas** (+RC charge, +radioactive decay & half-life). All SymPy-verified; 94 producer tests, parity
    5753, all six gates green.
- **Collisions / momentum — a fifth graph instrument (`kind:"collision"`): before/after bars where momentum is
  always conserved but kinetic energy isn't.** A 1D two-cart collision (2 kg @ 3 m/s into 1 kg at rest) with the
  **coefficient of restitution `e` as the cursor** (1 = perfectly elastic … 0 = perfectly inelastic). The
  **momentum** total bar is the same height before and after at *every* `e` (only the per-body split shifts);
  the **kinetic-energy** total bar matches only at `e=1` and collapses as `e→0`, the gap shaded as energy lost.
  The dual-register insight: momentum conservation is the **time-integral of Newton's third law** — the contact
  forces are equal and opposite at every instant, so the impulses `J=∫F dt` cancel for *any* force profile,
  elastic or not; kinetic energy is different because the deformation work need not come back, leaving
  `½μ(1−e²)(Δv)²` behind (`μ` the reduced mass). Proof `governing`: momentum conserved at every `e`, the
  restitution relation, the KE-loss identity, `e=1 ⇒` KE conserved, `e=0 ⇒` the common velocity `v_cm`. New
  `CollisionPlot` + `Collision.svelte` + `render_collision` + `collision_series`/`consts` schema, wired like the
  energy/area instruments (parity-verified `v1f,v2f` closed forms, **no new gate**). Paint-verified live:
  momentum 6→6 at every `e`; KE 9→9 elastic, 9→6 with 3 J (33 %) lost perfectly inelastic; equal masses elastic
  → full transfer (the incident cart stops dead, the target leaves at 3 m/s). One reference formula
  (perfectly-inelastic common velocity). Misconception: "momentum is only conserved when no energy is lost."
- **Conservation of energy — a fourth graph instrument (`kind:"energy"`): KE/PE bars that trade while the
  Total stays flat.** A block on a frictionless ramp; the kinetic and potential energies exchange as it
  descends, but their sum `mgH` never changes — the constant Total bar is the visual proof of conservation.
  The dual-register insight: energy conservation is the **first integral of `F=ma`** (`mv dv = F dx ⇒
  ½mv² = ∫F dx`), and because gravity's work `mg(H−h)` depends only on the height dropped, the speed
  `v=√(2g(H−h))` is **path-independent** — a steep and a gentle ramp to the same depth give the same bottom
  speed (only the time differs). Proof `governing` (dE/dh=0, the conservation law, the speed falls out, KE is
  the work integral). New `EnergyPlot` + `EnergyBars.svelte` + `render_energy` + `energy_series` schema, wired
  exactly like the area instrument (parity-verified KE/PE closed forms). Paint-verified: at h=10 KE=PE=200 J,
  at the bottom KE=400 J / PE=0 with the Total bar unchanged and v=20 m/s. (`m=2` kg, `H=20` m.)
- **Elliptical orbit — the regime-2 sequel; Kepler's three laws fall out of the numerically-integrated
  inverse-square law.** No elementary time-parameterisation exists (Kepler's equation is transcendental), so
  the path is RK4-integrated from `r̈ = −μr/r³` and shipped as `frames` the slider snaps between — sweeping the
  **eccentricity** at a *fixed semi-major axis* `a`, so every orbit has the **same period** `T=2π√(a³/μ)`
  (Kepler's 3rd law depends on `a`, not the shape). The producer refuses to emit unless the orbit conserves
  energy `½v²−μ/r=−μ/2a` (vis-viva) and angular momentum `x·vy−y·vx` (Kepler's 2nd law), **closes** after one
  period (Kepler's 1st — a closed ellipse), and recovers a circle at `e=0`. A `check-trajectory.mjs` branch (on
  `frame=="orbit"`) re-checks the committed points: each closes, **encircles the focus exactly once** (total
  turning ≈ 2π), `e=0` is a circle, and all frames share the period. Paint-verified live: `e=0` is a circle,
  `e=0.5` an ellipse (focus off-centre, `b/a=√(1−e²)`) with **the same 5.58 h period** and perihelion speed
  8.66 km/s vs aphelion 2.89 km/s. The island's orbit branch now handles the sampled (eccentricity) case;
  `view_half` schema field. Proof `governing`.
- **Circular orbit — the trajectory instrument generalized to a centred, looping path (a new `frame:"orbit"`):**
  a satellite traces the exact parametric circle $x=R\cos\omega t$, $y=R\sin\omega t$ ($\omega=\sqrt{\mu/R^3}$),
  proven (regime 1, equivalence) to solve the inverse-square equation of motion $\ddot{\mathbf r}=-\mu\mathbf r/R^3$,
  with the orbital speed $v=\sqrt{\mu/R}$ and **Kepler's third law** $T^2=4\pi^2R^3/\mu$ falling out. Gravity is
  the centripetal pull, so the satellite falls *around*, not down. The graph is interactive (parity-verified
  closed form): drag the radius and the loop widens while $v\propto1/\sqrt R$ and $T\propto R^{3/2}$ — verified
  live, the geostationary radius gives $T=23.9$ h. Reuses `kind:"trajectory"` (the closed form is parity-checked
  like the drag-free projectile); the only new surface is a centred, equal-aspect render frame in
  `render_trajectory` + `Trajectory.svelte` (the projectile/ground frame is unchanged) and a `frame`/`mu`
  schema field. Two reference formulas (orbital speed, Kepler's third law). $v=7.56$ km/s, $T=1.62$ h at low
  orbit.
- **Rendering fixes — interactive islands now hydrate in the preview env, and the area-graph caption is no
  longer hardcoded to work–energy:**
  - **`client:visible` → `client:load`** on the two island-bearing pages (the lesson `SolutionPlayer` and the
    `/reference/graph/` `ConceptGraph`). The headless preview loads at a **0×0 viewport**, so the
    `client:visible` `IntersectionObserver` never fired and the islands never hydrated — which is why prior
    sessions reported "this env can't paint." With `client:load` the islands hydrate on load (they are each the
    page's primary, above-the-fold content), the sliders/cursor render, and the closed-form-in-JS recomputes
    live. Verified by driving the sliders and reading the live values back (DOM + a11y snapshot; raw
    screenshots still time out, a separate renderer quirk).
  - **AreaPlot caption was hardcoded to the work–energy lesson** ("the work **W = … J**, which equals the
    kinetic energy gained (½mv²) … the force **F = … N**"). That was wrong on all nine *other* area lessons
    (force, electric energy, moment of inertia, impulse, PV-work…). It is now **label-driven** — it reads the
    quantity symbol + unit from each lesson's `f_label`/`g_label`/`u_label`, so it correctly says e.g.
    "**F = 400000 N**" on the hydrostatic-force wall, "**U = 10 J**" on the capacitor, "**ΔU = 0.90 J**" on
    Coulomb PE. Verified live across the linear, energy, and inverse-square cases.
- **Three more area-instrument lessons — open the fluids domain, deepen E&M, complete the rotation triad
  (no engine change; model + spec + test each):**
  - **Electric potential energy** (regime 2, E&M): the area instrument on the **separation** axis — the
    electric twin of gravitational PE. The energy to pull two opposite charges apart is the area under the
    Coulomb force $kq_1q_2/r^2$, and because it is the *same* inverse square as gravity, that area to infinity
    *converges*: the binding energy $kq_1q_2/R$ is finite (proven via `sympy.limit`). The uniform-field case
    collapses to the rectangle $qEd$. ($1.80$ J to separate a $\pm2\,\mu$C pair from $2$ cm; reaching $2R$
    captures exactly half.)
  - **Hydrostatic force on a wall** (regime 2, fluids — *the fluids domain's first lesson*): the area
    instrument on a **depth** axis. Water pressure grows linearly with depth, $P=\rho g h$, so the force on a
    vertical wall is the triangular area $\tfrac12\rho g w H^2$; SymPy shows the algebra's "average pressure ×
    area" is exactly that area, and the uniform-pressure case is the rectangle (twice the force). The
    misconception is the hydrostatic paradox — the force depends on depth and width, not on how much water is
    behind the wall. ($F=400$ kN for a $5$ m-wide wall at $4$ m depth.)
  - **Rotational work–energy** (regime 2, rotation): the area instrument on the **angle** axis — the perfect
    mirror of $\int F\,dx=\tfrac12 mv^2$. The work under a torque–angle curve $\tau(\theta)=c\theta$ is the
    rotational kinetic energy, and the memorized $\tfrac12 I\omega^2$ falls out of the integral; a constant
    torque collapses to the rectangle $\tau_0\,\Delta\theta$. Completes the rotation triad (kinematics ·
    moment of inertia · energy). ($W=9$ J, $\omega=6$ rad/s for a $0.5$ kg·m² flywheel.)
  - Reference depth: **65 → 67 formulas** (graph **67 nodes / 94 edges**) — hydrostatic force on a wall
    ($\tfrac12\rho g w H^2$) and rotational work ($\tau\Delta\theta$), each cross-linked to its integrand and
    its linear-area / work–energy siblings. Model registry now **16**
    (`+coulomb-pe`, `+hydrostatic-force`, `+rotational-work`); **68 producer tests**; all six gates green
    (parity 4676, KaTeX 740, scan clean); `astro build` clean (22 pages). Salt-only SVG regenerations reverted.
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
