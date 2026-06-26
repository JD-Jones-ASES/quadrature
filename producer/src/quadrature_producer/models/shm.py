"""Regime-2 model: simple harmonic motion (a mass on a spring).

There is no algebra answer to equate — calculus is the only road in. So the proof is the *governing* kind
(ADR-0013): the closed form solves the equation of motion x'' = −ω²x, satisfies the initial conditions,
conserves energy, and the memorized period T = 2π/ω falls out of it. Closed form is JS-cheap (cos/sin), so the
graph is fully interactive (ADR-0012).
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from ..util import tex
from .base import Marker, Scenario, Slider, make_result

t = sp.Symbol("t", nonnegative=True, real=True)
x0 = sp.Symbol("x0", real=True)
v0 = sp.Symbol("v0", real=True)
omega = sp.Symbol("omega", positive=True)

PROOF_DOMAIN = SampleDomain(
    bounds={omega: (0.5, 3.0), x0: (-3.0, 3.0), v0: (-3.0, 3.0), t: (0.1, 5.0)},
    positive={omega},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("m", "k"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: shm requires parameters.{key}")
    m_val, k_val = sp.nsimplify(p["m"]), sp.nsimplify(p["k"])
    x0v, v0v = sp.nsimplify(p.get("x0", 0)), sp.nsimplify(p.get("v0", 0))
    omega_val = sp.sqrt(k_val / m_val)

    # closed form (sliders omega, x0, v0 left free)
    x_expr = x0 * sp.cos(omega * t) + (v0 / omega) * sp.sin(omega * t)
    v_expr = sp.diff(x_expr, t)
    a_expr = sp.diff(v_expr, t)

    # --- governing proof (back-substitution into the equation of motion) ---
    period_sym = 2 * sp.pi / omega
    checks_spec = [
        ("solves_eom", "The closed form solves the equation of motion x'' = −ω²x.",
         sp.diff(x_expr, t, 2) + omega**2 * x_expr),
        ("ic_position", "It matches the initial position x(0) = x₀.", x_expr.subs(t, 0) - x0),
        ("ic_velocity", "It matches the initial velocity x'(0) = v₀.", v_expr.subs(t, 0) - v0),
        ("energy_conserved", "Total energy ½v² + ½ω²x² is conserved (its time-derivative is zero).",
         sp.diff(v_expr**2 / 2 + omega**2 * x_expr**2 / 2, t)),
        ("period_falls_out", "The memorized period T = 2π/ω falls out: x(t+T) = x(t).",
         x_expr.subs(t, t + period_sym) - x_expr),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"shm/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "The closed form provably solves the equation of motion — and the memorized period falls out.",
        "checked_by": "sympy",
        "holds": True,
        "detail": "back-substitute x(t) into x'' = −ω²x; check ICs; check d/dt(energy) = 0; check periodicity",
        "checks": checks,
    }

    rsubs = {omega: omega_val, x0: x0v, v0: v0v}
    amplitude = sp.sqrt(x0**2 + (v0 / omega) ** 2)
    result = {
        "angular_frequency": make_result(omega, rsubs, "rad/s", "Angular frequency ω = √(k/m)"),
        "period": make_result(2 * sp.pi / omega, rsubs, "s", "Period T = 2π/ω"),
        "amplitude": make_result(amplitude, rsubs, "m", "Amplitude"),
        "max_speed": make_result(omega * amplitude, rsubs, "m/s", "Maximum speed (ωA)"),
    }

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (memorized, no derivation)",
                "latex": r"T = 2\pi\sqrt{\tfrac{m}{k}} \qquad v_{\max} = \omega A",
                "prose": "You are told the motion is sinusoidal and given the period to memorize — but not "
                         "*why* the motion is a cosine, or where the period comes from. Calculus is the only "
                         "road to the why.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Newton's second law with Hooke's law",
                "latex": r"m\,x'' = -k\,x \;\;\Longrightarrow\;\; x'' = -\omega^2 x,\quad \omega^2 = \tfrac{k}{m}",
                "prose": "The spring force is proportional to displacement and points back toward equilibrium. "
                         "This is the equation of motion — a differential equation, not an algebra formula.",
            },
            {
                "label": "Solve the equation of motion",
                "latex": r"x(t) = x_0\cos\omega t + \tfrac{v_0}{\omega}\sin\omega t",
                "prose": "The function whose second derivative is −ω² times itself is a sinusoid. The two "
                         "constants are fixed by the initial position and velocity.",
            },
            {
                "label": "Differentiate for velocity and acceleration",
                "latex": r"v(t) = -x_0\,\omega\sin\omega t + v_0\cos\omega t,\qquad a(t) = -\omega^2 x(t)",
                "prose": "Acceleration is always −ω² times the displacement: largest at the extremes, zero at "
                         "equilibrium. On the stacked graph, v leads x by a quarter period.",
            },
            {
                "label": "The memorized period emerges",
                "latex": r"\boxed{\,T = \dfrac{2\pi}{\omega} = 2\pi\sqrt{\dfrac{m}{k}}\,}",
                "prose": "The cosine repeats every 2π/ω — and SymPy proves x(t+T) = x(t). The result the "
                         "algebra course made you memorize is exactly the period of the solution.",
                "emphasis": True,
            },
        ],
    }

    period_num = float(sp.N(2 * sp.pi / omega_val))
    quarter, half = period_num / 4, period_num / 2

    return Scenario(
        regime=2,
        t=t,
        x_expr=x_expr,
        v_expr=v_expr,
        a_expr=a_expr,
        constants={},  # omega, x0, v0 are all sliders
        constants_export={"m": float(m_val), "k": float(k_val)},
        unit_map={x0: "m", v0: "m/s", omega: "1/s", t: "s"},
        initial_conditions={"x0": float(x0v), "v0": float(v0v)},
        sliders=[
            Slider(omega, "omega", 0.5, 5.0, float(omega_val)),
            Slider(x0, "x0", -0.6, 0.6, float(x0v)),
            Slider(v0, "v0", -1.5, 1.5, float(v0v)),
        ],
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        t_window=2 * period_num,
        markers=[
            Marker("x", quarter, "x = 0 here", dy=-14, va="top"),
            Marker("v", quarter, "v is largest where x = 0\n— a quarter-period out of phase",
                   dx=8, dy=14, ha="left", va="bottom"),
            Marker("a", half, "a = −ω²x: always toward equilibrium", dy=14, va="bottom", dot=False),
        ],
        guides=[quarter, half, period_num],
        labels=("x  (m)", "v  (m/s)", "a  (m/s²)"),
    )
