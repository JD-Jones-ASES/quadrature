"""Orbital motion — the trajectory instrument (ADR-0015) on a **centred** frame (a central body, a closed
looping path), reusing the trajectory machinery with `frame_mode="orbit"`. Dispatches on the spec:

* **Circular orbit (regime 1).** An exact parametric circle $x=R\\cos\\omega t$, $y=R\\sin\\omega t$ with
  $\\omega=\\sqrt{\\mu/R^3}$. Gravity $\\mu/R^2$ is exactly the centripetal pull a circle needs, so the satellite
  falls *around*, not into, the body. The algebra-based course already does circular orbits (centripetal
  balance gives $v=\\sqrt{\\mu/R}$, $T=2\\pi\\sqrt{R^3/\\mu}$), so the registers agree — proof `equivalence`. The
  closed form is JS-cheap, so the graph is `interactive` (drag the radius; speed $\\propto 1/\\sqrt R$, period
  $\\propto R^{3/2}$ — Kepler's third law, parity-verified).

* **Elliptical orbit (regime 2).** The *general* orbit has no elementary time-parameterisation (Kepler's
  equation is transcendental), so the path is numerically integrated (RK4) from the central-force law
  $\\ddot{\\mathbf r}=-\\mu\\mathbf r/|\\mathbf r|^3$ and shipped as `frames` the slider snaps between — sweeping
  the **eccentricity** at a *fixed semi-major axis* $a$, so every orbit has the *same period*
  $T=2\\pi\\sqrt{a^3/\\mu}$ (Kepler's third law depends on $a$ alone, not the shape). The producer refuses to emit
  unless the path **conserves energy** $\\tfrac12 v^2-\\mu/r$ and **angular momentum** $x\\dot y-y\\dot x$ (Kepler's
  second law — equal areas in equal times) and **closes** after one period; $e=0$ recovers the circle. Proof
  `governing`; a `check-trajectory.mjs` branch (on `frame=="orbit"`) re-checks the committed points in CI.
"""

from __future__ import annotations

import math

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from ..util import display as _disp
from .base import Scenario, Slider, TrajFrame, TrajectoryPlot, TrajMarker, make_result

t = sp.Symbol("t", nonnegative=True, real=True)   # time (the path parameter)
mu = sp.Symbol("mu", positive=True)               # standard gravitational parameter μ = GM (m³/s²)
R = sp.Symbol("R", positive=True)                 # orbital radius (the free slider, circular case)

PROOF_DOMAIN = SampleDomain(
    bounds={t: (10.0, 5000.0), mu: (1.0e13, 5.0e14), R: (6.5e6, 4.5e7)},
    positive={mu, R},
)


# ===================== circular orbit (regime 1, exact closed form) =====================

