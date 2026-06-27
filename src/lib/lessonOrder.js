// The pedagogical course sequence for the lessons index. The index groups lessons by UNIT in the order of
// `UNITS`, and within a unit renders them in the order they appear in `ORDER`. Keyed by the solution `slug`.
//
// This is intentionally a presentation-only manifest in `src/` (NOT in the producer / verified JSON): reading
// order is editorial chrome, while the producer's solution.json is the machine-verified physics record. Adding
// a lesson is one line here; a lesson present in derived/ but absent from `ORDER` falls into a trailing
// "More lessons" group, so the index never breaks. Slugs listed here that don't exist yet (planned lessons)
// are simply skipped until their solution.json is built.

export const UNITS = [
  { id: "kinematics",   title: "Kinematics",              blurb: "Describing motion in one and two dimensions." },
  { id: "dynamics",     title: "Dynamics & forces",       blurb: "What makes motion change — Newton's laws, friction, drag." },
  { id: "energy",       title: "Energy & work",           blurb: "Work as the area under a force; conservation of energy." },
  { id: "momentum",     title: "Momentum & collisions",   blurb: "Impulse, and what survives a crash." },
  { id: "rotation",     title: "Rotation",                blurb: "The same calculus, with angular labels." },
  { id: "oscillations", title: "Oscillations",            blurb: "Simple harmonic motion and damping." },
  { id: "gravitation",  title: "Gravitation & orbits",    blurb: "From the inverse-square law to Kepler's laws." },
  { id: "fluids",       title: "Fluids",                  blurb: "Pressure, depth, and flow." },
  { id: "thermo",       title: "Thermodynamics",          blurb: "Work on a pressure–volume diagram." },
  { id: "em",           title: "Electricity & magnetism", blurb: "Charges, fields, stored energy, and circuits." },
  { id: "waves",        title: "Waves & optics",          blurb: "Periodic motion in space and time." },
  { id: "modern",       title: "Modern physics",          blurb: "Quanta, matter waves, and relativity." },
];

// [slug, unitId] in reading order. New (Phase 4–5) lessons are listed in place; they appear once built.
export const ORDER = [
  // Kinematics
  ["throw-up",            "kinematics"],
  ["drag-free",           "kinematics"],
  // Dynamics & forces
  ["incline-friction",    "dynamics"],     // (planned) Newton's second law on an incline with friction
  ["terminal-velocity",   "dynamics"],
  ["with-drag",           "dynamics"],
  // Energy & work
  ["work-variable-force", "energy"],
  ["conservation",        "energy"],
  // Momentum & collisions
  ["impulse",             "momentum"],
  ["collision",           "momentum"],
  // Rotation
  ["angular-kinematics",  "rotation"],
  ["moment-of-inertia",   "rotation"],
  ["rotational-work",     "rotation"],
  // Oscillations
  ["mass-spring",         "oscillations"],
  ["damped",              "oscillations"],
  // Gravitation & orbits
  ["circular-orbit",      "gravitation"],
  ["elliptical-orbit",    "gravitation"],
  ["potential-energy",    "gravitation"],
  // Fluids
  ["hydrostatic-force",   "fluids"],
  ["torricelli",          "fluids"],        // (planned) Torricelli / Bernoulli — draining tank
  // Thermodynamics
  ["isobaric-work",       "thermo"],        // constant-pressure work — the rectangle (the quadrature)
  ["isothermal-work",     "thermo"],
  ["adiabatic-work",      "thermo"],
  // Electricity & magnetism
  ["coulomb-pe",          "em"],
  ["line-charge-field",   "em"],            // (planned) field from a continuous charge, ∫k dq/r²
  ["capacitor-energy",    "em"],
  ["rc-charging",         "em"],            // (planned) RC charging, Q(t)/I(t) on the 2-panel stack
  ["lc-oscillation",      "em"],            // LC oscillator — Q/I on the 2-panel stack, the electrical spring
  ["faraday-generator",   "em"],            // Faraday induction — Φ/EMF on the 2-panel stack, the AC generator
  // Waves & optics
  ["standing-wave",       "waves"],         // standing waves on a string — opens Waves & optics (the 6th instrument)
  // Modern physics
  ["decay",               "modern"],        // radioactive decay — opens Modern (the N / dN/dt 2-panel stack)
];
