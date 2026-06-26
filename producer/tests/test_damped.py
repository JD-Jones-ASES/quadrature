"""Independent cross-checks for the damped-oscillator (regime-2, sampled) model."""

import sympy as sp

from quadrature_producer.models import damped_shm as d

SPEC = {"id": "t", "parameters": {"m": 1, "k": 16, "x0": 1, "v0": 0, "b_values": [2, 8, 14]}}


def test_damped_proof_holds():
    scn = d.build(SPEC)
    assert scn.proof["kind"] == "governing" and scn.proof["holds"]
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"underdamped_solves", "critical_solves", "overdamped_solves", "energy_dissipates"} <= keys


def test_damped_frames_classify_by_regime():
    scn = d.build(SPEC)
    labels = [f.label for f in scn.sampled["frames"]]
    assert "underdamped" in labels[0] and "critically" in labels[1] and "overdamped" in labels[2]
    assert scn.constants_export["b_critical"] == 2 * (16 * 1) ** 0.5  # 8


def test_underdamped_form_solves_ode_and_dissipates():
    t, g, wd, x0, v0 = d.t, d.gamma, d.wd, d.x0, d.v0
    x = sp.exp(-g * t) * (x0 * sp.cos(wd * t) + (v0 + g * x0) / wd * sp.sin(wd * t))
    assert sp.simplify(sp.diff(x, t, 2) + 2 * g * sp.diff(x, t) + (wd**2 + g**2) * x) == 0
    v = sp.diff(x, t)
    E = v**2 / 2 + (wd**2 + g**2) * x**2 / 2
    assert sp.simplify(sp.diff(E, t) + 2 * g * v**2) == 0   # dE/dt = -2γv² (= -b v²/m)
