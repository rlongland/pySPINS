"""Particle gun component - emits particles in a specified spin state."""

import numpy as np
from PySide6.QtWidgets import QGraphicsSceneMouseEvent
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath, QPolygonF
from PySide6.QtCore import QPointF, QRectF
from pyspins.physics.states import SpinState
from .base import ApparatusItem

# Map known state vectors to Dirac-notation labels
_STATE_LABELS = {
    SpinState.HALF_PLUS_Z.tobytes():  "|+z⟩",
    SpinState.HALF_MINUS_Z.tobytes(): "|-z⟩",
    SpinState.HALF_PLUS_X.tobytes():  "|+x⟩",
    SpinState.HALF_MINUS_X.tobytes(): "|-x⟩",
    SpinState.HALF_PLUS_Y.tobytes():  "|+y⟩",
    SpinState.HALF_MINUS_Y.tobytes(): "|-y⟩",
    SpinState.ONE_PLUS.tobytes():     "|+1⟩",
    SpinState.ONE_ZERO.tobytes():     "| 0⟩",
    SpinState.ONE_MINUS.tobytes():    "|-1⟩",
}


def _state_label(vec: np.ndarray) -> str:
    return _STATE_LABELS.get(vec.tobytes(), "|ψ⟩")


class ParticleGun(ApparatusItem):
    """
    Particle gun that emits particles in a specified spin state.

    Drawn as an ion-source shape: trapezoidal body with a triangular nozzle
    pointing right toward the output port.
    """

    # Visual style per Req 25
    COLOR = "#1a237e"  # Dark blue

    # Ion-source geometry (fits inside the 80×50 bounding box)
    _BODY_RIGHT = 58   # where the trapezoid body ends
    _TAPER_TOP  = 12   # top of the tapered body at the right edge
    _TAPER_BOT  = 38   # bottom of the tapered body at the right edge
    _TIP_X      = 78   # nozzle tip (leave 2px gap before the port circle)

    def __init__(self, x: float = 0, y: float = 0):
        """
        Initialize particle gun.

        Args:
            x: Initial x position on canvas
            y: Initial y position on canvas
        """
        super().__init__(label="", color=self.COLOR, x=x, y=y)

        # Default state: spin-1/2 |+z⟩
        self._spin_type = 0.5
        self._initial_state_vector = SpinState.HALF_PLUS_Z

        # Gun has no input ports, one output port (right side)
        self.input_ports = []
        self.output_ports = []

        self._refresh_label()

    def emit(self) -> SpinState:
        """Return the spin state of an emitted particle."""
        return SpinState(self._initial_state_vector, self._spin_type)

    def set_spin_type(self, s: float):
        if s not in (0.5, 1.0):
            raise ValueError("Spin type must be 0.5 or 1.0")
        self._spin_type = s
        if s == 0.5:
            self._initial_state_vector = SpinState.HALF_PLUS_Z
        else:
            self._initial_state_vector = SpinState.ONE_PLUS
        self._refresh_label()

    def set_initial_state(self, state_vector: np.ndarray):
        self._initial_state_vector = state_vector
        self._refresh_label()

    def _center_text(self):
        """Center text within the trapezoidal body, not the full bounding box."""
        text_rect = self._text_item.boundingRect()
        x = (self._BODY_RIGHT - text_rect.width()) / 2
        y = (self.HEIGHT - text_rect.height()) / 2
        self._text_item.setPos(x, y)

    def _refresh_label(self):
        """Update text to show spin type and state label."""
        s_str = "½" if self._spin_type == 0.5 else "1"
        state_str = _state_label(self._initial_state_vector)
        self.set_label(f"s={s_str}\n{state_str}")

    def paint(self, painter, option, widget=None):
        """Draw ion-source shape: trapezoidal body + triangular nozzle."""
        H = self.HEIGHT
        br = self._BODY_RIGHT
        tt = self._TAPER_TOP
        tb = self._TAPER_BOT
        tip = self._TIP_X
        mid = H / 2

        # Body: rounded trapezoid (left rectangle + tapered right side)
        body = QPainterPath()
        body.moveTo(8, 0)
        body.arcTo(QRectF(0, 0, 16, 16), 90, 90)        # top-left corner
        body.lineTo(0, H - 8)
        body.arcTo(QRectF(0, H - 16, 16, 16), 180, 90)  # bottom-left corner
        body.lineTo(br, tb)
        body.lineTo(br, tt)
        body.closeSubpath()

        painter.setBrush(QBrush(self._color))
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawPath(body)

        # Nozzle: filled triangle pointing right
        nozzle = QPolygonF([
            QPointF(br, tt),
            QPointF(tip, mid),
            QPointF(br, tb),
        ])
        painter.setBrush(QBrush(self._color.lighter(130)))
        painter.setPen(QPen(QColor("#000000"), 2))
        painter.drawPolygon(nozzle)

    def get_spin_type(self) -> float:
        """Get the current spin type.

        Returns:
            Spin quantum number (0.5 or 1.0)
        """
        return self._spin_type

    def get_initial_state_vector(self) -> np.ndarray:
        """Get the current initial state vector.

        Returns:
            Complex numpy array representing the state
        """
        return self._initial_state_vector.copy()

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent):
        """Handle double-click to open state picker dialog."""
        from pyspins.ui.dialogs import StatePickerDialog

        dialog = StatePickerDialog(
            current_spin_type=self._spin_type,
            current_state_vector=self._initial_state_vector,
            parent=None
        )

        if dialog.exec():
            spin_type, state_vector = dialog.get_state()
            self.set_spin_type(spin_type)
            self.set_initial_state(state_vector)

        # Don't propagate to parent
        event.accept()
