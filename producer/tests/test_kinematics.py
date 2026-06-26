"""Independent physics cross-checks for the constant-acceleration model.

These re-derive the throw-up answers by hand-checkable formulas (NOT by calling the same
solver), so a regression in kinematics.py is caught against physics, not against itself.
"""

import math

import sympy as sp

from quadrature_producer.kinematics import build_model, prove_equivalence, a, t, x0, v0


def _num(expr, model):
    return float(sp.N(expr.subs(model.subs)))


def test_throw_up_answers_match_hand_physics():
    # ball: v0 = 20 up, x0 = 1.5, a = g = -10, ground = 0
    m = build_model(a_value=-10, x0_value=1.5, v0_value=20, ground=0.0)
    apex = _num(m.unknowns["apex_time"], m)
    hmax = _num(m.unknowns["max_height"], m)
    tfly = _num(m.unknowns["flight_time"], m)
    vimp = _num(m.unknowns["impact_velocity"], m)

    # apex time = v0 / |g|
    assert math.isclose(apex, 20 / 10, rel_tol=1e-9)
    # max height = x0 + v0^2 / (2|g|)
    assert math.isclose(hmax, 1.5 + 20**2 / (2 * 10), rel_tol=1e-9)
    # flight: 1.5 + 20 t - 5 t^2 = 0  ->  t = (20 + sqrt(430)) / 10
    assert math.isclose(tfly, (20 + math.sqrt(430)) / 10, rel_tol=1e-9)
    # impact speed = -sqrt(v0^2 + 2|g| x0) downward
    assert math.isclose(vimp, -math.sqrt(20**2 + 2 * 10 * 1.5), rel_tol=1e-9)
    assert vimp < 0  # up positive -> impact is downward


def test_velocity_zero_at_apex_but_accel_is_not():
    m = build_model(a_value=-10, x0_value=1.5, v0_value=20)
    apex = m.unknowns["apex_time"]
    assert sp.simplify(m.v_expr.subs(t, apex)) == 0          # v = 0 at apex
    assert float(m.a_expr.subs(m.subs)) == -10.0            # a is the constant, never 0
    assert m.subs[a] != 0


def test_calculus_register_is_the_integral():
    m = build_model(a_value=-10, x0_value=1.5, v0_value=20)
    assert sp.simplify(sp.diff(m.x_expr, t) - m.v_expr) == 0   # dx/dt = v
    assert sp.simplify(sp.diff(m.v_expr, t) - m.a_expr) == 0   # dv/dt = a
    # and the algebra formulas equal the calculus expressions
    assert sp.simplify(m.x_alg - m.x_expr) == 0
    assert sp.simplify(m.v_alg - m.v_expr) == 0


def test_equivalence_proof_runs_clean():
    m = build_model(a_value=-10, x0_value=1.5, v0_value=20)
    proof = prove_equivalence(m, "test")
    assert proof["holds"] is True
    keys = {c["key"] for c in proof["checks"]}
    assert {"flight_time_lands", "apex_is_v_zero", "max_height_agrees"} <= keys


def test_general_parameters():
    # a different launch must still satisfy v=0 at apex and land at ground
    m = build_model(a_value=-10, x0_value=0, v0_value=30)
    apex = _num(m.unknowns["apex_time"], m)
    assert math.isclose(apex, 3.0, rel_tol=1e-9)
    assert math.isclose(_num(m.unknowns["max_height"], m), 45.0, rel_tol=1e-9)
    # symmetric throw from the ground: flight = 2 * apex
    assert math.isclose(_num(m.unknowns["flight_time"], m), 6.0, rel_tol=1e-9)
