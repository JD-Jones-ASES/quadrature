"""Cross-checks for the isobaric PV-work model — the area instrument with a constant integrand: the work is the
rectangle W = P·ΔV, the simplest quadrature (the algebra formula IS the integral evaluated)."""

import math

import sympy as sp

from quadrature_producer.models import isobaric_work as ib


SPEC = {"id": "t", "parameters": {"P": 100000, "V1": 0.001, "V2": 0.003}}


def test_builds_an_area_scenario_with_integral_proof():
    scn = ib.build(SPEC)
    assert scn.regime == 3 and scn.proof["kind"] == "integral"
    assert scn.area is not None
    assert scn.x_expr is None and scn.panels is None and scn.energy is None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "rectangle_quadrature"} <= keys


def test_work_is_the_rectangle_and_its_slope_is_the_pressure():
    V, P, V1 = ib.V, ib.P, ib.V1
    f = P                       # constant integrand (the height)
    g = P * (V - V1)            # accumulated work (the rectangle so far)
    assert sp.simplify(sp.diff(g, V) - f) == 0                       # dW/dV = P
    w = sp.Symbol("w", positive=True)
    assert sp.simplify(g - sp.integrate(f.subs(V, w), (w, V1, V))) == 0   # W = ∫P dV
    Vb = sp.Symbol("Vb", positive=True)
    assert sp.simplify(sp.integrate(P, (w, V1, Vb)) - P * (Vb - V1)) == 0  # constant integrand → rectangle


def test_results_match_hand_physics():
    r = ib.build(SPEC).algebra["result"]
    P_, V1_, V2_ = 100000, 0.001, 0.003
    assert math.isclose(r["isobaric_work"]["value"], P_ * (V2_ - V1_), rel_tol=1e-9)   # 200 J
    assert math.isclose(r["pressure"]["value"], P_, rel_tol=1e-9)
    assert math.isclose(r["volume_change"]["value"], V2_ - V1_, rel_tol=1e-9)          # 0.002 m³


def test_area_curves_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    scn = ib.build(SPEC)
    amap = {s: parse_unit(u, "t") for s, u in scn.area.unit_map.items()}
    check_homogeneous(scn.area.f_expr, amap, "t: P(V)")   # Pa
    check_homogeneous(scn.area.g_expr, amap, "t: W(V)")   # J
