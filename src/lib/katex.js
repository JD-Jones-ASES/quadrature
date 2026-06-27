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

// Lightweight markdown emphasis on already-HTML-escaped, non-math text: **bold** -> <strong>, *italic* -> <em>.
// Bold is matched first so a `**x**` doesn't leave stray single asterisks; the content classes `[^*]+` mean an
// unmatched (odd) asterisk is left literal rather than mangled. Authored prose carries this emphasis (e.g. a
// scenario's "a **real, inverted** image"); without this it rendered as literal asterisks.
function emphasize(s) {
  return s
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

// Formula-reference token (ADR-0030): an inline-math span may be tagged with a reference formula id written
// immediately after it — `$\tau = RC$@{em-rc-charge}`. The mapping is AUTHORED and adjacent (not inferred from
// the rendered span — that mapping is ambiguous, the reason it was parked in ADR-0026). When present, the math is
// wrapped in a link to that formula's reference entry and carries `data-fid` so the global SiteSearch island can
// attach a hover preview. The visible math is byte-identical to the untagged render.
const FTOKEN = /^@\{([a-z0-9-]+)\}/;
function refHref(id) {
  const base = import.meta.env.BASE_URL; // "/quadrature/" in prod, "/" under LOCAL_ROOT (same source as withBase)
  return (base.endsWith("/") ? base : base + "/") + "reference/#" + id;
}

// Render a prose string that may contain inline math delimited by $...$, returning HTML.
// Math segments become inline KaTeX; the surrounding text is HTML-escaped and gets markdown emphasis. Used for
// step prose, proof claims, result labels, scenarios, misconceptions — anywhere math sits inside a sentence.
export function inline(s) {
  if (s == null) return s;
  const parts = String(s).split(/(\$[^$]+\$)/g);
  let out = "";
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    const isMath = part.length > 2 && part.startsWith("$") && part.endsWith("$");
    if (!isMath) {
      out += emphasize(escapeHtml(part));
      continue;
    }
    const rendered = katex.renderToString(part.slice(1, -1), { throwOnError: false, displayMode: false });
    const next = parts[i + 1];
    const tag = next != null ? next.match(FTOKEN) : null;
    if (tag) {
      out += `<a class="ftok" data-fid="${tag[1]}" href="${refHref(tag[1])}">${rendered}</a>`;
      parts[i + 1] = next.slice(tag[0].length); // strip @{id} from the following text segment
    } else {
      out += rendered;
    }
  }
  return out;
}
