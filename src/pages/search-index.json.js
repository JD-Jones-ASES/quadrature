// Static search/preview index endpoint (ADR-0030). Pre-rendered at build into /search-index.json and fetched
// once by the SiteSearch island, so the baked KaTeX previews are cached across page navigations rather than
// re-embedded in every page. Pure aggregation of already-derived data — no producer change.
import { buildSearchIndex } from "../lib/search.js";

export const prerender = true;

export function GET() {
  return new Response(JSON.stringify(buildSearchIndex()), {
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}
