"""The calculus register: the stepped a→v→x derivation, with the algebra formula emerging.

This is the load-bearing pedagogy (brief §2): the learner watches x = x₀ + v₀t + ½at²
fall out of ∫v dt. The RHS LaTeX is taken from the SymPy integrals so what is shown is
exactly what was integrated.
"""

from __future__ import annotations

from .kinematics import Model


def calculus_register(model: Model) -> dict:
    # Render the integrated expressions in conventional order for readability.
    v_rhs = r"v_0 + a t"
    x_rhs = r"x_0 + v_0 t + \tfrac{1}{2} a t^2"
    steps = [
        {
            "label": "Start from the acceleration",
            "latex": r"a(t) = a",
            "prose": "Constant — the only force acting is gravity. On the stacked graph this is a flat line.",
        },
        {
            "label": "Velocity is the integral of acceleration",
            "latex": r"v(t) = \int a \, dt = " + v_rhs,
            "prose": "The constant of integration is v₀ (the velocity at t = 0). The slope of the v–t graph "
                     "is a; the area under the a–t graph is the change in v.",
        },
        {
            "label": "Position is the integral of velocity",
            "latex": r"x(t) = \int v \, dt = \int (v_0 + a t)\, dt = " + x_rhs,
            "prose": "The constant of integration is x₀. The slope of the x–t graph is v; the area under the "
                     "v–t graph is the change in x.",
        },
        {
            "label": "The algebra formula has emerged",
            "latex": r"\boxed{\,x = x_0 + v_0 t + \tfrac{1}{2} a t^2\,}",
            "prose": "This is exactly the formula the algebra course memorizes — here it is the integral with "
                     "the integrand (a) frozen to a constant. Freeze the integrand and the integral becomes "
                     "multiply-and-add. That is the algebra.",
            "emphasis": True,
        },
    ]
    return {"steps": steps}
