"""Orchestration: read TOML specs, run the producer, write verified derived JSON.

Two console entry points (pyproject.toml):
  build-problems   problems/**/*.problem.toml -> derived/<topic>/<slug>.solution.json (+ static SVGs)
  build-reference  reference/formulas/*.formula.toml -> derived/reference/{formulas,concept-graph}.json

The producer REFUSES TO EMIT on a failed equivalence proof or unit check (the local
"verification breaks the build"). Schema conformance is then enforced by the Node gates.
"""

from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

import sympy as sp

from . import BuildError, __version__
from .derive import calculus_register
from .dims import check_homogeneous, parse_unit
from .emit import closed_form, closed_form_params, sample_series
from .graph import render_stack
from .kinematics import a, build_model, prove_equivalence, t, v0, x0
from .reference import build_reference
from .solve import algebra_register


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False)
    path.write_text(text + "\n", encoding="utf-8")


def _sign(value: float) -> str:
    return "+" if value > 1e-12 else ("-" if value < -1e-12 else "0")


def _sign_analysis(model, apex_time: float, flight_time: float) -> dict:
    """Sign-rigor: speeding up ⟺ v and a share a sign. Signs are evaluated from the model."""
    subs = model.subs
    a_sign = _sign(float(model.subs[a]))

    def v_at(tt: float) -> float:
        return float(sp.N(model.v_expr.subs({**subs, t: sp.nsimplify(tt)})))

    rising_mid = apex_time / 2
    falling_mid = (apex_time + flight_time) / 2
    segs = [
        {"phase": "rising", "t_range": [0.0, round(apex_time, 6)],
         "v_sign": _sign(v_at(rising_mid)), "a_sign": a_sign, "state": "slowing down"},
        {"phase": "apex", "t": round(apex_time, 6),
         "v_sign": "0", "a_sign": a_sign, "state": "v = 0, but a ≠ 0"},
        {"phase": "falling", "t_range": [round(apex_time, 6), round(flight_time, 6)],
         "v_sign": _sign(v_at(falling_mid)), "a_sign": a_sign, "state": "speeding up"},
    ]
    return {"rule": "speeding up ⟺ sign(v·a) > 0; slowing down ⟺ sign(v·a) < 0", "segments": segs}


def build_problem(path: Path, root: Path) -> tuple[dict, str]:
    spec = tomllib.loads(path.read_text(encoding="utf-8"))
    ctx = spec.get("id", path.stem)
    consts = spec.get("constants", {})
    ics = spec.get("initial_conditions", {})
    if "g" not in consts:
        raise BuildError(f"{ctx}: constants.g is required (house convention g = -10)")
    a_value = consts["g"]
    x0_value = ics.get("x0", 0.0)
    v0_value = ics.get("v0", 0.0)

    model = build_model(a_value, x0_value, v0_value, ground=0.0)

    # unit check (raises on a dimensional contradiction)
    unit_map = {x0: parse_unit("m", ctx), v0: parse_unit("m/s", ctx),
                a: parse_unit("m/s**2", ctx), t: parse_unit("s", ctx)}
    for name, expr in (("v(t)", model.v_expr), ("x(t)", model.x_expr)):
        check_homogeneous(expr, unit_map, f"{ctx}: {name}")

    # the equivalence proof (raises on failure — refuses to emit)
    proof = prove_equivalence(model, ctx)

    algebra = algebra_register(model, spec.get("unknowns", list(model.unknowns)))
    calculus = calculus_register(model)

    flight_time = algebra["result"]["flight_time"]["value"] if "flight_time" in algebra["result"] \
        else float(sp.N(model.unknowns["flight_time"].subs(model.subs)))
    apex_time = float(sp.N(model.unknowns["apex_time"].subs(model.subs)))

    # graphs
    graphs = []
    for i, g in enumerate(spec.get("graphs", [])):
        mode = g.get("mode", "static")
        svg_rel = f"assets/graphs/{ctx}-{i}.svg"
        render_stack(model, root / "derived" / svg_rel, t_max=flight_time)
        gobj = {
            "kind": g.get("kind", "stack"),
            "mode": mode,
            "annotate": g.get("annotate", []),
            "svg": svg_rel,
            "series": sample_series(model, flight_time),
            "closed_form": closed_form(model),
            "closed_form_params": closed_form_params(model),
        }
        if mode == "interactive":
            if "params" not in g:
                raise BuildError(f"{ctx}: interactive graph needs [graphs.params.*] ranges")
            gobj["params"] = g["params"]
        graphs.append(gobj)

    solution = {
        "id": spec["id"],
        "title": spec["title"],
        "topic": spec["topic"],
        "slug": spec["slug"],
        "scenario": spec["scenario"],
        "regime": spec["regime"],
        "constants": consts,
        "initial_conditions": ics,
        "assumptions": spec.get("assumptions", []),
        "algebra": algebra,
        "calculus": calculus,
        "equivalence_proof": proof,
        "units_check": {"checked_by": "sympy", "holds": True},
        "sign_analysis": _sign_analysis(model, apex_time, flight_time),
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
        out = root / "derived" / out_rel
        _write_json(out, solution)
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
