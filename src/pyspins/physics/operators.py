"""Spin operators: Pauli matrices, spin-1 J matrices, rotation operators."""

from __future__ import annotations
import numpy as np

# ------------------------------------------------------------------
# Spin-1/2 operators  (S = σ/2, units ℏ=1)
# ------------------------------------------------------------------
SIGMA_X = np.array([[0, 1],  [1,  0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j],[1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0],  [0, -1]], dtype=complex)

S_HALF_X = SIGMA_X / 2
S_HALF_Y = SIGMA_Y / 2
S_HALF_Z = SIGMA_Z / 2

# ------------------------------------------------------------------
# Spin-1 operators  (J matrices for j=1, units ℏ=1)
# ------------------------------------------------------------------
_s2 = np.sqrt(2)
J1_X = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / _s2
J1_Y = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / _s2
J1_Z = np.diag([1.0, 0.0, -1.0]).astype(complex)


def spin_operator(s: float, axis: np.ndarray) -> np.ndarray:
    """Return the spin operator n̂·S for a unit vector axis=(nx,ny,nz)."""
    nx, ny, nz = axis
    if s == 0.5:
        return nx * S_HALF_X + ny * S_HALF_Y + nz * S_HALF_Z
    else:
        return nx * J1_X + ny * J1_Y + nz * J1_Z


def eigenstates(
    s: float, axis: np.ndarray
) -> tuple[list[float], list[np.ndarray]]:
    """Eigenvalues and eigenvectors of n̂·S, sorted in descending order (+s first).

    Returns (eigenvalues, eigenvectors) where each eigenvector is a 1-D array.
    """
    op = spin_operator(s, axis)
    vals, vecs = np.linalg.eigh(op)
    order = np.argsort(vals)[::-1]
    return [float(vals[i].real) for i in order], [vecs[:, i] for i in order]


def rotation_operator(s: float, axis: np.ndarray, angle: float) -> np.ndarray:
    """Rotation operator exp(−i · angle · n̂·S).

    Computed via eigendecomposition — exact for both spin-1/2 (2×2) and spin-1 (3×3).
    """
    op = spin_operator(s, axis)
    vals, vecs = np.linalg.eigh(op)
    exp_diag = np.exp(-1j * angle * vals)
    return vecs @ np.diag(exp_diag) @ vecs.conj().T


def axis_from_label(label: str, phi_deg: float = 0.0) -> np.ndarray:
    """Convert an axis label to a unit vector.

    Standard labels: +z, -z, +x, -x, +y, -y.
    'custom' uses phi_deg (angle in x-y plane, theta=90°).
    """
    _table: dict[str, np.ndarray] = {
        "+z": np.array([0.0, 0.0,  1.0]),
        "-z": np.array([0.0, 0.0, -1.0]),
        "+x": np.array([ 1.0, 0.0, 0.0]),
        "-x": np.array([-1.0, 0.0, 0.0]),
        "+y": np.array([0.0,  1.0, 0.0]),
        "-y": np.array([0.0, -1.0, 0.0]),
    }
    if label in _table:
        return _table[label]
    phi = np.deg2rad(phi_deg)
    return np.array([np.cos(phi), np.sin(phi), 0.0])
