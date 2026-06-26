"""Export for the browser: a JS-evaluable closed form + high-precision sample points.

The closed form lets the player redraw interactive graphs in JS with no SymPy and no
Matplotlib (brief §3.5). The sample points are the **parity oracle**: SymPy's own values
at the default parameters, which `check-parity.mjs` makes the JS reproduce within 1e-9.
Ported in spirit from Mechanic's emit_js.py (jscode is the single executable-math emitter).
"""

from __future__ import annotations

import sympy as sp
from sympy.printing.jscode import jscode

from . import BuildError
from .kinematics import Model, a, t, v0, x0


def closed_form(model: Model) -> dict[str, str]:
    """JS-evaluable expressions for x, v, a as functions of (t, v0, x0); a is fixed to its value."""
    a_val = model.subs[a]
    out = {}
    for name, expr in (("x", model.x_expr), ("v", model.v_expr), ("a", model.a_expr)):
        js_expr = expr.subs(a, a_val)
        try:
            out[name] = jscode(js_expr)
        except Exception as e:  # PrintMethodNotImplementedError etc. — fail loud
            raise BuildError(f"closed_form: cannot emit JS for {sp.srepr(js_expr)}: {e}") from e
    return out


def closed_form_params(model: Model) -> list[str]:
    """The free parameters of the closed form (the JS function signature), sorted."""
    a_val = model.subs[a]
    syms: set[str] = set()
    for expr in (model.x_expr, model.v_expr, model.a_expr):
        syms |= {str(s) for s in expr.subs(a, a_val).free_symbols}
    return sorted(syms)


def sample_series(model: Model, t_max: float, n: int = 61) -> dict:
    """SymPy's x/v/a values at the default parameters over t in [0, t_max] — the parity truth."""
    a_val, x0_val, v0_val = model.subs[a], model.subs[x0], model.subs[v0]
    base = {a: a_val, x0: x0_val, v0: v0_val}
    ts, xs, vs, as_ = [], [], [], []
    for i in range(n):
        # round t first, then evaluate AT the rounded t, so the JS player (which reads the rounded
        # t back) reproduces these x/v/a values exactly — this is what check-parity.mjs verifies.
        ti = round(float(sp.Rational(i, n - 1) * sp.nsimplify(t_max)), 9)
        sub = {**base, t: sp.Rational(str(ti))}
        ts.append(ti)
        xs.append(round(float(sp.N(model.x_expr.subs(sub), 30)), 10))
        vs.append(round(float(sp.N(model.v_expr.subs(sub), 30)), 10))
        as_.append(round(float(sp.N(model.a_expr.subs(sub), 30)), 10))
    return {"t": ts, "x": xs, "v": vs, "a": as_, "t_max": round(float(t_max), 9)}
