<script>
  // The trajectory instrument (ADR-0015): 2D projectile motion as the path y vs x. The horizontal and
  // vertical motions are independent 1D motions superposed; the path is their parametric trace. Drag-free is
  // a closed-form parabola (sliders for launch angle and speed, evaluated in JS, parity-verified); the
  // quadratic-drag case ships numerically-integrated frames the slider snaps between. No SymPy here.
  let { graph } = $props();

  const sampled = graph.mode === "sampled";
  const frames = graph.frames ?? [];
  const sweep = graph.sweep ?? null;
  const reference = graph.reference ?? null;
  const paramDefs = graph.params ?? {};
  const G = Math.abs(graph.g ?? -10);

  const compile = (expr, params) => new Function(...params, `"use strict"; return (${expr});`);
  const fns = $derived(sampled ? null : {
    x: compile(graph.closed_form.x, graph.closed_form_params),
    y: compile(graph.closed_form.y, graph.closed_form_params),
  });

  let vals = $state(Object.fromEntries(Object.entries(paramDefs).map(([k, p]) => [k, p.default])));
  let frameIdx = $state(sampled ? Math.max(0, Math.floor(frames.length / 2)) : 0);

  const call = (fn, tt) => fn(...graph.closed_form_params.map((p) => (p === "t" ? tt : vals[p])));

  // flight time: the closed-form path returns to y=0; find the positive root by scan + bisection.
  const tFlightCF = $derived.by(() => {
    if (sampled) return 0;
    let prev = call(fns.y, 0.0001);
    for (let t = 0.05; t <= 60; t += 0.05) {
      const cur = call(fns.y, t);
      if (cur <= 0 && prev > 0) {
        let lo = t - 0.05, hi = t;
        for (let k = 0; k < 40; k++) { const m = (lo + hi) / 2; if (call(fns.y, m) > 0) lo = m; else hi = m; }
        return hi;
      }
      prev = cur;
    }
    return graph.series?.t_max ?? 4;
  });

  const N = 160;
  // the current path as world-space points
  const path = $derived.by(() => {
    if (sampled) {
      const fr = frames[frameIdx];
      return { x: fr.series.x, y: fr.series.y };
    }
    const xs = [], ys = [];
    for (let i = 0; i <= N; i++) { const t = (i / N) * tFlightCF; xs.push(call(fns.x, t)); ys.push(call(fns.y, t)); }
    return { x: xs, y: ys };
  });
  const refPath = $derived(reference ? { x: reference.x, y: reference.y } : null);

  // derived readouts (closed-form case): range, apex, current speed components
  const theta = $derived(vals.theta);
  const v0 = $derived(vals.v0);
  const rangeR = $derived(sampled ? Math.max(...path.x) : call(fns.x, tFlightCF));
  const apexT = $derived(sampled ? 0 : tFlightCF / 2);
  const apexX = $derived(sampled ? path.x[path.y.indexOf(Math.max(...path.y))] : call(fns.x, apexT));
  const apexY = $derived(sampled ? Math.max(...path.y) : call(fns.y, apexT));

  // world extents: drag-free uses a v0-stable frame (max range = v0²/g at 45°) so range visibly peaks at 45°;
  // sampled uses the frame's own extent.
  const worldXmax = $derived(sampled ? Math.max(...path.x, ...(refPath?.x ?? [0])) * 1.06 : ((v0 * v0) / G) * 1.06);
  const worldYmax = $derived(sampled ? Math.max(...path.y, ...(refPath?.y ?? [0])) * 1.18 : ((v0 * v0) / (2 * G)) * 1.18);

  // geometry
  const W = 600, PADL = 50, PADR = 18, H = 300, TOP = 12;
  const innerW = W - PADL - PADR;
  const px = (x) => PADL + (x / worldXmax) * innerW;
  const py = (y) => TOP + H - (y / worldYmax) * H;
  const poly = (p) => p.x.map((x, k) => `${px(x).toFixed(1)},${py(p.y[k]).toFixed(1)}`).join(" ");

  const fmt = (n) => (Math.abs(n) >= 100 ? n.toFixed(0) : Math.abs(n) >= 10 ? n.toFixed(1) : n.toFixed(2));
</script>

