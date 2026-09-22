"""Port classes for apparatus component connections."""

from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QPen, QPainterPath


class Port(QGraphicsEllipseItem):
    """
    Base class for apparatus connection ports.

    Ports are 8px diameter circles positioned on component edges.
    Non-interactive in Phase 2; Phase 3 will add wire drawing.
    """

    # Port visual constants (per Req 25)
    PORT_DIAMETER = 8
    PORT_COLOR = "#1565c0"  # Blue

    def __init__(self, parent_item, eigenvalue: float = 0.0):
        """
        Initialize a port.

        Args:
            parent_item: The ApparatusItem this port belongs to
            eigenvalue: The measurement eigenvalue this port represents (for output ports)
        """
        # Create ellipse centered at (0, 0) with PORT_DIAMETER
        radius = self.PORT_DIAMETER / 2
        super().__init__(-radius, -radius, self.PORT_DIAMETER, self.PORT_DIAMETER, parent_item)

        self.eigenvalue = eigenvalue
        self._parent_item = parent_item
        # Connection objects attached to this port. An output port carries at most
        # one; an input port may receive several beams (recombination).
        self.connections = []

        # Visual styling (will be overridden by subclasses)
        self.setPen(QPen(QColor(self.PORT_COLOR), 2))

        # Enable mouse events for wire drawing
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, False)

    # Larger invisible hit area so ports are easier to click
    HIT_RADIUS = 10

    def shape(self):
        path = QPainterPath()
        path.addEllipse(-self.HIT_RADIUS, -self.HIT_RADIUS,
                        self.HIT_RADIUS * 2, self.HIT_RADIUS * 2)
        return path

    def set_position(self, x: float, y: float):
        """
        Set port position relative to parent item.

        Args:
            x: X coordinate relative to parent
            y: Y coordinate relative to parent
        """
        self.setPos(x, y)

    def get_canvas(self):
        """Get the ExperimentCanvas this port belongs to."""
        # Walk up the scene to find the view (canvas)
        scene = self.scene()
        if scene and scene.views():
            return scene.views()[0]
        return None


class InputPort(Port):
    """
    Input port for receiving particles.

    Visual: Filled circle on the left edge of component.
    """

    def __init__(self, parent_item):
        """
        Initialize input port.

        Args:
            parent_item: The ApparatusItem this port belongs to
        """
        super().__init__(parent_item)

        # Input ports are filled
        self.setBrush(QBrush(QColor(self.PORT_COLOR)))

    def position_on_left_edge(self, vertical_offset: float = 0):
        """
        Position port on the left edge of parent component.

        Args:
            vertical_offset: Vertical offset from center (default: centered)
        """
        parent_height = self._parent_item.HEIGHT
        x = 0  # Left edge
        y = parent_height / 2 + vertical_offset
        self.set_position(x, y)

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release on input port to complete wire connection.

        If in wire drawing mode and the source port is compatible,
        creates a permanent connection.
        """
        from PySide6.QtCore import Qt

        if event.button() == Qt.MouseButton.LeftButton:
            canvas = self.get_canvas()
            if canvas:
                canvas.complete_wire_drawing(self)
                event.accept()
                return

        super().mouseReleaseEvent(event)


class OutputPort(Port):
    """
    Output port for emitting particles.

    Visual: Hollow circle on the right edge of component.
    """

    def __init__(self, parent_item, eigenvalue: float = 0.0):
        """
        Initialize output port.

        Args:
            parent_item: The ApparatusItem this port belongs to
            eigenvalue: The measurement eigenvalue this port represents
        """
        super().__init__(parent_item, eigenvalue)

        # Output ports are hollow (no fill)
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def position_on_right_edge(self, vertical_offset: float = 0):
        """
        Position port on the right edge of parent component.

        Args:
            vertical_offset: Vertical offset from center (default: centered)
        """
        parent_width = self._parent_item.WIDTH
        parent_height = self._parent_item.HEIGHT
        x = parent_width  # Right edge
        y = parent_height / 2 + vertical_offset
        self.set_position(x, y)

    def mousePressEvent(self, event):
        from PySide6.QtCore import Qt

        if event.button() == Qt.MouseButton.LeftButton:
            canvas = self.get_canvas()
            if canvas:
                canvas.start_wire_drawing(self)
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        canvas = self.get_canvas()
        if canvas and canvas._drawing_wire:
            canvas.update_wire_drawing(event.scenePos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        from PySide6.QtCore import Qt

        if event.button() == Qt.MouseButton.LeftButton:
            canvas = self.get_canvas()
            if canvas and canvas._drawing_wire:
                # Check if there's an InputPort under the cursor
                scene = self.scene()
                dest_port = None
                if scene:
                    for item in scene.items(event.scenePos()):
                        if isinstance(item, InputPort):
                            dest_port = item
                            break
                if dest_port:
                    canvas.complete_wire_drawing(dest_port)
                else:
                    canvas.cancel_wire_drawing()
                event.accept()
                return

        super().mouseReleaseEvent(event)
