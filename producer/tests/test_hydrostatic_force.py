"""Cross-checks for the hydrostatic force on a wall — the area instrument on the depth axis (opens fluids):
the force is the triangular area under the linearly-growing pressure, and the algebra's average-pressure
formula is exactly that area."""

import math

import sympy as sp

from quadrature_producer.models import hydrostatic_force

SPEC = {"id": "t", "parameters": {"rho": 1000, "g": 10, "w": 5, "H": 4, "h_window": 4.8}}


def test_builds_on_area_instrument_with_integral_proof():
    scn = hydrostatic_force.build(SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "integral" and scn.area is not None
    assert scn.x_expr is None                                  # reuses the AreaPlot — no temporal stack
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "avg_pressure_falls_out", "uniform_pressure_echo"} <= keys


def test_results_match_hand_physics():
    r = hydrostatic_force.build(SPEC).algebra["result"]
    rho, g, w, H = 1000, 10, 5, 4
    assert math.isclose(r["wall_force"]["value"], 0.5 * rho * g * w * H**2, rel_tol=1e-9)     # ½ρgwH² = 400 kN
    assert math.isclose(r["bottom_pressure"]["value"], rho * g * H, rel_tol=1e-9)            # ρgH = 40 kPa
    assert math.isclose(r["avg_pressure"]["value"], rho * g * H / 2, rel_tol=1e-9)           # ½ρgH = 20 kPa
    # the uniform-(bottom-pressure) rectangle is exactly twice the real triangular force
    assert math.isclose(r["uniform_rectangle"]["value"], 2 * r["wall_force"]["value"], rel_tol=1e-9)


def test_force_is_the_integral_of_pressure_times_width():
    h, rho, g, w = hydrostatic_force.h, hydrostatic_force.rho, hydrostatic_force.g, hydrostatic_force.w
    s = sp.Symbol("s", nonnegative=True)
    F = sp.integrate(rho * g * w * s, (s, 0, h))             # ∫ ρg w h' dh'
    assert sp.simplify(sp.diff(F, h) - rho * g * w * h) == 0    # dF/dh = ρg w h (FTC)
    assert sp.simplify(F - rho * g * w * h**2 / 2) == 0         # = ½ρgwh²
    # average pressure × area is exactly the integral (only because P is linear in h)
    assert sp.simplify(F - (rho * g * h / 2) * (w * h)) == 0


def test_integrand_and_force_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    a = hydrostatic_force.build(SPEC).area
    amap = {s: parse_unit(uu, "t") for s, uu in a.unit_map.items()}
    check_homogeneous(a.f_expr, amap, "t: dF/dh")           # ρg w h → N/m
    check_homogeneous(a.g_expr, amap, "t: F")              # ½ρg w h² → N
