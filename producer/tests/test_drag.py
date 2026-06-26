"""Independent cross-checks for the linear-drag (regime-2) terminal-velocity model."""

import math

import sympy as sp

from quadrature_producer.models import linear_drag as drag


def test_drag_builds_and_proof_holds():
    scn = drag.build({"id": "t", "parameters": {"m": 1, "b": 0.5, "x0": 0, "v0": 0, "g": -10}})
    assert scn.regime == 2 and scn.proof["kind"] == "governing" and scn.proof["holds"]
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"solves_eom", "ic_velocity", "x_is_integral_of_v", "terminal_limit"} <= keys


def test_drag_results_match_hand_physics():
    scn = drag.build({"id": "t", "parameters": {"m": 1, "b": 0.5, "x0": 0, "v0": 0, "g": -10}})
    r = scn.algebra["result"]
    # v_term = mg/b = 1*(-10)/0.5 = -20 ; τ = m/b = 2
    assert math.isclose(r["terminal_velocity"]["value"], -20.0, rel_tol=1e-9)
    assert math.isclose(r["time_constant"]["value"], 2.0, rel_tol=1e-9)


def test_drag_velocity_limit_is_terminal():
    t, tau, v0, g = drag.t, drag.tau, drag.v0, drag.g
    v = g * tau + (v0 - g * tau) * sp.exp(-t / tau)
    assert sp.limit(v, t, sp.oo) == g * tau            # v → mg/b
    assert sp.simplify(sp.diff(v, t) - (g - v / tau)) == 0   # solves v' = g − v/τ
