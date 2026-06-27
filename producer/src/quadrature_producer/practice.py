"""Verified practice questions (ADR-0022) — the "solve it three ways" content type.

Each lesson may carry `[[practice]]` blocks in its spec. The producer turns each into a schema-shaped practice
question: a multiple-choice "just get the answer" (whose distractors are *machine-derived from named
misconceptions*), plus — when requested — the lesson's own algebra and calculus step-throughs reused verbatim.

The honesty model is the same as the rest of the course: the correct answer is the lesson's already-verified
result (or a SymPy expression evaluated at the scenario defaults), and **every distractor is proven finite and
proven distinct from the correct answer** at build time. A distractor that collides with the truth is a build
break — exactly like a failed parity check. The frontend reveals; it never computes.
"""

from __future__ import annotations

import math

import sympy as sp

from . import BuildError
from .util import display as _display


def _eval_number(expr_str: str, table: dict, subs: dict, ctx: str) -> float:
    """Sympify `expr_str` over the scenario symbol table, substitute the default values, and demand a finite
    real number — fail loud otherwise (unresolved symbol, division by zero, non-finite)."""
    try:
        expr = sp.sympify(expr_str, locals=table)
    except (sp.SympifyError, SyntaxError, TypeError) as e:
        raise BuildError(f"{ctx}: cannot parse '{expr_str}': {e}") from e
    val_expr = expr.subs(subs)
    leftover = val_expr.free_symbols
    if leftover:
        raise BuildError(f"{ctx}: '{expr_str}' leaves unresolved symbol(s) {sorted(map(str, leftover))} "
                         f"(the scenario exports {sorted(str(s) for s in subs)})")
    num = sp.N(val_expr, 15)
    if not num.is_number or num.has(sp.zoo, sp.oo, sp.nan) or not math.isfinite(float(num)):
        raise BuildError(f"{ctx}: '{expr_str}' did not evaluate to a finite number (got {num})")
    return float(num)


def emit_practice(scn, spec: dict, ctx: str) -> list[dict]:
    questions = spec.get("practice", [])
    if not questions:
        return []
    result_map = scn.algebra.get("result", {})
    # the scenario quantities a transform may reference: the exported constants plus the initial conditions
    # (e.g. x0, v0 for kinematics), with constants winning any name clash.
    quantities = {**(scn.initial_conditions or {}), **(scn.constants_export or {})}
    base_table = {name: sp.Symbol(name) for name in quantities}
    base_subs = {sp.Symbol(name): sp.nsimplify(val, rational=True) for name, val in quantities.items()}

    out: list[dict] = []
    seen: set[str] = set()
    for q in questions:
        qid = q.get("id")
        if not qid:
            raise BuildError(f"{ctx}: a practice question is missing 'id'")
        if qid in seen:
            raise BuildError(f"{ctx}: duplicate practice id '{qid}'")
        seen.add(qid)
        for field in ("asks", "prompt", "answer"):
            if field not in q:
                raise BuildError(f"{ctx}: practice '{qid}' is missing '{field}'")
        qctx = f"{ctx}: practice '{qid}'"

        # --- resolve the correct answer (a verified result key, or a SymPy expression) ---
        answer_spec = str(q["answer"])
        if answer_spec.startswith("result:"):
            key = answer_spec[len("result:"):]
            if key not in result_map:
                raise BuildError(f"{qctx}: answer 'result:{key}' — no such algebra result "
                                 f"(have {sorted(result_map)})")
            r = result_map[key]
            ans_val = float(r["value"])
            ans = {"value": round(ans_val, 6), "display": r["display"], "unit": r["unit"]}
            if r.get("symbolic_latex"):
                ans["symbolic_latex"] = r["symbolic_latex"]
        else:
            unit = q.get("unit")
            if not unit:
                raise BuildError(f"{qctx}: a formula/literal answer needs an explicit 'unit'")
            ans_val = _eval_number(answer_spec, base_table, base_subs, f"{qctx} answer")
            ans = {"value": round(ans_val, 6), "display": _display(ans_val), "unit": unit}
            if q.get("answer_latex"):
                ans["symbolic_latex"] = q["answer_latex"]

        # --- distractors: each a named misconception, evaluated and proven distinct from the answer ---
        table = {**base_table, "answer": sp.Symbol("answer")}
        subs = {**base_subs, sp.Symbol("answer"): sp.nsimplify(ans_val, rational=True)}
        choices = [{"value": ans["value"], "display": ans["display"], "correct": True}]
        for d in q.get("distractor", []):
            for field in ("method", "transform", "misconception"):
                if field not in d:
                    raise BuildError(f"{qctx}: a distractor is missing '{field}'")
            dctx = f"{qctx} distractor '{d['method']}'"
            dval = _eval_number(str(d["transform"]), table, subs, dctx)
            if abs(dval - ans_val) <= 1e-9 * max(1.0, abs(ans_val)):
                raise BuildError(f"{dctx}: distractor value {dval} collides with the correct answer "
                                 f"{ans_val} — a distractor must be a *wrong* answer")
            choices.append({"value": round(dval, 6), "display": _display(dval), "correct": False,
                            "method": d["method"], "misconception": d["misconception"]})
        if len(choices) < 2:
            raise BuildError(f"{qctx}: needs at least one distractor (a multiple-choice needs ≥2 options)")

        pq = {"id": qid, "asks": q["asks"], "prompt": q["prompt"], "answer": ans, "choices": choices}
        include = q.get("include", [])
        if "algebra" in include:
            pq["algebra_steps"] = scn.algebra["steps"]
        if "calculus" in include:
            pq["calculus_steps"] = scn.calculus["steps"]
        out.append(pq)
    return out
