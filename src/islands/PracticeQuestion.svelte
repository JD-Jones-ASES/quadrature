<script>
  // One practice question, "solved three ways" (ADR-0022): a multiple-choice "just get the answer" whose wrong
  // options are named misconceptions, plus (when the lesson supplies them) the algebra and calculus
  // step-throughs reused verbatim. It computes NOTHING and stores NOTHING — every value came from the producer,
  // proven finite and distinct from the answer at build time. This is practice as a reveal, not a graded quiz.
  let { question, calcLabel = "Calculus" } = $props();

  // a stable, SSR-safe shuffle: order choices by a hash of (id, value) so the correct answer isn't always
  // first, while the server and client render the same order (no hydration mismatch from Math.random).
  function hashKey(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); }
    return h >>> 0;
  }
  const choices = [...question.choices].sort(
    (a, b) => hashKey(`${question.id}:${a.value}`) - hashKey(`${question.id}:${b.value}`)
  );
  const correct = choices.find((c) => c.correct);
  const hasAlgebra = question.algebra_steps?.length > 0;
  const hasCalculus = question.calculus_steps?.length > 0;

  let mode = $state("answer");
  let picked = $state(null);
  let stepA = $state(0);
  let stepC = $state(0);
  const clamp = (i, n) => Math.max(0, Math.min(n - 1, i));
</script>

