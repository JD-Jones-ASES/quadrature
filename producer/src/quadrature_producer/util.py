"""Small shared helpers: LaTeX and numeric formatting."""

from __future__ import annotations

import sympy as sp


def tex(expr) -> str:
    """LaTeX for a SymPy expression (single source of truth for rendered math)."""
    return sp.latex(expr)


def numval(expr, subs) -> float:
    """Evaluate an expression numerically under the scenario substitutions."""
    val = sp.N(expr.subs(subs), 15)
    if not val.is_number or val.has(sp.zoo, sp.oo, sp.nan):
        raise ValueError(f"non-numeric result for {expr}: {val}")
    return float(val)


def display(value: float, sig: int = 4) -> str:
    """A clean human string for a number (no trailing-zero noise, no sci-notation for normal ranges)."""
    if value == 0:
        return "0"
    rounded = float(f"{value:.{sig}g}")
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:g}"
