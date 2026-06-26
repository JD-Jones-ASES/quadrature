"""Matplotlib renders the stacked x–t / v–t / a–t SVG at build time (committed asset). Model-agnostic.

The browser never runs Matplotlib; interactive graphs are redrawn in JS from the closed form. This static SVG
is the no-JS poster and a visual proof of the slope↔value / area↔change relationships (brief §5).

Human-eye QC rules baked in: explicit per-panel y-limits with headroom; the a–t panel always includes y = 0
(so a constant nonzero a reads as clearly nonzero); model-supplied markers/guides/shades, each annotation in a
paper-colored bbox so text never collides with the curves.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, deterministic
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import sympy as sp  # noqa: E402

PAPER = "#fbfaf7"
INK = "#1f2933"
ACCENT = "#2f6f4f"
GRID = "#d8d4c8"
FAINT = "#8a929b"


def _bbox():
    return dict(boxstyle="round,pad=0.28", fc=PAPER, ec=GRID, lw=0.6, alpha=0.92)


def render_stack(scn, out_path: Path, t_max: float) -> None:
    # substitute constants + slider defaults; only t remains free
    base = dict(scn.constants)
    for sl in scn.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    t = scn.t
    fx = sp.lambdify(t, scn.x_expr.subs(base), "numpy")
    fv = sp.lambdify(t, scn.v_expr.subs(base), "numpy")
    fa = sp.lambdify(t, scn.a_expr.subs(base), "numpy")
    fns = {"x": fx, "v": fv, "a": fa}

    ts = np.linspace(0.0, t_max, 240)
    series = {k: np.broadcast_to(np.asarray(fn(ts), dtype=float), ts.shape) for k, fn in fns.items()}

    fig, axes = plt.subplots(3, 1, figsize=(6.4, 7.8), sharex=True,
                             gridspec_kw={"hspace": 0.16}, facecolor=PAPER)
    panels = {"x": axes[0], "v": axes[1], "a": axes[2]}

    def ylim(arr, key):
        lo, hi = float(np.min(arr)), float(np.max(arr))
        if key == "a":
            lo, hi = min(lo, 0.0), max(hi, 0.0)  # a-panel always shows zero
        span = (hi - lo) or 1.0
        return lo - span * 0.16, hi + span * 0.20

    color = {"x": INK, "v": ACCENT, "a": INK}
    for key, ax in panels.items():
        ax.set_facecolor(PAPER)
        ax.set_ylabel(dict(zip(("x", "v", "a"), scn.labels))[key], fontsize=10, color=INK)
        ax.set_xlim(0, t_max)
        ax.set_ylim(*ylim(series[key], key))
        ax.tick_params(colors=FAINT, labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.axhline(0, color=GRID, lw=1)
        for g in scn.guides:
            ax.axvline(float(g), color=FAINT, lw=1, ls="--", alpha=0.7)
        ax.plot(ts, series[key], color=color[key], lw=2.2)

    for sh in scn.shades:
        ax = panels[sh.panel]
        m = (ts >= sh.t0) & (ts <= sh.t1)
        ax.fill_between(ts[m], series[sh.panel][m], color=ACCENT, alpha=0.16, lw=0)

    for mk in scn.markers:
        ax = panels[mk.panel]
        y = float(fns[mk.panel](mk.t))
        if mk.dot:
            ax.scatter([mk.t], [y], color=ACCENT, zorder=5)
        ax.annotate(mk.label, (mk.t, y), textcoords="offset points", xytext=(mk.dx, mk.dy),
                    ha=mk.ha, va=mk.va, fontsize=8.3, color=INK, bbox=_bbox())

    axes[2].set_xlabel("t  (s)", fontsize=10, color=INK)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
