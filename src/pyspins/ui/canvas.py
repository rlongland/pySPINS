from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt

from pyspins.ui.components.gun import ParticleGun
from pyspins.ui.components.analyzer import SternGerlachAnalyzer
from pyspins.ui.components.counter import ParticleCounter
from pyspins.ui.port import InputPort, OutputPort


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

        # Apparatus graph: list of (source_item, output_index, dest_item) tuples
        self._apparatus_graph = []

        # Component storage
        self._components = []

        # Build hardcoded default scene
        self._build_default_scene()

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

    def _build_default_scene(self):
        """
        Build hardcoded default apparatus: Gun → SG_z → Counter(+z) + Counter(−z).

        This is a scaffold for Phase 2. Phase 3 will replace this with interactive
        drag-and-connect functionality.
        """
        # Component positions (horizontal layout with spacing)
        gun_x, gun_y = 50, 150
        sg_x, sg_y = 200, 150
        counter_upper_x, counter_upper_y = 350, 100  # +z (upper beam)
        counter_lower_x, counter_lower_y = 350, 200  # -z (lower beam)

        # Create components
        gun = ParticleGun(gun_x, gun_y)
        sg_z = SternGerlachAnalyzer(sg_x, sg_y, axis_label="z")
        counter_upper = ParticleCounter(counter_upper_x, counter_upper_y, label="Counter(+z)")
        counter_lower = ParticleCounter(counter_lower_x, counter_lower_y, label="Counter(-z)")

        # Store components
        self._components = [gun, sg_z, counter_upper, counter_lower]

        # Create ports
        # Gun: 1 output port (right side, centered)
        gun_out = OutputPort(gun, eigenvalue=0.5)
        gun_out.position_on_right_edge(vertical_offset=0)
        gun.output_ports = [gun_out]

        # SG_z: 1 input port (left side), 2 output ports (right side, upper/lower)
        sg_in = InputPort(sg_z)
        sg_in.position_on_left_edge(vertical_offset=0)
        sg_z.input_ports = [sg_in]

        # For spin-1/2, output ports represent +1/2 (upper) and -1/2 (lower)
        sg_out_upper = OutputPort(sg_z, eigenvalue=0.5)   # +1/2
        sg_out_lower = OutputPort(sg_z, eigenvalue=-0.5)  # -1/2
        sg_out_upper.position_on_right_edge(vertical_offset=-15)  # Offset upward
        sg_out_lower.position_on_right_edge(vertical_offset=15)   # Offset downward
        sg_z.output_ports = [sg_out_upper, sg_out_lower]

        # Counter(+z): 1 input port (left side)
        counter_upper_in = InputPort(counter_upper)
        counter_upper_in.position_on_left_edge(vertical_offset=0)
        counter_upper.input_ports = [counter_upper_in]

        # Counter(-z): 1 input port (left side)
        counter_lower_in = InputPort(counter_lower)
        counter_lower_in.position_on_left_edge(vertical_offset=0)
        counter_lower.input_ports = [counter_lower_in]

        # Build apparatus graph: (source_item, output_index, dest_item)
        # Gun → SG_z (gun's output 0 → sg_z)
        # SG_z → Counter(+z) (sg_z's output 0 [upper] → counter_upper)
        # SG_z → Counter(-z) (sg_z's output 1 [lower] → counter_lower)
        self._apparatus_graph = [
            (gun, 0, sg_z),
            (sg_z, 0, counter_upper),   # output_index 0 = upper beam (+z)
            (sg_z, 1, counter_lower),   # output_index 1 = lower beam (-z)
        ]

        # Add components to scene
        for component in self._components:
            self._scene.addItem(component)
