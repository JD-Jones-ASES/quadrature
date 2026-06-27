"""Cross-checks for the standing-wave model — the spatial mode instrument (ADR-0023): the harmonic shape solves
the wave equation, the fixed ends quantize the modes (sin(kL)=0), and f_n = nv/2L, λ_n = 2L/n."""

import math

import sympy as sp

from quadrature_producer.models import standing_wave as sw

SPEC = {"id": "t", "parameters": {"L": 1.0, "v": 120.0, "A": 1.0, "n_max": 5, "n_default": 3}}


def test_builds_standing_scenario_with_governing_proof():
    scn = sw.build(SPEC)
    assert scn.regime == 3 and scn.proof["kind"] == "governing"
    assert scn.standing is not None
    assert scn.x_expr is None and scn.area is None and scn.panels is None and scn.energy is None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"wave_equation", "fixed_ends", "superposition", "frequency", "wavelength"} <= keys
    assert len(scn.standing.modes) == 5


def test_mode_solves_wave_equation_and_satisfies_boundary_conditions():
    x, t, n, A, L, v = sw.x, sw.t, sw.n, sw.A, sw.L, sw.v
    k = n * sp.pi / L
    omega = v * k
    y = A * sp.sin(k * x) * sp.cos(omega * t)
    assert sp.simplify(sp.diff(y, t, 2) - v**2 * sp.diff(y, x, 2)) == 0   # solves the wave equation
    assert sp.simplify(y.subs(x, 0)) == 0                                 # left end pinned
    assert sp.simplify(y.subs(x, L)) == 0                                 # right end pinned (sin(nπ)=0, n integer)
    # a standing wave is two counter-propagating travelling waves superposed
    assert sp.simplify((A / 2) * (sp.sin(k * x - omega * t) + sp.sin(k * x + omega * t)) - y) == 0
    # the harmonics: f_n = nv/2L, λ_n = 2L/n
    assert sp.simplify(omega / (2 * sp.pi) - n * v / (2 * L)) == 0
    assert sp.simplify(2 * sp.pi / k - 2 * L / n) == 0


def test_harmonics_match_hand_physics():
    scn = sw.build(SPEC)
    r = scn.algebra["result"]
    L_, v_ = 1.0, 120.0
    assert math.isclose(r["fundamental_frequency"]["value"], v_ / (2 * L_), rel_tol=1e-9)   # 60 Hz
    assert math.isclose(r["fundamental_wavelength"]["value"], 2 * L_, rel_tol=1e-9)          # 2 m
    assert math.isclose(r["nth_frequency"]["value"], 3 * v_ / (2 * L_), rel_tol=1e-9)         # 180 Hz
    assert [m["f"] for m in scn.standing.modes] == [60, 120, 180, 240, 300]
    assert math.isclose(scn.standing.modes[0]["lam"], 2.0) and math.isclose(scn.standing.modes[4]["lam"], 0.4)


def test_y_is_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    scn = sw.build(SPEC)
    smap = {s: parse_unit(u, "t") for s, u in scn.standing.unit_map.items()}
    check_homogeneous(scn.standing.y_expr, smap, "t: y(x)")   # A·sin(dimensionless) → m
