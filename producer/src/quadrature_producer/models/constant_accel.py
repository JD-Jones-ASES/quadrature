"""Regime-1 model: constant acceleration (a ball thrown straight up). Wraps the tested kinematics/solve/
derive modules into the generic Scenario, with the equivalence proof (algebra == calculus).
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..derive import calculus_register
from ..kinematics import a, build_model, prove_equivalence, t, v0, x0
from ..solve import algebra_register
from .base import Marker, Scenario, Shade, Slider


def _sign(val: float) -> str:
    return "+" if val > 1e-12 else ("-" if val < -1e-12 else "0")


def build(spec: dict) -> Scenario:
    consts = spec.get("constants", {})
    ics = spec.get("initial_conditions", {})
    if "g" not in consts:
        raise BuildError(f"{spec.get('id')}: constants.g is required (house convention g = -10)")
    a_val, x0v, v0v = consts["g"], ics.get("x0", 0.0), ics.get("v0", 0.0)
    ctx = spec.get("id", spec.get("slug", "scenario"))

    model = build_model(a_val, x0v, v0v, ground=0.0)
    proof = {
        "kind": "equivalence",
        "heading": "The algebra and the calculus agree — proven, not asserted.",
        **prove_equivalence(model, ctx),
    }
    algebra = algebra_register(model, spec.get("unknowns", list(model.unknowns)))
    calculus = calculus_register(model)

    flight = float(sp.N(model.unknowns["flight_time"].subs(model.subs)))
    apex_t = float(sp.N(model.unknowns["apex_time"].subs(model.subs)))
    apex_x = float(sp.N(model.unknowns["max_height"].subs(model.subs)))
    a_num = float(model.subs[a])

    def v_at(tt: float) -> float:
        return float(sp.N(model.v_expr.subs({**model.subs, t: sp.nsimplify(tt)})))

    sign_analysis = {
        "rule": "speeding up ⟺ sign(v·a) > 0; slowing down ⟺ sign(v·a) < 0",
        "segments": [
            {"phase": "rising", "t_range": [0.0, round(apex_t, 6)],
             "v_sign": _sign(v_at(apex_t / 2)), "a_sign": _sign(a_num), "state": "slowing down"},
            {"phase": "apex", "t": round(apex_t, 6),
             "v_sign": "0", "a_sign": _sign(a_num), "state": "v = 0, but a ≠ 0"},
            {"phase": "falling", "t_range": [round(apex_t, 6), round(flight, 6)],
             "v_sign": _sign(v_at((apex_t + flight) / 2)), "a_sign": _sign(a_num), "state": "speeding up"},
        ],
    }

    return Scenario(
        regime=1,
        t=t,
        x_expr=model.x_expr,
        v_expr=model.v_expr,
        a_expr=model.a_expr,
        constants={a: sp.nsimplify(a_val)},
        constants_export={"g": a_val},
        unit_map={v0: "m/s", x0: "m", a: "m/s**2", t: "s"},
        initial_conditions=dict(ics),
        sliders=[
            Slider(v0, "v0", 5.0, 30.0, float(v0v)),
            Slider(x0, "x0", 0.0, 5.0, float(x0v)),
        ],
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        t_window=flight,
        markers=[
            Marker("x", apex_t, f"apex: {apex_x:g} m at t = {apex_t:g} s", dy=-14, va="top"),
            Marker("v", apex_t, "v = 0 here — but the line\nnever bends: its slope is a",
                   dx=12, dy=16, ha="left", va="bottom"),
            Marker("a", flight * 0.5, f"a = {a_num:g} m/s²  — constant, never zero",
                   dy=12, va="bottom", dot=False),
        ],
        guides=[apex_t],
        shades=[Shade("v", 0.0, apex_t)],
        sign_analysis=sign_analysis,
        window_mode="landing",
    )
