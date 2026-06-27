# DECISIONS — architecture decision log

Newest at the bottom. Each entry: context → decision → consequences. Keep terse; this is a contract, not a
manual.

---

## ADR-0001 — Mirror the sibling-portal stack; do not invent a new one (2026-06-26)

**Context.** Quadrature is the fourth technical project in the line `RealStats → Mechanic → GlassBox → this`.
Three sibling repos already encode the house stack and methodology, and the brief names them as the template:
GlassBox (structure), Mechanic (SymPy), Decline / "Spengler Portal" (Astro+Svelte islands + the force-graph).

**Decision.** Mirror GlassBox/Decline exactly: **Astro 7** `output:"static"`, `trailingSlash:"always"`,
**Svelte 5** islands hydrated `client:visible`, vanilla ES modules + CSS custom properties (no framework),
**Ajv** (draft 2020-12, `additionalProperties:false`) gates, `base=/quadrature` with a `LOCAL_ROOT=1` preview
escape hatch. Carry Mechanic's producer/verification discipline. KaTeX for math (from Mechanic).

**Consequences.** No bespoke build system; an agent fluent in the siblings is fluent here.

## ADR-0002 — One build-time SymPy producer is the single source of truth (2026-06-26)

**Context.** The pedagogical contract is that the algebra and calculus registers genuinely agree and that
every formula is dimensionally sound. We need a producer whose output cannot drift from the mathematics.

**Decision.** A `uv` package (`producer/`, shaped like `Mechanic/pipeline`) does five things per the brief §3:
integrate `a→v→x` (calculus register); solve the kinematic relations for the unknowns (algebra register);
**prove** the registers equal via a tiered checker (`simplify` → `equals` → `rewrite` → high-precision numeric
sampling, ported from Mechanic's `tiered_zero`); check dimensional homogeneity (`sympy.physics.units`, ported
from Mechanic's `dims.py`); and export the closed form as JS-evaluable text (`jscode` + CSE + auto-guards,
from `emit_js.py`) plus high-precision sample points (the parity oracle). The producer **refuses to emit** a
solution whose proof or unit check fails — the local "verification breaks the build".

**Consequences.** The math is SymPy's actual verdict, not a transcription. The frontend never runs Python; the
Pyodide door stays open for a future "solve your own problem" sandbox (not built now).

## ADR-0003 — One solution schema, two-axis honesty model (2026-06-26)

**Context.** A polished, interactive graph must not imply a guarantee SymPy never produced. Some content is
machine-derived; some (the physics modeling) is an author's assertion.

**Decision.** A single `schemas/solution.schema.json` (brief §6): the four registers, `equivalence_proof`,
`units_check`, `assumptions[]`, `graphs[]` (`mode: static|interactive` + `closed_form` + `params`),
`misconception`, `regime`, `formulas_used`. Two orthogonal axes, shown as badges: **machine-derived**
(SymPy-checked: algebra, calculus, the proof, the unit check) vs **faithful-model** (author-asserted: `g=−10`,
no air resistance, point mass). The model axis is **disclosed, not discharged** — the reader checks the math
against SymPy but takes the assumptions on a textbook's footing. Assumptions never appear inside the
derivation record; the Ajv gate cross-checks `equivalence_proof.checked_by == "sympy"` and that assumptions
carry `kind:"model"`.

**Consequences.** Trust is by construction and visible (per-lesson badges + a `/verification/` page).

## ADR-0004 — Provider-agnostic, enforced by a build gate (2026-06-26)

**Context.** The course must not name any specific course, exam, or standards body. Discipline alone leaks —
the founding brief itself names one, and it was nearly published under the wrong filename.

**Decision.** Public language is "algebra-based physics" / "calculus-based physics" / topic names. The
course-mapped founding brief is kept **gitignored** (`PROJECT_BRIEF.md`). A build gate
(`scripts/validate/scan-text.mjs`) greps all committed text for banned terms and fails the build on a hit.

**Consequences.** The constraint is enforced, not hoped for. Internal scoping stays private. (The brief was
renamed `QUADRATURE_BRIEF.md` → `PROJECT_BRIEF.md` to match the gitignore on day one.)

## ADR-0005 — Authoring in TOML (2026-06-26)

**Context.** The human layer (scenario, ICs, assumptions, unknowns, graph choices, misconception) must stay
separate from the verified solution object, and SymPy needs only a spec, not prose.

**Decision.** Author each scenario as `problems/<topic>/<slug>.problem.toml` and each reference entry as
`reference/formulas/<id>.formula.toml`, parsed with stdlib `tomllib`. The producer reads the spec, does the
math, and emits `derived/*.json`. (`tomllib` is read-only, which suits an input format; YAML was rejected to
avoid a third-party parse dependency.)

**Consequences.** Editing a spec re-runs the producer; the verified JSON is regenerated and committed.

## ADR-0006 — The three-regime model is explicit per topic (2026-06-26)

**Context.** "Algebra is just calculus done" is only true for constant acceleration. Pretending everything is
that regime would be the physics version of a slide that lies — the exact failure the project exists to kill.

**Decision.** Every scenario and formula carries a `regime` (1 = algebra-is-calculus-evaluated; 2 =
calculus-does-what-algebra-cannot; 3 = algebra-only). The player surfaces it so a learner always knows which
relationship they are looking at. Regime 1 is Phase 0 (prove the engine on constant integrands); regime 2
(ODEs) is Phase 1; regime 3 (fluids/thermo/waves/modern) is Phase 3.

**Consequences.** The honesty about *what calculus buys you* is built into the data model, not the prose.

## ADR-0007 — The reference is generated independently of lessons; built breadth-first (2026-06-26)

**Context.** The brief wants both "a complete formula reference for all offerings" and "a few deeply-built
lessons." Coupling them would make breadth wait on depth.

