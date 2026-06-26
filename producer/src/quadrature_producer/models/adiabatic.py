"""Regime-3 model: work done by a gas expanding **adiabatically** — the SAME integral instrument (ADR-0014)
on the volume axis as the isothermal lesson, but along a steeper curve. No engine change (model + spec + test).

An adiabatic process exchanges no heat, so $PV^\\gamma = \\text{const}$ and the pressure falls as
$P(V) = P_1(V_1/V)^\\gamma$ — steeper than the isotherm's $1/V$. The shaded AREA under that curve is the work,
$W = \\int_{V_1}^{V} P\\,dV' = \\dfrac{P_1V_1 - P_2V_2}{\\gamma-1}$, whose SLOPE is the pressure. Because the
adiabat falls off faster, the gas does *less* work than it would isothermally — and since no heat flows in,
that work is paid for out of internal energy, so the gas **cools**: $T_2/T_1 = (V_1/V_2)^{\\gamma-1}$.

Proof kind is "integral": $W'(V) = P$; $W = \\int P\\,dV$ (via `conds='none'`, so no Piecewise); the memorized
adiabatic-work formula falls out; and the constant-pressure (isobaric) case collapses to the rectangle
$P\\,\\Delta V$ — the quadrature echo. The proof keeps $\\gamma$ symbolic (general), and every identity certifies
in a symbolic tier (it never reaches numeric sampling, which would choke on the $V^{1-\\gamma}$ powers).

The interactive AreaPlot bakes $\\gamma$ to its numeric value (a free $\\gamma$ would make the closed form's
$1/(1-\\gamma)$ singular when the dimensional check collapses units) and exposes the **initial pressure** $P_1$
as the slider: $P_1$ sets the curve's *scale*, while $\\gamma$ fixes its *shape* and the cooling ratio. The
cursor sweeps the volume; the shaded area is the accumulated work.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

V = sp.Symbol("V", positive=True)       # volume (the integration axis)
gamma = sp.Symbol("gamma", positive=True)  # heat-capacity ratio Cp/Cv (kept symbolic in the proof; >1)
P1 = sp.Symbol("P1", positive=True)     # initial pressure (the free slider — sets the curve's scale)
V1 = sp.Symbol("V1", positive=True)     # initial volume (constant; lower limit of the integral)
_V2 = sp.Symbol("V2", positive=True)    # fresh symbols for the memorized-result + isobaric echoes
_P0 = sp.Symbol("P0", positive=True)
_w = sp.Symbol("w", positive=True)      # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={V: (1.2e-3, 4.0e-3), gamma: (1.1, 1.67), P1: (5.0e4, 2.0e5), V1: (5.0e-4, 1.2e-3),
            _V2: (1.5e-3, 4.0e-3), _P0: (1.0e4, 2.0e5)},
    positive={V, gamma, P1, V1, _V2, _P0},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("P1", "V1", "V2", "gamma"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: adiabatic requires parameters.{key}")
    P1_val, V1_val = sp.nsimplify(p["P1"]), sp.nsimplify(p["V1"])
    V2_val, gamma_val = sp.nsimplify(p["V2"]), sp.nsimplify(p["gamma"])
    u_window = float(p.get("v_window", float(V2_val) * 1.15))

    # --- symbolic integrand P(V) and accumulated work W(V) along the adiabat (γ symbolic, for the proof) ---
    f_expr = P1 * (V1 / V) ** gamma
    g_expr = P1 * V1**gamma * (V ** (1 - gamma) - V1 ** (1 - gamma)) / (1 - gamma)
    P2 = f_expr.subs(V, _V2)                                  # pressure at the far volume
    memorized = (P1 * V1 - P2 * _V2) / (gamma - 1)            # the textbook W = (P₁V₁ − P₂V₂)/(γ−1)
    T_ratio = (V1 / _V2) ** (gamma - 1)                       # T₂/T₁ from PVγ = const & PV = nRT

    # --- proof (kind "integral"): conds='none' avoids the Piecewise; every check certifies symbolically ---
    checks_spec = [
        ("ftc_slope",
         r"The work's slope is the pressure: $\tfrac{dW}{dV} = P$ — the area's rate of growth is the curve's height.",
         sp.diff(g_expr, V) - f_expr),
        ("area_is_integral",
         r"The accumulated work is the area: $W(V) = \int_{V_1}^{V} P\,dV'$.",
         g_expr - sp.integrate(f_expr.subs(V, _w), (_w, V1, V), conds="none")),
        ("adiabatic_falls_out",
         r"The memorized adiabatic work $W = \dfrac{P_1V_1 - P_2V_2}{\gamma-1}$ is exactly the area at $V_2$.",
         g_expr.subs(V, _V2) - memorized),
        ("isobaric_echo",
         r"At constant pressure the integral collapses to $W = P\,\Delta V$ — the area is a rectangle (the quadrature).",
         sp.integrate(_P0, (_w, V1, _V2)) - _P0 * (_V2 - V1)),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"adiabatic/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "The adiabatic work is the area under a steeper P–V curve — and the memorized result falls out, with the gas cooling.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{dW}{dV} = P$; check $W = \int_{V_1}^{V} P\,dV'$; recover $W = (P_1V_1 - P_2V_2)/(\gamma-1)$; collapse the constant-pressure case to $P\,\Delta V$",
        "checks": checks,
    }

    rsubs = {P1: P1_val, V1: V1_val, gamma: gamma_val, V: V2_val}
    work = make_result(g_expr, rsubs, "J", r"Adiabatic work $W = \dfrac{P_1V_1 - P_2V_2}{\gamma-1}$ (the shaded area)")
    work["symbolic_latex"] = r"\tfrac{P_1V_1 - P_2V_2}{\gamma-1}"
    p2 = make_result(f_expr.subs(V, V2_val), {P1: P1_val, V1: V1_val, gamma: gamma_val}, "Pa",
                     r"Final pressure $P_2 = P_1(V_1/V_2)^\gamma$")
    p2["symbolic_latex"] = r"P_1\!\left(\tfrac{V_1}{V_2}\right)^{\!\gamma}"
    rect = make_result(P1 * (V2_val - V1_val), {P1: P1_val}, "J",
                       r"If pressure stayed at $P_1$: $W = P_1\,\Delta V$ (the rectangle)")
    rect["symbolic_latex"] = r"P_1\,\Delta V"
    tr = make_result(T_ratio.subs(_V2, V2_val), {V1: V1_val, gamma: gamma_val}, "",
                     r"Temperature ratio $T_2/T_1 = (V_1/V_2)^{\gamma-1}$ — the gas cools")
    tr["symbolic_latex"] = r"\left(\tfrac{V_1}{V_2}\right)^{\!\gamma-1}"
    result = {"adiabatic_work": work, "final_pressure": p2, "isobaric_rectangle": rect, "temperature_ratio": tr}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (a formula to memorize)",
                "latex": r"W = \frac{P_1V_1 - P_2V_2}{\gamma-1} \qquad(\text{adiabatic, }PV^\gamma=\text{const})",
                "prose": "For an adiabatic process the algebra course hands you $W = (P_1V_1 - P_2V_2)/(\\gamma-1)$ "
                         "with no account of where the $\\gamma$ or the denominator come from. It can compute the "
                         "number but cannot show that the work is the area under a particular curve — or why that "
                         "area is smaller than the isothermal one.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Work is the area under the pressure–volume curve",
                "latex": r"W = \int_{V_1}^{V_2} P\,dV",
                "prose": "As before, the work done by the gas is the integral of pressure over volume — the area "
                         "under the $P$–$V$ curve. What changes from the isotherm is only the *shape* of $P(V)$.",
            },
            {
                "label": "Use the adiabatic law $PV^\\gamma = \\text{const}$",
                "latex": r"P = P_1\!\left(\frac{V_1}{V}\right)^{\!\gamma} \ \Longrightarrow\ W = \int_{V_1}^{V_2} P_1V_1^\gamma\,V^{-\gamma}\,dV = \frac{P_1V_1 - P_2V_2}{\gamma-1}",
                "prose": "With no heat exchanged, $PV^\\gamma$ is constant, so $P\\propto V^{-\\gamma}$ — a steeper "
                         "fall than the isotherm's $V^{-1}$. Integrating that power law gives the memorized adiabatic "
                         "work exactly; its slope at any volume is $P(V)$. Because the curve drops faster, the area "
                         "is *smaller* than the isothermal area between the same volumes.",
                "emphasis": True,
            },
            {
                "label": "No heat in, so the gas cools",
                "latex": r"\boxed{\,\frac{T_2}{T_1} = \left(\frac{V_1}{V_2}\right)^{\!\gamma-1}\,}",
                "prose": "Since no heat enters, the work comes out of the gas's internal energy, so its temperature "
                         "falls — combine $PV^\\gamma=\\text{const}$ with $PV = nRT$ and the temperature ratio is "
                         "$(V_1/V_2)^{\\gamma-1}$. The isotherm holds $T$ fixed by drawing heat from a reservoir; the "
                         "adiabat has no reservoir, so the area you can extract is bounded by the cooling. $P_1$ sets "
                         "the curve's height, but $\\gamma$ alone fixes its shape and this cooling ratio.",
            },
        ],
    }

    # interactive plot: bake γ to its value (a free γ singularises 1/(1−γ) under the dimensional check);
    # keep V1 symbolic so the dimensionless ratio V1/V survives the units check; slider is the scale P1.
    f_area = P1 * (V1 / V) ** gamma_val
    g_area = P1 * V1**gamma_val * (V ** (1 - gamma_val) - V1 ** (1 - gamma_val)) / (1 - gamma_val)
    area = AreaPlot(
        u=V,
        f_expr=f_area,
        g_expr=g_area,
        u0=float(V1_val),
        u_window=u_window,
        cursor=Slider(V, "V", float(V1_val), u_window, float(V2_val)),
        sliders=[Slider(P1, "P1", 5.0e4, 2.0e5, float(P1_val))],
        constants={V1: V1_val},               # V1 fixed for the browser; P1 is the slider, V the axis
        unit_map={P1: "Pa", V1: "m**3", V: "m**3"},
        u_label="V  (m³)",
        f_label="P  (Pa)",
        g_label="W  (J)",
        u_unit="m³",
        annot="The shaded area under the adiabat P(V) is the work; the slope of W(V) is the pressure.",
    )

    return Scenario(
        regime=3,
        constants_export={"P1": float(P1_val), "V1": float(V1_val), "V2": float(V2_val),
                          "gamma": float(gamma_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        area=area,
    )
