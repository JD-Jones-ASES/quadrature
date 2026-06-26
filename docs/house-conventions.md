# House conventions

Baked into the producer and the player. Changing any of these is an ADR-level decision.

## Units & constants

- **Metric (SI) throughout.** Lengths in metres, time in seconds, mass in kilograms.
- **`g = −10 m/s²`** — a deliberate simplification of 9.81 for clean arithmetic. It is an *author-asserted
  model assumption* (it shows on the faithful-model badge), never a machine-derived fact. Stored as
  `constants.g = -10` in every scenario.
- The value carries its **sign**. We never write "`g = 10`, downward"; we write `g = −10` and let the sign do
  the work.

## Coordinates

- **Up is positive.** This is the single most important rigor target — students get the sign wrong precisely
  because they treat "down" as the default positive. With up positive, gravity is negative everywhere, the
  velocity of a rising ball is positive, and the apex is where `v = 0` while `a` is still `−10`.

## Sign rigor (the calculus-grounded fix)

- An object **speeds up** exactly when velocity and acceleration **share a sign**, and **slows down** when they
  oppose — i.e. the sign of `d|v|/dt` is the sign of `v·a`.
- On the way up (`v > 0`, `a < 0`): slowing. At the apex (`v = 0`): `a ≠ 0`. On the way down (`v < 0`,
  `a < 0`): speeding up.
- "Negative velocity" means *moving in the negative direction* (downward), not "slowing down." The player
  states this explicitly wherever sign appears.

## Notation

- Initial values: `x₀`, `v₀`. Time `t ≥ 0`. Acceleration `a`.
- Algebra register formulas (constant `a`): `v = v₀ + at`, `x = x₀ + v₀t + ½at²`, `v² = v₀² + 2a(x − x₀)`.
- Calculus register: `v(t) = ∫a dt`, `x(t) = ∫v dt`; the algebra formula is shown *emerging* from the integral.

## Regimes

Every scenario and formula declares a `regime` (1/2/3). See [regime-map.md](./regime-map.md) and ADR-0006.
