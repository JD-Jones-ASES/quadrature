"""Regime-2 model: the hydrostatic force on a vertical wall — the area instrument (ADR-0014) on a **depth**
axis. This opens the fluids domain with NO engine change: it reuses the AreaPlot contract untouched.

Water pressure grows linearly with depth, $P(h) = \\rho g h$, so a horizontal strip of the wall at depth $h$
(width $w$, height $dh$) feels a force $dF = P\\,w\\,dh = \\rho g w\\,h\\,dh$. The integrand $dF/dh = \\rho g w h$
rises as a straight line, and the shaded AREA under it from the surface to depth $H$ is the total force
$F(H) = \\int_0^H \\rho g w\\,h\\,dh = \\tfrac12\\rho g w H^2$ — a triangle. Its slope is the strip force, and the
algebra-based "average pressure times area" ($\\bar P A$, with $\\bar P = \\rho g H/2$ the pressure at the
centroid) is *exactly* this area — but only because the pressure happens to rise linearly. The regime-1
"quadrature" echo: if the pressure did not grow with depth (a uniform pressure $P_0$, like a gas), the
integrand would be the constant $P_0 w$ and the integral would collapse to the rectangle $F = P_0 A$.

Proof kind is "integral": $F'(h) = dF/dh$; $F(h) = \\int_0^h \\rho g w h'\\,dh'$; the memorized $\\bar P A$ falls
out; and the uniform-pressure case collapses to $P_0 A$. The integrand is a JS-cheap polynomial, so the graph
is interactive (ADR-0012): a cursor sweeps the water depth and the shaded force grows as its square.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

h = sp.Symbol("h", nonnegative=True, real=True)   # depth below the surface (the integration axis)
rho = sp.Symbol("rho", positive=True)             # fluid density, kg/m³ (the free slider — which fluid)
g = sp.Symbol("g", positive=True)                 # gravitational field magnitude, m/s² (constant)
w = sp.Symbol("w", positive=True)                 # wall width, m (constant)
_P0 = sp.Symbol("P0", positive=True)              # fresh symbols for the uniform-pressure echo
_H = sp.Symbol("H", positive=True)
_s = sp.Symbol("s", nonnegative=True)             # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={h: (0.1, 6.0), rho: (500.0, 1500.0), g: (8.0, 11.0), w: (1.0, 12.0),
            _P0: (1.0e3, 1.0e5), _H: (0.1, 6.0)},
    positive={rho, g, w, _P0, _H},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("rho", "g", "w", "H"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: hydrostatic-force requires parameters.{key}")
    rho_val, g_val = sp.nsimplify(p["rho"]), sp.nsimplify(p["g"])
    w_val, H_val = sp.nsimplify(p["w"]), sp.nsimplify(p["H"])
    u_window = float(p.get("h_window", float(H_val) * 1.2))

    f_expr = rho * g * w * h                          # dF/dh = P(h)·w = ρg w h  (strip force per unit depth)
    g_expr = sp.integrate(rho * g * w * _s, (_s, 0, h))   # F(h) = ∫₀ʰ ρg w h' dh' = ½ρg w h²

    # --- proof (kind "integral") ---
    checks_spec = [
        ("ftc_slope",
         r"The force's slope is the strip force: $F'(h) = \rho g w h$ — the area's growth rate is the curve's height.",
         sp.diff(g_expr, h) - f_expr),
        ("area_is_integral",
         r"The accumulated force is the area: $F(h) = \int_0^h \rho g w\,h'\,dh'$.",
         g_expr - sp.integrate(f_expr.subs(h, _s), (_s, 0, h))),
        ("avg_pressure_falls_out",
         r"The memorized $F = \bar P A$ (average pressure $\bar P = \rho g h/2$ at the centroid, area $A = wh$) is exactly the area.",
         g_expr - (rho * g * h / 2) * (w * h)),
        ("uniform_pressure_echo",
         r"If the pressure did not grow with depth ($P_0$ uniform), the integral collapses to $F = P_0 A$ — a rectangle (the quadrature).",
         sp.integrate(_P0 * w, (_s, 0, _H)) - _P0 * w * _H),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"hydrostatic-force/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "The force on the wall is the area under the pressure-times-width curve — and the average-pressure formula falls out.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{dF}{dh} = \rho g w h$; check $F = \int_0^h \rho g w\,h'\,dh'$; recover $F = \bar P A$; collapse the uniform-pressure case to $P_0 A$",
        "checks": checks,
    }

    # --- results at the full water depth h = H ---
    rsubs = {rho: rho_val, g: g_val, w: w_val, h: H_val}
    force = make_result(g_expr, rsubs, "N", r"Force on the wall $F = \tfrac12\rho g w H^2$ (the shaded area)")
    force["symbolic_latex"] = r"\tfrac12\rho g w H^2"
    bottom = make_result(rho * g * h, rsubs, "Pa", r"Pressure at the bottom $P = \rho g H$")
    bottom["symbolic_latex"] = r"\rho g H"
    avgp = make_result(rho * g * h / 2, rsubs, "Pa", r"Average (centroid) pressure $\bar P = \tfrac12\rho g H$")
    avgp["symbolic_latex"] = r"\tfrac12\rho g H"
    rect = make_result((rho * g * H_val) * (w_val * H_val), rsubs, "N",
                       r"If the pressure were the bottom value everywhere: $F = \rho g H\cdot A$ (the rectangle — twice the force)")
    rect["symbolic_latex"] = r"\rho g H\,A"
    result = {"wall_force": force, "bottom_pressure": bottom, "avg_pressure": avgp, "uniform_rectangle": rect}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you",
                "latex": r"F = \bar P\,A \qquad \bar P = \tfrac12\rho g H \quad(\text{pressure at the centroid})",
                "prose": "The algebra course says the force is the *average* pressure times the wall area. Because "
                         "the pressure runs from $0$ at the surface to $\\rho g H$ at the bottom, it takes the "
                         "average as the midpoint value $\\tfrac12\\rho g H$. That gives the right number — but only "
                         "because the pressure rises *linearly*, and the algebra cannot say why the average is the "
                         "midpoint rather than something else.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "The force is the area under the pressure–depth curve",
                "latex": r"F = \int_0^H P(h)\,w\,dh",
                "prose": "Each horizontal strip of the wall at depth $h$ (width $w$, height $dh$) feels a force "
                         "$dF = P(h)\\,w\\,dh$. The total force is the integral over the depth — the area under the "
                         "strip-force curve. For a uniform pressure this area is a rectangle ($P_0 A$); when the "
                         "pressure grows with depth it is the area under a rising line.",
            },
            {
                "label": "Use the hydrostatic law $P(h) = \\rho g h$",
                "latex": r"F = \int_0^H \rho g w\,h\,dh = \tfrac12\rho g w H^2 = \underbrace{\tfrac12\rho g H}_{\bar P}\,\underbrace{wH}_{A}",
                "prose": "With $P = \\rho g h$ the integrand is a straight line through the origin, so the area is a "
                         "triangle: $\\tfrac12\\,(\\text{base})\\,(\\text{height}) = \\tfrac12\\,H\\,(\\rho g w H)$. "
                         "That is $\\tfrac12\\rho g w H^2$ — and factoring it as $(\\tfrac12\\rho g H)(wH)$ shows the "
                         "algebra's $\\bar P A$ is exactly this area, with the centroid pressure emerging as the "
                         "average. Its slope at any depth is the strip force.",
                "emphasis": True,
            },
            {
                "label": "Why the depth, not the lake, sets the force",
                "latex": r"\text{uniform } P_0 \ \Longrightarrow\ F = \int_0^H P_0 w\,dh = P_0\,A",
                "prose": "If the pressure did not grow with depth — a gas at uniform $P_0$ pressing on the wall — the "
                         "integrand would be constant and the integral would collapse to the rectangle $P_0 A$. The "
                         "real force is only *half* the bottom-pressure rectangle $\\rho g H\\cdot A$ because the "
                         "pressure is small near the surface. And it depends only on the depth and the wall's width, "
                         "not on how much water is behind it.",
            },
        ],
    }

    area = AreaPlot(
        u=h,
        f_expr=f_expr,
        g_expr=g_expr,
        u0=0.0,
        u_window=u_window,
        cursor=Slider(h, "h", 0.0, u_window, float(H_val)),
        sliders=[Slider(rho, "rho", 500.0, 1500.0, float(rho_val))],
        constants={g: g_val, w: w_val},          # ρ is the slider, h the axis; g and w fixed for the browser
        unit_map={rho: "kg/m**3", g: "m/s**2", w: "m", h: "m"},
        u_label="h  (m)",
        f_label="dF/dh  (N/m)",
        g_label="F  (N)",
        u_unit="m",
        annot="The shaded area under ρg w h is the force on the wall; its slope is the strip force.",
    )

    return Scenario(
        regime=2,
        constants_export={"rho": float(rho_val), "g": float(g_val), "w": float(w_val), "H": float(H_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={},
        area=area,
    )