**Decision.** The reference (`reference/formulas/*` → `derived/reference/*`) is generated from SymPy formula
definitions independent of whether any lesson uses a formula. After the Phase 0 slice it is populated
**breadth-first** across the full union of offerings, while lessons trail depth-first. (Owner decision,
2026-06-26.)

**Consequences.** The "best formula sheet" can be comprehensive early; lessons interlink into it as they land.
Breadth lives in the reference; depth lives in the lessons.

## ADR-0008 — Concept graph: deterministic build-time layout, frozen into JSON (2026-06-26)

**Context.** The §8 concept graph is the navigational backbone (nodes = formulas/quantities; typed edges =
derived-from / integral-of / derivative-of / special-case-of / assumes / related-to). It must render with no
hydration mismatch and no heavy client library.

**Decision.** Port Decline's pattern: the producer computes a deterministic force layout (seeded, fixed
iterations) and **freezes** `x,y` into `derived/reference/concept-graph.json`; the Svelte island renders plain
SVG (no d3/cytoscape), color-coded by physics domain, edges grouped into typed families, with URL-hash
selection/deep-linking. No client-side layout.

**Consequences.** The graph is byte-stable and cheap; the producer stays the single source of truth (layout
included).

## ADR-0009 — Interactivity policy: static by default; a slider must earn its place (2026-06-26)

**Context.** Live controls add noise as often as insight, and most regime-2 closed forms aren't cheap
polynomials.

**Decision (brief §7).** Default to `mode:"static"` (a Matplotlib SVG). Make a graph `interactive` only when
sweeping a parameter reveals co-motion a static frame can't (drag v₀ → the x–t parabola, the v–t line, and the
apex move together). Encode the decision per graph in the spec, never as an engine default.

**Consequences.** Interactivity is a deliberate authoring choice. Regime-2 will be mostly static; a
precomputed-sample-points export for a limited set of regime-2 interactives is an open question for Phase 1
(see ROADMAP).

## ADR-0010 — Verification model: local producer + CI Node gates (2026-06-26)

**Context.** "Verification breaks the build" can mean run SymPy in CI (Mechanic) or run it locally and gate
the committed output in CI (GlassBox). The seeded `.gitignore` says "CI is a pure astro build".

**Decision (owner, 2026-06-26).** Local SymPy, GlassBox-style. The producer refuses to emit on a failed
proof/unit check (local break). The committed `derived/` is gated in CI by Node-only checks:
`validate-solutions`/`validate-reference` (Ajv schema + honesty cross-checks), **`check-parity`** (re-evaluate
each exported JS closed form at the embedded SymPy sample points; fail on relative error > 1e-9 — CI's
verification hook without Python), and `check-katex` (every LaTeX string renders). No Python in CI.

