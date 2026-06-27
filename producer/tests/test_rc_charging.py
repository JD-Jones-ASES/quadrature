"""Cross-checks for the RC-charging model — the N-panel temporal stack (a 2-panel Q–t / I–t stack): the
current is the slope of the charge, the charge solves the RC equation, and the time constant is RC."""

import math

import sympy as sp

from quadrature_producer.models import rc_charging as rc

SPEC = {"id": "t", "parameters": {"R": 1000, "C": 0.001, "V": 10}}


def test_builds_a_two_panel_stack_with_governing_proof():
    scn = rc.build(SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "governing"
    assert scn.panels is not None and len(scn.panels) == 2
    assert [p.key for p in scn.panels] == ["Q", "I"]
    assert scn.x_expr is None and scn.area is None and scn.energy is None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"current_is_slope", "governing_eqn", "charge_is_integral",
            "time_constant", "steady_state"} <= keys


def test_current_is_the_slope_of_charge_and_solves_the_rc_equation():
    t, R, C, V = rc.t, rc.R, rc.C, rc.V
    Q = C * V * (1 - sp.exp(-t / (R * C)))
    I = V / R * sp.exp(-t / (R * C))
    assert sp.simplify(I - sp.diff(Q, t)) == 0                       # I = dQ/dt
    assert sp.simplify(R * sp.diff(Q, t) + Q / C - V) == 0           # the RC ODE (Kirchhoff)
    w = sp.Symbol("w", nonnegative=True)
    assert sp.simplify(Q - sp.integrate(I.subs(t, w), (w, 0, t))) == 0   # Q is the area under I
    assert sp.limit(Q, t, sp.oo) == C * V                           # steady state → CV
    assert sp.limit(I, t, sp.oo) == 0                               # steady state → no current


def test_results_match_hand_physics():
    r = rc.build(SPEC).algebra["result"]
    R_, C_, V_ = 1000, 0.001, 10
    assert math.isclose(r["time_constant"]["value"], R_ * C_, rel_tol=1e-9)        # τ = 1 s
    assert math.isclose(r["final_charge"]["value"], C_ * V_, rel_tol=1e-9)         # CV = 0.01 C
    assert math.isclose(r["initial_current"]["value"], V_ / R_, rel_tol=1e-9)      # V/R = 0.01 A
    assert math.isclose(r["charge_at_tau"]["value"], C_ * V_ * (1 - math.exp(-1)), rel_tol=1e-4)  # 63% (6-dp rounded)


def test_panels_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    scn = rc.build(SPEC)
    umap = {s: parse_unit(u, "t") for s, u in scn.unit_map.items()}
    for p in scn.panels:
        check_homogeneous(p.expr, umap, f"t: {p.key}")     # Q → C, I → A
