from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt


class ExperimentCanvas(QGraphicsView):
    """Canvas for the Stern-Gerlach apparatus with zoom support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Set scene rect to large canvas area
        self._scene.setSceneRect(-2000, -2000, 4000, 4000)

        # Enable smooth transformations
        self.setRenderHint(self.RenderHint.Antialiasing)
        self.setRenderHint(self.RenderHint.SmoothPixmapTransform)

        # Enable drag mode for panning
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Set zoom limits
        self._zoom_factor = 1.0
        self._zoom_min = 0.1
        self._zoom_max = 5.0

    def wheelEvent(self, event):
        """Handle mouse wheel for zoom in/out."""
        # Get the scroll delta (positive = zoom in, negative = zoom out)
        delta = event.angleDelta().y()

        if delta > 0:
            zoom_multiplier = 1.15
        else:
            zoom_multiplier = 1 / 1.15

        # Check zoom limits
        new_zoom = self._zoom_factor * zoom_multiplier
        if new_zoom < self._zoom_min or new_zoom > self._zoom_max:
            return

        # Apply zoom
        self._zoom_factor = new_zoom
        self.scale(zoom_multiplier, zoom_multiplier)

        event.accept()

    def run_batch(self):
        """Run batch simulation (10k particles). To be implemented in later tasks."""
        pass

    def run_single(self):
        """Run single particle simulation. To be implemented in later tasks."""
        pass

    def reset_counts(self):
        """Reset all counter displays. To be implemented in later tasks."""
        pass
