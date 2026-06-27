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

  // --- orbit frame (ADR-0015 centred path): a closed loop around a central body at the origin, equal aspect.
  // Two cases: circular (interactive closed form, a radius slider) and elliptical (sampled eccentricity frames).
  const isOrbit = graph.frame === "orbit";
  const orbSampled = isOrbit && sampled;
  const muG = graph.mu ?? 4e14;
  // FIXED view half-extent so the loop's size is meaningful: producer-supplied for the ellipse sweep, or the
  // radius slider's max (+margin) for the circular case (so widening R visibly grows the circle).
  const orbHalf = isOrbit ? (graph.view_half ?? ((paramDefs.R?.max ?? 1) * 1.12)) : 1;
  const OSIZE = 380, OPAD = 26;
  const oInner = OSIZE - 2 * OPAD, oc = OPAD + oInner / 2;
  const opx = (x) => oc + (x / orbHalf) * (oInner / 2);
  const opy = (y) => oc - (y / orbHalf) * (oInner / 2);
  // the current orbit path as world points: the committed ellipse frame, or one period of the circular closed form
  const orbPathPts = $derived.by(() => {
    if (!isOrbit) return { x: [], y: [] };
    if (orbSampled) { const fr = frames[frameIdx]; return { x: fr.series.x, y: fr.series.y }; }
    const R = vals.R, T = 2 * Math.PI * Math.sqrt(R ** 3 / muG), xs = [], ys = [];
    for (let i = 0; i <= N; i++) { const t = (i / N) * T; xs.push(call(fns.x, t)); ys.push(call(fns.y, t)); }
    return { x: xs, y: ys };
  });
  const orbPoly = $derived(orbPathPts.x.map((x, k) => `${opx(x).toFixed(1)},${opy(orbPathPts.y[k]).toFixed(1)}`).join(" "));
  // radii along the path → perihelion/aphelion, semi-major axis, period, vis-viva speeds (elliptical case)
  const orbRs = $derived(orbPathPts.x.map((x, i) => Math.hypot(x, orbPathPts.y[i])));
  const orbR = $derived(isOrbit && !orbSampled ? vals.R : 0);    // circular radius
  const orbRmin = $derived(orbSampled ? Math.min(...orbRs) : orbR); // perihelion
  const orbRmax = $derived(orbSampled ? Math.max(...orbRs) : orbR); // aphelion
  const orbA = $derived(orbSampled ? (orbRmin + orbRmax) / 2 : orbR); // semi-major axis
  const orbEcc = $derived(orbSampled ? frames[frameIdx].value : 0);
  const orbT = $derived(2 * Math.PI * Math.sqrt(orbA ** 3 / muG)); // period (depends on a only — Kepler III)
  const orbV = $derived(Math.sqrt(muG / orbR));                  // circular orbital speed √(μ/R)
  const orbVp = $derived(Math.sqrt(muG * (2 / orbRmin - 1 / orbA))); // perihelion speed (vis-viva, fastest)
  const orbVa = $derived(Math.sqrt(muG * (2 / orbRmax - 1 / orbA))); // aphelion speed (slowest)
  const orbG = $derived(muG / orbR ** 2);                        // gravity at the (circular) orbit
  // pixel positions of the perihelion (+x extreme) and aphelion (−x extreme) of the elliptical frame
  const orbPeri = $derived.by(() => { let k = 0; for (let i = 1; i < orbPathPts.x.length; i++) if (orbPathPts.x[i] > orbPathPts.x[k]) k = i; return k; });
  const orbApo = $derived.by(() => { let k = 0; for (let i = 1; i < orbPathPts.x.length; i++) if (orbPathPts.x[i] < orbPathPts.x[k]) k = i; return k; });
  const fmtT = (s) => (s >= 3600 ? `${(s / 3600).toFixed(2)} h` : `${(s / 60).toFixed(1)} min`);
  const fmtR = (m) => `${(m / 1e6).toFixed(2)}×10⁶ m`;
</script>

