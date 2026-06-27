"""Cross-checks for the Phase-5 completeness lessons: incline-with-friction (stack), radioactive decay
(2-panel stack), Torricelli (energy bars), and the continuous line-charge field (area instrument)."""

import math

import sympy as sp

from quadrature_producer.dims import check_homogeneous, parse_unit
from quadrature_producer.models import decay, incline_friction, line_charge_field, torricelli


def _umap(scn):
    return {s: parse_unit(u, "t") for s, u in scn.unit_map.items()}


# --- incline with friction (regime 1, x/v/a stack) ---
def test_incline_acceleration_and_kinematics():
    scn = incline_friction.build({"id": "t", "parameters": {"g": 10, "theta_deg": 30, "mu": 0.2}})
    assert scn.regime == 1 and scn.proof["kind"] == "equivalence"
    g, th, mu = incline_friction.g, incline_friction.th, incline_friction.mu
    ang = th * sp.pi / 180
    a = g * (sp.sin(ang) - mu * sp.cos(ang))
    # mass-independent acceleration; v and x are its integrals; v² = 2ax
    assert math.isclose(float(a.subs({g: 10, th: 30, mu: 0.2})), 10 * (math.sin(math.radians(30)) - 0.2 * math.cos(math.radians(30))), rel_tol=1e-9)
    assert sp.simplify(scn.v_expr - a * incline_friction.t) == 0
    assert sp.simplify(scn.v_expr**2 - 2 * a * scn.x_expr) == 0
    for name, expr in (("x", scn.x_expr), ("v", scn.v_expr), ("a", scn.a_expr)):
        check_homogeneous(expr, _umap(scn), f"t: {name}")


# --- radioactive decay (regime 2, 2-panel N / dN/dt stack) ---
def test_decay_is_governed_by_dNdt_eq_minus_lambda_N():
    scn = decay.build({"id": "t", "parameters": {"lam": 0.5, "N0": 1000}})
    assert scn.regime == 2 and scn.panels is not None and [p.key for p in scn.panels] == ["N", "dNdt"]
    t, lam, N0 = decay.t, decay.lam, decay.N0
    N = N0 * sp.exp(-lam * t)
    assert sp.simplify(sp.diff(N, t) + lam * N) == 0                  # dN/dt = -λN
    assert sp.simplify(N.subs(t, sp.log(2) / lam) - N0 / 2) == 0      # half-life
    r = scn.algebra["result"]
    assert math.isclose(r["half_life"]["value"], math.log(2) / 0.5, rel_tol=1e-5)
    assert math.isclose(r["mean_lifetime"]["value"], 1 / 0.5, rel_tol=1e-9)
    for p in scn.panels:
        check_homogeneous(p.expr, _umap(scn), f"t: {p.key}")


# --- Torricelli (regime 2, energy bars) ---
def test_torricelli_efflux_speed():
    scn = torricelli.build({"id": "t", "parameters": {"rho": 1000, "g": 10, "h": 5}})
    assert scn.regime == 2 and scn.energy is not None
    d, rho, g, h = torricelli.d, torricelli.rho, torricelli.g, torricelli.h
    ke, pe = rho * g * d, rho * g * (h - d)
    assert sp.simplify((ke + pe) - rho * g * h) == 0                  # total flat
    assert sp.simplify(sp.diff(ke + pe, d)) == 0
    assert math.isclose(scn.algebra["result"]["efflux_speed"]["value"], math.sqrt(2 * 10 * 5), rel_tol=1e-9)  # √(2gh)=10
    check_homogeneous(scn.energy.ke_expr, _umap_energy(scn), "t: KE")


def _umap_energy(scn):
    return {s: parse_unit(u, "t") for s, u in scn.energy.unit_map.items()}


# --- continuous line-charge field (regime 2, area instrument) ---
def test_line_charge_field_is_the_integral_of_point_contributions():
    scn = line_charge_field.build({"id": "t", "parameters": {"k": 8990000000, "lam_nc": 100, "a": 0.1, "L": 0.3}})
    assert scn.regime == 2 and scn.proof["kind"] == "integral" and scn.area is not None
    x, k, lam, a = line_charge_field.x, line_charge_field.k, line_charge_field.lam, line_charge_field.a
    nano = line_charge_field._NANO
    f = k * lam * nano / x**2
    g = k * lam * nano * (1 / a - 1 / x)
    assert sp.simplify(sp.diff(g, x) - f) == 0                        # slope of accumulated field = contribution
    w = sp.Symbol("w", positive=True)
    assert sp.simplify(g - sp.integrate(f.subs(x, w), (w, a, x))) == 0   # field is the area
    # total field at the worked point: k·λ·(1/a − 1/(a+L)) with λ = 100 nC/m
    E = 8.99e9 * 100e-9 * (1 / 0.1 - 1 / 0.4)
    assert math.isclose(scn.algebra["result"]["total_field"]["value"], E, rel_tol=1e-4)
    check_homogeneous(scn.area.f_expr, {s: parse_unit(u, "t") for s, u in scn.area.unit_map.items()}, "t: f")
