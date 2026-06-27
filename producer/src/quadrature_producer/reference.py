"""The formula reference + concept graph producer.

Each formula's LaTeX is generated from its SymPy expression (no transcription typos), its
units are checked, and its declared derivation relationship is PROVEN (e.g. diff(x,t)==v).
The concept graph's typed edges get a deterministic, frozen force layout (ADR-0008), so the
Svelte island renders static SVG with no client-side layout.
"""

from __future__ import annotations

import random
import re

import sympy as sp

from . import BuildError
from .dims import check_homogeneous, parse_unit
from .prove import SampleDomain, tiered_zero

EDGE_TYPES = {"derived-from", "integral-of", "derivative-of", "special-case-of", "assumes", "related-to"}
DOMAINS = {"mechanics", "em", "thermo", "waves-optics", "modern"}
_RECIPROCAL = {"integral-of": "derivative-of", "derivative-of": "integral-of"}

# --- concept-graph node labels: turn a LaTeX `lhs` into a short clean glyph (no raw backslashes/braces) ---
# Curated map covers every LaTeX-bearing lhs currently in the reference; the generic fallback in
# _clean_label() keeps future formulas clean too.
_LABEL_MAP = {
    r"\tau": "τ", r"\eta": "η", r"\Phi": "Φ", r"\zeta": "ζ", r"\omega": "ω", r"\omega_d": "ω_d",
    r"\lambda": "λ", r"\theta_2": "θ₂", r"\mathcal{E}": "ℰ",
    r"F_{\text{net}}": "F_net", r"K_{\text{rot}}": "K_rot", r"v_{\text{term}}": "v_term", r"K_{\max}": "K_max",
    r"\frac{1}{f}": "1/f", r"\Delta U": "ΔU", r"P_2": "P₂", r"P_0": "P₀",
}
_GREEK = {
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ", r"\Delta": "Δ", r"\epsilon": "ε",
    r"\zeta": "ζ", r"\eta": "η", r"\theta": "θ", r"\lambda": "λ", r"\mu": "μ", r"\pi": "π", r"\rho": "ρ",
    r"\sigma": "σ", r"\tau": "τ", r"\phi": "φ", r"\Phi": "Φ", r"\omega": "ω", r"\Omega": "Ω",
}
_SUBSCRIPT_DIGITS = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def _clean_label(lhs: str) -> str:
    """A short, brace-free, backslash-free node label from a LaTeX lhs (e.g. '\\frac{1}{f}' -> '1/f')."""
    if not lhs:
        return ""
    if lhs in _LABEL_MAP:
        return _LABEL_MAP[lhs]
    s = lhs
    s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"\1/\2", s)        # \frac{a}{b} -> a/b
    s = re.sub(r"\\(?:text|mathrm|mathcal|mathbf)\{([^{}]*)\}", r"\1", s)  # \text{x} -> x
    s = s.replace(r"\max", "max").replace(r"\min", "min")
    for k, v in _GREEK.items():
        s = s.replace(k, v)
    s = re.sub(r"_\{([^{}]*)\}", r"_\1", s)                          # x_{ab} -> x_ab
    s = re.sub(r"_([0-9])", lambda m: m.group(1).translate(_SUBSCRIPT_DIGITS), s)  # P_2 -> P₂
    return s.replace("{", "").replace("}", "").replace("\\", "").strip()


# --- frozen force-layout geometry (ADR-0008, ADR-0020): a larger canvas, domain-clustered ---
LAYOUT_W, LAYOUT_H = 900, 640
# Each domain is seeded into its own region (fractions of W×H) and weakly pulled back toward it, so the five
# domains occupy distinct areas instead of intermixing. Mechanics dominates (most nodes) → central + largest.
DOMAIN_ANCHOR = {
    "mechanics":    (0.36, 0.52),
    "em":           (0.80, 0.38),
    "thermo":       (0.52, 0.86),
    "waves-optics": (0.84, 0.74),
    "modern":       (0.56, 0.13),
}


