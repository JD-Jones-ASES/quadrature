"""Regime-2 model: impulse and momentum — the area instrument (ADR-0014) on the TIME axis.

Reuses the integral instrument with no engine change: the shaded area under a force–time curve F(t) is the
impulse J(t) = ∫F dt, whose slope is the force, and which equals the change in momentum (J = Δp = mΔv). The
time-axis sibling of the work–energy lesson (∫F dx). The force is a half-sine contact pulse
F(t) = F_max·sin(πt/τ) — a realistic collision profile with an exact closed form, so the graph is interactive.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

t = sp.Symbol("t", nonnegative=True, real=True)   # time (the integration axis)
Fmax = sp.Symbol("Fmax", positive=True)           # peak force of the pulse
tau = sp.Symbol("tau", positive=True)             # contact duration
m = sp.Symbol("m", positive=True)                 # mass
_F0 = sp.Symbol("F0", positive=True)              # fresh symbols for the constant-force echo
_T0 = sp.Symbol("T0", positive=True)
_w = sp.Symbol("w", nonnegative=True)

PROOF_DOMAIN = SampleDomain(
    bounds={t: (0.001, 0.02), Fmax: (50.0, 400.0), tau: (0.01, 0.05), m: (0.1, 2.0),
            _F0: (1.0, 100.0), _T0: (0.01, 1.0)},
    positive={Fmax, tau, m, _F0, _T0},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("m", "Fmax", "tau"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: impulse requires parameters.{key}")
    m_val, Fmax_val, tau_val = sp.nsimplify(p["m"]), sp.nsimplify(p["Fmax"]), sp.nsimplify(p["tau"])

    f_expr = Fmax * sp.sin(sp.pi * t / tau)                          # F(t), a half-sine pulse
    g_expr = sp.integrate(Fmax * sp.sin(sp.pi * _w / tau), (_w, 0, t))  # J(t) = ∫₀ᵗ F dt'
    impulse_total = g_expr.subs(t, tau)                              # J(τ) = 2 F_max τ / π

    checks_spec = [
        ("ftc_slope", r"The impulse's slope is the force: $J'(t) = F(t)$ — the area's rate of growth is the curve's height.",
         sp.diff(g_expr, t) - f_expr),
        ("area_is_integral", r"The accumulated impulse is the area: $J(t) = \int_0^t F\,dt'$.",
         g_expr - sp.integrate(f_expr.subs(t, _w), (_w, 0, t))),
        ("impulse_result", r"The total impulse is $J = \tfrac{2}{\pi}F_{\max}\tau = \bar F\,\tau$ — exactly the area of the pulse.",
         impulse_total - 2 * Fmax * tau / sp.pi),
        ("constant_force_echo", r"For a constant force the integral collapses to $J = F\,\Delta t$ — the area is a rectangle (the quadrature).",
         sp.integrate(_F0, (_w, 0, _T0)) - _F0 * _T0),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"impulse/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "The impulse is the area under the force–time curve — and it is exactly the change in momentum.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{dJ}{dt} = F$; check $J = \int_0^t F\,dt'$; evaluate the pulse area $\tfrac{2}{\pi}F_{\max}\tau$; collapse the constant-force case to $F\,\Delta t$",
        "checks": checks,
    }

    rsubs = {Fmax: Fmax_val, tau: tau_val, m: m_val, t: tau_val}
    J = make_result(impulse_total, rsubs, "N·s", r"Impulse $J = \tfrac{2}{\pi}F_{\max}\tau$ (the shaded area)")
    J["symbolic_latex"] = r"\tfrac{2}{\pi}F_{\max}\tau"
    dv = make_result(impulse_total / m, rsubs, "m/s", r"Change in speed $\Delta v = J/m$")
    dv["symbolic_latex"] = r"J/m"
    fpk = make_result(Fmax, rsubs, "N", r"Peak force $F_{\max}$")
    fpk["symbolic_latex"] = r"F_{\max}"
    favg = make_result(2 * Fmax / sp.pi, rsubs, "N", r"Average force $\bar F = \tfrac{2}{\pi}F_{\max}$")
    favg["symbolic_latex"] = r"\tfrac{2}{\pi}F_{\max}"
    result = {"impulse": J, "delta_v": dv, "peak_force": fpk, "avg_force": favg}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you",
                "latex": r"J = \bar F\,\Delta t \qquad J = \Delta p = m\,\Delta v",
                "prose": "Impulse is the average force times the contact time, and it equals the change in "
                         "momentum. But a real collision force is not constant — it rises and falls over a few "
                         "milliseconds — so 'average force' hides where the number comes from.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Impulse is the area under the force–time curve",
                "latex": r"J = \int F\,dt",
                "prose": "Impulse is the integral of force over time — the area under the $F$–$t$ curve. For a "
                         "constant force this is a rectangle ($\\bar F\\,\\Delta t$); for a real pulse it is the "
                         "area under the curve.",
            },
            {
                "label": "Evaluate for the contact pulse $F(t) = F_{\\max}\\sin(\\pi t/\\tau)$",
                "latex": r"J = \int_0^{\tau} F_{\max}\sin\!\frac{\pi t}{\tau}\,dt = \frac{2}{\pi}F_{\max}\tau",
                "prose": "The area under a half-sine pulse is $\\tfrac{2}{\\pi}F_{\\max}\\tau$ — so the effective "
                         "average force is $\\tfrac{2}{\\pi}F_{\\max}\\approx 0.64\\,F_{\\max}$. Its slope at any "
                         "instant is the force $F(t)$.",
            },
            {
                "label": "The change in momentum falls out of the same integral",
                "latex": r"\int F\,dt = \int m\,\frac{dv}{dt}\,dt = m\,\Delta v \ \Longrightarrow\ J = \Delta p",
                "prose": "Because $F = m\\,dv/dt$, the impulse integral is exactly $m\\,\\Delta v$. The "
                         "impulse–momentum theorem is not a separate fact — it is the area under the force curve. "
                         "Drag the cursor: the shaded area and the momentum change grow together.",
                "emphasis": True,
            },
        ],
    }

    area = AreaPlot(
        u=t,
        f_expr=f_expr,
        g_expr=g_expr,
        u0=0.0,
        u_window=float(tau_val),
        cursor=Slider(t, "t", 0.0, float(tau_val), float(tau_val)),
        sliders=[Slider(Fmax, "Fmax", 50.0, 400.0, float(Fmax_val))],
        constants={tau: tau_val},
        unit_map={Fmax: "N", t: "s", tau: "s"},
        u_label="t  (s)",
        f_label="F  (N)",
        g_label="J  (N·s)",
        u_unit="s",
        annot="The shaded area under F(t) is the impulse; the slope of J(t) is the force.",
    )

    return Scenario(
        regime=2,
        constants_export={"m": float(m_val), "Fmax": float(Fmax_val), "tau": float(tau_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={"v0": 0.0},
        area=area,
    )
