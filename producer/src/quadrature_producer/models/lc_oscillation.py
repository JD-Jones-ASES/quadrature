"""Regime-2 model: the LC oscillator — the temporal stack as a TWO-panel Q–t / I–t stack (ADR-0021), the
electrical twin of the mass–spring oscillator. A charged capacitor $C$ discharges through an inductor $L$;
the charge $Q(t)$ and the current $I(t)$ oscillate forever (no resistance, no decay), and **the current is the
slope of the charge** — exactly as velocity is the slope of position, and exactly as in RC charging, one rung up.

The algebra-based course hands you the period $T = 2\\pi\\sqrt{LC}$ and the fact that the circuit "rings" as
rules. The calculus shows where they come from: Kirchhoff's voltage law $L\\,dI/dt + Q/C = 0$ with $I = dQ/dt$ is
the second-order ODE $L\\,d^2Q/dt^2 + Q/C = 0$ — the same shape as the spring's $x'' = -\\omega^2 x$. Its solution
is $Q(t) = Q_0\\cos(\\omega t)$ with $\\omega = 1/\\sqrt{LC}$; differentiating gives $I(t) = -Q_0\\omega\\sin(\\omega t)$.
Energy sloshes between the capacitor ($Q^2/2C$) and the inductor ($\\tfrac12 LI^2$) while the total stays fixed.

Proof kind `governing`: the current is the slope of the charge ($I = dQ/dt$); the charge solves the LC equation
($L\\,Q'' + Q/C = 0$); energy is conserved — the capacitor + inductor energies sum to the initial $Q_0^2/2C$ at
every instant; the period is $T = 2\\pi\\sqrt{LC}$ (so $Q(t+T) = Q(t)$); and a quarter period in, the capacitor is
empty while the current peaks — charge and current are $90^\\circ$ out of phase.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import Panel, Scenario, Slider, make_result

t = sp.Symbol("t", nonnegative=True, real=True)   # time (the shared axis)
L = sp.Symbol("L", positive=True)                 # inductance, H (slider — sets the period with C)
C = sp.Symbol("C", positive=True)                 # capacitance, F (constant)
Q0 = sp.Symbol("Q0", positive=True)               # initial charge amplitude, C (slider — sets the height)

PROOF_DOMAIN = SampleDomain(
    bounds={t: (0.001, 0.02), L: (0.005, 0.05), C: (5e-5, 2e-4), Q0: (0.005, 0.02)},
    positive={L, C, Q0},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("L", "C", "Q0"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: lc-oscillation requires parameters.{key}")
    L_val, C_val, Q0_val = sp.nsimplify(p["L"]), sp.nsimplify(p["C"]), sp.nsimplify(p["Q0"])

    omega = 1 / sp.sqrt(L * C)
    period = 2 * sp.pi * sp.sqrt(L * C)
    Q = Q0 * sp.cos(omega * t)                      # charge on the capacitor
    I = sp.diff(Q, t)                               # current = dQ/dt = -Q0·ω·sin(ωt)
    energy = Q**2 / (2 * C) + L * I**2 / 2          # capacitor energy + inductor energy

    checks_spec = [
        ("current_is_slope",
         r"The current is the slope of the charge: $I = \dfrac{dQ}{dt}$ — exactly as velocity is the slope of position.",
         I - sp.diff(Q, t)),
        ("governing_eqn",
         r"The charge solves the LC equation $L\,\dfrac{d^2Q}{dt^2} + \dfrac{Q}{C} = 0$ — the electrical twin of the spring's $x'' = -\omega^2 x$.",
         L * sp.diff(Q, t, 2) + Q / C),
        ("energy_conserved",
         r"Energy trades between the capacitor $\tfrac{Q^2}{2C}$ and the inductor $\tfrac12 LI^2$; the total stays at the initial $\tfrac{Q_0^2}{2C}$.",
         energy - Q0**2 / (2 * C)),
        ("period",
         r"The period is $T = 2\pi\sqrt{LC}$: a full cycle later the charge repeats, $Q(t+T) = Q(t)$.",
         Q.subs(t, t + period) - Q),
        ("quarter_phase",
         r"A quarter period in, the capacitor is empty ($Q = 0$) while the current peaks — charge and current are $90^\circ$ out of phase.",
         Q.subs(t, period / 4)),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"lc-oscillation/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "The current is the slope of the charge, and the charge solves the LC equation — the "
                   "mass–spring oscillator, one domain over.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $I = dQ/dt$; check $L\,Q'' + Q/C = 0$; energy $\tfrac{Q^2}{2C} + \tfrac12 LI^2$ "
                  r"constant; $T = 2\pi\sqrt{LC}$; quarter-period $90^\circ$ phase",
        "checks": checks,
    }

    rsubs = {L: L_val, C: C_val, Q0: Q0_val}
    omega_r = make_result(omega, rsubs, "1/s", r"Angular frequency $\omega = 1/\sqrt{LC}$")
    omega_r["symbolic_latex"] = r"\dfrac{1}{\sqrt{LC}}"
    period_r = make_result(period, rsubs, "s", r"Period $T = 2\pi\sqrt{LC}$")
    period_r["symbolic_latex"] = r"2\pi\sqrt{LC}"
    ipeak = make_result(Q0 * omega, rsubs, "A", r"Peak current $I_{\max} = Q_0\omega = Q_0/\sqrt{LC}$")
    ipeak["symbolic_latex"] = r"\dfrac{Q_0}{\sqrt{LC}}"
    emax = make_result(Q0**2 / (2 * C), rsubs, "J", r"Total energy $E = Q_0^2/2C$ (constant)")
    emax["symbolic_latex"] = r"\dfrac{Q_0^2}{2C}"
    result = {"angular_frequency": omega_r, "period": period_r, "peak_current": ipeak, "total_energy": emax}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (a ringing circuit and a period)",
                "latex": r"Q(t) = Q_0\cos(\omega t), \qquad T = 2\pi\sqrt{LC}, \qquad \omega = \frac{1}{\sqrt{LC}}",
                "prose": "An LC circuit oscillates: with no resistance to dissipate energy, the charge and "
                         "current swing back and forth forever at angular frequency $\\omega = 1/\\sqrt{LC}$, "
                         "period $T = 2\\pi\\sqrt{LC}$. You are handed the period as a rule — the same form as the "
                         "spring's $T = 2\\pi\\sqrt{m/k}$ — with no account of *why* the circuit rings or where "
                         "$\\omega = 1/\\sqrt{LC}$ comes from.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "Kirchhoff's voltage law is a second-order differential equation",
                "latex": r"L\,\frac{dI}{dt} + \frac{Q}{C} = 0, \quad I = \frac{dQ}{dt} \ \Longrightarrow\ L\,\frac{d^2Q}{dt^2} + \frac{Q}{C} = 0",
                "prose": "Around the loop, the inductor's back-EMF $L\\,dI/dt$ balances the capacitor voltage "
                         "$Q/C$. Because the current is the rate of change of charge, $I = dQ/dt$, this is a "
                         "*second-order* differential equation for $Q(t)$ — the exact shape of the mass–spring "
                         "equation $x'' = -\\omega^2 x$, with $\\omega^2 = 1/(LC)$.",
            },
            {
                "label": "Solving it gives the oscillation; its slope is the current",
                "latex": r"Q(t) = Q_0\cos(\omega t),\ \ \omega = \frac{1}{\sqrt{LC}} \ \Longrightarrow\ I(t) = \frac{dQ}{dt} = -Q_0\,\omega\sin(\omega t)",
                "prose": "The solution is a cosine at $\\omega = 1/\\sqrt{LC}$ — so $T = 2\\pi\\sqrt{LC}$ falls "
                         "straight out of the equation. Differentiating the charge gives the current: it lags a "
                         "quarter cycle behind, peaking when the charge is zero. The current is the *slope* of "
                         "the charge.",
                "emphasis": True,
            },
            {
                "label": "Watch the two panels — I is the slope of Q, and energy sloshes",
                "latex": r"\boxed{\,I(t) = \frac{dQ}{dt}\,}\qquad \frac{Q^2}{2C} + \tfrac12 LI^2 = \text{const}",
                "prose": "Drag $L$ or $Q_0$: the charge $Q$ and current $I$ oscillate, and at every instant the "
                         "slope of the upper $Q$–$t$ curve is the value of the lower $I$–$t$ curve — the same "
                         "relationship as position and velocity, in a circuit. The energy trades between the "
                         "capacitor ($Q^2/2C$, full when $Q$ peaks) and the inductor ($\\tfrac12 LI^2$, full when "
                         "$I$ peaks) while the total stays fixed. Raising $L$ stretches the period $2\\pi\\sqrt{LC}$.",
            },
        ],
    }

    panels = [
        Panel(key="Q", expr=Q, label="Q  (C)", unit="C", accent=False),
        Panel(key="I", expr=I, label="I  (A)", unit="A", accent=True),
    ]

    return Scenario(
        regime=2,
        constants_export={"L": float(L_val), "C": float(C_val), "Q0": float(Q0_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        t=t,
        constants={C: C_val},
        unit_map={L: "H", C: "F", Q0: "C", t: "s"},
        sliders=[Slider(L, "L", 0.005, 0.05, float(L_val)), Slider(Q0, "Q0", 0.005, 0.02, float(Q0_val))],
        t_window=0.015,
        window_mode="fixed",
        initial_conditions={"Q0": float(Q0_val), "I0": 0.0},
        panels=panels,
    )