def _symbol_table(specs: list[dict]) -> dict[str, sp.Symbol]:
    syms: dict[str, sp.Symbol] = {}
    for spec in specs:
        for name in spec.get("variables", {}):
            syms.setdefault(name, sp.Symbol(name, real=True))
    return syms


def _parse(spec: dict, table: dict[str, sp.Symbol]) -> sp.Expr:
    try:
        return sp.sympify(spec["expr"], locals=table)
    except (sp.SympifyError, SyntaxError) as e:
        raise BuildError(f"formula '{spec['id']}': cannot parse expr '{spec['expr']}': {e}") from e


def build_reference(specs: list[dict]) -> tuple[dict, dict]:
    if not specs:
        raise BuildError("reference: no formula specs found")
    table = _symbol_table(specs)
    by_id = {s["id"]: s for s in specs}
    exprs = {s["id"]: _parse(s, table) for s in specs}

    nodes = []
    formula_records = []
    edges: list[dict] = []

    for spec in specs:
        fid = spec["id"]
        if spec["domain"] not in DOMAINS:
            raise BuildError(f"formula '{fid}': unknown domain '{spec['domain']}'")
        expr = exprs[fid]
        variables = spec.get("variables", {})

        # unit map for this formula's symbols
        unit_map = {table[n]: parse_unit(v["unit"], f"{fid}.{n}") for n, v in variables.items()}
        missing = [str(s) for s in expr.free_symbols if s not in unit_map]
        if missing:
            raise BuildError(f"formula '{fid}': expr uses undeclared variables {sorted(missing)}")

        # dimensional check: the RHS must carry result_unit
        result_unit = parse_unit(spec["result_unit"], f"{fid}.result_unit")
        lhs_sym = sp.Symbol(f"__lhs_{fid}", real=True)
        check_homogeneous(lhs_sym - expr, {**unit_map, lhs_sym: result_unit}, f"{fid}: result_unit vs expr")

        # derivation: PROVE the declared relationship
        derivation = spec.get("derivation")
        if derivation:
            rel = derivation["relationship"]
            target = derivation["target"]
            var = table[derivation["variable"]]
            if target not in exprs:
                raise BuildError(f"formula '{fid}': derivation target '{target}' is unknown")
            t_expr = exprs[target]
            dom = SampleDomain(bounds={s: (1.0, 10.0) for s in table.values()}, positive=set())
            if rel == "integral-of":
                tiered_zero(sp.diff(expr, var) - t_expr, dom, f"{fid}: d/d{var}({fid}) == {target}",
                            seed=f"{fid}/integral-of")
            elif rel == "derivative-of":
                tiered_zero(expr - sp.diff(t_expr, var), dom, f"{fid}: {fid} == d/d{var}({target})",
                            seed=f"{fid}/derivative-of")
            else:
                raise BuildError(f"formula '{fid}': derivation relationship '{rel}' not provable here")

        latex = f"{spec.get('lhs', '')} = {sp.latex(expr)}".strip(" =") if not spec.get("lhs") \
            else f"{spec['lhs']} = {sp.latex(expr)}"

        formula_records.append({
            "id": fid,
            "name": spec["name"],
            "domain": spec["domain"],
            "regime": spec["regime"],
            "lhs": spec.get("lhs", ""),
            "expr": spec["expr"],
            "expr_srepr": sp.srepr(expr),
            "latex": latex,
            "result_unit": spec["result_unit"],
            "variables": {n: {"unit": v["unit"], "desc": v.get("desc", "")} for n, v in variables.items()},
            "assumptions": spec.get("assumptions", []),
            "derivation": derivation,
            "lessons": spec.get("lessons", []),
            "citations": spec.get("citations", []),
            "verified": {"units": True, "derivation": bool(derivation)},
        })

        for e in spec.get("edges", []):
            if e["type"] not in EDGE_TYPES:
                raise BuildError(f"formula '{fid}': unknown edge type '{e['type']}'")
            if e["target"] not in by_id:
                raise BuildError(f"formula '{fid}': edge target '{e['target']}' is unknown")
            edges.append({"source": fid, "target": e["target"], "type": e["type"],
                          "gloss": e.get("gloss", "")})
            recip = _RECIPROCAL.get(e["type"])
            if recip:
                edges.append({"source": e["target"], "target": fid, "type": recip,
                              "gloss": e.get("gloss", "")})

    # dedupe edges (source,target,type)
    seen = set()
    uniq_edges = []
    for e in edges:
        k = (e["source"], e["target"], e["type"])
        if k not in seen:
            seen.add(k)
            uniq_edges.append(e)

    nodes = _layout(formula_records, uniq_edges)
    formulas_obj = {"schema_version": 1, "formulas": formula_records}
    graph_obj = {"schema_version": 1, "layout": {"w": LAYOUT_W, "h": LAYOUT_H}, "nodes": nodes, "edges": uniq_edges}
    return formulas_obj, graph_obj