def _circular(spec: dict, mu_val, R_val) -> Scenario:
    p = spec.get("parameters", {})
    R_min = float(p.get("R_min", float(R_val)))
    R_max = float(p.get("R_max", float(R_val) * 6))

    omega = sp.sqrt(mu / R**3)                        # angular rate ω = √(μ/R³)
    x_expr = R * sp.cos(omega * t)
    y_expr = R * sp.sin(omega * t)
    vx, vy = sp.diff(x_expr, t), sp.diff(y_expr, t)
    speed_sq = sp.simplify(vx**2 + vy**2)            # = μ/R  (so v = √(μ/R))
    period = 2 * sp.pi / omega                        # T = 2π√(R³/μ)

    checks_spec = [
        ("is_circle",
         r"The path is a circle of radius $R$: $x^2+y^2 = R^2$ (the distance to the centre never changes).",
         x_expr**2 + y_expr**2 - R**2),
        ("solves_eom_x",
         r"It solves the inverse-square equation of motion: with $r=R$, $\ddot x = -\mu x/R^3$ (gravity points inward and is the centripetal pull).",
         sp.diff(x_expr, t, 2) + mu * x_expr / R**3),
        ("solves_eom_y",
         r"And the same vertically: $\ddot y = -\mu y/R^3$.",
         sp.diff(y_expr, t, 2) + mu * y_expr / R**3),
        ("orbital_speed",
         r"The orbital speed falls out: $\dot x^2+\dot y^2 = \mu/R$, so $v = \sqrt{\mu/R}$ — the memorized circular-orbit speed.",
         speed_sq - mu / R),
        ("kepler_third",
         r"Kepler's third law falls out of the period: $T^2 = 4\pi^2 R^3/\mu$.",
         period**2 - 4 * sp.pi**2 * R**3 / mu),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"orbit/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "equivalence",
        "heading": "The circular orbit solves the inverse-square law — and the memorized speed and Kepler's third law fall out, proven not asserted.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $x^2+y^2=R^2$; check $\ddot{\mathbf r} = -\mu\,\mathbf r/R^3$; show $v=\sqrt{\mu/R}$ and $T^2=4\pi^2R^3/\mu$ fall out",
        "checks": checks,
    }

    v_expr = sp.sqrt(mu / R)
    rsubs = {mu: mu_val, R: R_val}
    speed = make_result(v_expr, rsubs, "m/s", r"Orbital speed $v = \sqrt{\mu/R}$")
    speed["symbolic_latex"] = r"\sqrt{\mu/R}"
    per = make_result(period, rsubs, "s", r"Orbital period $T = 2\pi\sqrt{R^3/\mu}$")
    per["symbolic_latex"] = r"2\pi\sqrt{R^3/\mu}"
    g_at = make_result(mu / R**2, rsubs, "m/s**2", r"Gravity at the orbit $g = \mu/R^2$ (the centripetal pull)")
    g_at["symbolic_latex"] = r"\mu/R^2"
    omega_r = make_result(omega, rsubs, "1/s", r"Angular rate $\omega = \sqrt{\mu/R^3}$")
    omega_r["symbolic_latex"] = r"\sqrt{\mu/R^3}"
    result = {"orbital_speed": speed, "period": per, "gravity_at_orbit": g_at, "angular_rate": omega_r}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (centripetal balance)",
                "latex": r"\frac{GMm}{R^2} = \frac{mv^2}{R} \ \Longrightarrow\ v = \sqrt{\frac{GM}{R}},\quad T = 2\pi\sqrt{\frac{R^3}{GM}}",
                "prose": "For a *circular* orbit the algebra course is enough: set gravity equal to the centripetal "
                         "force, cancel the satellite's mass $m$, and the orbital speed and period drop out. It "
                         "gives the right numbers — but treats 'circular' as an assumption, with no account of why "
                         "the orbit is a circle (or, in general, an ellipse).",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Gravity is a central force — the orbit solves a vector ODE",
                "latex": r"m\,\ddot{\mathbf r} = -\frac{GMm}{r^2}\,\hat{\mathbf r} \ \Longrightarrow\ \ddot{\mathbf r} = -\frac{\mu}{r^3}\,\mathbf r",
                "prose": "Newton's second law with the inverse-square force is a second-order differential "
                         "equation for the position. The satellite's mass cancels, leaving the path governed by "
                         "$\\mu = GM$ alone. The orbit is whatever curve solves this equation.",
            },
            {
                "label": "The circle is the constant-radius solution",
                "latex": r"\mathbf r(t) = \big(R\cos\omega t,\ R\sin\omega t\big),\quad \omega = \sqrt{\mu/R^3}",
                "prose": "Try a circle of radius $R$ swept at a constant rate $\\omega$. Differentiating twice gives "
                         "$\\ddot{\\mathbf r} = -\\omega^2\\mathbf r$, and on the circle $r=R$ the force law needs "
                         "$\\omega^2 = \\mu/R^3$ — so the circle solves the equation exactly. The inward gravity "
                         "$\\mu/R^2$ is precisely the centripetal acceleration $\\omega^2 R = v^2/R$: the satellite "
                         "is in continuous free fall, falling *around* the body, not into it.",
                "emphasis": True,
            },
            {
                "label": "The memorized formulas — and Kepler's third law — fall out",
                "latex": r"\boxed{\,v = \sqrt{\tfrac{\mu}{R}},\qquad T = \frac{2\pi}{\omega} = 2\pi\sqrt{\tfrac{R^3}{\mu}}\ \Longrightarrow\ T^2 = \frac{4\pi^2}{\mu}R^3\,}",
                "prose": "The speed is $|\\dot{\\mathbf r}| = \\omega R = \\sqrt{\\mu/R}$ and the period is one turn, "
                         "$2\\pi/\\omega$. Squaring gives $T^2 \\propto R^3$ — Kepler's third law, which the algebra "
                         "course states but cannot derive. Drag the radius: the orbit widens, the speed drops as "
                         "$1/\\sqrt R$, and the period stretches as $R^{3/2}$.",
            },
        ],
    }

    mu_f, R_f = float(mu_val), float(R_val)
    omega_f = math.sqrt(mu_f / R_f**3)
    period_f = 2 * math.pi / omega_f
    v_f = math.sqrt(mu_f / R_f)

    traj = TrajectoryPlot(
        t=t,
        t_flight=period_f,
        constants={mu: mu_val},
        unit_map={mu: "m**3/s**2", R: "m", t: "s"},
        x_expr=x_expr,
        y_expr=y_expr,
        sliders=[Slider(R, "R", R_min, R_max, R_f)],
        markers=[
            TrajMarker(R_f, 0.0, f"R = {R_f/1e6:.2f}×10⁶ m", dy=-12, va="bottom"),
            TrajMarker(0.0, 0.0, "central body", dy=16, va="top", dot=True),
        ],
        x_label="x  (m)",
        y_label="y  (m)",
        frame_mode="orbit",
        mu=mu_f,
    )

    return Scenario(
        regime=1,
        constants_export={"mu": mu_f, "R": R_f, "v": v_f, "T": period_f},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={"x0": R_f, "y0": 0.0},
        trajectory=traj,
    )


