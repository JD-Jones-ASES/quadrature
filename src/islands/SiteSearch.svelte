<script>
  // The site-wide formula-affordances layer (ADR-0030). One fetched dataset (/search-index.json), two consumers:
  //   1. a ⌘K / Ctrl-K command palette over all formulas + lessons + pages, and
  //   2. the in-prose formula-token hover popover — any `<a class="ftok" data-fid="…">` (emitted by inline() from
  //      an authored `$…$@{id}` tag) shows a preview of its reference entry on hover/focus.
  // The index (with KaTeX baked at build) is fetched once and cached, so nothing is re-rendered in the browser.
  import { onMount } from "svelte";
  import { withBase } from "../lib/withBase.js";

  let data = $state(null);      // { formulas, lessons, pages } once fetched
  let fmap = $state({});        // formula id -> entry, for the hover popover
  let open = $state(false);     // palette visibility
  let q = $state("");           // query
  let sel = $state(0);          // selected result index
  let pop = $state(null);       // hover popover: { fid, top, left, above } | null
  let isMac = $state(false);
  let inputEl, resultsEl;
  let hideTimer;

  const kbd = $derived(isMac ? "⌘K" : "Ctrl K");

  async function loadIndex() {
    if (data) return;
    try {
      const res = await fetch(withBase("/search-index.json"));
      const json = await res.json();
      fmap = Object.fromEntries(json.formulas.map((f) => [f.id, f]));
      data = json;
    } catch { /* search/hover degrade silently if the index can't be fetched */ }
  }

  function openPalette() { open = true; q = ""; sel = 0; loadIndex(); }
  function navigate(href) { location.href = withBase(href); }

  // --- matching: every whitespace term must appear in the entry's haystack; then rank by where it hit ---
  function haystack(e) {
    return (e.type === "formula"
      ? `${e.name} ${e.id} ${e.symbols.join(" ")} ${e.desc} ${e.domainLabel}`
      : `${e.name} ${e.text ?? ""}`).toLowerCase();
  }
  function score(e, query, terms) {
    const hay = haystack(e);
    if (!terms.every((t) => hay.includes(t))) return 0;
    const name = e.name.toLowerCase();
    let s = 10;
    if (e.type === "formula" && (e.id === query || e.symbols.some((sym) => sym.toLowerCase() === query))) s += 100;
    if (name === query) s += 90;
    else if (name.startsWith(query)) s += 60;
    else if (name.includes(query)) s += 40;
    if (e.type === "page") s -= 5;
    return s;
  }
  const results = $derived.by(() => {
    if (!data) return [];
    const query = q.trim().toLowerCase();
    if (!query) return [];
    const terms = query.split(/\s+/).filter(Boolean);
    const all = [...data.formulas, ...data.lessons, ...data.pages];
    return all
      .map((e) => ({ e, s: score(e, query, terms) }))
      .filter((x) => x.s > 0)
      .sort((a, b) => b.s - a.s || a.e.name.localeCompare(b.e.name))
      .slice(0, 40)
      .map((x) => x.e);
  });

  const TYPE_LABEL = { formula: "Formula", lesson: "Lesson", page: "Page" };

  function onInputKey(e) {
    if (e.key === "ArrowDown") { e.preventDefault(); sel = Math.min(sel + 1, results.length - 1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); sel = Math.max(sel - 1, 0); }
    else if (e.key === "Enter") { e.preventDefault(); const r = results[sel]; if (r) navigate(r.href); }
    else if (e.key === "Escape") { open = false; }
  }

  // keep selection in range + scroll the active row into view
  $effect(() => { if (sel > results.length - 1) sel = Math.max(0, results.length - 1); });
  $effect(() => {
    if (open && inputEl) inputEl.focus();
  });
  $effect(() => {
    if (open && resultsEl) resultsEl.querySelector(".row.sel")?.scrollIntoView({ block: "nearest" });
  });

  // --- in-prose token hover popover (document-level delegation; robust against late-hydrated island prose) ---
  function showPop(el, fid) {
    const r = el.getBoundingClientRect();
    const above = r.bottom + 170 > window.innerHeight;
    pop = {
      fid,
      left: Math.max(8, Math.min(r.left, window.innerWidth - 332)),
      top: above ? r.top - 6 : r.bottom + 6,
      above,
    };
  }
  function tokenAt(e) { return e.target?.closest?.("[data-fid]"); }
  function onOver(e) { const el = tokenAt(e); if (el && fmap[el.dataset.fid]) { clearTimeout(hideTimer); showPop(el, el.dataset.fid); } }
  function onOut(e) { if (tokenAt(e)) hideTimer = setTimeout(() => (pop = null), 90); }
  function onFocusIn(e) { const el = tokenAt(e); if (el && fmap[el.dataset.fid]) showPop(el, el.dataset.fid); }
  function onFocusOut(e) { if (tokenAt(e)) pop = null; }

  onMount(() => {
    isMac = /mac|iphone|ipad/i.test(navigator.platform || navigator.userAgent || "");
    const onWinKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); open ? (open = false) : openPalette(); }
      else if (e.key === "Escape" && open) open = false;
    };
    window.addEventListener("keydown", onWinKey);
    document.addEventListener("mouseover", onOver);
    document.addEventListener("mouseout", onOut);
    document.addEventListener("focusin", onFocusIn);
    document.addEventListener("focusout", onFocusOut);
    // prefetch the index when the browser is idle so the first hover/⌘K is instant
    (window.requestIdleCallback ?? ((fn) => setTimeout(fn, 600)))(loadIndex);
    return () => {
      window.removeEventListener("keydown", onWinKey);
      document.removeEventListener("mouseover", onOver);
      document.removeEventListener("mouseout", onOut);
      document.removeEventListener("focusin", onFocusIn);
      document.removeEventListener("focusout", onFocusOut);
    };
  });
