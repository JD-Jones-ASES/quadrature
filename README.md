# Quadrature

**A dual algebra-based / calculus-based physics course where the verification system is the product.**

**Live:** https://jd-jones-ases.github.io/quadrature/

Physics is taught at whichever altitude the learner needs. If the goal is algebra-based physics, you get a
clean, rigorous course on its own terms. If the goal is calculus-based physics, you *also* get to see the
algebra as **calculus with the work already done** — and you leave with a sense for the physics and a sense for
the calculus that grew up together.

## The idea in three lines

For a ball thrown straight up (up positive, `g = −10 m/s²`):

```
a(t) = −10                       (constant)
v(t) = ∫a dt = v₀ − 10t          (a line; its slope is a)
x(t) = ∫v dt = x₀ + v₀t − 5t²    (a parabola; its slope is v, the area under v is its change)
```

The algebra formulas `v = v₀ + at` and `x = x₀ + v₀t + ½at²` are those integrals with `a` frozen to a
constant. *Quadrature* is the old word for evaluating an integral — finding the area under a curve. The
constant-acceleration formulas are quadratures: integrals already evaluated.

The **stacked x–t / v–t / a–t graph** is the pivot between the two registers: the slope of the upper graph is
the value of the lower; the area under the lower is the change in the upper. That is the derivative/integral
relationship made visible — and where a student with slope-and-area intuition meets the student with `dx/dt`
and `∫v dt`, and they turn out to be the same student.

## What's inside

A two-semester spread, built deep on a verified engine:

- **34 lessons** across 12 units and every major domain — mechanics (kinematics, dynamics, energy, momentum,
  rotation, gravitation/orbits, fluids), electricity & magnetism (circuits, fields, induction), thermodynamics,
  waves & optics, and modern physics. Each is one scenario shown four reconciled ways (scenario · algebra ·
  calculus · interactive graph), with a shown SymPy proof, an honest misconception, and "solve it three ways"
  practice.
- **Seven interactive graph instruments** — the stacked motion graph, the area/integral graph, a 2D
  trajectory (incl. orbits), energy-exchange bars, before/after collision bars, standing-wave modes, and a
  thin-lens ray diagram — all driven by SymPy-exported closed forms in your browser (no server).
- **A 96-formula reference** spanning all five domains, every entry's LaTeX generated from the SymPy expression
  it was verified against, plus a typed, pannable **concept graph** (96 nodes, 153 edges).
- **Navigation built in:** hover any formula chip — or a tagged formula in the prose — to preview its reference
  entry, and press **⌘K / Ctrl-K** anywhere to search every formula and lesson.

## How it's verified

One build-time **SymPy** program solves each scenario in the algebra register, derives it in the calculus
register, **proves the two agree** (`simplify(algebra − calculus) == 0`), checks every expression is
dimensionally homogeneous, and exports a cheap closed form the browser evaluates for the interactive graphs.
The learner isn't *told* the registers agree — SymPy proves it, and the proof is the artifact. Two honest
badges mark every claim: **machine-derived** (SymPy-checked math) versus **author-asserted** (the physics
modeling assumptions — `g=−10`, "no air resistance" — disclosed, not hidden).

## How it was made

AI-authored under an owner-designed verification system. There is no human-review gate on the math by design —
the verification *system* is the safeguard: a failed algebra=calculus proof, a non-homogeneous unit, a schema
mismatch, or a closed form that doesn't reproduce SymPy's numbers all **break the build** rather than ship.

## Stack

Astro 7 (static) + Svelte 5 islands + KaTeX, a Python/SymPy producer (run locally via `uv`), Matplotlib for
static figures, Ajv schema gates. No server, no database, no client-side Python. See
[`AGENTS.md`](./AGENTS.md) to work the repo.

## License

Code: [MIT](./LICENSE). Course content (prose, solutions, reference, figures): [CC BY-SA
4.0](./LICENSE-content.md).
