"""Stern-Gerlach analyzer component - measures spin along a specified axis."""

import numpy as np
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from pyspins.physics.states import SpinState
from pyspins.physics.measurement import measure
from .base import ApparatusItem


class SternGerlachAnalyzer(ApparatusItem):
    """
    Stern-Gerlach analyzer that performs projective measurement along an axis.

    Has one input port and multiple output ports (2 for spin-1/2, 3 for spin-1).
    Each output corresponds to a different eigenvalue of the measurement (Req 26).
    """

    # Visual style per Req 25
    COLOR = "#757575"  # Medium grey

    def __init__(self, x: float = 0, y: float = 0, axis_label: str = "+z", phi_deg: float = 0.0, spin_type: float = 0.5):
        """
        Initialize Stern-Gerlach analyzer.

        Args:
            x: Initial x position on canvas
            y: Initial y position on canvas
            axis_label: Measurement axis (+z, -z, +x, -x, +y, -y, custom)
            phi_deg: Angle in degrees for custom axis (0-360)
            spin_type: Spin type this analyzer is configured for (0.5 or 1.0)
        """
        super().__init__(label=f"SG {axis_label}", color=self.COLOR, x=x, y=y)

        self._axis_label = axis_label
        self._phi_deg = phi_deg
        self._axis_vector = self._axis_from_label(axis_label, phi_deg)
        self._spin_type = spin_type  # Store spin type (Req 26)

        # Analyzer has one input port (left), multiple output ports (right)
        # Ports will be created in Phase 2 Task 2.5
        self.input_ports = []  # Will be populated when Port class exists
        self.output_ports = []  # Number depends on spin type (Req 26)

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

    def set_axis(self, axis_label: str, phi_deg: float = 0.0):
        """
        Set the measurement axis.

        Args:
            axis_label: Axis label (+z, -z, +x, -x, +y, -y, or custom)
            phi_deg: Angle in degrees for custom axis (0-360)
        """
        self._axis_label = axis_label
        self._phi_deg = phi_deg
        self._axis_vector = self._axis_from_label(axis_label, phi_deg)

        # Update label to show custom angle if applicable
        if axis_label == "custom":
            self.set_label(f"SG φ={phi_deg:.0f}°")
        else:
            self.set_label(f"SG {axis_label}")

    def _axis_from_label(self, label: str, phi_deg: float = 0.0) -> np.ndarray:
        """
        Convert axis label to unit vector.

        Args:
            label: Axis label string
            phi_deg: Angle in degrees for custom axis (0-360)

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

        if label in axis_table:
            return axis_table[label]

        # Custom axis: angle phi in x-y plane (theta=90°)
        phi_rad = np.deg2rad(phi_deg)
        return np.array([np.cos(phi_rad), np.sin(phi_rad), 0.0])

    def get_axis_vector(self) -> np.ndarray:
        """Get the current axis unit vector."""
        return self._axis_vector

    def get_axis_label(self) -> str:
        """Get the current axis label."""
        return self._axis_label

    def get_phi(self) -> float:
        """Get the current phi angle in degrees."""
        return self._phi_deg

    def get_spin_type(self) -> float:
        """Get the spin type this analyzer is configured for."""
        return self._spin_type

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """Open axis picker dialog on double-click."""
        from pyspins.ui.dialogs import AxisPickerDialog

        dialog = AxisPickerDialog(self._axis_label, self._phi_deg, parent=None)
        if dialog.exec():
            axis_label, phi_deg = dialog.get_axis()
            self.set_axis(axis_label, phi_deg)

        event.accept()
