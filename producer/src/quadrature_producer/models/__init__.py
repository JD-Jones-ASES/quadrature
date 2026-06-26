"""Producer models — one per physics scenario type. Each exposes `build(spec) -> Scenario`.

A model owns its governing law, its stepped registers, its proof (regime-1 equivalence or regime-2
governing), and the symbolic x/v/a expressions the graph/closed-form layers consume. build.py dispatches on
the spec's `model` field. The Scenario shape is the contract — see base.py.
"""

from . import constant_accel, shm, linear_drag

MODELS = {
    "constant-accel": constant_accel.build,
    "shm": shm.build,
    "linear-drag": linear_drag.build,
}
