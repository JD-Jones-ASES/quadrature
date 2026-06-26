"""Regime-2 model: the damped harmonic oscillator — the under→critical→over transition.

The defining feature is a *qualitative* change: as damping crosses critical, the solution's functional form
changes (e^{−γt}cos → (A+Bt)e^{−γt} → e^{−γt}cosh). No single closed form spans the sweep, so the graph is
`sampled` (ADR-0012): the damping slider snaps between discrete, exact, individually parity-verified frames.

Governing proof (ADR-0013): all three forms solve m x'' + b x' + k x = 0; the initial conditions hold; and
energy *dissipates* at the rate dE/dt = −b v² (the dissipative invariant, the damped analog of conservation).
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import Frame, Marker, Scenario, Slider, make_result

t = sp.Symbol("t", nonnegative=True, real=True)
gamma = sp.Symbol("gamma", positive=True)   # decay rate γ = b/2m
wd = sp.Symbol("wd", positive=True)          # damped angular frequency √(ω₀²−γ²)
s = sp.Symbol("s", positive=True)            # overdamped rate √(γ²−ω₀²)
x0 = sp.Symbol("x0", real=True)
v0 = sp.Symbol("v0", real=True)

PROOF_DOMAIN = SampleDomain(
    bounds={gamma: (0.2, 3.0), wd: (0.5, 5.0), s: (0.2, 3.0), x0: (-2.0, 2.0), v0: (-2.0, 2.0), t: (0.1, 4.0)},
    positive={gamma, wd, s},
)

# symbolic solution forms (general)
_x_under = sp.exp(-gamma * t) * (x0 * sp.cos(wd * t) + (v0 + gamma * x0) / wd * sp.sin(wd * t))
_x_crit = (x0 + (v0 + gamma * x0) * t) * sp.exp(-gamma * t)
_x_over = sp.exp(-gamma * t) * (x0 * sp.cosh(s * t) + (v0 + gamma * x0) / s * sp.sinh(s * t))


def _prove() -> dict:
    vu = sp.diff(_x_under, t)
    checks_spec = [
        ("underdamped_solves", r"Underdamped form $e^{-\gamma t}(\cos,\sin)$ solves $x'' + 2\gamma x' + \omega_0^2 x = 0$.",
         sp.diff(_x_under, t, 2) + 2 * gamma * sp.diff(_x_under, t) + (wd**2 + gamma**2) * _x_under),
        ("critical_solves", r"Critical form $(x_0 + \dots\,t)\,e^{-\gamma t}$ solves $x'' + 2\gamma x' + \gamma^2 x = 0$ (where $\omega_0 = \gamma$).",
         sp.diff(_x_crit, t, 2) + 2 * gamma * sp.diff(_x_crit, t) + gamma**2 * _x_crit),
        ("overdamped_solves", r"Overdamped form $e^{-\gamma t}(\cosh,\sinh)$ solves $x'' + 2\gamma x' + (\gamma^2 - s^2)x = 0$.",
         sp.diff(_x_over, t, 2) + 2 * gamma * sp.diff(_x_over, t) + (gamma**2 - s**2) * _x_over),
        ("ic_position", r"It matches the initial position $x(0) = x_0$.", _x_under.subs(t, 0) - x0),
        ("ic_velocity", r"It matches the initial velocity $x'(0) = v_0$.", vu.subs(t, 0) - v0),
        ("energy_dissipates", r"Energy dissipates at exactly $\tfrac{dE}{dt} = -b v^2$ (here per unit mass, $b/m = 2\gamma$).",
         sp.diff(vu**2 / 2 + (wd**2 + gamma**2) * _x_under**2 / 2, t) + 2 * gamma * vu**2),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"damped: {key}", seed=f"damped/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    return {
        "kind": "governing",
        "heading": "All three damping regimes provably solve the equation of motion, and energy dissipates.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"back-substitute each form into $m x'' + b x' + k x = 0$; check the initial conditions; check $dE/dt = -b v^2$",
        "checks": checks,
    }


def _frame_expr(g: float, w0sq: float, x0v: float, v0v: float):
    """Numeric x(t) (t-only) for one damping value, choosing the right form; returns (x,v,a,label,zeta)."""
    disc = g * g - w0sq
    zeta = g / float(sp.sqrt(w0sq))
    G = sp.nsimplify(g)
    if disc < -1e-9:
        wdn = sp.sqrt(sp.nsimplify(w0sq) - G**2)
        x = sp.exp(-G * t) * (x0v * sp.cos(wdn * t) + (v0v + G * x0v) / wdn * sp.sin(wdn * t))
        label = f"underdamped (ζ = {zeta:.2f})"
    elif disc <= 1e-9:
        x = (x0v + (v0v + G * x0v) * t) * sp.exp(-G * t)
        label = f"critically damped (ζ = {zeta:.2f})"
    else:
        sn = sp.sqrt(G**2 - sp.nsimplify(w0sq))
        x = sp.exp(-G * t) * (x0v * sp.cosh(sn * t) + (v0v + G * x0v) / sn * sp.sinh(sn * t))
        label = f"overdamped (ζ = {zeta:.2f})"
    v = sp.diff(x, t)
    a = sp.diff(v, t)
    return x, v, a, label, zeta


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("m", "k"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: damped-shm requires parameters.{key}")
    m_val, k_val = float(p["m"]), float(p["k"])
    x0v, v0v = float(p.get("x0", 1)), float(p.get("v0", 0))
    b_values = p.get("b_values")
    if not b_values:
        raise BuildError(f"{spec.get('id')}: damped-shm requires parameters.b_values (the damping sweep)")
    w0sq = k_val / m_val
    b_crit = 2.0 * (k_val * m_val) ** 0.5
    t_window = float(p.get("t_window", 6.0))

    proof = _prove()

    frames = []
    for b in b_values:
        g = b / (2 * m_val)
        x, v, a, label, _ = _frame_expr(g, w0sq, x0v, v0v)
        frames.append(Frame(value=float(b), label=label, x_expr=x, v_expr=v, a_expr=a))

    # representative (a lightly-underdamped frame) for the static poster + the dimensional check
    g_rep = (b_values[0] / (2 * m_val))
    wd_rep = sp.sqrt(sp.nsimplify(w0sq) - sp.nsimplify(g_rep) ** 2)

    result = {
        "natural_frequency": make_result(sp.sqrt(sp.nsimplify(w0sq)), {}, "1/s", r"Natural angular frequency $\omega_0 = \sqrt{k/m}$"),
        "critical_damping": make_result(sp.nsimplify(b_crit), {}, "kg/s", r"Critical damping $b_c = 2\sqrt{km}$"),
    }

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course can't give you",
                "latex": r"\zeta = \frac{b}{2\sqrt{km}} \;:\; \zeta<1\ \text{under},\ \ \zeta=1\ \text{critical},\ \ \zeta>1\ \text{over}",
                "prose": "Algebra can name the three cases and the critical damping $b_c = 2\\sqrt{km}$, but it "
                         "cannot produce the motion — the acceleration depends on both position and velocity, so "
                         "only the differential equation has the answer.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Newton's law with a spring and a drag force",
                "latex": r"m\,x'' = -k\,x - b\,x' \;\;\Longrightarrow\;\; x'' + 2\gamma x' + \omega_0^2 x = 0",
                "prose": "Restoring force $-kx$ plus a velocity-dependent damping $-bx'$. Here $\\gamma = b/2m$ "
                         "and $\\omega_0^2 = k/m$.",
            },
            {
                "label": "The form of the solution depends on the damping",
                "latex": r"\zeta<1:\ e^{-\gamma t}\cos\omega_d t \quad \zeta=1:\ (A+Bt)e^{-\gamma t} \quad \zeta>1:\ e^{-\gamma t}\cosh st",
                "prose": "Underdamped: oscillation inside a decaying envelope, $\\omega_d = \\sqrt{\\omega_0^2 - \\gamma^2}$. "
                         "Critically damped: the fastest return without overshoot. Overdamped: a slow, "
                         "non-oscillating crawl back.",
            },
            {
                "label": "Energy leaks out",
                "latex": r"\frac{dE}{dt} = -b\,v^2 \le 0",
                "prose": "Unlike the undamped oscillator (where energy is conserved), the damping removes energy "
                         "at the rate $b v^2$ — and SymPy proves it.",
            },
            {
                "label": "The transition is the lesson",
                "latex": r"\boxed{\,\zeta = \dfrac{b}{2\sqrt{km}} = 1 \ \text{is the boundary}\,}",
                "prose": "Slide the damping through critical and watch oscillation give way to a dead-beat return. "
                         "Each stop on the slider is an exact, separately verified solution.",
                "emphasis": True,
            },
        ],
    }

    return Scenario(
        regime=2,
        t=t,
        x_expr=_x_under,
        v_expr=sp.diff(_x_under, t),
        a_expr=sp.diff(_x_under, t, 2),
        constants={gamma: sp.nsimplify(g_rep), wd: wd_rep, x0: sp.nsimplify(x0v), v0: sp.nsimplify(v0v)},
        constants_export={"m": m_val, "k": k_val, "b_critical": b_crit},
        unit_map={x0: "m", v0: "m/s", gamma: "1/s", wd: "1/s", t: "s"},
        initial_conditions={"x0": x0v, "v0": v0v},
        sliders=[],
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        t_window=t_window,
        markers=[
            Marker("x", t_window * 0.5, r"amplitude decays inside an $e^{-\gamma t}$ envelope", dy=-14, va="top", dot=False),
        ],
        labels=("x  (m)", "v  (m/s)", "a  (m/s²)"),
        window_mode="fixed",
        sampled={
            "sweep": {"name": "b", "label": "damping b", "unit": "kg/s",
                      "values": [float(b) for b in b_values], "critical": b_crit},
            "frames": frames,
        },
    )
