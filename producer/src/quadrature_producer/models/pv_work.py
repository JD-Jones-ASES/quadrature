"""Regime-3 model: work done by an expanding ideal gas — the SAME integral instrument (ADR-0014) on a new
axis. Here the integration variable is **volume**, not time or position: the shaded area under the P–V curve
is the work W = ∫P dV. Thermodynamics is taught algebra-first (you memorize W = PΔV at constant pressure and
W = nRT·ln(V₂/V₁) for an isotherm), so this is regime 3 — but the calculus underpinning is clean and worth
surfacing (Phase 3 policy), and it is exactly the area under the curve.

This model adds NO engine machinery: it reuses the AreaPlot contract, the schema's area graph, the parity
oracle, and the AreaPlot island untouched — the proof that the hard instrument makes a new domain's lessons
simple. The proof kind is "integral": dW/dV = P; W = ∫P dV; the memorized isothermal result falls out; and
the constant-pressure case collapses to the rectangle W = PΔV (the quadrature echo).
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

R = sp.Rational(83145, 10000)        # ideal-gas constant, J/(mol·K) (8.3145)
V = sp.Symbol("V", positive=True)    # volume (the integration axis)
T = sp.Symbol("T", positive=True)    # temperature (the free slider — scales the whole P–V curve)
a = sp.Symbol("a", positive=True)    # a = nR (J/K), the curve scale; keeps P = a·T/V cheap and unit-clean
V1 = sp.Symbol("V1", positive=True)  # initial volume (kept symbolic for the dimensional check)
_P0 = sp.Symbol("P0", positive=True)  # fresh symbols for the constant-pressure (isobaric) echo
_Vb = sp.Symbol("Vb", positive=True)
_w = sp.Symbol("w", positive=True)   # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={V: (0.03, 0.07), T: (200.0, 500.0), a: (4.0, 20.0), V1: (0.02, 0.03),
            _P0: (1.0e4, 2.0e5), _Vb: (0.05, 0.1)},
    positive={V, T, a, V1, _P0, _Vb},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("n", "T", "V1", "V2"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: pv-work requires parameters.{key}")
    n_val, T_val = sp.nsimplify(p["n"]), sp.nsimplify(p["T"])
    V1_val, V2_val = sp.nsimplify(p["V1"]), sp.nsimplify(p["V2"])
    a_val = n_val * R
    u_window = float(p.get("v_window", float(V2_val) * 1.12))

    # integrand P(V) = nRT/V and accumulated work W(V) = ∫_{V1}^{V} P dV' = nRT·ln(V/V1).
    # Write W as the combined-log closed form (so the log argument is the dimensionless ratio V/V1, not a
    # split log(V) − log(V1) with a dimensionful argument); its equality to the integral is proven below.
    f_expr = a * T / V
    g_expr = a * T * sp.log(V / V1)

    # --- proof (kind "integral") ---
    checks_spec = [
        ("ftc_slope",
         r"The work's slope is the pressure: $\tfrac{dW}{dV} = P$ — the area's rate of growth is the curve's height.",
         sp.diff(g_expr, V) - f_expr),
        ("area_is_integral",
         r"The accumulated work is the area: $W(V) = \int_{V_1}^{V} P\,dV'$.",
         g_expr - sp.integrate(f_expr.subs(V, _w), (_w, V1, V))),
        ("isothermal_falls_out",
         r"The memorized isothermal result $W = nRT\ln(V_2/V_1)$ is exactly the area at $V_2$.",
         g_expr.subs(V, _Vb) - a * T * sp.log(_Vb / V1)),
        ("isobaric_echo",
         r"At constant pressure the integral collapses to $W = P\,\Delta V$ — the area is a rectangle (the quadrature).",
         sp.integrate(_P0, (_w, V1, _Vb)) - _P0 * (_Vb - V1)),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"pv-work/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "The work is the area under the P–V curve — and the memorized isothermal result falls out.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{dW}{dV} = P$; check $W = \int_{V_1}^{V} P\,dV'$; recover $W = nRT\ln(V_2/V_1)$; collapse the constant-pressure case to $P\,\Delta V$",
        "checks": checks,
    }

    rsubs = {a: a_val, T: T_val, V: V2_val, V1: V1_val}
    work = make_result(g_expr, rsubs, "J", r"Isothermal work $W = nRT\ln(V_2/V_1)$ (the shaded area)")
    work["symbolic_latex"] = r"nRT\ln\!\frac{V_2}{V_1}"
    p1 = make_result(f_expr.subs(V, V1), rsubs, "Pa", r"Initial pressure $P_1 = nRT/V_1$")
    p1["symbolic_latex"] = r"nRT/V_1"
    p2 = make_result(f_expr, rsubs, "Pa", r"Final pressure $P_2 = nRT/V_2$")
    p2["symbolic_latex"] = r"nRT/V_2"
    rect = make_result(f_expr.subs(V, V1) * (V2_val - V1_val), rsubs, "J",
                       r"If pressure stayed at $P_1$: $W = P_1\,\Delta V$ (the rectangle)")
    rect["symbolic_latex"] = r"P_1\,\Delta V"
    result = {"isothermal_work": work, "initial_pressure": p1, "final_pressure": p2, "rectangle_work": rect}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (two memorized cases)",
                "latex": r"W = P\,\Delta V \quad(\text{constant pressure}) \qquad W = nRT\ln\!\frac{V_2}{V_1}\quad(\text{constant temperature})",
                "prose": "At constant pressure, work is pressure times volume change — a rectangle. For an "
                         "isothermal expansion you are handed a logarithm to memorize, with no account of where "
                         "it comes from. The algebra course can use both but cannot say why one is a rectangle "
                         "and the other a logarithm.",
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
                         "$P$–$V$ curve. At constant pressure the area is a rectangle ($P\\,\\Delta V$); when "
                         "the pressure varies, it is the area under a curve.",
            },
            {
                "label": "Use the ideal-gas law at constant temperature",
                "latex": r"P = \frac{nRT}{V} \ \Longrightarrow\ W = \int_{V_1}^{V_2}\frac{nRT}{V}\,dV = nRT\ln\!\frac{V_2}{V_1}",
                "prose": "For an isotherm, $PV = nRT$ makes $P$ inversely proportional to $V$ — a hyperbola. "
                         "The area under $1/V$ is a logarithm, so the memorized isothermal work is exactly the "
                         "area under the curve. Its slope at any volume is $P(V)$.",
                "emphasis": True,
            },
            {
                "label": "Why the pressure case is the special one",
                "latex": r"P = \text{const} \ \Longrightarrow\ W = \int_{V_1}^{V_2} P\,dV = P\,(V_2 - V_1)",
                "prose": "When pressure does not vary, the integrand is constant and the integral collapses to "
                         "the rectangle $P\\,\\Delta V$ — the algebra formula is the quadrature, the area already "
                         "evaluated. The expanding-gas work is less than this rectangle because the pressure "
                         "falls as the gas expands.",
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
        sliders=[Slider(T, "T", 200.0, 500.0, float(T_val))],
        constants={a: a_val, V1: V1_val},   # T is the slider, V the axis; a=nR and V1 fixed for the browser
        unit_map={a: "J/K", T: "K", V: "m**3", V1: "m**3"},
        u_label="V  (m³)",
        f_label="P  (Pa)",
        g_label="W  (J)",
        u_unit="m³",
        annot="The shaded area under P(V) is the work; the slope of W(V) is the pressure.",
    )

    return Scenario(
        regime=3,
        constants_export={"n": float(n_val), "R": float(R), "T": float(T_val),
                          "V1": float(V1_val), "V2": float(V2_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        area=area,
    )
