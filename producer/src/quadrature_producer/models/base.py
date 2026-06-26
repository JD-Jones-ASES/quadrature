"""The Scenario contract every model returns, plus shared helpers.

A Scenario is model-agnostic: it carries the symbolic x/v/a expressions (in terms of `t` + slider/constant
symbols), the constants to substitute, the sliders (free in the closed form), the stepped registers, the
proof, and graph hints (markers/guides/shades). build.py assembles it into a solution.json; emit.py and
graph.py consume the symbolic/graph parts.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import sympy as sp

from ..util import display as _display
from ..util import tex


@dataclass
class Slider:
    sym: sp.Symbol
    name: str
    min: float
    max: float
    default: float


@dataclass
class Marker:
    panel: str          # "x" | "v" | "a"
    t: float
    label: str
    dx: float = 0.0
    dy: float = -14.0
    ha: str = "center"
    va: str = "top"
    dot: bool = True


@dataclass
class Shade:
    panel: str
    t0: float
    t1: float


@dataclass
class Scenario:
    regime: int
    t: sp.Symbol
    x_expr: sp.Expr
    v_expr: sp.Expr
    a_expr: sp.Expr
    constants: dict                      # {sym: sympy number} — substituted for graph + closed form
    constants_export: dict               # {name: number} — for solution.json "constants"
    unit_map: dict                       # {sym: unit string} — for the dimensional-homogeneity check
    sliders: list                        # [Slider] — free in the closed form
    proof: dict                          # {kind, heading, checked_by, holds, detail, checks}
    algebra: dict                        # {steps, result}
    calculus: dict                       # {steps}
    t_window: float                      # plotting/sampling window at default params
    initial_conditions: dict = field(default_factory=dict)
    markers: list = field(default_factory=list)
    guides: list = field(default_factory=list)   # vertical dashed t-lines on the static graph
    shades: list = field(default_factory=list)
    sign_analysis: dict | None = None
    labels: tuple = ("x  (m)", "v  (m/s)", "a  (m/s²)")  # per-panel y-axis labels
    window_mode: str = "fixed"   # "landing" (clip at x returning to ground) | "fixed" (use t_window)


def make_result(expr: sp.Expr, subs: dict, unit: str, label: str) -> dict:
    """A numeric result entry for algebra.result (value + display + symbolic LaTeX)."""
    val = sp.N(expr.subs(subs), 15)
    if not val.is_number or val.has(sp.zoo, sp.oo, sp.nan):
        raise ValueError(f"non-numeric result for {expr}")
    value = float(val)
    return {
        "label": label,
        "unit": unit,
        "symbolic_latex": tex(expr),
        "value": round(value, 6),
        "display": _display(value),
    }
