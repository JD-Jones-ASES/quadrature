"""Cross-checks for the rotational work–energy model — the area instrument on the angle axis (the rotational
mirror of work_energy): the area under τ(θ) is the work, and ½Iω² falls out of the same integral."""

import math

import sympy as sp

from quadrature_producer.models import rotational_work

SPEC = {"id": "t", "parameters": {"I": 0.5, "c": 8, "theta": 1.5, "theta_window": 2.0}}


def test_builds_on_area_instrument_with_integral_proof():
    scn = rotational_work.build(SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "integral" and scn.area is not None
    assert scn.x_expr is None                                  # reuses the AreaPlot — no temporal stack
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "rotational_work_energy", "constant_torque_echo"} <= keys


def test_results_match_hand_physics():
    r = rotational_work.build(SPEC).algebra["result"]
    I, c, th = 0.5, 8, 1.5
    W = 0.5 * c * th**2
    assert math.isclose(r["work_done"]["value"], W, rel_tol=1e-9)                  # ½cθ² = 9 J
    assert math.isclose(r["rotational_ke"]["value"], W, rel_tol=1e-9)             # work = KE
    assert math.isclose(r["final_omega"]["value"], math.sqrt(2 * W / I), rel_tol=1e-9)   # √(2W/I) = 6 rad/s
    assert math.isclose(r["max_torque"]["value"], c * th, rel_tol=1e-9)           # cθ = 12 N·m


def test_ke_falls_out_of_the_torque_integral():
    theta, c, I = rotational_work.theta, rotational_work.c, rotational_work.I
    w = sp.Symbol("w", nonnegative=True)
    W = sp.integrate(c * w, (w, 0, theta))                   # ∫ τ dθ
    omega = sp.sqrt(2 * W / I)
    assert sp.simplify(sp.diff(W, theta) - c * theta) == 0     # dW/dθ = τ (FTC)
    assert sp.simplify(sp.Rational(1, 2) * I * omega**2 - W) == 0   # ½Iω² = W


def test_torque_and_work_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    a = rotational_work.build(SPEC).area
    amap = {s: parse_unit(uu, "t") for s, uu in a.unit_map.items()}
    check_homogeneous(a.f_expr, amap, "t: tau")             # cθ → N·m
    check_homogeneous(a.g_expr, amap, "t: W")              # ½cθ² → J
