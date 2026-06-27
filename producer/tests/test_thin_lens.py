"""Cross-checks for the thin-lens model — the ray-diagram instrument (ADR-0024): the closed-form image distance
satisfies the thin-lens equation, the three principal-ray similar-triangle constructions all give the same
magnification (which IS the lens equation), and the hand-physics numbers come out (dᵢ = 3 m, m = −2)."""

import math

import pytest
import sympy as sp

from quadrature_producer import BuildError
from quadrature_producer.models import thin_lens as tl

SPEC = {"id": "t", "parameters": {"f": 1.0, "ho": 0.4, "do_default": 1.5,
                                  "do_min": 0.5, "do_max": 4.0, "ho_min": 0.2, "ho_max": 0.6}}


def test_builds_lens_scenario_with_governing_proof():
    scn = tl.build(SPEC)
    assert scn.regime == 3 and scn.proof["kind"] == "governing"
    assert scn.lens is not None
    assert scn.x_expr is None and scn.area is None and scn.panels is None and scn.standing is None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"lens_equation", "chief_ray", "parallel_ray_agrees", "focal_ray_agrees",
            "magnification_form"} <= keys
    assert scn.calculus["register_label"] == "Ray diagram"


def test_closed_form_satisfies_lens_equation_and_three_rays_agree():
    do, f, ho = tl.do, tl.f, tl.ho
    di = do * f / (do - f)
    m = -f / (do - f)
    # the closed-form di solves the thin-lens equation
    assert sp.simplify(1 / do + 1 / di - 1 / f) == 0
    # the three principal-ray constructions all give the same magnification
    chief = -di / do
    parallel = -(di - f) / f
    focal = -f / (do - f)
    assert sp.simplify(chief - parallel) == 0
    assert sp.simplify(chief - focal) == 0
    assert sp.simplify(m - chief) == 0
    # magnification in do, f alone
    assert sp.simplify(m - f / (f - do)) == 0


def test_numbers_match_hand_physics():
    scn = tl.build(SPEC)
    r = scn.algebra["result"]
    # f = 1, do = 1.5  ->  di = do f/(do-f) = 3 ; m = -di/do = -2 ; hi = m ho = -0.8
    assert math.isclose(r["image_distance"]["value"], 3.0, rel_tol=1e-9)
    assert math.isclose(r["magnification"]["value"], -2.0, rel_tol=1e-9)
    assert math.isclose(r["image_height"]["value"], -0.8, rel_tol=1e-9)


def test_virtual_image_inside_focal_point():
    # object inside the focal point -> di < 0 (virtual), m > 1 (upright, enlarged)
    do_v, f_v, ho_v = 0.6, 1.0, 0.4
    di = do_v * f_v / (do_v - f_v)
    m = -f_v / (do_v - f_v)
    assert di < 0 and m > 1


def test_diverging_lens_always_virtual_upright_reduced():
    # f < 0 (diverging): no singularity, no straddle requirement; the image is always virtual/upright/reduced
    spec = {"id": "t", "parameters": {"f": -1.0, "ho": 0.4, "do_default": 1.5,
                                      "do_min": 0.3, "do_max": 4.0, "ho_min": 0.2, "ho_max": 0.6}}
    scn = tl.build(spec)
    r = scn.algebra["result"]
    assert math.isclose(r["image_distance"]["value"], -0.6, rel_tol=1e-9)   # virtual: di < 0
    assert math.isclose(r["magnification"]["value"], 0.4, rel_tol=1e-9)     # upright (m>0), reduced (|m|<1)
    assert math.isclose(r["image_height"]["value"], 0.16, rel_tol=1e-9)
    assert scn.proof["kind"] == "governing" and {c["tier"] for c in scn.proof["checks"]} == {"structural"}
    assert scn.calculus["register_label"] == "Ray diagram"
    # a diverging lens at several distances is ALWAYS virtual (di<0) and reduced (0<m<1)
    for d in (0.3, 1.0, 4.0):
        di = d * (-1.0) / (d - (-1.0))
        m = -(-1.0) / (d - (-1.0))
        assert di < 0 and 0 < m < 1


def test_diverging_lens_skips_the_straddle_requirement():
    # f<0 has no real focus to straddle; a range entirely above |f| must still build
    spec = {"id": "t", "parameters": {"f": -1.0, "ho": 0.4, "do_default": 2.0,
                                      "do_min": 1.5, "do_max": 4.0, "ho_min": 0.2, "ho_max": 0.6}}
    scn = tl.build(spec)   # must NOT raise
    assert scn.lens.focal_length == -1.0


def test_di_is_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    scn = tl.build(SPEC)
    lmap = {s: parse_unit(u, "t") for s, u in scn.lens.unit_map.items()}
    check_homogeneous(scn.lens.di_expr, lmap, "t: di")
    check_homogeneous(scn.lens.hi_expr, lmap, "t: hi")
    check_homogeneous(scn.lens.m_expr, lmap, "t: m")   # f/(do-f) -> dimensionless


def test_range_must_straddle_focal_length():
    bad = {"id": "t", "parameters": {"f": 1.0, "ho": 0.4, "do_default": 2.0,
                                     "do_min": 1.5, "do_max": 4.0, "ho_min": 0.2, "ho_max": 0.6}}
    with pytest.raises(BuildError):
        tl.build(bad)


def test_sample_series_avoids_the_singularity():
    from quadrature_producer.emit import sample_lens_series
    scn = tl.build(SPEC)
    s = sample_lens_series(scn.lens)
    assert all(math.isfinite(x) for x in s["di"] + s["hi"] + s["m"])
    assert all(abs(u - 1.0) > 1e-6 for u in s["u"])   # no sample on f = 1.0
