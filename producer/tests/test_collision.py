"""Cross-checks for the collision model — the before/after collision-bars instrument (kind:"collision"):
momentum is conserved at every coefficient of restitution, kinetic energy only at e = 1, and the lost KE is
½μ(1−e²)(Δv)²."""

import math

import sympy as sp

from quadrature_producer.models import collision as col

SPEC = {"id": "t", "parameters": {"m1": 2, "m2": 1, "v1": 3, "v2": 0}}


def test_builds_on_collision_instrument_with_governing_proof():
    scn = col.build(SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "governing"
    assert scn.collision is not None and scn.energy is None and scn.area is None and scn.x_expr is None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"momentum_conserved", "restitution", "ke_loss",
            "elastic_conserves_ke", "inelastic_common_velocity"} <= keys


def test_momentum_conserved_for_every_restitution():
    e, m1, m2, v1, v2 = col.e, col.m1, col.m2, col.v1, col.v2
    v1f, v2f = col._finals()
    # total momentum after == total momentum before, identically in e (and all masses/velocities)
    assert sp.simplify((m1 * v1f + m2 * v2f) - (m1 * v1 + m2 * v2)) == 0
    # the finals obey the restitution relation: separation = e · approach
    assert sp.simplify((v2f - v1f) - e * (v1 - v2)) == 0


def test_kinetic_energy_loss_is_reduced_mass_formula():
    e, m1, m2, v1, v2 = col.e, col.m1, col.m2, col.v1, col.v2
    v1f, v2f = col._finals()
    mu = m1 * m2 / (m1 + m2)
    ke_before = sp.Rational(1, 2) * m1 * v1**2 + sp.Rational(1, 2) * m2 * v2**2
    ke_after = sp.Rational(1, 2) * m1 * v1f**2 + sp.Rational(1, 2) * m2 * v2f**2
    loss = sp.Rational(1, 2) * mu * (1 - e**2) * (v1 - v2)**2
    assert sp.simplify((ke_before - ke_after) - loss) == 0          # the lost-energy identity
    assert sp.simplify((ke_after - ke_before).subs(e, 1)) == 0      # elastic conserves KE
    # perfectly inelastic: the bodies share the centre-of-mass velocity
    v_cm = (m1 * v1 + m2 * v2) / (m1 + m2)
    assert sp.simplify(v1f.subs(e, 0) - v_cm) == 0
    assert sp.simplify(v2f.subs(e, 0) - v_cm) == 0


def test_results_match_hand_physics():
    r = col.build(SPEC).algebra["result"]
    # elastic 2 kg @ 3 m/s into 1 kg at rest: v1' = 1, v2' = 4  (KE conserved)
    assert math.isclose(r["v1_elastic"]["value"], 1.0, rel_tol=1e-9)
    assert math.isclose(r["v2_elastic"]["value"], 4.0, rel_tol=1e-9)
    # perfectly inelastic: common velocity 6/3 = 2 m/s; KE 9 → 6, so 3 J lost
    assert math.isclose(r["v_inelastic"]["value"], 2.0, rel_tol=1e-9)
    assert math.isclose(r["ke_lost_inelastic"]["value"], 3.0, rel_tol=1e-9)


def test_finals_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    c = col.build(SPEC).collision
    cmap = {s: parse_unit(uu, "t") for s, uu in c.unit_map.items()}
    check_homogeneous(c.v1f_expr, cmap, "t: v1'")            # → m/s
    check_homogeneous(c.v2f_expr, cmap, "t: v2'")            # → m/s


# Head-on, opposite signs: the second collision lesson (m1=1@+4 meets m2=2@−2, so the total momentum is
# exactly zero). The closed forms already cover negative velocities; this pins the hand-physics of the
# striking case — a perfectly inelastic collision brings the pair to a DEAD STOP, losing ALL the kinetic energy.
HEADON = {"id": "h", "parameters": {"m1": 1, "m2": 2, "v1": 4, "v2": -2}}


def test_head_on_opposite_signs_dead_stop_and_total_loss():
    r = col.build(HEADON).algebra["result"]
    assert math.isclose(r["v1_elastic"]["value"], -4.0, abs_tol=1e-9)   # block 1 rebounds left
    assert math.isclose(r["v2_elastic"]["value"], 2.0, abs_tol=1e-9)    # block 2 rebounds right
    assert math.isclose(r["v_inelastic"]["value"], 0.0, abs_tol=1e-9)   # total p = 0 → common velocity 0
    # KE before = ½·1·4² + ½·2·2² = 8 + 4 = 12 J, and it is ALL lost when they stick (final KE is 0)
    assert math.isclose(r["ke_lost_inelastic"]["value"], 12.0, abs_tol=1e-9)


def test_total_momentum_is_zero_and_conserved_head_on():
    scn = col.build(HEADON)
    # every momentum_conserved check holds; and here the conserved total is identically zero
    e, m1, m2, v1, v2 = col.e, col.m1, col.m2, col.v1, col.v2
    v1f, v2f = col._finals()
    subs = {m1: 1, m2: 2, v1: 4, v2: -2}
    assert sp.simplify((m1 * v1f + m2 * v2f).subs(subs)) == 0   # net momentum is zero for all e
