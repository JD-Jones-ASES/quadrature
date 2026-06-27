"""Regime-2 model: the on-axis electric field of a uniformly charged DISK — the area/integral instrument
(kind:"area") on the ring-radius axis. A disk of radius $R$ and surface charge density $\\sigma$ produces, at a
point a distance $z$ along its axis, the field obtained by slicing the disk into concentric rings of radius $r$
(width $dr$, charge $dq = \\sigma\\,2\\pi r\\,dr$): each ring contributes $dE = k\\,dq\\,z/(z^2+r^2)^{3/2}$ on the
axis (by symmetry only the axial component survives).

This is the dual register at its sharpest — and a step beyond the line charge (`line_charge_field.py`): the
algebra-based course has the *point* charge $kq/r^2$ and the *infinite sheet* $\\sigma/2\\varepsilon_0$, but
nothing for a finite disk. Calculus is the only road in: integrate the rings. The shaded area under
$dE/dr = 2\\pi k\\sigma z\\,r/(z^2+r^2)^{3/2}$ from $0$ to the cursor is the accumulated field
$E(r) = 2\\pi k\\sigma\\,(1 - z/\\sqrt{z^2+r^2})$, and the whole disk gives
$E = \\tfrac{\\sigma}{2\\varepsilon_0}\\,(1 - z/\\sqrt{z^2+R^2})$. It bridges BOTH algebra limits: far away
($z \\gg R$) it collapses to the point charge $kQ/z^2$ with $Q = \\sigma\\pi R^2$; for a very large disk
($R \\to \\infty$) it becomes the infinite sheet $\\sigma/2\\varepsilon_0$, independent of distance. Proof kind
`integral`. ($\\sigma$ is a slider in nC/m² for a readable control; the field is computed in SI.)
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

r = sp.Symbol("r", positive=True)                 # ring radius (the integration axis)
k = sp.Symbol("k", positive=True)                 # Coulomb constant, N·m²/C²
sigma = sp.Symbol("sigma", positive=True)         # surface charge density, in nC/m² (slider; ×1e-9 for SI)
z = sp.Symbol("z", positive=True)                 # axial distance from the disk
R = sp.Symbol("R", positive=True)                 # disk radius
_w = sp.Symbol("w", positive=True)
_NANO = sp.Rational(1, 10**9)                      # nC → C, so the slider reads in nC/m²

PROOF_DOMAIN = SampleDomain(
    bounds={r: (0.05, 1.0), k: (1e9, 1e10), sigma: (50.0, 200.0), z: (0.05, 0.5), R: (0.2, 1.0)},
    positive={r, k, sigma, z, R},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    k_val = sp.nsimplify(p.get("k", sp.Rational(8990000000)))
    sigma_val = sp.nsimplify(p.get("sigma_nc", 100))   # nC/m²
    z_val = sp.nsimplify(p.get("z", sp.Rational(1, 10)))
    R_val = sp.nsimplify(p.get("R", sp.Rational(3, 10)))

    f_expr = 2 * sp.pi * k * sigma * _NANO * z * r / (z**2 + r**2)**sp.Rational(3, 2)   # dE/dr
    g_expr = 2 * sp.pi * k * sigma * _NANO * (1 - z / sp.sqrt(z**2 + r**2))             # E(r) = ∫_0^r f dr'
    total = g_expr.subs(r, R)                                                           # whole-disk field
    Q = sigma * _NANO * sp.pi * R**2                                                    # total charge σ·πR²

    checks_spec = [
        ("ftc_slope",
         r"The accumulated field's slope is the ring contribution: $\dfrac{dE}{dr} = \dfrac{2\pi k\sigma z\,r}{(z^2+r^2)^{3/2}}$.",
         sp.diff(g_expr, r) - f_expr),
        ("area_is_integral",
         r"The field is the area under the ring contributions: $E(r) = \int_0^r \dfrac{2\pi k\sigma z\,r'}{(z^2+r'^2)^{3/2}}\,dr'$.",
         g_expr - sp.integrate(f_expr.subs(r, _w), (_w, 0, r))),
        ("point_charge_limit",
         r"Far away the disk looks like a point charge: $E \to kQ/z^2$ with $Q = \sigma\pi R^2$ as $z \to \infty$.",
         sp.limit(total * z**2, z, sp.oo) - k * Q),
        ("infinite_sheet_limit",
         r"A very large disk is an infinite sheet: $E \to \sigma/2\varepsilon_0 = 2\pi k\sigma$, independent of $z$, as $R \to \infty$.",
         sp.limit(total, R, sp.oo) - 2 * sp.pi * k * sigma * _NANO),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"disk-field/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "A finite disk has no algebra formula — it sits between the point charge and the infinite "
                   "sheet. Calculus integrates the rings, and the area under them is the field.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $dE/dr = 2\pi k\sigma z\,r/(z^2+r^2)^{3/2}$; check $E = \int_0^r f\,dr'$; "
                  r"far limit $kQ/z^2$ ($z\to\infty$); large-disk limit $\sigma/2\varepsilon_0$ ($R\to\infty$)",
        "checks": checks,
    }

    rsubs = {k: k_val, sigma: sigma_val, z: z_val, R: R_val}
    etot = make_result(total, rsubs, "N/C", r"Total field $E = \dfrac{\sigma}{2\varepsilon_0}\!\left(1 - \dfrac{z}{\sqrt{z^2+R^2}}\right)$")
    etot["symbolic_latex"] = r"2\pi k\sigma\!\left(1 - \tfrac{z}{\sqrt{z^2+R^2}}\right)"
    epoint = make_result(k * Q / z**2, rsubs, "N/C", r"Point-charge approx $kQ/z^2$ (exact only far away; overestimates up close)")
    epoint["symbolic_latex"] = r"kQ/z^2,\ \ Q=\sigma\pi R^2"
    esheet = make_result(2 * sp.pi * k * sigma * _NANO, rsubs, "N/C", r"Infinite-sheet limit $\sigma/2\varepsilon_0$ (overestimate)")
    esheet["symbolic_latex"] = r"\sigma/2\varepsilon_0 = 2\pi k\sigma"
    result = {"total_field": etot, "point_charge_approx": epoint, "sheet_approx": esheet}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (two extremes, nothing between)",
                "latex": r"E_{\text{point}} = \frac{kQ}{z^2} \qquad\qquad E_{\text{sheet}} = \frac{\sigma}{2\varepsilon_0}",
                "prose": "Algebra gives the field of a *point* charge and of an *infinite* sheet — but a real disk "
                         "is neither. Its charge is spread over a finite area, every ring a different distance from "
                         "the axis point, and there is no algebra formula for that. This is where algebra runs out.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Slice the disk into rings and add their on-axis fields",
                "latex": r"dE = \frac{k\,dq\,z}{(z^2+r^2)^{3/2}}, \qquad dq = \sigma\,(2\pi r\,dr)",
                "prose": "Cut the disk into concentric rings of radius $r$ and width $dr$, each carrying charge "
                         "$dq = \\sigma\\,2\\pi r\\,dr$. By symmetry only the axial part of each ring's field "
                         "survives, $k\\,dq\\,z/(z^2+r^2)^{3/2}$. Summing over the rings is an integral — the only "
                         "way to handle a continuous distribution.",
            },
            {
                "label": "The total field is the area under the ring contributions",
                "latex": r"E = \int_0^R \frac{2\pi k\sigma z\,r}{(z^2+r^2)^{3/2}}\,dr = 2\pi k\sigma\left(1 - \frac{z}{\sqrt{z^2+R^2}}\right)",
                "prose": "Integrating the ring contributions gives the disk's field — the shaded area under "
                         "$dE/dr$. The slope of the accumulated-field curve is the contribution at the cursor; the "
                         "area under the contributions is the field. With $2\\pi k = 1/2\\varepsilon_0$ this is the "
                         "familiar $\\tfrac{\\sigma}{2\\varepsilon_0}(1 - z/\\sqrt{z^2+R^2})$.",
                "emphasis": True,
            },
            {
                "label": "It bridges both algebra limits",
                "latex": r"E \ \xrightarrow{\,z \gg R\,}\ \frac{kQ}{z^2}\,(Q=\sigma\pi R^2) \qquad E \ \xrightarrow{\,R \to \infty\,}\ \frac{\sigma}{2\varepsilon_0}",
                "prose": "Far from the disk ($z \\gg R$) the field collapses to the point charge $kQ/z^2$ with "
                         "$Q = \\sigma\\pi R^2$ — the whole disk seen from afar is just a point. For a very large "
                         "disk ($R \\to \\infty$) it becomes the infinite sheet $\\sigma/2\\varepsilon_0$, the same "
                         "at every distance. Drag the cursor to sweep how much of the disk is included, and "
                         "$\\sigma$ to scale the charge.",
            },
        ],
    }

    area = AreaPlot(
        u=r,
        f_expr=f_expr,
        g_expr=g_expr,
        u0=0.0,
        u_window=float(R_val),
        cursor=Slider(r, "r", 0.0, float(R_val), float(R_val)),
        sliders=[Slider(sigma, "sigma", 50.0, 200.0, float(sigma_val))],
        constants={k: k_val, z: z_val},
        unit_map={k: "N*m**2/C**2", sigma: "C/m**2", z: "m", r: "m"},
        u_label="r  (m)",
        f_label="dE/dr  (N/C/m)",
        g_label="E  (N/C)",
        u_unit="m",
        annot="The shaded area under the ring contributions is the field; its slope is the contribution at the cursor.",
    )

    return Scenario(
        regime=2,
        constants_export={"k": float(k_val), "sigma_nc": float(sigma_val),
                          "z": float(z_val), "R": float(R_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={},
        area=area,
    )
