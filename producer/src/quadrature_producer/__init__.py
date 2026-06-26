"""Build-time SymPy producer for Quadrature.

One pure function from a problem/formula spec to a verified, schema-shaped object.
It solves the algebra register, derives the calculus register, PROVES the two agree,
checks dimensional homogeneity, and exports a JS-evaluable closed form + sample points.

It REFUSES TO EMIT any object whose equivalence proof or unit check fails — that is
"verification breaks the build" at the source (ADR-0002, ADR-0010). The honesty model
(machine-derived vs author-asserted) and the schema live in /schemas + /docs.
"""

__version__ = "0.1.0"


class BuildError(Exception):
    """Loud, named build failure. The message must identify the problem/formula/step."""