<div class="trajectory">
  <svg viewBox={`0 0 ${W} ${TOP + H + 30}`} role="img" aria-label="Projectile path, height versus horizontal distance">
    <rect x={PADL} y={TOP} width={innerW} height={H} class="frame" />
    <text x="6" y={TOP + 12} class="axlabel">{graph.y_label}</text>
    <line x1={PADL} y1={py(0)} x2={W - PADR} y2={py(0)} class="ground" />

    {#if refPath}
      <polyline points={poly(refPath)} class="refpath" />
    {/if}
    <polyline points={poly(path)} class="path" />

    <!-- launch / apex / landing markers -->
    <circle cx={px(0)} cy={py(0)} r="4" class="mark launch" />
    {#if apexY > 0.01}
      <line x1={px(apexX)} y1={py(0)} x2={px(apexX)} y2={py(apexY)} class="drop" />
      <circle cx={px(apexX)} cy={py(apexY)} r="4" class="mark" />
      <text x={px(apexX)} y={py(apexY) - 8} class="lbl" text-anchor="middle">apex {fmt(apexY)} m</text>
    {/if}
    <circle cx={px(rangeR)} cy={py(0)} r="4" class="mark" />
    <text x={px(rangeR)} y={py(0) + 16} class="lbl" text-anchor="middle">range {fmt(rangeR)} m</text>

    <text x={W - PADR} y={TOP + H + 24} class="axlabel" text-anchor="end">{graph.x_label}</text>
  </svg>

  {#if sampled}
    <div class="sliders">
      <label>
        <span class="pname">{sweep?.label} = {fmt(frames[frameIdx].value)}{sweep?.unit ? " " + sweep.unit : ""}</span>
        <input type="range" min="0" max={frames.length - 1} step="1" bind:value={frameIdx} />
      </label>
      <p class="framelabel">{frames[frameIdx].label}</p>
      <p class="hint faint">Each stop is a numerically-integrated trajectory (no closed form exists for
        quadratic drag); the dashed curve is the drag-free parabola for comparison.</p>
    </div>
  {:else}
    <div class="annot">
      <p>At <strong>θ = {fmt(theta)}°</strong>, <strong>v₀ = {fmt(v0)} m/s</strong>: range
        <strong class="hl">{fmt(rangeR)} m</strong>, max height <strong>{fmt(apexY)} m</strong>. The horizontal
        speed v₀cosθ = <strong>{fmt(v0 * Math.cos((theta * Math.PI) / 180))} m/s</strong> never changes — even at
        the apex. Range is largest at <strong>45°</strong>, and complementary angles (e.g. 30° and 60°) give the
        same range.</p>
    </div>
    <div class="sliders">
      {#each Object.entries(paramDefs) as [name, def]}
        <label>
          <span class="pname">{name === "theta" ? "θ" : name} = {fmt(vals[name])}{name === "theta" ? "°" : ""}</span>
          <input type="range" min={def.min} max={def.max} step={(def.max - def.min) / 140} bind:value={vals[name]} />
        </label>
      {/each}
      <p class="hint faint">Drag the launch angle and speed: the parabola, the apex, and the range move
        together. Sweep θ through 45° to see the range peak.</p>
    </div>
  {/if}
</div>

<style>
  .trajectory { display: grid; gap: 0.5rem; }
  svg { width: 100%; height: auto; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); }
  .frame { fill: none; stroke: var(--line); stroke-width: 1; }
  .ground { stroke: color-mix(in srgb, var(--ink-faint) 60%, transparent); stroke-width: 1; }
  .path { fill: none; stroke: var(--accent); stroke-width: 2.4; }
  .refpath { fill: none; stroke: var(--ink-faint); stroke-width: 1.6; stroke-dasharray: 4 3; opacity: 0.8; }
  .drop { stroke: var(--ink-faint); stroke-width: 1; stroke-dasharray: 3 3; opacity: 0.7; }
  .mark { fill: var(--accent); }
  .mark.launch { fill: var(--ink); }
  .lbl { fill: var(--ink-2); font-size: 11px; font-family: var(--font-mono); }
  .axlabel { fill: var(--ink-faint); font-size: 11px; font-family: var(--font-mono); }
  .annot p { font-size: 0.92rem; color: var(--ink-2); margin: 0.3rem 0; line-height: 1.5; }
  .annot .hl { color: var(--accent); }
  .sliders { display: grid; gap: 0.4rem; padding-top: 0.3rem; }
  .sliders label { display: grid; grid-template-columns: 8rem 1fr; align-items: center; gap: 0.8rem; }
  .pname { font-family: var(--font-mono); font-size: 0.85rem; }
  .sliders input[type="range"] { width: 100%; accent-color: var(--accent); }
  .framelabel { margin: 0.1rem 0; font-weight: 600; }
  .hint { font-size: 0.82rem; margin: 0.2rem 0 0; }
</style>
