"""Regime-1 model: a block sliding down an incline with kinetic friction — the temporal x/v/a stack. The
single most foundational mechanics scenario the course was missing: Newton's second law resolved along a slope.

The algebra-based course hands you the acceleration as a number, $a = g(\\sin\\theta - \\mu\\cos\\theta)$, then
plugs it into the constant-acceleration kinematics. The calculus shows those kinematics are just the integrals
of a constant acceleration: $v = \\int a\\,dt = at$ and $x = \\int v\\,dt = \\tfrac12 at^2$. This is regime 1 —
"algebra is calculus, evaluated" — with the bonus that the acceleration itself comes from a free-body diagram:
along the slope, $ma = mg\\sin\\theta - \\mu mg\\cos\\theta$, and the mass cancels.
"""

from __future__ import annotations

import sympy as sp

from ..prove import SampleDomain, tiered_zero
from .base import Marker, Scenario, Slider, make_result

t = sp.Symbol("t", nonnegative=True, real=True)   # time
g = sp.Symbol("g", positive=True)                 # gravitational field magnitude, m/s²
th = sp.Symbol("theta", positive=True)            # incline angle, DEGREES (slider; converted with π/180)
mu = sp.Symbol("mu", nonnegative=True)            # coefficient of kinetic friction (slider)
_w = sp.Symbol("w", nonnegative=True)
_RAD = sp.pi / 180

PROOF_DOMAIN = SampleDomain(
    bounds={t: (0.0, 3.0), g: (8.0, 11.0), th: (20.0, 45.0), mu: (0.0, 0.3)},
    positive={g, th},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    g_val = sp.nsimplify(p.get("g", 10))
    th_val = sp.nsimplify(p.get("theta_deg", 30))
    mu_val = sp.nsimplify(p.get("mu", 0.2))

    ang = th * _RAD                                   # radians for the trig
    a_expr = g * (sp.sin(ang) - mu * sp.cos(ang))     # acceleration along the slope (from F = ma)
    v_expr = a_expr * t                               # released from rest
    x_expr = sp.Rational(1, 2) * a_expr * t**2

    checks_spec = [
        ("velocity_is_integral",
         r"The velocity is the integral of the (constant) acceleration: $v = \int_0^t a\,dt' = at$.",
         v_expr - sp.integrate(a_expr, (_w, 0, t))),
        ("position_is_integral",
         r"The position is the integral of the velocity: $x = \int_0^t v\,dt' = \tfrac12 at^2$ — the memorized formula is the quadrature.",
         x_expr - sp.integrate(a_expr * _w, (_w, 0, t))),
        ("kinematic_identity",
         r"The velocity–position relation falls out: $v^2 = 2ax$ (no time needed).",
         v_expr**2 - 2 * a_expr * x_expr),
        ("frictionless_limit",
         r"With no friction ($\mu = 0$) the acceleration is the bare gravity component $g\sin\theta$.",
         a_expr.subs(mu, 0) - g * sp.sin(ang)),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"incline-friction/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "equivalence",
        "heading": "The acceleration comes from a free-body diagram; the kinematics are its integrals — algebra "
                   "is calculus, evaluated.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $v = \int a\,dt$; check $x = \int v\,dt$; show $v^2 = 2ax$; check the $\mu=0$ limit $g\sin\theta$",
        "checks": checks,
    }

    rsubs = {g: g_val, th: th_val, mu: mu_val}
    accel = make_result(a_expr, rsubs, "m/s²", r"Acceleration $a = g(\sin\theta - \mu\cos\theta)$")
    accel["symbolic_latex"] = r"g(\sin\theta - \mu\cos\theta)"
    accel_free = make_result(g * sp.sin(ang), rsubs, "m/s²", r"Frictionless acceleration $g\sin\theta$")
    accel_free["symbolic_latex"] = r"g\sin\theta"
    v2 = make_result(v_expr.subs(t, 2), rsubs, "m/s", r"Speed after 2 s")
    v2["symbolic_latex"] = r"a\,t"
    x2 = make_result(x_expr.subs(t, 2), rsubs, "m", r"Distance in 2 s")
    x2["symbolic_latex"] = r"\tfrac12 a t^2"
    result = {"acceleration": accel, "frictionless_accel": accel_free, "speed_2s": v2, "distance_2s": x2}

    algebra = {
        "steps": [
            {
                "label": "Resolve the forces along the incline (Newton's second law)",
                "latex": r"ma = mg\sin\theta - \mu\,mg\cos\theta \ \Longrightarrow\ a = g(\sin\theta - \mu\cos\theta)",
                "prose": "Along the slope, gravity pulls the block down with $mg\\sin\\theta$ while kinetic "
                         "friction resists with $\\mu mg\\cos\\theta$ (the normal force is $mg\\cos\\theta$). The "
                         "mass cancels, so the acceleration depends only on the angle and the friction "
                         "coefficient — not on how heavy the block is.",
            },
            {
                "label": "Then use the constant-acceleration kinematics",
                "latex": r"v = at, \qquad x = \tfrac12 at^2, \qquad v^2 = 2ax",
                "prose": "With $a$ constant and the block released from rest, the speed grows linearly and the "
                         "distance grows quadratically — the standard formulas.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "The acceleration is constant — integrate it once for the velocity",
                "latex": r"v(t) = \int_0^t a\,dt' = at",
                "prose": "Because $a = g(\\sin\\theta - \\mu\\cos\\theta)$ does not change with time, its integral "
                         "is just $at$. The velocity rises in a straight line — its slope is $a$.",
            },
            {
                "label": "Integrate again for the position",
                "latex": r"x(t) = \int_0^t v\,dt' = \int_0^t at'\,dt' = \tfrac12 at^2",
                "prose": "Integrating the velocity gives the parabola $\\tfrac12 at^2$. The memorized kinematics "
                         "formula is this integral, already evaluated — a quadrature. The area under the $v$–$t$ "
                         "line is exactly the distance travelled.",
                "emphasis": True,
            },
            {
                "label": "Eliminate time and the velocity–position relation appears",
                "latex": r"v^2 = (at)^2 = 2a\left(\tfrac12 at^2\right) = 2ax",
                "prose": "Squaring $v = at$ and substituting $x = \\tfrac12 at^2$ gives $v^2 = 2ax$ with no $t$ — "
                         "the same identity the algebra course states as a rule. Drag the angle and friction: a "
                         "steeper slope or less friction means a larger $a$, and all three panels steepen together.",
            },
        ],
    }

    a_num = float(sp.N(a_expr.subs(rsubs)))
    return Scenario(
        regime=1,
        t=t,
        x_expr=x_expr,
        v_expr=v_expr,
        a_expr=a_expr,
        constants={g: g_val},
        constants_export={"g": float(g_val), "theta_deg": float(th_val), "mu": float(mu_val)},
        unit_map={g: "m/s**2", th: "1", mu: "1", t: "s"},
        initial_conditions={"x0": 0.0, "v0": 0.0},
        sliders=[
            Slider(th, "theta", 20.0, 45.0, float(th_val)),
            Slider(mu, "mu", 0.0, 0.3, float(mu_val)),
        ],
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        t_window=2.5,
        labels=("x  (m)", "v  (m/s)", "a  (m/s²)"),
        markers=[Marker("a", 1.25, f"a = {a_num:.2f} m/s² — constant", dy=12, va="bottom", dot=False)],
        window_mode="fixed",
    )
