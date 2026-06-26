"""Independent cross-checks for the 2D projectile model — the trajectory instrument (ADR-0015).
Drag-free (regime 1, exact closed form) is verified here; the quadratic-drag path is Part B."""

import math

import sympy as sp

from quadrature_producer.models import projectile

SPEC = {"id": "t", "parameters": {"v0": 20, "theta": 40, "g": -10}}


def test_drag_free_builds_with_trajectory_and_equivalence_proof():
    scn = projectile.build(SPEC)
    assert scn.regime == 1
    assert scn.proof["kind"] == "equivalence" and scn.proof["holds"]
    assert scn.x_expr is None and scn.trajectory is not None and scn.trajectory.x_expr is not None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"x_constant_velocity", "y_constant_gravity", "ic", "range_falls_out", "height_falls_out"} <= keys


def test_results_match_hand_physics():
    r = projectile.build(SPEC).algebra["result"]
    v0, th, g = 20.0, math.radians(40), 10.0
    # results are stored rounded to 6 decimals, so compare with a matching tolerance
    assert math.isclose(r["range"]["value"], v0**2 * math.sin(2 * th) / g, rel_tol=1e-5)        # ≈ 39.4 m
    assert math.isclose(r["max_height"]["value"], (v0 * math.sin(th))**2 / (2 * g), rel_tol=1e-5)  # ≈ 8.26 m
    assert math.isclose(r["flight_time"]["value"], 2 * v0 * math.sin(th) / g, rel_tol=1e-5)      # ≈ 2.57 s


def test_components_are_independent_constant_acceleration():
    t, v0, theta, g = projectile.t, projectile.v0, projectile.theta, projectile.g
    thr = theta * sp.pi / 180
    x = v0 * sp.cos(thr) * t
    y = v0 * sp.sin(thr) * t + g * t**2 / 2
    assert sp.simplify(sp.diff(x, t, 2)) == 0          # no horizontal force
    assert sp.simplify(sp.diff(y, t, 2) - g) == 0      # vertical acceleration is g
    # range = x at landing equals the memorized v0² sin2θ / |g|
    flight = -2 * v0 * sp.sin(thr) / g
    assert sp.simplify(x.subs(t, flight) - v0**2 * sp.sin(2 * thr) / (-g)) == 0


def test_complementary_angles_give_equal_range():
    r40 = projectile.build({"id": "t", "parameters": {"v0": 20, "theta": 40, "g": -10}}).algebra["result"]
    r50 = projectile.build({"id": "t", "parameters": {"v0": 20, "theta": 50, "g": -10}}).algebra["result"]
    assert math.isclose(r40["range"]["value"], r50["range"]["value"], rel_tol=1e-9)


# --- Part B: quadratic-drag (numerical) ---

DRAG_SPEC = {"id": "t", "parameters": {"v0": 30, "theta": 45, "g": -10, "m": 1,
                                       "b_values": [0, 0.005, 0.01, 0.02, 0.04]}}


def test_drag_builds_with_numerical_frames_and_governing_proof():
    scn = projectile.build(DRAG_SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "governing" and scn.proof["holds"]
    tr = scn.trajectory
    assert tr.x_expr is None and tr.frames is not None and tr.reference is not None
    assert len(tr.frames) == 5
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"converged", "solves_eom", "recovers_parabola", "drag_shortens"} <= keys


def test_drag_b0_recovers_the_exact_parabola():
    tr = projectile.build(DRAG_SPEC).trajectory
    f0 = tr.frames[0]
    assert f0.value == 0
    analytic_range = 30**2 * math.sin(math.radians(90)) / 10           # 90 m
    assert math.isclose(f0.x[-1], analytic_range, abs_tol=1e-2)         # b=0 path lands at the parabola's range


def test_drag_monotonically_shortens_the_range():
    tr = projectile.build(DRAG_SPEC).trajectory
    ranges = [fr.x[-1] for fr in tr.frames]                            # frames are in increasing-b order
    assert all(ranges[i + 1] < ranges[i] for i in range(len(ranges) - 1))
    assert ranges[-1] < 0.5 * ranges[0]                               # heavy drag roughly halves (or more) the range


def test_drag_integrator_matches_an_independent_rk4():
    # integrate the SAME EOM independently and compare the landing range
    import math as _m
    c, g, h = 0.01, -10.0, 0.001
    vx, vy = 30 * _m.cos(_m.radians(45)), 30 * _m.sin(_m.radians(45))
    x = y = t = 0.0
    def rhs(s):
        sx, sy, svx, svy = s; sp_ = _m.hypot(svx, svy)
        return [svx, svy, -c * sp_ * svx, g - c * sp_ * svy]
    s = [0.0, 0.0, vx, vy]; prev = s[:]
    while True:
        k1 = rhs(s); k2 = rhs([s[i]+0.5*h*k1[i] for i in range(4)])
        k3 = rhs([s[i]+0.5*h*k2[i] for i in range(4)]); k4 = rhs([s[i]+h*k3[i] for i in range(4)])
        nxt = [s[i]+(h/6)*(k1[i]+2*k2[i]+2*k3[i]+k4[i]) for i in range(4)]
        if nxt[1] < 0 and t > h:
            frac = s[1]/(s[1]-nxt[1]); land_x = s[0]+frac*(nxt[0]-s[0]); break
        s = nxt; t += h
    tr = projectile.build(DRAG_SPEC).trajectory
    f = next(fr for fr in tr.frames if fr.value == 0.01)
    assert math.isclose(f.x[-1], land_x, abs_tol=2e-2)
