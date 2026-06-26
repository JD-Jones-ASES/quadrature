"""Export for the browser: a JS-evaluable closed form + high-precision sample points.

Model-agnostic: works off a Scenario's symbolic x/v/a, its constants (substituted), and its sliders (left
free, since the player drives them). The sample points are the parity oracle — SymPy's own values at the
default parameters, which check-parity.mjs makes the JS reproduce within tolerance.
"""

from __future__ import annotations

import sympy as sp
from sympy.printing.jscode import jscode

from . import BuildError


def _subbed(scn, expr):
    return expr.subs(scn.constants)


def closed_form(scn) -> dict[str, str]:
    """JS-evaluable expressions for x, v, a (constants substituted; sliders + t left free)."""
    out = {}
    for name, expr in (("x", scn.x_expr), ("v", scn.v_expr), ("a", scn.a_expr)):
        e = _subbed(scn, expr)
        try:
            out[name] = jscode(e)
        except Exception as ex:  # PrintMethodNotImplementedError etc. — fail loud
            raise BuildError(f"closed_form.{name}: cannot emit JS for {sp.srepr(e)}: {ex}") from ex
    return out


def closed_form_params(scn) -> list[str]:
    syms: set[str] = set()
    for expr in (scn.x_expr, scn.v_expr, scn.a_expr):
        syms |= {str(s) for s in _subbed(scn, expr).free_symbols}
    return sorted(syms)


def closed_form_of(x_expr, v_expr, a_expr) -> dict[str, str]:
    """JS for a frame whose parameters are already fixed (only t free)."""
    out = {}
    for name, expr in (("x", x_expr), ("v", v_expr), ("a", a_expr)):
        try:
            out[name] = jscode(expr)
        except Exception as ex:
            raise BuildError(f"frame closed_form.{name}: cannot emit JS for {sp.srepr(expr)}: {ex}") from ex
    return out


def sample_series_of(x_expr, v_expr, a_expr, t, t_max: float, n: int = 61) -> dict:
    """Sample t-only frame expressions over [0, t_max] (rounded-t-then-evaluate, like sample_series)."""
    ts, xs, vs, as_ = [], [], [], []
    for i in range(n):
        ti = round(float(sp.Rational(i, n - 1) * sp.nsimplify(t_max)), 9)
        sub = {t: sp.Rational(str(ti))}
        ts.append(ti)
        xs.append(round(float(sp.N(x_expr.subs(sub), 30)), 10))
        vs.append(round(float(sp.N(v_expr.subs(sub), 30)), 10))
        as_.append(round(float(sp.N(a_expr.subs(sub), 30)), 10))
    return {"t": ts, "x": xs, "v": vs, "a": as_, "t_max": round(float(t_max), 9)}


def sample_series(scn, t_max: float, n: int = 61) -> dict:
    """SymPy's x/v/a at the default parameters over t in [0, t_max] — the parity truth.

    Rounds t first, then evaluates AT the rounded t, so the JS player (reading the rounded t back)
    reproduces these values exactly.
    """
    base = dict(scn.constants)
    for sl in scn.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    t = scn.t
    ts, xs, vs, as_ = [], [], [], []
    for i in range(n):
        ti = round(float(sp.Rational(i, n - 1) * sp.nsimplify(t_max)), 9)
        sub = {**base, t: sp.Rational(str(ti))}
        ts.append(ti)
        xs.append(round(float(sp.N(scn.x_expr.subs(sub), 30)), 10))
        vs.append(round(float(sp.N(scn.v_expr.subs(sub), 30)), 10))
        as_.append(round(float(sp.N(scn.a_expr.subs(sub), 30)), 10))
    return {"t": ts, "x": xs, "v": vs, "a": as_, "t_max": round(float(t_max), 9)}
