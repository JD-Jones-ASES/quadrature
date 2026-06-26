"""Independent cross-checks for the PV-work (regime-3, area-instrument) model — the integral instrument on
the VOLUME axis (ADR-0014), reusing the engine with no new machinery."""

import math

import sympy as sp

from quadrature_producer.models import pv_work

SPEC = {"id": "t", "parameters": {"n": 1, "T": 300, "V1": 0.025, "V2": 0.075, "v_window": 0.084}}


def test_builds_on_the_area_instrument_with_integral_proof():
    scn = pv_work.build(SPEC)
    assert scn.regime == 3                                    # algebra-only domain, calculus underpinning shown
    assert scn.proof["kind"] == "integral" and scn.proof["holds"]
    assert scn.x_expr is None and scn.area is not None        # reuses the AreaPlot — no temporal stack
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "isothermal_falls_out", "isobaric_echo"} <= keys


def test_results_match_hand_thermodynamics():
    r = pv_work.build(SPEC).algebra["result"]
    R = 8.3145
    W = 1 * R * 300 * math.log(0.075 / 0.025)                 # nRT ln(V2/V1)
    assert math.isclose(r["isothermal_work"]["value"], W, rel_tol=1e-4)            # ≈ 2741 J
    assert math.isclose(r["initial_pressure"]["value"], R * 300 / 0.025, rel_tol=1e-4)  # P1 = nRT/V1
    assert math.isclose(r["final_pressure"]["value"], R * 300 / 0.075, rel_tol=1e-4)    # P2 = nRT/V2
    # the isothermal work is LESS than the P1·ΔV rectangle (pressure falls as it expands)
    assert r["isothermal_work"]["value"] < r["rectangle_work"]["value"]


def test_work_is_the_integral_of_pressure_independently():
    V, T, a = pv_work.V, pv_work.T, pv_work.a
    w = sp.Symbol("w", positive=True)
    V1 = pv_work.V1
    P = a * T / V
    W = sp.integrate(a * T / w, (w, V1, V))                   # ∫ P dV
    assert sp.simplify(sp.diff(W, V) - P) == 0               # dW/dV = P (FTC)
    assert sp.simplify(W - a * T * sp.log(V / V1)) == 0      # closed form is nRT ln(V/V1)


def test_pressure_is_dimensionally_pascals():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    scn = pv_work.build(SPEC)
    a = scn.area
    amap = {s: parse_unit(uu, "t") for s, uu in a.unit_map.items()}
    check_homogeneous(a.f_expr, amap, "t: P")               # P → Pa; raises if not homogeneous
