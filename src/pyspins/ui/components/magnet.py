"""Spin rotation magnet component - applies rotation to spin states."""

import math
import numpy as np
from PySide6.QtGui import QMouseEvent
from pyspins.physics.operators import rotation_operator
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
        super().__init__(label="Mag\nβ=0", color=self.COLOR, x=x, y=y)

        # Rotation angle in radians (0 = no rotation)
        self.beta = 0.0

        # Magnet has one input port (left), one output port (right)
        # No beam splitting - single path through
        self.input_ports = []
        self.output_ports = []  # Will be populated when Port class exists

    def transfer(self, vector, s: float):
        """Rotate the amplitude by exp(-i β Sx / ℏ) (ℏ = 1)."""
        x_axis = np.array([1.0, 0.0, 0.0])
        return [rotation_operator(s, x_axis, self.beta) @ vector]

    def set_beta(self, beta: float):
        """
        Set the rotation angle and update label.

        Args:
            beta: Rotation angle in radians (0 to 4π)
        """
        self.beta = beta
        # Update label to show beta in terms of π for readability
        beta_pi = beta / math.pi
        self.label = f"Mag\nβ={beta_pi:.2f}π"
        self.update()  # Trigger repaint to show new label

    def get_beta(self) -> float:
        """
        Get the current rotation angle.

        Returns:
            Beta angle in radians (0 to 4π)
        """
        return self.beta

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """
        Handle double-click to open magnet controls dialog.

        Args:
            event: Mouse event
        """
        from pyspins.ui.dialogs import MagnetControlsDialog

        dialog = MagnetControlsDialog(current_beta=self.beta, parent=None)
        if dialog.exec():
            # User accepted - update beta
            new_beta = dialog.get_beta()
            self.set_beta(new_beta)

        event.accept()
