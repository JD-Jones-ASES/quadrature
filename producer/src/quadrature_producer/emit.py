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


# The browser-side axis variable is always the canonical `u`, regardless of the model's symbol name (V, x,
# …), so the JSON axis key (series `u`), the closed-form param, and the cursor name all agree.
_AXIS = sp.Symbol("u")


def _norm(area, expr):
    return expr.subs(area.constants).subs(area.u, _AXIS)


def closed_form_area(area) -> dict[str, str]:
    """JS-evaluable f(u) and g(u) for the area instrument (constants substituted; axis u + sliders free)."""
    out = {}
    for name, expr in (("f", area.f_expr), ("g", area.g_expr)):
        e = _norm(area, expr)
        try:
            out[name] = jscode(e)
        except Exception as ex:
            raise BuildError(f"area closed_form.{name}: cannot emit JS for {sp.srepr(e)}: {ex}") from ex
    return out


def closed_form_params_area(area) -> list[str]:
    syms: set[str] = set()
    for expr in (area.f_expr, area.g_expr):
        syms |= {str(s) for s in _norm(area, expr).free_symbols}
    return sorted(syms)


def sample_area_series(area, n: int = 61) -> dict:
    """SymPy's f(u) and g(u) at the default slider values over u in [u0, u_window] — the parity truth.

    Rounds u first, then evaluates AT the rounded u, so the JS player (reading the rounded u back)
    reproduces these values exactly. Axis key is `u` (the analogue of `t` in the temporal series)."""
    base = dict(area.constants)
    for sl in area.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    u = area.u
    us, fs, gs = [], [], []
    span = sp.nsimplify(area.u_window) - sp.nsimplify(area.u0)
    for i in range(n):
        ui = round(float(sp.nsimplify(area.u0) + sp.Rational(i, n - 1) * span), 9)
        sub = {**base, u: sp.Rational(str(ui))}
        us.append(ui)
        fs.append(round(float(sp.N(area.f_expr.subs(sub), 30)), 10))
        gs.append(round(float(sp.N(area.g_expr.subs(sub), 30)), 10))
    return {"u": us, "f": fs, "g": gs, "u_max": round(float(area.u_window), 9)}


def _norm_energy(en, expr):
    return expr.subs(en.constants).subs(en.u, _AXIS)


def closed_form_energy(en) -> dict[str, str]:
    """JS-evaluable ke(u) and pe(u) for the energy instrument (constants substituted; axis u + sliders free)."""
    out = {}
    for name, expr in (("ke", en.ke_expr), ("pe", en.pe_expr)):
        e = _norm_energy(en, expr)
        try:
            out[name] = jscode(e)
        except Exception as ex:
            raise BuildError(f"energy closed_form.{name}: cannot emit JS for {sp.srepr(e)}: {ex}") from ex
    return out


def closed_form_params_energy(en) -> list[str]:
    syms: set[str] = set()
    for expr in (en.ke_expr, en.pe_expr):
        syms |= {str(s) for s in _norm_energy(en, expr).free_symbols}
    return sorted(syms)


def sample_energy_series(en, n: int = 61) -> dict:
    """SymPy's ke(u) and pe(u) at the default slider values over u in [u0, u_window] — the parity truth.
    Rounds u first, then evaluates AT the rounded u (so the JS player reproduces it exactly). Axis key is `u`."""
    base = dict(en.constants)
    for sl in en.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    u = en.u
    us, kes, pes = [], [], []
    span = sp.nsimplify(en.u_window) - sp.nsimplify(en.u0)
    for i in range(n):
        ui = round(float(sp.nsimplify(en.u0) + sp.Rational(i, n - 1) * span), 9)
        sub = {**base, u: sp.Rational(str(ui))}
        us.append(ui)
        kes.append(round(float(sp.N(en.ke_expr.subs(sub), 30)), 10))
        pes.append(round(float(sp.N(en.pe_expr.subs(sub), 30)), 10))
    return {"u": us, "ke": kes, "pe": pes, "u_max": round(float(en.u_window), 9)}


