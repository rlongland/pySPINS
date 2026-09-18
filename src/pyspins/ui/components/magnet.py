"""Spin rotation magnet component - applies rotation to spin states."""

import numpy as np
from pyspins.physics.states import SpinState
from .base import ApparatusItem


class SpinRotationMagnet(ApparatusItem):
    """
    Spin rotation magnet that applies a rotation about the x-axis.

    For Phase 3 scaffold: basic component with beta=0 (no rotation).
    Phase 4 will add beta slider dialog and full rotation functionality.
    """

    # Visual style per plan Phase 4 specification
    COLOR = "#c62828"  # Red

    def __init__(self, x: float = 0, y: float = 0):
        """
        Initialize spin rotation magnet.

        Args:
            x: Initial x position on canvas
            y: Initial y position on canvas
        """
        super().__init__(label="Mag", color=self.COLOR, x=x, y=y)

        # Rotation angle in radians (0 = no rotation)
        self.beta = 0.0

        # Magnet has one input port (left), one output port (right)
        # No beam splitting - single path through
        self.input_ports = []
        self.output_ports = []  # Will be populated when Port class exists

    def simulate(self, state: SpinState, output_index: int = 0) -> SpinState:
        """
        Apply rotation to the spin state.

        For Phase 3: beta=0, so state passes through unchanged.
        Phase 4 will implement rotation_operator application.

        Args:
            state: Input SpinState to rotate
            output_index: Ignored (magnet has single output)

        Returns:
            SpinState: Rotated state (currently unchanged)
        """
        # Phase 3 stub: pass through unchanged
        # Phase 4 will add:
        # from pyspins.physics.operators import rotation_operator
        # R = rotation_operator(state.s, np.array([1, 0, 0.0]), self.beta)
        # return SpinState(R @ state.vector, state.s)
        return state

    def set_beta(self, beta: float):
        """
        Set the rotation angle.

        Args:
            beta: Rotation angle in radians (0 to 4π)
        """
        self.beta = beta
