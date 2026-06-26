"""Regime-2 model: the work–energy theorem under a variable force — the integral instrument off the time
axis (ADR-0014).

There is no temporal x–t/v–t/a–t stack here. The pivot is the **force–displacement** graph: the shaded
AREA under F(x) from 0 to x is the work W(x) = ∫F dx, whose SLOPE is F(x) (the fundamental theorem), and
which EQUALS the kinetic energy gained — the memorized ½mv² falls out of the integral. The regime-1
"quadrature" echo lives inside: when the force is constant, the integral collapses to the rectangle W = F·d.

Proof kind is "integral": back-substitution-style identities checked by the same tiered_zero —
  W'(x) = F(x);  W(x) = ∫₀ˣ F du;  ½mv² = W;  and  ∫₀ᵈ F du = F·d when F is constant.
The force F(x) = b·x is a JS-cheap polynomial, so the graph is fully interactive (ADR-0012): a cursor slider
sweeps the upper limit and the shaded area (= work = ΔKE) grows with it.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

u = sp.Symbol("u", nonnegative=True, real=True)   # position (the integration axis); shown to the reader as x
b = sp.Symbol("b", positive=True)                 # force-per-metre (the force law slope), N/m
m = sp.Symbol("m", positive=True)                 # mass, kg
_F = sp.Symbol("F", positive=True)                # fresh symbols for the constant-force echo
_d = sp.Symbol("d", positive=True)
_w = sp.Symbol("w", nonnegative=True)             # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={u: (0.1, 2.0), b: (1.0, 20.0), m: (0.5, 5.0), _F: (0.1, 10.0), _d: (0.1, 5.0)},
    positive={b, m, _F, _d},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("m", "b", "d"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: work-energy requires parameters.{key}")
    m_val, b_val, d_val = sp.nsimplify(p["m"]), sp.nsimplify(p["b"]), sp.nsimplify(p["d"])
    u_window = float(p.get("x_window", float(d_val) * 1.35))

    # --- the integrand and its accumulated integral (force law F(x) = b·x) ---
    f_expr = b * u                                  # F(x)
    g_expr = sp.integrate(b * _w, (_w, 0, u))       # W(x) = ∫₀ˣ b·u du = ½ b x²
    v_expr = sp.sqrt(2 * g_expr / m)                # v(x) from ½mv² = W  →  √(b/m)·x

    # --- proof (kind "integral"): the FTC relationship + the work–energy theorem + the regime-1 echo ---
    checks_spec = [
        ("ftc_slope",
         r"The work's slope is the force: $W'(x) = F(x)$ — the area's rate of growth is the curve's height.",
         sp.diff(g_expr, u) - f_expr),
        ("area_is_integral",
         r"The accumulated work is exactly the area: $W(x) = \int_0^x F\,du$.",
         g_expr - sp.integrate(f_expr.subs(u, _w), (_w, 0, u))),
        ("work_energy",
         r"The kinetic energy equals the work: $\tfrac12 m v^2 = W$ — the memorized $\tfrac12 m v^2$ is the area.",
         sp.Rational(1, 2) * m * v_expr**2 - g_expr),
        ("constant_force_echo",
         r"When the force is constant the integral collapses to $W = F\,d$ — the algebra formula is the area of a rectangle (the quadrature).",
         sp.integrate(_F, (_w, 0, _d)) - _F * _d),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"work-energy/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "The work is the area under the force curve — and the kinetic energy falls out of the integral.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{d}{dx}W = F$; check $W = \int_0^x F\,du$; back-substitute into $\tfrac12 m v^2 = W$; collapse the constant-force case to $F\,d$",
        "checks": checks,
    }

    # --- results at the worked displacement d ---
    rsubs = {b: b_val, m: m_val, u: d_val}
    work = make_result(g_expr, rsubs, "J", r"Work done $W = \tfrac12 b d^2$ (the shaded area)")
    work["symbolic_latex"] = r"\tfrac12 b\,d^2"
    kinetic = make_result(sp.Rational(1, 2) * m * v_expr**2, rsubs, "J", r"Kinetic energy gained $\tfrac12 m v^2$")
    kinetic["symbolic_latex"] = r"\tfrac12 m v^2"
    speed = make_result(v_expr, rsubs, "m/s", r"Final speed $v = \sqrt{b/m}\,d$")
    speed["symbolic_latex"] = r"\sqrt{b/m}\,d"
    fmax = make_result(f_expr, rsubs, "N", r"Maximum force $F_{\max} = b\,d$")
    fmax["symbolic_latex"] = r"b\,d"
    result = {"work_done": work, "kinetic_energy": kinetic, "final_speed": speed, "max_force": fmax}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you",
                "latex": r"W = F\,d \qquad(\text{constant force}) \qquad\Longrightarrow\qquad W = \bar F\,d,\ \ \bar F = \tfrac12 F_{\max}",
                "prose": "For a constant force, work is force times distance. When the force *varies*, the "
                         "algebra course patches it with an average force — which is only exact here because "
                         "the force happens to rise linearly. It can compute the number but cannot say *why* "
                         "the answer is an area.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Work is the area under the force–displacement curve",
                "latex": r"W = \int F\,dx",
                "prose": "Work is defined as the integral of force over displacement. For a constant force this "
                         "integral is a rectangle (and gives $W = F d$); for any force it is the area under the "
                         "$F$–$x$ curve. The algebra formula is the special case where the area is a rectangle.",
            },
            {
                "label": "Evaluate for the linear force $F(x) = b x$",
                "latex": r"W = \int_0^{x} b\,u\,du = \tfrac12 b\,x^2",
                "prose": "The area under a straight line from the origin is a triangle: "
                         "$\\tfrac12\\,(\\text{base})\\,(\\text{height}) = \\tfrac12\\,x\\,(b x) = \\tfrac12 b x^2$. "
                         "Its slope is $bx = F(x)$ — the force is the rate at which work accumulates.",
            },
            {
                "label": "The kinetic energy falls out of the same integral",
                "latex": r"\int F\,dx = \int m\,\frac{dv}{dt}\,dx = \int m\,v\,dv = \tfrac12 m v^2 \ \Longrightarrow\ \tfrac12 m v^2 = W",
                "prose": "Substituting $F = m\\,dv/dt$ and $dx = v\\,dt$ turns the work integral into $\\int m v\\,dv$. "
                         "The memorized $\\tfrac12 m v^2$ is not a separate fact — it is exactly the accumulated "
                         "work. The area under the force curve IS the kinetic energy.",
                "emphasis": True,
            },
            {
                "label": "So the speed follows from the area",
                "latex": r"\boxed{\,v(x) = \sqrt{\tfrac{2W}{m}} = \sqrt{\tfrac{b}{m}}\;x\,}",
                "prose": "Read the work off the area, set it equal to $\\tfrac12 m v^2$, and the speed at any "
                         "displacement follows. Drag the cursor: the shaded area and the kinetic energy move "
                         "together because they are the same quantity.",
            },
        ],
    }

    area = AreaPlot(
        u=u,
        f_expr=f_expr,
        g_expr=g_expr,
        u0=0.0,
        u_window=u_window,
        cursor=Slider(u, "u", 0.0, u_window, float(d_val)),
        sliders=[Slider(b, "b", 2.0, 16.0, float(b_val))],
        constants={},                       # b is a slider; u is the axis; m is not in f/g
        unit_map={b: "N/m", u: "m"},
        u_label="x  (m)",
        f_label="F  (N)",
        g_label="W  (J)",
        annot="The shaded area under F(x) is the work; the slope of W(x) is the force.",
    )

    return Scenario(
        regime=2,
        constants_export={"m": float(m_val), "b": float(b_val), "d": float(d_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={"x0": 0.0, "v0": 0.0},
        area=area,
    )
