"""Stern-Gerlach analyzer component - measures spin along a specified axis."""

import numpy as np
from pyspins.physics.states import SpinState
from pyspins.physics.measurement import measure
from .base import ApparatusItem


class SternGerlachAnalyzer(ApparatusItem):
    """
    Stern-Gerlach analyzer that performs projective measurement along an axis.

    Has one input port and multiple output ports (2 for spin-1/2, 3 for spin-1).
    Each output corresponds to a different eigenvalue of the measurement.
    """

    # Visual style per Req 25
    COLOR = "#757575"  # Medium grey

    def __init__(self, x: float = 0, y: float = 0, axis_label: str = "+z"):
        """
        Initialize Stern-Gerlach analyzer.

        Args:
            x: Initial x position on canvas
            y: Initial y position on canvas
            axis_label: Measurement axis (+z, -z, +x, -x, +y, -y)
        """
        super().__init__(label=f"SG {axis_label}", color=self.COLOR, x=x, y=y)

        self._axis_label = axis_label
        self._axis_vector = self._axis_from_label(axis_label)

        # Analyzer has one input port (left), multiple output ports (right)
        # Ports will be created in Phase 2 Task 2.5
        self.input_ports = []  # Will be populated when Port class exists
        self.output_ports = []  # Number depends on spin type

        # Coherent recombination mode (Phase 4 feature)
        self.coherent_mode = False

    def simulate(self, state: SpinState, output_index: int = 0) -> SpinState:
        """
        Perform measurement along the configured axis.

        Args:
            state: Incoming SpinState
            output_index: Which output port to simulate (used for deterministic path tracing)

        Returns:
            SpinState: Post-measurement collapsed state
        """
        # Perform projective measurement
        eigenvalue, post_state = measure(state, self._axis_vector)
        return post_state

    def set_axis(self, axis_label: str):
        """
        Set the measurement axis.

        Args:
            axis_label: Axis label (+z, -z, +x, -x, +y, -y, or custom)
        """
        self._axis_label = axis_label
        self._axis_vector = self._axis_from_label(axis_label)
        self.set_label(f"SG {axis_label}")

    def _axis_from_label(self, label: str) -> np.ndarray:
        """
        Convert axis label to unit vector.

        Args:
            label: Axis label string

        Returns:
            Unit vector as numpy array [nx, ny, nz]
        """
        axis_table = {
            "+z": np.array([0, 0, 1.0]),
            "-z": np.array([0, 0, -1.0]),
            "+x": np.array([1, 0, 0.0]),
            "-x": np.array([-1, 0, 0.0]),
            "+y": np.array([0, 1, 0.0]),
            "-y": np.array([0, -1, 0.0]),
        }
        return axis_table.get(label, np.array([0, 0, 1.0]))  # Default to +z

    def get_axis_vector(self) -> np.ndarray:
        """Get the current axis unit vector."""
        return self._axis_vector

    def get_axis_label(self) -> str:
        """Get the current axis label."""
        return self._axis_label
