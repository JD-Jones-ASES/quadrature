<script>
  // The integral instrument off the time axis (ADR-0014): the pivot is a force–displacement graph, not
  // an x–t/v–t/a–t stack. Top panel = the integrand f(u) (e.g. force F(x)); the shaded AREA under it from
  // u0 to the cursor IS the accumulated integral g (e.g. work W). Bottom panel = g(u), whose SLOPE is f.
  // Same "slope↔value / area↔change" thesis, with u (position/volume/…) as the integration variable.
  // The closed forms f(u), g(u) are JS-cheap and parity-verified; no SymPy/Matplotlib runs here.
  let { graph } = $props();

  const paramDefs = graph.params ?? {};
  const cursor = graph.cursor;
  const u0 = graph.u0 ?? 0;
  const uMax = graph.series?.u_max ?? cursor.max;

  const compile = (expr, params) => new Function(...params, `"use strict"; return (${expr});`);
  const fns = {
    f: compile(graph.closed_form.f, graph.closed_form_params),
    g: compile(graph.closed_form.g, graph.closed_form_params),
  };

  let vals = $state(Object.fromEntries(Object.entries(paramDefs).map(([k, p]) => [k, p.default])));
  let uc = $state(cursor.default);

  const call = (fn, uu) => fn(...graph.closed_form_params.map((p) => (p === cursor.name ? uu : vals[p])));

  const N = 140;
  const samples = $derived.by(() => {
    const us = [], fs = [], gs = [];
    for (let i = 0; i <= N; i++) {
      const u = u0 + (i / N) * (uMax - u0);
      us.push(u); fs.push(call(fns.f, u)); gs.push(call(fns.g, u));
    }
    return { us, fs, gs };
  });

  const fAtC = $derived(call(fns.f, uc));
  const gAtC = $derived(call(fns.g, uc));
  const rectAtC = $derived(fAtC * (uc - u0)); // the "F_max × d" rectangle the misconception assumes

  // geometry — two stacked panels sharing the u axis
  const W = 560, PADL = 52, PADR = 16, H = 150, GAP = 22, TOP = 8;
  const innerW = W - PADL - PADR;
  const px = (u) => PADL + ((u - u0) / (uMax - u0)) * innerW;
  const band = (i) => TOP + i * (H + GAP);
  function rangeOf(arr) {
    let lo = Math.min(...arr, 0), hi = Math.max(...arr, 0);
    if (hi - lo < 1e-9) { hi += 1; lo -= 1; }
    const pad = (hi - lo) * 0.14;
    return [lo - pad, hi + pad];
  }
  const py = (val, [lo, hi], i) => band(i) + H - ((val - lo) / (hi - lo)) * H;

  const rf = $derived(rangeOf(samples.fs));
  const rg = $derived(rangeOf(samples.gs));

  const fLine = $derived(samples.us.map((u, k) => `${px(u).toFixed(1)},${py(samples.fs[k], rf, 0).toFixed(1)}`).join(" "));
  const gLine = $derived(samples.us.map((u, k) => `${px(u).toFixed(1)},${py(samples.gs[k], rg, 1).toFixed(1)}`).join(" "));

  // shaded area under f from u0 to the cursor (= the work)
  const areaPoly = $derived.by(() => {
    const pts = [];
    const steps = 80;
    for (let i = 0; i <= steps; i++) {
      const u = u0 + (i / steps) * (uc - u0);
      pts.push(`${px(u).toFixed(1)},${py(call(fns.f, u), rf, 0).toFixed(1)}`);
    }
    pts.push(`${px(uc).toFixed(1)},${py(0, rf, 0).toFixed(1)}`);
    pts.push(`${px(u0).toFixed(1)},${py(0, rf, 0).toFixed(1)}`);
    return pts.join(" ");
  });

  const fmt = (n) => (Math.abs(n) >= 100 ? n.toFixed(0) : Math.abs(n) >= 10 ? n.toFixed(1) : n.toFixed(2));

  // Parse "SYMBOL  (UNIT)" labels the producer supplies, so the live caption names the right quantity for
  // EVERY area lesson (work W·J, force F·N, energy U·J, moment I·kg·m², …) — not a hardcoded work–energy one.
  const parseLabel = (lbl) => {
    const m = /^(.*?)\s*\(([^)]*)\)\s*$/.exec(lbl ?? "");
    return m ? { sym: m[1].trim(), unit: m[2].trim() } : { sym: (lbl ?? "").trim(), unit: "" };
  };
  const gL = parseLabel(graph.g_label);
  const fL = parseLabel(graph.f_label);
  const uSym = graph.u_label.split("(")[0].trim();
  const uUnit = cursor.unit ?? parseLabel(graph.u_label).unit;
</script>

