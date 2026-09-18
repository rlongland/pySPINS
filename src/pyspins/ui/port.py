"""Port classes for apparatus component connections."""

from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QPen


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

        # Visual styling (will be overridden by subclasses)
        self.setPen(QPen(QColor(self.PORT_COLOR), 2))

        # Ports are selectable but not movable (they move with parent)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, False)

    def set_position(self, x: float, y: float):
        """
        Set port position relative to parent item.

        Args:
            x: X coordinate relative to parent
            y: Y coordinate relative to parent
        """
        self.setPos(x, y)


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
