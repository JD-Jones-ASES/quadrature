"""Regime-2 model: the electric field of a continuous line of charge — the area/integral instrument
(kind:"area") on the charge-distribution axis. A uniformly charged rod (linear density $\\lambda$) lies along
the $x$-axis from $x = a$ to $x = a + L$; the field it produces at the origin is the sum of point-charge
contributions $dE = k\\,dq/x^2 = k\\lambda\\,dx/x^2$.

This is the dual register at its sharpest: the algebra-based course has the point-charge field $kq/r^2$ and is
*stuck* the moment the charge is spread out — there is no algebra formula for a continuous distribution.
Calculus is the only road in: slice the rod into infinitesimal charges and integrate. The shaded area under
$k\\lambda/x^2$ from $a$ to the cursor is the accumulated field $E(x) = k\\lambda(1/a - 1/x)$, and the total
$E = k\\lambda(1/a - 1/(a+L)) = kQ/(a(a+L))$ reduces to the point charge $kQ/a^2$ when the rod is short. Proof
kind `integral`. ($\\lambda$ is sliders in nC/m for a readable control; the field is computed in SI.)
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

x = sp.Symbol("x", positive=True)                 # position along the rod (the integration axis)
k = sp.Symbol("k", positive=True)                 # Coulomb constant, N·m²/C²
lam = sp.Symbol("lambda", positive=True)          # linear charge density, in nC/m (slider; ×1e-9 for SI)
a = sp.Symbol("a", positive=True)                 # distance from the origin to the near end of the rod
L = sp.Symbol("L", positive=True)                 # rod length
_w = sp.Symbol("w", positive=True)
_NANO = sp.Rational(1, 10**9)                      # nC → C, so the slider reads in nC/m

PROOF_DOMAIN = SampleDomain(
    bounds={x: (0.2, 2.0), k: (1e9, 1e10), lam: (50.0, 200.0), a: (0.05, 0.5), L: (0.1, 1.0)},
    positive={x, k, lam, a, L},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    k_val = sp.nsimplify(p.get("k", sp.Rational(8990000000)))
    lam_val = sp.nsimplify(p.get("lam_nc", 100))     # nC/m
    a_val = sp.nsimplify(p.get("a", sp.Rational(1, 10)))
    L_val = sp.nsimplify(p.get("L", sp.Rational(3, 10)))

    f_expr = k * lam * _NANO / x**2                  # field contribution per unit length, dE/dx
    g_expr = k * lam * _NANO * (1 / a - 1 / x)       # accumulated field E(x) = ∫_a^x f dx'
    total = g_expr.subs(x, a + L)                    # full-rod field

    checks_spec = [
        ("ftc_slope",
         r"The accumulated field's slope is the contribution density: $\dfrac{dE}{dx} = \dfrac{k\lambda}{x^2}$.",
         sp.diff(g_expr, x) - f_expr),
        ("area_is_integral",
         r"The field is the area under the contributions: $E(x) = \int_a^x \dfrac{k\lambda}{x'^2}\,dx'$.",
         g_expr - sp.integrate(f_expr.subs(x, _w), (_w, a, x))),
        ("total_field",
         r"The whole rod gives $E = k\lambda\left(\dfrac1a - \dfrac1{a+L}\right) = \dfrac{kQ}{a(a+L)}$ with $Q = \lambda L$.",
         total - k * lam * _NANO * L / (a * (a + L))),
        ("point_charge_limit",
         r"For a short rod the field reduces to a point charge: $E/Q \to k/a^2$ as $L \to 0$.",
         sp.limit(total / (lam * _NANO * L), L, 0) - k / a**2),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"line-charge/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "There is no algebra formula for a continuous charge — calculus sums the point-charge "
                   "contributions, and the area under them is the field.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $dE/dx = k\lambda/x^2$; check $E = \int_a^x k\lambda/x'^2\,dx'$; "
                  r"total $kQ/(a(a+L))$; short-rod limit $kQ/a^2$",
        "checks": checks,
    }

    rsubs = {k: k_val, lam: lam_val, a: a_val, L: L_val}
    etot = make_result(total, rsubs, "N/C", r"Total field $E = \dfrac{kQ}{a(a+L)}$")
    etot["symbolic_latex"] = r"k\lambda\!\left(\tfrac1a - \tfrac1{a+L}\right)"
    epoint = make_result(k * lam * _NANO * L / a**2, rsubs, "N/C", r"Point-charge approx $kQ/a^2$ (overestimate)")
    epoint["symbolic_latex"] = r"kQ/a^2"
    enear = make_result(g_expr.subs(x, a_val + L_val / 2), rsubs, "N/C", r"Field from the near half of the rod")
    enear["symbolic_latex"] = r"k\lambda(1/a - 1/(a+L/2))"
    result = {"total_field": etot, "point_charge_approx": epoint, "near_half_field": enear}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (and where it stops)",
                "latex": r"E_{\text{point}} = \frac{kq}{r^2}",
                "prose": "Algebra gives the field of a single point charge. But a charged rod is not a point — "
                         "the charge is spread along its length, every piece a different distance away — and "
                         "there is no algebra formula for that. This is where algebra runs out.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Slice the rod into point charges and add their fields",
                "latex": r"dE = \frac{k\,dq}{x^2} = \frac{k\lambda\,dx}{x^2}",
                "prose": "Cut the rod into slices of length $dx$, each carrying charge $dq = \\lambda\\,dx$ and "
                         "acting like a point charge at distance $x$. Its field is $k\\,dq/x^2$. Summing over the "
                         "rod is an integral — the only way to handle a continuous distribution.",
            },
            {
                "label": "The total field is the area under the contributions",
                "latex": r"E = \int_a^{a+L} \frac{k\lambda}{x^2}\,dx = k\lambda\left(\frac1a - \frac1{a+L}\right)",
                "prose": "Integrating the inverse-square contributions gives a finite field — the shaded area "
                         "under $k\\lambda/x^2$. The slope of the accumulated-field curve is the contribution at "
                         "the cursor; the area under the contributions is the field.",
                "emphasis": True,
            },
            {
                "label": "It reduces to the point charge when the rod is short",
                "latex": r"E = \frac{kQ}{a(a+L)} \ \xrightarrow{\,L \ll a\,}\ \frac{kQ}{a^2}",
                "prose": "Writing $Q = \\lambda L$, the rod's field is $kQ/(a(a+L))$. When the rod is much shorter "
                         "than its distance, this becomes $kQ/a^2$ — the point-charge formula, recovered. Drag the "
                         "cursor to sweep how much of the rod is included, and $\\lambda$ to scale the charge.",
            },
        ],
    }

    area = AreaPlot(
        u=x,
        f_expr=f_expr,
        g_expr=g_expr,
        u0=float(a_val),
        u_window=float(a_val + L_val),
        cursor=Slider(x, "x", float(a_val), float(a_val + L_val), float(a_val + L_val)),
        sliders=[Slider(lam, "lambda", 50.0, 200.0, float(lam_val))],
        constants={k: k_val, a: a_val},
        unit_map={k: "N*m**2/C**2", lam: "C/m", x: "m", a: "m"},
        u_label="x  (m)",
        f_label="dE/dx  (N/C/m)",
        g_label="E  (N/C)",
        u_unit="m",
        annot="The shaded area under the point-charge contributions kλ/x² is the field; its slope is the contribution.",
    )

    return Scenario(
        regime=2,
        constants_export={"k": float(k_val), "lam_nc": float(lam_val), "a": float(a_val), "L": float(L_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={},
        area=area,
    )
