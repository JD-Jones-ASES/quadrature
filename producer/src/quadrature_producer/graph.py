"""Matplotlib renders the stacked x–t / v–t / a–t SVG at build time (committed asset).

The browser never runs Matplotlib; interactive graphs are redrawn in JS from the closed
form. This static SVG is the no-JS poster and a visual proof of the slope↔value /
area↔change relationships (brief §5). up positive; shared time axis.

Human-eye QC rules baked in (so text never collides with the curves):
  - every panel gets explicit y-limits with headroom for its label;
  - the a–t panel is scaled to INCLUDE y = 0, so "a is never zero" is visually obvious
    (the flat line sits well below the zero axis) rather than hidden in a tight band;
  - annotations live in open regions and carry a paper-colored bbox for legibility.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless, deterministic
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import sympy as sp  # noqa: E402

from .kinematics import Model, a, t, v0, x0

PAPER = "#fbfaf7"
INK = "#1f2933"
ACCENT = "#2f6f4f"
GRID = "#d8d4c8"
FAINT = "#8a929b"


def _bbox():
    return dict(boxstyle="round,pad=0.28", fc=PAPER, ec=GRID, lw=0.6, alpha=0.92)


def _limits(lo, hi, pad_lo=0.12, pad_hi=0.12, floor=None, ceil=None):
    span = hi - lo or 1.0
    out_lo = lo - span * pad_lo
    out_hi = hi + span * pad_hi
    if floor is not None:
        out_lo = min(out_lo, floor)
    if ceil is not None:
        out_hi = max(out_hi, ceil)
    return out_lo, out_hi


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
        3, 1, figsize=(6.4, 7.8), sharex=True, gridspec_kw={"hspace": 0.16},
        facecolor=PAPER,
    )

    def style(ax, ylabel, ylim):
        ax.set_facecolor(PAPER)
        ax.set_ylabel(ylabel, fontsize=10, color=INK)
        ax.set_ylim(*ylim)
        ax.set_xlim(0, t_max)
        ax.tick_params(colors=FAINT, labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.axvline(apex_t, color=FAINT, lw=1, ls="--", alpha=0.7)  # shared apex guide

    # --- x–t: parabola + apex marked (label placed inside, under the peak) ---
    x_lo, x_hi = _limits(min(xs.min(), 0.0), apex_x, pad_hi=0.10)
    style(ax_x, "x  (m)", (x_lo, x_hi))
    ax_x.axhline(0, color=GRID, lw=1)
    ax_x.plot(ts, xs, color=INK, lw=2.2)
    ax_x.scatter([apex_t], [apex_x], color=ACCENT, zorder=5)
    ax_x.annotate(f"apex: {apex_x:g} m at t = {apex_t:g} s", (apex_t, apex_x),
                  textcoords="offset points", xytext=(0, -14), ha="center", va="top",
                  fontsize=8.5, color=ACCENT, bbox=_bbox())

    # --- v–t: line, shaded area to apex (= displacement), v=0 with slope unchanged ---
    v_lo, v_hi = _limits(vs.min(), v0_val, pad_lo=0.14, pad_hi=0.22)
    style(ax_v, "v  (m/s)", (v_lo, v_hi))
    ax_v.axhline(0, color=GRID, lw=1)
    mask = ts <= apex_t
    ax_v.fill_between(ts[mask], vs[mask], color=ACCENT, alpha=0.16, lw=0)
    ax_v.plot(ts, vs, color=ACCENT, lw=2.2)
    ax_v.scatter([apex_t], [0.0], color=ACCENT, zorder=5)
    # area label low inside the triangle; v=0 note up-right in open space above the falling line
    ax_v.annotate("area under v\n= rise in x", (apex_t * 0.30, v0_val * 0.16),
                  ha="center", va="center", fontsize=8, color=ACCENT, bbox=_bbox())
    ax_v.annotate("v = 0 here — but the line\nnever bends: its slope is a",
                  (apex_t, 0.0), textcoords="offset points", xytext=(12, 16),
                  ha="left", va="bottom", fontsize=8, color=INK, bbox=_bbox())

    # --- a–t: flat line, scaled to INCLUDE 0 so "never zero" is obvious ---
    pad = max(2.0, abs(a_val) * 0.25)
    style(ax_a, "a  (m/s²)", (a_val - pad, pad))
    ax_a.axhline(0, color=GRID, lw=1)
    ax_a.plot(ts, as_, color=INK, lw=2.2)
    ax_a.annotate(f"a = {a_val:g} m/s²  — constant, and never zero", (t_max * 0.5, a_val),
                  textcoords="offset points", xytext=(0, 12), ha="center", va="bottom",
                  fontsize=8.5, color=INK, bbox=_bbox())
    ax_a.annotate("zero is up here", (t_max * 0.02, 0.0), textcoords="offset points",
                  xytext=(2, -2), ha="left", va="top", fontsize=7.5, color=FAINT)
    ax_a.set_xlabel("t  (s)", fontsize=10, color=INK)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
