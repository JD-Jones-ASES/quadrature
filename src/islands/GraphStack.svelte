<script>
  // The pivot: a stacked temporal graph with a shared time axis. Default is x–t / v–t / a–t; with
  // `graph.panels` it generalizes to N panels (ADR-0021), e.g. RC charge Q–t over current I–t — the slope of
  // each panel is the panel below it (I is the slope of Q, exactly as v is the slope of x). Three modes
  // (ADR-0012): interactive (one JS closed form + sliders) · sampled (exact frames a slider snaps between) ·
  // static (a committed Matplotlib SVG, handled by the page). No SymPy or Matplotlib runs here.
  let { graph } = $props();

  const sampled = graph.mode === "sampled";
  const frames = graph.frames ?? [];
  const sweep = graph.sweep ?? null;
  const paramDefs = graph.params ?? {};
  const interactive = graph.mode === "interactive" && Object.keys(paramDefs).length > 0;
  const windowMode = graph.window ?? "fixed";

  const DEFAULT_LABELS = ["x  (m)", "v  (m/s)", "a  (m/s²)"];
  const panelDefs = graph.panels ?? [
    { key: "x", label: graph.labels?.[0] ?? DEFAULT_LABELS[0], accent: false },
    { key: "v", label: graph.labels?.[1] ?? DEFAULT_LABELS[1], accent: true },
    { key: "a", label: graph.labels?.[2] ?? DEFAULT_LABELS[2], accent: false },
  ];
  const nPanels = panelDefs.length;

  const compile = (expr, params) => new Function(...params, `"use strict"; return (${expr});`);

  let vals = $state(Object.fromEntries(Object.entries(paramDefs).map(([k, p]) => [k, p.default])));
  let frameIdx = $state(sampled ? Math.max(0, Math.floor(frames.length / 2)) : 0);

  const activeCF = $derived(sampled ? frames[frameIdx].closed_form : graph.closed_form);
  const activeParams = $derived(sampled ? frames[frameIdx].closed_form_params : graph.closed_form_params);
  const baseWindow = $derived(sampled ? frames[frameIdx].series.t_max : (graph.series?.t_max ?? 5));

  const fns = $derived.by(() => Object.fromEntries(panelDefs.map((p) => [p.key, compile(activeCF[p.key], activeParams)])));
  const call = (fn, t) => fn(...activeParams.map((p) => (p === "t" ? t : vals[p])));

  const tmax = $derived.by(() => {
    if (windowMode !== "landing" || !fns.x) return baseWindow;   // landing window is an x/v/a-only feature
    let prev = call(fns.x, 0);
    for (let t = 0.02; t <= 40; t += 0.02) {
      const cur = call(fns.x, t);
      if (cur <= 0 && prev > 0) {
        let lo = t - 0.02, hi = t;
        for (let k = 0; k < 44; k++) { const m = (lo + hi) / 2; if (call(fns.x, m) > 0) lo = m; else hi = m; }
        return Math.max(hi, 0.1);
      }
      prev = cur;
    }
    return baseWindow;
  });

  const apexT = $derived.by(() => {
    if (!fns.x || !fns.v) return null;
    let lo = 0, hi = tmax;
    if (call(fns.v, lo) * call(fns.v, hi) > 0) return null;
    for (let k = 0; k < 44; k++) { const m = (lo + hi) / 2; if (call(fns.v, lo) * call(fns.v, m) <= 0) hi = m; else lo = m; }
    return (lo + hi) / 2;
  });
  const showApex = $derived(windowMode === "landing" && apexT != null);
  const apexX = $derived(apexT == null ? null : call(fns.x, apexT));

  const N = 140;
  const samples = $derived.by(() => {
    const ts = [], cols = Object.fromEntries(panelDefs.map((p) => [p.key, []]));
    for (let i = 0; i <= N; i++) {
      const t = (i / N) * tmax;
      ts.push(t);
      for (const p of panelDefs) cols[p.key].push(call(fns[p.key], t));
    }
    return { ts, cols };
  });

  // geometry
  const W = 560, PADL = 52, PADR = 16, H = 132, GAP = 16, TOP = 8;
  const innerW = W - PADL - PADR;
  const px = (t) => PADL + (t / tmax) * innerW;
  const band = (i) => TOP + i * (H + GAP);
  function rangeOf(arr) {
    let lo = Math.min(...arr, 0), hi = Math.max(...arr, 0);
    if (hi - lo < 1e-9) { hi += 1; lo -= 1; }
    const pad = (hi - lo) * 0.12;
    return [lo - pad, hi + pad];
  }
  const py = (val, [lo, hi], i) => band(i) + H - ((val - lo) / (hi - lo)) * H;
  const poly = (arr, rng, i) => samples.ts.map((t, k) => `${px(t).toFixed(1)},${py(arr[k], rng, i).toFixed(1)}`).join(" ");

  const ranges = $derived(Object.fromEntries(panelDefs.map((p) => [p.key, rangeOf(samples.cols[p.key])])));

  const areaPoly = $derived.by(() => {
    if (!showApex) return "";
    const pts = [];
    for (let i = 0; i <= N; i++) { const t = (i / N) * apexT; pts.push(`${px(t).toFixed(1)},${py(call(fns.v, t), ranges.v, 1).toFixed(1)}`); }
    pts.push(`${px(apexT).toFixed(1)},${py(0, ranges.v, 1).toFixed(1)}`);
    pts.push(`${px(0).toFixed(1)},${py(0, ranges.v, 1).toFixed(1)}`);
    return pts.join(" ");
  });

  const panelsView = panelDefs.map((p, i) => ({ ...p, i }));
  const svgH = TOP + nPanels * H + (nPanels - 1) * GAP + 24;
  const fmt = (n) => (Math.abs(n) >= 100 ? n.toFixed(0) : n.toFixed(1));
