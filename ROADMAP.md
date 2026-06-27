# ROADMAP — Quadrature, phase by phase

The multi-session backbone. Each phase: **goal · scope · definition of done**. We open every phase with its
single most-complex "stress" scenario (so the granular fill inherits a solved instrument — the build method
from `JD.md`), then fill depth-first, and close with a doc sweep. Status lives here; history in
[`CHANGELOG.md`](./CHANGELOG.md); rationale in [`DECISIONS.md`](./DECISIONS.md).

## Status

- **Phase 0 — vertical slice — COMPLETE, reviewed, PUBLISHED** (2026-06-26). Producer, gates, player,
  reference, and concept graph end-to-end; the repo is public and the site is **live** at
  https://jd-jones-ases.github.io/quadrature/ (every push to `main` auto-deploys).
- **Phase 1 — full mechanics — IN PROGRESS.** Lessons: free fall (1), SHM (2), terminal velocity (2), damped
  oscillator (2, sampled), **work–energy (2, area)**, **projectile drag-free (1) and quadratic drag (2,
  numerical)**, **impulse–momentum (2, area on the time axis)**, **rotational kinematics (1, stack)**,
  **gravitational PE (2, area on the radial axis)**, **moment of inertia (2, area on the mass-distribution
  axis — `∫r² dm`)**, **rotational work–energy (2, area on the angle axis — `∫τ dθ → ½Iω²`)**,
  **hydrostatic force on a wall (2, area on the depth axis — opens the fluids domain)**, the
  **circular (1) and elliptical (2) orbit** (trajectory on a centred frame — `v=√(μ/R)` & Kepler's three laws),
  and **conservation of energy (2, the energy-bars instrument — path-independent `v=√(2gH)`)**.
  Engine now has **four graph instruments**: the temporal stack, the **integral instrument** (ADR-0014), the
  **2D trajectory instrument** (ADR-0015, drag-free exact + quadratic-drag numerical + a centred `frame:"orbit"`
  for orbits), and the **energy-exchange bars** (`kind:"energy"` — KE/PE trade, Total flat).
- **Phase 2 — electricity & magnetism — OPENED.** E&M lessons: **energy in a capacitor** (`∫V dq → ½CV²`,
  regime 2, area on the charge axis) and **electric potential energy** (`∫kq₁q₂/r² dr → kq₁q₂/R`, regime 2,
  area on the separation axis — the electric twin of gravitational PE, with the area to infinity converging to
  a finite binding energy), both built with no engine change. A **14-formula E&M reference**:
  electrostatics (Coulomb, point-charge field & potential, electric PE), circuits (capacitance, capacitor
  energy, Ohm's law, electrical power, RC time constant), and **magnetism** (Lorentz force, force on a wire,
  field of a long wire, magnetic flux, motional EMF — which seeds induction). Magnetism/induction lessons and
  continuous-charge integrals: not started.
- **Phase 3 — algebra-only domains — SEEDED & DEEPENING.** Thermo: **isothermal** and **adiabatic** PV-work
  lessons (`∫P dV`, regime 3, area instrument) + a 6-formula thermo reference (ideal gas, first law, specific
  heat, internal energy, adiabatic work & relation, Carnot). **Fluids now has its first lesson** — hydrostatic
  force on a wall (`∫ρg w h dh → ½ρgwH²`, regime 2, area on the depth axis), surfacing the calculus
  underpinning the algebra's "average pressure × area." Reference breadth seeded across the remaining
  algebra-only domains too — **fluids** (pressure, buoyancy, continuity, Bernoulli, wall force), **waves &
  optics** (wave speed, period, string, thin lens, magnification), **modern** (photon energy, de Broglie,
  E=mc², photoelectric).
- **Reference: 70 formulas across all five domains**, all SymPy-unit-verified, 70-node / 102-edge concept graph.

---

## Phase 0 — the vertical slice (then STOP for review)

**Goal.** Prove the whole instrument on one scenario: **vertical motion under constant gravity** (a ball
thrown straight up, `g=−10`, with `x₀`, `v₀`). Physically trivial, architecturally maximal — it stresses every
hard piece at once.

**Scope.**
1. Repo scaffold + the documentation/governance system + the neutrality fix.
2. The SymPy producer on the throw-up problem: integrate `a→v→x`; solve algebra for time-to-apex, max height,
   flight time; **prove algebra == calculus**; unit-check; export the closed form + sample points; render the
   Matplotlib stacked SVG.
3. The solution schema + the Node build gates.
4. The player: four registers (scenario · algebra stepped · calculus stepped, with `x=x₀+v₀t+½at²` emerging
   from `∫v dt` · the stacked x–t/v–t/a–t graph with slope↔value / area↔change annotations).
5. One interactive graph: drag `v₀` → parabola, v–t line, and apex move together (closed form in JS).
6. The misconception register: "a = 0 at the apex," refuted live by the unchanged v–t slope at v=0; plus the
   sign-based speeding-up/slowing-down treatment.
7. One fully-interlinked formula entry — `x(t)=x₀+v₀t+½at²` — wired into the reference + a minimal concept
   graph (this node + its integral-of/derivative-of neighbors).
8. Static build → GitHub Pages.

**Definition of done (brief §10).** A deployed page where a learner reads the scenario, steps the algebra,
steps the calculus and *watches the algebra formula fall out of the integral*, sees all three results agree
with SymPy's proof shown (not asserted), drags `v₀` and feels max-height ∝ v₀², watches "a = 0 at the top" die
in the v–t slope, with the one formula entry fully linked into the reference. **Then stop for review.**

## Phase 1 — full mechanics (incl. the regime-2 ODE content)

**Goal.** The dual register across all of mechanics; the first place calculus stops being optional.

**Scope.** Kinematics, dynamics (Newton's laws), energy, momentum, rotation, SHM, gravitation. **Regime 2**:
drag → terminal velocity (exponential approach), a spring (`x''=−ω²x → x=A cos ωt`), gravitation as a function
of r. The producer moves from integrating constants to solving ODEs.

**Resolved (ADR-0012, ADR-0013, 2026-06-26).**
- **Interactivity:** regime 2 is *not* defaulted to static — the large part with elementary closed forms
  (drag→exp, terminal velocity→tanh, SHM→cos, damped→e^{−γt}cos) stays `interactive` on the Phase-0 engine.
  The `sampled` mode (precomputed points + interpolation gate) is reserved for the no-closed-form minority and
  built only when a lesson needs it.
- **Verification:** regime-2 proof = back-substitute the closed form into the equation of motion + initial
  conditions + a conserved/limit invariant + show the memorized result falling out. The proof block is
  generalized (`equivalence` | `governing`).

**Status.** Regime-2 architecture stood up: proven first on **SHM** (the regime-2 "stress node"), then
**terminal velocity (drag)** and the **damped oscillator** (sampled). The **integral instrument** (ADR-0014)
generalized the engine off the time axis (proven on **work–energy**), and the **2D trajectory instrument**
(ADR-0015) added vector motion — drag-free (exact, regime 1) and **quadratic drag** (numerical, regime 2),
the latter resolving the ADR-0012 no-closed-form question with RK4 + a producer/Node verification split.
Since then: gravitation (PE, **circular + elliptical orbits**), rotation (kinematics, moment of inertia, work),
fluids (hydrostatic force), and **energy conservation** (the energy-bars instrument). Remaining mechanics
lesson: **momentum / collisions** (a before/after bar viz) + the rest of the reference fill.

**Definition of done.** The mechanics lessons run on the proven instrument; regime 2 is visibly the half where
calculus does what algebra can't; the reference covers all mechanics formulas.

## Phase 2 — electricity & magnetism (dual register)

**Goal.** The second domain where both an algebra and a calculus version exist.

**Scope.** Electrostatics, fields, potential, circuits, capacitors, magnetism, induction.

**Opened (2026-06-26).** The area instrument made the first E&M lesson clean to ship with no engine change:
**energy in a capacitor** (`∫V dq → ½CV²`, regime 2) — the stored energy is the triangle under the
voltage–charge line, and SymPy proves the memorized `½CV²` falls out; the constant-voltage battery case is the
rectangle `VQ` (twice the energy). A 9-formula E&M reference cluster seeds the rest (Coulomb ↔ gravitation, RC
↔ linear-drag, capacitor ↔ spring edges tie it into the existing graph). Next: an RC-charging temporal lesson
(needs a 2-panel stack or an area reframe — the stack is hard-wired to x/v/a), magnetism, induction, and a
continuous-charge field integral on the area instrument.

**Definition of done.** E&M dual-register lessons + full E&M reference coverage.

## Phase 3 — the algebra-only domains

**Goal.** Cover the domains with no calculus-based counterpart at the algebra level; surface calculus
underpinnings only where clean.

**Scope.** Fluids, thermodynamics, waves & optics, modern physics. Calculus underpinning optional and only
where natural (e.g. work as `∫P dV` on a PV diagram). Do **not** force a dual register where one doesn't exist.

**Seeded & deepening (2026-06-26).** The area instrument (ADR-0014) made the `∫P dV` underpinning clean to
ship, so thermo got an early start and now carries two lessons: **isothermal** and **adiabatic** PV-work
(regime 3, proof kind `integral`) — the same instrument on the volume axis, isotherm `∝1/V` vs the steeper
adiabat `∝V^{-γ}`, with the gas cooling on the adiabat. Reference coverage now reaches all four algebra-only
domains: thermo (first law, specific heat, internal energy, adiabatic, Carnot), **fluids** (pressure, buoyancy,
continuity, Bernoulli), **waves & optics** (wave speed, period, string, thin lens, magnification), and
**modern** (photon energy, de Broglie, E=mc², photoelectric). The pattern (a regime-3 lesson that surfaces a
clean calculus underpinning via the area instrument) is the template for the rest where one exists.

**Definition of done.** Algebra-level lessons + reference coverage for all four domains.

## Parallel track — the reference breadth-fill

After Phase 0 review, populate the §8 formula/concept reference **breadth-first** across the full union of
offerings (ADR-0007), independent of which lessons exist. Tracked against
[`docs/regime-map.md`](./docs/regime-map.md). Goal: the reference is a comprehensive, SymPy-verified, fully
interlinked formula sheet early, while lessons trail depth-first.

**Status (2026-06-26): the breadth-first pass now covers all five domains** — 70 formulas (mechanics incl.
fluids & rotation, E&M incl. magnetism, thermo, waves & optics, modern), a 70-node / 102-edge concept graph,
every formula's LaTeX generated from its SymPy expression and unit-checked. Remaining is per-domain depth (E&M
induction beyond motional EMF, Gauss, the rest of optics, nuclear), not new domains.

## Out of scope (v1)

Experimental design, lab procedure, and data-collection writeups (brief §9). Linearizing data to extract a
slope is in-spirit and may be revisited, but it is not Phase 0–1.
