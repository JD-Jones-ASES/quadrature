"""Independent cross-checks for the capacitor-energy (regime-2, area-instrument) model — the integral
instrument on the CHARGE axis (ADR-0014), opening E&M with no new engine machinery."""

import math

import sympy as sp

from quadrature_producer.models import capacitor_energy

SPEC = {"id": "t", "parameters": {"C": 5e-4, "Q": 0.1, "q_window": 0.12}}


def test_builds_on_the_area_instrument_with_integral_proof():
    scn = capacitor_energy.build(SPEC)
    assert scn.regime == 2
    assert scn.proof["kind"] == "integral" and scn.proof["holds"]
    assert scn.x_expr is None and scn.area is not None        # reuses the AreaPlot — no temporal stack
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "half_cv2", "constant_voltage_echo"} <= keys


def test_results_match_hand_electrostatics():
    r = capacitor_energy.build(SPEC).algebra["result"]
    C, Q = 5e-4, 0.1
    V = Q / C                                                  # 200 V
    U = Q**2 / (2 * C)                                         # ½CV² = 10 J
    assert math.isclose(r["final_voltage"]["value"], V, rel_tol=1e-9)
    assert math.isclose(r["energy_stored"]["value"], U, rel_tol=1e-9)
    assert math.isclose(r["final_charge"]["value"], Q, rel_tol=1e-9)
    # the battery does the full rectangle VQ — exactly twice the stored energy
    assert math.isclose(r["battery_work"]["value"], 2 * U, rel_tol=1e-9)


def test_energy_is_the_integral_of_voltage_independently():
    q, C = capacitor_energy.q, capacitor_energy.C
    w = sp.Symbol("w", nonnegative=True)
    Vq = q / C
    U = sp.integrate(w / C, (w, 0, q))                         # ∫ V dq
    assert sp.simplify(sp.diff(U, q) - Vq) == 0               # dU/dq = V (FTC)
    assert sp.simplify(U - q**2 / (2 * C)) == 0              # closed form is q²/2C


def test_voltage_and_energy_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    scn = capacitor_energy.build(SPEC)
    a = scn.area
    amap = {s: parse_unit(uu, "t") for s, uu in a.unit_map.items()}
    check_homogeneous(a.f_expr, amap, "t: V")                 # q/C → volts
    check_homogeneous(a.g_expr, amap, "t: U")                 # q²/2C → joules
