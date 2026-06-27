"""Cross-checks for the charged-disk field — the area instrument on the ring-radius axis (a continuous-charge
field, the disk generalisation of the line charge): the on-axis field is the area under the ring contributions,
and it bridges BOTH algebra limits — the point charge kQ/z² far away and the infinite sheet σ/2ε₀ for a huge disk."""

import math

import sympy as sp

from quadrature_producer.models import disk_field as df

SPEC = {"id": "t", "parameters": {"k": 8990000000, "sigma_nc": 100, "z": 0.1, "R": 0.3}}


def test_builds_on_area_instrument_with_integral_proof():
    scn = df.build(SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "integral" and scn.area is not None
    assert scn.x_expr is None                                  # reuses the AreaPlot — no temporal stack
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"ftc_slope", "area_is_integral", "point_charge_limit", "infinite_sheet_limit"} <= keys


def test_results_match_hand_physics():
    r = df.build(SPEC).algebra["result"]
    k, sig, z, R = 8.99e9, 100e-9, 0.1, 0.3
    twopiks = 2 * math.pi * k * sig
    total = twopiks * (1 - z / math.sqrt(z**2 + R**2))
    assert math.isclose(r["total_field"]["value"], total, rel_tol=1e-6)                 # ≈ 3862 N/C
    assert math.isclose(r["sheet_approx"]["value"], twopiks, rel_tol=1e-6)              # σ/2ε₀ ≈ 5649 N/C
    assert math.isclose(r["point_charge_approx"]["value"], k * sig * math.pi * R**2 / z**2, rel_tol=1e-6)  # ≈ 25420
    # a finite disk at finite distance sits BELOW both limiting estimates
    assert r["total_field"]["value"] < r["sheet_approx"]["value"]
    assert r["total_field"]["value"] < r["point_charge_approx"]["value"]


def test_field_is_the_ring_integral_and_bridges_both_limits():
    r, k, sig, z, R, NANO = df.r, df.k, df.sigma, df.z, df.R, df._NANO
    w = sp.Symbol("w", positive=True)
    f = 2 * sp.pi * k * sig * NANO * z * r / (z**2 + r**2)**sp.Rational(3, 2)
    g = sp.integrate(f.subs(r, w), (w, 0, r))                                   # ∫_0^r ring contributions
    assert sp.simplify(sp.diff(g, r) - f) == 0                                  # dE/dr = f (FTC)
    total = g.subs(r, R)
    assert sp.simplify(total - 2 * sp.pi * k * sig * NANO * (1 - z / sp.sqrt(z**2 + R**2))) == 0
    assert sp.simplify(sp.limit(total * z**2, z, sp.oo) - k * sig * NANO * sp.pi * R**2) == 0   # far → kQ/z²
    assert sp.simplify(sp.limit(total, R, sp.oo) - 2 * sp.pi * k * sig * NANO) == 0             # large → σ/2ε₀


def test_integrand_and_field_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    a = df.build(SPEC).area
    amap = {s: parse_unit(uu, "t") for s, uu in a.unit_map.items()}
    check_homogeneous(a.f_expr, amap, "t: dE/dr")           # → N/C/m
    check_homogeneous(a.g_expr, amap, "t: E")              # → N/C
