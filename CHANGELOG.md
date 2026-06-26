# Changelog

Notable changes, newest first. Architecture rationale lives in [`DECISIONS.md`](./DECISIONS.md); the phase
plan in [`ROADMAP.md`](./ROADMAP.md).

## [Unreleased] — Phase 1: full mechanics (in progress)

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
