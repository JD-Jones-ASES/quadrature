<script>
  // The energy-exchange instrument: as a system moves (cursor u — a height/position), the kinetic and
  // potential energies trade while their sum stays flat. KE(u), PE(u) are JS-cheap closed forms, parity-
  // verified like the area instrument; the Total bar staying constant IS the visual proof of conservation.
  let { graph } = $props();

  const paramDefs = graph.params ?? {};
  const cursor = graph.cursor;
  const u0 = graph.u0 ?? 0;
  const uMax = graph.cursor.max;

  const compile = (expr, params) => new Function(...params, `"use strict"; return (${expr});`);
  const fns = {
    ke: compile(graph.closed_form.ke, graph.closed_form_params),
    pe: compile(graph.closed_form.pe, graph.closed_form_params),
  };

  let vals = $state(Object.fromEntries(Object.entries(paramDefs).map(([k, p]) => [k, p.default])));
  let uc = $state(cursor.default);

  const call = (fn, uu) => fn(...graph.closed_form_params.map((p) => (p === cursor.name ? uu : vals[p])));

  const ke = $derived(Math.max(0, call(fns.ke, uc)));
  const pe = $derived(Math.max(0, call(fns.pe, uc)));
  const total = $derived(ke + pe);
  // the conserved ceiling: total is constant in u, so sample it at the top of the cursor range
  const ceiling = $derived(Math.max(call(fns.ke, u0) + call(fns.pe, u0), call(fns.ke, uMax) + call(fns.pe, uMax), 1e-9));
  // speed from the kinetic energy (½ m v² = KE); m is the slider if present
  const mass = $derived(vals[Object.keys(paramDefs)[0]] ?? graph.mass ?? 1);
  const speed = $derived(Math.sqrt(2 * ke / mass));

  // geometry
  const W = 460, H = 260, PAD = 26, BASE = H - 30, TOP = 18;
  const barH = (v) => (v / ceiling) * (BASE - TOP);
  const py = (v) => BASE - barH(v);
  // height-indicator track on the left; bars on the right
  const TX = PAD, TW = 70;                       // height track
  const trackTop = TOP, trackBot = BASE;
  const ballY = $derived(trackBot - ((uc - u0) / (uMax - u0)) * (trackBot - trackTop));
  const bars = $derived([
    { x: 170, label: graph.ke_label, val: ke, cls: "ke" },
    { x: 260, label: graph.pe_label, val: pe, cls: "pe" },
    { x: 350, label: graph.total_label, val: total, cls: "total" },
  ]);
  const BW = 56;
  const lab = (s) => (s || "").split("(")[0].trim();
  const fmt = (n) => (Math.abs(n) >= 100 ? n.toFixed(0) : Math.abs(n) >= 10 ? n.toFixed(1) : n.toFixed(2));
</script>

