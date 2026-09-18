from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt

from pyspins.ui.components.gun import ParticleGun
from pyspins.ui.components.analyzer import SternGerlachAnalyzer
from pyspins.ui.components.counter import ParticleCounter
from pyspins.ui.port import InputPort, OutputPort
from pyspins.physics.measurement import measure
from pyspins.physics.operators import eigenstates


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

    def run_batch(self, n: int = 10_000):
        """
        Run batch simulation of n particles through the apparatus.

        Walks the apparatus graph for each particle, performing measurements
        and accumulating counts in terminal counters.

        Args:
            n: Number of particles to simulate (default: 10,000)
        """
        # Reset all counters before batch run
        self.reset_counts()

        # Simulate n particles
        for _ in range(n):
            self._simulate_single_particle()

    def run_single(self):
        """
        Run single particle simulation through the apparatus.

        Simulates one particle's path through the apparatus, following
        the measurement outcomes to determine which path is taken.
        """
        self._simulate_single_particle()

    def reset_counts(self):
        """Reset all counter displays to zero."""
        for component in self._components:
            if isinstance(component, ParticleCounter):
                component.reset()

    def _simulate_single_particle(self):
        """
        Simulate a single particle's journey through the apparatus graph.

        Algorithm:
        1. Start at the gun, get initial state
        2. Follow graph connections based on measurement outcomes
        3. Increment counter when terminal component is reached
        """
        # Find the gun (source of particles)
        gun = None
        for component in self._components:
            if isinstance(component, ParticleGun):
                gun = component
                break

        if gun is None:
            return  # No gun in apparatus

        # Get initial state from gun
        current_state = gun.simulate()
        current_component = gun

        # Walk the graph until we reach a terminal component
        while current_state is not None:
            # Find connections from current component
            outgoing_connections = [
                (src, output_idx, dest)
                for src, output_idx, dest in self._apparatus_graph
                if src == current_component
            ]

            if not outgoing_connections:
                break  # Terminal component or dead end

            # Determine next component based on current component type
            if isinstance(current_component, ParticleGun):
                # Gun has single output (index 0)
                _, _, next_component = outgoing_connections[0]
                current_component = next_component

                # Process the next component
                if isinstance(current_component, ParticleCounter):
                    current_component.increment()
                    break  # Terminal
                else:
                    current_state = current_component.simulate(current_state)

            elif isinstance(current_component, SternGerlachAnalyzer):
                # Perform measurement to determine which output path is taken
                eigenvalue, post_state = measure(current_state, current_component.get_axis_vector())
                current_state = post_state

                # Determine which output index corresponds to this eigenvalue
                # Eigenvalues are ordered descending: for spin-1/2: [+0.5, -0.5]
                evals, _ = eigenstates(current_state.s, current_component.get_axis_vector())

                # Find the index of this eigenvalue
                # evals is a list of floats, find the closest match (handle floating point)
                output_idx = None
                for i, ev in enumerate(evals):
                    if abs(ev - eigenvalue) < 1e-10:
                        output_idx = i
                        break

                if output_idx is None:
                    break  # Shouldn't happen, but safety check

                # Find the connection with this output index
                next_component = None
                for src, idx, dest in outgoing_connections:
                    if idx == output_idx:
                        next_component = dest
                        break

                if next_component is None:
                    break  # No connection for this output

                current_component = next_component

                # Process the next component
                if isinstance(current_component, ParticleCounter):
                    current_component.increment()
                    break  # Terminal
                else:
                    current_state = current_component.simulate(current_state)

            else:
                # Unknown component type, shouldn't happen in Phase 2
                break

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
