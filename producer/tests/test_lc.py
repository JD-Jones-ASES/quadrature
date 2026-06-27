"""Cross-checks for the LC-oscillation model — the 2-panel Q–t / I–t stack: the current is the slope of the
charge, the charge solves the LC equation, energy is conserved, and the period is 2π√(LC)."""

import math

import sympy as sp

from quadrature_producer.models import lc_oscillation as lc

SPEC = {"id": "t", "parameters": {"L": 0.01, "C": 0.0001, "Q0": 0.01}}


def test_builds_a_two_panel_stack_with_governing_proof():
    scn = lc.build(SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "governing"
    assert scn.panels is not None and len(scn.panels) == 2
    assert [p.key for p in scn.panels] == ["Q", "I"]
    assert scn.x_expr is None and scn.area is None and scn.energy is None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"current_is_slope", "governing_eqn", "energy_conserved",
            "period", "quarter_phase"} <= keys


def test_current_is_slope_charge_solves_lc_equation_and_energy_is_conserved():
    t, L, C, Q0 = lc.t, lc.L, lc.C, lc.Q0
    omega = 1 / sp.sqrt(L * C)
    Q = Q0 * sp.cos(omega * t)
    I = sp.diff(Q, t)
    assert sp.simplify(I - sp.diff(Q, t)) == 0                       # I = dQ/dt
    assert sp.simplify(L * sp.diff(Q, t, 2) + Q / C) == 0            # the LC ODE: L Q'' + Q/C = 0
    energy = Q**2 / (2 * C) + L * I**2 / 2
    assert sp.simplify(energy - Q0**2 / (2 * C)) == 0                # total energy is the initial Q0²/2C
    assert sp.simplify(sp.diff(energy, t)) == 0                      # ...and constant in time
    T = 2 * sp.pi * sp.sqrt(L * C)
    assert sp.simplify(Q.subs(t, t + T) - Q) == 0                    # period T = 2π√(LC)
    assert sp.simplify(Q.subs(t, T / 4)) == 0                        # quarter period: capacitor empty


def test_results_match_hand_physics():
    r = lc.build(SPEC).algebra["result"]
    L_, C_, Q0_ = 0.01, 0.0001, 0.01
    omega = 1 / math.sqrt(L_ * C_)
    assert math.isclose(r["angular_frequency"]["value"], omega, rel_tol=1e-9)        # ω = 1000 rad/s
    assert math.isclose(r["period"]["value"], 2 * math.pi * math.sqrt(L_ * C_), rel_tol=1e-4)  # ≈ 6.28 ms (6-dp rounded)
    assert math.isclose(r["peak_current"]["value"], Q0_ * omega, rel_tol=1e-9)       # Q0·ω = 10 A
    assert math.isclose(r["total_energy"]["value"], Q0_**2 / (2 * C_), rel_tol=1e-9)  # Q0²/2C = 0.5 J


def test_panels_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    scn = lc.build(SPEC)
    umap = {s: parse_unit(u, "t") for s, u in scn.unit_map.items()}
    for p in scn.panels:
        check_homogeneous(p.expr, umap, f"t: {p.key}")     # Q → C, I → A
