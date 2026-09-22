"""Propagation of spin amplitudes through an apparatus network.

Rather than collapsing the state at every analyzer, the particle's amplitude is
carried along every path at once. An analyzer splits the incoming amplitude into
its projections onto each eigenstate (one per output), a magnet applies a unitary,
and a counter is where the particle is finally detected. Beams that meet at one
input add as amplitudes (coherent) or, if the receiving node has
``coherent_mode = False``, as probabilities (incoherent: which-path is measured).

For apparatus without recombination this reproduces sequential collapse exactly,
since the output paths of an analyzer are orthogonal and never meet again.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from .states import SpinState

#: Terminal key for particles leaving through an unconnected output (blocked beam).
LOST = None

_EPS = 1e-12


def outcome_probabilities(source, state: SpinState, edges) -> dict:
    """Exact probability that a particle emitted by ``source`` ends at each terminal.

    Args:
        source: The emitting node; its single output is index 0.
        state: The emitted spin state.
        edges: Iterable of ``(src, output_index, dest)`` connections.

    Every node downstream of ``source`` must provide ``transfer(vector, s)``,
    returning the list of (unnormalized) output amplitudes, one per output index,
    or ``None`` if the node is a terminal detector. A node may define
    ``coherent_mode``; it defaults to coherent.

    Returns:
        ``{terminal: probability}``, including ``LOST`` for blocked beams.
        Probabilities are normalized to sum to 1.

    Raises:
        ValueError: If the connections downstream of ``source`` contain a cycle.
    """
    out_edges: dict = defaultdict(dict)
    for src, idx, dest in edges:
        out_edges[src][idx] = dest

    order = _topological_order(source, out_edges)
    probs: dict = defaultdict(float)

    def pass_through(node, amp, branch):
        """Send ``amp`` through ``node``, depositing outputs into ``branch``."""
        outputs = node.transfer(amp, state.s)
        if outputs is None:
            probs[node] += _norm2(amp)
            return
        for idx, out in enumerate(outputs):
            p = _norm2(out)
            if p < _EPS:
                continue
            dest = out_edges[node].get(idx)
            if dest is None:
                probs[LOST] += p
            else:
                branch.setdefault(dest, []).append(out)

    # A branch is one pure (unnormalized) state spread over locations:
    # {node: [amplitude arriving on each incoming wire]}. The branches together
    # form an incoherent mixture, created by which-path measurements.
    first = out_edges[source].get(0)
    if first is None:
        return {LOST: 1.0}
    branches = [{first: [state.vector.copy()]}]

    for node in order[1:]:
        next_branches = []
        for branch in branches:
            arrivals = branch.pop(node, [])
            if len(arrivals) > 1 and not getattr(node, "coherent_mode", True):
                # Which-path measurement: each incoming beam becomes its own
                # branch, and the rest of the state (not at this node) another.
                next_branches.append(branch)
                for amp in arrivals:
                    piece: dict = {}
                    pass_through(node, amp, piece)
                    next_branches.append(piece)
            else:
                if arrivals:
                    pass_through(node, sum(arrivals), branch)
                next_branches.append(branch)
        branches = [b for b in next_branches if b]

    # Merging non-orthogonal beams into one input is not unitary, so the total
    # can drift from 1; the ideal cases (recombining an analyzer's own outputs)
    # conserve it exactly.
    total = sum(probs.values())
    if total < _EPS:
        return {LOST: 1.0}
    return {k: v / total for k, v in probs.items() if v / total > _EPS}


def _topological_order(source, out_edges) -> list:
    """Nodes reachable from ``source`` in topological order (source first)."""
    order: list = []
    state: dict = {}  # node -> "visiting" | "done"

    def visit(node):
        mark = state.get(node)
        if mark == "done":
            return
        if mark == "visiting":
            raise ValueError("Apparatus contains a loop")
        state[node] = "visiting"
        for dest in out_edges.get(node, {}).values():
            visit(dest)
        state[node] = "done"
        order.append(node)

    visit(source)
    order.reverse()
    return order


def _norm2(v: np.ndarray) -> float:
    return float(np.vdot(v, v).real)