<div class="pq">
  <p class="pq-prompt">{@html question.promptHtml}</p>

  <div class="pq-modes" role="tablist" aria-label="Solve it three ways">
    <button role="tab" aria-selected={mode === "answer"} onclick={() => (mode = "answer")}>Just the answer</button>
    {#if hasAlgebra}
      <button role="tab" aria-selected={mode === "algebra"} onclick={() => (mode = "algebra")}>Algebra</button>
    {/if}
    {#if hasCalculus}
      <button role="tab" aria-selected={mode === "calculus"} onclick={() => (mode = "calculus")}>{calcLabel}</button>
    {/if}
  </div>

  {#if mode === "answer"}
    <div class="pq-choices" role="radiogroup" aria-label="Choose an answer">
      {#each choices as c (c.value)}
        <button
          class="pq-choice"
          class:right={picked && c.correct}
          class:wrong={picked === c && !c.correct}
          aria-pressed={picked === c}
          onclick={() => (picked = c)}
        >
          <span class="pq-mark">{#if picked}{c.correct ? "✓" : picked === c ? "✗" : ""}{/if}</span>
          <span class="pq-val">{@html c.displayHtml} <span class="pq-unit">{question.answer.unit}</span></span>
        </button>
      {/each}
    </div>

    {#if picked}
      <div class="pq-reveal" class:ok={picked.correct}>
        {#if picked.correct}
          <p class="pq-verdict ok">Correct.</p>
        {:else}
          <p class="pq-verdict no">Not quite — that's a common slip.</p>
          {#if picked.misconceptionHtml}<p class="pq-misc">{@html picked.misconceptionHtml}</p>{/if}
        {/if}
        <p class="pq-answer">
          Answer: <strong>{@html correct.displayHtml} {question.answer.unit}</strong>
          {#if question.answer.symbolicHtml}<span class="pq-sym">= {@html question.answer.symbolicHtml}</span>{/if}
        </p>
        {#if hasAlgebra || hasCalculus}
          <p class="pq-hint">Step through the {hasAlgebra ? "Algebra" : ""}{hasAlgebra && hasCalculus ? " and " : ""}{hasCalculus ? calcLabel : ""} above to see <em>why</em>.</p>
        {/if}
      </div>
    {/if}
  {:else if mode === "algebra"}
    <div class="pq-stepper" role="tabpanel" aria-label="Algebra step-through">
      <div class="pq-step" class:emph={question.algebra_steps[stepA].emphasis}>
        <div class="pq-step-label">{@html question.algebra_steps[stepA].labelHtml}</div>
        <div class="pq-math">{@html question.algebra_steps[stepA].latexHtml}</div>
        {#if question.algebra_steps[stepA].prose}<p class="pq-prose">{@html question.algebra_steps[stepA].proseHtml}</p>{/if}
      </div>
      <nav class="pq-stepnav">
        <button onclick={() => (stepA = clamp(stepA - 1, question.algebra_steps.length))} disabled={stepA === 0}>‹ Prev</button>
        <span class="pq-count">{stepA + 1} / {question.algebra_steps.length}</span>
        <button onclick={() => (stepA = clamp(stepA + 1, question.algebra_steps.length))} disabled={stepA === question.algebra_steps.length - 1}>Next ›</button>
      </nav>
    </div>
  {:else}
    <div class="pq-stepper" role="tabpanel" aria-label={`${calcLabel} step-through`}>
      <div class="pq-step" class:emph={question.calculus_steps[stepC].emphasis}>
        <div class="pq-step-label">{@html question.calculus_steps[stepC].labelHtml}</div>
        <div class="pq-math">{@html question.calculus_steps[stepC].latexHtml}</div>
        {#if question.calculus_steps[stepC].prose}<p class="pq-prose">{@html question.calculus_steps[stepC].proseHtml}</p>{/if}
      </div>
      <nav class="pq-stepnav">
        <button onclick={() => (stepC = clamp(stepC - 1, question.calculus_steps.length))} disabled={stepC === 0}>‹ Prev</button>
        <span class="pq-count">{stepC + 1} / {question.calculus_steps.length}</span>
        <button onclick={() => (stepC = clamp(stepC + 1, question.calculus_steps.length))} disabled={stepC === question.calculus_steps.length - 1}>Next ›</button>
      </nav>
    </div>
  {/if}
</div>

<style>
  .pq { background: var(--paper-2); border: 1px solid var(--line); border-radius: var(--radius); padding: 1rem 1.2rem; display: grid; gap: 0.8rem; }
  .pq-prompt { margin: 0; font-size: 1rem; }

  .pq-modes { display: flex; gap: 0.3rem; flex-wrap: wrap; }
  .pq-modes button {
    border: 1px solid var(--line); background: var(--paper); padding: 0.3rem 0.7rem; cursor: pointer; font: inherit;
    color: var(--ink-2); border-radius: 999px; font-size: 0.85rem;
  }
  .pq-modes button[aria-selected="true"] { color: var(--accent); border-color: var(--accent); font-weight: 600; }

  .pq-choices { display: grid; gap: 0.4rem; }
  .pq-choice {
    display: flex; align-items: center; gap: 0.6rem; text-align: left; font: inherit; cursor: pointer;
    background: var(--paper); border: 1px solid var(--line); border-radius: 10px; padding: 0.5rem 0.8rem; color: var(--ink);
  }
  .pq-choice:hover { border-color: var(--accent); }
  .pq-choice.right { border-color: var(--accent); background: var(--accent-soft); }
  .pq-choice.wrong { border-color: var(--warn); background: var(--warn-soft); }
  .pq-mark { width: 1rem; font-weight: 700; color: var(--accent); }
  .pq-choice.wrong .pq-mark { color: var(--warn); }
  .pq-val { font-family: var(--font-mono); }
  .pq-unit { color: var(--ink-faint); }

  .pq-reveal { border-top: 1px dashed var(--line); padding-top: 0.7rem; display: grid; gap: 0.4rem; }
  .pq-verdict { margin: 0; font-weight: 600; }
  .pq-verdict.ok { color: var(--accent); }
  .pq-verdict.no { color: var(--warn); }
  .pq-misc { margin: 0; color: var(--ink-2); font-size: 0.93rem; }
  .pq-answer { margin: 0; }
  .pq-sym { margin-left: 0.4rem; color: var(--ink-2); }
  .pq-hint { margin: 0; color: var(--ink-faint); font-size: 0.88rem; }

  .pq-stepper { background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius); padding: 0.9rem 1.1rem; }
  .pq-step-label { font-size: 0.85rem; color: var(--ink-faint); margin-bottom: 0.3rem; }
  .pq-step.emph .pq-math { background: var(--accent-soft); border-radius: var(--radius); padding: 0.3rem 0.6rem; }
  .pq-math { overflow-x: auto; }
  .pq-prose { color: var(--ink-2); margin: 0.5rem 0 0; font-size: 0.93rem; }
  .pq-stepnav { display: flex; align-items: center; gap: 1rem; margin-top: 0.8rem; }
  .pq-stepnav button { font: inherit; cursor: pointer; background: var(--paper-2); border: 1px solid var(--line); border-radius: 8px; padding: 0.3rem 0.7rem; color: var(--ink); }
  .pq-stepnav button:disabled { opacity: 0.4; cursor: default; }
  .pq-count { font-family: var(--font-mono); font-size: 0.85rem; color: var(--ink-faint); }
</style>
