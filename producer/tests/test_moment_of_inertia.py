"""Independent cross-checks for the moment-of-inertia (regime-2, area-instrument) model — the integral
instrument on the mass-distribution axis (ADR-0014): I = ∫r² dm, reusing the engine with no new machinery."""

import math

import sympy as sp

from quadrature_producer.models import moment_of_inertia

SPEC = {"id": "t", "parameters": {"M": 2, "L": 1.2, "r_window": 1.42}}


def test_builds_on_the_area_instrument_with_integral_proof():
    scn = moment_of_inertia.build(SPEC)
    assert scn.regime == 2
    assert scn.proof["kind"] == "integral" and scn.proof["holds"]
    assert scn.x_expr is None and scn.area is not None        # reuses the AreaPlot — no temporal stack
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "rod_falls_out", "hoop_echo"} <= keys


def test_results_match_hand_rotation():
    r = moment_of_inertia.build(SPEC).algebra["result"]
    M, L = 2, 1.2
    assert math.isclose(r["moment_of_inertia"]["value"], M * L**2 / 3, rel_tol=1e-9)   # ⅓ML² = 0.96
    assert math.isclose(r["hoop_value"]["value"], M * L**2, rel_tol=1e-9)              # ML² = 2.88
    assert math.isclose(r["linear_density"]["value"], M / L, rel_tol=1e-5)
    # the rod's moment is exactly one third of the all-mass-at-the-tip value
    assert math.isclose(r["moment_of_inertia"]["value"] * 3, r["hoop_value"]["value"], rel_tol=1e-9)


def test_inertia_is_the_integral_of_r_squared_independently():
    r, M, L = moment_of_inertia.r, moment_of_inertia.M, moment_of_inertia.L
    w = sp.Symbol("w", nonnegative=True)
    lam = M / L
    I = sp.integrate(lam * w**2, (w, 0, r))                   # ∫ λ r² dr
    assert sp.simplify(sp.diff(I, r) - lam * r**2) == 0       # dI/dr = λr² (FTC)
    assert sp.simplify(I.subs(r, L) - M * L**2 / 3) == 0      # rod about its end = ⅓ML²


def test_integrand_and_inertia_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    scn = moment_of_inertia.build(SPEC)
    a = scn.area
    amap = {s: parse_unit(uu, "t") for s, uu in a.unit_map.items()}
    check_homogeneous(a.f_expr, amap, "t: dI/dr")            # λr² → kg·m
    check_homogeneous(a.g_expr, amap, "t: I")               # λr³/3 → kg·m²
