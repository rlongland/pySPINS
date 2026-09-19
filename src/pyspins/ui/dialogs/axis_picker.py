"""Axis selection dialog for Stern-Gerlach analyzers."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDoubleSpinBox, QPushButton, QDialogButtonBox
)
from PySide6.QtCore import Qt


class AxisPickerDialog(QDialog):
    """Dialog for selecting measurement axis for Stern-Gerlach analyzers.

    Supports six standard axes (+z, -z, +x, -x, +y, -y) and custom angle φ
    in the x-y plane (θ=90°).
    """

    def __init__(self, current_axis: str = "+z", current_phi: float = 0.0, parent=None):
        """Initialize axis picker dialog.

        Args:
            current_axis: Initial axis selection ("+z", "-z", "+x", "-x", "+y", "-y", "custom")
            current_phi: Initial phi angle in degrees (0-360) for custom axis
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Select Measurement Axis")
        self.setModal(True)
        self.resize(350, 150)

        # Store current selections
        self._current_axis = current_axis
        self._current_phi = current_phi

        # Main layout
        layout = QVBoxLayout(self)

        # Axis selection combo box
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Measurement Axis:"))

        self._combo = QComboBox()
        self._combo.addItems(["+z", "-z", "+x", "-x", "+y", "-y", "custom φ"])

        # Set current selection
        if current_axis == "custom":
            self._combo.setCurrentText("custom φ")
        else:
            self._combo.setCurrentText(current_axis)

        self._combo.currentTextChanged.connect(self._on_axis_changed)
        combo_layout.addWidget(self._combo)
        layout.addLayout(combo_layout)

        # Custom phi angle spinbox (only visible when "custom φ" selected)
        phi_layout = QHBoxLayout()
        self._phi_label = QLabel("Angle φ (degrees):")
        phi_layout.addWidget(self._phi_label)

        self._phi_spin = QDoubleSpinBox()
        self._phi_spin.setRange(0.0, 360.0)
        self._phi_spin.setSingleStep(1.0)
        self._phi_spin.setDecimals(1)
        self._phi_spin.setValue(current_phi)
        self._phi_spin.setSuffix("°")
        phi_layout.addWidget(self._phi_spin)
        layout.addLayout(phi_layout)

        # Show/hide phi controls based on initial selection
        self._update_phi_visibility()

        # Standard OK/Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Add help text
        help_label = QLabel(
            "Standard axes measure spin along cardinal directions.\n"
            "Custom φ allows arbitrary angle in the x-y plane (equatorial)."
        )
        help_label.setStyleSheet("color: #666; font-size: 9pt;")
        help_label.setWordWrap(True)
        layout.insertWidget(0, help_label)

    def _on_axis_changed(self, text: str):
        """Update visibility of phi controls when axis selection changes."""
        self._update_phi_visibility()

    def _update_phi_visibility(self):
        """Show phi spinbox only when 'custom φ' is selected."""
        is_custom = self._combo.currentText() == "custom φ"
        self._phi_label.setVisible(is_custom)
        self._phi_spin.setVisible(is_custom)

    def get_axis(self) -> tuple[str, float]:
        """Get the selected axis configuration.

        Returns:
            Tuple of (axis_label, phi_deg) where:
            - axis_label is "+z", "-z", "+x", "-x", "+y", "-y", or "custom"
            - phi_deg is the angle in degrees (0-360) for custom axis, 0.0 for standard axes
        """
        text = self._combo.currentText()

        # Convert "custom φ" display text to "custom" internal label
        if text == "custom φ":
            axis_label = "custom"
            phi_deg = self._phi_spin.value()
        else:
            axis_label = text
            phi_deg = 0.0

        return (axis_label, phi_deg)
