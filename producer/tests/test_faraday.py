"""Cross-checks for the Faraday-induction model — the rotating-coil AC generator on the 2-panel Φ–t / EMF–t
stack: the EMF is the negative slope of the flux, integrating it recovers the flux change, and the peak is BAω."""

import math

import sympy as sp

from quadrature_producer.models import faraday_induction as fr

SPEC = {"id": "t", "parameters": {"B": 0.5, "A": 0.1, "omega": 10}}


def test_builds_a_two_panel_stack_with_governing_proof():
    scn = fr.build(SPEC)
    assert scn.regime == 2 and scn.proof["kind"] == "governing"
    assert scn.panels is not None and len(scn.panels) == 2
    assert [p.key for p in scn.panels] == ["Phi", "EMF"]
    assert scn.x_expr is None and scn.area is None and scn.energy is None
    keys = {c["key"] for c in scn.proof["checks"]}
    assert {"emf_is_slope", "flux_is_integral", "peak_emf", "phase_90", "period"} <= keys


def test_emf_is_the_negative_slope_of_flux_and_integrates_back_to_flux_change():
    t, B, A, omega = fr.t, fr.B, fr.A, fr.omega
    Phi = B * A * sp.cos(omega * t)
    EMF = B * A * omega * sp.sin(omega * t)
    assert sp.simplify(EMF + sp.diff(Phi, t)) == 0                   # EMF = -dΦ/dt
    w = sp.Symbol("w", nonnegative=True)
    # ∫₀ᵗ EMF dt' = -ΔΦ = Φ(0) - Φ(t)
    assert sp.simplify((Phi.subs(t, 0) - Phi) - sp.integrate(EMF.subs(t, w), (w, 0, t))) == 0
    assert sp.simplify(EMF.subs(t, 0)) == 0                          # EMF zero at the flux peak (90° phase)
    assert sp.simplify(EMF.subs(t, sp.pi / (2 * omega)) - B * A * omega) == 0   # peak EMF = BAω


def test_results_match_hand_physics():
    r = fr.build(SPEC).algebra["result"]
    B_, A_, omega_ = 0.5, 0.1, 10
    assert math.isclose(r["peak_emf"]["value"], B_ * A_ * omega_, rel_tol=1e-9)   # 0.5 V
    assert math.isclose(r["peak_flux"]["value"], B_ * A_, rel_tol=1e-9)           # 0.05 Wb
    assert math.isclose(r["period"]["value"], 2 * math.pi / omega_, rel_tol=1e-4)  # ≈ 0.628 s (6-dp rounded)


def test_panels_are_dimensionally_clean():
    from quadrature_producer.dims import check_homogeneous, parse_unit
    scn = fr.build(SPEC)
    umap = {s: parse_unit(u, "t") for s, u in scn.unit_map.items()}
    for p in scn.panels:
        check_homogeneous(p.expr, umap, f"t: {p.key}")     # Φ → Wb, EMF → V
