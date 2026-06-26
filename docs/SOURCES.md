# SOURCES — citation & verification register

Quote/data validation is a hard rule (`JD.md`): every formula and physical fact in the shipped reference is
either machine-verified, sourced, or labeled. Physical laws and formulas are facts (not copyrightable); we
*extract and verify* them rather than reproduce any source's expression. No copyrighted source text or figures
are hosted.

Each reference formula carries its own `citations` in its `.formula.toml`; this file is the human-readable
register of what those ids point to and **how each was verified**.

## Verification methods (what the badge means)

- **`sympy-derived`** — the relationship is machine-proven by the producer (e.g. the v(t) node is `diff` of
  the x(t) node; the unit check passes). The strongest tier; no external source needed for the *math*.
- **`standard-result`** — a textbook-standard formula whose form is universal across sources; verified by the
  producer's dimensional-homogeneity check and (where applicable) by derivation from a more primitive node.
- **`cited`** — a value or convention taken from a named source (with edition/page or URL + access date).

## Register

| Citation id | Points to | Method | Notes |
|---|---|---|---|
| _(none yet — Phase 0 ships one SymPy-derived formula entry)_ | | | |

## Conventions for adding an entry

1. Give the citation a stable kebab-case id used in the formula's `citations` array.
2. Record the method above. Prefer `sympy-derived` / `standard-result`; reserve `cited` for values/conventions.
3. For `cited`, include enough to locate it (author, title, edition, page **or** URL + access date) — never the
   copyrighted text itself.
