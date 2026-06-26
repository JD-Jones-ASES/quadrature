<script>
  // The pivot: stacked x–t / v–t / a–t with a shared time axis. Interactive graphs are redrawn here
  // in pure JS from the exported closed form (no SymPy, no Matplotlib). Drag v₀ (or x₀) and the
  // parabola, the v-line, and the apex move together — slope↔value and area↔change made tangible.
  let { graph } = $props();

  const cf = graph.closed_form;
  const cfp = graph.closed_form_params;
  const paramDefs = graph.params ?? {};
  const interactive = graph.mode === "interactive" && Object.keys(paramDefs).length > 0;

  const compile = (expr) => new Function(...cfp, `"use strict"; return (${expr});`);
  const fx = compile(cf.x), fv = compile(cf.v), fa = compile(cf.a);

  let vals = $state(Object.fromEntries(Object.entries(paramDefs).map(([k, p]) => [k, p.default])));

  const call = (fn, t) => fn(...cfp.map((p) => (p === "t" ? t : vals[p])));

  const windowMode = graph.window ?? "fixed";
  const baseWindow = graph.series?.t_max ?? 5;

  // "landing" (projectile): clip at the first downward zero-crossing of x, which adapts to the
  // launch parameters. "fixed" (oscillator / decay): use the model's authored window.
  const tmax = $derived.by(() => {
    if (windowMode !== "landing") return baseWindow;
    let prev = call(fx, 0);
    for (let t = 0.02; t <= 40; t += 0.02) {
      const cur = call(fx, t);
      if (cur <= 0 && prev > 0) {
        let lo = t - 0.02, hi = t;
        for (let k = 0; k < 44; k++) { const m = (lo + hi) / 2; if (call(fx, m) > 0) lo = m; else hi = m; }
        return Math.max(hi, 0.1);
      }
      prev = cur;
    }
    return baseWindow;
  });

  const apexT = $derived.by(() => {
    let lo = 0, hi = tmax;
    if (call(fv, lo) * call(fv, hi) > 0) return null;
    for (let k = 0; k < 44; k++) { const m = (lo + hi) / 2; if (call(fv, lo) * call(fv, m) <= 0) hi = m; else lo = m; }
    return (lo + hi) / 2;
  });
  // the apex marker / area-to-apex shading only make sense for a projectile (one turning point)
  const showApex = $derived(windowMode === "landing" && apexT != null);

  const N = 140;
  const samples = $derived.by(() => {
    const ts = [], xs = [], vs = [], as = [];
    for (let i = 0; i <= N; i++) {
      const t = (i / N) * tmax;
      ts.push(t); xs.push(call(fx, t)); vs.push(call(fv, t)); as.push(call(fa, t));
    }
    return { ts, xs, vs, as };
  });

  // geometry
  const W = 560, PADL = 52, PADR = 16, H = 132, GAP = 16, TOP = 8;
  const innerW = W - PADL - PADR;
  const px = (t) => PADL + (t / tmax) * innerW;

  function band(i) { return TOP + i * (H + GAP); }
  function rangeOf(arr) {
    let lo = Math.min(...arr, 0), hi = Math.max(...arr, 0);
    if (hi - lo < 1e-9) { hi += 1; lo -= 1; }
    const pad = (hi - lo) * 0.12; return [lo - pad, hi + pad];
  }
  function py(val, [lo, hi], i) { return band(i) + H - ((val - lo) / (hi - lo)) * H; }
  function poly(arr, rng, i) { return samples.ts.map((t, k) => `${px(t).toFixed(1)},${py(arr[k], rng, i).toFixed(1)}`).join(" "); }

  const rx = $derived(rangeOf(samples.xs));
  const rv = $derived(rangeOf(samples.vs));
  const ra = $derived(rangeOf(samples.as));

  // area-under-v polygon (0 -> apex), to the v=0 axis
  const areaPoly = $derived.by(() => {
    if (apexT == null) return "";
    const pts = [];
    for (let i = 0; i <= N; i++) {
      const t = (i / N) * apexT;
      pts.push(`${px(t).toFixed(1)},${py(call(fv, t), rv, 1).toFixed(1)}`);
    }
    pts.push(`${px(apexT).toFixed(1)},${py(0, rv, 1).toFixed(1)}`);
    pts.push(`${px(0).toFixed(1)},${py(0, rv, 1).toFixed(1)}`);
    return pts.join(" ");
  });

  const panels = [
    { i: 0, label: "x  (m)", rng: () => rx, arr: () => samples.xs, key: "x" },
    { i: 1, label: "v  (m/s)", rng: () => rv, arr: () => samples.vs, key: "v" },
    { i: 2, label: "a  (m/s²)", rng: () => ra, arr: () => samples.as, key: "a" },
  ];
  const apexX = $derived(apexT == null ? null : call(fx, apexT));
  const fmt = (n) => (Math.abs(n) >= 100 ? n.toFixed(0) : n.toFixed(1));
