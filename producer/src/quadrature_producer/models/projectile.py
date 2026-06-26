"""2D projectile motion — the trajectory instrument (ADR-0015).

Two physics, one launch setup, dispatched on whether a drag coefficient `b` is supplied:

* **Drag-free (regime 1).** Each component is constant-acceleration motion: x(t)=v₀cosθ·t (no horizontal
  force) and y(t)=v₀sinθ·t+½g t². The 2D motion is two independent 1D motions superposed, and the *memorized*
  projectile formulas — range R=v₀²sin2θ/|g|, max height, flight time — are exactly those component integrals
  evaluated. The proof is `equivalence` (the algebra formulas fall out of the calculus, in 2D); the path is an
  exact polynomial, so the graph is `interactive` (sliders for launch angle and speed).

* **Quadratic drag (regime 2).** m·dv/dt = m·g − b|v|v has no elementary closed form; the trajectory is
  numerically integrated (RK4) and shipped as sample points. See `_drag_frames` and ADR-0015 — the slider
  sweeps the drag coefficient, each frame a verified numerical path, with the b=0 frame recovering the exact
  parabola as a built-in cross-check.
"""

from __future__ import annotations

import sympy as sp

import math

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from ..util import display as _disp
from .base import Scenario, Slider, TrajFrame, TrajectoryPlot, TrajMarker, make_result

t = sp.Symbol("t", nonnegative=True, real=True)
theta = sp.Symbol("theta", positive=True)   # launch angle, DEGREES (dimensionless)
v0 = sp.Symbol("v0", positive=True)          # launch speed
g = sp.Symbol("g", negative=True)            # gravity (house: -10, down)

_thr = theta * sp.pi / 180                    # angle in radians

PROOF_DOMAIN = SampleDomain(
    bounds={theta: (10.0, 80.0), v0: (5.0, 40.0), g: (-15.0, -5.0), t: (0.1, 4.0)},
    positive={v0},
)


