// Build-time KaTeX rendering. Used in Astro frontmatter to turn LaTeX strings into HTML so the player
// islands never ship KaTeX to the browser. The check:katex gate guarantees every string renders, so
// throwOnError can stay false here (a survived string is known-good).
import katex from "katex";

export function tex(latex, displayMode = true) {
  return katex.renderToString(latex, { throwOnError: false, displayMode });
}
