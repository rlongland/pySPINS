"""Spin state representation."""

from __future__ import annotations
import numpy as np


class SpinState:
    """Normalized complex spin-state vector in the z-basis.

    s=0.5: ℂ² with basis |+z⟩=[1,0], |−z⟩=[0,1]
    s=1.0: ℂ³ with basis |+1⟩=[1,0,0], |0⟩=[0,1,0], |−1⟩=[0,0,1]
    """

    # ------------------------------------------------------------------
    # Spin-1/2 standard basis states
    # ------------------------------------------------------------------
    HALF_PLUS_Z  = np.array([1, 0], dtype=complex)
    HALF_MINUS_Z = np.array([0, 1], dtype=complex)
    HALF_PLUS_X  = np.array([1,  1], dtype=complex) / np.sqrt(2)
    HALF_MINUS_X = np.array([1, -1], dtype=complex) / np.sqrt(2)
    HALF_PLUS_Y  = np.array([1,  1j], dtype=complex) / np.sqrt(2)
    HALF_MINUS_Y = np.array([1, -1j], dtype=complex) / np.sqrt(2)

    # ------------------------------------------------------------------
    # Spin-1 standard basis states
    # ------------------------------------------------------------------
    ONE_PLUS  = np.array([1, 0, 0], dtype=complex)
    ONE_ZERO  = np.array([0, 1, 0], dtype=complex)
    ONE_MINUS = np.array([0, 0, 1], dtype=complex)

    def __init__(self, vector: np.ndarray, s: float) -> None:
        if s not in (0.5, 1.0):
            raise ValueError(f"s must be 0.5 or 1.0, got {s}")
        expected_dim = int(2 * s + 1)
        arr = np.asarray(vector, dtype=complex).ravel()
        if arr.shape != (expected_dim,):
            raise ValueError(
                f"State vector for s={s} must have dimension {expected_dim}, "
                f"got {arr.shape[0]}"
            )
        self.s = s
        self.vector = arr.copy()
        self._normalize()

    def _normalize(self) -> None:
        norm = np.linalg.norm(self.vector)
        if norm < 1e-15:
            raise ValueError("Cannot normalize a zero vector")
        self.vector /= norm

    @property
    def dim(self) -> int:
        return int(2 * self.s + 1)

    def inner(self, other: SpinState) -> complex:
        """⟨self|other⟩ — conjugate-linear in self."""
        return complex(np.vdot(self.vector, other.vector))

    def __repr__(self) -> str:
        return f"SpinState(s={self.s}, vector={self.vector})"