<div class="areaplot">
  <svg viewBox={`0 0 ${W} ${TOP + 2 * H + GAP + 24}`} role="img"
       aria-label={`${fL.sym} versus ${uSym}, with the shaded area equal to the accumulated ${gL.sym} below`}>
    <!-- top: the integrand f(u) with its area shaded to the cursor -->
    <rect x={PADL} y={band(0)} width={innerW} height={H} class="frame" />
    <text x="6" y={band(0) + 14} class="axlabel">{graph.f_label}</text>
    <line x1={PADL} y1={py(0, rf, 0)} x2={W - PADR} y2={py(0, rf, 0)} class="zero" />
    <!-- the rectangle F(x)·x the misconception assumes (faint), to contrast with the triangle -->
    <rect x={px(u0)} y={py(fAtC, rf, 0)} width={Math.max(0, px(uc) - px(u0))}
          height={Math.max(0, py(0, rf, 0) - py(fAtC, rf, 0))} class="rect" />
    <polygon points={areaPoly} class="area" />
    <polyline points={fLine} class="curve f" />
    <line x1={px(uc)} y1={band(0)} x2={px(uc)} y2={band(0) + H} class="cursorline" />
    <circle cx={px(uc)} cy={py(fAtC, rf, 0)} r="4" class="mark" />

    <!-- bottom: the accumulated integral g(u); its slope is f -->
    <rect x={PADL} y={band(1)} width={innerW} height={H} class="frame" />
    <text x="6" y={band(1) + 14} class="axlabel">{graph.g_label}</text>
    <line x1={PADL} y1={py(0, rg, 1)} x2={W - PADR} y2={py(0, rg, 1)} class="zero" />
    <polyline points={gLine} class="curve g" />
    <line x1={px(uc)} y1={band(1)} x2={px(uc)} y2={band(1) + H} class="cursorline" />
    <line x1={PADL} y1={py(gAtC, rg, 1)} x2={px(uc)} y2={py(gAtC, rg, 1)} class="valueline" />
    <circle cx={px(uc)} cy={py(gAtC, rg, 1)} r="4" class="mark" />

    <text x={PADL} y={TOP + 2 * H + GAP + 18} class="axlabel">{graph.u_label.split("(")[0].trim()} = {fmt(u0)}</text>
    <text x={W - PADR} y={TOP + 2 * H + GAP + 18} class="axlabel" text-anchor="end">{graph.u_label}</text>
  </svg>

  <div class="annot">
    <p>
      At <strong>{uSym} = {fmt(uc)} {uUnit}</strong>:
      the shaded area under the {fL.sym} curve is
      <strong class="g">{gL.sym} = {fmt(gAtC)} {gL.unit}</strong>, and the slope of the {gL.sym} curve below
      is <strong class="f">{fL.sym} = {fmt(fAtC)} {fL.unit}</strong>.
      A rectangle of that height, {fL.sym}·{uSym} = {fmt(rectAtC)} {gL.unit}, would miss it — because
      {fL.sym} isn't constant, the accumulated value is the <em>area under the curve</em>, not a rectangle.
    </p>
  </div>

  <div class="sliders">
    <label>
      <span class="pname">{graph.u_label.split("(")[0].trim()} = {fmt(uc)} {cursor.unit ?? ""}</span>
      <input type="range" min={cursor.min} max={cursor.max} step={(cursor.max - cursor.min) / 200} bind:value={uc} />
    </label>
    {#each Object.entries(paramDefs) as [name, def]}
      <label>
        <span class="pname">{name} = {fmt(vals[name])}</span>
        <input type="range" min={def.min} max={def.max} step={(def.max - def.min) / 100} bind:value={vals[name]} />
      </label>
    {/each}
    <p class="hint faint">Drag the cursor: the shaded area and the value on the lower graph move
      together — the area under the {fL.sym} curve <em>is</em> the accumulated {gL.sym}.</p>
  </div>
</div>

<style>
  .areaplot { display: grid; gap: 0.5rem; }
  svg { width: 100%; height: auto; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); }
  .frame { fill: none; stroke: var(--line); stroke-width: 1; }
  .zero { stroke: color-mix(in srgb, var(--ink-faint) 60%, transparent); stroke-width: 1; }
  .curve { fill: none; stroke-width: 2; }
  .curve.f { stroke: var(--ink); }
  .curve.g { stroke: var(--accent); }
  .area { fill: color-mix(in srgb, var(--accent) 20%, transparent); stroke: none; }
  .rect { fill: color-mix(in srgb, var(--ink-faint) 10%, transparent); stroke: var(--ink-faint); stroke-width: 1; stroke-dasharray: 3 3; }
  .cursorline { stroke: var(--ink-faint); stroke-width: 1; stroke-dasharray: 3 3; opacity: 0.8; }
  .valueline { stroke: var(--accent); stroke-width: 1; stroke-dasharray: 2 2; opacity: 0.7; }
  .mark { fill: var(--accent); }
  .axlabel { fill: var(--ink-faint); font-size: 11px; font-family: var(--font-mono); }
  .annot p { font-size: 0.92rem; color: var(--ink-2); margin: 0.3rem 0; line-height: 1.5; }
  .annot .g { color: var(--accent); }
  .annot .f { color: var(--ink); }
  .sliders { display: grid; gap: 0.4rem; padding-top: 0.3rem; }
  .sliders label { display: grid; grid-template-columns: 12rem 1fr; align-items: center; gap: 0.8rem; }
  .pname { font-family: var(--font-mono); font-size: 0.85rem; }
  .sliders input[type="range"] { width: 100%; accent-color: var(--accent); }
  .hint { font-size: 0.82rem; margin: 0.2rem 0 0; }
</style>
