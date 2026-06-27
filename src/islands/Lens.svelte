<script>
  // The thin-lens ray-diagram instrument (ADR-0024, the 7th): a GEOMETRIC construction, not a curve. A
  // converging lens of fixed focal length f sits at the origin; an upright object stands a distance dₒ to the
  // left (the cursor). The island draws the three principal rays and reads off where they cross — the image —
  // recomputing live as the object moves. The closed forms dᵢ(dₒ), hᵢ(dₒ, hₒ), m(dₒ) are JS-cheap and
  // parity-verified; nothing runs SymPy here. As dₒ crosses the focal point f, the image flips from
  // real/inverted (projector) to virtual/upright/enlarged (magnifying glass).
  let { graph } = $props();

  const f = graph.consts.f;
  const cur = graph.cursor;                 // object distance dₒ (the canonical `u` axis)
  const hoParam = graph.params.ho;

  const compile = (expr, params) => new Function(...params, `"use strict"; return (${expr});`);
  const diFn = compile(graph.closed_form.di, graph.closed_form_params);
  const hiFn = compile(graph.closed_form.hi, graph.closed_form_params);
  const mFn = compile(graph.closed_form.m, graph.closed_form_params);
  const ev = (fn, ho, dobj) => fn(...graph.closed_form_params.map((p) => (p === "ho" ? ho : dobj)));

  let dobj = $state(cur.default);           // object distance
  let ho = $state(hoParam.default);         // object height

  const di = $derived(ev(diFn, ho, dobj));
  const hi = $derived(ev(hiFn, ho, dobj));
  const m = $derived(ev(mFn, ho, dobj));

  const converging = f > 0;                      // f > 0 converging lens; f < 0 diverging (always virtual/reduced)
  const atFocus = $derived(converging && Math.abs(dobj - f) < 0.02);
  const real = $derived(!atFocus && di > 0);
  const inverted = $derived(m < 0);
  const enlarged = $derived(Math.abs(m) > 1.0001);

  // --- physical viewport (optics diagrams are not drawn to scale: x and y scale independently) ---
  const xLo = -(cur.max + 0.5), xHi = cur.max + 0.5;
  const yHalf = Math.max(hoParam.max, 0.5) * 2.6;
  const W = 640, H = 300, PADL = 14, PADR = 14, PADT = 14, PADB = 30;
  const innerW = W - PADL - PADR, innerH = H - PADT - PADB;
  const midY = PADT + innerH / 2;
  const px = (x) => PADL + ((x - xLo) / (xHi - xLo)) * innerW;
  const py = (y) => midY - (y / yHalf) * (innerH / 2);

  // Liang–Barsky clip of the physical segment p0→p1 to [xLo,xHi]×[-yHalf,yHalf]; null if outside.
  function clip(p0, p1) {
    let [x0, y0] = p0, [x1, y1] = p1;
    const dx = x1 - x0, dy = y1 - y0;
    let t0 = 0, t1 = 1;
    const edges = [[-dx, x0 - xLo], [dx, xHi - x0], [-dy, y0 + yHalf], [dy, yHalf - y0]];
    for (const [p, q] of edges) {
      if (p === 0) { if (q < 0) return null; continue; }
      const r = q / p;
      if (p < 0) { if (r > t1) return null; if (r > t0) t0 = r; }
      else { if (r < t0) return null; if (r < t1) t1 = r; }
    }
    return [[x0 + t0 * dx, y0 + t0 * dy], [x0 + t1 * dx, y0 + t1 * dy]];
  }

  const seg = (p0, p1) => {
    const c = clip(p0, p1);
    return c ? `${px(c[0][0])},${py(c[0][1])} ${px(c[1][0])},${py(c[1][1])}` : null;
  };

  // a half-line from `start` along `dir` (physical units), long enough to exit the viewport, then clipped
  const diag = Math.hypot(xHi - xLo, 2 * yHalf) * 1.3;
  function halfline(start, dir, sign) {
    const len = Math.hypot(dir[0], dir[1]) || 1;
    const end = [start[0] + (sign * dir[0] / len) * diag, start[1] + (sign * dir[1] / len) * diag];
    return seg(start, end);
  }

  const Otip = $derived([-dobj, ho]);
  const Ipt = $derived([di, hi]);
  const onWindow = $derived(di > xLo && di < xHi && Math.abs(hi) < yHalf * 1.02);

  // the three principal rays: each an incident segment (object→lens) + a refracted half-line, plus (for a
  // virtual image) a dashed backward extension that meets at the image behind the lens.
  const rays = $derived.by(() => {
    const A = [0, ho], C = [0, 0], B = [0, hi];
    // Refracted-ray directions, written so the forward (transmitted) half always travels right (+x), for BOTH
    // a converging (f>0) and a diverging (f<0) lens: the parallel ray's slope is −hₒ/f (down for converging,
    // up/diverging for f<0); the chief ray continues straight through the centre; the focal ray emerges parallel.
    const defs = [
      { inc: seg(Otip, A), lens: A, dir: [1, -ho / f], cls: "r1" },   // parallel → toward/from the focus
      { inc: seg(Otip, C), lens: C, dir: [dobj, -ho], cls: "r2" },    // chief, through the centre
      { inc: seg(Otip, B), lens: B, dir: [1, 0], cls: "r3" },         // focal ray → parallel out
    ];
    return defs.map((d) => ({
      cls: d.cls,
      inc: d.inc,
      fwd: halfline(d.lens, d.dir, 1),
      back: real ? null : halfline(d.lens, d.dir, -1),
    }));
  });

  // focal points: F always on the object side (left), F′ on the image side (right), at distance |f| — so the
  // labels do not swap when f goes negative.
  const af = Math.abs(f);
  const foci = [
    { x: -af, label: "F" }, { x: af, label: "F′" },
    { x: -2 * af, label: "2F" }, { x: 2 * af, label: "2F′" },
  ].filter((d) => d.x > xLo && d.x < xHi);

  // lens glyph arrowheads: outward (≷) for a converging lens, inward (≶) for a diverging lens
  const lensHead = $derived.by(() => {
    const cx = px(0), yT = py(yHalf * 0.9), yB = py(-yHalf * 0.9), s = converging ? 1 : -1;
    return {
      top: `${cx - 6},${yT + 9 * s} ${cx},${yT} ${cx + 6},${yT + 9 * s}`,
      bot: `${cx - 6},${yB - 9 * s} ${cx},${yB} ${cx + 6},${yB - 9 * s}`,
    };
  });

  const fmt = (x) => (Math.abs(x) >= 100 ? x.toFixed(0) : Math.abs(x) >= 10 ? x.toFixed(1) : x.toFixed(2));
  const objArrow = $derived(seg([-dobj, 0], [-dobj, ho]));
  const imgArrow = $derived(seg([di, 0], [di, hi]));
