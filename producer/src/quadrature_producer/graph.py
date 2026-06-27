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


def render_area(area, out_path: Path) -> None:
    """Two-panel poster for the integral instrument (ADR-0014): the integrand f(u) with its area shaded,
    and the accumulated integral g(u) below. The static analogue of the x–t/v–t/a–t stack, off the time
    axis — area under the top IS the value of the bottom; slope of the bottom IS the top."""
    base = dict(area.constants)
    for sl in area.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    u = area.u
    ff = sp.lambdify(u, area.f_expr.subs(base), "numpy")
    gf = sp.lambdify(u, area.g_expr.subs(base), "numpy")
    us = np.linspace(float(area.u0), float(area.u_window), 240)
    fv = np.broadcast_to(np.asarray(ff(us), dtype=float), us.shape)
    gv = np.broadcast_to(np.asarray(gf(us), dtype=float), us.shape)

    fig, axes = plt.subplots(2, 1, figsize=(6.4, 5.6), sharex=True,
                             gridspec_kw={"hspace": 0.14}, facecolor=PAPER)
    (ax_f, ax_g) = axes

    def style(ax, label, arr):
        ax.set_facecolor(PAPER)
        ax.set_ylabel(label, fontsize=10, color=INK)
        ax.set_xlim(float(area.u0), float(area.u_window))
        lo, hi = min(float(np.min(arr)), 0.0), max(float(np.max(arr)), 0.0)
        span = (hi - lo) or 1.0
        ax.set_ylim(lo - span * 0.10, hi + span * 0.20)
        ax.tick_params(colors=FAINT, labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.axhline(0, color=GRID, lw=1)

    style(ax_f, area.f_label, fv)
    style(ax_g, area.g_label, gv)

    # top: integrand with the whole area shaded (the work)
    ax_f.fill_between(us, fv, color=ACCENT, alpha=0.16, lw=0)
    ax_f.plot(us, fv, color=INK, lw=2.2)
    fmid = float(ff((float(area.u0) + float(area.u_window)) / 2))
    ax_f.annotate("shaded area  =  ∫ F dx  =  work W",
                  ((float(area.u0) + float(area.u_window)) / 2, fmid * 0.45),
                  ha="center", va="center", fontsize=8.6, color=INK, bbox=_bbox())

    # bottom: accumulated integral; its slope is the integrand
    ax_g.plot(us, gv, color=ACCENT, lw=2.2)
    uq = float(area.u0) + 0.62 * (float(area.u_window) - float(area.u0))
    ax_g.annotate("slope of W  =  F(x)", (uq, float(gf(uq))), textcoords="offset points",
                  xytext=(8, -2), ha="left", va="top", fontsize=8.6, color=INK, bbox=_bbox())

    ax_g.set_xlabel(area.u_label, fontsize=10, color=INK)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


def render_energy(en, out_path: Path) -> None:
    """Static poster for the energy-exchange instrument: KE(u) rising, PE(u) falling, and their sum (Total) a
    flat line — the visual proof that energy is conserved as the system moves."""
    base = dict(en.constants)
    for sl in en.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    u = en.u
    kf = sp.lambdify(u, en.ke_expr.subs(base), "numpy")
    pf = sp.lambdify(u, en.pe_expr.subs(base), "numpy")
    us = np.linspace(float(en.u0), float(en.u_window), 240)
    kv = np.broadcast_to(np.asarray(kf(us), dtype=float), us.shape)
    pv = np.broadcast_to(np.asarray(pf(us), dtype=float), us.shape)
    tv = kv + pv

    fig, ax = plt.subplots(figsize=(6.6, 4.0), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    ax.fill_between(us, 0, kv, color=ACCENT, alpha=0.16, lw=0)
    ax.plot(us, kv, color=ACCENT, lw=2.2, label=en.ke_label.split("(")[0].strip())
    ax.plot(us, pv, color=INK, lw=2.2, label=en.pe_label.split("(")[0].strip())
    ax.plot(us, tv, color=FAINT, lw=1.8, ls="--", label=en.total_label.split("(")[0].strip())

    hi = max(float(np.max(tv)), 0.0) or 1.0
    ax.set_xlim(float(en.u0), float(en.u_window))
    ax.set_ylim(0.0, hi * 1.18)
    ax.set_xlabel(en.u_label, fontsize=10, color=INK)
    ax.set_ylabel("energy  (J)", fontsize=10, color=INK)
    ax.tick_params(colors=FAINT, labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.legend(frameon=False, fontsize=8.6, loc="center right")
    ax.annotate("Total stays flat — energy is conserved", (float(en.u0) + 0.5 * (float(en.u_window) - float(en.u0)), hi * 1.04),
                ha="center", va="center", fontsize=8.6, color=INK, bbox=_bbox())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


def render_collision(col, out_path: Path) -> None:
    """Static poster for the collision instrument (ADR-0018): two grouped bar charts — total MOMENTUM (before
    vs after, identical: conservation made visible) and total KINETIC ENERGY (before vs after-elastic vs
    after-inelastic, the inelastic bar shorter — the lost energy is the lesson). Each bar is stacked by body,
    so the momentum chart shows the *transfer* between bodies while the total is pinned."""
    base = dict(col.constants)
    for sl in col.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    v1f = col.v1f_expr.subs(base)
    v2f = col.v2f_expr.subs(base)
    m1v = float(base[col.sliders[0].sym])
    m2v = float(col.constants[[s for s in col.constants if str(s) == "m2"][0]])
    v1v = float(col.constants[[s for s in col.constants if str(s) == "v1"][0]])
    v2v = float(col.constants[[s for s in col.constants if str(s) == "v2"][0]])

    def state(ev):
        a = float(v1f.subs(col.u, ev))
        b = float(v2f.subs(col.u, ev))
        return (m1v * a, m2v * b, 0.5 * m1v * a * a, 0.5 * m2v * b * b)

    p1b, p2b = m1v * v1v, m2v * v2v
    k1b, k2b = 0.5 * m1v * v1v * v1v, 0.5 * m2v * v2v * v2v
    p1e, p2e, k1e, k2e = state(1.0)   # elastic
    p1i, p2i, k1i, k2i = state(0.0)   # perfectly inelastic

    fig, (axp, axk) = plt.subplots(1, 2, figsize=(7.0, 4.0), facecolor=PAPER,
                                   gridspec_kw={"wspace": 0.28})

    def stacked(ax, cols, title, ceiling):
        ax.set_facecolor(PAPER)
        for x, (s1, s2, lbl) in cols.items():
            ax.bar(x, s1, width=0.62, color=ACCENT, edgecolor=PAPER, lw=0.5)
            ax.bar(x, s2, width=0.62, bottom=s1, color=INK, edgecolor=PAPER, lw=0.5)
            ax.text(x, s1 + s2 + ceiling * 0.03, f"{s1 + s2:.0f}", ha="center", va="bottom",
                    fontsize=9, color=INK)
        ax.set_xticks(list(range(len(cols))))
        ax.set_xticklabels([c[2] for c in cols.values()], fontsize=8.5, color=INK)
        ax.set_ylim(0, ceiling * 1.20)
        ax.set_title(title, fontsize=10, color=INK)
        ax.tick_params(colors=FAINT, labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)

    pceil = max(p1b + p2b, p1e + p2e, p1i + p2i, 1e-9)
    stacked(axp, {0: (p1b, p2b, "before"), 1: (p1e, p2e, "after")},
            "Momentum  (kg·m/s)", pceil)
    axp.axhline(p1b + p2b, color=FAINT, lw=1.2, ls="--")
    axp.text(0.5, (p1b + p2b) * 1.06, "conserved", ha="center", va="bottom", fontsize=8, color=FAINT)

    kceil = max(k1b + k2b, k1e + k2e, k1i + k2i, 1e-9)
    stacked(axk, {0: (k1b, k2b, "before"), 1: (k1e, k2e, "elastic"), 2: (k1i, k2i, "inelastic")},
            "Kinetic energy  (J)", kceil)
    axk.axhline(k1b + k2b, color=FAINT, lw=1.0, ls=":")
    # shade the energy lost in the inelastic case
    axk.add_patch(plt.Rectangle((2 - 0.31, k1i + k2i), 0.62, (k1b + k2b) - (k1i + k2i),
                                facecolor=FAINT, alpha=0.22, edgecolor="none"))
    axk.annotate("lost", (2, (k1i + k2i + k1b + k2b) / 2), ha="center", va="center",
                 fontsize=8, color=INK, bbox=_bbox())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


def render_trajectory(traj, out_path: Path) -> None:
    """Static poster for the 2D projectile path y vs x (ADR-0015): the parabola (or the numerically-integrated
    drag curve), with launch/apex/range markers. The drag case overlays the drag-free parabola for contrast."""
    base = dict(traj.constants)
    for sl in traj.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    tt = traj.t

    is_orbit = getattr(traj, "frame_mode", "ground") == "orbit"
    fig, ax = plt.subplots(figsize=(6.6, 4.0), facecolor=PAPER)
    ax.set_facecolor(PAPER)

    if traj.frames is not None:
        # numerical (drag) case: plot the representative frame + the drag-free reference overlay
        fr = traj.frames[len(traj.frames) // 2]
        ax.plot(fr.x, fr.y, color=ACCENT, lw=2.4, label=fr.label)
        if traj.reference is not None:
            ax.plot(traj.reference.x, traj.reference.y, color=FAINT, lw=1.6, ls="--", label="no drag")
        ax.legend(frameon=False, fontsize=8.5, loc="upper right")
        xs_all, ys_all = fr.x, fr.y
    else:
        fx = sp.lambdify(tt, traj.x_expr.subs(base), "numpy")
        fy = sp.lambdify(tt, traj.y_expr.subs(base), "numpy")
        ts = np.linspace(0.0, traj.t_flight, 240)
        xs_all = np.broadcast_to(np.asarray(fx(ts), dtype=float), ts.shape)
        ys_all = np.broadcast_to(np.asarray(fy(ts), dtype=float), ts.shape)
        ax.plot(xs_all, ys_all, color=ACCENT, lw=2.4)

    if is_orbit:
        # centred frame: the central body at the origin, equal aspect (a circle reads as a circle), the full
        # path bounding box with symmetric padding — no ground line, no negative-x clip.
        ax.set_aspect("equal", adjustable="box")
        ax.scatter([0.0], [0.0], color=INK, s=60, zorder=5)
        ax.axhline(0, color=GRID, lw=0.8, ls=":")
        ax.axvline(0, color=GRID, lw=0.8, ls=":")
        rx = float(np.max(np.abs(xs_all))) or 1.0
        ry = float(np.max(np.abs(ys_all))) or 1.0
        rad = max(rx, ry) * 1.18
        ax.set_xlim(-rad, rad)
        ax.set_ylim(-rad, rad)
    else:
        ax.axhline(0, color=GRID, lw=1)
        xmax = float(np.max(xs_all)) or 1.0
        ymax = float(np.max(ys_all)) or 1.0
        ax.set_xlim(-0.04 * xmax, xmax * 1.08)
        ax.set_ylim(min(0.0, float(np.min(ys_all))) - 0.06 * ymax, ymax * 1.20)
    ax.set_xlabel(traj.x_label, fontsize=10, color=INK)
    ax.set_ylabel(traj.y_label, fontsize=10, color=INK)
    ax.tick_params(colors=FAINT, labelsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)

    for mk in traj.markers:
        if mk.dot:
            ax.scatter([mk.x], [mk.y], color=ACCENT, zorder=5)
        ax.annotate(mk.label, (mk.x, mk.y), textcoords="offset points", xytext=(mk.dx, mk.dy),
                    ha=mk.ha, va=mk.va, fontsize=8.3, color=INK, bbox=_bbox())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


def render_panels(scn, out_path: Path, t_max: float) -> None:
    """Static poster for an N-panel temporal stack (ADR-0021): each panel's curve vs a shared time axis, with
    the 'rate' panel accented. The general form of the x/v/a stack — the slope of each panel is the panel
    below it (e.g. the current I is the slope of the charge Q)."""
    base = dict(scn.constants)
    for sl in scn.sliders:
        base[sl.sym] = sp.nsimplify(sl.default)
    t = scn.t
    panels = scn.panels
    fns = [sp.lambdify(t, p.expr.subs(base), "numpy") for p in panels]
    ts = np.linspace(0.0, t_max, 240)
    series = [np.broadcast_to(np.asarray(fn(ts), dtype=float), ts.shape) for fn in fns]

    n = len(panels)
    fig, axes = plt.subplots(n, 1, figsize=(6.4, 2.6 * n), sharex=True,
                             gridspec_kw={"hspace": 0.16}, facecolor=PAPER)
    if n == 1:
        axes = [axes]

    for ax, p, arr in zip(axes, panels, series):
        ax.set_facecolor(PAPER)
        ax.set_ylabel(p.label, fontsize=10, color=INK)
        ax.set_xlim(0, t_max)
        lo, hi = float(np.min(arr)), float(np.max(arr))
        lo, hi = min(lo, 0.0), max(hi, 0.0)
        span = (hi - lo) or 1.0
        ax.set_ylim(lo - span * 0.14, hi + span * 0.18)
        ax.tick_params(colors=FAINT, labelsize=8)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GRID)
        ax.axhline(0, color=GRID, lw=1)
        ax.plot(ts, arr, color=(ACCENT if p.accent else INK), lw=2.2)

    axes[-1].set_xlabel("t  (s)", fontsize=10, color=INK)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="svg", bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


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
