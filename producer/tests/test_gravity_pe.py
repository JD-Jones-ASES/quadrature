"""Cross-checks for gravitational potential energy — the area instrument on the radial axis, where the area
under 1/r² to infinity converges to a finite escape energy."""

import math

import sympy as sp

from quadrature_producer.models import gravity_pe

SPEC = {"id": "t", "parameters": {"mu": 4e14, "R": 6.4e6, "m": 1, "r_window": 4.0e7}}


def test_builds_on_area_instrument_with_integral_proof():
    scn = gravity_pe.build(SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "integral" and scn.area is not None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "escape_is_finite", "flat_earth_echo"} <= keys


def test_results_match_hand_physics():
    r = gravity_pe.build(SPEC).algebra["result"]
    mu, R = 4e14, 6.4e6
    assert math.isclose(r["escape_energy"]["value"], mu / R, rel_tol=1e-5)          # GMm/R
    assert math.isclose(r["pe_to_2R"]["value"], mu / (2 * R), rel_tol=1e-5)         # GMm/2R
    assert math.isclose(r["surface_force"]["value"], mu / R**2, rel_tol=1e-5)       # = g ≈ 9.77 N


def test_area_under_inverse_square_converges():
    r, mu, m, R = gravity_pe.r, gravity_pe.mu, gravity_pe.m, gravity_pe.R
    w = sp.Symbol("w", positive=True)
    U = sp.integrate(mu * m / w**2, (w, R, r))             # ∫_R^r F dr'
    assert sp.simplify(sp.diff(U, r) - mu * m / r**2) == 0  # U'(r) = F(r)
    assert sp.simplify(sp.limit(U, r, sp.oo) - mu * m / R) == 0   # finite escape energy
