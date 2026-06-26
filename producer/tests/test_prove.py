"""The tiered prover must certify true identities and reject false ones."""

import pytest
import sympy as sp

from quadrature_producer import BuildError
from quadrature_producer.prove import SampleDomain, tiered_zero

x, y = sp.symbols("x y", positive=True)
DOM = SampleDomain(bounds={x: (1.0, 9.0), y: (1.0, 9.0)}, positive={x, y})


def test_true_identity_certified():
    # (x+y)^2 - (x^2 + 2xy + y^2) == 0
    tier = tiered_zero((x + y) ** 2 - (x**2 + 2 * x * y + y**2), DOM, "ok", "s1")
    assert tier in {"structural", "simplify", "equals", "exp-rewrite", "numeric"}


def test_trig_identity_certified():
    tiered_zero(sp.sin(x) ** 2 + sp.cos(x) ** 2 - 1, DOM, "trig", "s2")


def test_false_identity_rejected():
    with pytest.raises(BuildError):
        tiered_zero(x**2 - y**2, DOM, "bad", "s3")
