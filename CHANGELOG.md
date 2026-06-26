# Changelog

Notable changes, newest first. Architecture rationale lives in [`DECISIONS.md`](./DECISIONS.md); the phase
plan in [`ROADMAP.md`](./ROADMAP.md).

## [Unreleased] — Phase 0 vertical slice

Building the end-to-end instrument on one scenario: vertical motion under constant gravity.

- Repo scaffold: Astro 7 + Svelte 5 + KaTeX player, a SymPy (uv) producer, Ajv + parity + scan Node gates,
  GitHub Pages workflow (Pages disabled until review).
- Documentation/governance system seeded: AGENTS.md, DECISIONS.md (ADR-0001…0011), ROADMAP.md, this changelog,
  `docs/` (architecture, authoring-problems, authoring-formulas, regime-map, house-conventions, SOURCES), and
  a per-session log under `docs/sessions/`.
- Provider-agnostic from day one: founding brief renamed `QUADRATURE_BRIEF.md → PROJECT_BRIEF.md` (gitignored)
  and a `scan-text.mjs` build gate.
- Licensing: MIT (code) + CC BY-SA 4.0 (content).
