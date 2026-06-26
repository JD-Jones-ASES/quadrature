"""The tiered equivalence checker: prove an expression is identically zero, or fail the build.

Ported from Mechanic's verify.py `tiered_zero`. This is the engine behind the
algebra==calculus proof (brief §3.3): the learner is not told the registers agree —
this proves it. Semi-decidable by nature: simplify() and .equals() can both fail to
certify a true identity, so the high-precision numeric tier is load-bearing and last.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

import sympy as sp

from . import BuildError

NUM_SAMPLES = 30
PRECISION_DPS = 50
TOLERANCE = sp.Float("1e-40")
SIMPLIFY_OPS_CAP = 200  # above this, skip super-linear symbolic tiers; numeric tier decides


@dataclass
class SampleDomain:
    """Per-symbol sampling bounds for the numeric tier (exact rationals)."""
    bounds: dict[sp.Symbol, tuple[float, float]]
    positive: set[sp.Symbol]


def _sample_value(sym: sp.Symbol, dom: SampleDomain, rng: random.Random) -> sp.Rational:
    lo, hi = dom.bounds.get(sym, (0.1, 10.0))
    if sym in dom.positive and lo <= 0:
        lo = 0.1
    num = rng.randint(1, 10_000)
    return sp.Rational(num, 10_000) * sp.Rational(str(hi - lo)) + sp.Rational(str(lo))


def tiered_zero(expr: sp.Expr, dom: SampleDomain, context: str, seed: str) -> str:
    """Prove `expr` is identically zero over the declared domain, or raise BuildError.

    Returns the name of the tier that certified it (for the proof record).
    """
    expr = sp.together(sp.expand(expr))
    if expr == 0:
        return "structural"
    if sp.count_ops(expr) <= SIMPLIFY_OPS_CAP:
        if sp.simplify(expr) == 0:
            return "simplify"
        if expr.equals(0) is True:
            return "equals"
        if sp.simplify(expr.rewrite(sp.exp)) == 0:
            return "exp-rewrite"
    # Tier 4: high-precision numeric sampling over the declared domain.
    rng = random.Random(seed)
    free = sorted(expr.free_symbols, key=str)
    valid = 0
    attempts = 0
    while valid < NUM_SAMPLES and attempts < 20 * NUM_SAMPLES:
        attempts += 1
        subs = {s: _sample_value(s, dom, rng) for s in free}
        try:
            val = expr.evalf(PRECISION_DPS, subs=subs, chop=True)
        except (ValueError, ZeroDivisionError):
            continue
        if not val.is_number or val.has(sp.zoo, sp.oo, sp.nan) or val.is_real is not True:
            continue
        valid += 1
        if abs(val) > TOLERANCE:
            raise BuildError(
                f"{context}: NOT an identity — residual {sp.N(val, 6)} at "
                f"{ {str(k): str(v) for k, v in subs.items()} }"
            )
    if valid < max(10, NUM_SAMPLES // 3):
        raise BuildError(
            f"{context}: only {valid} real-valued samples found after {attempts} attempts — "
            f"cannot certify the identity (check sampling bounds)"
        )
    return "numeric"
