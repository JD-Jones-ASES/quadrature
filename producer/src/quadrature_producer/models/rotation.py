"""Regime-1 model: rotational kinematics under constant angular acceleration — the temporal stack (θ/ω/α),
reused from the linear case with angular labels. The rotational equations are the integrals of a constant α,
exactly as the linear constant-acceleration formulas are the integrals of a constant a: θ = ∫ω dt, ω = ∫α dt.
The proof is `equivalence` — the memorized timeless equation ω² = ω₀² + 2αΔθ and the average-velocity relation
fall out of the integrals. Closed form is a polynomial, so the graph is interactive.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import Marker, Scenario, Slider, make_result

t = sp.Symbol("t", nonnegative=True, real=True)
theta0 = sp.Symbol("theta0", real=True)
omega0 = sp.Symbol("omega0", real=True)
alpha = sp.Symbol("alpha", real=True)

PROOF_DOMAIN = SampleDomain(
    bounds={theta0: (-2.0, 2.0), omega0: (-5.0, 10.0), alpha: (0.5, 6.0), t: (0.1, 6.0)},
    positive=set(),
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("omega0", "alpha"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: rotation requires parameters.{key}")
    th0v = sp.nsimplify(p.get("theta0", 0))
    w0v, av = sp.nsimplify(p["omega0"]), sp.nsimplify(p["alpha"])
    T = float(p.get("t", 4.0))

    theta = theta0 + omega0 * t + alpha * t**2 / 2
    omega = omega0 + alpha * t
    alpha_e = sp.diff(omega, t)

    checks_spec = [
        ("omega_is_integral", r"Angular velocity is the integral of $\alpha$: $\omega = d\theta/dt$.",
         sp.diff(theta, t) - omega),
        ("alpha_constant", r"Angular acceleration is constant: $\alpha = d\omega/dt$.",
         sp.diff(omega, t) - alpha),
        ("timeless_falls_out", r"The memorized timeless equation $\omega^2 = \omega_0^2 + 2\alpha\,\Delta\theta$ falls out.",
         omega**2 - (omega0**2 + 2 * alpha * (theta - theta0))),
        ("average_velocity", r"The average-velocity relation $\Delta\theta = \tfrac12(\omega_0+\omega)\,t$ holds.",
         (theta - theta0) - (omega0 + omega) / 2 * t),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"rotation/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "equivalence",
        "heading": "The rotational equations are the linear ones with angular symbols — and the timeless equation falls out of the integrals.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\theta' = \omega$ and $\omega' = \alpha$; show $\omega^2 = \omega_0^2 + 2\alpha\Delta\theta$ and $\Delta\theta = \tfrac12(\omega_0+\omega)t$ fall out",
        "checks": checks,
    }

    rsubs = {theta0: th0v, omega0: w0v, alpha: av, t: sp.nsimplify(T)}
    theta_T = make_result(theta, rsubs, "rad", r"Angle turned $\theta(T)$")
    omega_T = make_result(omega, rsubs, "rad/s", r"Final angular velocity $\omega(T)$")
    revs = make_result(theta / (2 * sp.pi), rsubs, "rev", r"Revolutions $\theta/2\pi$")
    result = {"angle": theta_T, "final_omega": omega_T, "revolutions": revs}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (the same four equations, angular)",
                "latex": r"\omega = \omega_0 + \alpha t,\quad \theta = \theta_0 + \omega_0 t + \tfrac12\alpha t^2,\quad \omega^2 = \omega_0^2 + 2\alpha\Delta\theta",
                "prose": "The rotational kinematics formulas are the straight-line ones with every symbol "
                         "swapped for its angular twin: $x\\to\\theta$, $v\\to\\omega$, $a\\to\\alpha$. They are "
                         "memorized as a separate set — but they are the same calculus.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Constant angular acceleration",
                "latex": r"\alpha = \text{const} \quad\Longrightarrow\quad \omega(t) = \omega_0 + \int_0^t \alpha\,dt' = \omega_0 + \alpha t",
                "prose": "A constant net torque gives a constant angular acceleration. Integrate it once for "
                         "the angular velocity — exactly as constant linear acceleration integrates to $v$.",
            },
            {
                "label": "Integrate again for the angle",
                "latex": r"\theta(t) = \theta_0 + \int_0^t \omega\,dt' = \theta_0 + \omega_0 t + \tfrac12\alpha t^2",
                "prose": "Integrate the angular velocity for the angle. This is the rotational $x = x_0 + v_0 t "
                         "+ \\tfrac12 a t^2$ — the area under the $\\omega$–$t$ line is the angle turned.",
            },
            {
                "label": "The timeless equation falls out",
                "latex": r"\boxed{\,\omega^2 = \omega_0^2 + 2\alpha\,\Delta\theta\,}",
                "prose": "Eliminate $t$ between the two integrals and the memorized timeless equation appears — "
                         "and SymPy proves it. Nothing about rotation is new; it is constant-acceleration "
                         "kinematics with angular labels.",
                "emphasis": True,
            },
        ],
    }

    th0_f, w0_f, a_f = float(th0v), float(w0v), float(av)
    wT = w0_f + a_f * T
    return Scenario(
        regime=1,
        t=t,
        x_expr=theta,
        v_expr=omega,
        a_expr=alpha_e,
        constants={theta0: th0v},
        constants_export={"theta0": th0_f, "omega0": w0_f, "alpha": a_f},
        unit_map={theta0: "rad", omega0: "rad/s", alpha: "rad/s**2", t: "s"},
        initial_conditions={"theta0": th0_f, "omega0": w0_f},
        sliders=[Slider(omega0, "omega0", -5.0, 10.0, w0_f), Slider(alpha, "alpha", 0.5, 6.0, a_f)],
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        t_window=T,
        markers=[
            Marker("v", T * 0.55, "slope of ω–t is α (constant)", dy=-14, va="top", dot=False),
            Marker("a", T * 0.5, f"α = {a_f:g} rad/s² — constant", dy=12, va="bottom", dot=False),
        ],
        labels=("θ  (rad)", "ω  (rad/s)", "α  (rad/s²)"),
        window_mode="fixed",
    )
