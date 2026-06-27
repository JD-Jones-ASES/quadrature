<script>
  // The formula concept graph — the navigational backbone (brief §8), ported from the Spengler
  // Portal's lexicon force-graph. Layout is frozen at build time (ADR-0008) and used as the initial
  // positions; nodes are then click-to-select AND drag-to-reposition (pointer events) after hydration.
  // Renders plain SVG, color-coded by domain, with typed edges (integral-of / derivative-of / …).
  let { graph, formulas } = $props();
  const byId = Object.fromEntries(formulas.map((f) => [f.id, f]));

  let selected = $state(null);

  const W = graph.layout.w, H = graph.layout.h;
  const domClass = (d) => `dom-${d}`;
  const radius = (n) => 16 + Math.min(10, n.degree * 2);
  const radiusById = Object.fromEntries(graph.nodes.map((n) => [n.id, radius(n)]));

  // live positions: start from the frozen layout (so SSR matches), then drag overrides them
  let positions = $state(Object.fromEntries(graph.nodes.map((n) => [n.id, { x: n.x, y: n.y }])));

  // --- drag (pointer events; threshold distinguishes a click from a drag so selection still works) ---
  let svgEl;
  let drag = $state(null); // { id, offX, offY, downX, downY, moved } — pointer-drag session state
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  function toSvg(evt) {
    if (!svgEl?.createSVGPoint || !svgEl.getScreenCTM) return null;
    const pt = svgEl.createSVGPoint();
    pt.x = evt.clientX; pt.y = evt.clientY;
    const ctm = svgEl.getScreenCTM();
    return ctm ? pt.matrixTransform(ctm.inverse()) : null;
  }
  function onDown(id, evt) {
    const p = toSvg(evt);
    if (!p) return;
    const cur = positions[id];
    drag = { id, offX: cur.x - p.x, offY: cur.y - p.y, downX: evt.clientX, downY: evt.clientY, moved: false };
    evt.currentTarget.setPointerCapture?.(evt.pointerId);
  }
  function onMove(evt) {
    if (!drag) return;
    const p = toSvg(evt);
    if (!p) return;
    if (Math.hypot(evt.clientX - drag.downX, evt.clientY - drag.downY) > 4) drag.moved = true;
    const r = radiusById[drag.id];
    positions = { ...positions, [drag.id]: { x: clamp(p.x + drag.offX, r, W - r), y: clamp(p.y + drag.offY, r, H - r) } };
  }
  function onUp(id) {
    if (drag && !drag.moved) selected = selected === id ? null : id;  // it was a click, not a drag
    drag = null;
  }
  function onKey(id, ev) {
    if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); selected = selected === id ? null : id; }
  }

  const neighbors = $derived.by(() => {
    if (!selected) return new Set();
    const set = new Set([selected]);
    for (const e of graph.edges) {
      if (e.source === selected) set.add(e.target);
      if (e.target === selected) set.add(e.source);
    }
    return set;
  });

  const FAMILY = {
    "integral-of": "calculus", "derivative-of": "calculus",
    "derived-from": "structure", "special-case-of": "structure",
    "assumes": "assumes", "related-to": "related",
  };
  const dimmed = (id) => selected && !neighbors.has(id);
  const edgeActive = (e) => !selected || (neighbors.has(e.source) && neighbors.has(e.target) && (e.source === selected || e.target === selected));

  const selectedEdges = $derived(selected ? graph.edges.filter((e) => e.source === selected) : []);
  const sel = $derived(selected ? byId[selected] : null);
</script>

