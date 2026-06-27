"""Regime-2 model: Torricelli's law — a draining tank, on the energy-exchange bars (kind:"energy"). Opens
fluid *dynamics* (only fluid statics had shipped). A parcel of water falls from the surface to an orifice a
depth $h$ below; its gravitational potential energy converts to kinetic energy, and at the orifice it emerges
with speed $v = \\sqrt{2gh}$ — the fluid analogue of a block sliding down a frictionless ramp.

The algebra-based course states Torricelli's law (or Bernoulli) as a rule. The calculus shows it is the same
first integral of $F = ma$ that gives energy conservation: along a streamline, $\\tfrac12\\rho v^2 + \\rho g y$
is constant, so the speed depends only on the depth dropped, not the path through the tank. Per unit volume,
$\\text{KE}(d) = \\rho g\\,d$ grows while $\\text{PE}(d) = \\rho g (h - d)$ shrinks, and the Total bar
$\\rho g h$ never moves. Proof kind `governing`.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import EnergyPlot, Scenario, Slider, make_result

d = sp.Symbol("d", nonnegative=True, real=True)   # depth below the surface (the cursor), m
rho = sp.Symbol("rho", positive=True)             # fluid density, kg/m³ (slider)
g = sp.Symbol("g", positive=True)                 # gravitational field magnitude, m/s²
h = sp.Symbol("h", positive=True)                 # depth of the orifice below the surface (constant)
_w = sp.Symbol("w", nonnegative=True)

PROOF_DOMAIN = SampleDomain(
    bounds={d: (0.0, 10.0), rho: (500.0, 1500.0), g: (8.0, 11.0), h: (1.0, 20.0)},
    positive={rho, g, h},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("rho", "h"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: torricelli requires parameters.{key}")
    rho_val, h_val = sp.nsimplify(p["rho"]), sp.nsimplify(p["h"])
    g_val = sp.nsimplify(p.get("g", 10))

    ke_expr = rho * g * d                           # kinetic energy per unit volume at depth d
    pe_expr = rho * g * (h - d)                      # potential energy per unit volume
    total = rho * g * h
    v_expr = sp.sqrt(2 * g * d)                      # speed from ½ρv² = KE per volume

    checks_spec = [
        ("energy_constant",
         r"The total energy per unit volume does not change with depth: $\tfrac{d}{dd}(\text{KE}+\text{PE}) = 0$.",
         sp.diff(ke_expr + pe_expr, d)),
        ("conservation_law",
         r"Bernoulli along the streamline: $\tfrac12\rho v^2 + \rho g y = \rho g h$ is constant as the parcel falls.",
         (ke_expr + pe_expr) - total),
        ("speed_falls_out",
         r"The speed falls out of the kinetic energy: $\tfrac12\rho v^2 = \text{KE}$, so $v = \sqrt{2gd}$.",
         sp.Rational(1, 2) * rho * v_expr**2 - ke_expr),
        ("torricelli",
         r"At the orifice ($d = h$) the efflux speed is Torricelli's law $v = \sqrt{2gh}$ — the same as a body that fell freely through $h$.",
         v_expr.subs(d, h) - sp.sqrt(2 * g * h)),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"torricelli/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "Torricelli's law is energy conservation along a streamline — the efflux speed depends only "
                   "on the depth, not the shape of the tank.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{d}{dd}(\text{KE}+\text{PE})=0$; check $\tfrac12\rho v^2+\rho g y=\rho g h$; "
                  r"show $v=\sqrt{2gd}$; orifice speed $\sqrt{2gh}$",
        "checks": checks,
    }

    rsubs = {rho: rho_val, g: g_val, h: h_val}
    vexit = make_result(v_expr.subs(d, h_val), rsubs, "m/s", r"Efflux speed $v = \sqrt{2gh}$")
    vexit["symbolic_latex"] = r"\sqrt{2gh}"
    etot = make_result(total, rsubs, "Pa", r"Total energy density $\rho g h$")
    etot["symbolic_latex"] = r"\rho g h"
    ke_half = make_result(ke_expr.subs(d, h_val / 2), rsubs, "Pa", r"KE density at half depth")
    ke_half["symbolic_latex"] = r"\tfrac12 \rho g h"
    vhalf = make_result(v_expr.subs(d, h_val / 2), rsubs, "m/s", r"Speed at half depth $\sqrt{gh}$")
    vhalf["symbolic_latex"] = r"\sqrt{gh}"
    result = {"efflux_speed": vexit, "total_density": etot, "ke_at_half": ke_half, "speed_at_half": vhalf}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (Torricelli's law)",
                "latex": r"v = \sqrt{2gh}",
                "prose": "Water leaves an orifice a depth $h$ below the surface at the same speed an object would "
                         "reach falling freely through $h$. It works — but it is handed to you as a rule, with no "
                         "account of *why* the tank's shape or the water above doesn't matter.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Energy conservation along a streamline (Bernoulli) is the first integral of $F = ma$",
                "latex": r"\tfrac12\rho v^2 + \rho g y = \text{const}",
                "prose": "For a parcel of fluid following a streamline, Newton's second law integrates to the "
                         "statement that pressure, kinetic energy density, and potential energy density trade so "
                         "their sum is constant. With the surface and the orifice both at atmospheric pressure, "
                         "the kinetic energy gained equals the potential energy lost, $\\tfrac12\\rho v^2 = \\rho g h$.",
            },
            {
                "label": "The depth sets the speed — the route does not",
                "latex": r"\tfrac12\rho v^2 = \rho g h \ \Longrightarrow\ v = \sqrt{2gh}",
                "prose": "The density cancels, so the efflux speed is $\\sqrt{2gh}$ regardless of the fluid or the "
                         "shape of the tank — exactly the speed of free fall through $h$. A wide tank and a narrow "
                         "one drain at the same orifice speed for the same depth.",
                "emphasis": True,
            },
            {
                "label": "Watch the energies trade with the total fixed",
                "latex": r"\boxed{\,v(d) = \sqrt{2gd}\,}",
                "prose": "Drag the cursor down from the surface: potential energy density converts to kinetic, but "
                         "the Total bar never moves. At the orifice it is all kinetic, with speed $\\sqrt{2gh}$. The "
                         "bars are Bernoulli's equation made visible.",
            },
        ],
    }

    energy = EnergyPlot(
        u=d,
        ke_expr=ke_expr,
        pe_expr=pe_expr,
        u0=0.0,
        u_window=float(h_val),
        cursor=Slider(d, "d", 0.0, float(h_val), float(h_val) / 2),
        sliders=[Slider(rho, "rho", 600.0, 1200.0, float(rho_val))],
        constants={g: g_val, h: h_val},
        unit_map={rho: "kg/m**3", g: "m/s**2", d: "m", h: "m"},
        u_label="d  (m)",
        ke_label="KE  (J/m³)",
        pe_label="PE  (J/m³)",
        total_label="Total  (J/m³)",
        u_unit="m",
        annot="Potential energy density converts to kinetic as the parcel falls; the total stays flat — Bernoulli.",
    )

    return Scenario(
        regime=2,
        constants_export={"rho": float(rho_val), "g": float(g_val), "h": float(h_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={"d0": 0.0, "v0": 0.0},
        energy=energy,
    )
