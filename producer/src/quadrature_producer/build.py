"""Orchestration: read TOML specs, run the producer, write verified derived JSON.

Two console entry points (pyproject.toml):
  build-problems   problems/**/*.problem.toml -> derived/<topic>/<slug>.solution.json (+ static SVGs)
  build-reference  reference/formulas/*.formula.toml -> derived/reference/{formulas,concept-graph}.json

Dispatches on the spec's `model` field to a model in models/ (constant-accel | shm | linear-drag), which
returns a generic Scenario. The model REFUSES TO EMIT on a failed proof; here we add the dimensional check
and assemble the schema-shaped solution. Schema conformance is then enforced by the Node gates.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

import sympy as sp

from . import BuildError, __version__
from .dims import check_homogeneous, parse_unit
from .emit import (closed_form, closed_form_area, closed_form_collision, closed_form_energy, closed_form_lens,
                   closed_form_of, closed_form_panels, closed_form_params, closed_form_params_area,
                   closed_form_params_collision, closed_form_params_energy, closed_form_params_lens,
                   closed_form_params_panels, closed_form_params_standing, closed_form_params_traj,
                   closed_form_standing, closed_form_traj, sample_area_series, sample_collision_series,
                   sample_energy_series, sample_lens_series, sample_panels_series, sample_series,
                   sample_series_of, sample_standing_series, sample_traj_series)
from .graph import (render_area, render_collision, render_energy, render_lens, render_panels, render_stack,
                    render_standing, render_trajectory)
from .models import MODELS
from .practice import emit_practice
from .reference import build_reference


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)
    path.write_text(text + "\n", encoding="utf-8")


def build_problem(path: Path, root: Path) -> tuple[dict, str]:
    spec = tomllib.loads(path.read_text(encoding="utf-8"))
    ctx = spec.get("id", path.stem)
    model_name = spec.get("model", "constant-accel")
    if model_name not in MODELS:
        raise BuildError(f"{ctx}: unknown model '{model_name}' (have {sorted(MODELS)})")

    scn = MODELS[model_name](spec)  # runs the model's proof; raises on failure

    # dimensional homogeneity (raises on a contradiction) — the units_check
    umap = {s: parse_unit(u, ctx) for s, u in scn.unit_map.items()}
    if scn.x_expr is not None:
        for name, expr in (("x(t)", scn.x_expr), ("v(t)", scn.v_expr), ("a(t)", scn.a_expr)):
            check_homogeneous(expr, umap, f"{ctx}: {name}")
    if scn.panels is not None:
        for p in scn.panels:
            check_homogeneous(p.expr, umap, f"{ctx}: {p.key}(t)")
    if scn.area is not None:
        amap = {s: parse_unit(uu, ctx) for s, uu in scn.area.unit_map.items()}
        check_homogeneous(scn.area.f_expr, amap, f"{ctx}: F(x)")
        check_homogeneous(scn.area.g_expr, amap, f"{ctx}: W(x)")
    if scn.energy is not None:
        emap = {s: parse_unit(uu, ctx) for s, uu in scn.energy.unit_map.items()}
        check_homogeneous(scn.energy.ke_expr, emap, f"{ctx}: KE(u)")
        check_homogeneous(scn.energy.pe_expr, emap, f"{ctx}: PE(u)")
    if scn.collision is not None:
        comap = {s: parse_unit(uu, ctx) for s, uu in scn.collision.unit_map.items()}
        check_homogeneous(scn.collision.v1f_expr, comap, f"{ctx}: v1'")
        check_homogeneous(scn.collision.v2f_expr, comap, f"{ctx}: v2'")
    if scn.standing is not None:
        smap = {s: parse_unit(uu, ctx) for s, uu in scn.standing.unit_map.items()}
        check_homogeneous(scn.standing.y_expr, smap, f"{ctx}: y(x)")
    if scn.lens is not None:
        lmap = {s: parse_unit(uu, ctx) for s, uu in scn.lens.unit_map.items()}
        check_homogeneous(scn.lens.di_expr, lmap, f"{ctx}: di(do)")
        check_homogeneous(scn.lens.hi_expr, lmap, f"{ctx}: hi(do)")
        check_homogeneous(scn.lens.m_expr, lmap, f"{ctx}: m(do)")
    if scn.trajectory is not None and scn.trajectory.x_expr is not None:
        tmap = {s: parse_unit(uu, ctx) for s, uu in scn.trajectory.unit_map.items()}
        check_homogeneous(scn.trajectory.x_expr, tmap, f"{ctx}: x(t)")
        check_homogeneous(scn.trajectory.y_expr, tmap, f"{ctx}: y(t)")

    graphs = []
    for i, gentry in enumerate(spec.get("graphs", [])):
        kind = gentry.get("kind", "stack")
        mode = gentry.get("mode", "static")
        svg_rel = f"assets/graphs/{ctx}-{i}.svg"
        gobj = {
            "kind": kind,
            "mode": mode,
            "window": scn.window_mode,
            "annotate": gentry.get("annotate", []),
            "svg": svg_rel,
        }
        if kind == "area":
            if scn.area is None:
                raise BuildError(f"{ctx}: graph kind 'area' but the model produced no AreaPlot")
            a = scn.area
            render_area(a, root / "derived" / svg_rel)
            gobj["mode"] = "interactive"
            gobj["series"] = sample_area_series(a)
            gobj["closed_form"] = closed_form_area(a)
            gobj["closed_form_params"] = closed_form_params_area(a)
            gobj["params"] = {sl.name: {"min": sl.min, "max": sl.max, "default": sl.default}
                              for sl in a.sliders}
            # the cursor drives the canonical axis variable `u` (see emit._AXIS)
            gobj["cursor"] = {"name": "u", "label": a.u_label, "unit": a.u_unit,
                              "min": a.cursor.min, "max": a.cursor.max, "default": a.cursor.default}
            gobj["u_label"] = a.u_label
            gobj["f_label"] = a.f_label
            gobj["g_label"] = a.g_label
            gobj["u0"] = a.u0
            graphs.append(gobj)
            continue

        if kind == "energy":
            if scn.energy is None:
                raise BuildError(f"{ctx}: graph kind 'energy' but the model produced no EnergyPlot")
            en = scn.energy
            render_energy(en, root / "derived" / svg_rel)
            gobj["mode"] = "interactive"
            gobj["series"] = sample_energy_series(en)
            gobj["closed_form"] = closed_form_energy(en)
            gobj["closed_form_params"] = closed_form_params_energy(en)
            gobj["params"] = {sl.name: {"min": sl.min, "max": sl.max, "default": sl.default}
                              for sl in en.sliders}
            gobj["cursor"] = {"name": "u", "label": en.u_label, "unit": en.u_unit,
                              "min": en.cursor.min, "max": en.cursor.max, "default": en.cursor.default}
            gobj["u_label"] = en.u_label
            gobj["ke_label"] = en.ke_label
            gobj["pe_label"] = en.pe_label
            gobj["total_label"] = en.total_label
            gobj["u0"] = en.u0
            graphs.append(gobj)
            continue

        if kind == "collision":
            if scn.collision is None:
                raise BuildError(f"{ctx}: graph kind 'collision' but the model produced no CollisionPlot")
            col = scn.collision
            render_collision(col, root / "derived" / svg_rel)
            gobj["mode"] = "interactive"
            gobj["series"] = sample_collision_series(col)
            gobj["closed_form"] = closed_form_collision(col)
            gobj["closed_form_params"] = closed_form_params_collision(col)
            gobj["params"] = {sl.name: {"min": sl.min, "max": sl.max, "default": sl.default}
                              for sl in col.sliders}
            gobj["cursor"] = {"name": "u", "label": col.u_label, "unit": col.u_unit,
                              "min": col.cursor.min, "max": col.cursor.max, "default": col.cursor.default}
            gobj["u_label"] = col.u_label
            gobj["consts"] = col.consts_export
            graphs.append(gobj)
            continue

        if kind == "standing":
            if scn.standing is None:
                raise BuildError(f"{ctx}: graph kind 'standing' but the model produced no StandingPlot")
            st = scn.standing
            render_standing(st, root / "derived" / svg_rel)
            gobj["mode"] = "interactive"
            gobj["series"] = sample_standing_series(st)
            gobj["closed_form"] = closed_form_standing(st)
            gobj["closed_form_params"] = closed_form_params_standing(st)
            gobj["params"] = {st.n.name: {"min": 1, "max": st.n_max, "default": st.n_default}}
            gobj["consts"] = {"v": st.speed, "L": st.length, "A": st.amplitude, "n_max": float(st.n_max)}
            gobj["modes"] = st.modes
            gobj["u_label"] = st.u_label
            gobj["y_label"] = st.y_label
            gobj["u0"] = 0.0
            graphs.append(gobj)
            continue

        if kind == "lens":
            if scn.lens is None:
                raise BuildError(f"{ctx}: graph kind 'lens' but the model produced no LensPlot")
            lp = scn.lens
            render_lens(lp, root / "derived" / svg_rel)
            gobj["mode"] = "interactive"
            gobj["series"] = sample_lens_series(lp)
            gobj["closed_form"] = closed_form_lens(lp)
            gobj["closed_form_params"] = closed_form_params_lens(lp)
            gobj["params"] = {sl.name: {"min": sl.min, "max": sl.max, "default": sl.default}
                              for sl in lp.sliders}
            gobj["cursor"] = {"name": "u", "label": lp.u_label, "unit": lp.u_unit,
                              "min": lp.cursor.min, "max": lp.cursor.max, "default": lp.cursor.default}
            gobj["u_label"] = lp.u_label
            gobj["consts"] = lp.consts_export
            gobj["u0"] = lp.cursor.min
            graphs.append(gobj)
            continue

        if kind == "trajectory":
            if scn.trajectory is None:
                raise BuildError(f"{ctx}: graph kind 'trajectory' but the model produced no TrajectoryPlot")
            tr = scn.trajectory
            render_trajectory(tr, root / "derived" / svg_rel)
            gobj["x_label"] = tr.x_label
            gobj["y_label"] = tr.y_label
            gobj["g"] = float(scn.constants_export.get("g", -10))
            gobj["frame"] = tr.frame_mode
            if tr.mu is not None:
                gobj["mu"] = float(tr.mu)
            if tr.view_half is not None:
                gobj["view_half"] = float(tr.view_half)
            if tr.frames is not None:
                gobj["mode"] = "sampled"
                gobj["sweep"] = tr.sweep
                gobj["frames"] = [
                    {"value": fr.value, "label": fr.label,
                     "series": {"t": fr.t, "x": fr.x, "y": fr.y, "t_max": round(fr.t[-1], 9)}}
                    for fr in tr.frames
                ]
                if tr.reference is not None:
                    gobj["reference"] = {"t": tr.reference.t, "x": tr.reference.x,
                                         "y": tr.reference.y, "t_max": round(tr.reference.t[-1], 9)}
            else:
                gobj["mode"] = "interactive"
                gobj["series"] = sample_traj_series(tr)
                gobj["closed_form"] = closed_form_traj(tr)
                gobj["closed_form_params"] = closed_form_params_traj(tr)
                gobj["params"] = {sl.name: {"min": sl.min, "max": sl.max, "default": sl.default}
                                  for sl in tr.sliders}
            graphs.append(gobj)
            continue

        if scn.panels is not None:
            render_panels(scn, root / "derived" / svg_rel, scn.t_window)
            gobj["mode"] = "interactive"
            gobj["panels"] = [{"key": p.key, "label": p.label, "unit": p.unit, "accent": p.accent}
                              for p in scn.panels]
            gobj["series"] = sample_panels_series(scn, scn.t_window)
            gobj["closed_form"] = closed_form_panels(scn)
            gobj["closed_form_params"] = closed_form_params_panels(scn)
            gobj["params"] = {sl.name: {"min": sl.min, "max": sl.max, "default": sl.default}
                              for sl in scn.sliders}
            graphs.append(gobj)
            continue

        render_stack(scn, root / "derived" / svg_rel, scn.t_window)
        if mode == "sampled":
            if not scn.sampled:
                raise BuildError(f"{ctx}: graph mode 'sampled' but the model produced no frames")
            gobj["sweep"] = scn.sampled["sweep"]
            gobj["frames"] = [
                {
                    "value": fr.value,
                    "label": fr.label,
                    "closed_form": closed_form_of(fr.x_expr, fr.v_expr, fr.a_expr),
                    "closed_form_params": ["t"],
                    "series": sample_series_of(fr.x_expr, fr.v_expr, fr.a_expr, scn.t, scn.t_window),
                }
                for fr in scn.sampled["frames"]
            ]
        else:
            gobj["series"] = sample_series(scn, scn.t_window)
            gobj["closed_form"] = closed_form(scn)
            gobj["closed_form_params"] = closed_form_params(scn)
            if mode == "interactive":
                gobj["params"] = {
                    sl.name: {"min": sl.min, "max": sl.max, "default": sl.default} for sl in scn.sliders
                }
        graphs.append(gobj)

    solution = {
        "id": spec["id"],
        "title": spec["title"],
        "topic": spec["topic"],
        "slug": spec["slug"],
        "scenario": spec["scenario"],
        "regime": scn.regime,
        "constants": scn.constants_export,
        "initial_conditions": scn.initial_conditions,
        "assumptions": spec.get("assumptions", []),
        "algebra": scn.algebra,
        "calculus": scn.calculus,
        "proof": scn.proof,
        "units_check": {"checked_by": "sympy", "holds": True},
        "graphs": graphs,
        "misconception": spec.get("misconception"),
        "formulas_used": spec.get("formulas_used", []),
        "provenance": {
            "producer": "quadrature_producer",
            "version": __version__,
            "sympy": sp.__version__,
            "author": spec.get("author", "Quadrature"),
            "created": spec.get("created", ""),
        },
    }
    if scn.sign_analysis is not None:
        solution["sign_analysis"] = scn.sign_analysis
    if spec.get("practice"):
        solution["practice"] = emit_practice(scn, spec, ctx)

    out_rel = f"{spec['topic']}/{spec['slug']}.solution.json"
    return solution, out_rel


def build_problems_main(argv: list[str] | None = None) -> int:
    root = Path.cwd()
    problems = sorted((root / "problems").glob("**/*.problem.toml"))
    if not problems:
        print("no *.problem.toml found under problems/", file=sys.stderr)
        return 1
    for path in problems:
        try:
            solution, out_rel = build_problem(path, root)
        except BuildError as e:
            print(f"BUILD FAILED — {e}", file=sys.stderr)
            return 1
        _write_json(root / "derived" / out_rel, solution)
        print(f"  built {path.relative_to(root).as_posix()} -> derived/{out_rel}")
    return 0


def build_reference_main(argv: list[str] | None = None) -> int:
    root = Path.cwd()
    specs_paths = sorted((root / "reference" / "formulas").glob("*.formula.toml"))
    if not specs_paths:
        print("no *.formula.toml found under reference/formulas/", file=sys.stderr)
        return 1
    specs = []
    for p in specs_paths:
        spec = tomllib.loads(p.read_text(encoding="utf-8"))
        spec.setdefault("id", p.stem.replace(".formula", ""))
        specs.append(spec)
    try:
        formulas_obj, graph_obj = build_reference(specs)
    except BuildError as e:
        print(f"BUILD FAILED — {e}", file=sys.stderr)
        return 1
    _write_json(root / "derived" / "reference" / "formulas.json", formulas_obj)
    _write_json(root / "derived" / "reference" / "concept-graph.json", graph_obj)
    print(f"  built {len(formulas_obj['formulas'])} formula(s) -> derived/reference/formulas.json")
    print(f"  built {len(graph_obj['nodes'])} node(s), {len(graph_obj['edges'])} edge(s) "
          f"-> derived/reference/concept-graph.json")
    return 0
