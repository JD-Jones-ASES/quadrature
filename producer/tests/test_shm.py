"""Independent cross-checks for the SHM (regime-2) model."""

import math

import sympy as sp

from quadrature_producer.models import shm


def test_shm_builds_and_proof_holds():
    scn = shm.build({"id": "t", "parameters": {"m": 1, "k": 4, "x0": 0.3, "v0": 0}})
    assert scn.regime == 2 and scn.proof["kind"] == "governing" and scn.proof["holds"]
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"solves_eom", "ic_position", "energy_conserved", "period_falls_out"} <= keys


def test_shm_results_match_hand_physics():
    scn = shm.build({"id": "t", "parameters": {"m": 1, "k": 4, "x0": 0.3, "v0": 0}})
    r = scn.algebra["result"]
    assert math.isclose(r["angular_frequency"]["value"], math.sqrt(4 / 1), rel_tol=1e-9)  # ω=√(k/m)=2
    assert math.isclose(r["period"]["value"], 2 * math.pi / 2, rel_tol=1e-6)              # T=2π/ω=π
    assert math.isclose(r["amplitude"]["value"], 0.3, rel_tol=1e-9)                       # released from rest
    assert math.isclose(r["max_speed"]["value"], 0.3 * 2, rel_tol=1e-9)                   # ωA


def test_shm_solution_solves_the_ode_independently():
    t, om, x0, v0 = shm.t, shm.omega, shm.x0, shm.v0
    x = x0 * sp.cos(om * t) + (v0 / om) * sp.sin(om * t)
    assert sp.simplify(sp.diff(x, t, 2) + om**2 * x) == 0          # x'' = -ω²x
    E = sp.diff(x, t) ** 2 / 2 + om**2 * x**2 / 2
    assert sp.simplify(sp.diff(E, t)) == 0                          # energy conserved
