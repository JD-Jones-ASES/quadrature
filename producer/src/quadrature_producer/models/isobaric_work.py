"""Regime-3 model: work done by a gas expanding at CONSTANT pressure — the area instrument (ADR-0014) in its
simplest, most revealing case. The integration variable is **volume**; the shaded area under the P–V curve is
the work W = ∫P dV. Here the integrand is a constant (P does not change), so the curve is a horizontal line and
the area is a **rectangle**: W = P·ΔV. This is the cleanest "quadrature = the integral already evaluated" in the
whole course — the memorized algebra formula and the calculus integral are *literally identical* because the
integrand is constant.

It completes the PV-process trio on one instrument: the isotherm (P ∝ 1/V, a hyperbola → a logarithm), the
adiabat (P ∝ V^−γ, steeper → a power law), and the **isobar** (P constant → a flat line → a rectangle). No engine
machinery is added: it reuses the AreaPlot contract, the schema's area graph, the parity oracle, and the AreaPlot
island untouched. Proof kind "integral": dW/dV = P; W = ∫P dV; and a constant integrand makes the integral the
rectangle base×height (the quadrature).
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

V = sp.Symbol("V", positive=True)    # volume (the integration axis)
P = sp.Symbol("P", positive=True)    # pressure (the free slider — the constant height of the rectangle)
V1 = sp.Symbol("V1", positive=True)  # initial volume (kept symbolic for the dimensional check)
_Vb = sp.Symbol("Vb", positive=True)  # a fresh upper limit for the quadrature identity
_w = sp.Symbol("w", positive=True)   # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={V: (0.001, 0.004), P: (5e4, 2e5), V1: (5e-4, 1.5e-3), _Vb: (2e-3, 4e-3)},
    positive={V, P, V1, _Vb},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("P", "V1", "V2"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: isobaric-work requires parameters.{key}")
    P_val, V1_val, V2_val = sp.nsimplify(p["P"]), sp.nsimplify(p["V1"]), sp.nsimplify(p["V2"])
    u_window = float(p.get("v_window", float(V2_val) * 1.18))

    # integrand P(V) = P (constant) and accumulated work W(V) = ∫_{V1}^{V} P dV' = P·(V − V1) (a straight line).
    f_expr = P
    g_expr = P * (V - V1)

    # --- proof (kind "integral") ---
    checks_spec = [
        ("ftc_slope",
         r"The work's slope is the pressure: $\tfrac{dW}{dV} = P$ — the area's rate of growth is the (constant) height.",
         sp.diff(g_expr, V) - f_expr),
        ("area_is_integral",
         r"The accumulated work is the area: $W(V) = \int_{V_1}^{V} P\,dV'$.",
         g_expr - sp.integrate(f_expr.subs(V, _w), (_w, V1, V))),
        ("rectangle_quadrature",
         r"A constant integrand makes the integral a rectangle: $\int_{V_1}^{V_2} P\,dV = P\,\Delta V$ — the algebra formula *is* the integral already evaluated.",
         sp.integrate(P, (_w, V1, _Vb)) - P * (_Vb - V1)),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"isobaric-work/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "The work is the area under the P–V curve — and because the pressure is constant, that area "
                   "is a rectangle, W = PΔV (the quadrature).",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{dW}{dV} = P$; check $W = \int_{V_1}^{V} P\,dV'$; collapse the constant-integrand integral to the rectangle $P\,\Delta V$",
        "checks": checks,
    }

    rsubs = {P: P_val, V: V2_val, V1: V1_val}
    work = make_result(g_expr, rsubs, "J", r"Isobaric work $W = P\,\Delta V$ (the shaded rectangle)")
    work["symbolic_latex"] = r"P\,\Delta V"
    pres = make_result(P, rsubs, "Pa", r"Pressure $P$ (constant — the height of the rectangle)")
    pres["symbolic_latex"] = r"P"
    dv = make_result(V2_val - V1_val, rsubs, "m**3", r"Volume change $\Delta V = V_2 - V_1$ (the width)")
    dv["symbolic_latex"] = r"V_2 - V_1"
    result = {"isobaric_work": work, "pressure": pres, "volume_change": dv}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (a rectangle of work)",
                "latex": r"W = P\,\Delta V = P\,(V_2 - V_1)\quad(\text{constant pressure})",
                "prose": "At constant pressure, work is pressure times volume change — the area of a rectangle "
                         "on the $P$–$V$ diagram. The algebra course uses this directly; it is the one process "
                         "whose work is just 'height times width,' with no curve to integrate.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Work is the area under the pressure–volume curve",
                "latex": r"W = \int_{V_1}^{V_2} P\,dV",
                "prose": "Work done by the gas is the integral of pressure over volume — the area under the "
                         "$P$–$V$ curve, for *any* process. The shape of that area depends on how $P$ varies as "
                         "the gas expands.",
            },
            {
                "label": "A constant pressure makes the integrand constant — the area is a rectangle",
                "latex": r"P = \text{const} \ \Longrightarrow\ W = \int_{V_1}^{V_2} P\,dV = P\,(V_2 - V_1)",
                "prose": "When the pressure does not vary, $P$ comes straight out of the integral and what is "
                         "left, $\\int_{V_1}^{V_2} dV = V_2 - V_1$, is just the width. The area is a rectangle "
                         "$P\\,\\Delta V$ — the algebra formula is the integral already evaluated, the simplest "
                         "*quadrature*. Its slope at every volume is the constant height $P$.",
                "emphasis": True,
            },
            {
                "label": "Why this is the easy one (and the others are not)",
                "latex": r"\text{isobar: } P=\text{const}\quad\text{vs}\quad \text{isotherm: } P=\frac{nRT}{V}\ \ (\text{a curve})",
                "prose": "Compare the isothermal expansion, where $P = nRT/V$ falls as the gas expands: that area "
                         "is under a hyperbola, a logarithm, not a rectangle. The isobaric case is special "
                         "precisely because its integrand is constant — the same reason the constant-acceleration "
                         "kinematics formulas are quadratures.",
            },
        ],
    }

    area = AreaPlot(
        u=V,
        f_expr=f_expr,
        g_expr=g_expr,
        u0=float(V1_val),
        u_window=u_window,
        cursor=Slider(V, "V", float(V1_val), u_window, float(V2_val)),
        sliders=[Slider(P, "P", 5.0e4, 2.0e5, float(P_val))],
        constants={V1: V1_val},          # P is the slider, V the axis; V1 fixed for the browser
        unit_map={P: "Pa", V: "m**3", V1: "m**3"},
        u_label="V  (m³)",
        f_label="P  (Pa)",
        g_label="W  (J)",
        u_unit="m³",
        annot="The shaded area under the constant P is the work; it is a rectangle, W = PΔV.",
    )

    return Scenario(
        regime=3,
        constants_export={"P": float(P_val), "V1": float(V1_val), "V2": float(V2_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        area=area,
    )
