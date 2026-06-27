"""Regime-2 model: radioactive decay — a two-panel temporal stack N–t over dN/dt–t (ADR-0021), opening the
modern-physics unit. A sample of $N_0$ nuclei decays; the number remaining is $N(t) = N_0 e^{-\\lambda t}$ and
the rate of change $dN/dt = -\\lambda N$ is the panel below — the decay rate IS the slope of $N$.

The algebra-based course hands you the half-life $t_{1/2} = \\ln 2 / \\lambda$ as a rule. The calculus shows
where it comes from: each nucleus decays independently, so the number that decay per second is proportional to
how many are left, $dN/dt = -\\lambda N$ — a first-order ODE whose solution is the exponential $N_0 e^{-\\lambda t}$.
The same exponential family as RC charging and linear drag, one domain over. Proof kind `governing`.
"""

from __future__ import annotations

import sympy as sp

from ..prove import SampleDomain, tiered_zero
from .base import Panel, Scenario, Slider, make_result

t = sp.Symbol("t", nonnegative=True, real=True)   # time
lam = sp.Symbol("lambda", positive=True)          # decay constant, 1/s (slider)
N0 = sp.Symbol("N0", positive=True)               # initial number of nuclei (slider)

PROOF_DOMAIN = SampleDomain(
    bounds={t: (0.0, 8.0), lam: (0.1, 1.5), N0: (100.0, 5000.0)},
    positive={lam, N0},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    lam_val = sp.nsimplify(p.get("lam", 0.5))
    N0_val = sp.nsimplify(p.get("N0", 1000))

    N = N0 * sp.exp(-lam * t)                       # nuclei remaining
    dNdt = sp.diff(N, t)                            # = -λN, the decay rate (the lower panel)

    checks_spec = [
        ("rate_is_slope",
         r"The decay rate is the slope of $N$: the lower panel is $\dfrac{dN}{dt}$ exactly, the derivative of the curve above.",
         dNdt - sp.diff(N, t)),
        ("governing_eqn",
         r"Each nucleus decays independently, so the rate is proportional to how many remain: $\dfrac{dN}{dt} = -\lambda N$.",
         dNdt + lam * N),
        ("half_life",
         r"The half-life is $t_{1/2} = \dfrac{\ln 2}{\lambda}$: after it, exactly half remain, $N(t_{1/2}) = N_0/2$.",
         N.subs(t, sp.log(2) / lam) - N0 / 2),
        ("mean_lifetime",
         r"After one mean lifetime $\tau = 1/\lambda$, a fraction $1/e$ of the sample remains.",
         N.subs(t, 1 / lam) - N0 / sp.E),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"decay/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "The decay rate is proportional to the number remaining — and that rate is the slope of "
                   "$N(t)$, the panel below.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $dN/dt$ is the slope; check $dN/dt = -\lambda N$; $t_{1/2} = \ln 2/\lambda$; "
                  r"$1/e$ left after $\tau = 1/\lambda$",
        "checks": checks,
    }

    rsubs = {lam: lam_val, N0: N0_val}
    thalf = make_result(sp.log(2) / lam, rsubs, "s", r"Half-life $t_{1/2} = \ln 2 / \lambda$")
    thalf["symbolic_latex"] = r"\ln 2 / \lambda"
    tau = make_result(1 / lam, rsubs, "s", r"Mean lifetime $\tau = 1/\lambda$")
    tau["symbolic_latex"] = r"1/\lambda"
    rate0 = make_result(lam * N0, rsubs, "1/s", r"Initial decay rate $\lambda N_0$")
    rate0["symbolic_latex"] = r"\lambda N_0"
    left5 = make_result(N.subs(t, 5), rsubs, "1", r"Nuclei left after 5 s")
    left5["symbolic_latex"] = r"N_0 e^{-5\lambda}"
    result = {"half_life": thalf, "mean_lifetime": tau, "initial_rate": rate0, "left_at_5s": left5}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (a half-life)",
                "latex": r"N(t) = N_0\,2^{-t/t_{1/2}}, \qquad t_{1/2} = \frac{\ln 2}{\lambda}",
                "prose": "The sample halves every half-life $t_{1/2}$: after one $t_{1/2}$ half is left, after two "
                         "a quarter, and so on. You are handed the half-life and the decay curve as rules, with "
                         "no account of *why* decay is exponential.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "The decay rate is proportional to the number remaining",
                "latex": r"\frac{dN}{dt} = -\lambda N",
                "prose": "Each nucleus has the same fixed chance per second of decaying, so the number decaying "
                         "per second is proportional to how many are left. That is a first-order differential "
                         "equation — the rate $dN/dt$ depends on $N$ itself.",
            },
            {
                "label": "Solving it gives the exponential; the rate is the slope",
                "latex": r"N(t) = N_0\,e^{-\lambda t} \ \Longrightarrow\ \frac{dN}{dt} = -\lambda N_0\,e^{-\lambda t}",
                "prose": "The solution is an exponential, and the half-life $t_{1/2} = \\ln 2/\\lambda$ falls out "
                         "of it. The decay rate is the *slope* of $N(t)$ — the same exponential machine as a "
                         "discharging capacitor or a body slowing under drag, in the nucleus.",
                "emphasis": True,
            },
            {
                "label": "Watch the two panels — the lower is the slope of the upper",
                "latex": r"\boxed{\,\frac{dN}{dt} = -\lambda N\,}",
                "prose": "Drag $\\lambda$: a larger decay constant means a shorter half-life and a steeper fall. "
                         "At every instant the slope of the upper $N$–$t$ curve is the value of the lower "
                         "$dN/dt$–$t$ curve, and the area under $dN/dt$ is the number that have decayed. The "
                         "activity a Geiger counter reads is the magnitude $|dN/dt| = \\lambda N$.",
            },
        ],
    }

    panels = [
        Panel(key="N", expr=N, label="N  (nuclei)", unit="1", accent=False),
        Panel(key="dNdt", expr=dNdt, label="dN/dt  (1/s)", unit="1/s", accent=True),
    ]

    return Scenario(
        regime=2,
        constants_export={"lam": float(lam_val), "N0": float(N0_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        t=t,
        constants={},
        unit_map={lam: "1/s", N0: "1", t: "s"},
        sliders=[Slider(lam, "lambda", 0.1, 1.5, float(lam_val)), Slider(N0, "N0", 500.0, 2000.0, float(N0_val))],
        t_window=6.0,
        window_mode="fixed",
        initial_conditions={"N_start": float(N0_val)},
        panels=panels,
    )
