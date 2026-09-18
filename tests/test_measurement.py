import numpy as np
import pytest
from pyspins.physics.states import SpinState
from pyspins.physics.measurement import probabilities, measure, batch_measure

Z_AXIS = np.array([0, 0, 1.0])
X_AXIS = np.array([1, 0, 0.0])
Y_AXIS = np.array([0, 1, 0.0])


# ------------------------------------------------------------------
# probabilities()
# ------------------------------------------------------------------

def test_probs_sum_to_one_half():
    s = SpinState(np.array([1, 1j], dtype=complex), 0.5)
    ps = probabilities(s, Z_AXIS)
    assert abs(sum(p for _, p in ps) - 1.0) < 1e-12


def test_probs_sum_to_one_spin1():
    s = SpinState(np.array([1, 2, 3], dtype=complex), 1.0)
    ps = probabilities(s, Z_AXIS)
    assert abs(sum(p for _, p in ps) - 1.0) < 1e-12


def test_plus_z_on_sgz_is_certain():
    s = SpinState(SpinState.HALF_PLUS_Z, 0.5)
    ps = dict(probabilities(s, Z_AXIS))
    assert abs(ps[0.5] - 1.0) < 1e-12
    assert abs(ps[-0.5]) < 1e-12


def test_minus_z_on_sgz_is_certain():
    s = SpinState(SpinState.HALF_MINUS_Z, 0.5)
    ps = dict(probabilities(s, Z_AXIS))
    assert abs(ps[-0.5] - 1.0) < 1e-12
    assert abs(ps[0.5]) < 1e-12


def test_plus_z_on_sgx_is_fifty_fifty():
    s = SpinState(SpinState.HALF_PLUS_Z, 0.5)
    ps = dict(probabilities(s, X_AXIS))
    assert abs(ps[0.5] - 0.5) < 1e-12
    assert abs(ps[-0.5] - 0.5) < 1e-12


def test_plus_z_on_sgy_is_fifty_fifty():
    s = SpinState(SpinState.HALF_PLUS_Z, 0.5)
    ps = dict(probabilities(s, Y_AXIS))
    assert abs(ps[0.5] - 0.5) < 1e-12
    assert abs(ps[-0.5] - 0.5) < 1e-12


def test_plus_x_on_sgx_is_certain():
    s = SpinState(SpinState.HALF_PLUS_X, 0.5)
    ps = dict(probabilities(s, X_AXIS))
    assert abs(ps[0.5] - 1.0) < 1e-12


def test_spin1_plus1_on_sgz_is_certain():
    s = SpinState(SpinState.ONE_PLUS, 1.0)
    ps = dict(probabilities(s, Z_AXIS))
    assert abs(ps[1.0] - 1.0) < 1e-12
    assert abs(ps[0.0]) < 1e-12
    assert abs(ps[-1.0]) < 1e-12


# ------------------------------------------------------------------
# measure()
# ------------------------------------------------------------------

def test_measure_returns_eigenvalue():
    s = SpinState(SpinState.HALF_PLUS_Z, 0.5)
    val, post = measure(s, X_AXIS)
    assert val in (0.5, -0.5)


def test_measure_post_state_is_normalized():
    s = SpinState(np.array([1, 1], dtype=complex), 0.5)
    _, post = measure(s, Z_AXIS)
    assert abs(np.linalg.norm(post.vector) - 1.0) < 1e-12


def test_collapse_idempotency():
    """Measuring the same axis twice gives the same eigenvalue with certainty."""
    s = SpinState(np.array([1, 1], dtype=complex), 0.5)
    val, post = measure(s, Z_AXIS)
    ps = dict(probabilities(post, Z_AXIS))
    assert abs(ps[val] - 1.0) < 1e-12


def test_certain_state_always_returns_same_eigenvalue():
    """100 measurements of |+z⟩ along z all return +0.5."""
    s = SpinState(SpinState.HALF_PLUS_Z, 0.5)
    for _ in range(100):
        val, _ = measure(s, Z_AXIS)
        assert val == pytest.approx(0.5)


# ------------------------------------------------------------------
# batch_measure()
# ------------------------------------------------------------------

def test_batch_counts_sum_to_n():
    s = SpinState(SpinState.HALF_PLUS_Z, 0.5)
    counts = batch_measure(s, X_AXIS, n=10_000)
    assert sum(counts.values()) == 10_000


def test_batch_certain_state():
    s = SpinState(SpinState.HALF_PLUS_Z, 0.5)
    counts = batch_measure(s, Z_AXIS, n=1_000)
    assert counts[0.5] == 1_000
    assert counts[-0.5] == 0


def test_batch_fifty_fifty_approx():
    """Statistical test: |+z⟩ on SGx should give ~50% each, within 5σ."""
    rng_state = np.random.get_state()
    np.random.seed(42)
    s = SpinState(SpinState.HALF_PLUS_Z, 0.5)
    counts = batch_measure(s, X_AXIS, n=10_000)
    np.random.set_state(rng_state)
    # 5σ tolerance for n=10000: σ = sqrt(0.25 * 10000) = 50
    assert abs(counts[0.5] - 5000) < 250
    assert abs(counts[-0.5] - 5000) < 250


def test_batch_spin1_counts_sum():
    s = SpinState(SpinState.ONE_ZERO, 1.0)
    counts = batch_measure(s, Z_AXIS, n=5_000)
    assert sum(counts.values()) == 5_000