# ===================== elliptical orbit (regime 2, numerical RK4) =====================

def _orbit_rhs(s, mu_f):
    """State derivative for the inverse-square central force: a = −μ r/|r|³."""
    x, y, vx, vy = s
    r3 = (x * x + y * y) ** 1.5
    return [vx, vy, -mu_f * x / r3, -mu_f * y / r3]


def _integrate_orbit(mu_f, x0, y0, vx0, vy0, T, n):
    """Fixed-step RK4 of the planar two-body motion for one period T (n steps). Deterministic."""
    s = [x0, y0, vx0, vy0]
    out = [(0.0, x0, y0, vx0, vy0)]
    h = T / n
    tt = 0.0
    for _ in range(n):
        k1 = _orbit_rhs(s, mu_f)
        k2 = _orbit_rhs([s[i] + 0.5 * h * k1[i] for i in range(4)], mu_f)
        k3 = _orbit_rhs([s[i] + 0.5 * h * k2[i] for i in range(4)], mu_f)
        k4 = _orbit_rhs([s[i] + h * k3[i] for i in range(4)], mu_f)
        s = [s[i] + (h / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) for i in range(4)]
        tt += h
        out.append((tt, s[0], s[1], s[2], s[3]))
    return out


def _verify_orbit(traj, mu_f, a_f, ctx, e):
    """Refuse to emit unless the integrated orbit conserves energy and angular momentum, closes after one
    period, and (the specific energy) matches the vis-viva value −μ/2a. Returns (E-dev, L-dev, closure)."""
    x0, y0, vx0, vy0 = traj[0][1:]
    E0 = 0.5 * (vx0 * vx0 + vy0 * vy0) - mu_f / math.hypot(x0, y0)
    L0 = x0 * vy0 - y0 * vx0
    eE = eL = 0.0
    for (_tt, x, y, vx, vy) in traj:
        r = math.hypot(x, y)
        E = 0.5 * (vx * vx + vy * vy) - mu_f / r
        L = x * vy - y * vx
        eE = max(eE, abs(E - E0) / abs(E0))
        eL = max(eL, abs(L - L0) / abs(L0))
    if eE > 1e-4:
        raise BuildError(f"{ctx}: energy not conserved on the orbit (rel dev {eE:.2e} at e={e})")
    if eL > 1e-4:
        raise BuildError(f"{ctx}: angular momentum not conserved (rel dev {eL:.2e} at e={e})")
    closure = math.hypot(traj[-1][1] - x0, traj[-1][2] - y0) / a_f
    if closure > 1e-2:
        raise BuildError(f"{ctx}: orbit does not close after one period (gap {closure:.2e}·a at e={e})")
    if abs(E0 - (-mu_f / (2 * a_f))) / (mu_f / (2 * a_f)) > 1e-3:
        raise BuildError(f"{ctx}: specific energy ≠ −μ/2a (vis-viva) at e={e}")
    return eE, eL, closure


def _subsample(traj, n):
    if len(traj) <= n:
        return traj
    idx = [round(i * (len(traj) - 1) / (n - 1)) for i in range(n)]
    return [traj[i] for i in sorted(set(idx))]


