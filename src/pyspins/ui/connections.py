"""Wire connections between apparatus components."""

from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPen, QColor, QPainterPath, QPainterPathStroker


class Connection:
    """
    Represents a logical connection between two ports.

    Stores the source port (OutputPort), destination port (InputPort),
    and the visual WireItem that represents this connection on the canvas.
    """

    def __init__(self, source_port, dest_port, wire_item):
        """
        Initialize connection.

        Args:
            source_port: OutputPort where the connection starts
            dest_port: InputPort where the connection ends
            wire_item: WireItem visual representation
        """
        self.source_port = source_port
        self.dest_port = dest_port
        self.wire_item = wire_item

        # Register connection with ports
        source_port.connections.append(self)
        dest_port.connections.append(self)


class WireItem(QGraphicsPathItem):
    """
    Visual representation of a wire connection between two ports.

    Draws a cubic Bezier curve from source port to destination port.
    The curve uses horizontal control points for smooth, natural-looking wiring.
    Wire color indicates the eigenvalue it represents (Req 25).
    """

    # Wire visual constants (Req 25: colored by eigenvalue)
    WIRE_COLOR_PLUS = "#1565c0"   # Blue for + eigenvalue
    WIRE_COLOR_MINUS = "#c62828"  # Red for − eigenvalue
    WIRE_COLOR_ZERO = "#757575"   # Grey for 0 eigenvalue (spin-1 only)
    WIRE_WIDTH = 2
    WIRE_SELECT_COLOR = "#f57c00"  # Orange for selected wire
    WIRE_HIGHLIGHT_COLOR = "#ffd54f"  # Amber for the path a single particle took
    HIGHLIGHT_WIDTH = 5
    HIT_DETECTION_WIDTH = 10  # Wider hit area (5px on each side)

    def __init__(self, source_port, dest_port):
        """
        Initialize wire item.

        Args:
            source_port: OutputPort where the wire starts
            dest_port: InputPort where the wire ends
        """
        super().__init__()

        self.source_port = source_port
        self.dest_port = dest_port

        # Determine wire color based on source port eigenvalue (Req 25)
        eigenvalue = source_port.eigenvalue
        if eigenvalue > 0.01:
            wire_color = self.WIRE_COLOR_PLUS  # Blue for positive eigenvalue
        elif eigenvalue < -0.01:
            wire_color = self.WIRE_COLOR_MINUS  # Red for negative eigenvalue
        else:
            wire_color = self.WIRE_COLOR_ZERO  # Grey for zero eigenvalue (spin-1)

        # Visual styling
        self._normal_pen = QPen(QColor(wire_color), self.WIRE_WIDTH)
        self._selected_pen = QPen(QColor(self.WIRE_SELECT_COLOR), self.WIRE_WIDTH + 1)
        self._highlight_pen = QPen(QColor(self.WIRE_HIGHLIGHT_COLOR), self.HIGHLIGHT_WIDTH)
        self._highlighted = False
        self.setPen(self._normal_pen)

        # Make wire selectable for deletion in Phase 3 Task 3.3
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable, True)

        # Update the path
        self.update_path()

    def itemChange(self, change, value):
        """
        Handle item state changes, particularly selection.

        When selected, changes pen color to highlight the wire.
        """
        if change == QGraphicsPathItem.GraphicsItemChange.ItemSelectedChange:
            self._apply_pen(selected=bool(value))

        return super().itemChange(change, value)

    def set_highlighted(self, highlighted: bool):
        """Mark this wire as part of the path a single particle took."""
        self._highlighted = highlighted
        self._apply_pen(selected=self.isSelected())

    def is_highlighted(self) -> bool:
        return self._highlighted

    def _apply_pen(self, selected: bool):
        """Selection wins over highlighting, which wins over the eigenvalue colour."""
        if selected:
            self.setPen(self._selected_pen)
        elif self._highlighted:
            self.setPen(self._highlight_pen)
        else:
            self.setPen(self._normal_pen)

    def shape(self):
        """
        Return the shape for collision/hit detection.

        Creates a wider stroke (10px) around the wire path for easier clicking.
        This makes it easier to select wires with the mouse.
        """
        stroker = QPainterPathStroker()
        stroker.setWidth(self.HIT_DETECTION_WIDTH)
        return stroker.createStroke(self.path())

    def update_path(self):
        """
        Update the Bezier curve path based on current port positions.

        Recalculates the path whenever ports move (when their parent components move).
        Uses horizontal control points that extend from each port for smooth curves.
        """
        # Get port positions in scene coordinates
        start_pos = self.source_port.scenePos()
        if self.dest_port is None:
            return
        end_pos = self.dest_port.scenePos()

        # Calculate control points for Bezier curve
        # Control points extend horizontally from each port
        # Distance is 1/3 of the horizontal distance between ports
        control_distance = abs(end_pos.x() - start_pos.x()) / 3

        # First control point: extends right from source port
        ctrl1 = QPointF(start_pos.x() + control_distance, start_pos.y())

        # Second control point: extends left from destination port
        ctrl2 = QPointF(end_pos.x() - control_distance, end_pos.y())

        # Create Bezier path
        path = QPainterPath()
        path.moveTo(start_pos)
        path.cubicTo(ctrl1, ctrl2, end_pos)

        # Set the path
        self.setPath(path)

    def set_temporary_end_point(self, scene_pos: QPointF):
        """
        Set temporary end point for wire while dragging (before connecting to a port).

        Used during wire drawing when the user is dragging from an output port
        but hasn't released on an input port yet.

        Args:
            scene_pos: Current mouse position in scene coordinates
        """
        # Get source port position in scene coordinates
        start_pos = self.source_port.scenePos()

        # Calculate control points
        control_distance = abs(scene_pos.x() - start_pos.x()) / 3
        ctrl1 = QPointF(start_pos.x() + control_distance, start_pos.y())
        ctrl2 = QPointF(scene_pos.x() - control_distance, scene_pos.y())

        # Create Bezier path to mouse cursor
        path = QPainterPath()
        path.moveTo(start_pos)
        path.cubicTo(ctrl1, ctrl2, scene_pos)

        # Set the path
        self.setPath(path)