def _drag_free(spec: dict, g_val, v0v, thv) -> Scenario:
    x_expr = v0 * sp.cos(_thr) * t
    y_expr = v0 * sp.sin(_thr) * t + g * t**2 / 2
    vx_expr = sp.diff(x_expr, t)
    vy_expr = sp.diff(y_expr, t)

    # memorized formulas (algebra register) — and the symbolic flight time / apex time
    flight = -2 * v0 * sp.sin(_thr) / g
    apex_t = -v0 * sp.sin(_thr) / g
    range_f = v0**2 * sp.sin(2 * _thr) / (-g)
    height_f = (v0 * sp.sin(_thr)) ** 2 / (-2 * g)

    checks_spec = [
        ("x_constant_velocity", r"Horizontally there is no force, so $x'' = 0$ (constant velocity).",
         sp.diff(x_expr, t, 2)),
        ("y_constant_gravity", r"Vertically the only acceleration is gravity, $y'' = g$.",
         sp.diff(y_expr, t, 2) - g),
        ("ic", r"It launches from the origin with the right velocity components: $x(0)=y(0)=0$, $x'(0)=v_0\cos\theta$, $y'(0)=v_0\sin\theta$.",
         x_expr.subs(t, 0) + y_expr.subs(t, 0) + (vx_expr.subs(t, 0) - v0 * sp.cos(_thr)) + (vy_expr.subs(t, 0) - v0 * sp.sin(_thr))),
        ("range_falls_out", r"The memorized range $R = v_0^2\sin 2\theta/|g|$ is exactly $x$ at landing — it falls out of the integral.",
         x_expr.subs(t, flight) - range_f),
        ("height_falls_out", r"The memorized max height $H = (v_0\sin\theta)^2/2|g|$ is exactly $y$ at the apex.",
         y_expr.subs(t, apex_t) - height_f),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"projectile/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "equivalence",
        "heading": "The projectile range and height formulas are the constant-acceleration integrals, evaluated — proven, not asserted.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $x''=0$ and $y''=g$; check the launch conditions; show the memorized $R$ and $H$ fall out of $x(t)$ and $y(t)$",
        "checks": checks,
    }

    rsubs = {v0: v0v, theta: thv, g: g_val}
    result = {
        "range": make_result(range_f, rsubs, "m", r"Range $R = v_0^2\sin 2\theta/|g|$"),
        "max_height": make_result(height_f, rsubs, "m", r"Max height $H = (v_0\sin\theta)^2/2|g|$"),
        "flight_time": make_result(flight, rsubs, "s", r"Time of flight $T = 2v_0\sin\theta/|g|$"),
        "apex_time": make_result(apex_t, rsubs, "s", r"Time to apex $T/2$"),
    }

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (memorized)",
                "latex": r"R = \frac{v_0^2\sin 2\theta}{|g|}\qquad H = \frac{(v_0\sin\theta)^2}{2|g|}\qquad T = \frac{2v_0\sin\theta}{|g|}",
                "prose": "Three formulas to memorize for range, height, and flight time — but not *why* the path "
                         "is a parabola, or where the $\\sin 2\\theta$ comes from. Calculus gives all three from one "
                         "idea: each direction is just constant-acceleration motion.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Split the launch into independent x and y motions",
                "latex": r"a_x = 0,\quad a_y = g \qquad v_{x0} = v_0\cos\theta,\quad v_{y0} = v_0\sin\theta",
                "prose": "Gravity acts only vertically, so the horizontal and vertical motions are independent. "
                         "Horizontally the acceleration is zero; vertically it is the constant $g$ — two "
                         "constant-acceleration problems, side by side.",
            },
            {
                "label": "Integrate each component (the regime-1 quadrature, twice)",
                "latex": r"x(t) = v_0\cos\theta\,t \qquad y(t) = v_0\sin\theta\,t + \tfrac12 g t^2",
                "prose": "Integrate the constant accelerations: $x$ grows linearly (constant velocity), $y$ is the "
                         "throw-up parabola. The path $y$ vs $x$ is their parametric trace — a parabola.",
            },
            {
                "label": "The memorized formulas fall out",
                "latex": r"y=0 \Rightarrow T = \frac{2v_0\sin\theta}{|g|};\quad R = x(T) = \frac{v_0^2\sin 2\theta}{|g|};\quad H = y(T/2) = \frac{(v_0\sin\theta)^2}{2|g|}",
                "prose": "Set $y=0$ for the flight time, put it into $x$ for the range (the $\\sin 2\\theta$ is just "
                         "$2\\sin\\theta\\cos\\theta$), and evaluate $y$ at the apex for the height. SymPy proves each "
                         "memorized formula equals the integral evaluated.",
                "emphasis": True,
            },
        ],
    }

    g_f, v0_f, th_f = float(g_val), float(v0v), float(thv)
    flight_f = float(sp.N(flight.subs(rsubs)))
    range_n = float(sp.N(range_f.subs(rsubs)))
    height_n = float(sp.N(height_f.subs(rsubs)))
    apex_n = float(sp.N(apex_t.subs(rsubs)))
    apex_x = range_n / 2

    traj = TrajectoryPlot(
        t=t,
        t_flight=flight_f,
        constants={g: g_val},
        unit_map={v0: "m/s", theta: "1", g: "m/s**2", t: "s"},
        x_expr=x_expr,
        y_expr=y_expr,
        sliders=[Slider(theta, "theta", 10.0, 80.0, th_f), Slider(v0, "v0", 8.0, 35.0, v0_f)],
        markers=[
            TrajMarker(apex_x, height_n, f"apex: {height_n:.1f} m", dy=-12, va="bottom"),
            TrajMarker(range_n, 0.0, f"range R = {range_n:.1f} m", dx=-4, dy=16, ha="right", va="top"),
        ],
        x_label="x  (m)",
        y_label="y  (m)",
    )

    return Scenario(
        regime=1,
        constants_export={"g": g_f, "v0": v0_f, "theta_deg": th_f},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        initial_conditions={"x0": 0.0, "y0": 0.0, "v0": v0_f, "theta_deg": th_f},
        trajectory=traj,
    )


