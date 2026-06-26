// Build-time KaTeX rendering. Used in Astro frontmatter to turn LaTeX into HTML so the player islands
// never ship KaTeX to the browser. The check:katex gate guarantees every string renders, so throwOnError
// can stay false here (a survived string is known-good).
import katex from "katex";

export function tex(latex, displayMode = true) {
  return katex.renderToString(latex, { throwOnError: false, displayMode });
}

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Render a prose string that may contain inline math delimited by $...$, returning HTML.
// Math segments become inline KaTeX; the surrounding text is HTML-escaped. Used for step prose, proof
// claims, result labels, misconceptions — anywhere math sits inside a sentence.
export function inline(s) {
  if (s == null) return s;
  return String(s)
    .split(/(\$[^$]+\$)/g)
    .map((part) =>
      part.length > 2 && part.startsWith("$") && part.endsWith("$")
        ? katex.renderToString(part.slice(1, -1), { throwOnError: false, displayMode: false })
        : escapeHtml(part)
    )
    .join("");
}