</script>

<div class="graphstack">
  <svg viewBox={`0 0 ${W} ${TOP + 3 * H + 2 * GAP + 24}`} role="img"
       aria-label="Stacked position, velocity, and acceleration versus time">
    {#each panels as p}
      {@const rng = p.rng()}
      {@const zeroY = py(0, rng, p.i)}
      <!-- panel frame -->
      <rect x={PADL} y={band(p.i)} width={innerW} height={H} class="frame" />
      <text x="6" y={band(p.i) + 14} class="axlabel">{p.label}</text>
      <!-- zero axis -->
      <line x1={PADL} y1={zeroY} x2={W - PADR} y2={zeroY} class="zero" />
      <!-- apex guide across all panels (projectile only) -->
      {#if showApex}
        <line x1={px(apexT)} y1={band(p.i)} x2={px(apexT)} y2={band(p.i) + H} class="apexline" />
      {/if}
      <!-- area under v to the apex (projectile only) -->
      {#if showApex && p.key === "v" && areaPoly}
        <polygon points={areaPoly} class="area" />
      {/if}
      <!-- the curve -->
      <polyline points={poly(p.arr(), rng, p.i)} class={`curve ${p.key}`} />
      <!-- apex marker on x and v -->
      {#if showApex && p.key === "x"}
        <circle cx={px(apexT)} cy={py(apexX, rng, p.i)} r="4" class="mark" />
      {/if}
      {#if showApex && p.key === "v"}
        <circle cx={px(apexT)} cy={py(0, rng, p.i)} r="4" class="mark" />
      {/if}
    {/each}
    <!-- time axis -->
    <text x={PADL} y={TOP + 3 * H + 2 * GAP + 18} class="axlabel">t = 0</text>
    <text x={W - PADR} y={TOP + 3 * H + 2 * GAP + 18} class="axlabel" text-anchor="end">t = {tmax.toFixed(2)} s</text>
  </svg>

  <div class="annot">
    {#if showApex}
      <p><strong>Apex</strong> at t = {apexT.toFixed(2)} s, x = {apexX.toFixed(2)} m: on v–t the line crosses
        zero but its <em>slope never changes</em> — that slope is a, and a is never zero. The shaded area
        under v from 0 to the apex is exactly the rise in x.</p>
    {:else}
      <p>The three panels share a time axis: the <strong>slope</strong> of each graph is the value of the one
        below it, and the <strong>area</strong> under each is the change in the one above. Drag the sliders and
        watch them move together.</p>
    {/if}
  </div>

  {#if interactive}
    <div class="sliders">
      {#each Object.entries(paramDefs) as [name, def]}
        <label>
          <span class="pname">{name} = {fmt(vals[name])}</span>
          <input type="range" min={def.min} max={def.max} step={(def.max - def.min) / 100}
                 bind:value={vals[name]} />
        </label>
      {/each}
      <p class="hint faint">Drag v₀ and watch the parabola rise, the v–t line steepen, and the apex slide —
        max height grows with v₀².</p>
    </div>
  {:else if graph.svg}
    <p class="faint">A static figure is also available.</p>
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
  .sliders { display: grid; gap: 0.5rem; padding-top: 0.3rem; }
  .sliders label { display: grid; grid-template-columns: 8rem 1fr; align-items: center; gap: 0.8rem; }
  .pname { font-family: var(--font-mono); font-size: 0.85rem; }
  .sliders input[type="range"] { width: 100%; accent-color: var(--accent); }
  .hint { grid-column: 1 / -1; font-size: 0.82rem; margin: 0.2rem 0 0; }
</style>
