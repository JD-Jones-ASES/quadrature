"""Regime-2 model: the energy stored in a capacitor — the integral instrument (ADR-0014) on the **charge**
axis. This opens the E&M domain (Phase 2) with NO engine change: it reuses the AreaPlot contract, the area
schema, the parity oracle, and the AreaPlot island untouched.

There is no temporal x–t/v–t/a–t stack. The pivot is the **voltage–charge** graph: as charge accumulates on
the plates the voltage rises linearly, $V(q) = q/C$, and the shaded AREA under that line from $0$ to $q$ is the
energy stored, $U(q) = \\int_0^q V\\,dq' = q^2/2C$, whose SLOPE is the voltage. The memorized $\\tfrac12 CV^2$
is exactly that area — a triangle, not a rectangle. The regime-1 "quadrature" echo lives inside: a *battery*
holding the voltage constant would do $W = VQ$ (a rectangle), exactly twice the stored energy — the missing
half is dissipated in the charging resistance, the classic "where did half the energy go" result.

Proof kind is "integral": $U'(q) = V(q)$; $U = \\int_0^q V\\,dq'$; the memorized $\\tfrac12 CV^2$ falls out;
and the constant-voltage case collapses to the rectangle $VQ$. The integrand $V(q) = q/C$ is a JS-cheap
polynomial, so the graph is fully interactive (ADR-0012): a cursor sweeps the upper limit and the shaded area
(= stored energy) grows with it.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

q = sp.Symbol("q", nonnegative=True, real=True)   # charge on the plates (the integration axis)
C = sp.Symbol("C", positive=True)                 # capacitance, F (the free slider — sets the line's slope 1/C)
_Q = sp.Symbol("Q", positive=True)                # fresh symbols for the ½CV² / constant-voltage echoes
_V0 = sp.Symbol("V0", positive=True)
_w = sp.Symbol("w", nonnegative=True)             # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={q: (0.01, 0.2), C: (1.0e-4, 2.0e-3), _Q: (0.01, 0.2), _V0: (1.0, 400.0)},
    positive={C, _Q, _V0},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("C", "Q"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: capacitor-energy requires parameters.{key}")
    C_val, Q_val = sp.nsimplify(p["C"]), sp.nsimplify(p["Q"])
    u_window = float(p.get("q_window", float(Q_val) * 1.2))
    V_final = Q_val / C_val

    # --- the integrand V(q) = q/C and its accumulated integral U(q) = ∫₀^q q'/C dq' = q²/2C ---
    f_expr = q / C                                  # voltage across the capacitor
    g_expr = q**2 / (2 * C)                         # energy stored

    # --- proof (kind "integral"): the FTC relationship + ½CV² + the constant-voltage (battery) echo ---
    V_of_Q = _Q / C
    checks_spec = [
        ("ftc_slope",
         r"The energy's slope is the voltage: $U'(q) = V(q)$ — the area's rate of growth is the curve's height.",
         sp.diff(g_expr, q) - f_expr),
        ("area_is_integral",
         r"The stored energy is exactly the area: $U(q) = \int_0^q V\,dq'$.",
         g_expr - sp.integrate(f_expr.subs(q, _w), (_w, 0, q))),
        ("half_cv2",
         r"The memorized $\tfrac12 CV^2$ is the area at full charge: $\tfrac12 C V^2 = U(Q)$ with $V = Q/C$.",
         sp.Rational(1, 2) * C * V_of_Q**2 - g_expr.subs(q, _Q)),
        ("constant_voltage_echo",
         r"A battery holding the voltage constant would do $W = VQ$ — a rectangle, twice the stored energy (the quadrature).",
         sp.integrate(_V0, (_w, 0, _Q)) - _V0 * _Q),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"capacitor-energy/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "The stored energy is the area under the voltage–charge line — and the memorized ½CV² falls out of the integral.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{dU}{dq} = V$; check $U = \int_0^q V\,dq'$; recover $\tfrac12 C V^2$; the constant-voltage case is the rectangle $VQ$ (twice the energy)",
        "checks": checks,
    }

    # --- results at the worked charge Q ---
    rsubs = {C: C_val, q: Q_val}
    energy = make_result(g_expr, rsubs, "J", r"Energy stored $U = \tfrac12 C V^2 = Q^2/2C$ (the shaded area)")
    energy["symbolic_latex"] = r"\tfrac{Q^2}{2C}"
    voltage = make_result(f_expr, rsubs, "V", r"Final voltage $V = Q/C$")
    voltage["symbolic_latex"] = r"Q/C"
    rect = make_result(f_expr.subs(q, Q_val) * Q_val, rsubs, "J",
                       r"If the voltage were constant: $W = VQ$ (the rectangle — twice the energy)")
    rect["symbolic_latex"] = r"V\,Q"
    charge = make_result(q, {q: Q_val}, "C", r"Charge delivered $Q = C V$")
    charge["symbolic_latex"] = r"C\,V"
    result = {"energy_stored": energy, "final_voltage": voltage, "battery_work": rect, "final_charge": charge}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you",
                "latex": r"U = \tfrac12 C V^2 = \tfrac12 Q V \qquad(\bar V = \tfrac12 V,\ \text{the average voltage})",
                "prose": "The energy in a capacitor is handed to you as $\\tfrac12 C V^2$, usually justified by an "
                         "*average voltage*: the voltage ramps from $0$ to $V$, so on average the charge crosses "
                         "$\\tfrac12 V$, giving $U = \\tfrac12 Q V$. That works — but only because the voltage rises "
                         "*linearly*, and the algebra cannot say why the factor is $\\tfrac12$ rather than $1$.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Energy is the area under the voltage–charge line",
                "latex": r"U = \int_0^Q V\,dq",
                "prose": "Pushing a charge $dq$ across the capacitor's voltage $V$ costs energy $V\\,dq$. The total "
                         "stored energy is the integral of voltage over charge — the area under the $V$–$q$ graph. "
                         "Because $V = q/C$ rises from zero, that area is a triangle, not a rectangle.",
            },
            {
                "label": "Evaluate for the linear law $V(q) = q/C$",
                "latex": r"U = \int_0^{Q} \frac{q}{C}\,dq = \frac{Q^2}{2C} = \tfrac12 C V^2",
                "prose": "The area under a straight line from the origin is $\\tfrac12\\,(\\text{base})\\,"
                         "(\\text{height}) = \\tfrac12\\,Q\\,(Q/C) = Q^2/2C$. Substituting $Q = CV$ gives the "
                         "memorized $\\tfrac12 C V^2$ — it is exactly the area, and its slope is $V(q)$.",
                "emphasis": True,
            },
            {
                "label": "Where the other half went",
                "latex": r"\boxed{\,U = \tfrac12 V Q \quad\text{but a battery does}\quad W = V Q\,}",
                "prose": "If a battery had held the voltage at $V$ the whole time, it would have done $W = VQ$ — the "
                         "full rectangle. The capacitor stores only the triangle $\\tfrac12 VQ$; the other half is "
                         "dissipated as heat in the wire's resistance while the charge flows. The constant-voltage "
                         "rectangle is the quadrature; the real charging is the area under a rising line.",
            },
        ],
    }

    area = AreaPlot(
        u=q,
        f_expr=f_expr,
        g_expr=g_expr,
        u0=0.0,
        u_window=u_window,
        cursor=Slider(q, "q", 0.0, u_window, float(Q_val)),
        sliders=[Slider(C, "C", 1.0e-4, 2.0e-3, float(C_val))],
        constants={},                       # C is a slider; q is the axis
        unit_map={C: "F", q: "C"},
        u_label="q  (C)",
        f_label="V  (V)",
        g_label="U  (J)",
        u_unit="C",
        annot="The shaded area under V(q) is the stored energy; the slope of U(q) is the voltage.",
    )

    return Scenario(
        regime=2,
        constants_export={"C": float(C_val), "Q": float(Q_val), "V": float(V_final)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={"q0": 0.0, "V0": 0.0},
        area=area,
    )
