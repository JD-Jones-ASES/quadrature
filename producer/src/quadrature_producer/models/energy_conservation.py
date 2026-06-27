"""Regime-2 model: conservation of energy on a frictionless ramp — the energy-exchange instrument (a new
graph `kind:"energy"`). An object released from rest at height H slides down a frictionless track; its
kinetic and potential energies trade as it descends, but their sum is constant.

The algebra-based course states energy conservation as a rule ($\\tfrac12 mv^2 + mgh = E$) and uses it. The
calculus shows *why* it holds and *why the speed is path-independent*: energy conservation is the **first
integral of Newton's second law**. Writing $m\\,dv/dt = F$ and multiplying by $dx$ gives $mv\\,dv = F\\,dx$,
which integrates to $\\tfrac12 mv^2 = \\int F\\,dx = -\\Delta(\\text{PE})$ for a conservative force — so the
kinetic energy gained is exactly the work done by gravity, $mg(H-h)$, no matter what shape the ramp is. The
speed at any height depends only on the height dropped, not the route.

The pivot is the **KE/PE bars**: as the cursor (height $h$) falls, $\\text{KE}(h)=mg(H-h)$ grows while
$\\text{PE}(h)=mgh$ shrinks, and the Total bar $\\text{KE}+\\text{PE}=mgH$ never moves. Proof kind `governing`
(the conserved energy is the first integral of the equation of motion): $\\tfrac{d}{dh}(\\text{KE}+\\text{PE})=0$;
$\\text{KE}+\\text{PE}=mgH$; the speed $v=\\sqrt{2g(H-h)}$ falls out; and $\\text{KE}=\\int_h^H mg\\,dh'$ (the work
integral). The closed forms are JS-cheap, so the bars are interactive and parity-verified.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import EnergyPlot, Scenario, Slider, make_result

h = sp.Symbol("h", nonnegative=True, real=True)   # height above the bottom (the cursor axis)
m = sp.Symbol("m", positive=True)                 # mass, kg (the free slider — scales the energies)
g = sp.Symbol("g", positive=True)                 # gravitational field magnitude, m/s² (constant)
H = sp.Symbol("H", positive=True)                 # release height (constant; symbolic for the dimensional check)
_w = sp.Symbol("w", nonnegative=True)             # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={h: (0.0, 20.0), m: (0.5, 5.0), g: (8.0, 11.0), H: (5.0, 30.0)},
    positive={m, g, H},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("m", "H"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: energy-conservation requires parameters.{key}")
    m_val, H_val = sp.nsimplify(p["m"]), sp.nsimplify(p["H"])
    g_val = sp.nsimplify(p.get("g", 10))

    ke_expr = m * g * (H - h)                        # kinetic energy at height h (= work done falling from H)
    pe_expr = m * g * h                             # potential energy at height h
    total = m * g * H                               # constant total energy
    v_expr = sp.sqrt(2 * g * (H - h))               # speed from ½mv² = KE  →  path-independent

    # --- proof (kind "governing"): energy conservation is the first integral of the equation of motion ---
    checks_spec = [
        ("energy_constant",
         r"The total energy does not change with height: $\tfrac{d}{dh}(\text{KE}+\text{PE}) = 0$.",
         sp.diff(ke_expr + pe_expr, h)),
        ("conservation_law",
         r"The memorized law holds at every height: $\tfrac12 mv^2 + mgh = mgH$ (the energy is conserved).",
         (ke_expr + pe_expr) - total),
        ("speed_falls_out",
         r"The speed falls out of the kinetic energy: $\tfrac12 mv^2 = \text{KE}$, so $v = \sqrt{2g(H-h)}$.",
         sp.Rational(1, 2) * m * v_expr**2 - ke_expr),
        ("work_energy_root",
         r"The kinetic energy is exactly the work gravity does over the descent: $\text{KE} = \int_h^H mg\,dh'$ — the first integral of $F=ma$, independent of the path.",
         ke_expr - sp.integrate(m * g, (_w, h, H))),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"energy-conservation/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "Energy conservation is the first integral of Newton's second law — and the speed depends only on the height, not the path.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{d}{dh}(\text{KE}+\text{PE})=0$; check $\tfrac12 mv^2+mgh=mgH$; show $v=\sqrt{2g(H-h)}$ falls out; check $\text{KE}=\int_h^H mg\,dh'$ (path-independent)",
        "checks": checks,
    }

    # --- results ---
    rsubs = {m: m_val, g: g_val, H: H_val}
    etot = make_result(total, rsubs, "J", r"Total energy $E = mgH$ (conserved)")
    etot["symbolic_latex"] = r"mgH"
    vbot = make_result(v_expr.subs(h, 0), rsubs, "m/s", r"Speed at the bottom $v = \sqrt{2gH}$")
    vbot["symbolic_latex"] = r"\sqrt{2gH}"
    ke_half = make_result(ke_expr.subs(h, H_val / 2), rsubs, "J", r"KE at half height $= \tfrac12 mgH$")
    ke_half["symbolic_latex"] = r"\tfrac12 mgH"
    pe_top = make_result(pe_expr.subs(h, H_val), rsubs, "J", r"PE at the top $= mgH$ (all potential)")
    pe_top["symbolic_latex"] = r"mgH"
    result = {"total_energy": etot, "bottom_speed": vbot, "ke_at_half": ke_half, "pe_at_top": pe_top}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (a conservation rule)",
                "latex": r"\tfrac12 mv^2 + mgh = E \ \Longrightarrow\ v = \sqrt{2g(H-h)}",
                "prose": "The algebra course states that mechanical energy is conserved and lets you solve for the "
                         "speed at any height. It works — but it is handed to you as a rule, with no account of "
                         "*why* energy is conserved, or why the speed at the bottom does not depend on the shape "
                         "of the ramp.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Energy conservation is the first integral of $F = ma$",
                "latex": r"m\,\frac{dv}{dt} = F \ \Longrightarrow\ m\,v\,dv = F\,dx \ \Longrightarrow\ \tfrac12 mv^2 = \int F\,dx",
                "prose": "Start from Newton's second law and multiply by $dx$: since $dv/dt\\cdot dx = v\\,dv$, the "
                         "equation becomes $mv\\,dv = F\\,dx$. Integrating once gives $\\tfrac12 mv^2 = \\int F\\,dx$ — "
                         "the kinetic energy is the work done by the force. Energy is not a separate principle; it "
                         "is the equation of motion, integrated.",
            },
            {
                "label": "For gravity the work is $mg(H-h)$ — and it is path-independent",
                "latex": r"\int_h^H mg\,dh' = mg(H-h) = \text{KE} \ \Longrightarrow\ \tfrac12 mv^2 + mgh = mgH",
                "prose": "Gravity is a conservative force, so the work it does depends only on the change in height, "
                         "not the route: $\\int mg\\,dh' = mg(H-h)$. That is the kinetic energy gained, so "
                         "$\\tfrac12 mv^2 + mgh$ is constant. A steep ramp and a gentle ramp to the same depth give "
                         "the *same speed* — only the time differs.",
                "emphasis": True,
            },
            {
                "label": "Watch the energies trade with the total fixed",
                "latex": r"\boxed{\,v(h) = \sqrt{2g(H-h)}\,}",
                "prose": "Drag the cursor: potential energy converts to kinetic and back, but the Total bar never "
                         "moves. At the top it is all potential; at the bottom all kinetic, with speed "
                         "$\\sqrt{2gH}$. The bars are the conservation law made visible.",
            },
        ],
    }

    energy = EnergyPlot(
        u=h,
        ke_expr=ke_expr,
        pe_expr=pe_expr,
        u0=0.0,
        u_window=float(H_val),
        cursor=Slider(h, "h", 0.0, float(H_val), float(H_val) / 2),
        sliders=[Slider(m, "m", 1.0, 5.0, float(m_val))],
        constants={g: g_val, H: H_val},
        unit_map={m: "kg", g: "m/s**2", h: "m", H: "m"},
        u_label="h  (m)",
        ke_label="KE  (J)",
        pe_label="PE  (J)",
        total_label="Total  (J)",
        u_unit="m",
        annot="KE and PE trade as the object descends; the total stays flat — energy is conserved.",
    )

    return Scenario(
        regime=2,
        constants_export={"m": float(m_val), "g": float(g_val), "H": float(H_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={"h0": float(H_val), "v0": 0.0},
        energy=energy,
    )
