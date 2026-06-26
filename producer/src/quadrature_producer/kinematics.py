"""The constant-acceleration kinematics model (regime 1).

Builds v(t)=∫a dt and x(t)=∫v dt symbolically, the constant-`a` algebra relations, and
solves the standard unknowns. Crucially it assembles the **equivalence-proof identities**
— the expressions that must be identically zero for "algebra == calculus" to hold (brief
§3.3). Phase 0 proves the engine on this regime; later regimes swap in a different a(t).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import sympy as sp

from .prove import SampleDomain, tiered_zero

# House symbols. up positive; t >= 0.
t = sp.Symbol("t", nonnegative=True, real=True)
x0 = sp.Symbol("x0", real=True)
v0 = sp.Symbol("v0", positive=True)
a = sp.Symbol("a", negative=True)  # gravity is negative with up positive
x, v = sp.symbols("x v", real=True)

# Sampling domain for the numeric proof tier (used only if the symbolic tiers abstain).
PROOF_DOMAIN = SampleDomain(
    bounds={v0: (1.0, 30.0), x0: (0.5, 5.0), a: (-15.0, -1.0), t: (0.1, 5.0)},
    positive={v0, x0},
)


@dataclass
class Model:
    # calculus register (integrated)
    a_expr: sp.Expr
    v_expr: sp.Expr
    x_expr: sp.Expr
    # algebra register (constant-a relations, as the algebra student writes them)
    v_alg: sp.Expr
    x_alg: sp.Expr
    timeless: sp.Eq
    # solved unknowns, symbolic in (x0, v0, a)
    unknowns: dict[str, sp.Expr]
    # equivalence-proof identities: (key, claim, expr-that-must-be-zero)
    identities: list[tuple[str, str, sp.Expr]]
    # numeric substitution map for this scenario
    subs: dict[sp.Symbol, sp.Rational] = field(default_factory=dict)


def build_model(a_value, x0_value, v0_value, ground: float = 0.0) -> Model:
    """Assemble the symbolic model and the proof identities for one scenario.

    a_value is the (negative) constant acceleration (= g for free fall). ground is the
    height at which 'flight time'/'impact' are measured.
    """
    # --- calculus register: integrate up from the acceleration ---
    a_expr = a                                   # a(t) = a (constant)
    v_expr = v0 + sp.integrate(a_expr, t)        # v(t) = v0 + ∫a dt = v0 + a t
    x_expr = x0 + sp.integrate(v_expr, t)        # x(t) = x0 + ∫v dt = x0 + v0 t + a t²/2

    # --- algebra register: the constant-a relations, asserted ---
    v_alg = v0 + a * t
    x_alg = x0 + v0 * t + a * t**2 / 2
    timeless = sp.Eq(v**2, v0**2 + 2 * a * (x - x0))

    # --- solve the standard unknowns symbolically (in x0, v0, a) ---
    apex_time = -v0 / a                                       # v = 0
    max_height = sp.solve(timeless.subs(v, 0), x)[0]          # x0 - v0²/(2a)
    disc = v0**2 + 2 * a * (ground - x0)                      # timeless eq at x = ground (v² there)
    flight_time = (-v0 - sp.sqrt(disc)) / a                   # physical (later) root of x = ground
    impact_velocity = -sp.sqrt(disc)                          # downward root of the timeless eq at ground
    unknowns = {
        "apex_time": sp.simplify(apex_time),
        "max_height": sp.simplify(max_height),
        "flight_time": sp.simplify(flight_time),
        "impact_velocity": sp.simplify(impact_velocity),
    }

    # --- the equivalence-proof identities (each must be identically zero) ---
    identities = [
        ("v_formula_is_integral",
         "The algebra velocity formula v = v₀ + at IS the integral ∫a dt with v(0)=v₀.",
         v_alg - v_expr),
        ("x_formula_is_integral",
         "The algebra position formula x = x₀ + v₀t + ½at² IS the integral ∫v dt with x(0)=x₀.",
         x_alg - x_expr),
        ("apex_is_v_zero",
         "Velocity really is zero at the apex time (so the apex time is correct).",
         v_expr.subs(t, apex_time)),
        ("max_height_agrees",
         "Max height from the timeless equation equals the calculus trajectory at its apex.",
         max_height - x_expr.subs(t, apex_time)),
        ("flight_time_lands",
         "At the flight time the calculus trajectory really returns to the ground (so the time is correct).",
         x_expr.subs(t, flight_time) - ground),
        ("impact_velocity_agrees",
         "Impact velocity from the timeless equation equals the calculus velocity at landing.",
         impact_velocity - v_expr.subs(t, flight_time)),
    ]

    subs = {
        a: sp.nsimplify(a_value),
        x0: sp.nsimplify(x0_value),
        v0: sp.nsimplify(v0_value),
    }
    return Model(a_expr, v_expr, x_expr, v_alg, x_alg, timeless, unknowns, identities, subs)


def prove_equivalence(model: Model, context: str) -> dict:
    """Run every identity through the tiered checker. Returns the proof record; raises on failure."""
    checks = []
    for key, claim, expr in model.identities:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{context}: {key}", seed=f"{context}/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    return {
        "checked_by": "sympy",
        "holds": True,
        "detail": "simplify(algebra - calculus) == 0 for each identity below",
        "checks": checks,
    }
