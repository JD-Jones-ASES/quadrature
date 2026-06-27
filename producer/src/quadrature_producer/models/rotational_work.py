"""Regime-2 model: the rotational work–energy theorem under a varying torque — the area instrument (ADR-0014)
on the **angle** axis. The rotational mirror of `work_energy.py` (∫F dx → ½mv²), built with NO engine change.

There is no temporal stack. The pivot is the **torque–angle** graph: the shaded AREA under $\\tau(\\theta)$
from $0$ to $\\theta$ is the rotational work $W(\\theta) = \\int\\tau\\,d\\theta$, whose SLOPE is $\\tau(\\theta)$,
and which EQUALS the rotational kinetic energy gained — the memorized $\\tfrac12 I\\omega^2$ falls out of the
integral, exactly as $\\tfrac12 mv^2$ does in the linear case. The torque $\\tau(\\theta) = c\\theta$ grows with
angle (a torsion drive engaging a flywheel from rest), so the area is a triangle. The regime-1 "quadrature"
echo: a *constant* drive torque $\\tau_0$ (a steady motor) collapses the integral to the rectangle
$W = \\tau_0\\,\\Delta\\theta$.

Proof kind is "integral": $W'(\\theta) = \\tau(\\theta)$; $W = \\int_0^\\theta \\tau\\,d\\theta'$;
$\\tfrac12 I\\omega^2 = W$; and $\\int_0^{\\Delta\\theta}\\tau_0\\,d\\theta = \\tau_0\\,\\Delta\\theta$ for a constant
torque. The torque is a JS-cheap polynomial, so the graph is interactive (ADR-0012): a cursor sweeps the angle
and the shaded area (= work = ΔKE_rot) grows with it.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import AreaPlot, Scenario, Slider, make_result

theta = sp.Symbol("theta", nonnegative=True, real=True)  # angle turned (the integration axis), rad
c = sp.Symbol("c", positive=True)                        # torque per radian (the drive's stiffness), N·m/rad
I = sp.Symbol("I", positive=True)                        # moment of inertia, kg·m²
_tau0 = sp.Symbol("tau0", positive=True)                 # fresh symbols for the constant-torque echo
_dth = sp.Symbol("dth", positive=True)
_w = sp.Symbol("w", nonnegative=True)                    # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={theta: (0.1, 3.0), c: (1.0, 20.0), I: (0.1, 5.0), _tau0: (0.5, 30.0), _dth: (0.1, 6.0)},
    positive={c, I, _tau0, _dth},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("I", "c", "theta"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: rotational-work requires parameters.{key}")
    I_val, c_val, th_val = sp.nsimplify(p["I"]), sp.nsimplify(p["c"]), sp.nsimplify(p["theta"])
    u_window = float(p.get("theta_window", float(th_val) * 1.35))

    # --- the integrand and its accumulated integral (torque law τ(θ) = c·θ) ---
    f_expr = c * theta                              # τ(θ)
    g_expr = sp.integrate(c * _w, (_w, 0, theta))   # W(θ) = ∫₀^θ c·θ' dθ' = ½ c θ²
    omega_expr = sp.sqrt(2 * g_expr / I)            # ω(θ) from ½Iω² = W  →  √(c/I)·θ

    # --- proof (kind "integral") ---
    checks_spec = [
        ("ftc_slope",
         r"The work's slope is the torque: $W'(\theta) = \tau(\theta)$ — the area's rate of growth is the curve's height.",
         sp.diff(g_expr, theta) - f_expr),
        ("area_is_integral",
         r"The accumulated work is exactly the area: $W(\theta) = \int_0^\theta \tau\,d\theta'$.",
         g_expr - sp.integrate(f_expr.subs(theta, _w), (_w, 0, theta))),
        ("rotational_work_energy",
         r"The rotational kinetic energy equals the work: $\tfrac12 I\omega^2 = W$ — the memorized $\tfrac12 I\omega^2$ is the area.",
         sp.Rational(1, 2) * I * omega_expr**2 - g_expr),
        ("constant_torque_echo",
         r"For a constant torque the integral collapses to $W = \tau_0\,\Delta\theta$ — the area is a rectangle (the quadrature).",
         sp.integrate(_tau0, (_w, 0, _dth)) - _tau0 * _dth),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"rotational-work/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "integral",
        "heading": "The rotational work is the area under the torque–angle curve — and ½Iω² falls out of the integral.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\tfrac{d}{d\theta}W = \tau$; check $W = \int_0^\theta \tau\,d\theta'$; back-substitute into $\tfrac12 I\omega^2 = W$; collapse the constant-torque case to $\tau_0\,\Delta\theta$",
        "checks": checks,
    }

    # --- results at the worked angle θ ---
    rsubs = {c: c_val, I: I_val, theta: th_val}
    work = make_result(g_expr, rsubs, "J", r"Rotational work $W = \tfrac12 c\,\theta^2$ (the shaded area)")
    work["symbolic_latex"] = r"\tfrac12 c\,\theta^2"
    ke = make_result(sp.Rational(1, 2) * I * omega_expr**2, rsubs, "J", r"Rotational kinetic energy $\tfrac12 I\omega^2$")
    ke["symbolic_latex"] = r"\tfrac12 I\omega^2"
    omega = make_result(omega_expr, rsubs, "rad/s", r"Final angular speed $\omega = \sqrt{c/I}\,\theta$")
    omega["symbolic_latex"] = r"\sqrt{c/I}\,\theta"
    tmax = make_result(f_expr, rsubs, "N·m", r"Maximum torque $\tau_{\max} = c\,\theta$")
    tmax["symbolic_latex"] = r"c\,\theta"
    result = {"work_done": work, "rotational_ke": ke, "final_omega": omega, "max_torque": tmax}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you",
                "latex": r"W = \bar\tau\,\Delta\theta \qquad \tfrac12 I\omega^2 = W \quad(\bar\tau = \tfrac12\tau_{\max},\ \text{the average torque})",
                "prose": "For a constant torque, rotational work is torque times the angle turned, and it equals "
                         "the rotational kinetic energy $\\tfrac12 I\\omega^2$. When the torque *varies*, the algebra "
                         "course patches it with an average torque — which is only exact here because the torque "
                         "happens to rise linearly. It can compute the number but cannot say *why* the answer is an "
                         "area.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Rotational work is the area under the torque–angle curve",
                "latex": r"W = \int \tau\,d\theta",
                "prose": "Rotational work is the integral of torque over the angle turned — the rotational twin of "
                         "$\\int F\\,dx$. For a constant torque this integral is a rectangle (and gives "
                         "$W = \\tau\\,\\Delta\\theta$); for any torque it is the area under the $\\tau$–$\\theta$ "
                         "curve.",
            },
            {
                "label": "Evaluate for the linear torque $\\tau(\\theta) = c\\,\\theta$",
                "latex": r"W = \int_0^{\theta} c\,\theta'\,d\theta' = \tfrac12 c\,\theta^2",
                "prose": "The area under a straight line from the origin is a triangle: "
                         "$\\tfrac12\\,(\\text{base})\\,(\\text{height}) = \\tfrac12\\,\\theta\\,(c\\theta) = "
                         "\\tfrac12 c\\theta^2$. Its slope is $c\\theta = \\tau(\\theta)$ — the torque is the rate at "
                         "which rotational work accumulates.",
            },
            {
                "label": "The rotational kinetic energy falls out of the same integral",
                "latex": r"\int \tau\,d\theta = \int I\,\frac{d\omega}{dt}\,d\theta = \int I\,\omega\,d\omega = \tfrac12 I\omega^2 \ \Longrightarrow\ \tfrac12 I\omega^2 = W",
                "prose": "Substituting $\\tau = I\\,d\\omega/dt$ and $d\\theta = \\omega\\,dt$ turns the work integral "
                         "into $\\int I\\omega\\,d\\omega$. The memorized $\\tfrac12 I\\omega^2$ is not a separate "
                         "fact — it is exactly the accumulated rotational work, the perfect mirror of "
                         "$\\tfrac12 mv^2 = \\int F\\,dx$. The area under the torque curve IS the rotational kinetic "
                         "energy.",
                "emphasis": True,
            },
            {
                "label": "So the spin rate follows from the area",
                "latex": r"\boxed{\,\omega(\theta) = \sqrt{\tfrac{2W}{I}} = \sqrt{\tfrac{c}{I}}\;\theta\,}",
                "prose": "Read the work off the area, set it equal to $\\tfrac12 I\\omega^2$, and the angular speed at "
                         "any angle follows. Drag the cursor: the shaded area and the rotational kinetic energy move "
                         "together because they are the same quantity. A heavier flywheel (larger $I$) reaches the "
                         "same area at a lower speed.",
            },
        ],
    }

    area = AreaPlot(
        u=theta,
        f_expr=f_expr,
        g_expr=g_expr,
        u0=0.0,
        u_window=u_window,
        cursor=Slider(theta, "theta", 0.0, u_window, float(th_val)),
        sliders=[Slider(c, "c", 2.0, 16.0, float(c_val))],
        constants={},                       # c is a slider; θ is the axis; I is only in the ω result
        unit_map={c: "N*m", theta: "rad"},
        u_label="θ  (rad)",
        f_label="τ  (N·m)",
        g_label="W  (J)",
        u_unit="rad",
        annot="The shaded area under τ(θ) is the rotational work; the slope of W(θ) is the torque.",
    )

    return Scenario(
        regime=2,
        constants_export={"I": float(I_val), "c": float(c_val), "theta": float(th_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={"theta0": 0.0, "omega0": 0.0},
        area=area,
    )
