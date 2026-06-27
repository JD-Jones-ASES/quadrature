"""Regime-2 model: Faraday induction in a rotating coil — the AC generator — as a TWO-panel Φ–t / EMF–t stack
(ADR-0021). A coil of area $A$ spins at angular velocity $\\omega$ in a uniform field $B$, so the flux through it
is $\\Phi(t) = BA\\cos(\\omega t)$ and the **induced EMF is its (negative) rate of change**,
$\\mathcal{E} = -d\\Phi/dt = BA\\omega\\sin(\\omega t)$ — a sinusoid a quarter cycle ahead of the flux. This is how a
generator turns rotation into alternating current.

The algebra-based course hands you Faraday's law $\\mathcal{E} = -N\\,\\Delta\\Phi/\\Delta t$ as a rule and computes
*average* EMFs. The calculus gives the *instantaneous* EMF as the slope of the flux: differentiate the cosine
flux and a sine EMF falls out, $90^\\circ$ out of phase. Plotted as a stacked Φ–t over EMF–t, the slope of the
flux at every instant *is* the (negated) EMF, and integrating the EMF recovers the change in flux — the same
slope↔value / area↔change pivot as the kinematics stack, one domain over.

Proof kind `governing`: the EMF is the negative slope of the flux ($\\mathcal{E} = -d\\Phi/dt$); integrating the
EMF recovers the flux change ($\\int_0^t \\mathcal{E}\\,dt' = -\\Delta\\Phi$); the peak EMF is $BA\\omega$; the EMF is
zero exactly when the flux peaks ($90^\\circ$ phase); and the generator repeats with period $T = 2\\pi/\\omega$.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import Panel, Scenario, Slider, make_result

t = sp.Symbol("t", nonnegative=True, real=True)   # time (the shared axis)
B = sp.Symbol("B", positive=True)                 # magnetic flux density, T (slider — sets the amplitude)
A = sp.Symbol("A", positive=True)                 # coil area, m² (constant)
omega = sp.Symbol("omega", positive=True)         # rotation rate, rad/s (slider — sets the frequency)
_w = sp.Symbol("w", nonnegative=True)             # dummy integration variable

PROOF_DOMAIN = SampleDomain(
    bounds={t: (0.05, 2.0), B: (0.1, 2.0), A: (0.01, 0.5), omega: (2.0, 20.0)},
    positive={B, A, omega},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("B", "A", "omega"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: faraday-induction requires parameters.{key}")
    B_val, A_val, omega_val = sp.nsimplify(p["B"]), sp.nsimplify(p["A"]), sp.nsimplify(p["omega"])

    Phi = B * A * sp.cos(omega * t)                 # flux through the rotating coil
    EMF = B * A * omega * sp.sin(omega * t)         # induced EMF = -dΦ/dt
    period = 2 * sp.pi / omega

    checks_spec = [
        ("emf_is_slope",
         r"The EMF is the negative slope of the flux: $\mathcal{E} = -\dfrac{d\Phi}{dt}$ (Faraday's law).",
         EMF + sp.diff(Phi, t)),
        ("flux_is_integral",
         r"Integrating the EMF recovers the change in flux: $\int_0^t \mathcal{E}\,dt' = -\Delta\Phi$ — the area↔change pivot, one domain over.",
         (Phi.subs(t, 0) - Phi) - sp.integrate(EMF.subs(t, _w), (_w, 0, t))),
        ("peak_emf",
         r"The peak EMF is $\mathcal{E}_0 = BA\omega$, reached a quarter period in (when the flux crosses zero).",
         EMF.subs(t, sp.pi / (2 * omega)) - B * A * omega),
        ("phase_90",
         r"The EMF is zero exactly when the flux is at its peak (here $t=0$) — the slope of a cosine at its crest is flat, so flux and EMF are $90^\circ$ out of phase.",
         EMF.subs(t, 0)),
        ("period",
         r"The generator repeats every period $T = 2\pi/\omega$: $\Phi(t+T) = \Phi(t)$.",
         Phi.subs(t, t + period) - Phi),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"faraday/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "The induced EMF is the slope of the flux — Faraday's law as the slope↔value pivot, with the "
                   "AC sinusoid falling out of a rotating coil.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\mathcal{E} = -d\Phi/dt$; check $\int_0^t \mathcal{E}\,dt' = -\Delta\Phi$; "
                  r"peak $\mathcal{E}_0 = BA\omega$; $90^\circ$ phase; period $T = 2\pi/\omega$",
        "checks": checks,
    }

    rsubs = {B: B_val, A: A_val, omega: omega_val}
    peak = make_result(B * A * omega, rsubs, "V", r"Peak EMF $\mathcal{E}_0 = BA\omega$")
    peak["symbolic_latex"] = r"BA\omega"
    flux_amp = make_result(B * A, rsubs, "Wb", r"Peak flux $\Phi_0 = BA$")
    flux_amp["symbolic_latex"] = r"BA"
    period_r = make_result(period, rsubs, "s", r"Period $T = 2\pi/\omega$")
    period_r["symbolic_latex"] = r"\dfrac{2\pi}{\omega}"
    result = {"peak_emf": peak, "peak_flux": flux_amp, "period": period_r}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (Faraday's law as a rule)",
                "latex": r"\mathcal{E} = -N\,\frac{\Delta\Phi}{\Delta t}, \qquad \Phi = BA\cos(\omega t)",
                "prose": "Faraday's law says the induced EMF is set by how fast the flux changes. The "
                         "algebra-based course uses it to find *average* EMFs over an interval — flux change "
                         "divided by time — and hands you the result that a coil spinning in a field makes "
                         "alternating current, with no account of the instant-by-instant shape.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "The instantaneous EMF is the derivative of the flux",
                "latex": r"\mathcal{E}(t) = -\frac{d\Phi}{dt}, \quad \Phi(t) = BA\cos(\omega t)",
                "prose": "Faraday's law in its exact form uses the *instantaneous* rate of change — a derivative, "
                         "not a ratio of finite changes. For a coil rotating at constant $\\omega$, the flux is a "
                         "cosine, $\\Phi = BA\\cos(\\omega t)$.",
            },
            {
                "label": "Differentiate the flux — a sine EMF falls out, 90° ahead",
                "latex": r"\mathcal{E}(t) = -\frac{d}{dt}\big[BA\cos(\omega t)\big] = BA\omega\sin(\omega t)",
                "prose": "Differentiating the cosine gives a sine: the EMF is $BA\\omega\\sin(\\omega t)$, with peak "
                         "$\\mathcal{E}_0 = BA\\omega$. Because the derivative of a cosine is a sine, the EMF is a "
                         "quarter cycle ahead of the flux — when the flux is at its crest, its slope (and so the "
                         "EMF) is zero. The EMF is the *slope* of the flux.",
                "emphasis": True,
            },
            {
                "label": "Watch the two panels — EMF is the slope of Φ",
                "latex": r"\boxed{\,\mathcal{E}(t) = -\frac{d\Phi}{dt}\,}\qquad \int_0^t \mathcal{E}\,dt' = -\Delta\Phi",
                "prose": "Drag $B$ or $\\omega$: the flux $\\Phi$ and EMF oscillate, and at every instant the "
                         "(negated) slope of the upper $\\Phi$–$t$ curve is the value of the lower EMF–$t$ curve. "
                         "The area under the EMF is the flux change. Raising $\\omega$ packs more cycles in and "
                         "raises the peak EMF $BA\\omega$ — spin a generator faster and it makes more voltage.",
            },
        ],
    }

    panels = [
        Panel(key="Phi", expr=Phi, label="Φ  (Wb)", unit="Wb", accent=False),
        Panel(key="EMF", expr=EMF, label="EMF  (V)", unit="V", accent=True),
    ]

    return Scenario(
        regime=2,
        constants_export={"B": float(B_val), "A": float(A_val), "omega": float(omega_val)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        t=t,
        constants={A: A_val},
        unit_map={B: "T", A: "m**2", omega: "1/s", t: "s"},
        sliders=[Slider(B, "B", 0.1, 2.0, float(B_val)), Slider(omega, "omega", 2.0, 20.0, float(omega_val))],
        t_window=1.5,
        window_mode="fixed",
        initial_conditions={"Phi0": float(B_val * A_val), "EMF0": 0.0},
        panels=panels,
    )
