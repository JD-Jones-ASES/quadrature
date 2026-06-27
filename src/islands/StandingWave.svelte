<script>
  // The standing-wave instrument (ADR-0023, the 6th): a SPATIAL plot of the n-th harmonic shape y(x) on a
  // string fixed at both ends, driven by a discrete mode-number slider n. Unlike every other instrument (whose
  // axis is time or an integration variable), the axis here is position and the cursor is an integer mode. The
  // closed form y(u; n) = A·sin(nπu/L) is JS-cheap and parity-verified; nothing runs SymPy here. The nodes
  // (always-still points) stay pinned as n changes — the visual heart of "boundary conditions quantize."
  let { graph } = $props();

  const consts = graph.consts;           // { v, L, A, n_max }
  const L = consts.L, A = consts.A, v = consts.v;
  const uMax = graph.series?.u_max ?? L;
  const modes = graph.modes;             // [{ n, f, lam }]
  const nDef = graph.params.n.default;

  const compile = (expr, params) => new Function(...params, `"use strict"; return (${expr});`);
  const yFn = compile(graph.closed_form.y, graph.closed_form_params);
  const yAt = (uu, nn) => yFn(...graph.closed_form_params.map((p) => (p === "n" ? nn : uu)));

  let n = $state(nDef);
  const cur = $derived(modes.find((m) => m.n === n) ?? modes[0]);

  // geometry — one spatial panel
  const W = 560, PADL = 26, PADR = 18, PADT = 18, PADB = 16, H = 230;
  const innerW = W - PADL - PADR;
  const midY = PADT + (H - PADT - PADB) / 2;
  const amp = (H - PADT - PADB) / 2 * 0.92;
  const px = (u) => PADL + (u / uMax) * innerW;
  const py = (y) => midY - (y / A) * amp;

  const NS = 200;
  const shape = $derived.by(() => {
    const top = [], bot = [];
    for (let i = 0; i <= NS; i++) {
      const u = (i / NS) * uMax;
      const y = yAt(u, n);
      top.push(`${px(u).toFixed(1)},${py(y).toFixed(1)}`);
      bot.push(`${px(u).toFixed(1)},${py(-y).toFixed(1)}`);
    }
    return { top: top.join(" "), bot: bot.join(" ") };
  });

  // nodes at x = jL/n (j = 0..n); antinodes at the half-steps between them
  const nodes = $derived(Array.from({ length: n + 1 }, (_, j) => (j * L) / n));
  const antinodes = $derived(Array.from({ length: n }, (_, j) => ((j + 0.5) * L) / n));
  const fmt = (x) => (Math.abs(x) >= 100 ? x.toFixed(0) : Math.abs(x) >= 1 ? x.toFixed(2) : x.toFixed(3));
</script>

<div class="standing">
  <svg viewBox={`0 0 ${W} ${H}`} role="img"
       aria-label={`Standing wave, harmonic n = ${n}, with ${n - 1} interior nodes`}>
    <rect x={PADL} y={PADT} width={innerW} height={H - PADT - PADB} class="frame" />
    <!-- the oscillation envelope: the shape and its mirror are the two extremes -->
    <polyline points={shape.bot} class="mirror" />
    <line x1={PADL} y1={py(0)} x2={W - PADR} y2={py(0)} class="zero" />
    <polyline points={shape.top} class="wave" />
    <!-- antinodes (max sway) -->
    {#each antinodes as xa}
      <line x1={px(xa)} y1={py(A)} x2={px(xa)} y2={py(-A)} class="antinode" />
    {/each}
    <!-- the two fixed walls -->
    <line x1={px(0)} y1={py(A) - 6} x2={px(0)} y2={py(-A) + 6} class="wall" />
    <line x1={px(uMax)} y1={py(A) - 6} x2={px(uMax)} y2={py(-A) + 6} class="wall" />
    <!-- nodes: always-still points -->
    {#each nodes as xn}
      <circle cx={px(xn)} cy={py(0)} r="4.5" class="node" />
    {/each}
  </svg>

  <div class="readout">
    <p>
      Harmonic <strong class="acc">n = {n}</strong>: {n} half-wavelength{n === 1 ? "" : "s"} fit the string,
      with <strong>{n - 1}</strong> interior node{n - 1 === 1 ? "" : "s"} (dots) that never move.
      Frequency <strong class="acc">f<sub>{n}</sub> = {fmt(cur.f)} Hz</strong> = {n} × the fundamental;
      wavelength <strong>λ<sub>{n}</sub> = {fmt(cur.lam)} m</strong> = 2L/{n}.
    </p>
  </div>

  <div class="sliders">
    <label>
      <span class="pname">mode n = {n}</span>
      <input type="range" min={graph.params.n.min} max={graph.params.n.max} step="1" bind:value={n} />
    </label>
    <div class="harmonics">
      {#each modes as m}
        <button class="chip" class:on={m.n === n} onclick={() => (n = m.n)}>
          n{m.n} · {fmt(m.f)} Hz
        </button>
      {/each}
    </div>
    <p class="hint faint">The frequencies are exact integer multiples of the fundamental f₁ = v/2L = {fmt(modes[0].f)} Hz —
      a string fixed at both ends rings only at these harmonics, because the pinned ends force a node at each wall.</p>
  </div>
</div>

<style>
  .standing { display: grid; gap: 0.5rem; }
  svg { width: 100%; height: auto; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); }
  .frame { fill: none; stroke: var(--line); stroke-width: 1; }
  .zero { stroke: color-mix(in srgb, var(--ink-faint) 55%, transparent); stroke-width: 1; }
  .wave { fill: none; stroke: var(--accent); stroke-width: 2.4; }
  .mirror { fill: none; stroke: var(--accent); stroke-width: 1; stroke-dasharray: 3 3; opacity: 0.45; }
  .antinode { stroke: color-mix(in srgb, var(--accent) 30%, transparent); stroke-width: 1; stroke-dasharray: 2 3; }
  .wall { stroke: var(--ink-faint); stroke-width: 3; stroke-linecap: round; }
  .node { fill: var(--ink); stroke: var(--paper); stroke-width: 1.5; }
  .readout p { font-size: 0.92rem; color: var(--ink-2); margin: 0.2rem 0; line-height: 1.5; }
  .readout .acc { color: var(--accent); }
  .sliders { display: grid; gap: 0.5rem; padding-top: 0.2rem; }
  .sliders label { display: grid; grid-template-columns: 8rem 1fr; align-items: center; gap: 0.8rem; }
  .pname { font-family: var(--font-mono); font-size: 0.85rem; }
  .sliders input[type="range"] { width: 100%; accent-color: var(--accent); }
  .harmonics { display: flex; flex-wrap: wrap; gap: 0.35rem; }
  .chip {
    font: inherit; font-size: 0.8rem; font-family: var(--font-mono); cursor: pointer;
    background: var(--paper-2); border: 1px solid var(--line); border-radius: 999px; padding: 0.2rem 0.6rem; color: var(--ink-2);
  }
  .chip.on { border-color: var(--accent); color: var(--accent); font-weight: 600; }
  .hint { font-size: 0.82rem; margin: 0.2rem 0 0; }
</style>
