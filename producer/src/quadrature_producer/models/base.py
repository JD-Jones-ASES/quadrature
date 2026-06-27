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
class EnergyPlot:
    """The energy-conservation instrument: two energies that trade as a system moves, with their sum flat.

    A cursor sweeps a configuration variable u (a height, a position, an angle); the kinetic and potential
    energies ke(u), pe(u) are drawn as bars that exchange while the total bar ke+pe stays constant — the visual
    proof that energy is conserved. The closed forms are JS-cheap and parity-verified, like the area instrument.
    """
    u: sp.Symbol
    ke_expr: sp.Expr          # kinetic energy KE(u)
    pe_expr: sp.Expr          # potential energy PE(u)
    u0: float                 # cursor lower bound
    u_window: float           # cursor upper bound
    cursor: Slider            # the configuration-variable slider over [u0, u_window]
    sliders: list             # parameter sliders free in ke/pe (e.g. the mass)
    constants: dict           # {sym: number} substituted for graph + closed form
    unit_map: dict            # {sym: unit string} for the dimensional-homogeneity check on ke and pe
    u_label: str              # cursor axis label, e.g. "h  (m)"
    ke_label: str = "KE  (J)"
    pe_label: str = "PE  (J)"
    total_label: str = "Total  (J)"
    u_unit: str = "m"         # the cursor unit shown beside the readout
    annot: str = ""           # one-line static-figure annotation


@dataclass
class CollisionPlot:
    """The collision instrument: a before/after two-state bar comparison (ADR-0018).

    A 1D two-body collision parameterised by the coefficient of restitution e (the cursor, 0=perfectly
    inelastic, 1=perfectly elastic). The producer ships the closed-form final velocities v1'(e, m1),
    v2'(e, m1); the island computes the before/after momentum and kinetic-energy bars from them. The
    *momentum* total bar is identical before and after at every e (equal-and-opposite impulses cancel —
    Newton's third law integrated); the *kinetic-energy* total bar equals the before value only at e=1 and
    shrinks as e→0 — the lost KE is the lesson. Closed forms are JS-cheap and parity-verified, like the
    area/energy instruments. v1f_expr/v2f_expr are symbolic in (m1, m2, v1, v2, e); `constants` substitutes
    m2/v1/v2, leaving m1 (the slider) and e (the cursor) free.
    """
    u: sp.Symbol                  # the coefficient-of-restitution cursor symbol (e)
    v1f_expr: sp.Expr             # final velocity of body 1, v1'(m1, m2, v1, v2, e)
    v2f_expr: sp.Expr             # final velocity of body 2, v2'(...)
    cursor: Slider                # e over [0, 1]
    sliders: list                 # parameter sliders free in v1f/v2f (the incident mass m1)
    constants: dict               # {sym: number} substituted (m2, v1, v2) for graph + closed form
    consts_export: dict           # {"m2":, "v1":, "v2":} floats the island needs to form p/KE bars
    unit_map: dict                # {sym: unit string} for the dimensional check on v1f and v2f
    u_label: str = "e  (restitution)"
    u_unit: str = ""              # the cursor (restitution) is dimensionless
    annot: str = ""               # one-line static-figure annotation


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
    frame_mode: str = "ground"      # "ground" (projectile: origin bottom-left, ground line) | "orbit"
                                    #   (a central body at the origin, equal aspect, a closed/looping path)
    mu: float | None = None         # orbit only: μ = GM (m³/s²), passed to the island for the v/T readouts
    view_half: float | None = None  # orbit only: fixed half-extent for the centred view (the elliptical/sampled
                                    #   case has no radius slider, so the producer supplies the frame size)


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
    energy: "EnergyPlot | None" = None  # the energy-exchange bars instrument; graph kind "energy"
    collision: "CollisionPlot | None" = None  # the before/after collision bars (ADR-0018); kind "collision"


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
