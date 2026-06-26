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
class Frame:
    """One discrete stop of a `sampled` graph — an exact, parity-verified solution at a fixed parameter
    value. The slider snaps between frames (the solution's functional form changes across the sweep, so it
    cannot be a single closed form; each frame stays exact)."""
    value: float
    label: str
    x_expr: sp.Expr   # functions of t only (all parameters fixed numerically)
    v_expr: sp.Expr
    a_expr: sp.Expr


@dataclass
class AreaPlot:
    """The integral instrument on a general (non-time) axis — the thesis off the time axis (ADR-0014).

    A curve f(u) (the integrand: a force, a pressure, a field) over an axis u (position, volume, …); the
    shaded AREA under f from u0 to a cursor IS the accumulated integral g(u) = ∫ f du (work, …), whose SLOPE
    is f. Same "slope↔value / area↔change" pivot as the x–t/v–t/a–t stack, but the integration variable is
    u, not t. f_expr/g_expr are functions of u + the parameter sliders; `cursor` is the upper-limit slider.
    """
    u: sp.Symbol
    f_expr: sp.Expr           # integrand f(u)  (e.g. force F(x))
    g_expr: sp.Expr           # accumulated integral g(u) = ∫_{u0}^{u} f du  (e.g. work W(x))
    u0: float                 # lower limit of integration
    u_window: float           # axis range plotted/sampled (max cursor)
    cursor: Slider            # the upper-limit (displacement) slider over [u0, u_window]
    sliders: list             # parameter sliders free in f/g (e.g. the force constant)
    constants: dict           # {sym: number} substituted for graph + closed form
    unit_map: dict            # {sym: unit string} for the dimensional-homogeneity check on f and g
    u_label: str              # shared x-axis label, e.g. "x  (m)"
    f_label: str              # integrand panel label, e.g. "F  (N)"
    g_label: str              # accumulated panel label, e.g. "W  (J)"
    u_unit: str = "m"         # the axis/cursor unit (m, m**3, …) — shown beside the cursor readout
    annot: str = ""           # one-line static-figure annotation


@dataclass
class TrajMarker:
    """A point annotation in (x, y) space on the trajectory poster (apex, range, launch)."""
    x: float
    y: float
    label: str
    dx: float = 0.0
    dy: float = -12.0
    ha: str = "center"
    va: str = "top"
    dot: bool = True


@dataclass
class TrajFrame:
    """One numerically-integrated trajectory (no closed form) at a fixed sweep value — committed as sample
    points (the path is a polyline). Used by the quadratic-drag case (ADR-0015); the slider snaps between
    frames, and within a frame the polyline's deviation from the fine solution is bounded by the accuracy
    gate."""
    value: float
    label: str
    t: list
    x: list
    y: list


@dataclass
class TrajectoryPlot:
    """The trajectory instrument: 2D projectile motion plotted as the path y vs x (ADR-0015). Two modes —
    a closed-form interactive path (drag-free: x(t), y(t) are exact polynomials, sliders for launch angle and
    speed) or numerically-integrated `frames` swept over one parameter (quadratic drag: no closed form). The
    horizontal and vertical motions are independent 1D motions superposed; the path is their parametric trace.
    """
    t: sp.Symbol
    t_flight: float                 # default flight-time window (sampling/plot range)
    constants: dict                 # {sym: number} substituted for graph + closed form
    unit_map: dict                  # {sym: unit string} for the dimensional check on x and y
    x_expr: sp.Expr | None = None   # closed-form (drag-free) path components, functions of t + sliders
    y_expr: sp.Expr | None = None
    sliders: list = field(default_factory=list)   # launch sliders (angle, speed)
    markers: list = field(default_factory=list)   # TrajMarker — static poster annotations at defaults
    x_label: str = "x  (m)"
    y_label: str = "y  (m)"
    sweep: dict | None = None       # numerical case: {name,label,unit,values,critical?}
    frames: list | None = None      # numerical case: [TrajFrame]
    reference: TrajFrame | None = None  # optional drag-free overlay (the parabola) on the drag plot


@dataclass
class Scenario:
    regime: int
    constants_export: dict               # {name: number} — for solution.json "constants"
    proof: dict                          # {kind, heading, checked_by, holds, detail, checks}
    algebra: dict                        # {steps, result}
    calculus: dict                       # {steps}
    # --- temporal stack (the x–t/v–t/a–t instrument); None for a pure area-instrument scenario ---
    t: sp.Symbol | None = None
    x_expr: sp.Expr | None = None
    v_expr: sp.Expr | None = None
    a_expr: sp.Expr | None = None
    constants: dict = field(default_factory=dict)   # {sym: sympy number} — substituted for graph/closed form
    unit_map: dict = field(default_factory=dict)     # {sym: unit string} — temporal dimensional check
    sliders: list = field(default_factory=list)      # [Slider] — free in the closed form
    t_window: float = 0.0                # plotting/sampling window at default params
    initial_conditions: dict = field(default_factory=dict)
    markers: list = field(default_factory=list)
    guides: list = field(default_factory=list)   # vertical dashed t-lines on the static graph
    shades: list = field(default_factory=list)
    sign_analysis: dict | None = None
    labels: tuple = ("x  (m)", "v  (m/s)", "a  (m/s²)")  # per-panel y-axis labels
    window_mode: str = "fixed"   # "landing" (clip at x returning to ground) | "fixed" (use t_window)
    sampled: dict | None = None  # {"sweep": {name,label,unit,values:[...]}, "frames": [Frame, ...]}
    area: AreaPlot | None = None  # the non-temporal integral instrument (ADR-0014); graph kind "area"
    trajectory: TrajectoryPlot | None = None  # 2D projectile path (ADR-0015); graph kind "trajectory"


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
