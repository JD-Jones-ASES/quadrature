# ROADMAP — Quadrature, phase by phase

The multi-session backbone. Each phase: **goal · scope · definition of done**. We open every phase with its
single most-complex "stress" scenario (so the granular fill inherits a solved instrument — the build method
from `JD.md`), then fill depth-first, and close with a doc sweep. Status lives here; history in
[`CHANGELOG.md`](./CHANGELOG.md); rationale in [`DECISIONS.md`](./DECISIONS.md).

## Status

- **Phase 0 — vertical slice — COMPLETE, awaiting review** (built 2026-06-26). Producer, gates, player,
  reference, and concept graph all working end-to-end and pushed to the private repo. Pages intentionally not
  yet enabled. **Stop here for owner review before Phase 1.**
- Phases 1–3 and the reference breadth-fill: not started.

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

**Open questions to resolve at the top of Phase 1 (brief §12).**
- **ODE strategy.** Most regime-2 closed forms aren't cheap polynomials, so most regime-2 graphs are static by
  the ADR-0009 policy. Confirm that, or add a small **precomputed-sample-points** export to drive a limited set
  of regime-2 interactives (a third graph mode between `static` and polynomial `interactive`).

**Definition of done.** The mechanics lessons run on the proven instrument; regime 2 is visibly the half where
calculus does what algebra can't; the reference covers all mechanics formulas.

## Phase 2 — electricity & magnetism (dual register)

**Goal.** The second domain where both an algebra and a calculus version exist.

**Scope.** Electrostatics, fields, potential, circuits, capacitors, magnetism, induction.

**Definition of done.** E&M dual-register lessons + full E&M reference coverage.

## Phase 3 — the algebra-only domains

**Goal.** Cover the domains with no calculus-based counterpart at the algebra level; surface calculus
underpinnings only where clean.

**Scope.** Fluids, thermodynamics, waves & optics, modern physics. Calculus underpinning optional and only
where natural (e.g. work as `∫P dV` on a PV diagram). Do **not** force a dual register where one doesn't exist.

**Definition of done.** Algebra-level lessons + reference coverage for all four domains.

## Parallel track — the reference breadth-fill

After Phase 0 review, populate the §8 formula/concept reference **breadth-first** across the full union of
offerings (ADR-0007), independent of which lessons exist. Tracked against
[`docs/regime-map.md`](./docs/regime-map.md). Goal: the reference is a comprehensive, SymPy-verified, fully
interlinked formula sheet early, while lessons trail depth-first.

## Out of scope (v1)

Experimental design, lab procedure, and data-collection writeups (brief §9). Linearizing data to extract a
slope is in-spirit and may be revisited, but it is not Phase 0–1.
