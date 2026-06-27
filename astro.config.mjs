import { defineConfig } from "astro/config";
import svelte from "@astrojs/svelte";

// Deployed to GitHub Pages as a project site:
//   https://jd-jones-ases.github.io/quadrature/
// `base` is applied to all built asset URLs; in-app links go through withBase() in src/lib/withBase.js.
// Set LOCAL_ROOT=1 to serve from "/" for local previews (the production base is a subpath).
const base = process.env.LOCAL_ROOT ? "/" : (process.env.PAGES_BASE ?? "/quadrature");

// Dev/preview server port: honor the harness-assigned PORT env var (autoPort), falling back to 4321.
// Only affects `astro dev`/`astro preview`; the static `astro build` ignores it.
const devPort = process.env.PORT ? Number(process.env.PORT) : 4321;

export default defineConfig({
  site: "https://jd-jones-ases.github.io",
  base,
  output: "static",
  trailingSlash: "always",
  // `css: "injected"` makes every Svelte component (incl. CHILD islands like GraphStack/AreaPlot/Collision
  // that are imported and rendered *inside* SolutionPlayer) ship its scoped <style> via the JS chunk and inject
  // it on mount. Without this, Astro only delivered the CSS of the top-level islands used directly in .astro
  // pages, so the child graph instruments rendered with default black SVG fills. See DECISIONS ADR-0019.
  integrations: [svelte({ compilerOptions: { css: "injected" } })],
  server: { port: devPort },
});
