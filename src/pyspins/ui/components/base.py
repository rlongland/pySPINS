"""Abstract base class for apparatus components."""

from abc import ABC, abstractmethod
from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPen


class ApparatusItem(QGraphicsRectItem, ABC):
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

        # Make component selectable and movable (will be used in Phase 3)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable, False)  # Phase 3 will enable

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

    @abstractmethod
    def simulate(self, state, output_index: int = 0):
        """
        Simulate particle passing through this component.

        Args:
            state: SpinState representing the incoming particle
            output_index: Which output port the particle exits from (for analyzers)

        Returns:
            SpinState representing the outgoing particle, or None for counters
        """
        pass

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