**Consequences.** Fast CI; the symbolic proof runs under supervision locally, and the parity gate guarantees
the JS the browser runs reproduces SymPy's numbers. The day stronger CI is wanted, the producer can be added
to the workflow via uv (Mechanic's model) without changing the schema.

## ADR-0011 — Licensing: MIT (code) + CC BY-SA 4.0 (content) (2026-06-26)

**Context.** House standard; the repo mixes code and authored course content.

**Decision.** Code under MIT (`LICENSE`); course content (prose, solutions, reference entries, figures) under
CC BY-SA 4.0 (`LICENSE-content.md`). Cite, don't reproduce (fact extraction); no copyrighted source text or
figures hosted. Citations + verification method per entry in `docs/SOURCES.md`.

**Consequences.** Clear reuse terms; the verification-as-product stance extends to provenance.

## ADR-0012 — Regime-2 interactivity policy: closed-form-in-JS by default; `sampled` mode only where there is no closed form (2026-06-26)

**Context.** The brief (§7, §12) assumed most regime-2 graphs must be static because "the closed form
isn't cheap past polynomials." That conflates two different things: *transcendental* (exp, cos, tanh, log)
is JS-cheap, while *no elementary closed form* (needs numerical integration) is the real constraint. The
purpose of interaction is to drive physical/mathematical intuition, not to add widgets.

**Decision (owner-approved, 2026-06-26).** Three graph tiers, chosen per graph in the spec:
1. **`interactive`** — a closed form the browser evaluates in JS. Used for **regime 1 AND the large part of
   regime 2 with elementary closed forms** (linear drag → exp, terminal velocity → tanh, SHM → cos, RC/decay
   → exp, underdamped → e^{−γt}cos). Same engine and parity oracle as Phase 0; no new machinery. Regime 2 is
   **not** defaulted to static.
2. **`sampled`** — precomputed sample points (a parameter grid) the player interpolates, for the minority with
   **no elementary closed form** (2D quadratic-drag trajectories, anharmonic oscillators, non-1/r² orbits).
   Deferred until a lesson needs it; it carries extra cost (see Consequences) so it must earn its place twice.
3. **`static`** — a Matplotlib SVG: a single illustrative configuration, or where the curve barely changes
   across the parameter range.

Gate **every** interactive (any regime) on one sentence: *name the relationship the slider reveals* — an
asymptote, a time-constant, a phase relationship, a qualitative transition, or a scaling law. If you can't,
it is `static`. Highest-value regime-2 interactives to prioritize: the **damping transition**
(under→critical→over), **terminal-velocity approach**, and **SHM phase/period**.

**Consequences.** Most of regime 2 stays genuinely interactive for free. The `sampled` tier, when built, adds
a real verification surface — "parity" becomes an *interpolation-error bound* between sample points (a new
gate), plus an honesty disclosure that the curve is interpolated (it can hide stiffness/discontinuities
between samples). We pay that only where the intuition payoff is high. Multi-parameter `sampled` grids risk a
committed-data blowup; prefer a 1-parameter sweep or `static`.

**Implementation refinement (2026-06-26, damped oscillator).** Rather than *interpolating* between precomputed
points (which would introduce interpolation error and force a "this curve is approximate" disclosure), the
`sampled` mode ships **discrete exact frames**: one closed form per sweep value, each individually
parity-verified (1e-9) like any `interactive` graph, and the slider *snaps* between them. This is honest —
every displayed curve is an exact, verified solution — and it sidesteps the interpolation-error gate entirely.
It fits the motivating case perfectly: the damped oscillator's solution *form* changes at critical damping, so
a single closed form is impossible *by nature*, which is exactly why discrete exact stops (not one morphing
formula) is the right model. The disclosure states the slider snaps between exact solutions.

## ADR-0013 — Regime-2 verification model: back-substitution into the equation of motion (2026-06-26)

**Context.** Regime 1's proof is `simplify(algebra − calculus) == 0` — but in regime 2 there is no algebra
answer to equate; calculus is the only road in. We still need "verification is the product," so the proof
must be redefined, not dropped.

**Decision.** For a regime-2 scenario governed by an equation of motion (an ODE), the producer proves, via the
same tiered checker (`prove.tiered_zero`):
1. **The closed form solves the equation of motion** — substitute the proposed `x(t)` into the ODE residual;
   it must reduce to zero (Mechanic's back-substitution move). This is the load-bearing check.
2. **The initial conditions hold** — `x(0)=x₀`, `x'(0)=v₀`.
3. **An invariant**, model-appropriate: for a conservative system, a **conserved quantity** (energy:
   `d/dt(½mv² + ½kx²) == 0`); for a dissipative system, the **equilibrium / asymptotic limit** (terminal
   velocity satisfies the force balance `mg = b·v_term`, i.e. `v'=0` there).
4. Where the algebra-based course hands over a **memorized result** (period `T=2π√(m/k)`, `v_term=mg/b`), prove
   that result **falls out of** the calculus solution — a regime-2 echo of the regime-1 equivalence.

The shared proof block in the schema is generalized from `equivalence_proof` to **`proof`** with a `kind`
(`equivalence` | `governing`) and a `heading`, so the player shows the right framing. Dimensional homogeneity
is checked as in regime 1.

**Consequences.** Regime 2 keeps a machine-checked proof shown to the reader — now "this closed form provably
solves the equation of motion, and the memorized results fall out of it." The honesty axes are unchanged;
modeling assumptions (linear vs quadratic drag, ideal spring) remain author-asserted and disclosed.

## ADR-0014 — The integral instrument off the time axis: a general "area = integral" graph kind (2026-06-26)

**Context.** The whole engine assumed the integration variable is **time** and the visual instrument is the
stacked x–t/v–t/a–t graph. But a comprehensive course integrates over things other than time: work `∫F dx`
(position), thermodynamic work `∫P dV` (volume), electric potential `∫E·dl`, the field of a charge
distribution `∫dq/r²`, moment of inertia `∫r² dm`. The project's own thesis — "the area under the lower graph
is the change in the upper" — is axis-agnostic, but the data model (the `Scenario`, the schema's `series`,
the parity gate, the player) hard-wired `{t,x,v,a}`. Generalizing off the time axis is the highest-leverage
architectural move toward breadth: once the engine can put **area-under-a-curve = accumulated integral** on
*any* axis, work-energy, thermo PV-work, and E&M field/potential integrals become authoring, not engineering.

**Decision.** Add a second, parallel instrument — the **area (integral) graph** — without disturbing the
temporal stack:
1. A model may return a `Scenario` whose temporal fields (`t/x_expr/v_expr/a_expr`) are `None` and that instead
   carries an **`AreaPlot`**: an integrand `f(u)` and its accumulated integral `g(u) = ∫_{u0}^{u} f du` over a
   general axis `u`, with axis/panel labels, parameter sliders, and a **cursor** (the upper-limit slider). The
   shaded area under `f` up to the cursor *is* `g`; the slope of `g` *is* `f` — the thesis, on the `u` axis.
2. A new graph **`kind:"area"`** in the schema, with its own `area_series` shape `{u,f,g,u_max}` (gated by
   kind, alongside the temporal `series`), `closed_form{f,g}`, a `cursor`, and `u_label/f_label/g_label`. The
   browser-side axis variable is normalized to the canonical `u` (emit substitutes the model's symbol → `u`),
   so the series key, the closed-form param, and the cursor name always agree.
3. A third **proof kind `"integral"`** (alongside `equivalence`/`governing`), proven via the same
   `tiered_zero`: `g'(u)=f` (FTC / slope↔value), `g=∫f du` (area↔change), the **memorized result falls out**
   of the integral (`½mv²=W`; `nRT ln(V₂/V₁)`), and the **constant-integrand case collapses to the rectangle**
   (`W=Fd`; `W=PΔV`) — the regime-1 quadrature echo, now on the work axis.
4. A static poster (`graph.render_area`) and a new **`AreaPlot.svelte`** island render the two-panel figure
   with a draggable cursor. `check-parity.mjs` and `validate-solutions.mjs` were made axis-agnostic (`u` or
   `t`), so the same 1e-9 oracle proves the area closed forms the browser evaluates.

**Regime-3 with a calculus underpinning.** Thermodynamics is regime 3 (algebra-only), yet PV-work has a clean
calculus underpinning (`W=∫P dV`). Per Phase-3 policy ("surface calculus underpinnings only where clean"), a
regime-3 area lesson shows that underpinning without claiming a dual register: the badge stays "regime 3 ·
algebra-only" and the proof kind is `integral`, not `equivalence`.

**Consequences.** Proven on two lessons across two axes with **no engine change between them**: **work-energy**
(`∫F dx`; position; regime 2; mechanics) and **isothermal PV-work** (`∫P dV`; volume; regime 3; thermo —
opening Phase 3). The second reused the schema, the gates, and the island untouched — the demonstration that
the hard instrument makes a domain's granular lessons simple. The frontier the area instrument does *not* yet
cover is a **numerically-integrated** curve with no elementary closed form — that is the separate
`sampled`-interpolation open question (ADR-0012) — **now resolved by ADR-0015**. A future instrument that
needs a vector or multi-panel integral (an E&M field) would extend `AreaPlot`, not replace it.

## ADR-0015 — The trajectory instrument (2D projectile) + a verification model for numerically-integrated motion (2026-06-26)

**Context.** Everything before was 1D: a single x(t) over time, or an integral over one axis. 2D projectile
motion is the first genuinely vector scenario, and it splits into the two cases the engine had never handled:
a **drag-free** path (each component is constant-acceleration motion — an *exact* closed form, plotted as
y-vs-x) and a **quadratic-drag** path (m v̇ = mg − b|v|v — coupled components, **no elementary closed form**:
the motivating case for the `sampled` mode parked in ADR-0012).

**Decision.**
1. **A trajectory graph kind** (`kind:"trajectory"`): the path y vs x (the parametric trace of two
   independent 1D motions), carried by a `TrajectoryPlot` on the `Scenario` (temporal `x/v/a` left `None`),
   with its own `traj_series {t,x,y,t_max}` schema shape, a `Trajectory.svelte` island, and `render_trajectory`.
2. **Drag-free (regime 1, exact).** x(t)=v₀cosθ·t and y(t)=v₀sinθ·t+½gt² are exact polynomials; the graph is
   `interactive` (launch-angle and speed sliders, closed-form-in-JS, parity-verified). The proof is
   `equivalence`: each component solves its constant-acceleration EOM, and the memorized projectile formulas
   (range, height, flight time) fall out of the component integrals — regime 1, in 2D.
3. **Quadratic drag (regime 2, numerical).** No closed form, so the producer integrates the vector ODE by
   fixed-step RK4 and ships the path as `frames` of sample points swept over **one** parameter (the drag
   coefficient b); the slider snaps between numerically-integrated trajectories, with the drag-free parabola
   overlaid as a `reference`. A single-parameter sweep avoids the committed-data blow-up ADR-0012 warned about
   for a 2-D launch grid.
4. **A verification model for numerical motion** (the governing proof, extended for no-closed-form solutions,
   in the ADR-0010 split):
   - **Producer (strong, local, refuse-to-emit):** each path is verified RK4-**converged** (halving the step
     moves the range < 1 mm), made to satisfy the **equation-of-motion residual** (central-difference
     acceleration matches g − (b/m)|v|v to < 1e-2 m/s²), and the **b=0 path is cross-checked against the exact
     analytic parabola** (independent ground truth). A failure raises; nothing is emitted.
   - **CI Node re-gate** (`check-trajectory.mjs`, the analog of `check-parity` for paths with no closed form):
     the committed points are structurally sound (start at the origin, land at y≈0, t increasing, finite,
     y≥0), the b=0 frame reproduces the exact parabola range, and the range is **monotonically non-increasing
     in the drag coefficient** (drag can only shorten the flight). The strong physics lives in the producer;
     the Node side re-checks what it can do exactly.

**This resolves the ADR-0012 parked question** for its motivating case: the no-closed-form region is handled
by numerically-integrated, individually-verified frames the slider snaps between — *not* by continuous
interpolation between samples, so no interpolation-error gate is needed (the committed sample density just
sets drawing smoothness; the *physics* accuracy is the producer's converged solution).

**Consequences.** The engine now spans 1D temporal motion, the integral instrument, and 2D trajectories —
drag-free (exact) and drag (numerical). "Verification is the product" extends to numerically-integrated
solutions: the path is converged, satisfies the EOM, and recovers the exact parabola at zero drag, all
machine-checked. Honesty axes unchanged; the quadratic-drag model and the use of numerical integration are
author-disclosed. Future numerical models (anharmonic oscillators, non-1/r² orbits) reuse this exact pattern
(RK4 + producer verification + the trajectory / `check-trajectory` gate).

## ADR-0016 — Orbits: a centred `frame:"orbit"` for the trajectory instrument + conservation-gated numerical ellipses (2026-06-26)

**Context.** Orbits are the payoff of gravitation, but the trajectory instrument (ADR-0015) hard-coded a
*projectile* frame: the origin at bottom-left, a ground line, `set_xlim(-0.04·xmax, …)` clipping negative x,
and a `check-trajectory.mjs` that asserts "starts at the origin, lands at y≈0, range monotonic in drag." A
closed orbit loops around a central body, lives in all four quadrants, and never lands — none of those
projectile assumptions hold. The question parked across earlier sessions ("orbits need a trajectory-gate
generalization") was really two questions: the **render frame** and the **verification**.

**Decision.** Reuse `kind:"trajectory"`; switch behavior on a new **`frame` field** (`"ground"` default |
`"orbit"`), so the two working projectile lessons are byte-stable.
1. **Centred frame.** `render_trajectory` and `Trajectory.svelte` gain an orbit branch: equal aspect (a circle
   reads as a circle), a central body / focus at the origin, a producer-supplied fixed `view_half` (so widening
   the orbit visibly grows the loop rather than auto-fitting), and no ground line.
2. **Circular orbit (regime 1, exact).** `x=R\cosωt`, `y=R\sinωt`, `ω=√(μ/R³)` is an exact closed form, so it
   reuses the parity gate with **no gate change** — and since `check-trajectory` only validates trajectory
   graphs *with frames* (numerical), it correctly skips the interactive orbit. Proof `equivalence`: the path is
   a circle, solves the inverse-square EOM, and `v=√(μ/R)` + Kepler's third law fall out.
3. **Elliptical orbit (regime 2, numerical).** No elementary time-parameterisation (Kepler's equation is
   transcendental), so the producer RK4-integrates `r̈=−μr/r³` for one period from perihelion, sweeping the
   **eccentricity at fixed semi-major axis a** (so every orbit shares the period — Kepler III). It refuses to
   emit unless energy `½v²−μ/r` and angular momentum `x·ẏ−y·ẋ` are conserved, the orbit **closes**, and `e=0`
   recovers a circle. A `check-trajectory.mjs` **`frame=="orbit"` branch** re-checks the committed points with
   exact geometry: finite, closes, **encircles the focus exactly once** (total turning ≈ 2π), `e=0` is a circle,
   and all frames share the period. Proof `governing`.

**Consequences.** Kepler's three laws all fall out, paint-verified live (geostationary T≈24 h; an `e=0.5`
ellipse with the same period as its circle, perihelion 3× faster than aphelion). The projectile and orbit cases
share one kind, one island, one renderer, and one gate file, branched on `frame`. The same numerical pattern
(RK4 + conservation-gate) now covers any central-force orbit.

## ADR-0017 — The energy-exchange bars: a fourth instrument for conservation laws (2026-06-26)

**Context.** Three instruments cover a curve over time (the stack), an integral over an axis (area), and a 2D
path (trajectory). But a **conservation law** — kinetic and potential energy trading while their sum is fixed —
is none of those: it is two quantities exchanging, best shown as **bars** that trade with a flat total, not a
curve or a path. Energy conservation and (next) collisions are core mechanics the brief requires and the
existing instruments cannot frame.

**Decision.** Add a fourth, parallel instrument — the **energy-exchange bars** (`kind:"energy"`) — wired
exactly like the area instrument (ADR-0014), so it inherits the verification for free:
1. A model returns a `Scenario` carrying an **`EnergyPlot`**: `ke_expr(u)` and `pe_expr(u)` over a cursor axis
   `u` (a height/position), with parameter sliders and the canonical-`u` normalization. The island draws KE, PE,
   and Total bars; as the cursor moves the KE/PE bars trade while **the Total bar stays flat — conservation made
   visible** — plus a height indicator and a live speed readout.
2. A schema `kind:"energy"` with an `energy_series {u,ke,pe,u_max}` shape and `ke_label/pe_label/total_label`;
   `closed_form{ke,pe}` and a `cursor`. The kind-agnostic **parity oracle re-checks the KE/PE closed forms** the
   browser evaluates (1e-9) — no new gate. `render_energy` is the static poster; `EnergyBars.svelte` the island.
3. Proof kind `governing`: energy conservation is the **first integral of `F=ma`** (`mv\,dv=F\,dx ⇒ ½mv²=∫F\,dx`).
   The checks are `d/dh(KE+PE)=0`, the conservation law, the speed falling out, and `KE=∫_h^H mg\,dh'` — which
   makes the speed **path-independent** (a steep and a gentle frictionless ramp to the same depth give the same
   bottom speed).

**Consequences.** Proven on conservation of energy (frictionless ramp; regime 2; mechanics), paint-verified
(the Total bar holds while KE/PE trade; bottom speed `√(2gH)`). The next lesson, collisions/momentum, reuses
the bars idea in a **before/after** two-state mode (momentum bars always equal; KE bars equal only if elastic) —
either an `EnergyPlot`/`EnergyBars` extension or a sibling `kind:"collision"`. Like ADR-0014, the hard part was
the instrument; new conservation lessons are model + spec + test.

## ADR-0018 — The collision bars: a fifth instrument for before/after conservation (2026-06-27)

**Context.** The energy bars (ADR-0017) show one continuous state trading along a cursor. A **collision** is
different: it compares **two discrete states** (before / after) of *two* conserved-or-not quantities at once —
total momentum (always equal) and total kinetic energy (equal only if elastic). That is not a curve, a path, or
a single-cursor bar trade; the lost kinetic energy *is the lesson*, and it only reads against the unchanged
momentum total beside it. The energy bars' single-cursor frame cannot say "before vs after."

**Decision.** Add a fifth, parallel instrument — the **collision bars** (`kind:"collision"`) — wired like the
area/energy instruments so it inherits the verification for free:
1. A model returns a `Scenario` carrying a **`CollisionPlot`**: the closed-form final velocities `v1f(e,m1)`,
   `v2f(e,m1)` of a 1D two-body collision, with the **coefficient of restitution `e` as the cursor** (0 =
   perfectly inelastic … 1 = perfectly elastic), the incident mass `m1` a slider, and `m2/v1/v2` constants
   (exported as `consts` for the island). The island forms the before/after **momentum** and **kinetic-energy**
   stacked bars from the finals: the momentum total is pinned at every `e` (only the per-body split shifts),
   while the KE total collapses as `e→0`, the gap shaded as energy lost.
2. A schema `kind:"collision"` with a `collision_series {u,v1f,v2f,u_max}` shape (axis `u`=e) and a `consts`
   object; `closed_form{v1f,v2f}` + a `cursor`. The kind-agnostic **parity oracle re-checks `v1f,v2f`** the
   browser evaluates (1e-9, axis auto-detected as `u`) — **no new gate**. `render_collision` is the static
   poster (momentum before/after equal; KE before/after-elastic/after-inelastic, the inelastic bar short);
   `Collision.svelte` the island (a before/after block schematic + the two bar groups).
3. Proof kind `governing`: momentum conservation is the **time-integral of Newton's third law** — the contact
   forces are equal and opposite at every instant, so the impulses `J=∫F dt` cancel for *any* force profile.
   The checks are `m₁v₁'+m₂v₂'=m₁v₁+m₂v₂` (every `e`), the restitution relation, the KE-loss identity
   `½μ(1−e²)(Δv)²` (μ the reduced mass), `e=1 ⇒` KE conserved, and `e=0 ⇒` the common velocity `v_cm`.

**Consequences.** Proven on a 1D cart collision (2 kg @ 3 m/s into 1 kg at rest; regime 2; mechanics),
paint-verified (momentum 6→6 at every `e`; KE 9→9 elastic, 9→6 with 3 J/33 % lost perfectly inelastic; equal
masses elastic → full transfer, the incident cart stops dead). Five instruments now: temporal stack · area ·
trajectory · energy bars · collision bars. The pattern holds — the hard part was the instrument; a second
collision lesson (head-on, or 2D) would be model + spec + test.

## ADR-0019 — Graph-island CSS delivery (`css: "injected"`) + declared full dark mode (2026-06-27)

**Context.** The owner reviewed the live site and found every interactive graph instrument rendering as solid
black SVGs — unreadable (and invisible on their dark browser). Root-caused live: Astro/@astrojs/svelte delivered
the scoped `<style>` of the **top-level** island components used directly in `.astro` with `client:load`
(`SolutionPlayer`, `ConceptGraph` — their chrome was styled), but **not** the scoped `<style>` of the **child**
graph components those islands import and render internally (`GraphStack`, `AreaPlot`, `Trajectory`,
`EnergyBars`, `Collision`). The children fell back to browser-default black SVG fills — broken in *light* mode
too; the owner's force-dark browser merely made it black-on-black. Compounded by: no `color-scheme` declaration
(so a force-dark browser mangled the page), and the static Matplotlib posters being baked light.

**Decision.**
1. **Deliver child-island CSS at the source:** `svelte({ compilerOptions: { css: "injected" } })` in
   `astro.config.mjs` — every Svelte component (including children) ships its scoped CSS via its JS chunk and
   injects it on mount. One line; **no island edits**; dark mode then works automatically through the existing
   `@media (prefers-color-scheme: dark)` variable swap. (A global-utility-class fallback in `portal.css` was
   designed as a backup but proved unnecessary — the config fix fully resolved it.)
2. **Declare dark mode** so browsers stop force-darkening: `<meta name="color-scheme" content="light dark">`
   (Base.astro) + `color-scheme: light dark` on `:root` (portal.css). The existing dark variable block is correct.
3. **Static posters on a fixed-light figure card:** the committed Matplotlib SVGs are baked light, so `.svgwrap`
   gets an always-light `--figure-paper` background + border (does not flip in dark mode), reading as an
   intentional figure in both themes.

**Consequences.** Verified live via computed styles in both `colorScheme` light and dark across all five
instruments (bars/curves/text resolve to the right `var(--*)` values; SVG backgrounds are `--paper`).
Verification lesson recorded: **prior "paint-verified" passes only checked DOM geometry/values, never computed
colors** — which is why this shipped broken. Going forward, verify `getComputedStyle().fill/stroke` on a
representative SVG element. Also polished in this pass: lesson "formulas used" now deep-link to `/reference/#id`;
`role="tabpanel"` on the register panels; an `aria-label` on the reference variable tables.

## ADR-0020 — Concept graph: clean Unicode labels + domain-clustered layout (2026-06-27)

**Context.** The 71-node concept graph showed **raw LaTeX** in node labels (`\tau`, `\Phi`, `\frac{1}{f}`,
`F_{\text{net}}`, …) because the label was the formula's `lhs` rendered as plain SVG `<text>`, and its frozen
640×480 single-blob force layout was badly overcrowded.

**Decision.** Both fixes are producer-side (`reference.py`), regenerated by `prepare:data`, no schema change.
1. **Labels → curated Unicode** via `_clean_label(lhs)` + `_LABEL_MAP` (e.g. `\tau→τ`, `\frac{1}{f}→1/f`,
   `\Delta U→ΔU`, `F_{\text{net}}→F_net`, `P_2→P₂`), with generic fallbacks (strip `\text{}`, a Greek table,
   `\frac{a}{b}→a/b`, numeric subscripts→Unicode) for future formulas. All 16 LaTeX-bearing labels covered.
2. **Layout → domain-clustered on a larger canvas** (`_layout`): each node is seeded near its domain anchor and
   weakly pulled toward it each step, so the five domains settle into distinct regions; canvas 640×480→900×640,
   stronger repulsion + longer edge rest length. Deterministic (seeded RNG kept). Residual overlap (~13 of 2485
   pairs in the dense mechanics core) is handled by the island.
3. **Island** (`ConceptGraph.svelte`): an ink **halo** on labels (`paint-order: stroke`) so they stay legible
   where they overflow a circle; **pan/zoom** (wheel + buttons + background-drag-pan), with node-drag mapped
   through the inner group's CTM so it stays correct at any zoom/pan; and a **domain color legend**.

**Consequences.** Paint-verified: 71 clean Unicode labels (zero raw LaTeX), 900×640 viewBox, zoom-about-center
+ background-pan + node-drag all functional, domain legend present. Adding any formula re-runs the deterministic
layout (expected churn).

## ADR-0021 — The N-panel temporal stack (generalizing x/v/a) (2026-06-27)

**Context.** The temporal stack was hard-wired to exactly three panels (x/v/a) in both the producer and
`GraphStack.svelte`. RC charging, LC, and radioactive decay are derivative/integral *pairs* (Q–I, N–dN/dt) that
want a 2-panel stack with the same slope↔value pivot — the marquee "E&M/nuclear meets calculus" lessons.

**Decision.** Add an optional `panels: [Panel(key, expr, label, unit, accent)]` to the `Scenario` (beside the
default x/v/a). When set: `build.py` emits a `panels` metadata array + a `panel_series` keyed by each panel
(`emit.closed_form_panels`/`sample_panels_series`), `graph.render_panels` draws the static poster, and
`GraphStack.svelte` renders N bands from the panel list (the x/v/a path is byte-unchanged — apex/landing/area
features guard on `fns.x`/`fns.v`). The schema adds a `panels` property + a permissive `panel_series` def and
switches the `series` field from `oneOf`→`anyOf` (so a standard x/v/a series and a panel series don't fight for
exclusivity). The **kind-agnostic parity oracle re-checks the panel closed forms** — no new gate.

**Consequences.** Proven on **RC charging** (regime 2, Q–t over I–t: I is the slope of Q, the RC ODE
back-substitutes, τ=RC falls out) and **radioactive decay** (regime 2, N–t over dN/dt–t, opens the modern unit).
Paint-verified: both render 2 panels with the rate panel accented and the sliders driving the curves; the
existing x/v/a stacks (throw-up interactive, damped sampled) are unaffected. LC oscillation is now a near-free
clone.


## ADR-0022 — Verified practice questions: "solve it three ways" (2026-06-27)

**Context.** Lessons teach a concept in two registers; practice should cement it *in the same two registers*,
not bolt on a generic homework grader. The course's principle is "we are not an interactive homework site —
practice is built from what we already do well." Reasoning-heavy physics exams test the *same* scenario at two
math levels (a memorized-formula answer vs. a derivative/integral/ODE derivation) and lean on
misconception-based multiple-choice distractors. That maps exactly onto the engine we already have: verified
results, stepped algebra/calculus registers, and the misconception register.

**Decision.** A new **opt-in, build-time-verified content type**, with no new gate and no new engine.
1. **Authoring** — `[[practice]]` blocks in `problems/<topic>/<slug>.problem.toml`. Each names the quantity
   asked (`answer = "result:<key>"` into the lesson's verified `algebra.result`, or a SymPy expression in the
   scenario's symbols + initial conditions), a prompt, an optional `include = ["algebra","calculus"]` (which
   *reuses the lesson's own step registers* — no duplicate step prose), and `[[practice.distractor]]`s, each a
   `method` (named misconception key) + a SymPy `transform` + a `misconception` explanation.
2. **Producer** (`practice.py`, hooked in `build.py`) — evaluates the answer and every distractor at the
   scenario defaults and **fails the build loud if any distractor is non-finite or collides with the correct
   answer**. A distractor that equals the truth is a build break, exactly like a failed parity check. So every
   wrong answer is *machine-derived from a stated misconception* and *proven wrong*.
3. **Schema** — an optional top-level `practice[]` + `$defs/practice_question` (`additionalProperties:false`),
   reusing `$defs/step` for the step-throughs. The multiple-choice block requires ≥2 choices and exactly one
   `correct`.
4. **Gates (extended, none added)** — Ajv validates the block; `validate-solutions` enforces unique ids /
   exactly-one-correct / finite values; `check-katex` renders every prompt, choice, misconception, and reused
   step; `check-parity` re-asserts (without Python) that the answer and choices are finite and that each
   distractor is distinct from the answer; `scan-text` already covers the new prose.
5. **Frontend** — `PracticeQuestion.svelte` (a "Practice" tab in `SolutionPlayer`, shown only when the lesson
   has questions): a multiple-choice reveal (pick → mark correct/incorrect, surface the chosen distractor's
   misconception, show the answer + its symbolic form) plus Algebra and Calculus step-throughs. It **computes
   nothing and stores nothing** — no scoring, no persistence, no login. Choices are ordered by a stable hash of
   `(id, value)` so the answer isn't always first and SSR/hydration agree. All LaTeX is baked to HTML at build
   time by `renderSolution` (`view.js`).

**Consequences.** Practice is as verified as the lesson: every answer is the already-proven result and every
distractor is SymPy-derived from a named error and proven distinct. Piloted one-per-regime (`throw-up` R1,
`rc-charging` R2, `isothermal-work` R3) with a "solve-it-three-ways" anchor + misconception multiple-choice
quick-checks, and seeded on the three new lessons (LC, isobaric, Faraday). Fanning practice out to the
remaining lessons is pure authoring. Natural follow-ons: FRQ-style multi-part chains and the §8
hover-to-reference backbone.


## ADR-0023 — The standing-wave instrument: a spatial mode viewer (2026-06-27)

**Context.** Waves & optics had a reference cluster but no lesson, because thin-lens and standing waves fit
none of the five existing instruments — all of which assume a continuous *time* or *integration* axis. Standing
waves are about *discrete spatial modes*: a shape y(x) that changes with an integer mode number n. Forcing them
onto the temporal stack or the area instrument would be dishonest.

**Decision.** Add a sixth instrument, `kind:"standing"` (`StandingPlot` + `StandingWave.svelte` +
`standing_wave.py` + `render_standing`), modelled on the area instrument's data flow but with a **position
axis** and an **integer mode cursor**:
1. The producer ships the parity-verified closed form y(u; n) = A·sin(nπu/L) over the canonical `u` axis (u =
   position x), an n-slider in `params`, a `consts` block (v, L, A, n_max), and a producer-computed `modes[]`
   harmonic table (n, f_n, λ_n). Because it reuses the `u` axis, the **kind-agnostic parity oracle re-checks it
   with no gate change** — only the schema gained a `standing_series` def, a `modes[]` property, and a
   `kind=="standing"` required-fields branch.
2. The proof is `governing` and surfaces the honest calculus underpinning of a regime-3 topic (Phase-3 policy):
   the mode solves the wave equation ∂ₜₜy = v²∂ₓₓy; the fixed-end boundary conditions sin(kL)=sin(nπ)=0
   **quantize** the modes (this is *why* only integer harmonics appear); the standing wave is a superposition of
   two counter-propagating travelling waves; and f_n = nv/2L, λ_n = 2L/n fall out. (n is a SymPy integer symbol,
   so sin(nπ) collapses to 0 at construction — the boundary check certifies symbolically.)
3. The island draws the mode shape with its ±envelope, the **nodes pinned as n changes** (the visual heart of
   "boundary conditions quantize"), the two walls, and a clickable harmonic table; the n-slider steps by
   integers and the curve recomputes from the closed form.

**Consequences.** Opens the Waves & optics unit with a genuine dual-register lesson (the harmonics handed down
as a rule vs. derived from the wave equation + boundary conditions). Six instruments now: temporal stack ·
area/integral · trajectory · energy bars · collision bars · **standing waves**. 110 producer tests, 30 lessons,
parity 6274, all six gates green. Thin-lens optics still has no instrument (a ray-diagram renderer is a separate
future build); standing waves were the higher-value opener.


## ADR-0024 — The thin-lens ray-diagram instrument: a geometric construction as the second register (2026-06-27)

**Context.** Thin-lens optics was the last flagged gap in Waves & optics (ADR-0023 noted it "still has no
instrument"). It fits none of the six prior instruments: there is no time axis, no integration axis, no mode
ladder — image formation is a *geometric construction*. And its honest "second way" is not calculus at all:
optics at this level is geometry, so forcing it into a "Calculus" register would be the same dishonesty
ADR-0023 refused for standing waves.

**Decision.** Add a seventh instrument, `kind:"lens"` (`LensPlot` + `Lens.svelte` + `thin_lens.py` +
`render_lens`), plus a small honesty-preserving frontend generalization:
1. **The instrument is a live ray tracer.** A converging lens of *fixed* focal length f sits at the origin; the
   object distance d_o is the cursor (mapped to the canonical `u` axis, so the kind-agnostic parity oracle
   re-checks the closed forms with **no gate change** — only a `lens_series {u,di,hi,m}` schema def and a
   `kind=="lens"` required-fields branch were added). The producer ships parity-verified closed forms
   d_i(d_o)=d_o f/(d_o−f), h_i(d_o,h_o)=−h_o f/(d_o−f), m(d_o)=−f/(d_o−f); the island *draws the three
   principal rays* (parallel→F′, chief through the centre, focal→parallel) with Liang–Barsky viewport clipping
   and reads off where they cross. As d_o crosses f the image flips real/inverted (projector) ↔ virtual/upright/
   enlarged (magnifying glass), with dashed backward-extension rays in the virtual case. **f is a fixed
   constant, never a slider**, so the singularity at d_o=f never moves; the sample grid is chosen to straddle it
   without landing on it (the sampler fails loud if a sample lands within 1e-7 of f).
2. **Proof `governing`, regime 3.** The second register is the ray diagram, and SymPy proves it *is* the lens
   equation: the closed-form d_i satisfies 1/d_o+1/d_i=1/f; the chief ray gives m=−d_i/d_o by similar triangles;
   the parallel and focal rays give the *same* magnification (the three constructions agree at one point — which
   is exactly the thin-lens equation); and m=f/(f−d_o). (Fermat's stationary-path principle is noted as the one
   genuinely-calculus statement underneath, but not derived.)
3. **A per-lesson `register_label` override** (optional `calculus.register_label`, default "Calculus"): a
   regime-3 lesson whose honest second register is *not* calculus relabels the tab — here "Ray diagram." Threaded
   through `SolutionPlayer` (the register tab + aria) and `PracticeQuestion` (the practice step-through tab), so
   the dishonesty of calling geometry "calculus" never appears. The schema gained one optional string field.
4. **Markdown emphasis in authored prose (`inline()`).** Authored scenarios/steps/misconceptions carry
   `**bold**`/`*italic*` pervasively (≈65 bold + ≈272 italic pairs site-wide) that `inline()` — math-only — had
   been emitting as **literal asterisks**. Added escape-then-emphasize (bold before italic; unmatched asterisks
   left literal; applied only to non-`$…$` segments). One function, no gate change, fixes every authored surface
   at once. (The earlier guide-page fix had worked *around* this for one string; this fixes the root.)

**Consequences.** Seven instruments now; Waves & optics has both its lessons (standing waves + thin lens) and
the last domain gap on the proven engine is closed. The `register_label` override is the general hook for any
future regime-3 lesson whose second way is geometric/graphical rather than calculus. Practice also fanned out
further (a verified second question on eight foundational lessons across kinematics, energy, momentum,
oscillations, gravitation, and circuits). 117 producer tests, 31 lessons, parity 6467, all six gates green.

**Variant (same session): the diverging lens.** The instrument generalizes to **f < 0** with no engine change —
the same model, closed forms, proof, and `kind:"lens"` island, parameterized by the sign of f. The model's
straddle guard is gated on f>0 (a diverging lens has no singularity to straddle); its step prose and the
island's readout/chips are driven by the *computed* image character (real/virtual, upright/inverted,
enlarged/reduced) rather than hard-coded converging language; the island's parallel-ray direction is written
sign-generally (slope −hₒ/f, so it diverges when f<0) and the focal-point labels use |f| (F left, F′ right, no
swap); the lens glyph draws inward arrowheads for a diverging element; and `render_lens` grew a virtual-image
branch (dashed backward extensions). The new lesson — *the diverging lens: one image, always virtual* — shows
that for **every** object distance dᵢ<0 and 0<m<1 (virtual, upright, reduced), the complement to the converging
lens. 119 producer tests, 32 lessons, parity 6652, all six gates green.
