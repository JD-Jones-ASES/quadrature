"""Regime-2 model: charging an RC circuit — the temporal stack generalized to a TWO-panel Q–t / I–t stack
(ADR-0021). A capacitor $C$ charges through a resistor $R$ from a battery of EMF $V$. The charge $Q(t)$ rises
toward $CV$ while the current $I(t)$ decays from $V/R$ — and **the current is the slope of the charge**,
exactly as velocity is the slope of position, one domain over.

The algebra-based course hands you the charging curve and the time constant $\\tau = RC$ as rules. The calculus
shows where they come from: Kirchhoff's voltage law $V = IR + Q/C$ with $I = dQ/dt$ is a first-order ODE,
$R\\,dQ/dt + Q/C = V$, whose solution is $Q(t) = CV\\,(1 - e^{-t/RC})$; differentiating gives the current
$I(t) = (V/R)\\,e^{-t/RC}$. Plotted as a stacked Q–t over I–t, the slope of $Q$ at every instant *is* $I$, and
the area under $I$ from $0$ to $t$ is exactly the accumulated charge $Q$ — the same slope↔value / area↔change
pivot as the kinematics stack.

Proof kind `governing`: the current is the slope of the charge ($I = dQ/dt$); the charge solves the RC equation
($R\\,dQ/dt + Q/C = V$); the charge is the time-integral of the current ($Q = \\int_0^t I\\,dt'$); the time
constant is $\\tau = RC$ (at $t = \\tau$ the capacitor is $1 - 1/e \\approx 63\\%$ charged); the steady state is
$Q \\to CV$, $I \\to 0$.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import Panel, Scenario, Slider, make_result

t = sp.Symbol("t", nonnegative=True, real=True)   # time (the shared axis)
R = sp.Symbol("R", positive=True)                 # resistance, Ω (slider — sets the time constant)
C = sp.Symbol("C", positive=True)                 # capacitance, F (constant)
V = sp.Symbol("V", positive=True)                 # battery EMF, V (slider — sets the height)
_w = sp.Symbol("w", nonnegative=True)             # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={t: (0.01, 8.0), R: (100.0, 5000.0), C: (1e-4, 1e-2), V: (1.0, 20.0)},
    positive={R, C, V},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("R", "C", "V"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: rc-charging requires parameters.{key}")
    R_val, C_val, V_val = sp.nsimplify(p["R"]), sp.nsimplify(p["C"]), sp.nsimplify(p["V"])

    tau = R * C
    Q = C * V * (1 - sp.exp(-t / tau))             # charge on the capacitor
    I = V / R * sp.exp(-t / tau)                    # current = dQ/dt

    checks_spec = [
        ("current_is_slope",
         r"The current is the slope of the charge: $I = \dfrac{dQ}{dt}$ — exactly as velocity is the slope of position.",
         I - sp.diff(Q, t)),
        ("governing_eqn",
         r"The charge solves Kirchhoff's voltage law $V = IR + Q/C$, i.e. the RC equation $R\,\dfrac{dQ}{dt} + \dfrac{Q}{C} = V$.",
         R * sp.diff(Q, t) + Q / C - V),
        ("charge_is_integral",
         r"The charge is the accumulated current — the area under $I$: $Q(t) = \int_0^t I\,dt'$.",
         Q - sp.integrate(I.subs(t, _w), (_w, 0, t))),
        ("time_constant",
         r"The time constant is $\tau = RC$: at $t = \tau$ the capacitor is $1 - 1/e \approx 63\%$ charged, $Q(\tau) = CV(1 - e^{-1})$.",
         Q.subs(t, tau) - C * V * (1 - sp.exp(-1))),
        ("steady_state",
         r"The steady state is full charge and no current: $Q \to CV$ and $I \to 0$ as $t \to \infty$.",
         sp.limit(Q, t, sp.oo) - C * V),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"rc-charging/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "The current is the slope of the charge, and the charge solves the RC equation — the "
                   "kinematics slope↔value pivot, one domain over.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $I = dQ/dt$; check $R\,dQ/dt + Q/C = V$; check $Q = \int_0^t I\,dt'$; "
                  r"$\tau = RC$ (63\% at $t=\tau$); steady state $Q\to CV$, $I\to 0$",
        "checks": checks,
    }

    rsubs = {R: R_val, C: C_val, V: V_val}
    tau_r = make_result(tau, rsubs, "s", r"Time constant $\tau = RC$")
    tau_r["symbolic_latex"] = r"RC"
    qmax = make_result(C * V, rsubs, "C", r"Final charge $Q_\infty = CV$")
    qmax["symbolic_latex"] = r"CV"
    i0 = make_result(V / R, rsubs, "A", r"Initial current $I_0 = V/R$")
    i0["symbolic_latex"] = r"V/R"
    qtau = make_result(C * V * (1 - sp.exp(-1)), rsubs, "C", r"Charge after one $\tau$ ($\approx 63\%$)")
    qtau["symbolic_latex"] = r"CV(1 - e^{-1})"
    result = {"time_constant": tau_r, "final_charge": qmax, "initial_current": i0, "charge_at_tau": qtau}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (a charging curve and a time constant)",
                "latex": r"Q(t) = CV\left(1 - e^{-t/RC}\right), \qquad \tau = RC",
                "prose": "The capacitor charges toward $Q_\\infty = CV$, and the time constant $\\tau = RC$ sets "
                         "how fast: after one $\\tau$ it is about $63\\%$ charged, after $5\\tau$ essentially "
                         "full. You are handed the curve and the time constant as rules, with no account of "
                         "*why* the approach is exponential or where $\\tau = RC$ comes from.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Kirchhoff's voltage law is a differential equation",
                "latex": r"V = IR + \frac{Q}{C}, \quad I = \frac{dQ}{dt} \ \Longrightarrow\ R\,\frac{dQ}{dt} + \frac{Q}{C} = V",
                "prose": "Around the loop, the battery EMF equals the resistor drop $IR$ plus the capacitor "
                         "voltage $Q/C$. Because the current is the rate of change of charge, $I = dQ/dt$, this "
                         "is a first-order differential equation for $Q(t)$ — not an algebra equation.",
            },
            {
                "label": "Solving it gives the charging curve; its slope is the current",
                "latex": r"Q(t) = CV\left(1 - e^{-t/RC}\right) \ \Longrightarrow\ I(t) = \frac{dQ}{dt} = \frac{V}{R}\,e^{-t/RC}",
                "prose": "The solution is the exponential approach to $CV$, with the time constant $\\tau = RC$ "
                         "falling straight out of the equation. Differentiating the charge gives the current: it "
                         "starts at $V/R$ and decays. The current is the *slope* of the charge.",
                "emphasis": True,
            },
            {
                "label": "Watch the two panels — I is the slope of Q",
                "latex": r"\boxed{\,I(t) = \frac{dQ}{dt}\,}",
                "prose": "Drag $R$ or $V$: the charge $Q$ rises and levels off while the current $I$ decays, and "
                         "at every instant the slope of the upper $Q$–$t$ curve is the value of the lower $I$–$t$ "
                         "curve — the same relationship as position and velocity, in a circuit. The area under "
                         "$I$ is the charge delivered. Raising $R$ stretches the time constant $RC$, slowing both.",
            },
        ],
    }

    panels = [
        Panel(key="Q", expr=Q, label="Q  (C)", unit="C", accent=False),
        Panel(key="I", expr=I, label="I  (A)", unit="A", accent=True),
    ]

    return Scenario(
        regime=2,
        constants_export={"R": float(R_val), "C": float(C_val), "V": float(V_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        t=t,
        constants={C: C_val},
        unit_map={R: "ohm", C: "F", V: "V", t: "s"},
        sliders=[Slider(R, "R", 200.0, 4000.0, float(R_val)), Slider(V, "V", 5.0, 20.0, float(V_val))],
        t_window=5.0,
        window_mode="fixed",
        initial_conditions={"Q0": 0.0, "I0": float(V_val / R_val)},
        panels=panels,
    )
