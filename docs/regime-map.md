# Regime map — the breadth scope tracker

The union of a solid algebra-based course with the union of the calculus-based offerings, every topic tagged by
**regime** and by whether the **dual register** is native. This is how we track "covering all topics" and drive
the breadth-first reference fill (ADR-0007). Update the status column as the reference and lessons land.

**Regimes** (ADR-0006): **1** = algebra *is* calculus evaluated (constant integrand) · **2** = calculus does
what algebra cannot (non-constant forces; ODEs) · **3** = algebra-only (no calculus-based counterpart).

**Register** column: *dual* = the offerings ship both an algebra and a calculus version (build both) ·
*algebra* = algebra-only domain (cover at the algebra level; calculus underpinning only where clean).

| Domain | Topic | Register | Regimes | Phase | Status |
|---|---|---|---|---|---|
| Mechanics | Kinematics (constant a) | dual | 1 | 0–1 | lesson + ref |
| Mechanics | Kinematics (non-constant a, drag) | dual | 2 | 1 | lesson + ref |
| Mechanics | Projectile / 2D motion | dual | 1–2 | 1 | lesson (drag-free exact + quadratic-drag numerical) |
| Mechanics | Dynamics / Newton's laws | dual | 1–2 | 1 | ref ✓ |
| Mechanics | Work & energy | dual | 1–2 | 1 | lesson (area: ∫F dx) + ref |
| Mechanics | Momentum & impulse | dual | 1–2 | 1 | lesson (impulse: area ∫F dt) + ref |
| Mechanics | Rotation / rigid bodies | dual | 1–2 | 1 | lesson (angular kinematics) + ref (partial) |
| Mechanics | Simple harmonic motion | dual | 2 | 1 | lesson + ref |
| Mechanics | Gravitation | dual | 2 | 1 | ref ✓ |
| Mechanics | Circular motion | dual | 1 | 1 | ref ✓ |
| E&M | Electrostatics (Coulomb, field) | dual | 1–2 | 2 | — |
| E&M | Gauss / continuous charge | dual | 2 | 2 | — |
| E&M | Electric potential | dual | 1–2 | 2 | — |
| E&M | DC circuits | dual | 1 | 2 | — |
| E&M | Capacitors (incl. RC) | dual | 2 | 2 | — |
| E&M | Magnetism & forces | dual | 1–2 | 2 | — |
| E&M | Induction (Faraday/Lenz) | dual | 2 | 2 | — |
| Fluids | Statics & dynamics | algebra | 3 | 3 | — |
| Thermo | Temperature, heat, kinetic theory | algebra | 3 | 3 | — |
| Thermo | Laws / PV work | algebra | 3 (∫P dV stretch) | 3 | lesson (area: isothermal ∫P dV) + ref (partial) |
| Waves & optics | Waves, sound, superposition | algebra | 3 | 3 | — |
| Waves & optics | Geometric & physical optics | algebra | 3 | 3 | — |
| Modern | Quanta, atom, nuclear | algebra | 3 | 3 | — |

Notes:
- **Fluids** is algebra-only and is *not* in the calculus-based mechanics offering — keep it in the algebra
  register (brief §9).
- The "stretch" calculus underpinnings (e.g. work as `∫P dV`) are optional and only added where they are
  clean; do not force a dual register where one doesn't naturally exist. When they *are* clean, the **area
  instrument** (ADR-0014) is the vehicle: a regime-3 lesson can show the underpinning as the area under a
  curve without claiming a dual register (the isothermal PV-work lesson is the first such).
