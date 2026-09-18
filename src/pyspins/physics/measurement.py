"""Projective quantum measurement, state collapse, and batch simulation."""

from __future__ import annotations
import numpy as np
from .states import SpinState
from .operators import eigenstates


def probabilities(
    state: SpinState, axis: np.ndarray
) -> list[tuple[float, float]]:
    """Return [(eigenvalue, probability), ...] in descending eigenvalue order.

    Deterministic — no random sampling.
    """
    evals, evecs = eigenstates(state.s, axis)
    probs = [float(abs(np.vdot(ev, state.vector)) ** 2) for ev in evecs]
    total = sum(probs)
    return [(evals[i], probs[i] / total) for i in range(len(evals))]


def measure(
    state: SpinState, axis: np.ndarray
) -> tuple[float, SpinState]:
    """Single projective measurement along axis.

    Returns (eigenvalue, post-measurement SpinState) drawn from the Born distribution.
    """
    evals, evecs = eigenstates(state.s, axis)
    probs = np.array([abs(np.vdot(ev, state.vector)) ** 2 for ev in evecs])
    probs /= probs.sum()
    idx = int(np.random.choice(len(evals), p=probs))
    return evals[idx], SpinState(evecs[idx], state.s)


def batch_measure(
    state: SpinState, axis: np.ndarray, n: int = 10_000
) -> dict[float, int]:
    """Run n independent measurements; return {eigenvalue: count}.

    Uses numpy.random.multinomial for efficiency — O(components), not O(particles).
    """
    evals, evecs = eigenstates(state.s, axis)
    probs = np.array([abs(np.vdot(ev, state.vector)) ** 2 for ev in evecs])
    probs /= probs.sum()
    counts_arr = np.random.multinomial(n, probs)
    return {evals[i]: int(counts_arr[i]) for i in range(len(evals))}