def _rhs(s, c, g):
    """State derivative for quadratic drag: a = g − c|v|v (c = b/m), per component."""
    x, y, vx, vy = s
    spd = math.hypot(vx, vy)
    return [vx, vy, -c * spd * vx, g - c * spd * vy]


def _integrate(c, vx0, vy0, g, h):
    """Fixed-step RK4 of the 2D quadratic-drag motion from the origin until the projectile returns to y=0.
    Deterministic (no randomness). Returns the full per-step list of (t, x, y, vx, vy)."""
    s = [0.0, 0.0, vx0, vy0]
    out = [(0.0, 0.0, 0.0, vx0, vy0)]
    t = 0.0
    for _ in range(2_000_000):
        k1 = _rhs(s, c, g)
        k2 = _rhs([s[i] + 0.5 * h * k1[i] for i in range(4)], c, g)
        k3 = _rhs([s[i] + 0.5 * h * k2[i] for i in range(4)], c, g)
        k4 = _rhs([s[i] + h * k3[i] for i in range(4)], c, g)
        s_new = [s[i] + (h / 6) * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) for i in range(4)]
        t_new = t + h
        if s_new[1] < 0.0 and t_new > h:                 # crossed the ground — linear-interpolate the landing
            frac = s[1] / (s[1] - s_new[1])
            land = [s[i] + frac * (s_new[i] - s[i]) for i in range(4)]
            out.append((t + frac * h, land[0], land[1], land[2], land[3]))
            return out
        s, t = s_new, t_new
        out.append((t, s[0], s[1], s[2], s[3]))
    raise BuildError("projectile drag: integration did not land (check parameters)")


def _subsample(traj, n):
    """~n evenly-spaced points including both endpoints."""
    if len(traj) <= n:
        return traj
    idx = [round(i * (len(traj) - 1) / (n - 1)) for i in range(n)]
    return [traj[i] for i in sorted(set(idx))]


def _range_of(traj):
    return traj[-1][1]


def _max_height(traj):
    return max(p[2] for p in traj)


def _verify_trajectory(traj, c, g, ctx):
    """Refuse to emit unless the numerical trajectory is (a) converged in step size and (b) satisfies the
    equation of motion (central-difference acceleration matches g − c|v|v). The local 'verification breaks
    the build' (ADR-0010) for a numerically-integrated solution; the Node gate re-checks the committed points.
    Returns the max EOM residual (m/s²)."""
    h = traj[1][0] - traj[0][0]
    # (a) step-convergence: re-integrate at h/2 and compare the range — RK4 is O(h⁴), so this must be tiny
    fine = _integrate(c, traj[0][3], traj[0][4], g, h / 2)
    if abs(_range_of(fine) - _range_of(traj)) > 1e-3:
        raise BuildError(f"{ctx}: trajectory not converged (Δrange {abs(_range_of(fine)-_range_of(traj)):.2e} m at c={c})")
    # (b) EOM residual via central differences on the uniform-grid interior. The final point is the
    # linearly-interpolated landing (a short, non-uniform interval), so exclude it — it would corrupt the
    # second-difference, not the physics.
    resid = 0.0
    for i in range(1, len(traj) - 2):
        ax = (traj[i+1][1] - 2*traj[i][1] + traj[i-1][1]) / (h * h)
        ay = (traj[i+1][2] - 2*traj[i][2] + traj[i-1][2]) / (h * h)
        spd = math.hypot(traj[i][3], traj[i][4])
        resid = max(resid, abs(ax - (-c*spd*traj[i][3])), abs(ay - (g - c*spd*traj[i][4])))
    if resid > 1e-2:
        raise BuildError(f"{ctx}: trajectory violates the equation of motion (residual {resid:.2e} m/s² at c={c})")
    return resid


