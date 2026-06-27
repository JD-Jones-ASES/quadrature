"""Regime-3 model: image formation by a thin converging lens — the ray-diagram instrument (ADR-0024, the 7th
graph instrument). Deepens Waves & optics.

The algebra-based course hands you two rules: the **thin-lens equation** $1/d_o + 1/d_i = 1/f$ and the
**magnification** $m = -d_i/d_o$. Plug in the object distance $d_o$ and focal length $f$, solve for the image
distance $d_i$, and read off whether the image is real or virtual, upright or inverted, enlarged or reduced.
You memorize the equation; you are not shown *why* it is true.

The honest second register here is not calculus — optics at this level is a *geometric* science — it is the
**ray diagram**. Three special rays leave the tip of the object, and you can draw each with a ruler and no
equation at all:
1. the ray *parallel* to the axis refracts through the far focal point $F'$;
2. the ray through the lens *center* passes straight through, undeviated;
3. the ray through the near focal point $F$ refracts *parallel* to the axis.

Wherever those rays cross is the image. And the thin-lens equation is nothing more than the statement that they
*do* all cross at one point: the chief ray (through the center) gives, by similar triangles, $m = -d_i/d_o$;
the parallel ray gives $m = -(d_i - f)/f$; setting the two equal and clearing fractions yields
$1/f = 1/d_o + 1/d_i$. The equation you memorized is the algebra of "the three rays meet."

Proof kind `governing`: the closed form $d_i = d_o f/(d_o-f)$ satisfies the thin-lens equation; the chief ray's
similar triangles give $m=-d_i/d_o$; the parallel and focal rays give the *same* magnification (the constructions
agree — which IS the lens equation); and $m = -d_i/d_o = f/(f-d_o)$. (Deeper still — and genuinely calculus —
Fermat's principle: every ray from object to image has a *stationary* optical path length, $dL=0$. A lens is a
piece of glass shaped so that the bent paths all take equal time. That is left as a remark, not derived.)
"""

from __future__ import annotations

import sympy as sp

from .. import BuildError
from ..prove import SampleDomain, tiered_zero
from .base import LensPlot, Scenario, Slider, make_result

do = sp.Symbol("do", positive=True)   # object distance (the cursor; the canonical `u` axis)
f = sp.Symbol("f", positive=True)     # focal length (a FIXED constant — the singularity at do=f never moves)
ho = sp.Symbol("ho", positive=True)   # object height (a slider; scales the image, not the magnification)

PROOF_DOMAIN = SampleDomain(
    bounds={do: (1.5, 4.0), f: (0.7, 1.0), ho: (0.3, 0.6)},   # do kept clear of f so do-f is bounded away from 0
    positive={do, f, ho},
)


