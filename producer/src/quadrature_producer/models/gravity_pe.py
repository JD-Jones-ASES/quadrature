"""Regime-2 model: gravitational potential energy — the area instrument (ADR-0014) on the radial axis.

The work to lift a mass against gravity is the area under the force–distance curve, F(r) = GMm/r². Because the
force is an inverse square, that area to infinity *converges* — the escape energy GMm/R is finite. Reuses the
integral instrument with no engine change. The regime-1 echo lives inside: near the surface F ≈ mg = const, so
PE ≈ mgh is the rectangle (the flat-Earth approximation). Uses μ = GM (the standard gravitational parameter,
m³/s²) so the force is unit-clean without G in the namespace; R is kept symbolic for the dimensional check.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

r = sp.Symbol("r", positive=True)          # distance from the planet's centre (the integration axis)
mu = sp.Symbol("mu", positive=True)        # standard gravitational parameter μ = GM (m³/s²)
m = sp.Symbol("m", positive=True)          # lifted mass
R = sp.Symbol("R", positive=True)          # surface radius (lower limit; symbolic for dims, fixed for the browser)
_F0 = sp.Symbol("F0", positive=True)       # fresh symbols for the constant-force (flat-Earth) echo
_h = sp.Symbol("h", positive=True)
_w = sp.Symbol("w", positive=True)

PROOF_DOMAIN = SampleDomain(
    bounds={r: (6.4e6, 4.0e7), mu: (1.0e13, 5.0e14), m: (1.0, 500.0), R: (1.0e6, 7.0e6),
            _F0: (1.0, 100.0), _h: (1.0, 1.0e4)},
    positive={r, mu, m, R, _F0, _h},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("mu", "R", "m"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: gravity-pe requires parameters.{key}")
    mu_val, R_val, m_val = sp.nsimplify(p["mu"]), sp.nsimplify(p["R"]), sp.nsimplify(p["m"])
    r_window = float(p.get("r_window", float(R_val) * 6))

    f_expr = mu * m / r**2                                   # F(r), the gravitational force
    g_expr = mu * m * (1 / R - 1 / r)                        # PE gained lifting from R to r = ∫_R^r F dr'
    escape = mu * m / R                                      # the r→∞ limit (finite!)

    checks_spec = [
        ("ftc_slope", r"The PE's slope is the force: $U'(r) = F(r)$ — the area's rate of growth is the curve's height.",
         sp.diff(g_expr, r) - f_expr),
        ("area_is_integral", r"The accumulated PE is the area: $\Delta U(r) = \int_R^r F\,dr'$.",
         g_expr - sp.integrate(f_expr.subs(r, _w), (_w, R, r))),
        ("escape_is_finite", r"The area to infinity converges: the escape energy $\to GMm/R$ is finite as $r\to\infty$.",
         sp.limit(g_expr, r, sp.oo) - escape),
        ("flat_earth_echo", r"Near the surface $F\approx mg$ is constant, so $\Delta U \approx mgh$ — the area is a rectangle (the quadrature).",
         sp.integrate(_F0, (_w, 0, _h)) - _F0 * _h),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"gravity-pe/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "Gravitational PE is the area under the force curve — and the area to infinity converges to a finite escape energy.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{d}{dr}\Delta U = F$; check $\Delta U = \int_R^r F\,dr'$; check $\lim_{r\to\infty}\Delta U = GMm/R$; collapse the near-surface case to $mgh$",
        "checks": checks,
    }

    rsubs = {mu: mu_val, m: m_val, R: R_val, r: 2 * R_val}
    pe2R = make_result(g_expr, rsubs, "J", r"PE gained reaching $r=2R$")
    pe2R["symbolic_latex"] = r"\tfrac{GMm}{2R}"
    esc = make_result(escape, {mu: mu_val, m: m_val, R: R_val}, "J", r"Escape energy $GMm/R$ (area to $\infty$)")
    esc["symbolic_latex"] = r"\tfrac{GMm}{R}"
    fsurf = make_result(f_expr.subs(r, R), rsubs, "N", r"Surface weight $F(R)=GMm/R^2=mg$")
    fsurf["symbolic_latex"] = r"\tfrac{GMm}{R^2}"
    result = {"pe_to_2R": pe2R, "escape_energy": esc, "surface_force": fsurf}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you",
                "latex": r"\Delta U = mgh \quad(\text{near the surface, } g \text{ constant})",
                "prose": "Close to the ground, gravity is treated as a constant $mg$, so the potential energy is "
                         "$mgh$ — the area of a rectangle. But gravity weakens with distance ($F\\propto 1/r^2$), "
                         "so this fails once $h$ is comparable to the planet's radius. There is no algebra formula "
                         "for the energy to reach orbit or escape.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Potential energy is the area under the force–distance curve",
                "latex": r"\Delta U = \int_R^r F\,dr' = \int_R^r \frac{GMm}{r'^2}\,dr'",
                "prose": "The work to lift a mass against gravity is the integral of the force over distance — "
                         "the area under the $F$–$r$ curve. For a constant force this is a rectangle ($mgh$); for "
                         "the inverse-square force it is the area under a falling curve.",
            },
            {
                "label": "Evaluate the inverse-square integral",
                "latex": r"\Delta U = GMm\left(\frac{1}{R} - \frac{1}{r}\right)",
                "prose": "The area under $1/r^2$ from $R$ to $r$ is $GMm(1/R - 1/r)$. Its slope at any radius is "
                         "$GMm/r^2 = F(r)$ — the force is the rate at which potential energy accumulates.",
            },
            {
                "label": "The escape energy is finite — the area converges",
                "latex": r"\boxed{\,\lim_{r\to\infty}\Delta U = \frac{GMm}{R}\,}",
                "prose": "Push the cursor outward and the PE rises toward a *finite* ceiling, even as $r\\to\\infty$: "
                         "the area under $1/r^2$ converges. That ceiling is the escape energy — and SymPy proves "
                         "the limit. A constant force would give an infinite area; the inverse square does not.",
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
        sliders=[Slider(m, "m", 1.0, 500.0, float(m_val))],
        constants={mu: mu_val, R: R_val},
        unit_map={mu: "m**3/s**2", m: "kg", r: "m", R: "m"},
        u_label="r  (m)",
        f_label="F  (N)",
        g_label="ΔU  (J)",
        u_unit="m",
        annot="The shaded area under F(r) is the potential energy gained; its slope is the force.",
    )

    return Scenario(
        regime=2,
        constants_export={"mu": float(mu_val), "R": float(R_val), "m": float(m_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={},
        area=area,
    )
