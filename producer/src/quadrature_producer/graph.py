"""Matplotlib renders the stacked x–t / v–t / a–t SVG at build time (committed asset).

The browser never runs Matplotlib; interactive graphs are redrawn in JS from the closed
form. This static SVG is the no-JS poster and a visual proof of the slope↔value /
area↔change relationships (brief §5). up positive; shared time axis.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, deterministic
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import sympy as sp  # noqa: E402

from .kinematics import Model, a, t, v0, x0


def render_stack(model: Model, out_path: Path, t_max: float) -> None:
    a_val = float(model.subs[a])
    x0_val = float(model.subs[x0])
    v0_val = float(model.subs[v0])
    apex_t = float(sp.N(model.unknowns["apex_time"].subs(model.subs)))
    apex_x = float(sp.N(model.unknowns["max_height"].subs(model.subs)))

    ts = np.linspace(0.0, t_max, 240)
    xs = x0_val + v0_val * ts + 0.5 * a_val * ts**2
    vs = v0_val + a_val * ts
    as_ = np.full_like(ts, a_val)

    fig, (ax_x, ax_v, ax_a) = plt.subplots(
        3, 1, figsize=(6.2, 7.0), sharex=True, gridspec_kw={"hspace": 0.12}
    )
    ink, accent, faint = "#1f2933", "#2f6f4f", "#c9d6cf"

    # x–t (parabola); mark the apex
    ax_x.plot(ts, xs, color=ink, lw=2)
    ax_x.scatter([apex_t], [apex_x], color=accent, zorder=5)
    ax_x.annotate(f"apex: x = {apex_x:g} m at t = {apex_t:g} s",
                  (apex_t, apex_x), textcoords="offset points", xytext=(8, -4),
                  fontsize=8, color=accent)
    ax_x.set_ylabel("x  (m)")
    ax_x.axhline(0, color=faint, lw=1)

    # v–t (line); shade the area to the apex (= displacement) and mark v=0 with slope unchanged
    ax_v.plot(ts, vs, color=ink, lw=2)
    mask = ts <= apex_t
    ax_v.fill_between(ts[mask], vs[mask], color=accent, alpha=0.15)
    ax_v.annotate("area under v = change in x", (apex_t / 2, v0_val / 2),
                  fontsize=8, color=accent, ha="center")
    ax_v.scatter([apex_t], [0.0], color=accent, zorder=5)
    ax_v.annotate("v = 0 here, but the line never bends:\nits slope (= a) is unchanged",
                  (apex_t, 0.0), textcoords="offset points", xytext=(8, 10), fontsize=8, color=accent)
    ax_v.set_ylabel("v  (m/s)")
    ax_v.axhline(0, color=faint, lw=1)

    # a–t (flat, nonzero everywhere)
    ax_a.plot(ts, as_, color=ink, lw=2)
    ax_a.annotate(f"a = {a_val:g} m/s²  (constant, never zero)", (t_max * 0.45, a_val),
                  textcoords="offset points", xytext=(0, 8), fontsize=8, color=accent, ha="center")
    ax_a.set_ylabel("a  (m/s²)")
    ax_a.set_xlabel("t  (s)")
    ax_a.axvline(apex_t, color=faint, lw=1, ls="--")
    ax_v.axvline(apex_t, color=faint, lw=1, ls="--")
    ax_x.axvline(apex_t, color=faint, lw=1, ls="--")

    for ax in (ax_x, ax_v, ax_a):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.margins(x=0)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight")
    plt.close(fig)