def build(spec: dict) -> Scenario:
    p = spec.get("parameters", {})
    for key in ("f", "ho", "do_default", "do_min", "do_max", "ho_min", "ho_max"):
        if key not in p:
            raise BuildError(f"{spec.get('id')}: thin-lens requires parameters.{key}")
    f_val, ho_val = sp.nsimplify(p["f"]), sp.nsimplify(p["ho"])
    do_def, do_lo, do_hi = float(p["do_default"]), float(p["do_min"]), float(p["do_max"])
    ho_lo, ho_hi = float(p["ho_min"]), float(p["ho_max"])
    fnum = float(f_val)
    converging = fnum > 0   # f > 0 converging lens; f < 0 diverging lens (always a virtual, reduced image)
    if fnum == 0:
        raise BuildError(f"{spec.get('id')}: focal length cannot be zero")
    if do_lo <= 0:
        raise BuildError(f"{spec.get('id')}: object distance must be positive (object in front of the lens)")
    if converging and not (do_lo < fnum < do_hi):
        raise BuildError(f"{spec.get('id')}: a converging lens (f>0) needs the object-distance range to "
                         f"straddle f, to show the real↔virtual flip as the object crosses the focal point")
    if not (do_lo <= do_def <= do_hi):
        raise BuildError(f"{spec.get('id')}: do_default must lie in [do_min, do_max]")

    # closed forms — the image distance, height, and magnification as functions of the object distance
    di = do * f / (do - f)                 # thin-lens equation solved for di
    hi = -ho * f / (do - f)                # image height = m·ho
    m = -f / (do - f)                      # magnification = -di/do

    # --- proof (governing): the closed form satisfies the lens equation, and the three principal-ray
    #     similar-triangle constructions all agree (which IS the thin-lens equation) ---
    checks_spec = [
        ("lens_equation",
         r"The closed form $d_i = \dfrac{d_o f}{d_o - f}$ satisfies the thin-lens equation "
         r"$\dfrac{1}{d_o} + \dfrac{1}{d_i} = \dfrac{1}{f}$ — back-substituting leaves zero.",
         1 / do + 1 / di - 1 / f),
        ("chief_ray",
         r"The ray through the lens *center* is undeviated, so the object and image triangles about the center "
         r"are similar: $m = h_i/h_o = -d_i/d_o$.",
         m - (-di / do)),
        ("parallel_ray_agrees",
         r"The *parallel* ray refracts toward (or away from) the focus, giving $m = -(d_i - f)/f$ by similar "
         r"triangles. It equals the chief-ray value $-d_i/d_o$ — the two independent constructions locate the "
         r"*same* image point, and that agreement is exactly the thin-lens equation.",
         (-(di - f) / f) - (-di / do)),
        ("focal_ray_agrees",
         r"The *focal* ray (through a focus, emerging parallel) gives $m = -f/(d_o - f)$ — the same "
         r"magnification again. All three principal-ray constructions locate one image point.",
         (-f / (do - f)) - (-di / do)),
        ("magnification_form",
         r"The magnification in terms of $d_o, f$ alone: $m = -\dfrac{d_i}{d_o} = \dfrac{f}{f - d_o}$ — its sign "
         r"sets the orientation (upright when $m>0$, inverted when $m<0$), its size the scale.",
         m - f / (f - do)),
    ]
    checks = []
    for key, claim, expr in checks_spec:
        tier = tiered_zero(expr, PROOF_DOMAIN, f"{spec.get('id')}: {key}", seed=f"thin-lens/{key}")
        checks.append({"key": key, "claim": claim, "holds": True, "tier": tier})
    proof = {
        "kind": "governing",
        "heading": "The thin-lens equation is the algebra of “the three principal-ray constructions locate one "
                   "image” — SymPy proves the chief, parallel, and focal rays all agree.",
        "checked_by": "sympy",
        "holds": True,
        "detail": r"check $d_i = d_o f/(d_o-f)$ solves $1/d_o+1/d_i=1/f$; chief ray $m=-d_i/d_o$; parallel & "
                  r"focal rays give the same $m$; $m = f/(f-d_o)$",
        "checks": checks,
    }

    rsubs = {do: sp.Rational(str(do_def)), f: f_val, ho: ho_val}
    di_r = make_result(di, rsubs, "m", rf"Image distance $d_i = d_o f/(d_o-f)$ at $d_o = {do_def:g}$ m")
    di_r["symbolic_latex"] = r"\dfrac{d_o\,f}{d_o - f}"
    m_r = make_result(m, rsubs, "", rf"Magnification $m = -d_i/d_o$ at $d_o = {do_def:g}$ m (a pure number)")
    m_r["symbolic_latex"] = r"-\dfrac{d_i}{d_o}"
    hi_r = make_result(hi, rsubs, "m", rf"Image height $h_i = m\,h_o$ at $d_o = {do_def:g}$ m, $h_o = {float(ho_val):g}$ m")
    hi_r["symbolic_latex"] = r"-\dfrac{h_o\,f}{d_o - f}"
    result = {"image_distance": di_r, "magnification": m_r, "image_height": hi_r}

    # classify the default image so the prose reads correctly for either lens (a converging lens gives a real
    # inverted image beyond f and a virtual upright one inside f; a diverging lens is always virtual/upright/reduced)
    di_val, m_val = float(di_r["value"]), float(m_r["value"])
    is_real = di_val > 0
    is_inverted = m_val < 0
    is_enlarged = abs(m_val) > 1
    di_sentence = (
        "It is **positive**, so the image is **real** — it forms on the far side of the lens, where you could "
        "place a screen." if is_real else
        "It is **negative**, so the image is **virtual** — it forms on the *same* side as the object. You cannot "
        "catch it on a screen; you see it by looking *through* the lens.")
    sign_word = "the sign is negative, so the image is **inverted**" if is_inverted \
        else "the sign is positive, so the image is **upright**"
    size_word = "$|m| > 1$, so it is **enlarged**" if is_enlarged else "$|m| < 1$, so it is **reduced**"
    if converging and is_real:
        regime = ("this is the projector regime ($f < d_o < 2f$). Slide the object *inside* the focal point and "
                  "$m$ flips positive — a magnifying glass.")
    elif converging:
        regime = ("inside the focal point, a converging lens acts as a **magnifying glass**.")
    else:
        regime = ("a diverging lens does this at *every* object distance — the image is always virtual, upright, "
                  "and shrunken, and can never be projected.")

    algebra = {
        "steps": [
            {
                "label": "What the algebra-based course hands you (two rules)",
                "latex": r"\frac{1}{d_o} + \frac{1}{d_i} = \frac{1}{f}, \qquad m = -\frac{d_i}{d_o} = \frac{h_i}{h_o}",
                "prose": "Two memorized equations. The first locates the image; the second gives its size and "
                         "orientation. A negative $m$ means the image is inverted; $|m| < 1$ means reduced; a "
                         "negative $d_i$ means the image is virtual (on the object's side).",
            },
            {
                "label": "Solve the lens equation for the image distance",
                "latex": rf"\frac{{1}}{{d_i}} = \frac{{1}}{{f}} - \frac{{1}}{{d_o}} \ \Longrightarrow\ "
                         rf"d_i = \frac{{d_o f}}{{d_o - f}} = {di_r['display']}\ \text{{m}}",
                "prose": f"With $f = {float(f_val):g}$ m and $d_o = {do_def:g}$ m, the image distance is "
                         f"$d_i = {di_r['display']}$ m. {di_sentence}",
            },
            {
                "label": "Read off the magnification and image height",
                "latex": rf"m = -\frac{{d_i}}{{d_o}} = {m_r['display']}, \qquad h_i = m\,h_o = {hi_r['display']}\ \text{{m}}",
                "prose": f"The magnification is $m = {m_r['display']}$: {sign_word}, and {size_word} — {regime}",
            },
        ],
        "result": result,
    }

    ray_rules = (
        "the ray *parallel* to the axis bends through the far focus $F'$; the ray through the lens *center* goes "
        "straight; the ray through the near focus $F$ leaves *parallel*. Each is a straight line you can rule by "
        "hand. Where they cross is the image." if converging else
        "the ray *parallel* to the axis bends **outward**, as if it had come from the near focus $F$; the ray "
        "through the lens *center* goes straight; the ray aimed at the far focus $F'$ leaves *parallel*. The "
        "refracted rays diverge — but traced *backward* they meet, and that crossing is the (virtual) image.")
    geometry = {
        "register_label": "Ray diagram",
        "steps": [
            {
                "label": "Draw three rays from the tip of the object — no equation needed",
                "latex": r"\text{(1) parallel}\leftrightarrow F \qquad \text{(2) through center}\to\text{straight} "
                         r"\qquad \text{(3) } F' \leftrightarrow \text{parallel}",
                "prose": f"Geometric optics needs no calculus and, at first, no algebra. From the object tip, "
                         f"{ray_rules}",
            },
            {
                "label": "Two of the rays give the magnification two different ways (similar triangles)",
                "latex": r"\underbrace{\frac{h_i}{h_o} = -\frac{d_i}{d_o}}_{\text{center ray}} \qquad "
                         r"\underbrace{\frac{h_i}{h_o} = -\frac{d_i - f}{f}}_{\text{parallel ray}}",
                "prose": "The center ray makes two similar triangles (object–axis–center and image–axis–center), so "
                         "$h_i/h_o = -d_i/d_o$. The parallel ray makes two more about a focal point, so "
                         "$h_i/h_o = -(d_i - f)/f$. Same ratio $h_i/h_o$, computed from two different rays.",
            },
            {
                "label": "Set the two equal — and the thin-lens equation falls out",
                "latex": r"-\frac{d_i}{d_o} = -\frac{d_i - f}{f} \ \Longrightarrow\ d_i f = d_o(d_i - f) "
                         r"\ \Longrightarrow\ \frac{1}{f} = \frac{1}{d_o} + \frac{1}{d_i}",
                "prose": "Demanding that the two rays cross at one point — that the two magnifications agree — and "
                         "clearing fractions gives $1/f = 1/d_o + 1/d_i$ exactly. The equation you memorized is the "
                         "algebra of *the rays meet*. (Deeper still, Fermat's principle: every path takes a "
                         "stationary time, $dL = 0$ — the one genuinely calculus statement underneath it all.)",
                "emphasis": True,
            },
        ],
    }

    lens = LensPlot(
        u=do,
        di_expr=di,
        hi_expr=hi,
        m_expr=m,
        focal_length=float(f_val),
        cursor=Slider(do, "u", do_lo, do_hi, do_def),
        sliders=[Slider(ho, "ho", ho_lo, ho_hi, float(ho_val))],
        constants={f: f_val},
        consts_export={"f": float(f_val)},
        unit_map={do: "m", f: "m", ho: "m"},
        annot=(f"{'Converging' if converging else 'Diverging'} lens, f = {float(f_val):g} m. "
               f"Object at dₒ = {do_def:g} m → a {'real, inverted' if is_real else 'virtual, upright'} image."),
    )

    return Scenario(
        regime=3,
        constants_export={"f": float(f_val), "do": do_def, "ho": float(ho_val)},
        proof=proof,
        algebra=algebra,
        calculus=geometry,
        lens=lens,
    )
