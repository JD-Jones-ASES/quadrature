<script>
  // The pivot: stacked x–t / v–t / a–t with a shared time axis. Three graph modes (ADR-0012):
  //   interactive — one JS-cheap closed form driven by parameter sliders;
  //   sampled     — discrete exact frames (the solution form changes across the sweep, e.g. damping
  //                 crossing critical); a frame slider snaps between exact, parity-verified solutions;
  //   static      — a committed Matplotlib SVG (handled by the page, not here).
  // No SymPy or Matplotlib runs here.
  let { graph } = $props();

  const sampled = graph.mode === "sampled";
  const frames = graph.frames ?? [];
  const sweep = graph.sweep ?? null;
  const paramDefs = graph.params ?? {};
  const interactive = graph.mode === "interactive" && Object.keys(paramDefs).length > 0;
  const windowMode = graph.window ?? "fixed";

  const compile = (expr, params) => new Function(...params, `"use strict"; return (${expr});`);

  let vals = $state(Object.fromEntries(Object.entries(paramDefs).map(([k, p]) => [k, p.default])));
  let frameIdx = $state(sampled ? Math.max(0, Math.floor(frames.length / 2)) : 0);

  const activeCF = $derived(sampled ? frames[frameIdx].closed_form : graph.closed_form);
  const activeParams = $derived(sampled ? frames[frameIdx].closed_form_params : graph.closed_form_params);
  const baseWindow = $derived(sampled ? frames[frameIdx].series.t_max : (graph.series?.t_max ?? 5));

  const fns = $derived.by(() => ({
    x: compile(activeCF.x, activeParams),
    v: compile(activeCF.v, activeParams),
    a: compile(activeCF.a, activeParams),
  }));
  const call = (fn, t) => fn(...activeParams.map((p) => (p === "t" ? t : vals[p])));

  const tmax = $derived.by(() => {
    if (windowMode !== "landing") return baseWindow;
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
    let lo = 0, hi = tmax;
    if (call(fns.v, lo) * call(fns.v, hi) > 0) return null;
    for (let k = 0; k < 44; k++) { const m = (lo + hi) / 2; if (call(fns.v, lo) * call(fns.v, m) <= 0) hi = m; else lo = m; }
    return (lo + hi) / 2;
  });
  const showApex = $derived(windowMode === "landing" && apexT != null);
  const apexX = $derived(apexT == null ? null : call(fns.x, apexT));

  const N = 140;
  const samples = $derived.by(() => {
    const ts = [], xs = [], vs = [], as = [];
    for (let i = 0; i <= N; i++) {
      const t = (i / N) * tmax;
      ts.push(t); xs.push(call(fns.x, t)); vs.push(call(fns.v, t)); as.push(call(fns.a, t));
    }
    return { ts, xs, vs, as };
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

  const rx = $derived(rangeOf(samples.xs));
  const rv = $derived(rangeOf(samples.vs));
  const ra = $derived(rangeOf(samples.as));

  const areaPoly = $derived.by(() => {
    if (!showApex) return "";
    const pts = [];
    for (let i = 0; i <= N; i++) { const t = (i / N) * apexT; pts.push(`${px(t).toFixed(1)},${py(call(fns.v, t), rv, 1).toFixed(1)}`); }
    pts.push(`${px(apexT).toFixed(1)},${py(0, rv, 1).toFixed(1)}`);
    pts.push(`${px(0).toFixed(1)},${py(0, rv, 1).toFixed(1)}`);
    return pts.join(" ");
  });

  const panels = [
    { i: 0, rng: () => rx, arr: () => samples.xs, key: "x" },
    { i: 1, rng: () => rv, arr: () => samples.vs, key: "v" },
    { i: 2, rng: () => ra, arr: () => samples.as, key: "a" },
  ];
  const fmt = (n) => (Math.abs(n) >= 100 ? n.toFixed(0) : n.toFixed(1));
</script>

<div class="graphstack">
  <svg viewBox={`0 0 ${W} ${TOP + 3 * H + 2 * GAP + 24}`} role="img"
       aria-label="Stacked position, velocity, and acceleration versus time">
    {#each panels as p}
      {@const rng = p.rng()}
      <rect x={PADL} y={band(p.i)} width={innerW} height={H} class="frame" />
      <text x="6" y={band(p.i) + 14} class="axlabel">{graph.labels?.[p.i] ?? ["x  (m)", "v  (m/s)", "a  (m/s²)"][p.i]}</text>
      <line x1={PADL} y1={py(0, rng, p.i)} x2={W - PADR} y2={py(0, rng, p.i)} class="zero" />
      {#if showApex}
        <line x1={px(apexT)} y1={band(p.i)} x2={px(apexT)} y2={band(p.i) + H} class="apexline" />
      {/if}
      {#if showApex && p.key === "v" && areaPoly}
        <polygon points={areaPoly} class="area" />
      {/if}
      <polyline points={poly(p.arr(), rng, p.i)} class={`curve ${p.key}`} />
      {#if showApex && p.key === "x"}
        <circle cx={px(apexT)} cy={py(apexX, rng, p.i)} r="4" class="mark" />
      {/if}
      {#if showApex && p.key === "v"}
        <circle cx={px(apexT)} cy={py(0, rng, p.i)} r="4" class="mark" />
      {/if}
    {/each}
    <text x={PADL} y={TOP + 3 * H + 2 * GAP + 18} class="axlabel">t = 0</text>
    <text x={W - PADR} y={TOP + 3 * H + 2 * GAP + 18} class="axlabel" text-anchor="end">t = {tmax.toFixed(2)} s</text>
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
        <p>The three panels share a time axis: the <strong>slope</strong> of each graph is the value of the one
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
        <p class="hint faint">Drag a slider and watch all three panels move together.</p>
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
  .curve.v { stroke: var(--accent); }
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
