"""Regime-2 model: electric potential energy of two point charges — the area instrument (ADR-0014) on the
radial axis. The electric twin of gravitational PE (`gravity_pe.py`), built with NO engine change.

The work to pull a bound pair of opposite charges apart is the area under the force–distance curve,
$F(r) = kq_1q_2/r^2$ (the Coulomb attraction magnitude). Because the force is an inverse square — exactly the
same shape as gravity — that area to infinity *converges*: the energy to fully separate the pair (its binding
energy) is finite, $kq_1q_2/R$. The regime-1 "quadrature" echo lives inside: in a *uniform* field (between
parallel plates) the force is the constant $qE$, so the PE collapses to the rectangle $U = qEd$ — the same
constant-integrand limit the capacitor lesson leans on.

Proof kind is "integral": $U'(r) = F(r)$; $U(r) = \\int_R^r F\\,dr'$; the area to infinity converges to the
finite separation energy $kq_1q_2/R$ (`sympy.limit`); and the uniform-field case collapses to $qEd$. The force
$kq_1q_2/r^2$ is a JS-cheap rational function, so the graph is interactive (ADR-0012): a cursor sweeps the
separation and the shaded area (= the energy supplied so far) grows toward its ceiling.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

r = sp.Symbol("r", positive=True)          # separation between the charges (the integration axis)
k = sp.Symbol("k", positive=True)          # Coulomb constant 1/(4πε₀), N·m²/C²
q1 = sp.Symbol("q1", positive=True)        # fixed charge magnitude (one of the pair)
q2 = sp.Symbol("q2", positive=True)        # moving charge magnitude (the free slider — scales the curve)
R = sp.Symbol("R", positive=True)          # initial separation (lower limit; symbolic for dims, fixed for browser)
_F0 = sp.Symbol("F0", positive=True)       # fresh symbols for the uniform-field (constant-force) echo
_d = sp.Symbol("d", positive=True)
_w = sp.Symbol("w", positive=True)         # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={r: (0.01, 0.2), k: (8.0e9, 9.5e9), q1: (1.0e-6, 5.0e-6), q2: (1.0e-6, 5.0e-6),
            R: (0.005, 0.05), _F0: (1.0, 100.0), _d: (0.001, 0.1)},
    positive={k, q1, q2, R, _F0, _d},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("k", "q1", "q2", "R"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: coulomb-pe requires parameters.{key}")
    k_val, q1_val = sp.nsimplify(p["k"]), sp.nsimplify(p["q1"])
    q2_val, R_val = sp.nsimplify(p["q2"]), sp.nsimplify(p["R"])
    r_window = float(p.get("r_window", float(R_val) * 6))

    f_expr = k * q1 * q2 / r**2                              # F(r), the Coulomb force magnitude
    g_expr = k * q1 * q2 * (1 / R - 1 / r)                   # energy supplied separating from R to r = ∫_R^r F dr'
    separation = k * q1 * q2 / R                             # the r→∞ limit (finite!) — the binding energy

    checks_spec = [
        ("ftc_slope", r"The PE's slope is the force: $U'(r) = F(r)$ — the area's rate of growth is the curve's height.",
         sp.diff(g_expr, r) - f_expr),
        ("area_is_integral", r"The accumulated PE is the area: $\Delta U(r) = \int_R^r F\,dr'$.",
         g_expr - sp.integrate(f_expr.subs(r, _w), (_w, R, r))),
        ("separation_is_finite", r"The area to infinity converges: the energy to fully separate the pair $\to kq_1q_2/R$ is finite as $r\to\infty$.",
         sp.limit(g_expr, r, sp.oo) - separation),
        ("uniform_field_echo", r"In a uniform field $F\approx qE$ is constant, so $U \approx qEd$ — the area is a rectangle (the quadrature).",
         sp.integrate(_F0, (_w, 0, _d)) - _F0 * _d),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"coulomb-pe/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "Electric PE is the area under the Coulomb force curve — and the area to infinity converges to a finite separation energy.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{d}{dr}\Delta U = F$; check $\Delta U = \int_R^r F\,dr'$; check $\lim_{r\to\infty}\Delta U = kq_1q_2/R$; collapse the uniform-field case to $qEd$",
        "checks": checks,
    }

    rsubs = {k: k_val, q1: q1_val, q2: q2_val, R: R_val, r: 2 * R_val}
    pe2R = make_result(g_expr, rsubs, "J", r"PE gained reaching $r=2R$")
    pe2R["symbolic_latex"] = r"\tfrac{kq_1q_2}{2R}"
    sep = make_result(separation, {k: k_val, q1: q1_val, q2: q2_val, R: R_val}, "J",
                      r"Separation energy $kq_1q_2/R$ (area to $\infty$)")
    sep["symbolic_latex"] = r"\tfrac{kq_1q_2}{R}"
    finit = make_result(f_expr.subs(r, R), rsubs, "N", r"Force at the start $F(R)=kq_1q_2/R^2$")
    finit["symbolic_latex"] = r"\tfrac{kq_1q_2}{R^2}"
    result = {"pe_to_2R": pe2R, "separation_energy": sep, "initial_force": finit}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you",
                "latex": r"U = \frac{kq_1q_2}{r}\quad(\text{point charges}) \qquad U = qEd\quad(\text{uniform field})",
                "prose": "The algebra-based course hands you the point-charge energy $kq_1q_2/r$ as a formula, and "
                         "for a uniform field (parallel plates) the energy $qEd$ — a constant force times a "
                         "distance. It can compute the number but cannot show that the energy is an *area* under the "
                         "Coulomb force, or why pulling a bound pair completely apart takes only a *finite* amount "
                         "of energy when the force reaches out forever.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Electric PE is the area under the force–distance curve",
                "latex": r"\Delta U = \int_R^r F\,dr' = \int_R^r \frac{kq_1q_2}{r'^2}\,dr'",
                "prose": "The energy to pull two attracting charges apart is the integral of the Coulomb force over "
                         "distance — the area under the $F$–$r$ curve. For a constant force (a uniform field) this is "
                         "a rectangle ($qEd$); for the inverse-square force of point charges it is the area under a "
                         "falling curve.",
            },
            {
                "label": "Evaluate the inverse-square integral",
                "latex": r"\Delta U = kq_1q_2\left(\frac{1}{R} - \frac{1}{r}\right)",
                "prose": "The area under $1/r^2$ from $R$ to $r$ is $kq_1q_2(1/R - 1/r)$. Its slope at any separation "
                         "is $kq_1q_2/r^2 = F(r)$ — the force is the rate at which the potential energy accumulates. "
                         "This is the *same* inverse-square area as gravity, with charge in place of mass.",
            },
            {
                "label": "The separation energy is finite — the area converges",
                "latex": r"\boxed{\,\lim_{r\to\infty}\Delta U = \frac{kq_1q_2}{R}\,}",
                "prose": "Push the cursor outward and the energy rises toward a *finite* ceiling, even as "
                         "$r\\to\\infty$: the area under $1/r^2$ converges. That ceiling is the binding energy — the "
                         "energy needed to completely separate the pair — and SymPy proves the limit. A constant "
                         "force would give an infinite area; the inverse square does not. (To bring point charges "
                         "all the way *together*, $r\\to 0$, does diverge — the convergent end is infinity, not "
                         "contact.)",
                "emphasis": True,
            },
        ],
    }

    area = AreaPlot(
        u=r,
        f_expr=f_expr,
        g_expr=g_expr,
        u0=float(R_val),
        u_window=r_window,
        cursor=Slider(r, "r", float(R_val), r_window, float(2 * R_val)),
        sliders=[Slider(q2, "q2", 1.0e-6, 5.0e-6, float(q2_val))],
        constants={k: k_val, q1: q1_val, R: R_val},
        unit_map={k: "N*m**2/C**2", q1: "C", q2: "C", r: "m", R: "m"},
        u_label="r  (m)",
        f_label="F  (N)",
        g_label="ΔU  (J)",
        u_unit="m",
        annot="The shaded area under F(r) is the energy supplied; its slope is the Coulomb force.",
    )

    return Scenario(
        regime=2,
        constants_export={"k": float(k_val), "q1": float(q1_val), "q2": float(q2_val), "R": float(R_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={},
        area=area,
    )