def _layout(records: list[dict], edges: list[dict]) -> list[dict]:
    """Deterministic, domain-clustered force layout, frozen into node coordinates (ADR-0008, ADR-0020).

    Each node is seeded near its domain's anchor region and weakly pulled back toward it each step, so the five
    domains settle into distinct areas instead of intermixing. Larger canvas + stronger repulsion than the
    original 640×480 single-blob layout, so 71 nodes have room to breathe. Seeded RNG → reproducible."""
    W, H = LAYOUT_W, LAYOUT_H
    ids = [r["id"] for r in records]
    anchor = {r["id"]: (DOMAIN_ANCHOR.get(r["domain"], (0.5, 0.5))[0] * W,
                        DOMAIN_ANCHOR.get(r["domain"], (0.5, 0.5))[1] * H) for r in records}
    degree = {i: 0 for i in ids}
    for e in edges:
        degree[e["source"]] = degree.get(e["source"], 0) + 1
        degree[e["target"]] = degree.get(e["target"], 0) + 1
    rng = random.Random("quadrature-concept-graph-v1")
    pos = {i: [anchor[i][0] + rng.uniform(-65, 65), anchor[i][1] + rng.uniform(-65, 65)] for i in ids}
    links = [(e["source"], e["target"]) for e in edges]
    for it in range(500):
        cool = max(0.08, 1 - it / 580)
        # repulsion (all pairs) — strong enough to keep ~52px-diameter nodes from overlapping
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a_, b_ = ids[i], ids[j]
                dx = pos[a_][0] - pos[b_][0]
                dy = pos[a_][1] - pos[b_][1]
                d2 = dx * dx + dy * dy + 0.01
                rep = 19000 / d2
                d = d2**0.5
                ux, uy = dx / d, dy / d
                pos[a_][0] += ux * rep * cool
                pos[a_][1] += uy * rep * cool
                pos[b_][0] -= ux * rep * cool
                pos[b_][1] -= uy * rep * cool
        # springs (longer rest length for the larger canvas)
        for s, tg in links:
            dx = pos[tg][0] - pos[s][0]
            dy = pos[tg][1] - pos[s][1]
            d = (dx * dx + dy * dy) ** 0.5 + 0.01
            k = (d - 160) * 0.02 * cool
            ux, uy = dx / d, dy / d
            pos[s][0] += ux * k
            pos[s][1] += uy * k
            pos[tg][0] -= ux * k
            pos[tg][1] -= uy * k
        # per-domain centering: a gentle bias toward the domain anchor (clusters the domains without
        # collapsing them — kept weak so repulsion still spaces nodes inside a cluster)
        for i in ids:
            ax, ay = anchor[i]
            pos[i][0] += (ax - pos[i][0]) * 0.016 * cool
            pos[i][1] += (ay - pos[i][1]) * 0.016 * cool
    nodes = []
    for r in records:
        i = r["id"]
        px = min(W - 40, max(40, pos[i][0]))
        py = min(H - 40, max(40, pos[i][1]))
        nodes.append({
            "id": i, "label": _clean_label(r["lhs"]) or r["name"], "name": r["name"],
            "domain": r["domain"], "degree": degree[i],
            "x": round(px, 2), "y": round(py, 2),
        })
    return nodes
