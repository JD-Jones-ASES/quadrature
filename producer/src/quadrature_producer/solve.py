"""The algebra register: the stepped algebra-based solution + named results.

The algebra student asserts the constant-a relations and solves for the unknowns. The
LaTeX for each *solved* result comes from the SymPy expression (no transcription typos);
the canonical relation forms are written in their conventional order for readability.
"""

from __future__ import annotations

from .kinematics import Model
from .util import display, numval, tex

_UNITS = {
    "apex_time": ("s", "Time to the apex"),
    "max_height": ("m", "Maximum height"),
    "flight_time": ("s", "Time of flight"),
    "impact_velocity": ("m/s", "Velocity at impact"),
}


def algebra_register(model: Model, unknown_keys: list[str]) -> dict:
    steps = [
        {
            "label": "Assert the constant-acceleration relations",
            "latex": r"v = v_0 + a t \qquad x = x_0 + v_0 t + \tfrac{1}{2} a t^2",
            "prose": "These are the formulas the algebra-based course memorizes. (They are quadratures — "
                     "we will see them fall out of the calculus.)",
        },
        {
            "label": "Apex: the top is where velocity is zero",
            "latex": r"v = 0 \;\implies\; t_{\text{apex}} = " + tex(model.unknowns["apex_time"]),
            "prose": "Velocity is zero only for an instant — but acceleration is not. The ball is still "
                     "being pulled down at g.",
        },
        {
            "label": "Maximum height from the timeless equation",
            "latex": r"0 = v_0^2 + 2a\,(x - x_0) \;\implies\; x_{\max} = " + tex(model.unknowns["max_height"]),
            "prose": "Set v = 0 in v² = v₀² + 2a(x − x₀). No time needed — this is the equation an algebra "
                     "student is handed without its derivation.",
        },
        {
            "label": "Time of flight: solve for when it returns to the ground",
            "latex": r"x_0 + v_0 t + \tfrac{1}{2} a t^2 = 0 \;\implies\; t_{\text{flight}} = "
                     + tex(model.unknowns["flight_time"]),
            "prose": "The physical (later) root of the quadratic — the moment it lands.",
        },
        {
            "label": "Impact velocity at the ground",
            "latex": r"v_{\text{impact}} = " + tex(model.unknowns["impact_velocity"]),
            "prose": "Negative because it is moving downward at impact (up is positive).",
        },
    ]

    result = {}
    for key in unknown_keys:
        if key not in model.unknowns:
            continue
        unit, label = _UNITS.get(key, ("", key))
        value = numval(model.unknowns[key], model.subs)
        result[key] = {
            "label": label,
            "unit": unit,
            "symbolic_latex": tex(model.unknowns[key]),
            "value": round(value, 6),
            "display": display(value),
        }
    return {"steps": steps, "result": result}
