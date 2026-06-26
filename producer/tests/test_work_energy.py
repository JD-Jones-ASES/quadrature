"""Independent cross-checks for the work-energy (regime-2, area-instrument) model — the integral off the
time axis (ADR-0014). These verify the physics by hand, separately from the producer's own proof block."""

import math

import sympy as sp

from quadrature_producer.models import work_energy

SPEC = {"id": "t", "parameters": {"m": 2, "b": 8, "d": 1.5, "x_window": 2.0}}


def test_builds_with_area_and_integral_proof():
    scn = work_energy.build(SPEC)
    assert scn.regime == 2
    assert scn.proof["kind"] == "integral" and scn.proof["holds"]
    assert scn.x_expr is None and scn.area is not None          # no temporal stack; it is an area instrument
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "work_energy", "constant_force_echo"} <= keys


def test_results_match_hand_physics():
    r = work_energy.build(SPEC).algebra["result"]
    # F(x)=bx, d=1.5, b=8, m=2  ->  W=½bd²=9 J,  v=√(b/m)d=3 m/s,  Fmax=bd=12 N,  KE=W
    assert math.isclose(r["work_done"]["value"], 0.5 * 8 * 1.5**2, rel_tol=1e-9)        # 9 J
    assert math.isclose(r["kinetic_energy"]["value"], r["work_done"]["value"], rel_tol=1e-12)
    assert math.isclose(r["final_speed"]["value"], math.sqrt(8 / 2) * 1.5, rel_tol=1e-9)  # 3 m/s
    assert math.isclose(r["max_force"]["value"], 8 * 1.5, rel_tol=1e-9)                 # 12 N


def test_work_is_the_integral_of_force_independently():
    u, b, m = work_energy.u, work_energy.b, work_energy.m
    w = sp.Symbol("w", nonnegative=True)
    W = sp.integrate(b * w, (w, 0, u))                  # ∫₀ˣ F dw
    F = b * u
    assert sp.simplify(sp.diff(W, u) - F) == 0          # FTC: W'(x) = F(x)
    v = sp.sqrt(2 * W / m)
    assert sp.simplify(sp.Rational(1, 2) * m * v**2 - W) == 0   # work–energy theorem: ½mv² = W


def test_area_instrument_is_dimensionally_clean_and_js_emittable():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    from quadrature_producer.emit import closed_form_area, closed_form_params_area
    scn = work_energy.build(SPEC)
    a = scn.area
    amap = {s: parse_unit(uu, "t") for s, uu in a.unit_map.items()}
    check_homogeneous(a.f_expr, amap, "t: F")           # N
    check_homogeneous(a.g_expr, amap, "t: W")           # J — raises if not homogeneous
    cf = closed_form_area(a)
    assert set(cf) == {"f", "g"} and "u" in closed_form_params_area(a)
