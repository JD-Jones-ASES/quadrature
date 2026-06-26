"""Dimensional analysis: unit parsing, SI 7-vectors, homogeneity checking.

Built on sympy.physics.units (NOT pint): it operates on the same symbolic expressions
used for verification. `SI._collect_factor_and_dimension` is semi-private API — pinned
to sympy==1.14.0 and covered by tests/test_dims.py. Ported from Mechanic's dims.py.

7-vector order: [L, M, T, I, Theta, N, J]
(length, mass, time, current, temperature, amount of substance, luminous intensity)
"""

from __future__ import annotations

import sympy as sp
from sympy.physics import units as u
from sympy.physics.units.systems.si import SI, dimsys_SI

from . import BuildError

# Namespace for parsing authored `unit:` strings. Deliberately explicit — an unknown
# unit name must fail the build, not silently become a free symbol.
UNIT_NAMESPACE: dict[str, object] = {
    "m": u.meter, "kg": u.kilogram, "s": u.second, "A": u.ampere,
    "K": u.kelvin, "mol": u.mole, "cd": u.candela,
    "N": u.newton, "Pa": u.pascal, "J": u.joule, "W": u.watt, "Hz": u.hertz,
    "C": u.coulomb, "V": u.volt, "ohm": u.ohm, "F": u.farad, "T": u.tesla, "Wb": u.weber,
    "rad": u.radian,
    "mm": u.millimeter, "cm": u.centimeter, "km": u.kilometer,
    "g": u.gram, "kPa": u.kilo * u.pascal, "MPa": u.mega * u.pascal,
    "kN": u.kilo * u.newton, "minute": u.minute, "hour": u.hour,
}

_DIM_ORDER = (
    "length", "mass", "time", "current", "temperature",
    "amount_of_substance", "luminous_intensity",
)


def parse_unit(unit_str: str, context: str) -> sp.Expr:
    """Parse an authored unit string like 'N', 'kg/m**3', 'm/s**2', or '1'."""
    s = (unit_str or "").strip()
    if s in ("1", ""):
        return sp.S.One
    try:
        expr = sp.sympify(s, locals=dict(UNIT_NAMESPACE))
    except (sp.SympifyError, SyntaxError) as e:
        raise BuildError(f"{context}: cannot parse unit '{unit_str}': {e}") from e
    leftover = expr.free_symbols
    if leftover:
        raise BuildError(
            f"{context}: unit '{unit_str}' contains unknown unit name(s) "
            f"{sorted(map(str, leftover))}; add them to dims.UNIT_NAMESPACE if legitimate"
        )
    return expr


def dim_vector(unit_expr: sp.Expr, context: str) -> list[float]:
    """SI dimension exponents [L,M,T,I,Theta,N,J] of a unit expression."""
    if unit_expr == sp.S.One:
        return [0.0] * 7
    try:
        _, dim = SI._collect_factor_and_dimension(unit_expr)
    except ValueError as e:
        raise BuildError(f"{context}: cannot determine dimension: {e}") from e
    deps = dimsys_SI.get_dimensional_dependencies(dim)
    vec = [0.0] * 7
    for d, exp in deps.items():
        name = str(d.name) if hasattr(d, "name") else str(d)
        if name not in _DIM_ORDER:
            raise BuildError(f"{context}: unexpected base dimension '{name}'")
        vec[_DIM_ORDER.index(name)] = float(exp)
    return vec


def _is_dimensionless(expr: sp.Expr) -> bool:
    if not expr.atoms(u.Quantity):
        return True
    _, dim = SI._collect_factor_and_dimension(expr)
    return dimsys_SI.get_dimensional_dependencies(dim) == {}


def check_homogeneous(expr: sp.Expr, unit_map: dict[sp.Symbol, sp.Expr], context: str) -> None:
    """Fail the build unless `expr` is dimensionally homogeneous.

    Substitutes each variable with its unit expression and lets
    _collect_factor_and_dimension walk the result — it raises ValueError on mismatched
    additive terms. We additionally enforce dimensionless arguments to transcendentals.
    """
    missing = [s for s in expr.free_symbols if s not in unit_map]
    if missing:
        raise BuildError(f"{context}: symbols without declared units: {sorted(map(str, missing))}")
    substituted = expr.subs(unit_map)
    try:
        SI._collect_factor_and_dimension(substituted)
    except ValueError as e:
        raise BuildError(f"{context}: not dimensionally homogeneous: {e}") from e
    for f in expr.atoms(sp.Function):
        if f.func.__name__ in ("sin", "cos", "tan", "asin", "acos", "atan",
                               "exp", "log", "sinh", "cosh", "tanh"):
            for arg in f.args:
                if not _is_dimensionless(arg.subs(unit_map)):
                    raise BuildError(
                        f"{context}: argument of {f.func.__name__} must be dimensionless, got {arg}"
                    )
