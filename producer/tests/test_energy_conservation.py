"""Cross-checks for the energy-conservation model — the energy-exchange instrument (kind:"energy"): KE and PE
trade as the object descends, their sum is constant, and the speed is path-independent."""

import math

import sympy as sp

from quadrature_producer.models import energy_conservation as ec

SPEC = {"id": "t", "parameters": {"m": 2, "g": 10, "H": 20}}


def test_builds_on_energy_instrument_with_governing_proof():
    scn = ec.build(SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "governing"
    assert scn.energy is not None and scn.area is None and scn.x_expr is None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"energy_constant", "conservation_law", "speed_falls_out", "work_energy_root"} <= keys


def test_results_match_hand_physics():
    r = ec.build(SPEC).algebra["result"]
    m, g, H = 2, 10, 20
    assert math.isclose(r["total_energy"]["value"], m * g * H, rel_tol=1e-9)            # mgH = 400 J
    assert math.isclose(r["bottom_speed"]["value"], math.sqrt(2 * g * H), rel_tol=1e-9) # √(2gH) = 20 m/s
    assert math.isclose(r["ke_at_half"]["value"], 0.5 * m * g * H, rel_tol=1e-9)        # ½mgH = 200 J
    assert math.isclose(r["pe_at_top"]["value"], m * g * H, rel_tol=1e-9)


def test_energy_is_conserved_at_every_height_independently():
    h, m, g, H = ec.h, ec.m, ec.g, ec.H
    ke, pe = m * g * (H - h), m * g * h
    assert sp.simplify((ke + pe) - m * g * H) == 0          # total constant
    assert sp.simplify(sp.diff(ke + pe, h)) == 0            # dE/dh = 0
    v = sp.sqrt(2 * g * (H - h))
    assert sp.simplify(sp.Rational(1, 2) * m * v**2 - ke) == 0   # ½mv² = KE
    w = sp.Symbol("w", nonnegative=True)
    assert sp.simplify(ke - sp.integrate(m * g, (w, h, H))) == 0  # KE is the work integral (path-independent)


def test_energy_bars_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    en = ec.build(SPEC).energy
    emap = {s: parse_unit(uu, "t") for s, uu in en.unit_map.items()}
    check_homogeneous(en.ke_expr, emap, "t: KE")           # mg(H−h) → J
    check_homogeneous(en.pe_expr, emap, "t: PE")           # mgh → J