<div class="energy">
  <svg viewBox={`0 0 ${W} ${H}`} role="img"
       aria-label="Energy bars: kinetic and potential energy trade as the object moves, with the total constant">
    <!-- height indicator: a vertical track with the object descending as the cursor falls -->
    <line x1={TX + TW / 2} y1={trackTop} x2={TX + TW / 2} y2={trackBot} class="track" />
    <line x1={TX} y1={trackBot} x2={TX + TW} y2={trackBot} class="ground" />
    <line x1={TX + TW / 2} y1={ballY} x2={170} y2={ballY} class="link" />
    <circle cx={TX + TW / 2} cy={ballY} r="7" class="ball" />
    <text x={TX + TW / 2} y={trackTop - 6} class="lbl" text-anchor="middle">{lab(graph.u_label)}</text>
    <text x={TX + TW / 2} y={trackBot + 14} class="lbl" text-anchor="middle">bottom</text>

    <!-- the conserved-total ceiling line across the bars -->
    <line x1={150} y1={py(ceiling)} x2={W - PAD} y2={py(ceiling)} class="ceiling" />
    <text x={W - PAD} y={py(ceiling) - 4} class="lbl" text-anchor="end">conserved total</text>

    <!-- KE, PE, Total bars -->
    {#each bars as b}
      <rect x={b.x} y={py(b.val)} width={BW} height={Math.max(0, barH(b.val))} class={`bar ${b.cls}`} />
      <line x1={b.x} y1={BASE} x2={b.x + BW} y2={BASE} class="axis" />
      <text x={b.x + BW / 2} y={BASE + 14} class="lbl" text-anchor="middle">{lab(b.label)}</text>
      <text x={b.x + BW / 2} y={py(b.val) - 5} class="val" text-anchor="middle">{fmt(b.val)}</text>
    {/each}
  </svg>

  <div class="annot">
    <p>At <strong>{lab(graph.u_label)} = {fmt(uc)} {cursor.unit ?? ""}</strong>: kinetic energy
      <strong class="ke">{fmt(ke)} J</strong>, potential energy <strong class="pe">{fmt(pe)} J</strong>, speed
      <strong>{fmt(speed)} m/s</strong>. Their sum is <strong>{fmt(total)} J</strong> — the
      <em>same at every height</em>. Drag the cursor: the KE and PE bars trade, but the Total never moves. The
      speed depends only on how far the object has dropped, not on the path it took.</p>
  </div>

  <div class="sliders">
    <label>
      <span class="pname">{lab(graph.u_label)} = {fmt(uc)} {cursor.unit ?? ""}</span>
      <input type="range" min={cursor.min} max={cursor.max} step={(cursor.max - cursor.min) / 200} bind:value={uc} />
    </label>
    {#each Object.entries(paramDefs) as [name, def]}
      <label>
        <span class="pname">{name} = {fmt(vals[name])}</span>
        <input type="range" min={def.min} max={def.max} step={(def.max - def.min) / 100} bind:value={vals[name]} />
      </label>
    {/each}
    <p class="hint faint">Drag the height: potential energy converts to kinetic and back, but the total bar is
      fixed — energy is conserved. (Raising the mass scales all three bars together.)</p>
  </div>
</div>

<style>
  .energy { display: grid; gap: 0.5rem; }
  svg { width: 100%; height: auto; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); }
  .track { stroke: var(--line); stroke-width: 2; }
  .ground { stroke: color-mix(in srgb, var(--ink-faint) 60%, transparent); stroke-width: 1.5; }
  .link { stroke: var(--ink-faint); stroke-width: 1; stroke-dasharray: 3 3; opacity: 0.7; }
  .ball { fill: var(--accent); }
  .ceiling { stroke: var(--ink-faint); stroke-width: 1.4; stroke-dasharray: 5 3; opacity: 0.9; }
  .axis { stroke: var(--line); stroke-width: 1; }
  .bar.ke { fill: var(--accent); }
  .bar.pe { fill: var(--ink); }
  .bar.total { fill: color-mix(in srgb, var(--ink-faint) 35%, transparent); stroke: var(--ink-faint); stroke-width: 1; }
  .lbl { fill: var(--ink-faint); font-size: 11px; font-family: var(--font-mono); }
  .val { fill: var(--ink-2); font-size: 11px; font-family: var(--font-mono); }
  .annot p { font-size: 0.92rem; color: var(--ink-2); margin: 0.3rem 0; line-height: 1.5; }
  .annot .ke { color: var(--accent); }
  .annot .pe { color: var(--ink); }
  .sliders { display: grid; gap: 0.4rem; padding-top: 0.3rem; }
  .sliders label { display: grid; grid-template-columns: 12rem 1fr; align-items: center; gap: 0.8rem; }
  .pname { font-family: var(--font-mono); font-size: 0.85rem; }
  .sliders input[type="range"] { width: 100%; accent-color: var(--accent); }
  .hint { font-size: 0.82rem; margin: 0.2rem 0 0; }
</style>