<div class="trajectory">
{#if isOrbit}
  <svg viewBox={`0 0 ${OSIZE} ${OSIZE}`} role="img"
       aria-label={orbSampled ? "Elliptical orbit: a closed ellipse with the planet at one focus" : "Circular orbit: the satellite's closed path around the central body"}>
    <defs>
      <marker id="vtip" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto">
        <path d="M0,0 L7,3.5 L0,7 z" class="vfill" />
      </marker>
    </defs>
    <line x1={opx(-orbHalf)} y1={oc} x2={opx(orbHalf)} y2={oc} class="oaxis" />
    <line x1={oc} y1={opy(-orbHalf)} x2={oc} y2={opy(orbHalf)} class="oaxis" />
    <polyline points={orbPoly} class="path" />
    <circle cx={oc} cy={oc} r="7" class="body" />
    {#if orbSampled}
      <text x={oc} y={oc + 20} class="lbl" text-anchor="middle">focus (planet)</text>
      <!-- perihelion (closest, fastest) and aphelion (farthest, slowest) markers -->
      <circle cx={opx(orbPathPts.x[orbPeri])} cy={opy(orbPathPts.y[orbPeri])} r="5" class="mark peri" />
      <text x={opx(orbPathPts.x[orbPeri]) + 6} y={opy(orbPathPts.y[orbPeri]) - 6} class="lbl">perihelion</text>
      <circle cx={opx(orbPathPts.x[orbApo])} cy={opy(orbPathPts.y[orbApo])} r="5" class="mark" />
      <text x={opx(orbPathPts.x[orbApo]) - 6} y={opy(orbPathPts.y[orbApo]) - 6} class="lbl" text-anchor="end">aphelion</text>
    {:else}
      <text x={oc} y={oc + 20} class="lbl" text-anchor="middle">central body</text>
      <line x1={oc} y1={oc} x2={opx(orbR)} y2={opy(0)} class="radius" />
      <text x={(oc + opx(orbR)) / 2} y={oc - 6} class="lbl" text-anchor="middle">R</text>
      <circle cx={opx(orbR)} cy={opy(0)} r="5" class="mark" />
      <line x1={opx(orbR)} y1={opy(0)} x2={opx(orbR)} y2={opy(0) - 30} class="varrow" marker-end="url(#vtip)" />
      <text x={opx(orbR) + 6} y={opy(0) - 18} class="lbl">v</text>
    {/if}
    <text x={OPAD} y={OPAD - 8} class="axlabel">{graph.y_label}</text>
    <text x={OSIZE - OPAD} y={OSIZE - 6} class="axlabel" text-anchor="end">{graph.x_label}</text>
  </svg>
  {#if orbSampled}
    <div class="annot">
      <p>At <strong>eccentricity e = {fmt(orbEcc)}</strong>: the orbit is {orbEcc === 0 ? "a circle" : "an ellipse with the planet at one focus"}.
        Perihelion <strong>{fmtR(orbRmin)}</strong> at <strong class="hl">{fmt(orbVp / 1000)} km/s</strong> (fastest),
        aphelion <strong>{fmtR(orbRmax)}</strong> at <strong>{fmt(orbVa / 1000)} km/s</strong> (slowest) —
        equal areas in equal times (Kepler's 2nd law). Period <strong>T = {fmtT(orbT)}</strong>, the
        <em>same for every eccentricity</em> because they share the semi-major axis (Kepler's 3rd law).</p>
    </div>
    <div class="sliders">
      <label>
        <span class="pname">{sweep?.label} = {fmt(frames[frameIdx].value)}</span>
        <input type="range" min="0" max={frames.length - 1} step="1" bind:value={frameIdx} />
      </label>
      <p class="framelabel">{frames[frameIdx].label}</p>
      <p class="hint faint">Each stop is a numerically-integrated orbit (no closed form for the motion in time).
        Slide the eccentricity: the shape stretches from a circle to a long ellipse, but the period never
        changes — it depends on the semi-major axis alone.</p>
    </div>
  {:else}
    <div class="annot">
      <p>At radius <strong>R = {fmtR(orbR)}</strong>: orbital speed <strong class="hl">v = {fmt(orbV / 1000)} km/s</strong>,
        period <strong>T = {fmtT(orbT)}</strong>. Gravity here is <strong>{fmt(orbG)} m/s²</strong> — that inward pull
        is exactly the centripetal acceleration v²/R, so the satellite falls <em>around</em> the planet, not into it.
        Widen the orbit and the speed drops as 1/√R while the period grows as R^(3/2) — Kepler's third law.</p>
    </div>
    <div class="sliders">
      {#each Object.entries(paramDefs) as [name, def]}
        <label>
          <span class="pname">R = {fmtR(vals[name])}</span>
          <input type="range" min={def.min} max={def.max} step={(def.max - def.min) / 200} bind:value={vals[name]} />
        </label>
      {/each}
      <p class="hint faint">Drag the orbital radius: the loop widens, the satellite slows, and the period stretches —
        double the radius and the period grows by 2^(3/2) ≈ 2.83 (Kepler's third law).</p>
    </div>
  {/if}
{:else}
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
{/if}
</div>

<style>
  .trajectory { display: grid; gap: 0.5rem; }
  svg { width: 100%; height: auto; background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); }
  .frame { fill: none; stroke: var(--line); stroke-width: 1; }
  .ground { stroke: color-mix(in srgb, var(--ink-faint) 60%, transparent); stroke-width: 1; }
  .oaxis { stroke: color-mix(in srgb, var(--ink-faint) 35%, transparent); stroke-width: 1; stroke-dasharray: 2 3; }
  .body { fill: var(--ink); }
  .radius { stroke: var(--ink-faint); stroke-width: 1; stroke-dasharray: 4 3; }
  .varrow { stroke: var(--accent); stroke-width: 2; }
  .vfill { fill: var(--accent); }
  .mark.peri { fill: var(--accent); stroke: var(--ink); stroke-width: 1.5; }
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
