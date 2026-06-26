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
