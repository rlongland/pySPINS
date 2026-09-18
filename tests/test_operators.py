import numpy as np
import pytest
from pyspins.physics.operators import (
    S_HALF_X, S_HALF_Y, S_HALF_Z,
    J1_X, J1_Y, J1_Z,
    eigenstates, rotation_operator, axis_from_label,
)


def _commutator(A, B):
    return A @ B - B @ A


# ------------------------------------------------------------------
# Spin-1/2 (Pauli / 2)
# ------------------------------------------------------------------

def test_half_commutator_XY():
    """[Sx, Sy] = i Sz"""
    assert np.allclose(_commutator(S_HALF_X, S_HALF_Y), 1j * S_HALF_Z)


def test_half_commutator_YZ():
    """[Sy, Sz] = i Sx"""
    assert np.allclose(_commutator(S_HALF_Y, S_HALF_Z), 1j * S_HALF_X)


def test_half_commutator_ZX():
    """[Sz, Sx] = i Sy"""
    assert np.allclose(_commutator(S_HALF_Z, S_HALF_X), 1j * S_HALF_Y)


def test_half_eigenvalues_z():
    evals, _ = eigenstates(0.5, np.array([0, 0, 1.0]))
    assert np.isclose(evals[0],  0.5)
    assert np.isclose(evals[1], -0.5)


def test_half_eigenvalues_x():
    evals, _ = eigenstates(0.5, np.array([1, 0, 0.0]))
    assert np.isclose(evals[0],  0.5)
    assert np.isclose(evals[1], -0.5)


def test_half_rotation_unitarity():
    R = rotation_operator(0.5, np.array([0, 0, 1.0]), np.pi / 3)
    assert np.allclose(R @ R.conj().T, np.eye(2), atol=1e-12)


def test_half_rotation_2pi_is_minus_identity():
    """A 2π rotation of a spin-1/2 state gives −I (spinor sign change)."""
    R = rotation_operator(0.5, np.array([0, 0, 1.0]), 2 * np.pi)
    assert np.allclose(R, -np.eye(2), atol=1e-12)


# ------------------------------------------------------------------
# Spin-1 (J matrices)
# ------------------------------------------------------------------

def test_spin1_commutator_XY():
    """[Jx, Jy] = i Jz"""
    assert np.allclose(_commutator(J1_X, J1_Y), 1j * J1_Z)


def test_spin1_commutator_YZ():
    """[Jy, Jz] = i Jx"""
    assert np.allclose(_commutator(J1_Y, J1_Z), 1j * J1_X)


def test_spin1_commutator_ZX():
    """[Jz, Jx] = i Jy"""
    assert np.allclose(_commutator(J1_Z, J1_X), 1j * J1_Y)


def test_spin1_eigenvalues_z():
    evals, _ = eigenstates(1.0, np.array([0, 0, 1.0]))
    assert np.allclose(sorted(evals, reverse=True), [1.0, 0.0, -1.0])


def test_spin1_rotation_unitarity():
    R = rotation_operator(1.0, np.array([1, 0, 0.0]), np.pi / 4)
    assert np.allclose(R @ R.conj().T, np.eye(3), atol=1e-12)


def test_spin1_rotation_4pi_is_identity():
    """A 4π rotation of a spin-1 state gives +I."""
    R = rotation_operator(1.0, np.array([0, 1, 0.0]), 4 * np.pi)
    assert np.allclose(R, np.eye(3), atol=1e-12)


# ------------------------------------------------------------------
# axis_from_label
# ------------------------------------------------------------------

def test_axis_label_z():
    assert np.allclose(axis_from_label("+z"), [0, 0, 1])
    assert np.allclose(axis_from_label("-z"), [0, 0, -1])


def test_axis_label_x():
    assert np.allclose(axis_from_label("+x"), [1, 0, 0])
    assert np.allclose(axis_from_label("-x"), [-1, 0, 0])


def test_axis_label_custom_90():
    v = axis_from_label("custom", phi_deg=90.0)
    assert np.allclose(v, [0, 1, 0], atol=1e-12)


def test_axis_label_custom_45():
    v = axis_from_label("custom", phi_deg=45.0)
    assert np.allclose(v, [1 / np.sqrt(2), 1 / np.sqrt(2), 0], atol=1e-12)