<div class="cg">
  <div class="canvas">
    <svg bind:this={svgEl} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Formula concept graph (drag nodes to rearrange)">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" class="arrowhead" />
        </marker>
      </defs>
      {#each graph.edges as e}
        {@const a = positions[e.source]}
        {@const b = positions[e.target]}
        <line x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              class={`edge fam-${FAMILY[e.type]}`} class:active={edgeActive(e)} class:hide={selected && !edgeActive(e)}
              marker-end={e.type === "integral-of" || e.type === "derivative-of" ? "url(#arrow)" : null} />
      {/each}
      {#each graph.nodes as n}
        {@const p = positions[n.id]}
        <g class="node" class:dim={dimmed(n.id)} class:dragging={drag?.id === n.id}
           role="button" tabindex="0" aria-label={`${n.name} — click to select, drag to move`}
           onpointerdown={(ev) => onDown(n.id, ev)} onpointermove={onMove}
           onpointerup={() => onUp(n.id)} onkeydown={(ev) => onKey(n.id, ev)}>
          <circle cx={p.x} cy={p.y} r={radius(n)} class={domClass(n.domain)} class:sel={selected === n.id} />
          <text x={p.x} y={p.y + 5} text-anchor="middle" class="nlabel">{n.label}</text>
        </g>
      {/each}
    </svg>
  </div>

  <aside class="panel">
    {#if sel}
      <h3>{sel.name}</h3>
      <div class="math">{@html sel.latexHtml}</div>
      <p class="faint">Domain: {sel.domain} · regime {sel.regime} · units {sel.result_unit}
        {#if sel.verified}· <span class="vchk">✓ units{sel.verified.derivation ? " & derivation" : ""} machine-checked</span>{/if}</p>
      {#if selectedEdges.length}
        <h4>Relations</h4>
        <ul class="rels">
          {#each selectedEdges as e}
            <li><button class="rel" onclick={() => (selected = e.target)}>
              <span class={`reltype fam-${FAMILY[e.type]}`}>{e.type}</span> → {byId[e.target]?.name ?? e.target}
            </button>{#if e.gloss}<div class="gloss">{e.gloss}</div>{/if}</li>
          {/each}
        </ul>
      {/if}
      {#if sel.lessons?.length}
        <p class="faint">Used in: {sel.lessons.join(", ")}</p>
      {/if}
      <button class="clear" onclick={() => (selected = null)}>Clear selection</button>
    {:else}
      <p class="muted">Click a node to see the formula and its typed relations — or <strong>drag</strong> a
        node to rearrange the graph. Green arrows are the calculus spine: <em>x is the integral of v is the
        integral of a</em>; reverse them and you have the derivatives.</p>
      <ul class="legend">
        <li><span class="sw fam-calculus"></span> integral-of / derivative-of</li>
        <li><span class="sw fam-structure"></span> derived-from / special-case-of</li>
      </ul>
    {/if}
  </aside>
</div>

<style>
  .cg { display: grid; grid-template-columns: 1.4fr 1fr; gap: 1rem; align-items: start; }
  @media (max-width: 720px) { .cg { grid-template-columns: 1fr; } }
  .canvas svg { width: 100%; height: auto; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); }

  .edge { stroke: var(--ink-faint); stroke-width: 1.5; opacity: 0.55; }
  .edge.fam-calculus { stroke: var(--accent); }
  .edge.fam-structure { stroke: var(--accent-2); stroke-dasharray: 4 3; }
  .edge.hide { opacity: 0.08; }
  .edge.active { opacity: 1; stroke-width: 2.2; }
  .arrowhead { fill: var(--accent); }

  .node { cursor: grab; touch-action: none; }
  .node.dragging { cursor: grabbing; }
  .node.dragging circle { stroke: var(--ink); stroke-width: 3; }
  .node.dim { opacity: 0.3; }
  circle { stroke: var(--paper); stroke-width: 2; }
  circle.sel { stroke: var(--ink); stroke-width: 3; }
  .dom-mechanics { fill: var(--dom-mechanics); }
  .dom-em { fill: var(--dom-em); }
  .dom-thermo { fill: var(--dom-thermo); }
  .dom-waves-optics { fill: var(--dom-waves-optics); }
  .dom-modern { fill: var(--dom-modern); }
  .nlabel { fill: var(--paper); font-family: var(--font-mono); font-size: 14px; font-weight: 600; pointer-events: none; }

  .panel { background: var(--paper-2); border: 1px solid var(--line); border-radius: var(--radius); padding: 1rem 1.1rem; min-height: 12rem; }
  .panel h3 { margin: 0 0 0.3rem; }
  .panel h4 { margin: 0.9rem 0 0.3rem; font-size: 0.9rem; color: var(--ink-2); }
  .rels { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.5rem; }
  .rel { background: none; border: none; padding: 0; font: inherit; color: var(--ink); cursor: pointer; text-align: left; }
  .reltype { font-family: var(--font-mono); font-size: 0.78rem; padding: 0.1rem 0.4rem; border-radius: 6px; background: var(--accent-soft); color: var(--accent); }
  .reltype.fam-structure { background: color-mix(in srgb, var(--accent-2) 14%, transparent); color: var(--accent-2); }
  .gloss { color: var(--ink-faint); font-size: 0.85rem; margin-left: 0.3rem; }
  .vchk { color: var(--accent); }
  .clear { margin-top: 1rem; background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 0.3rem 0.7rem; cursor: pointer; font: inherit; color: var(--ink-2); }
  .legend { list-style: none; padding: 0; font-size: 0.85rem; color: var(--ink-2); }
  .legend li { display: flex; align-items: center; gap: 0.5rem; margin: 0.3rem 0; }
  .sw { width: 1.6rem; height: 0; border-top: 2px solid var(--accent); display: inline-block; }
  .sw.fam-structure { border-top: 2px dashed var(--accent-2); }
</style>
