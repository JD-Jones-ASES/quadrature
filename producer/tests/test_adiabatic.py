"""Independent cross-checks for the adiabatic-work (regime-3, area-instrument) model — the integral
instrument on the VOLUME axis (ADR-0014) along the adiabat PVγ = const, reusing the engine unchanged."""

import math

import sympy as sp

from quadrature_producer.models import adiabatic

SPEC = {"id": "t", "parameters": {"P1": 1e5, "V1": 1e-3, "V2": 3e-3, "gamma": 1.4, "v_window": 3.45e-3}}


def test_builds_on_the_area_instrument_with_integral_proof():
    scn = adiabatic.build(SPEC)
    assert scn.regime == 3
    assert scn.proof["kind"] == "integral" and scn.proof["holds"]
    assert scn.x_expr is None and scn.area is not None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "adiabatic_falls_out", "isobaric_echo"} <= keys


def test_results_match_hand_thermodynamics():
    r = adiabatic.build(SPEC).algebra["result"]
    P1, V1, V2, g = 1e5, 1e-3, 3e-3, 1.4
    P2 = P1 * (V1 / V2) ** g
    W = (P1 * V1 - P2 * V2) / (g - 1)                          # ≈ 89 J
    assert math.isclose(r["final_pressure"]["value"], P2, rel_tol=1e-6)
    assert math.isclose(r["adiabatic_work"]["value"], W, rel_tol=1e-6)
    # adiabatic work is LESS than the constant-pressure rectangle (pressure falls steeply)
    assert r["adiabatic_work"]["value"] < r["isobaric_rectangle"]["value"]
    # the gas cools: T2/T1 = (V1/V2)^(γ-1) < 1
    assert math.isclose(r["temperature_ratio"]["value"], (V1 / V2) ** (g - 1), rel_tol=1e-5)
    assert r["temperature_ratio"]["value"] < 1


def test_adiabatic_work_recovers_the_textbook_formula_independently():
    V, gamma, P1, V1 = adiabatic.V, adiabatic.gamma, adiabatic.P1, adiabatic.V1
    w, V2 = sp.Symbol("w", positive=True), sp.Symbol("V2x", positive=True)
    P = P1 * (V1 / V) ** gamma
    W = sp.integrate(P1 * V1**gamma * w ** (-gamma), (w, V1, V2), conds="none")   # ∫ P dV
    P2 = P.subs(V, V2)
    assert sp.simplify(W - (P1 * V1 - P2 * V2) / (gamma - 1)) == 0  # textbook closed form


def test_pressure_and_work_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    scn = adiabatic.build(SPEC)
    a = scn.area
    amap = {s: parse_unit(uu, "t") for s, uu in a.unit_map.items()}
    check_homogeneous(a.f_expr, amap, "t: P")                 # P → Pa
    check_homogeneous(a.g_expr, amap, "t: W")                 # W → J
