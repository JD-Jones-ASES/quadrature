"""Regime-2 model: the moment of inertia of a rod — the integral instrument (ADR-0014) on a **mass-distribution**
axis. The algebra-based course hands you a *table* of moments ($\\tfrac13ML^2$ for a rod about its end,
$\\tfrac12MR^2$ for a disk, $MR^2$ for a hoop) with no derivation; calculus produces them all from one integral,
$I = \\int r^2\\,dm$. This reuses the AreaPlot with no engine change.

There is no temporal x–t/v–t/a–t stack. The pivot is the **(dI/dr)–r** graph: with the rod's mass spread at
linear density $\\lambda = M/L$, each slice at radius $r$ contributes $dI = r^2\\,dm = \\lambda r^2\\,dr$, so the
integrand is $dI/dr = \\lambda r^2$ (a parabola). The shaded AREA under it from $0$ to $r$ is the accumulated
moment $I(r) = \\int_0^r \\lambda r'^2\\,dr' = \\tfrac13\\lambda r^3$, whose SLOPE is $\\lambda r^2$, and which at
the rod's end ($r=L$) gives the memorized $\\tfrac13ML^2$. The regime-1 "quadrature" echo: if all the mass sat
at a single radius $R$ (a thin hoop), the integrand is the constant $R^2$ in $dm$ and the integral collapses to
$I = MR^2$ — the table's hoop value is the rectangle.

Proof kind is "integral": $I'(r) = dI/dr$; $I(r) = \\int_0^r \\lambda r'^2\\,dr'$; the memorized $\\tfrac13ML^2$
falls out at $r=L$; and the hoop case collapses to $MR^2$. The integrand is a JS-cheap polynomial, so the graph
is interactive (ADR-0012): a cursor sweeps the radius and the shaded area (= accumulated $I$) grows with it.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

r = sp.Symbol("r", nonnegative=True, real=True)   # distance from the pivot end (the integration axis)
M = sp.Symbol("M", positive=True)                 # total rod mass, kg (the free slider — scales the curve)
L = sp.Symbol("L", positive=True)                 # rod length, m (constant; the upper limit / pivot-to-tip)
_M = sp.Symbol("Mh", positive=True)               # fresh symbols for the hoop (constant-radius) echo
_R = sp.Symbol("Rh", positive=True)
_w = sp.Symbol("w", nonnegative=True)             # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={r: (0.05, 1.5), M: (0.1, 10.0), L: (0.3, 2.0), _M: (0.1, 10.0), _R: (0.05, 2.0)},
    positive={M, L, _M, _R},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("M", "L"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: moment-of-inertia requires parameters.{key}")
    M_val, L_val = sp.nsimplify(p["M"]), sp.nsimplify(p["L"])
    u_window = float(p.get("r_window", float(L_val) * 1.18))

    lam = M / L                                     # linear mass density λ = M/L (kg/m)
    f_expr = lam * r**2                             # dI/dr = λ r²  (the slice's contribution per unit length)
    g_expr = sp.integrate(lam * _w**2, (_w, 0, r))  # I(r) = ∫₀ʳ λ r'² dr' = λ r³/3

    # --- proof (kind "integral") ---
    checks_spec = [
        ("ftc_slope",
         r"The moment's slope is the integrand: $\tfrac{dI}{dr} = \lambda r^2$ — the area's growth rate is the curve's height.",
         sp.diff(g_expr, r) - f_expr),
        ("area_is_integral",
         r"The accumulated moment is the area: $I(r) = \int_0^r \lambda r'^2\,dr'$.",
         g_expr - sp.integrate(f_expr.subs(r, _w), (_w, 0, r))),
        ("rod_falls_out",
         r"At the rod's end the area is the memorized $I = \tfrac13 M L^2$.",
         g_expr.subs(r, L) - M * L**2 / 3),
        ("hoop_echo",
         r"If all the mass sat at one radius $R$ (a hoop), the integral collapses to $I = M R^2$ — the rectangle (the quadrature).",
         sp.integrate(_R**2, (_w, 0, _M)) - _R**2 * _M),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"moment-of-inertia/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "The moment of inertia is the area under dI/dr = λr² — and the table's ⅓ML² falls out of the integral.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{dI}{dr} = \lambda r^2$; check $I = \int_0^r \lambda r'^2\,dr'$; recover $\tfrac13 M L^2$ at $r=L$; collapse the hoop case to $M R^2$",
        "checks": checks,
    }

    # --- results at the rod's end r = L ---
    rsubs = {M: M_val, L: L_val, r: L_val}
    inertia = make_result(g_expr, rsubs, "kg*m**2", r"Moment of inertia $I = \tfrac13 M L^2$ (the shaded area)")
    inertia["symbolic_latex"] = r"\tfrac13 M L^2"
    hoop = make_result(M * L**2, {M: M_val, L: L_val}, "kg*m**2",
                       r"If all the mass were at the tip: $I = M L^2$ (the hoop/point rectangle)")
    hoop["symbolic_latex"] = r"M L^2"
    density = make_result(lam, {M: M_val, L: L_val}, "kg/m", r"Linear mass density $\lambda = M/L$")
    density["symbolic_latex"] = r"M/L"
    tip_rate = make_result(f_expr.subs(r, L), rsubs, "kg*m", r"Integrand at the tip $\lambda L^2$")
    tip_rate["symbolic_latex"] = r"\lambda L^2"
    result = {"moment_of_inertia": inertia, "hoop_value": hoop, "linear_density": density, "tip_rate": tip_rate}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (a table to memorize)",
                "latex": r"I_{\text{rod}} = \tfrac13 M L^2,\quad I_{\text{disk}} = \tfrac12 M R^2,\quad I_{\text{hoop}} = M R^2",
                "prose": "The algebra-based course gives moments of inertia as a *lookup table* — a different "
                         "fraction for each shape, with no account of where the $\\tfrac13$, $\\tfrac12$, or $1$ "
                         "come from. It can use the numbers but cannot say why a rod's coefficient is $\\tfrac13$ "
                         "while a hoop's is $1$.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Moment of inertia is the integral of r² over the mass",
                "latex": r"I = \int r^2\,dm",
                "prose": "Every slice of mass $dm$ at radius $r$ contributes $r^2\\,dm$ to the moment of inertia. "
                         "The total is the integral over the whole body — and for a body whose mass is spread out, "
                         "that is the area under a curve, not a single term.",
            },
            {
                "label": "Spread the rod's mass at density $\\lambda = M/L$",
                "latex": r"dm = \lambda\,dr \ \Longrightarrow\ I = \int_0^{L} \lambda\,r^2\,dr = \tfrac13\lambda L^3 = \tfrac13 M L^2",
                "prose": "With the rod's mass spread uniformly at $\\lambda = M/L$ per metre, the integrand becomes "
                         "$\\lambda r^2$ — a parabola. The area under it from $0$ to $L$ is $\\tfrac13\\lambda L^3$, "
                         "and $\\lambda L = M$ turns that into the memorized $\\tfrac13 M L^2$. Its slope at any "
                         "radius is $\\lambda r^2$ — the rate at which the moment accumulates.",
                "emphasis": True,
            },
            {
                "label": "Why the hoop's coefficient is the special one",
                "latex": r"\text{all mass at } R \ \Longrightarrow\ I = \int R^2\,dm = M R^2",
                "prose": "If instead the mass is all at a single radius $R$ — a thin hoop — the integrand $r^2$ is "
                         "the constant $R^2$, and the integral collapses to the rectangle $M R^2$. The rod's "
                         "$\\tfrac13$ is small because most of its mass sits close to the pivot, where $r^2$ is "
                         "tiny; the hoop's $1$ is the extreme where all the mass is as far out as possible.",
            },
        ],
    }

    area = AreaPlot(
        u=r,
        f_expr=f_expr,
        g_expr=g_expr,
        u0=0.0,
        u_window=u_window,
        cursor=Slider(r, "r", 0.0, u_window, float(L_val)),
        sliders=[Slider(M, "M", 0.2, 8.0, float(M_val))],
        constants={L: L_val},               # M is the slider, r the axis; L fixed for the browser
        unit_map={M: "kg", L: "m", r: "m"},
        u_label="r  (m)",
        f_label="dI/dr  (kg·m)",
        g_label="I  (kg·m²)",
        u_unit="m",
        annot="The shaded area under dI/dr = λr² is the moment of inertia; its slope is the integrand.",
    )

    return Scenario(
        regime=2,
        constants_export={"M": float(M_val), "L": float(L_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={},
        area=area,
    )
