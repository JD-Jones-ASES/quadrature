"""Cross-checks for two mechanics-breadth lessons built on existing instruments with no engine change:
impulse–momentum (the area instrument on the time axis) and rotational kinematics (the temporal stack)."""

import math

import sympy as sp

from quadrature_producer.models import impulse, rotation


def test_impulse_builds_on_area_instrument():
    scn = impulse.build({"id": "t", "parameters": {"m": 0.5, "Fmax": 200, "tau": 0.02}})
    assert scn.regime == 2 and scn.proof["kind"] == "integral"
    assert scn.x_expr is None and scn.area is not None        # reuses the AreaPlot, time axis
    r = scn.algebra["result"]
    J = 2 * 200 * 0.02 / math.pi                               # half-sine pulse area = 2 Fmax τ / π
    assert math.isclose(r["impulse"]["value"], J, rel_tol=1e-5)
    assert math.isclose(r["delta_v"]["value"], J / 0.5, rel_tol=1e-5)   # Δv = J/m
    assert math.isclose(r["avg_force"]["value"], 2 * 200 / math.pi, rel_tol=1e-5)


def test_impulse_is_the_integral_of_force_independently():
    t, Fmax, tau = impulse.t, impulse.Fmax, impulse.tau
    w = sp.Symbol("w", nonnegative=True)
    F = Fmax * sp.sin(sp.pi * t / tau)
    J = sp.integrate(Fmax * sp.sin(sp.pi * w / tau), (w, 0, t))
    assert sp.simplify(sp.diff(J, t) - F) == 0                 # dJ/dt = F (FTC)
    assert sp.simplify(J.subs(t, tau) - 2 * Fmax * tau / sp.pi) == 0   # total impulse


def test_rotation_builds_on_stack_with_equivalence():
    scn = rotation.build({"id": "t", "parameters": {"omega0": 0, "alpha": 3, "theta0": 0, "t": 4}})
    assert scn.regime == 1 and scn.proof["kind"] == "equivalence"
    assert scn.x_expr is not None and scn.labels[0].startswith("θ")   # temporal stack, angular labels
    r = scn.algebra["result"]
    assert math.isclose(r["final_omega"]["value"], 0 + 3 * 4, rel_tol=1e-9)        # ω = ω₀ + αT = 12
    assert math.isclose(r["angle"]["value"], 0.5 * 3 * 16, rel_tol=1e-9)           # θ = ½αT² = 24
    assert math.isclose(r["revolutions"]["value"], 24 / (2 * math.pi), rel_tol=1e-5)


def test_rotation_timeless_equation_falls_out():
    t, th0, w0, a = rotation.t, rotation.theta0, rotation.omega0, rotation.alpha
    theta = th0 + w0 * t + a * t**2 / 2
    omega = w0 + a * t
    assert sp.simplify(omega**2 - (w0**2 + 2 * a * (theta - th0))) == 0    # ω² = ω₀² + 2αΔθ