</script>

<div class="graphstack">
  <svg viewBox={`0 0 ${W} ${svgH}`} role="img"
       aria-label="Stacked time-series graph; the slope of each panel is the value of the panel below it">
    {#each panelsView as p}
      {@const rng = ranges[p.key]}
      <rect x={PADL} y={band(p.i)} width={innerW} height={H} class="frame" />
      <text x="6" y={band(p.i) + 14} class="axlabel">{p.label}</text>
      <line x1={PADL} y1={py(0, rng, p.i)} x2={W - PADR} y2={py(0, rng, p.i)} class="zero" />
      {#if showApex}
        <line x1={px(apexT)} y1={band(p.i)} x2={px(apexT)} y2={band(p.i) + H} class="apexline" />
      {/if}
      {#if showApex && p.key === "v" && areaPoly}
        <polygon points={areaPoly} class="area" />
      {/if}
      <polyline points={poly(samples.cols[p.key], rng, p.i)} class="curve" class:accent={p.accent} />
      {#if showApex && p.key === "x"}
        <circle cx={px(apexT)} cy={py(apexX, rng, p.i)} r="4" class="mark" />
      {/if}
      {#if showApex && p.key === "v"}
        <circle cx={px(apexT)} cy={py(0, rng, p.i)} r="4" class="mark" />
      {/if}
    {/each}
    <text x={PADL} y={svgH - 6} class="axlabel">t = 0</text>
    <text x={W - PADR} y={svgH - 6} class="axlabel" text-anchor="end">t = {tmax.toFixed(2)} s</text>
  </svg>

  {#if sampled}
    <div class="sliders">
      <label>
        <span class="pname">{sweep?.label} = {fmt(frames[frameIdx].value)}{sweep?.unit ? " " + sweep.unit : ""}</span>
        <input type="range" min="0" max={frames.length - 1} step="1" bind:value={frameIdx} />
      </label>
      <p class="framelabel" class:critical={sweep?.critical != null && Math.abs(frames[frameIdx].value - sweep.critical) < 1e-6}>
        {frames[frameIdx].label}
        {#if sweep?.critical != null} · critical at {sweep.label} = {fmt(sweep.critical)}{/if}
      </p>
      <p class="hint faint">Each stop is an exact, separately verified solution — the form changes at the
        critical value, so the slider snaps between them rather than morphing one formula.</p>
    </div>
  {:else}
    <div class="annot">
      {#if showApex}
        <p><strong>Apex</strong> at t = {apexT.toFixed(2)} s, x = {apexX.toFixed(2)} m: on v–t the line crosses
          zero but its <em>slope never changes</em> — that slope is a, and a is never zero. The shaded area
          under v from 0 to the apex is exactly the rise in x.</p>
      {:else}
        <p>The panels share a time axis: the <strong>slope</strong> of each graph is the value of the one
          below it, and the <strong>area</strong> under each is the change in the one above.</p>
      {/if}
    </div>
    {#if interactive}
      <div class="sliders">
        {#each Object.entries(paramDefs) as [name, def]}
          <label>
            <span class="pname">{name} = {fmt(vals[name])}</span>
            <input type="range" min={def.min} max={def.max} step={(def.max - def.min) / 100} bind:value={vals[name]} />
          </label>
        {/each}
        <p class="hint faint">Drag a slider and watch the panels move together.</p>
      </div>
    {/if}
  {/if}
</div>

<style>
  .graphstack { display: grid; gap: 0.5rem; }
  svg { width: 100%; height: auto; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); }
  .frame { fill: none; stroke: var(--line); stroke-width: 1; }
  .zero { stroke: color-mix(in srgb, var(--ink-faint) 60%, transparent); stroke-width: 1; }
  .apexline { stroke: var(--ink-faint); stroke-width: 1; stroke-dasharray: 3 3; opacity: 0.7; }
  .curve { fill: none; stroke: var(--ink); stroke-width: 2; }
  .curve.accent { stroke: var(--accent); }
  .area { fill: color-mix(in srgb, var(--accent) 16%, transparent); stroke: none; }
  .mark { fill: var(--accent); }
  .axlabel { fill: var(--ink-faint); font-size: 11px; font-family: var(--font-mono); }
  .annot p { font-size: 0.9rem; color: var(--ink-2); margin: 0.3rem 0; }
  .sliders { display: grid; gap: 0.4rem; padding-top: 0.3rem; }
  .sliders label { display: grid; grid-template-columns: 12rem 1fr; align-items: center; gap: 0.8rem; }
  .pname { font-family: var(--font-mono); font-size: 0.85rem; }
  .sliders input[type="range"] { width: 100%; accent-color: var(--accent); }
  .framelabel { margin: 0.1rem 0; font-weight: 600; }
  .framelabel.critical { color: var(--accent); }
  .hint { font-size: 0.82rem; margin: 0.2rem 0 0; }
</style>