def _elliptical(spec: dict, mu_val, a_val, ecc_list) -> Scenario:
    mu_f, a_f = float(mu_val), float(a_val)
    if not ecc_list:
        raise BuildError(f"{spec.get('id')}: elliptical orbit requires parameters.eccentricities")
    period_f = 2 * math.pi * math.sqrt(a_f**3 / mu_f)          # same for every e (Kepler III: depends on a only)
    n_steps = int(spec.get("parameters", {}).get("steps", 8000))
    ctx = spec.get("id", "orbit")

    frames, full = [], {}
    max_eE = max_eL = max_gap = 0.0
    for e in ecc_list:
        e = float(e)
        rp = a_f * (1 - e)                                     # perihelion distance
        vp = math.sqrt(mu_f * (1 + e) / (a_f * (1 - e)))        # perihelion speed (purely tangential, +y)
        traj = _integrate_orbit(mu_f, rp, 0.0, 0.0, vp, period_f, n_steps)
        eE, eL, gap = _verify_orbit(traj, mu_f, a_f, ctx, e)
        max_eE, max_eL, max_gap = max(max_eE, eE), max(max_eL, eL), max(max_gap, gap)
        full[e] = traj
        sub = _subsample(traj, 140)
        ts = [round(p[0], 4) for p in sub]
        xs = [round(p[1], 4) for p in sub]
        ys = [round(p[2], 4) for p in sub]
        label = ("e = 0: a circle" if e == 0
                 else f"e = {e:g}: ellipse, perihelion {rp/1e6:.2f}×10⁶ m, aphelion {a_f*(1+e)/1e6:.2f}×10⁶ m")
        frames.append(TrajFrame(value=e, label=label, t=ts, x=xs, y=ys))

    # e=0 must reproduce a circle of radius a (independent ground truth)
    if float(ecc_list[0]) == 0:
        r0 = [math.hypot(x, y) for (_t, x, y, _vx, _vy) in full[0.0]]
        if (max(r0) - min(r0)) / a_f > 1e-3:
            raise BuildError(f"{ctx}: e=0 orbit is not a circle of radius a (Δr {max(r0)-min(r0):.2e})")

    default_idx = min(len(ecc_list) - 1, max(1, len(ecc_list) // 2))
    e_def = float(ecc_list[default_idx])
    rp_def, ra_def = a_f * (1 - e_def), a_f * (1 + e_def)
    vp_def = math.sqrt(mu_f * (1 + e_def) / (a_f * (1 - e_def)))
    va_def = math.sqrt(mu_f * (1 - e_def) / (a_f * (1 + e_def)))

    checks = [
        {"key": "energy_conserved", "tier": "numeric", "holds": True,
         "claim": rf"The specific energy $\tfrac12 v^2-\mu/r=-\mu/2a$ is conserved along the orbit (max relative drift ${max_eE:.1e}$)."},
        {"key": "angular_momentum_conserved", "tier": "numeric", "holds": True,
         "claim": rf"The angular momentum $x\dot y-y\dot x$ is conserved (max relative drift ${max_eL:.1e}$) — Kepler's second law: the line to the body sweeps equal areas in equal times."},
        {"key": "orbit_closes", "tier": "numeric", "holds": True,
         "claim": rf"After one period the path returns to its start (gap $<{max_gap:.1e}\,a$) — a closed ellipse (Kepler's first law)."},
        {"key": "period_independent_of_e", "tier": "numeric", "holds": True,
         "claim": r"Every orbit shares the semi-major axis $a$, so all have the same period $T=2\pi\sqrt{a^3/\mu}$ — Kepler's third law depends on $a$, not the shape."},
    ]
    proof = {
        "kind": "governing",
        "heading": "No closed form for the motion exists — so the ellipse is integrated numerically and machine-verified against the conservation laws (Kepler's three laws fall out).",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"integrate $\ddot{\mathbf r}=-\mu\mathbf r/r^3$ by RK4; check energy $\tfrac12 v^2-\mu/r$ and angular momentum $x\dot y-y\dot x$ are conserved; check the orbit closes; same $a\Rightarrow$ same $T$",
        "checks": checks,
    }

    def _res(label, unit, val, tex=""):
        return {"label": label, "unit": unit, "value": round(val, 6), "display": _disp(val), "symbolic_latex": tex}

    result = {
        "period": _res(r"Period $T = 2\pi\sqrt{a^3/\mu}$ (same for every $e$)", "s", period_f, r"2\pi\sqrt{a^3/\mu}"),
        "perihelion": _res(r"Perihelion distance $r_p = a(1-e)$", "m", rp_def, r"a(1-e)"),
        "aphelion": _res(r"Aphelion distance $r_a = a(1+e)$", "m", ra_def, r"a(1+e)"),
        "perihelion_speed": _res(r"Speed at perihelion (fastest)", "m/s", vp_def, r"\sqrt{\tfrac{\mu(1+e)}{a(1-e)}}"),
        "aphelion_speed": _res(r"Speed at aphelion (slowest)", "m/s", va_def, r"\sqrt{\tfrac{\mu(1-e)}{a(1+e)}}"),
    }

    algebra = {
        "steps": [
            {
                "label": "Where the algebra-based course stops",
                "latex": r"v=\sqrt{GM/R}\quad\text{— only for a circle; no algebra formula for an ellipse's motion}",
                "prose": "Centripetal balance handles a circle, but a real orbit is an *ellipse* with the body at "
                         "one focus, speeding up near perihelion and slowing at aphelion. There is no algebra "
                         "formula for where the planet is at time $t$ — the speed and radius change continuously.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Solve the central-force ODE numerically",
                "latex": r"\ddot{\mathbf r} = -\frac{\mu}{r^3}\,\mathbf r,\qquad \mathbf s_{n+1}=\mathbf s_n+\tfrac{h}{6}(k_1+2k_2+2k_3+k_4)",
                "prose": "The same inverse-square law, but now the radius varies, so there is no elementary "
                         "time-parameterisation (Kepler's equation is transcendental). Step the position and "
                         "velocity forward with RK4 from perihelion. The producer checks the result conserves "
                         "energy and angular momentum and that the orbit closes — verification, for a numerical "
                         "solution.",
            },
            {
                "label": "Kepler's first two laws are conservation laws",
                "latex": r"\tfrac12 v^2-\frac{\mu}{r}=-\frac{\mu}{2a}=\text{const}\qquad x\dot y-y\dot x=\text{const}",
                "prose": "Energy conservation fixes the orbit's size (the semi-major axis $a$); angular-momentum "
                         "conservation is **Kepler's second law** — the line from the body to the planet sweeps "
                         "equal areas in equal times, so the planet races through perihelion and dawdles at "
                         "aphelion. The closed curve is an ellipse with the body at one focus (**Kepler's first "
                         "law**).",
                "emphasis": True,
            },
            {
                "label": "Same semi-major axis, same period (Kepler's third law)",
                "latex": r"\boxed{\,T = 2\pi\sqrt{a^3/\mu}\ \text{— independent of the eccentricity}\,}",
                "prose": "Slide the eccentricity: the orbit stretches from a circle to a long thin ellipse, but "
                         "because every one shares the semi-major axis $a$, they all take the *same time* to go "
                         "around. The period depends on $a$ alone — Kepler's third law, the same $T^2\\propto a^3$ "
                         "the circular lesson derived, now for any shape.",
            },
        ],
    }

    view = a_f * (1 + max(float(e) for e in ecc_list)) * 1.12   # fixed extent: fits the largest aphelion
    traj = TrajectoryPlot(
        t=t, t_flight=period_f, constants={}, unit_map={},
        sliders=[],
        markers=[TrajMarker(0.0, 0.0, "focus (central body)", dy=16, va="top", dot=True)],
        x_label="x  (m)", y_label="y  (m)",
        sweep={"name": "e", "label": "eccentricity e", "unit": "", "values": [float(e) for e in ecc_list]},
        frames=frames,
        frame_mode="orbit", mu=mu_f, view_half=view,
    )

    return Scenario(
        regime=2,
        constants_export={"mu": mu_f, "a": a_f, "T": period_f, "e_default": e_def},
        proof=proof, algebra=algebra, calculus=calculus,
        initial_conditions={"x0": a_f * (1 - e_def), "y0": 0.0},
        trajectory=traj,
    )


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    if "mu" not in p:
        raise BuildError(f"{spec.get('id')}: orbit requires parameters.mu")
    mu_val = sp.nsimplify(p["mu"])
    if "eccentricities" in p:
        if "a" not in p:
            raise BuildError(f"{spec.get('id')}: elliptical orbit requires parameters.a (semi-major axis)")
        return _elliptical(spec, mu_val, sp.nsimplify(p["a"]), p["eccentricities"])
    if "R" not in p:
        raise BuildError(f"{spec.get('id')}: circular orbit requires parameters.R")
    return _circular(spec, mu_val, sp.nsimplify(p["R"]))
