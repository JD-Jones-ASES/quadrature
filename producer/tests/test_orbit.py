"""Cross-checks for the circular-orbit model — the trajectory instrument on a centred frame: the parametric
circle solves the inverse-square equation of motion, and the orbital speed + Kepler's third law fall out."""

import math

import sympy as sp

from quadrature_producer.models import orbit

SPEC = {"id": "t", "parameters": {"mu": 4e14, "R": 7e6, "R_min": 7e6, "R_max": 4.22e7}}


def test_builds_on_trajectory_with_orbit_frame():
    scn = orbit.build(SPEC)
    assert scn.regime == 1 and scn.proof["kind"] == "equivalence"
    assert scn.trajectory is not None and scn.trajectory.frame_mode == "orbit"
    assert scn.area is None and scn.x_expr is None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"is_circle", "solves_eom_x", "solves_eom_y", "orbital_speed", "kepler_third"} <= keys


def test_results_match_hand_physics():
    r = orbit.build(SPEC).algebra["result"]
    mu, R = 4e14, 7e6
    assert math.isclose(r["orbital_speed"]["value"], math.sqrt(mu / R), rel_tol=1e-6)          # √(μ/R) ≈ 7559 m/s
    assert math.isclose(r["period"]["value"], 2 * math.pi * math.sqrt(R**3 / mu), rel_tol=1e-6)  # ≈ 5818 s
    assert math.isclose(r["gravity_at_orbit"]["value"], mu / R**2, rel_tol=1e-6)               # μ/R² ≈ 8.16 m/s²
    # consistency: v = ωR and T = 2πR/v (ω≈1e-3 is rounded to 6 dp in make_result, so check it loosely;
    # the exact v=ωR is proven symbolically in test_path_solves_the_inverse_square_eom_independently)
    v, T, w = r["orbital_speed"]["value"], r["period"]["value"], r["angular_rate"]["value"]
    assert math.isclose(v, w * R, rel_tol=1e-3)
    assert math.isclose(T, 2 * math.pi * R / v, rel_tol=1e-6)


def test_path_solves_the_inverse_square_eom_independently():
    t, mu, R = orbit.t, orbit.mu, orbit.R
    w = sp.sqrt(mu / R**3)
    x, y = R * sp.cos(w * t), R * sp.sin(w * t)
    # ẍ = −μ x / r³ with r = R on the circle
    assert sp.simplify(sp.diff(x, t, 2) + mu * x / R**3) == 0
    assert sp.simplify(sp.diff(y, t, 2) + mu * y / R**3) == 0
    assert sp.simplify((x**2 + y**2) - R**2) == 0                      # constant radius (a circle)
    assert sp.simplify((sp.diff(x, t)**2 + sp.diff(y, t)**2) - mu / R) == 0   # v² = μ/R


def test_kepler_third_law_scaling():
    # doubling the radius multiplies the period by 2^{3/2}
    r1 = orbit.build(SPEC).algebra["result"]["period"]["value"]
    spec2 = {"id": "t", "parameters": {"mu": 4e14, "R": 14e6, "R_min": 7e6, "R_max": 4.22e7}}
    r2 = orbit.build(spec2).algebra["result"]["period"]["value"]
    assert math.isclose(r2 / r1, 2**1.5, rel_tol=1e-6)


def test_path_is_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    tr = orbit.build(SPEC).trajectory
    tmap = {s: parse_unit(uu, "t") for s, uu in tr.unit_map.items()}
    check_homogeneous(tr.x_expr, tmap, "t: x(t)")      # R cos(√(μ/R³)·t) → m, arg dimensionless
    check_homogeneous(tr.y_expr, tmap, "t: y(t)")


# --- elliptical orbit (regime 2, numerical RK4 + conservation) ---

ELL = {"id": "e", "parameters": {"mu": 4e14, "a": 1.6e7, "eccentricities": [0, 0.2, 0.4, 0.5], "steps": 8000}}


def test_elliptical_builds_with_governing_proof_and_frames():
    scn = orbit.build(ELL)
    assert scn.regime == 2 and scn.proof["kind"] == "governing"
    tr = scn.trajectory
    assert tr.frame_mode == "orbit" and tr.frames is not None and len(tr.frames) == 4
    assert tr.view_half and tr.view_half > 1.6e7        # fixed view covers the largest aphelion
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"energy_conserved", "angular_momentum_conserved", "orbit_closes", "period_independent_of_e"} <= keys


def test_elliptical_conserves_energy_and_angular_momentum():
    # re-integrate independently and check the invariants on the e=0.5 orbit
    mu, a, e = 4e14, 1.6e7, 0.5
    rp, vp = a * (1 - e), math.sqrt(mu * (1 + e) / (a * (1 - e)))
    T = 2 * math.pi * math.sqrt(a**3 / mu)
    traj = orbit._integrate_orbit(mu, rp, 0.0, 0.0, vp, T, 8000)
    E0 = 0.5 * vp**2 - mu / rp
    L0 = rp * vp
    for (_t, x, y, vx, vy) in traj:
        r = math.hypot(x, y)
        assert math.isclose(0.5 * (vx**2 + vy**2) - mu / r, E0, rel_tol=2e-4)   # energy conserved
        assert math.isclose(x * vy - y * vx, L0, rel_tol=2e-4)                  # angular momentum conserved
    assert math.isclose(E0, -mu / (2 * a), rel_tol=1e-6)                        # vis-viva: E = −μ/2a
    # closes after one period
    assert math.hypot(traj[-1][1] - rp, traj[-1][2]) / a < 1e-2


def test_period_independent_of_eccentricity_kepler_third():
    scn = orbit.build(ELL)
    T = scn.constants_export["T"]
    assert math.isclose(T, 2 * math.pi * math.sqrt(1.6e7**3 / 4e14), rel_tol=1e-9)
    # every committed frame shares the same period (t_max)
    tmaxes = [fr.t[-1] for fr in scn.trajectory.frames]
    assert max(tmaxes) - min(tmaxes) < 1e-3


def test_eccentric_orbit_is_faster_at_perihelion():
    r = orbit.build(ELL).algebra["result"]
    assert r["perihelion_speed"]["value"] > r["aphelion_speed"]["value"]        # Kepler's 2nd law
    assert r["perihelion"]["value"] < r["aphelion"]["value"]