def _norm_collision(col, expr):
    return expr.subs(col.constants).subs(col.u, _AXIS)


def closed_form_collision(col) -> dict[str, str]:
    """JS-evaluable v1'(m1, e) and v2'(m1, e) for the collision instrument (m2/v1/v2 substituted; the mass
    slider m1 + the restitution cursor e (canonical `u`) left free)."""
    out = {}
    for name, expr in (("v1f", col.v1f_expr), ("v2f", col.v2f_expr)):
        ex = _norm_collision(col, expr)
        try:
            out[name] = jscode(ex)
        except Exception as exn:
            raise BuildError(f"collision closed_form.{name}: cannot emit JS for {sp.srepr(ex)}: {exn}") from exn
    return out


def closed_form_params_collision(col) -> list[str]:
    syms: set[str] = set()
    for expr in (col.v1f_expr, col.v2f_expr):
        syms |= {str(s) for s in _norm_collision(col, expr).free_symbols}
    return sorted(syms)


def sample_collision_series(col, n: int = 61) -> dict:
    """SymPy's v1'(e) and v2'(e) at the default mass over e in [cursor.min, cursor.max] — the parity truth.
    Rounds e first, then evaluates AT the rounded e (so the JS player reproduces it exactly). Axis key is `u`."""
    base = dict(col.constants)
    for sl in col.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    u = col.u
    us, v1s, v2s = [], [], []
    lo, hi = sp.nsimplify(col.cursor.min), sp.nsimplify(col.cursor.max)
    span = hi - lo
    for i in range(n):
        ui = round(float(lo + sp.Rational(i, n - 1) * span), 9)
        sub = {**base, u: sp.Rational(str(ui))}
        us.append(ui)
        v1s.append(round(float(sp.N(col.v1f_expr.subs(sub), 30)), 10))
        v2s.append(round(float(sp.N(col.v2f_expr.subs(sub), 30)), 10))
    return {"u": us, "v1f": v1s, "v2f": v2s, "u_max": round(float(col.cursor.max), 9)}


def closed_form_traj(traj) -> dict[str, str]:
    """JS-evaluable x(t) and y(t) for the trajectory instrument (constants substituted; t + sliders free)."""
    out = {}
    for name, expr in (("x", traj.x_expr), ("y", traj.y_expr)):
        e = expr.subs(traj.constants)
        try:
            out[name] = jscode(e)
        except Exception as ex:
            raise BuildError(f"traj closed_form.{name}: cannot emit JS for {sp.srepr(e)}: {ex}") from ex
    return out


def closed_form_params_traj(traj) -> list[str]:
    syms: set[str] = set()
    for expr in (traj.x_expr, traj.y_expr):
        syms |= {str(s) for s in expr.subs(traj.constants).free_symbols}
    return sorted(syms)


def sample_traj_series(traj, n: int = 81) -> dict:
    """SymPy's x(t), y(t) at the default slider values over t in [0, t_flight] — the parity truth for the
    closed-form (drag-free) path. Rounds t first, then evaluates (so the JS player reproduces it exactly)."""
    base = dict(traj.constants)
    for sl in traj.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    tt = traj.t
    ts, xs, ys = [], [], []
    span = sp.nsimplify(traj.t_flight)
    for i in range(n):
        ti = round(float(sp.Rational(i, n - 1) * span), 9)
        sub = {**base, tt: sp.Rational(str(ti))}
        ts.append(ti)
        xs.append(round(float(sp.N(traj.x_expr.subs(sub), 30)), 10))
        ys.append(round(float(sp.N(traj.y_expr.subs(sub), 30)), 10))
    return {"t": ts, "x": xs, "y": ys, "t_max": round(float(traj.t_flight), 9)}


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
