"""Regime-2 model: a 1D two-body collision — the before/after collision-bars instrument (a new graph
`kind:"collision"`, ADR-0018). Body 1 (mass $m_1$, velocity $v_1$) strikes body 2 (mass $m_2$, velocity
$v_2$); the coefficient of restitution $e\\in[0,1]$ dials the outcome from perfectly inelastic ($e=0$, the
bodies stick) to perfectly elastic ($e=1$, kinetic energy conserved).

The algebra-based course hands you two equations — conservation of momentum and (for an elastic collision)
conservation of kinetic energy — and you solve. The calculus shows *why momentum is always conserved while
kinetic energy usually isn't*: during contact the two bodies push on each other with **equal and opposite
forces at every instant** (Newton's third law), so the impulses $J=\\int F\\,dt$ are equal and opposite and
cancel — the total momentum is unchanged for *any* force profile, elastic or not. Kinetic energy is different:
the same contact force does work over each body's (different) displacement, and unless the deformation springs
all the way back, $\\tfrac12\\mu(1-e^2)(v_1-v_2)^2$ stays behind as heat — with $\\mu=m_1m_2/(m_1+m_2)$ the
reduced mass.

Solving momentum conservation $m_1v_1+m_2v_2=m_1v_1'+m_2v_2'$ together with the restitution relation
$v_2'-v_1'=e(v_1-v_2)$ gives the closed-form finals
$$v_1'=\\frac{(m_1-e\\,m_2)v_1+(1+e)m_2v_2}{m_1+m_2},\\qquad
  v_2'=\\frac{(m_2-e\\,m_1)v_2+(1+e)m_1v_1}{m_1+m_2}.$$

The pivot is the **before/after bars**: the momentum total bar is the same height before and after at every
$e$ (only the split between the two bodies shifts), while the kinetic-energy total bar equals the before value
only at $e=1$ and shrinks to its minimum at $e=0$. Proof kind `governing` (the conservation law is the
time-integral of Newton's law): momentum conserved; the finals satisfy restitution; the KE deficit is
$\\tfrac12\\mu(1-e^2)(\\Delta v)^2$; $e=1$ conserves KE; $e=0$ leaves the bodies at the common velocity
$v_{cm}$. The closed forms are JS-cheap, so the bars are interactive and parity-verified.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import CollisionPlot, Scenario, Slider, make_result

e = sp.Symbol("e", nonnegative=True, real=True)   # coefficient of restitution (the cursor), dimensionless
m1 = sp.Symbol("m1", positive=True)               # incident mass, kg (the free slider)
m2 = sp.Symbol("m2", positive=True)               # target mass, kg (constant)
v1 = sp.Symbol("v1", real=True)                   # incident velocity, m/s (constant)
v2 = sp.Symbol("v2", real=True)                   # target velocity, m/s (constant)

PROOF_DOMAIN = SampleDomain(
    bounds={m1: (0.5, 4.0), m2: (0.5, 4.0), v1: (-6.0, 6.0), v2: (-6.0, 6.0), e: (0.0, 1.0)},
    positive={m1, m2},
)


def _finals():
    """The closed-form final velocities from momentum conservation + the restitution relation."""
    M = m1 + m2
    v1f = ((m1 - e * m2) * v1 + (1 + e) * m2 * v2) / M
    v2f = ((m2 - e * m1) * v2 + (1 + e) * m1 * v1) / M
    return v1f, v2f


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("m1", "m2", "v1"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: collision requires parameters.{key}")
    m1_val, m2_val = sp.nsimplify(p["m1"]), sp.nsimplify(p["m2"])
    v1_val, v2_val = sp.nsimplify(p["v1"]), sp.nsimplify(p.get("v2", 0))

    v1f, v2f = _finals()
    mu = m1 * m2 / (m1 + m2)                                    # reduced mass
    ke_before = sp.Rational(1, 2) * m1 * v1**2 + sp.Rational(1, 2) * m2 * v2**2
    ke_after = sp.Rational(1, 2) * m1 * v1f**2 + sp.Rational(1, 2) * m2 * v2f**2
    ke_loss = sp.Rational(1, 2) * mu * (1 - e**2) * (v1 - v2)**2
    v_cm = (m1 * v1 + m2 * v2) / (m1 + m2)

    # --- proof (kind "governing"): the conservation law is the time-integral of Newton's law ---
    checks_spec = [
        ("momentum_conserved",
         r"Total momentum is unchanged for *every* $e$: $m_1v_1'+m_2v_2' = m_1v_1+m_2v_2$. The contact forces "
         r"are equal and opposite (Newton's third law), so the impulses $J=\int F\,dt$ cancel — true for any "
         r"force profile, elastic or not.",
         (m1 * v1f + m2 * v2f) - (m1 * v1 + m2 * v2)),
        ("restitution",
         r"The solved finals obey the restitution relation $v_2'-v_1' = e\,(v_1-v_2)$ — the relative speed of "
         r"separation is $e$ times the relative speed of approach.",
         (v2f - v1f) - e * (v1 - v2)),
        ("ke_loss",
         r"The kinetic energy lost is $\tfrac12\mu(1-e^2)(v_1-v_2)^2$ with reduced mass $\mu=m_1m_2/(m_1+m_2)$ "
         r"— so KE is conserved only when $e=1$, and the loss is greatest when $e=0$.",
         (ke_before - ke_after) - ke_loss),
        ("elastic_conserves_ke",
         r"At $e=1$ (perfectly elastic) the kinetic energy is unchanged: $\text{KE}_f = \text{KE}_i$.",
         (ke_after - ke_before).subs(e, 1)),
        ("inelastic_common_velocity",
         r"At $e=0$ (perfectly inelastic) the bodies move off together at the common velocity "
         r"$v_{cm}=(m_1v_1+m_2v_2)/(m_1+m_2)$.",
         (v1f - v_cm).subs(e, 0)),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"collision/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "Momentum is conserved in every collision (equal-and-opposite impulses cancel); kinetic "
                   "energy is conserved only when the collision is perfectly elastic.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $m_1v_1'+m_2v_2'=m_1v_1+m_2v_2$; check $v_2'-v_1'=e(v_1-v_2)$; check "
                  r"$\Delta\text{KE}=\tfrac12\mu(1-e^2)(\Delta v)^2$; $e=1\Rightarrow\text{KE}$ conserved; "
                  r"$e=0\Rightarrow$ common velocity $v_{cm}$",
        "checks": checks,
    }

    # --- results: the two iconic outcomes, elastic and perfectly inelastic ---
    rsubs = {m1: m1_val, m2: m2_val, v1: v1_val, v2: v2_val}
    v1e = make_result(v1f.subs(e, 1), rsubs, "m/s", r"Elastic ($e=1$): body 1 final $v_1'$")
    v1e["symbolic_latex"] = r"\frac{(m_1-m_2)v_1+2m_2v_2}{m_1+m_2}"
    v2e = make_result(v2f.subs(e, 1), rsubs, "m/s", r"Elastic ($e=1$): body 2 final $v_2'$")
    v2e["symbolic_latex"] = r"\frac{(m_2-m_1)v_2+2m_1v_1}{m_1+m_2}"
    vstick = make_result(v_cm, rsubs, "m/s", r"Inelastic ($e=0$): common velocity $v_{cm}$")
    vstick["symbolic_latex"] = r"\frac{m_1v_1+m_2v_2}{m_1+m_2}"
    keloss0 = make_result(ke_loss.subs(e, 0), rsubs, "J", r"Inelastic ($e=0$): kinetic energy lost")
    keloss0["symbolic_latex"] = r"\tfrac12\mu(v_1-v_2)^2"
    result = {"v1_elastic": v1e, "v2_elastic": v2e, "v_inelastic": vstick, "ke_lost_inelastic": keloss0}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (two conservation rules)",
                "latex": r"m_1v_1+m_2v_2 = m_1v_1'+m_2v_2' \qquad (\text{elastic:})\ \ \tfrac12 m_1v_1^2+\tfrac12 m_2v_2^2 = \tfrac12 m_1v_1'^2+\tfrac12 m_2v_2'^2",
                "prose": "Momentum is conserved in a collision, and for an *elastic* collision so is kinetic "
                         "energy — two equations, two unknown final velocities. It works, but it is handed to "
                         "you as a pair of rules, with no account of *why* momentum is always conserved while "
                         "kinetic energy usually is not.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Momentum conservation is the time-integral of Newton's third law",
                "latex": r"F_{12} = -F_{21} \ \Longrightarrow\ J_1 = \int F_{12}\,dt = -\int F_{21}\,dt = -J_2 \ \Longrightarrow\ \Delta p_1 = -\Delta p_2",
                "prose": "During contact the two bodies push on each other with equal and opposite forces at "
                         "every instant (Newton's third law). The impulse each receives is the time-integral of "
                         "that force, $J=\\int F\\,dt$ — and since the forces are equal and opposite, so are the "
                         "impulses. They cancel: $\\Delta p_1+\\Delta p_2=0$. The total momentum is unchanged no "
                         "matter how complicated the contact force is, elastic or not. This is the impulse–"
                         "momentum theorem doing the work the algebra states as a rule.",
            },
            {
                "label": "Kinetic energy is different — the lost KE is the deformation work",
                "latex": r"\text{KE}_i-\text{KE}_f = \tfrac12\,\mu\,(1-e^2)\,(v_1-v_2)^2, \qquad \mu = \frac{m_1m_2}{m_1+m_2}",
                "prose": "The same contact force does work over each body's displacement, and those "
                         "displacements differ, so the works do *not* cancel: energy goes into deforming the "
                         "bodies. If they spring all the way back ($e=1$) it is returned and kinetic energy is "
                         "conserved; otherwise the fraction $\\tfrac12\\mu(1-e^2)(\\Delta v)^2$ stays as heat. "
                         "The coefficient of restitution $e$ measures how much of the relative speed survives.",
                "emphasis": True,
            },
            {
                "label": "Watch the two totals as you sweep $e$",
                "latex": r"v_1' = \frac{(m_1-e\,m_2)v_1+(1+e)m_2v_2}{m_1+m_2}, \qquad v_2' = \frac{(m_2-e\,m_1)v_2+(1+e)m_1v_1}{m_1+m_2}",
                "prose": "Drag the restitution slider from $e=1$ down to $e=0$: the **momentum** total bar never "
                         "moves (only the split between the two bodies shifts), while the **kinetic-energy** "
                         "total bar shrinks, the gap shaded as energy lost. At $e=1$ both totals are conserved; "
                         "at $e=0$ the bodies leave at the common velocity $v_{cm}$ and the KE loss is maximal.",
            },
        ],
    }

    collision = CollisionPlot(
        u=e,
        v1f_expr=v1f,
        v2f_expr=v2f,
        cursor=Slider(e, "e", 0.0, 1.0, 1.0),
        sliders=[Slider(m1, "m1", 1.0, 4.0, float(m1_val))],
        constants={m2: m2_val, v1: v1_val, v2: v2_val},
        consts_export={"m2": float(m2_val), "v1": float(v1_val), "v2": float(v2_val)},
        unit_map={m1: "kg", m2: "kg", v1: "m/s", v2: "m/s", e: "1"},
        u_label="e  (restitution)",
        u_unit="",
        annot="Momentum is conserved at every e; kinetic energy is conserved only at e = 1.",
    )

    return Scenario(
        regime=2,
        constants_export={"m1": float(m1_val), "m2": float(m2_val),
                          "v1": float(v1_val), "v2": float(v2_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={"v1": float(v1_val), "v2": float(v2_val)},
        collision=collision,
    )
