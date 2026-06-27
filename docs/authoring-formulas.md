# Authoring a reference formula

The reference (the "best formula sheet") is generated from `reference/formulas/<id>.formula.toml`. Each entry is
SymPy-verified: its LaTeX is generated from the SymPy expression (no transcription typos), its units are
checked, and its declared derivation relationship is proven. After editing, run `npm run prepare:data`; the
sheet (`derived/reference/formulas.json`) and the concept graph (`derived/reference/concept-graph.json`)
regenerate. Schema: `schemas/formula.schema.json` + `schemas/concept-graph.schema.json`.

## Spec fields

```toml
id = "kin-x-of-t"                 # stable, kebab-case, unique; used by lessons' formulas_used and by edges
name = "Position under constant acceleration"
domain = "mechanics"             # colors the concept-graph node: mechanics | em | thermo | waves-optics | modern
regime = 1
expr = "x0 + v0*t + a*t**2/2"    # the SymPy expression (RHS); symbols declared in [variables]
lhs = "x"                         # the quantity this defines
result_unit = "m"
assumptions = ["constant acceleration"]   # domain-of-validity flags shown on the entry

[variables]
x0 = { unit = "m",      desc = "initial position" }
v0 = { unit = "m/s",    desc = "initial velocity" }
a  = { unit = "m/s**2", desc = "acceleration (constant)" }
t  = { unit = "s",      desc = "time" }
# A symbol whose sympify-friendly ASCII name isn't already clean LaTeX needs a `latex` GLYPH (ADR-0025), e.g.
#   lam    = { unit = "1/s", desc = "decay constant λ", latex = '\lambda' }      # λ is a built-in default
#   dPhidt = { unit = "Wb/s", desc = "dΦ/dt",          latex = '\frac{d\Phi}{dt}' }
#   di     = { unit = "m",   desc = "image distance",  latex = 'd_i' }
# Use single-quoted TOML (literal, so backslashes need no escaping). The glyph also renders in the variable
# table. The RHS LaTeX stays generated from `expr` — the glyph only tells the printer how to spell the symbol.

[derivation]                      # the producer PROVES this relationship
relationship = "integral-of"     # this node is ∫(target) d(variable)
target = "kin-v-of-t"
variable = "t"

lessons = ["freefall-throw-up"]   # back-links to lessons that use it
citations = []                    # ids registered in docs/SOURCES.md

[[edges]]                         # typed concept-graph edges out of this node
type = "integral-of"             # derived-from | integral-of | derivative-of | special-case-of | assumes | related-to
target = "kin-v-of-t"
gloss = "x is the running area under v"
```

## Edge types (concept graph)

- `integral-of` / `derivative-of` — the calculus spine (x ↔ v ↔ a). The producer adds the reciprocal.
- `derived-from` — algebraically derived from another node.
- `special-case-of` — e.g. constant-`a` kinematics as a special case of the general integral (the regime-1 dual).
- `assumes` — points at a domain-of-validity condition.
- `related-to` — only where a sharper type would over-claim.

## Rules the producer enforces

- **The declared derivation must hold.** For `relationship:"integral-of"`, the producer proves
  `diff(expr, variable) − target.expr == 0` via `prove.tiered_zero`; for `derivative-of`, the inverse. A
  mismatch fails the build.
- **Units must be homogeneous** and the result must carry `result_unit`.
- **LaTeX is generated from `expr`** so the rendered formula and the verified expression can never disagree. The
  RHS is rendered by a `LatexPrinter` subclass (ADR-0025) that orders Mul factors / Add terms by the order you
  wrote them in `expr` — so **write `expr` in physics-conventional order** (`m*c**2`, not `c**2*m`; `B*q*v` →
  `qvB` only if you write `q*v*B`). It changes print order only, never the expression, so semantics can't drift.
- **No leaked ASCII** (`check-latex-quality.mjs`): if a generated formula's LaTeX still contains a multi-letter
  ASCII run that isn't a known function or an author-declared glyph, the build fails — add the missing
  `latex` glyph (see `[variables]` above). Typography breaks the build the way a bad unit does.
- **Edge endpoints must resolve** to known formula ids (`validate-reference.mjs`).
- **Provider-agnostic** (`scan-text.mjs`).