</script>

<button class="strigger" onclick={openPalette} aria-label={`Search (${kbd})`} aria-haspopup="dialog">
  <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
    <circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.6" />
    <line x1="10.4" y1="10.4" x2="14" y2="14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
  </svg>
  <span class="slabel">Search</span>
  <kbd>{kbd}</kbd>
</button>

{#if open}
  <div class="overlay" role="presentation" onclick={() => (open = false)}>
    <div class="palette" role="dialog" aria-modal="true" aria-label="Search" onclick={(e) => e.stopPropagation()}>
      <div class="pbar">
        <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" class="picon">
          <circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" stroke-width="1.6" />
          <line x1="10.4" y1="10.4" x2="14" y2="14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
        </svg>
        <input bind:this={inputEl} bind:value={q} onkeydown={onInputKey}
               placeholder="Search formulas, lessons, pages…" aria-label="Search query"
               autocomplete="off" autocapitalize="off" spellcheck="false" />
        <kbd class="esc">Esc</kbd>
      </div>
      <div class="results" bind:this={resultsEl} role="listbox" aria-label="Search results">
        {#if !data}
          <p class="hint">Loading the index…</p>
        {:else if !q.trim()}
          <p class="hint">Search {data.formulas.length} formulas and {data.lessons.length} lessons.
            Try <em>momentum</em>, <em>capacitor</em>, <em>entropy</em>, or a symbol like <em>τ</em>.</p>
        {:else if results.length === 0}
          <p class="hint">No matches for “{q}”.</p>
        {:else}
          {#each results as r, i (r.type + (r.id ?? r.slug ?? r.href))}
            <a class="row" class:sel={i === sel} href={withBase(r.href)} role="option" aria-selected={i === sel}
               onmouseenter={() => (sel = i)}>
              <span class="rtype rt-{r.type}">{TYPE_LABEL[r.type]}</span>
              <span class="rmain">
                <span class="rname">{r.name}</span>
                {#if r.type === "formula"}
                  <span class="rmath">{@html r.latexHtml}</span>
                  <span class="rmeta">{r.domainLabel} · regime {r.regime}</span>
                {:else if r.type === "lesson"}
                  <span class="rmeta">{r.topic} · regime {r.regime}{r.snippet ? ` — ${r.snippet}` : ""}</span>
                {/if}
              </span>
            </a>
          {/each}
        {/if}
      </div>
    </div>
  </div>
{/if}

{#if pop && fmap[pop.fid]}
  {@const f = fmap[pop.fid]}
  <div class="fpop" class:above={pop.above} style={`top:${pop.top}px; left:${pop.left}px;`} role="tooltip">
    <div class="fpop-name">{f.name}</div>
    <div class="fpop-math">{@html f.latexHtml}</div>
    {#if f.assumptions?.length}
      <p class="fpop-assume"><strong>Valid when:</strong> {f.assumptions.join("; ")}</p>
    {/if}
    <p class="fpop-go">Open in reference →</p>
  </div>
{/if}

<style>
  /* ---- header trigger ---- */
  .strigger {
    display: inline-flex; align-items: center; gap: 0.4rem; cursor: pointer; font: inherit;
    color: var(--ink-2); background: var(--paper-2); border: 1px solid var(--line);
    border-radius: 8px; padding: 0.3rem 0.6rem;
  }
  .strigger:hover { border-color: var(--accent); color: var(--accent); }
  .strigger kbd {
    font-family: var(--font-mono); font-size: 0.72rem; color: var(--ink-faint);
    background: var(--paper-sunk); border: 1px solid var(--line); border-radius: 5px; padding: 0.02rem 0.32rem;
  }
  @media (max-width: 33rem) { .strigger .slabel, .strigger kbd { display: none; } }

  /* ---- palette ---- */
  .overlay {
    position: fixed; inset: 0; z-index: 100; background: rgba(0, 0, 0, 0.42);
    display: flex; justify-content: center; align-items: flex-start; padding: 12vh 1rem 1rem;
  }
  .palette {
    width: 100%; max-width: 40rem; background: var(--paper-2); border: 1px solid var(--line);
    border-radius: var(--radius); box-shadow: 0 16px 50px rgba(0, 0, 0, 0.35); overflow: hidden;
    display: flex; flex-direction: column; max-height: 70vh;
  }
  .pbar { display: flex; align-items: center; gap: 0.55rem; padding: 0.7rem 0.9rem; border-bottom: 1px solid var(--line); }
  .pbar .picon { color: var(--ink-faint); flex: none; }
  .pbar input { flex: 1; font: inherit; font-size: 1.05rem; background: none; border: none; color: var(--ink); outline: none; }
  .pbar .esc { font-family: var(--font-mono); font-size: 0.72rem; color: var(--ink-faint); background: var(--paper-sunk); border: 1px solid var(--line); border-radius: 5px; padding: 0.05rem 0.35rem; }

  .results { overflow-y: auto; padding: 0.35rem; }
  .hint { color: var(--ink-2); font-size: 0.9rem; padding: 0.7rem 0.6rem; margin: 0; }
  .hint em { color: var(--accent); font-style: normal; font-family: var(--font-mono); }

  .row {
    display: flex; gap: 0.7rem; align-items: baseline; padding: 0.5rem 0.6rem; border-radius: 8px;
    color: inherit; text-decoration: none;
  }
  .row.sel { background: var(--accent-soft); }
  .rtype {
    flex: none; width: 4.2rem; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.04em;
    color: var(--ink-faint); font-family: var(--font-mono); padding-top: 0.15rem;
  }
  .rt-formula { color: var(--accent); }
  .rmain { display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }
  .rname { color: var(--ink); font-weight: 600; }
  .rmath { color: var(--ink-2); overflow-x: auto; }
  .rmeta { font-size: 0.8rem; color: var(--ink-faint); }

  /* ---- in-prose token + its hover popover ---- */
  .fpop {
    position: fixed; z-index: 120; width: 21rem; max-width: calc(100vw - 1rem);
    padding: 0.7rem 0.85rem; background: var(--paper-2); border: 1px solid var(--line);
    border-radius: var(--radius); box-shadow: 0 8px 28px rgba(0, 0, 0, 0.22);
  }
  .fpop.above { transform: translateY(-100%); }
  .fpop-name { font-weight: 600; font-size: 0.95rem; margin-bottom: 0.25rem; }
  .fpop-math { overflow-x: auto; margin: 0.1rem 0 0.35rem; }
  .fpop-assume { font-size: 0.82rem; color: var(--ink-2); margin: 0.3rem 0 0; }
  .fpop-go { font-size: 0.78rem; color: var(--accent); margin: 0.45rem 0 0; }
</style>
