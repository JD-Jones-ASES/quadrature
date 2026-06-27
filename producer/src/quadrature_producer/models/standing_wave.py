"""Regime-3 model: standing waves on a string fixed at both ends — the spatial mode instrument (ADR-0023, the
6th graph instrument). Opens Waves & optics.

The algebra-based course hands you the harmonic series as rules: the allowed standing waves on a string of
length $L$ have wavelengths $\\lambda_n = 2L/n$ and frequencies $f_n = nv/(2L)$, for $n = 1, 2, 3, \\ldots$ —
and you memorize that only integer multiples of the fundamental appear. *Why* only integers? That is the
calculus underpinning this lesson surfaces (Phase-3 policy: surface it where it is honest).

A wave on the string obeys the wave equation $\\partial_{tt} y = v^2\\,\\partial_{xx} y$. Its standing solutions
separate as $y(x,t) = A\\sin(kx)\\cos(\\omega t)$ with $\\omega = vk$. The string is *pinned at both ends*, so
$y(0,t) = y(L,t) = 0$; the first is automatic, and the second forces $\\sin(kL) = 0$, i.e. $kL = n\\pi$. Only the
discrete $k_n = n\\pi/L$ fit a whole number of half-wavelengths between the walls — the boundary conditions
**quantize** the modes, and $f_n = \\omega_n/2\\pi = nv/(2L)$ falls straight out. A standing wave is also two
counter-propagating travelling waves superposed: $\\tfrac12 A[\\sin(kx-\\omega t) + \\sin(kx+\\omega t)] =
A\\sin(kx)\\cos(\\omega t)$, and the nodes are where they always cancel.

Proof kind `governing`: the mode solves the wave equation; the fixed-end boundary condition holds (the
quantization $\\sin(kL)=\\sin(n\\pi)=0$); the standing wave is a superposition of two travelling waves;
$f_n = nv/(2L)$; and $\\lambda_n = 2L/n$.
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import Scenario, StandingPlot, make_result

x = sp.Symbol("x", nonnegative=True, real=True)   # position along the string (the spatial axis)
t = sp.Symbol("t", real=True)                      # time (used only in the proof)
n = sp.Symbol("n", integer=True, positive=True)    # mode number (the slider/cursor)
A = sp.Symbol("A", positive=True)                  # antinode amplitude
L = sp.Symbol("L", positive=True)                  # string length
v = sp.Symbol("v", positive=True)                  # wave speed

PROOF_DOMAIN = SampleDomain(
    bounds={x: (0.05, 0.95), t: (0.1, 2.0), n: (1.0, 5.0), A: (0.5, 2.0), L: (0.8, 1.5), v: (50.0, 200.0)},
    positive={A, L, v},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("L", "v", "A", "n_max", "n_default"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: standing-wave requires parameters.{key}")
    L_val, v_val, A_val = sp.nsimplify(p["L"]), sp.nsimplify(p["v"]), sp.nsimplify(p["A"])
    n_max, n_default = int(p["n_max"]), int(p["n_default"])
    if not (1 <= n_default <= n_max):
        raise BuildError(f"{spec.get('id')}: n_default must be in [1, n_max]")

    k = n * sp.pi / L
    omega = v * k
    y_shape = A * sp.sin(k * x)                      # the spatial mode shape (snapshot at maximum displacement)
    y_full = A * sp.sin(k * x) * sp.cos(omega * t)   # the full standing wave (for the proof)

    checks_spec = [
        ("wave_equation",
         r"The mode solves the wave equation $\partial_{tt} y = v^2\,\partial_{xx} y$ — back-substituting $y = A\sin(kx)\cos(\omega t)$ leaves zero, with $\omega = vk$.",
         sp.diff(y_full, t, 2) - v**2 * sp.diff(y_full, x, 2)),
        ("fixed_ends",
         r"The string is pinned at both ends: $y(0)=0$ automatically, and $y(L)=0$ forces $\sin(kL)=\sin(n\pi)=0$ — the boundary condition that quantizes the modes to integer $n$.",
         y_shape.subs(x, L)),
        ("superposition",
         r"A standing wave is two counter-propagating travelling waves superposed: $\tfrac12 A[\sin(kx-\omega t)+\sin(kx+\omega t)] = A\sin(kx)\cos(\omega t)$.",
         (A / 2) * (sp.sin(k * x - omega * t) + sp.sin(k * x + omega * t)) - y_full),
        ("frequency",
         r"The harmonic frequencies fall out: $f_n = \omega_n/2\pi = nv/(2L)$.",
         omega / (2 * sp.pi) - n * v / (2 * L)),
        ("wavelength",
         r"The wavelengths are $\lambda_n = 2\pi/k_n = 2L/n$ — an integer number of half-wavelengths fits the length.",
         2 * sp.pi / k - 2 * L / n),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"standing-wave/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "The harmonics come from the wave equation plus the fixed ends — the boundary conditions "
                   "quantize the modes, and $f_n = nv/2L$ falls out.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $\partial_{tt}y = v^2\partial_{xx}y$; fixed ends $\sin(kL)=0$; standing = two "
                  r"travelling waves; $f_n = nv/2L$; $\lambda_n = 2L/n$",
        "checks": checks,
    }

    # harmonic table (n, f_n, lam_n) for n = 1..n_max — producer-computed display data
    modes = [{"n": j,
              "f": round(float(j * v_val / (2 * L_val)), 6),
              "lam": round(float(2 * L_val / j), 6)}
             for j in range(1, n_max + 1)]

    rsubs = {A: A_val, L: L_val, v: v_val, n: n_default}
    f1 = make_result(v / (2 * L), {v: v_val, L: L_val}, "Hz", r"Fundamental frequency $f_1 = v/2L$")
    f1["symbolic_latex"] = r"\dfrac{v}{2L}"
    lam1 = make_result(2 * L, {L: L_val}, "m", r"Fundamental wavelength $\lambda_1 = 2L$")
    lam1["symbolic_latex"] = r"2L"
    fn = make_result(n * v / (2 * L), rsubs, "Hz", rf"Frequency of harmonic $n={n_default}$: $f_n = nv/2L$")
    fn["symbolic_latex"] = r"\dfrac{nv}{2L}"
    lamn = make_result(2 * L / n, rsubs, "m", rf"Wavelength of harmonic $n={n_default}$: $\lambda_n = 2L/n$")
    lamn["symbolic_latex"] = r"\dfrac{2L}{n}"
    result = {"fundamental_frequency": f1, "fundamental_wavelength": lam1,
              "nth_frequency": fn, "nth_wavelength": lamn}

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (a harmonic series)",
                "latex": r"f_n = \frac{n v}{2L}, \qquad \lambda_n = \frac{2L}{n}, \qquad n = 1, 2, 3, \ldots",
                "prose": "A string fixed at both ends can only vibrate at a discrete set of frequencies — the "
                         "fundamental $f_1 = v/2L$ and its integer multiples (the harmonics). You are handed the "
                         "series as a rule, with no account of *why* only whole-number multiples appear and not, "
                         "say, $1.5\\,f_1$.",
            },
        ],
        "result": result,
    }
    calculus = {
        "steps": [
            {
                "label": "The string obeys the wave equation; its standing solutions separate",
                "latex": r"\partial_{tt} y = v^2\,\partial_{xx} y \ \Longrightarrow\ y(x,t) = A\sin(kx)\cos(\omega t),\quad \omega = vk",
                "prose": "Every small piece of the string obeys the wave equation. Looking for solutions that "
                         "oscillate in place — a fixed shape times a time wobble — gives $y = A\\sin(kx)"
                         "\\cos(\\omega t)$, which solves it whenever $\\omega = vk$. So far $k$ could be anything.",
            },
            {
                "label": "The fixed ends quantize k — only integer modes fit",
                "latex": r"y(0,t)=y(L,t)=0 \ \Longrightarrow\ \sin(kL)=0 \ \Longrightarrow\ kL = n\pi \ \Longrightarrow\ k_n = \frac{n\pi}{L}",
                "prose": "Now impose the physics: the string is pinned at both ends, so $y=0$ there at all times. "
                         "$y(0)=0$ is automatic; $y(L)=0$ demands $\\sin(kL)=0$, which is only true when $kL$ is a "
                         "whole multiple of $\\pi$. *That* is why $n$ must be an integer — the boundary conditions "
                         "select a discrete ladder of modes. An integer number of half-wavelengths fits the length.",
                "emphasis": True,
            },
            {
                "label": "The harmonic series falls out",
                "latex": r"f_n = \frac{\omega_n}{2\pi} = \frac{v k_n}{2\pi} = \frac{n v}{2L}, \qquad \lambda_n = \frac{2\pi}{k_n} = \frac{2L}{n}",
                "prose": "Each allowed $k_n$ gives a frequency $f_n = nv/2L$ and wavelength $\\lambda_n = 2L/n$ — "
                         "the memorized series, now derived. Drag the mode slider: each harmonic adds one more "
                         "antinode, the nodes (always-still points) stay pinned, and the frequency climbs in "
                         "exact integer steps.",
            },
        ],
    }

    standing = StandingPlot(
        u=x,
        n=n,
        y_expr=y_shape,
        length=float(L_val),
        speed=float(v_val),
        amplitude=float(A_val),
        n_max=n_max,
        n_default=n_default,
        modes=modes,
        constants={A: A_val, L: L_val},
        unit_map={A: "m", x: "m", L: "m", n: "1"},
        u_label="x  (m)",
        y_label="y  (m)",
        annot="The n-th harmonic of a string fixed at both ends: n half-wavelengths, n−1 interior nodes.",
    )

    return Scenario(
        regime=3,
        constants_export={"L": float(L_val), "v": float(v_val), "A": float(A_val),
                          "n_max": float(n_max), "n_default": float(n_default)},
        proof=proof,
        algebra=algebra,
        calculus=calculus,
        standing=standing,
    )
