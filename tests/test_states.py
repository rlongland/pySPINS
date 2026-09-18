import numpy as np
import pytest
from pyspins.physics.states import SpinState


def test_normalization_half():
    s = SpinState(np.array([3, 4], dtype=complex), 0.5)
    assert abs(np.linalg.norm(s.vector) - 1.0) < 1e-12


def test_normalization_one():
    s = SpinState(np.array([1, 2, 3], dtype=complex), 1.0)
    assert abs(np.linalg.norm(s.vector) - 1.0) < 1e-12


def test_z_basis_orthogonality():
    pz = SpinState(SpinState.HALF_PLUS_Z, 0.5)
    mz = SpinState(SpinState.HALF_MINUS_Z, 0.5)
    assert abs(pz.inner(mz)) < 1e-12


def test_x_basis_orthogonality():
    px = SpinState(SpinState.HALF_PLUS_X, 0.5)
    mx = SpinState(SpinState.HALF_MINUS_X, 0.5)
    assert abs(px.inner(mx)) < 1e-12


def test_y_basis_orthogonality():
    py = SpinState(SpinState.HALF_PLUS_Y, 0.5)
    my = SpinState(SpinState.HALF_MINUS_Y, 0.5)
    assert abs(py.inner(my)) < 1e-12


def test_inner_product_self_is_one():
    s = SpinState(np.array([1, 1j], dtype=complex), 0.5)
    assert abs(s.inner(s) - 1.0) < 1e-12


def test_spin1_basis_orthogonality():
    p = SpinState(SpinState.ONE_PLUS, 1.0)
    z = SpinState(SpinState.ONE_ZERO, 1.0)
    m = SpinState(SpinState.ONE_MINUS, 1.0)
    assert abs(p.inner(z)) < 1e-12
    assert abs(p.inner(m)) < 1e-12
    assert abs(z.inner(m)) < 1e-12


def test_wrong_dimension_raises():
    with pytest.raises(ValueError):
        SpinState(np.array([1, 0, 0], dtype=complex), 0.5)


def test_wrong_s_raises():
    with pytest.raises(ValueError):
        SpinState(np.array([1, 0], dtype=complex), 2.0)


def test_zero_vector_raises():
    with pytest.raises(ValueError):
        SpinState(np.array([0, 0], dtype=complex), 0.5)


def test_dim_property():
    assert SpinState(SpinState.HALF_PLUS_Z, 0.5).dim == 2
    assert SpinState(SpinState.ONE_ZERO, 1.0).dim == 3