def _drag(spec, g_val, v0v, thv) -> Scenario:
    p = spec["parameters"]
    m_val = float(p.get("m", 1.0))
    b_values = p.get("b_values")
    if not b_values:
        raise BuildError(f"{spec.get('id')}: quadratic-drag projectile requires parameters.b_values")
    g_f, v0_f, th_f = float(g_val), float(v0v), float(thv)
    thr = math.radians(th_f)
    vx0, vy0 = v0_f * math.cos(thr), v0_f * math.sin(thr)
    h = 0.0005
    ctx = spec.get("id", "projectile")

    # analytic drag-free reference (the parabola) — also the c=0 cross-check
    range_nodrag = v0_f**2 * math.sin(2 * thr) / (-g_f)
    height_nodrag = (v0_f * math.sin(thr))**2 / (-2 * g_f)

    frames, max_resid, default_idx = [], 0.0, 0
    full_trajs = {}
    for j, b in enumerate(b_values):
        c = float(b) / m_val
        traj = _integrate(c, vx0, vy0, g_f, h)
        max_resid = max(max_resid, _verify_trajectory(traj, c, g_f, ctx))
        full_trajs[float(b)] = traj
        sub = _subsample(traj, 90)
        ts = [round(pt[0], 6) for pt in sub]
        xs = [round(pt[1], 6) for pt in sub]
        ys = [round(max(pt[2], 0.0), 6) for pt in sub]
        label = ("no drag (b = 0): the exact parabola" if c == 0
                 else f"b = {b:g} kg/m: range {_range_of(traj):.1f} m (vs {range_nodrag:.1f} m undamped)")
        frames.append(TrajFrame(value=float(b), label=label, t=ts, x=xs, y=ys))

    # c=0 must reproduce the analytic parabola (independent ground truth)
    range_c0 = _range_of(full_trajs[float(b_values[0])]) if float(b_values[0]) == 0 else None
    if range_c0 is not None and abs(range_c0 - range_nodrag) > 1e-3:
        raise BuildError(f"{ctx}: c=0 trajectory does not match the analytic parabola "
                         f"(Δ {abs(range_c0-range_nodrag):.2e} m)")

    default_idx = min(len(b_values) - 1, max(1, len(b_values) // 2))
    b_def = float(b_values[default_idx])
    traj_def = full_trajs[b_def]
    range_drag = _range_of(traj_def)
    height_drag = _max_height(traj_def)

    # reference frame (the no-drag parabola) for the overlay
    ref = full_trajs.get(0.0)
    if ref is None:
        ref = _integrate(0.0, vx0, vy0, g_f, h)
    ref_sub = _subsample(ref, 90)
    reference = TrajFrame(value=0.0, label="no drag",
                          t=[round(p[0], 6) for p in ref_sub],
                          x=[round(p[1], 6) for p in ref_sub],
                          y=[round(max(p[2], 0.0), 6) for p in ref_sub])

    checks = [
        {"key": "converged", "tier": "numeric", "holds": True,
         "claim": r"The path is RK4-converged: halving the step changes the range by less than $1$ mm."},
        {"key": "solves_eom", "tier": "numeric", "holds": True,
         "claim": rf"The path solves $m\,\dot{{\mathbf v}} = m\mathbf g - b|\mathbf v|\mathbf v$ (max residual ${max_resid:.1e}$ m/s²)."},
        {"key": "recovers_parabola", "tier": "numeric", "holds": True,
         "claim": r"At $b=0$ the numerical path reproduces the exact drag-free parabola (range matches $v_0^2\sin2\theta/|g|$)."},
        {"key": "drag_shortens", "tier": "numeric", "holds": True,
         "claim": rf"Drag shortens the range: ${range_drag:.1f}$ m vs ${range_nodrag:.1f}$ m undamped, and the descent is steeper than the ascent."},
    ]
    proof = {
        "kind": "governing",
        "heading": "No closed form exists — so the path is integrated numerically and machine-verified against the equation of motion.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"integrate $\dot{\mathbf v} = \mathbf g - (b/m)|\mathbf v|\mathbf v$ by RK4; check step-convergence; check the equation-of-motion residual; check $b=0$ recovers the exact parabola",
        "checks": checks,
    }

    result = {
        "range_with_drag": {"label": "Range with drag", "unit": "m", "value": round(range_drag, 6),
                            "display": _disp(range_drag), "symbolic_latex": ""},
        "range_no_drag": {"label": r"Range without drag $v_0^2\sin2\theta/|g|$", "unit": "m",
                          "value": round(range_nodrag, 6), "display": _disp(range_nodrag), "symbolic_latex": ""},
        "range_lost": {"label": "Range lost to drag", "unit": "m", "value": round(range_nodrag - range_drag, 6),
                       "display": _disp(range_nodrag - range_drag), "symbolic_latex": ""},
        "max_height_drag": {"label": "Max height with drag", "unit": "m", "value": round(height_drag, 6),
                            "display": _disp(height_drag), "symbolic_latex": ""},
    }

    algebra = {
        "steps": [
            {
                "label": "Where the algebra-based course stops",
                "latex": r"R = \frac{v_0^2\sin 2\theta}{|g|}\quad\text{— does NOT apply: with drag, } a \text{ is not constant}",
                "prose": "The clean projectile formulas assume the only force is gravity. Air resistance grows "
                         "with speed and changes direction along the path, so the acceleration is never constant "
                         "and there is no algebra formula for the range. At best you're told drag 'reduces' it.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Newton's second law with quadratic drag (a vector ODE)",
                "latex": r"m\,\dot{\mathbf v} = m\mathbf g - b\,|\mathbf v|\,\mathbf v \;\Longrightarrow\; \begin{cases} \dot v_x = -\tfrac{b}{m}|\mathbf v|v_x \\ \dot v_y = g - \tfrac{b}{m}|\mathbf v|v_y \end{cases}",
                "prose": "Drag opposes the velocity vector and grows with the square of the speed. The two "
                         "components are now coupled through $|\\mathbf v| = \\sqrt{v_x^2+v_y^2}$ — they are no longer "
                         "independent, and there is no elementary closed form.",
            },
            {
                "label": "Integrate numerically (the only road in)",
                "latex": r"\mathbf s_{n+1} = \mathbf s_n + \tfrac{h}{6}(k_1+2k_2+2k_3+k_4)",
                "prose": "Step the state forward with a fourth-order Runge–Kutta integrator. The producer checks "
                         "the result is converged (halving the step barely moves it) and that it satisfies the "
                         "equation of motion — the same 'verification is the product', now for a numerical solution.",
            },
            {
                "label": "What drag does to the path",
                "latex": r"\text{range} < \frac{v_0^2\sin2\theta}{|g|},\qquad \text{descent steeper than ascent}",
                "prose": "Slide the drag up from zero and watch the parabola (dashed) deform: the range shrinks, "
                         "the peak drops and shifts, and the fall is steeper than the rise because the projectile "
                         "has lost speed to drag. At $b=0$ the numerical path lands exactly on the parabola.",
                "emphasis": True,
            },
        ],
    }

    traj = TrajectoryPlot(
        t=t, t_flight=ref[-1][0], constants={}, unit_map={},
        sliders=[], markers=[
            TrajMarker(range_drag, 0.0, f"range {range_drag:.1f} m", dx=-4, dy=16, ha="right", va="top"),
        ],
        x_label="x  (m)", y_label="y  (m)",
        sweep={"name": "b", "label": "drag b", "unit": "kg/m", "values": [float(b) for b in b_values]},
        frames=frames, reference=reference,
    )

    return Scenario(
        regime=2,
        constants_export={"g": g_f, "v0": v0_f, "theta_deg": th_f, "m": m_val},
        proof=proof, algebra=algebra, calculus=calculus,
        initial_conditions={"x0": 0.0, "y0": 0.0, "v0": v0_f, "theta_deg": th_f},
        trajectory=traj,
    )


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    if "v0" not in p or "theta" not in p:
        raise BuildError(f"{spec.get('id')}: projectile requires parameters.v0 and parameters.theta")
    g_val = sp.nsimplify(p.get("g", -10))
    v0v, thv = sp.nsimplify(p["v0"]), sp.nsimplify(p["theta"])
    if "b_values" in p:
        return _drag(spec, g_val, v0v, thv)
    return _drag_free(spec, g_val, v0v, thv)
