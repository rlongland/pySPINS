"""Abstract base class for apparatus components."""

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtCore import QRectF, Qt, QPointF
from PySide6.QtGui import QBrush, QColor, QPen


class ApparatusItem(QGraphicsRectItem):
    """
    Abstract base class for all apparatus components.

    Components are 80x50 px rectangles with 8px rounded corners.
    Each component has a label, fill color, and simulation behavior.
    """

    # Standard component dimensions (per Req 25)
    WIDTH = 80
    HEIGHT = 50
    CORNER_RADIUS = 8

    def __init__(self, label: str, color: str, x: float = 0, y: float = 0):
        """
        Initialize apparatus component.

        Args:
            label: Text label to display on component
            color: Hex color string for fill (e.g., "#1a237e")
            x: Initial x position on canvas
            y: Initial y position on canvas
        """
        super().__init__(0, 0, self.WIDTH, self.HEIGHT)

        self.label = label
        self._color = QColor(color)

        # Set position
        self.setPos(x, y)

        # Make component selectable and movable
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, True)  # Phase 3: enabled

        # Set visual appearance
        self.setBrush(QBrush(self._color))
        self.setPen(QPen(QColor("#000000"), 2))  # Black border, 2px wide

        # Create text label
        self._text_item = QGraphicsTextItem(label, self)
        self._center_text()
        self._text_item.setDefaultTextColor(QColor("#ffffff"))  # White text

        # Port lists (will be populated by subclasses)
        self.input_ports = []
        self.output_ports = []

    def _center_text(self):
        """Center the text label within the component bounds."""
        text_rect = self._text_item.boundingRect()
        x = (self.WIDTH - text_rect.width()) / 2
        y = (self.HEIGHT - text_rect.height()) / 2
        self._text_item.setPos(x, y)

    def paint(self, painter, option, widget=None):
        """
        Custom paint to render rounded rectangle.

        Override QGraphicsRectItem's paint to use rounded corners.
        """
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(
            QRectF(0, 0, self.WIDTH, self.HEIGHT),
            self.CORNER_RADIUS,
            self.CORNER_RADIUS
        )

    def transfer(self, vector, s: float):
        """
        Propagate an (unnormalized) spin amplitude through this component.

        Args:
            vector: Incoming amplitude as a complex numpy array
            s: Spin quantum number of the particle (0.5 or 1.0)

        Returns:
            List of outgoing amplitudes, one per output port index,
            or None for terminal components (counters)
        """
        raise NotImplementedError

    def notify_canvas(self):
        """Tell the canvas this component changed, so the status bar refreshes."""
        scene = self.scene()
        for view in scene.views() if scene else []:
            if hasattr(view, "notify_changed"):
                view.notify_changed()

    def set_label(self, label: str):
        """Update the component's text label."""
        self.label = label
        self._text_item.setPlainText(label)
        self._center_text()

    def get_color(self) -> QColor:
        """Get the component's fill color."""
        return self._color

    def set_color(self, color: str):
        """
        Update the component's fill color.

        Args:
            color: Hex color string (e.g., "#1a237e")
        """
        self._color = QColor(color)
        self.setBrush(QBrush(self._color))

    def itemChange(self, change, value):
        """
        Handle item changes (e.g., position changes).

        When component moves, update all connected wires to follow.
        """
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update all wires connected to this component's ports
            self._update_connected_wires()

        return super().itemChange(change, value)

    def _update_connected_wires(self):
        """Update all wires connected to this component's ports."""
        for port in self.input_ports + self.output_ports:
            for connection in port.connections:
                connection.wire_item.update_path()
