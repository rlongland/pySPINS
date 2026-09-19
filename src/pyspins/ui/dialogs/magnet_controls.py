"""Magnet Controls Dialog

Provides UI for configuring spin rotation magnet β angle (rotation about x-axis).
"""

import math
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QDoubleSpinBox, QDialogButtonBox
)
from PySide6.QtCore import Qt


class MagnetControlsDialog(QDialog):
    """Dialog for setting the rotation angle β of a SpinRotationMagnet component.

    The magnet applies rotation exp(-i * β * Sx / ℏ) about the x-axis.
    β ranges from 0 to 4π radians (0° to 720°).
    """

    def __init__(self, current_beta: float = 0.0, parent=None):
        """Initialize dialog with current beta value.

        Args:
            current_beta: Current rotation angle in radians (0 to 4π)
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Magnet Rotation Control")
        self.resize(400, 200)

        layout = QVBoxLayout(self)

        # Help text
        help_label = QLabel(
            "Set the rotation angle β for the spin rotation magnet.\n"
            "The magnet rotates the spin state about the x-axis: exp(-i β Sx / ℏ)"
        )
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        # Beta label
        beta_label = QLabel("Rotation angle β:")
        layout.addWidget(beta_label)

        # Slider (0 to 4π, using integer steps for slider precision)
        # Slider range: 0 to 4000 (represents 0.000π to 4.000π in steps of 0.001π)
        slider_layout = QHBoxLayout()
        slider_min_label = QLabel("0")
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(4000)  # 4000 steps = 0 to 4π in 0.001π increments
        self._slider.setValue(int(current_beta / math.pi * 1000))  # Convert radians to slider units
        slider_max_label = QLabel("4π")
        slider_layout.addWidget(slider_min_label)
        slider_layout.addWidget(self._slider)
        slider_layout.addWidget(slider_max_label)
        layout.addLayout(slider_layout)

        # Spinbox (precise numeric input in radians)
        spinbox_layout = QHBoxLayout()
        spinbox_label = QLabel("β (radians):")
        self._spinbox = QDoubleSpinBox()
        self._spinbox.setMinimum(0.0)
        self._spinbox.setMaximum(4 * math.pi)
        self._spinbox.setDecimals(4)
        self._spinbox.setSingleStep(0.1)
        self._spinbox.setValue(current_beta)
        self._spinbox.setSuffix(" rad")
        spinbox_layout.addWidget(spinbox_label)
        spinbox_layout.addWidget(self._spinbox)
        spinbox_layout.addStretch()
        layout.addLayout(spinbox_layout)

        # Display β in terms of π for readability
        pi_layout = QHBoxLayout()
        pi_label = QLabel("β (in π):")
        self._pi_display = QLabel(f"{current_beta / math.pi:.3f}π")
        pi_layout.addWidget(pi_label)
        pi_layout.addWidget(self._pi_display)
        pi_layout.addStretch()
        layout.addLayout(pi_layout)

        # OK/Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Connect signals for synchronization
        self._slider.valueChanged.connect(self._on_slider_changed)
        self._spinbox.valueChanged.connect(self._on_spinbox_changed)

    def _on_slider_changed(self, value: int):
        """Update spinbox when slider changes.

        Args:
            value: Slider value (0 to 4000, representing 0 to 4π)
        """
        # Convert slider value to radians: value / 1000 * π
        beta_rad = value / 1000.0 * math.pi

        # Block signals to prevent recursive updates
        self._spinbox.blockSignals(True)
        self._spinbox.setValue(beta_rad)
        self._spinbox.blockSignals(False)

        # Update π display
        self._pi_display.setText(f"{beta_rad / math.pi:.3f}π")

    def _on_spinbox_changed(self, value: float):
        """Update slider when spinbox changes.

        Args:
            value: Beta value in radians
        """
        # Convert radians to slider units: value / π * 1000
        slider_value = int(value / math.pi * 1000)

        # Block signals to prevent recursive updates
        self._slider.blockSignals(True)
        self._slider.setValue(slider_value)
        self._slider.blockSignals(False)

        # Update π display
        self._pi_display.setText(f"{value / math.pi:.3f}π")

    def get_beta(self) -> float:
        """Get the selected rotation angle in radians.

        Returns:
            Beta angle in radians (0 to 4π)
        """
        return self._spinbox.value()
