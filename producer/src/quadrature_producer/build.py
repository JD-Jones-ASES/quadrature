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
from .emit import closed_form, closed_form_params, sample_series
from .graph import render_stack
from .models import MODELS
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
    for name, expr in (("x(t)", scn.x_expr), ("v(t)", scn.v_expr), ("a(t)", scn.a_expr)):
        check_homogeneous(expr, umap, f"{ctx}: {name}")

    graphs = []
    for i, gentry in enumerate(spec.get("graphs", [])):
        mode = gentry.get("mode", "static")
        svg_rel = f"assets/graphs/{ctx}-{i}.svg"
        render_stack(scn, root / "derived" / svg_rel, scn.t_window)
        gobj = {
            "kind": gentry.get("kind", "stack"),
            "mode": mode,
            "window": scn.window_mode,
            "annotate": gentry.get("annotate", []),
            "svg": svg_rel,
            "series": sample_series(scn, scn.t_window),
            "closed_form": closed_form(scn),
            "closed_form_params": closed_form_params(scn),
        }
        if mode in ("interactive", "sampled"):
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
