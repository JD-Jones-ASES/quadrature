"""Cross-checks for electric potential energy — the area instrument on the radial axis (the electric twin of
gravity_pe): the area under the Coulomb force 1/r² to infinity converges to a finite separation energy."""

import math

import sympy as sp

from quadrature_producer.models import coulomb_pe

SPEC = {"id": "t", "parameters": {"k": 8.99e9, "q1": 2e-6, "q2": 2e-6, "R": 0.02, "r_window": 0.12}}


def test_builds_on_area_instrument_with_integral_proof():
    scn = coulomb_pe.build(SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "integral" and scn.area is not None
    assert scn.x_expr is None                                  # reuses the AreaPlot — no temporal stack
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "separation_is_finite", "uniform_field_echo"} <= keys


def test_results_match_hand_physics():
    r = coulomb_pe.build(SPEC).algebra["result"]
    k, q1, q2, R = 8.99e9, 2e-6, 2e-6, 0.02
    assert math.isclose(r["separation_energy"]["value"], k * q1 * q2 / R, rel_tol=1e-5)      # kq₁q₂/R
    assert math.isclose(r["pe_to_2R"]["value"], k * q1 * q2 / (2 * R), rel_tol=1e-5)         # kq₁q₂/2R
    assert math.isclose(r["initial_force"]["value"], k * q1 * q2 / R**2, rel_tol=1e-5)       # kq₁q₂/R²
    # reaching 2R captures exactly half of the total separation energy (the inverse-square geometry)
    assert math.isclose(r["pe_to_2R"]["value"] * 2, r["separation_energy"]["value"], rel_tol=1e-9)


def test_area_under_inverse_square_converges():
    r, k, q1, q2, R = coulomb_pe.r, coulomb_pe.k, coulomb_pe.q1, coulomb_pe.q2, coulomb_pe.R
    w = sp.Symbol("w", positive=True)
    U = sp.integrate(k * q1 * q2 / w**2, (w, R, r))           # ∫_R^r F dr'
    assert sp.simplify(sp.diff(U, r) - k * q1 * q2 / r**2) == 0     # U'(r) = F(r) (FTC)
    assert sp.simplify(sp.limit(U, r, sp.oo) - k * q1 * q2 / R) == 0   # finite separation energy


def test_integrand_and_pe_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    a = coulomb_pe.build(SPEC).area
    amap = {s: parse_unit(uu, "t") for s, uu in a.unit_map.items()}
    check_homogeneous(a.f_expr, amap, "t: F(r)")             # kq₁q₂/r² → N
    check_homogeneous(a.g_expr, amap, "t: ΔU")              # kq₁q₂(1/R−1/r) → J
