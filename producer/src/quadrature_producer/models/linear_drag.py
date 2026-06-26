"""Regime-2 model: free fall with linear air resistance — terminal velocity.

Acceleration is NOT constant, so the constant-a formulas don't apply: calculus is the only road in
(regime 2). EOM: m v' = mg − b v  ⟺  v' = g − v/τ, with time constant τ = m/b. The proof is governing
(ADR-0013): the closed form solves the EOM, matches the initial velocity, x is its integral, and the
terminal-velocity *limit* falls out (machine-checked with sympy.limit). Closed form is JS-cheap (exp), so the
graph is interactive (ADR-0012).
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import Marker, Scenario, Slider, make_result

t = sp.Symbol("t", nonnegative=True, real=True)
tau = sp.Symbol("tau", positive=True)
v0 = sp.Symbol("v0", real=True)
g = sp.Symbol("g", real=True)
x0 = sp.Symbol("x0", real=True)

PROOF_DOMAIN = SampleDomain(
    bounds={g: (-15.0, -1.0), tau: (0.5, 5.0), v0: (-5.0, 5.0), x0: (-5.0, 5.0), t: (0.1, 5.0)},
    positive={tau},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("m", "b"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: linear-drag requires parameters.{key}")
    m_val, b_val = sp.nsimplify(p["m"]), sp.nsimplify(p["b"])
    g_val = sp.nsimplify(p.get("g", -10))
    x0v, v0v = sp.nsimplify(p.get("x0", 0)), sp.nsimplify(p.get("v0", 0))
    tau_val = m_val / b_val
    vt_val = g_val * tau_val

    vt = g * tau  # terminal velocity, symbolic
    v_expr = vt + (v0 - vt) * sp.exp(-t / tau)
    x_expr = x0 + vt * t + (v0 - vt) * tau * (1 - sp.exp(-t / tau))
    a_expr = sp.diff(v_expr, t)

    checks_spec = [
        ("solves_eom", "The closed form solves the equation of motion v' = g − v/τ.",
         sp.diff(v_expr, t) - (g - v_expr / tau)),
        ("ic_velocity", "It matches the initial velocity v(0) = v₀.", v_expr.subs(t, 0) - v0),
        ("x_is_integral_of_v", "Position is the integral of velocity (dx/dt = v).",
         sp.diff(x_expr, t) - v_expr),
        ("terminal_limit", "The terminal velocity falls out: v → g·τ = mg/b as t → ∞.",
         sp.limit(v_expr, t, sp.oo) - vt),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"drag/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "The closed form provably solves the equation of motion — and terminal velocity falls out.",
        "checked_by": "sympy",
        "holds": True,
        "detail": "back-substitute v(t) into v' = g − v/τ; check IC; check dx/dt = v; check lim v = g·τ",
        "checks": checks,
    }

    rsubs = {g: g_val, tau: tau_val, v0: v0v}
    result = {
        "terminal_velocity": make_result(vt, rsubs, "m/s", "Terminal velocity (mg/b)"),
        "time_constant": make_result(tau, {tau: tau_val}, "s", "Time constant τ = m/b"),
    }

    algebra = {
        "steps": [
            {
                "label": "Where the algebra-based course stops",
                "latex": r"x = x_0 + v_0 t + \tfrac{1}{2}a t^2 \;\; \text{(does NOT apply: } a \text{ is not constant)}",
                "prose": "With air resistance the acceleration changes as the object speeds up, so the "
                         "constant-a formulas fail. At best you're handed the terminal velocity v = mg/b as a "
                         "fact, with no path to it.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Newton's second law with linear drag",
                "latex": r"m\,v' = mg - b\,v \;\;\Longrightarrow\;\; v' = g - \tfrac{v}{\tau},\quad \tau = \tfrac{m}{b}",
                "prose": "Drag opposes motion and grows with speed, so the net force — and the acceleration — "
                         "shrink as the object speeds up. This is a differential equation, not algebra.",
            },
            {
                "label": "Solve the linear ODE",
                "latex": r"v(t) = v_{\text{term}} + (v_0 - v_{\text{term}})\,e^{-t/\tau},\quad v_{\text{term}} = g\tau = \tfrac{mg}{b}",
                "prose": "Velocity approaches the terminal value exponentially, with time constant τ.",
            },
            {
                "label": "Acceleration decays to zero",
                "latex": r"a(t) = \frac{v_{\text{term}} - v_0}{\tau}\,e^{-t/\tau} \;\to\; 0",
                "prose": "Unlike free fall (where a is constant), here the acceleration decays: drag grows "
                         "until it cancels gravity and there is no net force.",
            },
            {
                "label": "Terminal velocity emerges",
                "latex": r"\boxed{\,\lim_{t\to\infty} v(t) = v_{\text{term}} = \dfrac{mg}{b}\,}",
                "prose": "The memorized terminal velocity is the long-time limit of the solution — and SymPy "
                         "proves the limit.",
                "emphasis": True,
            },
        ],
    }

    tau_f = float(tau_val)
    vt_f = float(vt_val)
    twindow = 5 * tau_f
    return Scenario(
        regime=2,
        t=t,
        x_expr=x_expr,
        v_expr=v_expr,
        a_expr=a_expr,
        constants={g: g_val, x0: x0v},
        constants_export={"m": float(m_val), "b": float(b_val), "g": float(g_val)},
        unit_map={g: "m/s**2", tau: "s", v0: "m/s", x0: "m", t: "s"},
        initial_conditions={"x0": float(x0v), "v0": float(v0v)},
        sliders=[
            Slider(tau, "tau", 0.5, 6.0, tau_f),
            Slider(v0, "v0", -10.0, 10.0, float(v0v)),
        ],
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        t_window=twindow,
        markers=[
            Marker("v", tau_f, "one time-constant τ:\n~63% of the way to terminal", dx=8, dy=-14,
                   ha="left", va="top"),
            Marker("v", twindow * 0.82, f"v → terminal = {vt_f:g} m/s", dy=16, va="bottom", dot=False),
            Marker("a", twindow * 0.5, "a decays to 0: drag cancels gravity", dy=12, va="bottom", dot=False),
        ],
        guides=[tau_f],
        labels=("x  (m)", "v  (m/s)", "a  (m/s²)"),
    )
