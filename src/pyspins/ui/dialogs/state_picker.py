"""State selection dialog for particle gun configuration."""

import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QRadioButton, QButtonGroup, QGroupBox, QGridLayout,
    QLineEdit, QDialogButtonBox
)
from PySide6.QtCore import Qt
from pyspins.physics.states import UNKNOWN_STATES, SpinState


class StatePickerDialog(QDialog):
    """Dialog for selecting initial spin state for particle gun.

    Supports spin-1/2 and spin-1 preset states, custom state entry,
    and unknown states (A, B, C, D) for pedagogical purposes.
    """

    # Preset state labels for each spin type
    PRESET_HALF = ["+z", "-z", "+x", "-x", "+y", "-y", "custom", "A", "B", "C", "D"]
    PRESET_ONE = ["+1", "0", "-1", "custom"]


    def __init__(self, current_spin_type: float = 0.5, current_state_vector=None,
                 current_unknown: str | None = None, parent=None):
        """Initialize state picker dialog.

        Args:
            current_spin_type: Initial spin type (0.5 or 1.0)
            current_state_vector: Initial state vector (numpy array), or None for default
            current_unknown: "A"–"D" if the current state is an unknown one
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Select Initial Spin State")
        self.setModal(True)
        self.resize(400, 350)

        # Store current selections
        self._current_spin_type = current_spin_type
        self._current_state_vector = current_state_vector
        self._current_unknown = current_unknown

        # Main layout
        layout = QVBoxLayout(self)

        # Help text
        help_label = QLabel(
            "Configure the initial spin state emitted by the particle gun.\n"
            "Choose spin type (1/2 or 1) and select a preset or custom state."
        )
        help_label.setStyleSheet("color: #666; font-size: 9pt;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        # Spin type selection
        spin_type_group = QGroupBox("Spin Type")
        spin_type_layout = QHBoxLayout()

        self._spin_half_radio = QRadioButton("Spin-1/2")
        self._spin_one_radio = QRadioButton("Spin-1")

        self._spin_button_group = QButtonGroup()
        self._spin_button_group.addButton(self._spin_half_radio, 0)
        self._spin_button_group.addButton(self._spin_one_radio, 1)

        # Set current selection
        if current_spin_type == 0.5:
            self._spin_half_radio.setChecked(True)
        else:
            self._spin_one_radio.setChecked(True)

        self._spin_button_group.buttonClicked.connect(self._on_spin_type_changed)

        spin_type_layout.addWidget(self._spin_half_radio)
        spin_type_layout.addWidget(self._spin_one_radio)
        spin_type_group.setLayout(spin_type_layout)
        layout.addWidget(spin_type_group)

        # State selection combo box
        state_layout = QHBoxLayout()
        state_layout.addWidget(QLabel("State:"))

        self._state_combo = QComboBox()
        self._state_combo.currentTextChanged.connect(self._on_state_changed)
        state_layout.addWidget(self._state_combo)
        layout.addLayout(state_layout)

        # Custom state entry fields (only visible when "custom" selected)
        self._custom_group = QGroupBox("Custom State Vector")
        custom_layout = QGridLayout()

        # Create entry fields for each component
        # Spin-1/2 needs 2 components, spin-1 needs 3
        # We'll create 3 and show/hide as needed
        self._custom_entries = []
        for i in range(3):
            label = QLabel(f"Component {i}:")
            real_label = QLabel("Real:")
            real_entry = QLineEdit("0.0")
            imag_label = QLabel("Imag:")
            imag_entry = QLineEdit("0.0")

            custom_layout.addWidget(label, i, 0)
            custom_layout.addWidget(real_label, i, 1)
            custom_layout.addWidget(real_entry, i, 2)
            custom_layout.addWidget(imag_label, i, 3)
            custom_layout.addWidget(imag_entry, i, 4)

            self._custom_entries.append({
                'label': label,
                'real_label': real_label,
                'real': real_entry,
                'imag_label': imag_label,
                'imag': imag_entry
            })

        self._custom_group.setLayout(custom_layout)
        layout.addWidget(self._custom_group)

        # Standard OK/Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Initialize state combo box and visibility
        self._update_state_combo()
        self._update_custom_visibility()

    def _on_spin_type_changed(self):
        """Update state combo box when spin type selection changes."""
        self._update_state_combo()
        self._update_custom_visibility()

    def _on_state_changed(self, text: str):
        """Update visibility of custom entry fields when state selection changes."""
        self._update_custom_visibility()

    def _update_state_combo(self):
        """Populate state combo box based on current spin type."""
        # Clear existing items
        self._state_combo.clear()

        # Add items based on spin type
        if self._spin_half_radio.isChecked():
            self._state_combo.addItems(self.PRESET_HALF)
        else:
            self._state_combo.addItems(self.PRESET_ONE)

        self._select_current_state()

    def _select_current_state(self):
        """Preselect the state the gun is currently emitting."""
        if self._current_unknown:
            self._state_combo.setCurrentText(self._current_unknown)
            return
        if self._current_state_vector is None:
            return
        for i in range(self._state_combo.count()):
            label = self._state_combo.itemText(i)
            if label in ("custom",) or label in UNKNOWN_STATES:
                continue
            preset = self._preset_vector(label)
            if preset is not None and preset.shape == self._current_state_vector.shape \
                    and np.allclose(preset, self._current_state_vector):
                self._state_combo.setCurrentIndex(i)
                return

    def _preset_vector(self, label: str):
        """State vector for a preset label, or None if it is not a preset."""
        presets = {
            "+z": SpinState.HALF_PLUS_Z, "-z": SpinState.HALF_MINUS_Z,
            "+x": SpinState.HALF_PLUS_X, "-x": SpinState.HALF_MINUS_X,
            "+y": SpinState.HALF_PLUS_Y, "-y": SpinState.HALF_MINUS_Y,
            "+1": SpinState.ONE_PLUS, "0": SpinState.ONE_ZERO, "-1": SpinState.ONE_MINUS,
        }
        return presets.get(label)

    def _update_custom_visibility(self):
        """Show custom entry fields only when 'custom' is selected."""
        is_custom = self._state_combo.currentText() == "custom"
        self._custom_group.setVisible(is_custom)

        # Show/hide third component based on spin type
        if self._spin_half_radio.isChecked():
            # Spin-1/2: only show first 2 components
            for i, entry_dict in enumerate(self._custom_entries):
                visible = (i < 2)
                entry_dict['label'].setVisible(visible)
                entry_dict['real_label'].setVisible(visible)
                entry_dict['real'].setVisible(visible)
                entry_dict['imag_label'].setVisible(visible)
                entry_dict['imag'].setVisible(visible)
        else:
            # Spin-1: show all 3 components
            for entry_dict in self._custom_entries:
                entry_dict['label'].setVisible(True)
                entry_dict['real_label'].setVisible(True)
                entry_dict['real'].setVisible(True)
                entry_dict['imag_label'].setVisible(True)
                entry_dict['imag'].setVisible(True)

    def get_state(self) -> tuple[float, np.ndarray]:
        """Get the selected spin state configuration.

        Returns:
            Tuple of (spin_type, state_vector) where:
            - spin_type is 0.5 or 1.0
            - state_vector is a complex numpy array
        """
        # Determine spin type
        spin_type = 0.5 if self._spin_half_radio.isChecked() else 1.0

        # Get state selection
        state_label = self._state_combo.currentText()

        # Map state label to state vector
        if state_label == "custom":
            # Build custom state vector from entry fields
            dim = 2 if spin_type == 0.5 else 3
            components = []
            for i in range(dim):
                try:
                    real = float(self._custom_entries[i]['real'].text())
                    imag = float(self._custom_entries[i]['imag'].text())
                    components.append(real + 1j * imag)
                except ValueError:
                    # Invalid input, use zero
                    components.append(0.0 + 0.0j)
            state_vector = np.array(components, dtype=complex)

        elif state_label in UNKNOWN_STATES:
            # Unknown state (A, B, C, D)
            state_vector = UNKNOWN_STATES[state_label].copy()

        else:
            default = SpinState.HALF_PLUS_Z if spin_type == 0.5 else SpinState.ONE_PLUS
            preset = self._preset_vector(state_label)
            state_vector = (default if preset is None else preset).copy()

        return (spin_type, state_vector)

    def get_unknown_label(self) -> str | None:
        """Return "A"–"D" if an unknown state was chosen, else None."""
        label = self._state_combo.currentText()
        return label if label in UNKNOWN_STATES else None