</script>

<div class="lens">
  <svg viewBox={`0 0 ${W} ${H}`} role="img"
       aria-label={`Thin-lens ray diagram: object at ${fmt(dobj)} m, ${real ? "real inverted" : "virtual upright"} image`}>
    <!-- optical axis -->
    <line x1={px(xLo)} y1={py(0)} x2={px(xHi)} y2={py(0)} class="axis" />
    <!-- the lens: a vertical line with arrowheads — outward for converging, inward for diverging -->
    <line x1={px(0)} y1={py(yHalf * 0.9)} x2={px(0)} y2={py(-yHalf * 0.9)} class="lens-body" />
    <polyline points={lensHead.top} class="lens-body" fill="none" />
    <polyline points={lensHead.bot} class="lens-body" fill="none" />
    <!-- focal points -->
    {#each foci as fp}
      <circle cx={px(fp.x)} cy={py(0)} r="3" class="focus" />
      <text x={px(fp.x)} y={py(0) + 16} class="flabel" text-anchor="middle">{fp.label}</text>
    {/each}

    <!-- the three principal rays -->
    {#each rays as r}
      {#if r.inc}<polyline points={r.inc} class={`ray ${r.cls}`} />{/if}
      {#if r.fwd}<polyline points={r.fwd} class={`ray ${r.cls}`} />{/if}
      {#if r.back}<polyline points={r.back} class={`ray ${r.cls} virtual`} />{/if}
    {/each}

    <!-- object (upright) and image (inverted=real / upright=virtual) -->
    {#if objArrow}
      <polyline points={objArrow} class="object" marker-end="url(#arrowO)" />
    {/if}
    {#if imgArrow && onWindow}
      <polyline points={imgArrow} class={`image ${real ? "" : "virtual"}`} marker-end="url(#arrowI)" />
    {/if}

    <defs>
      <marker id="arrowO" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" class="mk-o" />
      </marker>
      <marker id="arrowI" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" class="mk-i" />
      </marker>
    </defs>
  </svg>

  <div class="readout">
    {#if atFocus}
      <p>Object <strong class="acc">at the focal point</strong> (dₒ = f = {fmt(f)} m): the refracted rays come out
        <strong>parallel</strong> — they never meet, so the image is <strong>at infinity</strong>. This is how a
        flashlight makes a beam.</p>
    {:else if real}
      <p>Object at <strong class="acc">dₒ = {fmt(dobj)} m</strong> (outside the focal point): a
        <strong>real, {inverted ? "inverted" : "upright"}</strong>, {enlarged ? "enlarged" : "reduced"} image forms at
        <strong class="acc">dᵢ = {fmt(di)} m</strong> on the far side — catchable on a screen.
        Magnification <strong>m = {fmt(m)}</strong> (negative ⇒ inverted{enlarged ? `, |m| > 1 ⇒ enlarged` : `, |m| < 1 ⇒ reduced`}).
        {#if !onWindow}<em>The image is off the diagram — the three rays are still converging toward it.</em>{/if}</p>
    {:else}
      <p>Object at <strong class="acc">dₒ = {fmt(dobj)} m</strong>: the refracted rays
        <strong>diverge</strong>, so no real image forms. Tracing them <em>backward</em> (dashed) they meet at a
        <strong>virtual, {inverted ? "inverted" : "upright"}, {enlarged ? "enlarged" : "reduced"}</strong> image at
        <strong class="acc">dᵢ = {fmt(di)} m</strong> (same side as the object).
        Magnification <strong>m = {fmt(m)}</strong> —
        {converging ? "inside the focal point a converging lens is a magnifying glass." : "a diverging lens does this at every object distance, like a peephole viewer."}</p>
    {/if}
  </div>

  <div class="sliders">
    <label>
      <span class="pname">object dₒ = {fmt(dobj)} m</span>
      <input type="range" min={cur.min} max={cur.max} step="0.01" bind:value={dobj} />
    </label>
    <label>
      <span class="pname">height hₒ = {fmt(ho)} m</span>
      <input type="range" min={hoParam.min} max={hoParam.max} step="0.01" bind:value={ho} />
    </label>
    <div class="chips">
      {#if converging}
        <button class="chip" onclick={() => (dobj = 2 * f)}>dₒ = 2f (same size)</button>
        <button class="chip" onclick={() => (dobj = 1.5 * f)}>between f and 2f (projector)</button>
        <button class="chip" onclick={() => (dobj = Math.max(cur.min, 0.6 * f))}>inside f (magnifier)</button>
      {:else}
        <button class="chip" onclick={() => (dobj = Math.max(cur.min, 0.5 * af))}>close up</button>
        <button class="chip" onclick={() => (dobj = af)}>dₒ = |f|</button>
        <button class="chip" onclick={() => (dobj = Math.min(cur.max, 3 * af))}>far away</button>
      {/if}
    </div>
    <p class="hint faint">The magnification m = −dᵢ/dₒ depends only on the two <em>distances</em>, never on the
      object's height — drag hₒ and watch m hold steady while the image scales with the object.</p>
  </div>
</div>

<style>
  .lens { display: grid; gap: 0.5rem; }
  svg { width: 100%; height: auto; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); }
  .axis { stroke: color-mix(in srgb, var(--ink-faint) 55%, transparent); stroke-width: 1; }
  .lens-body { stroke: var(--ink); stroke-width: 2; }
  .focus { fill: var(--ink-faint); }
  .flabel { fill: var(--ink-faint); font-size: 11px; font-family: var(--font-mono); }

  .ray { fill: none; stroke-width: 1.4; }
  .ray.r1 { stroke: var(--accent); }
  .ray.r2 { stroke: color-mix(in srgb, var(--ink) 55%, var(--paper)); }
  .ray.r3 { stroke: var(--warn); }
  .ray.virtual { stroke-dasharray: 4 4; opacity: 0.6; }

  .object { fill: none; stroke: var(--ink); stroke-width: 2.6; }
  .image { fill: none; stroke: var(--accent); stroke-width: 2.6; }
  .image.virtual { stroke-dasharray: 5 4; opacity: 0.85; }
  .mk-o { fill: var(--ink); }
  .mk-i { fill: var(--accent); }

  .readout p { font-size: 0.92rem; color: var(--ink-2); margin: 0.2rem 0; line-height: 1.55; }
  .readout .acc { color: var(--accent); }

  .sliders { display: grid; gap: 0.5rem; padding-top: 0.2rem; }
  .sliders label { display: grid; grid-template-columns: 11rem 1fr; align-items: center; gap: 0.8rem; }
  .pname { font-family: var(--font-mono); font-size: 0.85rem; }
  .sliders input[type="range"] { width: 100%; accent-color: var(--accent); }
  .chips { display: flex; flex-wrap: wrap; gap: 0.35rem; }
  .chip {
    font: inherit; font-size: 0.8rem; font-family: var(--font-mono); cursor: pointer;
    background: var(--paper-2); border: 1px solid var(--line); border-radius: 999px; padding: 0.2rem 0.6rem; color: var(--ink-2);
  }
  .chip:hover { border-color: var(--accent); color: var(--accent); }
  .hint { font-size: 0.82rem; margin: 0.2rem 0 0; }
</style>
