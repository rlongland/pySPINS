"""Tests for amplitude propagation through apparatus networks (no Qt)."""

import numpy as np
import pytest

from pyspins.physics.network import LOST, outcome_probabilities
from pyspins.physics.operators import axis_from_label, eigenstates, rotation_operator
from pyspins.physics.states import SpinState


class Gun:
    pass


class Analyzer:
    def __init__(self, axis="+z", coherent_mode=True):
        self.axis = axis_from_label(axis)
        self.coherent_mode = coherent_mode

    def transfer(self, vector, s):
        _, evecs = eigenstates(s, self.axis)
        return [ev * np.vdot(ev, vector) for ev in evecs]


class Magnet:
    def __init__(self, beta):
        self.beta = beta

    def transfer(self, vector, s):
        return [rotation_operator(s, np.array([1.0, 0.0, 0.0]), self.beta) @ vector]


class Counter:
    def transfer(self, vector, s):
        return None


PLUS_Z = SpinState(SpinState.HALF_PLUS_Z, 0.5)


def test_experiment_1_single_analyzer():
    gun, sg, up, down = Gun(), Analyzer("+z"), Counter(), Counter()
    edges = [(gun, 0, sg), (sg, 0, up), (sg, 1, down)]
    probs = outcome_probabilities(gun, PLUS_Z, edges)
    assert probs[up] == pytest.approx(1.0)
    assert down not in probs


def test_blocked_output_is_lost():
    gun, sg, up = Gun(), Analyzer("+x"), Counter()
    probs = outcome_probabilities(gun, PLUS_Z, [(gun, 0, sg), (sg, 0, up)])
    assert probs[up] == pytest.approx(0.5)
    assert probs[LOST] == pytest.approx(0.5)


def test_unconnected_gun_is_lost():
    assert outcome_probabilities(Gun(), PLUS_Z, []) == {LOST: 1.0}


def test_experiment_3_sequential_analyzers_match_collapse():
    gun, z1, x, z2 = Gun(), Analyzer("+z"), Analyzer("+x"), Analyzer("+z")
    c1, c2, c3, c4 = Counter(), Counter(), Counter(), Counter()
    edges = [
        (gun, 0, z1), (z1, 0, x), (z1, 1, c1),
        (x, 0, z2), (x, 1, c2),
        (z2, 0, c3), (z2, 1, c4),
    ]
    probs = outcome_probabilities(gun, PLUS_Z, edges)
    assert c1 not in probs
    assert probs[c2] == pytest.approx(0.5)
    assert probs[c3] == pytest.approx(0.25)
    assert probs[c4] == pytest.approx(0.25)


def _recombination(coherent):
    """Gun(+z) → SGz(+) → SGx (both outputs into) → SGz → two counters."""
    gun, z1, x, z2 = Gun(), Analyzer("+z"), Analyzer("+x"), Analyzer("+z", coherent)
    up, down = Counter(), Counter()
    edges = [
        (gun, 0, z1), (z1, 0, x),
        (x, 0, z2), (x, 1, z2),
        (z2, 0, up), (z2, 1, down),
    ]
    return outcome_probabilities(gun, PLUS_Z, edges), up, down


def test_experiment_4_coherent_recombination():
    probs, up, down = _recombination(coherent=True)
    assert probs[up] == pytest.approx(1.0)
    assert down not in probs


def test_experiment_4_incoherent_recombination():
    probs, up, down = _recombination(coherent=False)
    assert probs[up] == pytest.approx(0.5)
    assert probs[down] == pytest.approx(0.5)


def test_magnet_in_one_path_gives_spinor_sign():
    """A 2π rotation flips the sign of one path, turning |+z⟩ into |−z⟩."""
    gun, x, mag, z = Gun(), Analyzer("+x"), Magnet(2 * np.pi), Analyzer("+z")
    up, down = Counter(), Counter()
    edges = [
        (gun, 0, x), (x, 0, mag), (x, 1, z), (mag, 0, z),
        (z, 0, up), (z, 1, down),
    ]
    probs = outcome_probabilities(gun, PLUS_Z, edges)
    assert probs[down] == pytest.approx(1.0)
    assert up not in probs


def test_spin_one_partial_recombination_projects_onto_subspace():
    state = SpinState(SpinState.ONE_PLUS, 1.0)
    gun, x, z = Gun(), Analyzer("+x"), Analyzer("+z")
    lower, c_plus, c_zero, c_minus = Counter(), Counter(), Counter(), Counter()
    edges = [
        (gun, 0, x), (x, 0, z), (x, 1, z), (x, 2, lower),
        (z, 0, c_plus), (z, 1, c_zero), (z, 2, c_minus),
    ]
    probs = outcome_probabilities(gun, state, edges)

    _, xvecs = eigenstates(1.0, axis_from_label("+x"))
    minus_x = xvecs[2]
    kept = state.vector - minus_x * np.vdot(minus_x, state.vector)
    assert probs[lower] == pytest.approx(0.25)
    for counter, amp in zip((c_plus, c_zero, c_minus), kept):
        assert probs.get(counter, 0.0) == pytest.approx(abs(amp) ** 2)


def test_loop_raises():
    gun, a, b = Gun(), Analyzer(), Analyzer()
    with pytest.raises(ValueError):
        outcome_probabilities(gun, PLUS_Z, [(gun, 0, a), (a, 0, b), (b, 0, a)])
