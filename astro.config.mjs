import { defineConfig } from "astro/config";
import svelte from "@astrojs/svelte";

// Deployed to GitHub Pages as a project site:
//   https://jd-jones-ases.github.io/quadrature/
// `base` is applied to all built asset URLs; in-app links go through withBase() in src/lib/withBase.js.
// Set LOCAL_ROOT=1 to serve from "/" for local previews (the production base is a subpath).
const base = process.env.LOCAL_ROOT ? "/" : (process.env.PAGES_BASE ?? "/quadrature");

export default defineConfig({
  site: "https://jd-jones-ases.github.io",
  base,
  output: "static",
  trailingSlash: "always",
  integrations: [svelte()],
});
