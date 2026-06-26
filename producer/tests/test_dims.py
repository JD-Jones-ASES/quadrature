"""Self-tests for the dimensional layer (sympy.physics.units semi-private API is pinned)."""

import pytest
import sympy as sp

from quadrature_producer import BuildError
from quadrature_producer.dims import check_homogeneous, dim_vector, parse_unit


def test_parse_known_units():
    assert parse_unit("1", "t") == sp.S.One
    assert parse_unit("m/s**2", "t") is not None
    assert parse_unit("N", "t") is not None


def test_unknown_unit_fails():
    with pytest.raises(BuildError):
        parse_unit("smoot", "t")


def test_dim_vector_orders_LMT():
    # velocity m/s -> [L=1, M=0, T=-1, ...]
    vec = dim_vector(parse_unit("m/s", "t"), "t")
    assert vec[0] == 1.0 and vec[2] == -1.0
    # acceleration m/s^2 -> T=-2
    assert dim_vector(parse_unit("m/s**2", "t"), "t")[2] == -2.0


def test_homogeneous_passes_and_inhomogeneous_fails():
    x0, v0, a, t = sp.symbols("x0 v0 a t")
    um = {x0: parse_unit("m", "c"), v0: parse_unit("m/s", "c"),
          a: parse_unit("m/s**2", "c"), t: parse_unit("s", "c")}
    # x = x0 + v0 t + a t^2/2 is homogeneous (all metres)
    check_homogeneous(x0 + v0 * t + a * t**2 / 2, um, "ok")
    # adding a bare time to a length is not
    with pytest.raises(BuildError):
        check_homogeneous(x0 + t, um, "bad")
