<script>
  // The dumb stepper: four reconciled views of one SymPy-verified scenario — scenario, the algebra
  // register (stepped), the calculus register (stepped, the algebra formula emerging from ∫v dt), and
  // the graph. Plus the two honesty badges, the SHOWN equivalence proof, the misconception register,
  // and the sign-rigor treatment. It computes nothing; every value came from the producer.
  import GraphStack from "./GraphStack.svelte";
  import AreaPlot from "./AreaPlot.svelte";
  import Trajectory from "./Trajectory.svelte";
  import EnergyBars from "./EnergyBars.svelte";
  import Collision from "./Collision.svelte";
  import PracticeQuestion from "./PracticeQuestion.svelte";

  let { solution } = $props();
  const s = solution;
  const graph = s.graphs[0];

  let tab = $state("calculus");
  let stepA = $state(0);
  let stepC = $state(0);
  let showProof = $state(true);

  const aSteps = s.algebra.steps;
  const cSteps = s.calculus.steps;
  const clamp = (i, n) => Math.max(0, Math.min(n - 1, i));
  const results = Object.entries(s.algebra.result);
</script>

<section class="player">
  <header class="head">
    <div class="badges">
      <span class="badge regime">Regime {s.regime} · {s.regime === 1 ? "algebra is calculus, evaluated" : s.regime === 2 ? "calculus does more" : "algebra-only"}</span>
      <span class="badge machine"><span class="dot"></span>Math machine-derived &amp; checked by SymPy</span>
      <span class="badge model"><span class="dot"></span>{s.assumptions.length} modeling assumptions (author-asserted)</span>
    </div>
    <p class="scenario">{@html s.scenarioHtml}</p>
  </header>

  <!-- results -->
  {#if results.length}
    <div class="results">
      {#each results as [key, r]}
        <div class="result">
          <div class="label">{@html r.labelHtml}</div>
          <div class="value">{r.display} <span class="unit">{r.unit}</span></div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- register tabs -->
  <div class="tabs" role="tablist">
    <button role="tab" aria-selected={tab === "algebra"} onclick={() => (tab = "algebra")}>Algebra</button>
    <button role="tab" aria-selected={tab === "calculus"} onclick={() => (tab = "calculus")}>Calculus</button>
    <button role="tab" aria-selected={tab === "graph"} onclick={() => (tab = "graph")}>Graph</button>
    {#if s.practice?.length}
      <button role="tab" aria-selected={tab === "practice"} onclick={() => (tab = "practice")}>Practice</button>
    {/if}
  </div>

  {#if tab === "algebra"}
    <div class="stepper" role="tabpanel" aria-label="Algebra register">
      <div class="step">
        <div class="step-label">{@html aSteps[stepA].labelHtml}</div>
        <div class="math">{@html aSteps[stepA].latexHtml}</div>
        {#if aSteps[stepA].prose}<p class="prose">{@html aSteps[stepA].proseHtml}</p>{/if}
      </div>
      <nav class="stepnav">
        <button onclick={() => (stepA = clamp(stepA - 1, aSteps.length))} disabled={stepA === 0}>‹ Prev</button>
        <span class="count">{stepA + 1} / {aSteps.length}</span>
        <button onclick={() => (stepA = clamp(stepA + 1, aSteps.length))} disabled={stepA === aSteps.length - 1}>Next ›</button>
      </nav>
    </div>
  {:else if tab === "calculus"}
    <div class="stepper" role="tabpanel" aria-label="Calculus register">
      <div class="step" class:emph={cSteps[stepC].emphasis}>
        <div class="step-label">{@html cSteps[stepC].labelHtml}</div>
        <div class="math">{@html cSteps[stepC].latexHtml}</div>
        {#if cSteps[stepC].prose}<p class="prose">{@html cSteps[stepC].proseHtml}</p>{/if}
      </div>
      <nav class="stepnav">
        <button onclick={() => (stepC = clamp(stepC - 1, cSteps.length))} disabled={stepC === 0}>‹ Prev</button>
        <span class="count">{stepC + 1} / {cSteps.length}</span>
        <button onclick={() => (stepC = clamp(stepC + 1, cSteps.length))} disabled={stepC === cSteps.length - 1}>Next ›</button>
      </nav>
    </div>
  {:else if tab === "graph"}
    <div class="graphpanel" role="tabpanel" aria-label="Graph">
      {#if graph.kind === "area"}
        <AreaPlot {graph} />
      {:else if graph.kind === "trajectory"}
        <Trajectory {graph} />
      {:else if graph.kind === "energy"}
        <EnergyBars {graph} />
      {:else if graph.kind === "collision"}
        <Collision {graph} />
      {:else}
        <GraphStack {graph} />
      {/if}
    </div>
  {:else if tab === "practice"}
    <div class="practicepanel" role="tabpanel" aria-label="Practice">
      <p class="practice-lede">Solve each one three ways — get the answer, then watch it fall out in the algebra and the calculus. Wrong options are common misconceptions, not random numbers.</p>
      {#each s.practice as q (q.id)}
        <PracticeQuestion question={q} />
      {/each}
    </div>
  {/if}

  <!-- the proof, SHOWN not asserted (equivalence for regime 1; governing for regime 2) -->
  <div class="proof">
    <button class="proof-head" onclick={() => (showProof = !showProof)} aria-expanded={showProof}>
      <span class="badge machine"><span class="dot"></span>SymPy proof</span>
      <strong>{@html s.proof.headingHtml}</strong>
      <span class="chev">{showProof ? "▾" : "▸"}</span>
    </button>
    {#if showProof}
      <p class="faint detail">{@html s.proof.detailHtml}</p>
      <ul class="checks">
        {#each s.proof.checks as c}
          <li><span class="tick">✓</span> {@html c.claimHtml} <span class="tier">[{c.tier}]</span></li>
        {/each}
      </ul>
      <p class="faint">Dimensional homogeneity: checked by SymPy ({s.units_check.holds ? "holds" : "FAILS"}).</p>
    {/if}
  </div>

  <!-- misconception register -->
  {#if s.misconception}
    <div class="misconception">
      <div class="mis-claim"><span class="x">✗</span> Common misconception: “{@html s.misconception.claimHtml}”</div>
      <p class="mis-fix">{@html s.misconception.refutedHtml}</p>
    </div>
  {/if}

  <!-- sign rigor -->
  {#if s.sign_analysis}
    <div class="signs">
      <div class="sign-rule">{@html s.sign_analysis.ruleHtml}</div>
      <div class="sign-grid">
        {#each s.sign_analysis.segments as seg}
          <div class="seg">
            <div class="seg-phase">{seg.phase}</div>
            <div class="seg-sign">v {seg.v_sign} · a {seg.a_sign}</div>
            <div class="seg-state">{@html seg.stateHtml}</div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- assumptions, disclosed -->
  <details class="assumptions">
    <summary><span class="badge model"><span class="dot"></span>Modeling assumptions</span> — author-asserted, disclosed not discharged</summary>
    <ul>
      {#each s.assumptions as a}<li>{@html a.claimHtml}</li>{/each}
    </ul>
  </details>
</section>

<style>
  .player { display: grid; gap: 1.1rem; }
  .badges { display: flex; flex-wrap: wrap; gap: 0.5rem; }
  .scenario { font-size: 1.05rem; margin: 0.6rem 0 0; }

  .tabs { display: flex; gap: 0.4rem; border-bottom: 1px solid var(--line); }
  .tabs button {
    border: none; background: none; padding: 0.5rem 0.9rem; cursor: pointer; font: inherit;
    color: var(--ink-2); border-bottom: 2px solid transparent; margin-bottom: -1px;
  }
  .tabs button[aria-selected="true"] { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }

  .stepper { background: var(--paper-2); border: 1px solid var(--line); border-radius: var(--radius); padding: 1rem 1.2rem; }
  .step-label { font-size: 0.85rem; color: var(--ink-faint); margin-bottom: 0.3rem; }
  .step.emph .math { background: var(--accent-soft); border-radius: var(--radius); padding: 0.3rem 0.6rem; }
  .math { overflow-x: auto; }
  .prose { color: var(--ink-2); margin: 0.5rem 0 0; font-size: 0.95rem; }
  .stepnav { display: flex; align-items: center; gap: 1rem; margin-top: 0.8rem; }
  .stepnav button { font: inherit; cursor: pointer; background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 0.3rem 0.7rem; color: var(--ink); }
  .stepnav button:disabled { opacity: 0.4; cursor: default; }
  .count { font-family: var(--font-mono); font-size: 0.85rem; color: var(--ink-faint); }

  .proof { border: 1px solid color-mix(in srgb, var(--accent) 30%, var(--line)); border-radius: var(--radius); padding: 0.4rem 0.9rem 0.9rem; }
  .proof-head { display: flex; align-items: center; gap: 0.7rem; width: 100%; background: none; border: none; cursor: pointer; font: inherit; color: var(--ink); padding: 0.5rem 0; text-align: left; }
  .proof-head .chev { margin-left: auto; color: var(--ink-faint); }
  .checks { list-style: none; padding: 0; margin: 0.3rem 0; display: grid; gap: 0.35rem; }
  .checks li { font-size: 0.93rem; }
  .tick { color: var(--accent); font-weight: 700; }
  .tier { color: var(--ink-faint); font-family: var(--font-mono); font-size: 0.78rem; }
  .detail { font-family: var(--font-mono); font-size: 0.82rem; margin: 0.2rem 0; }

  .misconception { background: var(--warn-soft); border: 1px solid color-mix(in srgb, var(--warn) 35%, transparent); border-radius: var(--radius); padding: 0.8rem 1rem; }
  .mis-claim { font-weight: 600; color: var(--warn); }
  .mis-claim .x { font-weight: 700; }
  .mis-fix { margin: 0.4rem 0 0; color: var(--ink-2); font-size: 0.95rem; }

  .signs { display: grid; gap: 0.5rem; }
  .sign-rule { font-family: var(--font-mono); font-size: 0.85rem; color: var(--ink-2); }
  .sign-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr)); gap: 0.6rem; }
  .seg { background: var(--paper-2); border: 1px solid var(--line); border-radius: var(--radius); padding: 0.6rem 0.8rem; }
  .seg-phase { font-weight: 600; text-transform: capitalize; }
  .seg-sign { font-family: var(--font-mono); font-size: 0.85rem; color: var(--accent); }
  .seg-state { color: var(--ink-2); font-size: 0.9rem; }

  .assumptions summary { cursor: pointer; color: var(--ink-2); }
  .assumptions ul { color: var(--ink-2); font-size: 0.93rem; }

  .practicepanel { display: grid; gap: 0.9rem; }
  .practice-lede { margin: 0; color: var(--ink-2); font-size: 0.95rem; }
</style>
