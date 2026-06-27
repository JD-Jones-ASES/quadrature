"""Producer models — one per physics scenario type. Each exposes `build(spec) -> Scenario`.

A model owns its governing law, its stepped registers, its proof (regime-1 equivalence or regime-2
governing), and the symbolic x/v/a expressions the graph/closed-form layers consume. build.py dispatches on
the spec's `model` field. The Scenario shape is the contract — see base.py.
"""

from . import (constant_accel, shm, linear_drag, damped_shm, work_energy, pv_work,
               projectile, impulse, rotation, gravity_pe, capacitor_energy, adiabatic,
               moment_of_inertia, coulomb_pe, hydrostatic_force, rotational_work, orbit,
               energy_conservation)

MODELS = {
    "constant-accel": constant_accel.build,
    "shm": shm.build,
    "linear-drag": linear_drag.build,
    "damped-shm": damped_shm.build,
    "work-energy": work_energy.build,
    "pv-work": pv_work.build,
    "projectile": projectile.build,
    "impulse": impulse.build,
    "rotation": rotation.build,
    "gravity-pe": gravity_pe.build,
    "capacitor-energy": capacitor_energy.build,
    "adiabatic": adiabatic.build,
    "moment-of-inertia": moment_of_inertia.build,
    "coulomb-pe": coulomb_pe.build,
    "hydrostatic-force": hydrostatic_force.build,
    "rotational-work": rotational_work.build,
    "orbit": orbit.build,
    "energy-conservation": energy_conservation.build,
}
