from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QKeyEvent

from pyspins.ui.components.gun import ParticleGun
from pyspins.ui.components.analyzer import SternGerlachAnalyzer
from pyspins.ui.components.counter import ParticleCounter
from pyspins.ui.components.magnet import SpinRotationMagnet
from pyspins.ui.port import InputPort, OutputPort
from pyspins.ui.connections import Connection, WireItem
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

        # Connection storage
        self._connections = []

        # Wire drawing state
        self._drawing_wire = False
        self._temp_wire = None
        self._wire_source_port = None

        # Component placement position (for toolbar "Add" buttons)
        self._next_component_x = 100
        self._next_component_y = 100

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

    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle key press events.

        Delete key removes selected wire connections.
        """
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            # Get all selected items
            selected_items = self._scene.selectedItems()

            # Filter for WireItem instances
            selected_wires = [item for item in selected_items if isinstance(item, WireItem)]

            # Delete each selected wire
            for wire in selected_wires:
                self.delete_wire(wire)

            event.accept()
        else:
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.

        During wire drawing, updates the temporary wire to follow the cursor.
        """
        if self._drawing_wire and self._temp_wire:
            # Update temporary wire end point to current mouse position
            scene_pos = self.mapToScene(event.pos())
            self._temp_wire.set_temporary_end_point(scene_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events.

        If in wire drawing mode and not released on an input port,
        cancels the wire drawing.
        """
        if self._drawing_wire:
            # User released without hitting an input port - cancel wire drawing
            self.cancel_wire_drawing()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def start_wire_drawing(self, source_port):
        """
        Start wire drawing from an output port.

        Creates a temporary wire that follows the mouse cursor until
        the user releases on an input port or cancels.

        Args:
            source_port: OutputPort where wire drawing started
        """
        # Don't allow multiple connections from the same output port
        if source_port.connection is not None:
            return

        self._drawing_wire = True
        self._wire_source_port = source_port

        # Create temporary wire (will be finalized or removed on mouse release)
        self._temp_wire = WireItem(source_port, None)
        self._temp_wire.dest_port = None  # No destination yet
        self._scene.addItem(self._temp_wire)

        # Set initial position to source port
        self._temp_wire.set_temporary_end_point(source_port.scenePos())

    def complete_wire_drawing(self, dest_port):
        """
        Complete wire drawing by connecting to an input port.

        Creates a permanent connection if the ports are compatible
        (source is OutputPort, dest is InputPort, neither already connected).

        Args:
            dest_port: InputPort where wire drawing ended
        """
        if not self._drawing_wire or not self._temp_wire:
            return

        # Validate connection
        if not self._is_valid_connection(self._wire_source_port, dest_port):
            self.cancel_wire_drawing()
            return

        # Finalize the wire by setting its destination port
        self._temp_wire.dest_port = dest_port
        self._temp_wire.update_path()

        # Create connection object
        connection = Connection(self._wire_source_port, dest_port, self._temp_wire)
        self._connections.append(connection)

        # Update apparatus graph
        # Find the components that own these ports
        source_component = self._wire_source_port._parent_item
        dest_component = dest_port._parent_item

        # Find the output index of the source port
        output_index = source_component.output_ports.index(self._wire_source_port)

        # Add to apparatus graph
        self._apparatus_graph.append((source_component, output_index, dest_component))

        # Clear wire drawing state
        self._drawing_wire = False
        self._temp_wire = None
        self._wire_source_port = None

    def cancel_wire_drawing(self):
        """
        Cancel wire drawing.

        Removes the temporary wire and resets wire drawing state.
        """
        if self._temp_wire:
            self._scene.removeItem(self._temp_wire)
            self._temp_wire = None

        self._drawing_wire = False
        self._wire_source_port = None

    def _is_valid_connection(self, source_port, dest_port):
        """
        Check if a connection between two ports is valid.

        Valid connections require:
        - Source is an OutputPort
        - Destination is an InputPort
        - Neither port is already connected
        - Ports belong to different components

        Args:
            source_port: Port where connection starts
            dest_port: Port where connection ends

        Returns:
            bool: True if connection is valid
        """
        # Check types
        if not isinstance(source_port, OutputPort):
            return False
        if not isinstance(dest_port, InputPort):
            return False

        # Check if ports are already connected
        if source_port.connection is not None:
            return False
        if dest_port.connection is not None:
            return False

        # Check that ports belong to different components
        if source_port._parent_item == dest_port._parent_item:
            return False

        return True

    def delete_wire(self, wire_item: WireItem):
        """
        Delete a wire connection.

        Removes the wire from the scene, clears port connections,
        removes from the connections list, and updates the apparatus graph.

        Args:
            wire_item: The WireItem to delete
        """
        # Find the connection object for this wire
        connection = None
        for conn in self._connections:
            if conn.wire_item == wire_item:
                connection = conn
                break

        if connection is None:
            # Wire not found in connections list, shouldn't happen
            # but handle gracefully by just removing from scene
            self._scene.removeItem(wire_item)
            return

        # Clear port connection references
        connection.source_port.connection = None
        connection.dest_port.connection = None

        # Remove from apparatus graph
        # Find the graph entry for this connection
        source_component = connection.source_port._parent_item
        dest_component = connection.dest_port._parent_item
        output_index = source_component.output_ports.index(connection.source_port)

        # Remove matching entry from apparatus graph
        self._apparatus_graph = [
            (src, idx, dest)
            for src, idx, dest in self._apparatus_graph
            if not (src == source_component and idx == output_index and dest == dest_component)
        ]

        # Remove from connections list
        self._connections.remove(connection)

        # Remove wire from scene
        self._scene.removeItem(wire_item)

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

    def add_gun(self):
        """Add a new particle gun to the canvas."""
        # Create gun at next available position
        gun = ParticleGun(self._next_component_x, self._next_component_y)

        # Create ports
        gun_out = OutputPort(gun, eigenvalue=0.5)
        gun_out.position_on_right_edge(vertical_offset=0)
        gun.output_ports = [gun_out]

        # Add to scene and component list
        self._scene.addItem(gun)
        self._components.append(gun)

        # Update position for next component
        self._next_component_x += 150
        if self._next_component_x > 500:
            self._next_component_x = 100
            self._next_component_y += 100

    def add_analyzer(self):
        """Add a new Stern-Gerlach analyzer to the canvas."""
        # Create analyzer at next available position
        analyzer = SternGerlachAnalyzer(self._next_component_x, self._next_component_y, axis_label="z")

        # Create ports: 1 input, 2 outputs for spin-1/2
        analyzer_in = InputPort(analyzer)
        analyzer_in.position_on_left_edge(vertical_offset=0)
        analyzer.input_ports = [analyzer_in]

        # Output ports for spin-1/2 (+1/2 upper, -1/2 lower)
        analyzer_out_upper = OutputPort(analyzer, eigenvalue=0.5)
        analyzer_out_lower = OutputPort(analyzer, eigenvalue=-0.5)
        analyzer_out_upper.position_on_right_edge(vertical_offset=-15)
        analyzer_out_lower.position_on_right_edge(vertical_offset=15)
        analyzer.output_ports = [analyzer_out_upper, analyzer_out_lower]

        # Add to scene and component list
        self._scene.addItem(analyzer)
        self._components.append(analyzer)

        # Update position for next component
        self._next_component_x += 150
        if self._next_component_x > 500:
            self._next_component_x = 100
            self._next_component_y += 100

    def add_magnet(self):
        """Add a new spin rotation magnet to the canvas."""
        # Create magnet at next available position
        magnet = SpinRotationMagnet(self._next_component_x, self._next_component_y)

        # Create ports: 1 input, 1 output (no beam splitting)
        magnet_in = InputPort(magnet)
        magnet_in.position_on_left_edge(vertical_offset=0)
        magnet.input_ports = [magnet_in]

        magnet_out = OutputPort(magnet, eigenvalue=0.5)
        magnet_out.position_on_right_edge(vertical_offset=0)
        magnet.output_ports = [magnet_out]

        # Add to scene and component list
        self._scene.addItem(magnet)
        self._components.append(magnet)

        # Update position for next component
        self._next_component_x += 150
        if self._next_component_x > 500:
            self._next_component_x = 100
            self._next_component_y += 100

    def add_counter(self):
        """Add a new particle counter to the canvas."""
        # Create counter at next available position
        counter = ParticleCounter(self._next_component_x, self._next_component_y)

        # Create ports: 1 input (terminal component)
        counter_in = InputPort(counter)
        counter_in.position_on_left_edge(vertical_offset=0)
        counter.input_ports = [counter_in]

        # Add to scene and component list
        self._scene.addItem(counter)
        self._components.append(counter)

        # Update position for next component
        self._next_component_x += 150
        if self._next_component_x > 500:
            self._next_component_x = 100
            self._next_component_y += 100

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

            elif isinstance(current_component, SpinRotationMagnet):
                # Magnet has single output (index 0), no measurement
                _, _, next_component = outgoing_connections[0]
                current_component = next_component

                # Process the next component
                if isinstance(current_component, ParticleCounter):
                    current_component.increment()
                    break  # Terminal
                else:
                    current_state = current_component.simulate(current_state)

            else:
                # Unknown component type
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
