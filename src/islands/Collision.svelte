<script>
  // The collision instrument (ADR-0018): a before/after two-state bar comparison. A 1D two-body collision
  // dialled by the coefficient of restitution e (the cursor, 0 = perfectly inelastic, 1 = perfectly elastic).
  // The producer ships the closed-form final velocities v1'(e, m1), v2'(e, m1) (parity-verified like the
  // area/energy instruments); the island forms the momentum and kinetic-energy bars from them. The momentum
  // total bar is the SAME height before and after at every e (equal-and-opposite impulses cancel); the
  // kinetic-energy total bar equals the before value only at e = 1 and shrinks as e → 0 — the lost KE is the
  // lesson.
  let { graph } = $props();

  const paramDefs = graph.params ?? {};
  const cursor = graph.cursor;                       // the restitution cursor e (canonical name "u")
  const C = graph.consts ?? {};                      // { m2, v1, v2 } — the fixed target + initial velocities
  const massName = Object.keys(paramDefs)[0];        // the incident-mass slider m1

  const compile = (expr, params) => new Function(...params, `"use strict"; return (${expr});`);
  const fns = {
    v1f: compile(graph.closed_form.v1f, graph.closed_form_params),
    v2f: compile(graph.closed_form.v2f, graph.closed_form_params),
  };

  let vals = $state(Object.fromEntries(Object.entries(paramDefs).map(([k, p]) => [k, p.default])));
  let ec = $state(cursor.default);

  const call = (fn, ee) => fn(...graph.closed_form_params.map((p) => (p === cursor.name ? ee : vals[p])));

  // masses + initial velocities
  const m1 = $derived(vals[massName]);
  const m2 = C.m2, v1 = C.v1, v2 = C.v2;
  // finals at the current restitution
  const v1a = $derived(call(fns.v1f, ec));
  const v2a = $derived(call(fns.v2f, ec));

  // momentum (signed) and kinetic energy, per body, before and after
  const p1b = $derived(m1 * v1), p2b = $derived(m2 * v2);
  const p1a = $derived(m1 * v1a), p2a = $derived(m2 * v2a);
  const k1b = $derived(0.5 * m1 * v1 * v1), k2b = $derived(0.5 * m2 * v2 * v2);
  const k1a = $derived(0.5 * m1 * v1a * v1a), k2a = $derived(0.5 * m2 * v2a * v2a);
  const pTotB = $derived(p1b + p2b), pTotA = $derived(p1a + p2a);
  const kTotB = $derived(k1b + k2b), kTotA = $derived(k1a + k2a);
  const kLost = $derived(Math.max(0, kTotB - kTotA));
  const lostPct = $derived(kTotB > 1e-9 ? (100 * kLost) / kTotB : 0);

  // geometry
  const W = 520, H = 348;
  const fmt = (n) => (Math.abs(n) >= 100 ? n.toFixed(0) : Math.abs(n) >= 10 ? n.toFixed(1) : n.toFixed(2));

  // --- schematic: two lanes (before / after), each with the two blocks + velocity arrows ---
  const blockW = (mass) => 20 + 9 * mass;                 // box width grows with mass
  const SPD = 9;                                          // px per (m/s) for the arrow length
  const arrow = (v) => Math.sign(v) * Math.min(46, Math.abs(v) * SPD);

  // --- bars ---
  const BASE = H - 30, TOP = 150;                         // bar band vertical extent
  const barPx = (v, ceil) => (ceil > 1e-9 ? (v / ceil) * (BASE - TOP) : 0);
  const pCeil = $derived(Math.max(pTotB, pTotA, 1e-9));
  const kCeil = $derived(Math.max(kTotB, kTotA, 1e-9));
</script>

