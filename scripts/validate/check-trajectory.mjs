// check-trajectory.mjs — the CI re-gate for numerically-integrated trajectories (ADR-0015), the analog of
// check-parity for paths that have NO closed form (quadratic-drag projectile). The producer does the strong
// verification (RK4 step-convergence + equation-of-motion residual) and refuses to emit a bad path; this gate
// re-checks the COMMITTED sample points with physics the Node side can do exactly:
//   - structural integrity (starts at the origin, lands at y≈0, t increasing, all finite, y≥0);
//   - the b=0 frame reproduces the exact drag-free parabola range v0²·sin2θ/|g| (independent ground truth);
//   - the range decreases monotonically as the drag coefficient grows (drag can only shorten the flight).
// Fails loud (exit 1).

import { readdirSync, statSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, relative, join } from "node:path";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const DERIVED = resolve(ROOT, "derived");

const errors = [];
const fail = (m) => errors.push(m);

function walk(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else if (name.endsWith(".solution.json")) out.push(p);
  }
  return out;
}

let count = 0;
for (const file of walk(DERIVED).sort()) {
  const rel = relative(ROOT, file).replace(/\\/g, "/");
  const data = JSON.parse(readFileSync(file, "utf8"));
  const c = data.constants ?? {};
  data.graphs.forEach((g, gi) => {
    if (g.kind !== "trajectory" || !g.frames) return;
    const label = `${rel} graphs[${gi}]`;

    // --- orbit frames (frame:"orbit"): a closed loop around the focus at the origin, not a projectile arc.
    // The producer proves energy/angular-momentum conservation on the full-resolution path; here we re-check
    // the COMMITTED points with exact geometry — each frame is finite, closes after one period, encircles the
    // focus exactly once (total turning ≈ 2π), e=0 is a circle, and every frame shares the period (Kepler III).
    if (g.frame === "orbit") {
      const periods = [];
      for (const fr of g.frames) {
        const { t, x, y } = fr.series;
        const tag = `${label} frame e=${fr.value}`;
        if (![t, x, y].every((a) => a.every(Number.isFinite))) { fail(`${tag}: non-finite sample`); continue; }
        const n = x.length;
        const scale = Math.max(...x.map(Math.abs), ...y.map(Math.abs), 1);
        if (Math.hypot(x[n - 1] - x[0], y[n - 1] - y[0]) > 0.02 * scale)
          fail(`${tag}: does not close after one period`);
        let turn = 0;
        for (let i = 0; i < n - 1; i++) {
          let d = Math.atan2(y[i + 1], x[i + 1]) - Math.atan2(y[i], x[i]);
          if (d > Math.PI) d -= 2 * Math.PI; else if (d < -Math.PI) d += 2 * Math.PI;
          turn += d;
        }
        if (Math.abs(Math.abs(turn) - 2 * Math.PI) > 0.05)
          fail(`${tag}: does not encircle the focus exactly once (total turning ${turn.toFixed(3)})`);
        if (fr.value === 0) {
          const rs = x.map((xi, i) => Math.hypot(xi, y[i]));
          if ((Math.max(...rs) - Math.min(...rs)) / scale > 0.01)
            fail(`${tag}: e=0 orbit is not a circle (Δr/scale ${((Math.max(...rs) - Math.min(...rs)) / scale).toExponential(2)})`);
        }
        periods.push(fr.series.t_max);
        count++;
      }
      if (Math.max(...periods) - Math.min(...periods) > 1e-3)
        fail(`${label}: orbit frames have different periods (Kepler III: same a ⇒ same T)`);
      return;
    }

    const ranges = [];
    for (const fr of g.frames) {
      const { t, x, y } = fr.series;
      const finite = [t, x, y].every((arr) => arr.every(Number.isFinite));
      if (!finite) { fail(`${label} frame b=${fr.value}: non-finite sample`); continue; }
      if (Math.abs(t[0]) > 1e-6 || Math.abs(x[0]) > 1e-6 || Math.abs(y[0]) > 1e-6)
        fail(`${label} frame b=${fr.value}: does not start at the origin at t=0`);
      for (let i = 1; i < t.length; i++) if (t[i] <= t[i - 1])
        { fail(`${label} frame b=${fr.value}: time not increasing at ${i}`); break; }
      if (y.some((v) => v < -1e-6)) fail(`${label} frame b=${fr.value}: y goes below ground`);
      if (Math.abs(y[y.length - 1]) > 1e-3) fail(`${label} frame b=${fr.value}: does not land at y≈0 (y=${y[y.length - 1]})`);
      ranges.push({ b: fr.value, R: x[x.length - 1] });
      count++;
    }
    // b=0 must reproduce the exact drag-free parabola
    const zero = g.frames.find((fr) => fr.value === 0);
    if (zero && c.v0 != null && c.theta_deg != null && c.g != null) {
      const th = (c.theta_deg * Math.PI) / 180;
      const R = (c.v0 * c.v0 * Math.sin(2 * th)) / Math.abs(c.g);
      const got = zero.series.x[zero.series.x.length - 1];
      if (Math.abs(got - R) > 2e-2)
        fail(`${label} b=0 range ${got.toFixed(4)} ≠ analytic parabola ${R.toFixed(4)} (Δ=${Math.abs(got - R).toExponential(2)})`);
    }
    // range must be non-increasing as drag grows
    const byB = ranges.slice().sort((a, b) => a.b - b.b);
    for (let i = 1; i < byB.length; i++) if (byB[i].R > byB[i - 1].R + 1e-6)
      fail(`${label}: range grew with drag (b=${byB[i - 1].b}→${byB[i].b}: ${byB[i - 1].R.toFixed(2)}→${byB[i].R.toFixed(2)} m)`);
  });
}

if (errors.length) {
  console.error(`\nTRAJECTORY CHECK FAILED (${errors.length}):`);
  for (const e of errors) console.error("  - " + e);
  process.exit(1);
}
console.log(`OK: ${count} numerical trajectory frame(s) structurally + physically consistent.`);
