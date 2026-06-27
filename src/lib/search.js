// Build-time search / preview index (ADR-0030). Aggregates already-derived data — no producer change.
// Powers BOTH the ⌘K command palette and the in-prose formula-token hover popover (one dataset, two consumers).
// Served as a single static JSON endpoint (src/pages/search-index.json.js) and fetched once by the SiteSearch
// island, so the pre-baked KaTeX is cached across navigations instead of re-embedded in every page's HTML.
import { tex } from "./katex.js";
import formulaData from "../../derived/reference/formulas.json";

const DOMAIN_LABEL = {
  mechanics: "Mechanics", em: "Electricity & magnetism", thermo: "Thermodynamics",
  "waves-optics": "Waves & optics", modern: "Modern physics",
};

// Plain-text projection for matching / snippets / meta descriptions: drop inline math delimiters, formula tags,
// and markdown emphasis markers so authored prose never leaks `$…$`, `@{id}`, or `**` into SEO/social text.
export function plain(s) {
  return String(s ?? "")
    .replace(/\$[^$]*\$/g, " ")
    .replace(/@\{[a-z0-9-]+\}/g, " ")
    .replace(/[*_`]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function buildSearchIndex() {
  const formulas = formulaData.formulas.map((f) => ({
    type: "formula",
    id: f.id,
    name: f.name,
    latexHtml: tex(f.latex, false), // inline KaTeX, baked at build (no KaTeX shipped to the browser)
    symbols: [f.lhs, ...Object.keys(f.variables ?? {})].filter(Boolean),
    domain: f.domain,
    domainLabel: DOMAIN_LABEL[f.domain] ?? f.domain,
    regime: f.regime,
    desc: Object.values(f.variables ?? {}).map((v) => v.desc).filter(Boolean).join(" · "),
    assumptions: f.assumptions ?? [],
    href: "/reference/#" + f.id,
    graphHref: "/reference/graph/#" + f.id,
  }));

  const mods = import.meta.glob("../../derived/**/*.solution.json", { eager: true });
  const lessons = Object.values(mods)
    .filter((m) => m.default && m.default.slug)
    .map((m) => {
      const s = m.default;
      const snippet = plain(s.scenario);
      return {
        type: "lesson",
        slug: s.slug,
        name: s.title,
        topic: s.topic,
        regime: s.regime,
        snippet: snippet.length > 130 ? snippet.slice(0, 127) + "…" : snippet,
        text: plain(`${s.title} ${s.scenario} ${s.topic ?? ""}`),
        href: "/lessons/" + s.slug + "/",
      };
    })
    .sort((a, b) => a.name.localeCompare(b.name));

  const pages = [
    { type: "page", name: "Guide — how to read this course", href: "/guide/", text: "guide how to read regimes practice solve it three ways" },
    { type: "page", name: "Lessons", href: "/lessons/", text: "lessons index all lessons" },
    { type: "page", name: "Formula reference", href: "/reference/", text: "reference formulas sheet" },
    { type: "page", name: "Concept graph", href: "/reference/graph/", text: "concept graph relationships nodes edges" },
    { type: "page", name: "Verification", href: "/verification/", text: "verification sympy proof how it works gates" },
  ];

  return { formulas, lessons, pages };
}