<div class="collision">
  <svg viewBox={`0 0 ${W} ${H}`} role="img"
       aria-label="Collision bars: total momentum is the same before and after; total kinetic energy is conserved only when the collision is elastic">
    <!-- ===================== schematic: before / after lanes ===================== -->
    {#each [{ y: 38, lbl: "before", a: v1, b: v2 }, { y: 100, lbl: "after", a: v1a, b: v2a }] as lane}
      <text x="14" y={lane.y + 4} class="lane">{lane.lbl}</text>
      <line x1="70" y1={lane.y + 16} x2="320" y2={lane.y + 16} class="ground" />
      <!-- block 1 -->
      {@const w1 = blockW(m1)}
      <rect x={150 - w1} y={lane.y} width={w1} height="16" rx="2" class="b1" />
      <text x={150 - w1 / 2} y={lane.y + 12} class="bl">m₁</text>
      {#if Math.abs(lane.a) > 1e-6}
        <line x1={150} y1={lane.y - 6} x2={150 + arrow(lane.a)} y2={lane.y - 6} class="arr b1s" marker-end="url(#ah1)" />
      {/if}
      <text x={150 + (Math.abs(lane.a) > 1e-6 ? arrow(lane.a) + 6 : 8)} y={lane.y - 2} class="vlab b1s">{fmt(lane.a)}</text>
      <!-- block 2 -->
      {@const w2 = blockW(m2)}
      <rect x={250} y={lane.y} width={w2} height="16" rx="2" class="b2" />
      <text x={250 + w2 / 2} y={lane.y + 12} class="bl light">m₂</text>
      {#if Math.abs(lane.b) > 1e-6}
        <line x1={250 + w2} y1={lane.y - 6} x2={250 + w2 + arrow(lane.b)} y2={lane.y - 6} class="arr b2s" marker-end="url(#ah2)" />
      {/if}
      <text x={250 + w2 + (Math.abs(lane.b) > 1e-6 ? arrow(lane.b) + 6 : 8)} y={lane.y - 2} class="vlab b2s">{fmt(lane.b)}</text>
    {/each}
    <defs>
      <marker id="ah1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" class="b1fill" /></marker>
      <marker id="ah2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" class="b2fill" /></marker>
    </defs>

    <!-- divider -->
    <line x1="14" y1="134" x2={W - 14} y2="134" class="rule" />

    <!-- ===================== bars: momentum (left) · kinetic energy (right) ===================== -->
    <!-- MOMENTUM -->
    <text x="120" y="150" class="title" text-anchor="middle">Momentum  (kg·m/s)</text>
    <line x1="40" y1={BASE - barPx(pTotB, pCeil)} x2="210" y2={BASE - barPx(pTotB, pCeil)} class="conserved" />
    <text x="210" y={BASE - barPx(pTotB, pCeil) - 4} class="clab" text-anchor="end">conserved</text>
    {#each [{ x: 70, p1: p1b, p2: p2b, lbl: "before" }, { x: 150, p1: p1a, p2: p2a, lbl: "after" }] as col}
      <rect x={col.x} y={BASE - barPx(col.p1, pCeil)} width="48" height={Math.max(0, barPx(col.p1, pCeil))} class="seg b1" />
      <rect x={col.x} y={BASE - barPx(col.p1 + col.p2, pCeil)} width="48" height={Math.max(0, barPx(col.p2, pCeil))} class="seg b2" />
      <line x1={col.x} y1={BASE} x2={col.x + 48} y2={BASE} class="axis" />
      <text x={col.x + 24} y={BASE + 13} class="lbl" text-anchor="middle">{col.lbl}</text>
      <text x={col.x + 24} y={BASE - barPx(col.p1 + col.p2, pCeil) - 4} class="val" text-anchor="middle">{fmt(col.p1 + col.p2)}</text>
    {/each}

    <!-- KINETIC ENERGY -->
    <text x="390" y="150" class="title" text-anchor="middle">Kinetic energy  (J)</text>
    <line x1="310" y1={BASE - barPx(kTotB, kCeil)} x2="500" y2={BASE - barPx(kTotB, kCeil)} class="ceiling" />
    {#each [{ x: 340, k1: k1b, k2: k2b, lbl: "before" }, { x: 420, k1: k1a, k2: k2a, lbl: "after" }] as col}
      <rect x={col.x} y={BASE - barPx(col.k1, kCeil)} width="48" height={Math.max(0, barPx(col.k1, kCeil))} class="seg b1" />
      <rect x={col.x} y={BASE - barPx(col.k1 + col.k2, kCeil)} width="48" height={Math.max(0, barPx(col.k2, kCeil))} class="seg b2" />
      <line x1={col.x} y1={BASE} x2={col.x + 48} y2={BASE} class="axis" />
      <text x={col.x + 24} y={BASE + 13} class="lbl" text-anchor="middle">{col.lbl}</text>
      <text x={col.x + 24} y={BASE - barPx(col.k1 + col.k2, kCeil) - 4} class="val" text-anchor="middle">{fmt(col.k1 + col.k2)}</text>
    {/each}
    <!-- the lost-energy region atop the "after" KE bar -->
    {#if kLost > 1e-6}
      <rect x="420" y={BASE - barPx(kTotB, kCeil)} width="48" height={Math.max(0, barPx(kLost, kCeil))} class="lost" />
      <text x="444" y={BASE - barPx(kTotA + kLost / 2, kCeil) + 3} class="lostlab" text-anchor="middle">lost</text>
    {/if}
  </svg>

  <div class="annot">
    <p>Restitution <strong>e = {fmt(ec)}</strong>
      ({ec > 0.98 ? "perfectly elastic" : ec < 0.02 ? "perfectly inelastic" : "partially elastic"}):
      body 1 ends at <strong class="b1s">{fmt(v1a)} m/s</strong>, body 2 at
      <strong class="b2s">{fmt(v2a)} m/s</strong>. Total momentum
      <strong>{fmt(pTotB)} → {fmt(pTotA)} kg·m/s</strong> — <em>unchanged</em>. Kinetic energy
      <strong>{fmt(kTotB)} → {fmt(kTotA)} J</strong>, with <strong>{fmt(kLost)} J ({fmt(lostPct)}%)</strong>
      lost to deformation. Drag <em>e</em> down to 0: momentum holds, the energy bar collapses.</p>
  </div>

  <div class="sliders">
    <label>
      <span class="pname">e = {fmt(ec)}</span>
      <input type="range" min={cursor.min} max={cursor.max} step={(cursor.max - cursor.min) / 200} bind:value={ec} />
    </label>
    {#each Object.entries(paramDefs) as [name, def]}
      <label>
        <span class="pname">{name} = {fmt(vals[name])} kg</span>
        <input type="range" min={def.min} max={def.max} step={(def.max - def.min) / 100} bind:value={vals[name]} />
      </label>
    {/each}
    <p class="hint faint">Slide <em>e</em> from 1 (elastic — kinetic energy conserved) to 0 (perfectly
      inelastic — the blocks stick and move together). The momentum total never moves; the kinetic-energy
      total is the only one that changes. (Raising m₁ changes how the velocities split.)</p>
  </div>
</div>

<style>
  .collision { display: grid; gap: 0.5rem; }
  svg { width: 100%; height: auto; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); }
  .lane { fill: var(--ink-faint); font-size: 11px; font-family: var(--font-mono); text-transform: uppercase; letter-spacing: 0.04em; }
  .ground { stroke: color-mix(in srgb, var(--ink-faint) 50%, transparent); stroke-width: 1.2; }
  .b1 { fill: var(--accent); }
  .b2 { fill: var(--ink); }
  .b1fill { fill: var(--accent); }
  .b2fill { fill: var(--ink); }
  .bl { fill: var(--paper); font-size: 9.5px; font-family: var(--font-mono); text-anchor: middle; }
  .bl.light { fill: var(--paper); }
  .arr { stroke-width: 2.4; }
  .b1s { color: var(--accent); }
  .arr.b1s { stroke: var(--accent); }
  .arr.b2s { stroke: var(--ink); }
  .vlab { font-size: 10px; font-family: var(--font-mono); }
  .vlab.b1s { fill: var(--accent); }
  .vlab.b2s { fill: var(--ink); }
  .rule { stroke: var(--line); stroke-width: 1; }
  .title { fill: var(--ink-2); font-size: 11.5px; font-family: var(--font-mono); }
  .seg.b1 { fill: var(--accent); }
  .seg.b2 { fill: var(--ink); }
  .axis { stroke: var(--line); stroke-width: 1; }
  .conserved { stroke: var(--ink-faint); stroke-width: 1.4; stroke-dasharray: 5 3; }
  .ceiling { stroke: var(--ink-faint); stroke-width: 1; stroke-dasharray: 3 3; opacity: 0.7; }
  .lost { fill: color-mix(in srgb, var(--ink-faint) 24%, transparent); stroke: var(--ink-faint); stroke-width: 0.8; stroke-dasharray: 3 2; }
  .lostlab { fill: var(--ink-2); font-size: 10px; font-family: var(--font-mono); }
  .clab { fill: var(--ink-faint); font-size: 10px; font-family: var(--font-mono); }
  .lbl { fill: var(--ink-faint); font-size: 11px; font-family: var(--font-mono); }
  .val { fill: var(--ink-2); font-size: 11px; font-family: var(--font-mono); }
  .annot p { font-size: 0.92rem; color: var(--ink-2); margin: 0.3rem 0; line-height: 1.5; }
  .annot .b1s { color: var(--accent); }
  .annot .b2s { color: var(--ink); }
  .sliders { display: grid; gap: 0.4rem; padding-top: 0.3rem; }
  .sliders label { display: grid; grid-template-columns: 9rem 1fr; align-items: center; gap: 0.8rem; }
  .pname { font-family: var(--font-mono); font-size: 0.85rem; }
  .sliders input[type="range"] { width: 100%; accent-color: var(--accent); }
  .hint { font-size: 0.82rem; margin: 0.2rem 0 0; }
</style>
