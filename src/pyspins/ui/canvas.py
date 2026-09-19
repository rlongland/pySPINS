from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QKeyEvent, QPainter, QImage

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
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

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
            selected_items = self._scene.selectedItems()

            # Delete selected wires first
            for item in selected_items:
                if isinstance(item, WireItem):
                    self.delete_wire(item)

            # Delete selected components (and their connected wires)
            for item in [i for i in selected_items if i in self._components]:
                self.delete_component(item)

            event.accept()
        else:
            super().keyPressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.

        During wire drawing, updates the temporary wire to follow the cursor.
        The OutputPort item handles this via its own mouseMoveEvent; this is
        a fallback for when the cursor leaves the port area.
        """
        if self._drawing_wire and self._temp_wire:
            scene_pos = self.mapToScene(event.pos())
            self._temp_wire.set_temporary_end_point(scene_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events.

        If in wire drawing mode and not released on an input port,
        cancels the wire drawing.
        """
        if self._drawing_wire:
            # Let the scene dispatch to items first (OutputPort may complete the wire)
            super().mouseReleaseEvent(event)
            # If still drawing after items had a chance, no port was hit — cancel
            if self._drawing_wire:
                self.cancel_wire_drawing()
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

        # Update coherent mode checkboxes (topology may have changed)
        self._update_coherent_checkboxes()

        # Clear wire drawing state
        self._drawing_wire = False
        self._temp_wire = None
        self._wire_source_port = None

    def update_wire_drawing(self, scene_pos):
        """Update the temporary wire endpoint to follow the mouse."""
        if self._temp_wire:
            self._temp_wire.set_temporary_end_point(scene_pos)

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

        # Update coherent mode checkboxes (topology may have changed)
        self._update_coherent_checkboxes()

    def delete_component(self, component):
        """Remove a component and all its connected wires from the canvas."""
        # Collect wires attached to any of this component's ports
        all_ports = component.input_ports + component.output_ports
        wires_to_delete = []
        for conn in list(self._connections):
            if conn.source_port in all_ports or conn.dest_port in all_ports:
                wires_to_delete.append(conn.wire_item)
        for wire in wires_to_delete:
            self.delete_wire(wire)

        # Remove from apparatus graph
        self._apparatus_graph = [
            (src, idx, dest)
            for src, idx, dest in self._apparatus_graph
            if src is not component and dest is not component
        ]

        # Remove from component list and scene
        self._components = [c for c in self._components if c is not component]
        self._scene.removeItem(component)

        # Update coherent mode checkboxes (topology may have changed)
        self._update_coherent_checkboxes()

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

    def add_analyzer(self, spin_type: float = 0.5):
        """
        Add a new Stern-Gerlach analyzer to the canvas.

        Args:
            spin_type: Spin type for the analyzer (0.5 or 1.0, default 0.5)
        """
        # Create analyzer at next available position
        analyzer = SternGerlachAnalyzer(
            self._next_component_x, self._next_component_y,
            axis_label="+z", spin_type=spin_type
        )

        # Create ports: 1 input, multiple outputs based on spin type (Req 26)
        analyzer_in = InputPort(analyzer)
        analyzer_in.position_on_left_edge(vertical_offset=0)
        analyzer.input_ports = [analyzer_in]

        # Create output ports based on spin type (Req 26)
        if spin_type == 0.5:
            # Spin-1/2: 2 ports labeled "+" and "−"
            analyzer_out_upper = OutputPort(analyzer, eigenvalue=0.5)
            analyzer_out_lower = OutputPort(analyzer, eigenvalue=-0.5)
            analyzer_out_upper.position_on_right_edge(vertical_offset=-15)
            analyzer_out_lower.position_on_right_edge(vertical_offset=15)
            analyzer.output_ports = [analyzer_out_upper, analyzer_out_lower]
        else:  # spin_type == 1.0
            # Spin-1: 3 ports labeled "+1", "0", "−1"
            analyzer_out_plus = OutputPort(analyzer, eigenvalue=1.0)
            analyzer_out_zero = OutputPort(analyzer, eigenvalue=0.0)
            analyzer_out_minus = OutputPort(analyzer, eigenvalue=-1.0)
            analyzer_out_plus.position_on_right_edge(vertical_offset=-20)
            analyzer_out_zero.position_on_right_edge(vertical_offset=0)
            analyzer_out_minus.position_on_right_edge(vertical_offset=20)
            analyzer.output_ports = [analyzer_out_plus, analyzer_out_zero, analyzer_out_minus]

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

    def _update_coherent_checkboxes(self):
        """
        Update the visibility of coherent mode checkboxes on all analyzers.

        Checkboxes are shown only on analyzers that have multiple incoming
        connections from the same upstream analyzer (recombination points).
        """
        for component in self._components:
            if isinstance(component, SternGerlachAnalyzer):
                upstream_analyzer = self._all_inputs_from_same_analyzer(component)
                should_show = upstream_analyzer is not None
                component.update_coherent_checkbox_visibility(should_show)

    def _all_inputs_from_same_analyzer(self, component):
        """
        Check if all incoming connections to this component come from outputs
        of the same upstream analyzer.

        This detects the coherent recombination topology where multiple output
        ports of one analyzer all connect to inputs of this component.

        Args:
            component: Component to check (typically an analyzer)

        Returns:
            SternGerlachAnalyzer or None: The upstream analyzer if recombination
                                          is detected, None otherwise
        """
        if not isinstance(component, SternGerlachAnalyzer):
            return None

        # Find all incoming connections to this component
        incoming = [
            (src, output_idx, dest)
            for src, output_idx, dest in self._apparatus_graph
            if dest == component
        ]

        if len(incoming) < 2:
            # Need at least 2 paths for recombination
            return None

        # Check if all sources are the same component and it's an analyzer
        sources = [src for src, _, _ in incoming]
        first_source = sources[0]

        if not isinstance(first_source, SternGerlachAnalyzer):
            return None

        if all(src == first_source for src in sources):
            return first_source  # All paths come from the same analyzer

        return None

    def _get_coherent_recombination_target(self, analyzer):
        """
        Check if this analyzer's outputs recombine at a downstream analyzer
        that has coherent mode enabled.

        Args:
            analyzer: SternGerlachAnalyzer to check

        Returns:
            SternGerlachAnalyzer or None: The downstream recombination analyzer
                                          if coherent recombination is active
        """
        if not isinstance(analyzer, SternGerlachAnalyzer):
            return None

        # Find all outgoing connections from this analyzer
        outgoing = [
            (src, output_idx, dest)
            for src, output_idx, dest in self._apparatus_graph
            if src == analyzer
        ]

        if len(outgoing) < 2:
            # Need at least 2 outputs for recombination
            return None

        # Check if all outputs go to the same component
        destinations = [dest for _, _, dest in outgoing]
        first_dest = destinations[0]

        if not isinstance(first_dest, SternGerlachAnalyzer):
            return None

        if all(dest == first_dest for dest in destinations):
            # All outputs go to the same analyzer
            if first_dest.coherent_mode:
                return first_dest

        return None

    def _simulate_single_particle(self):
        """
        Simulate a single particle's journey through the apparatus graph.

        Algorithm:
        1. Start at the gun, get initial state
        2. Follow graph connections based on measurement outcomes
        3. Handle coherent recombination (no collapse at intermediate analyzer)
        4. Increment counter when terminal component is reached
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
                # Check if this analyzer's outputs recombine coherently downstream
                recombination_target = self._get_coherent_recombination_target(current_component)

                if recombination_target:
                    # Coherent recombination: Don't measure here, pass state through unchanged
                    # Take the first available connection (all lead to same recombination point)
                    _, _, next_component = outgoing_connections[0]
                    current_component = next_component

                    # Process the next component (should be the recombination analyzer)
                    if isinstance(current_component, ParticleCounter):
                        current_component.increment()
                        break  # Terminal
                    else:
                        # State passes through unchanged - measurement happens at recombination point
                        current_state = current_component.simulate(current_state)
                else:
                    # Incoherent (normal) mode: Perform measurement to determine path
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
        sg_z = SternGerlachAnalyzer(sg_x, sg_y, axis_label="+z", spin_type=0.5)  # Spin-1/2 analyzer
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

    def to_json(self) -> dict:
        """
        Serialize scene to dict suitable for json.dumps.

        Returns a dictionary with:
        - version: file format version (1)
        - components: list of component dicts with type, position, and parameters
        - connections: list of (source_id, output_index, dest_id) tuples

        Returns:
            dict: Serialized scene data
        """
        import uuid

        # Assign temporary UUIDs to components for connection references
        component_ids = {comp: str(uuid.uuid4()) for comp in self._components}

        # Serialize components
        components_data = []
        for component in self._components:
            comp_id = component_ids[component]
            comp_data = {
                "id": comp_id,
                "x": component.x(),
                "y": component.y(),
            }

            if isinstance(component, ParticleGun):
                comp_data["type"] = "gun"
                comp_data["spin_type"] = component.get_spin_type()
                comp_data["state_vector"] = component.get_initial_state_vector().tolist()

            elif isinstance(component, SternGerlachAnalyzer):
                comp_data["type"] = "analyzer"
                comp_data["axis_label"] = component._axis_label
                comp_data["phi_deg"] = component._phi_deg
                comp_data["spin_type"] = component.get_spin_type()
                comp_data["coherent_mode"] = component.coherent_mode

            elif isinstance(component, SpinRotationMagnet):
                comp_data["type"] = "magnet"
                comp_data["beta"] = component.get_beta()

            elif isinstance(component, ParticleCounter):
                comp_data["type"] = "counter"
                comp_data["label"] = component.label
                comp_data["count"] = component._count

            components_data.append(comp_data)

        # Serialize connections
        connections_data = []
        for connection in self._connections:
            source_comp = connection.source_port._parent_item
            dest_comp = connection.dest_port._parent_item
            source_id = component_ids[source_comp]
            dest_id = component_ids[dest_comp]
            output_index = source_comp.output_ports.index(connection.source_port)

            connections_data.append({
                "source_id": source_id,
                "output_index": output_index,
                "dest_id": dest_id,
            })

        return {
            "version": 1,
            "components": components_data,
            "connections": connections_data,
        }

    def from_json(self, data: dict):
        """
        Restore scene from deserialized dict.

        Clears the current scene and rebuilds components and connections
        from the serialized data.

        Args:
            data: Dictionary from to_json() (after json.loads)
        """
        import numpy as np

        # Validate version
        if data.get("version") != 1:
            raise ValueError(f"Unsupported file version: {data.get('version')}")

        # Clear current scene
        self.clear_scene()

        # Map from serialized ID to recreated component
        id_to_component = {}

        # Recreate components
        for comp_data in data["components"]:
            comp_id = comp_data["id"]
            comp_type = comp_data["type"]
            x = comp_data["x"]
            y = comp_data["y"]

            if comp_type == "gun":
                component = ParticleGun(x, y)
                spin_type = comp_data["spin_type"]
                state_vector = np.array(comp_data["state_vector"], dtype=complex)
                component.set_spin_type(spin_type)
                component.set_initial_state(state_vector)

                # Create ports
                gun_out = OutputPort(component, eigenvalue=0.5)
                gun_out.position_on_right_edge(vertical_offset=0)
                component.output_ports = [gun_out]

            elif comp_type == "analyzer":
                axis_label = comp_data["axis_label"]
                phi_deg = comp_data["phi_deg"]
                spin_type = comp_data["spin_type"]
                component = SternGerlachAnalyzer(x, y, axis_label, phi_deg, spin_type)
                component.coherent_mode = comp_data.get("coherent_mode", False)

                # Create ports: 1 input, multiple outputs based on spin type
                analyzer_in = InputPort(component)
                analyzer_in.position_on_left_edge(vertical_offset=0)
                component.input_ports = [analyzer_in]

                if spin_type == 0.5:
                    analyzer_out_upper = OutputPort(component, eigenvalue=0.5)
                    analyzer_out_lower = OutputPort(component, eigenvalue=-0.5)
                    analyzer_out_upper.position_on_right_edge(vertical_offset=-15)
                    analyzer_out_lower.position_on_right_edge(vertical_offset=15)
                    component.output_ports = [analyzer_out_upper, analyzer_out_lower]
                else:  # spin_type == 1.0
                    analyzer_out_plus = OutputPort(component, eigenvalue=1.0)
                    analyzer_out_zero = OutputPort(component, eigenvalue=0.0)
                    analyzer_out_minus = OutputPort(component, eigenvalue=-1.0)
                    analyzer_out_plus.position_on_right_edge(vertical_offset=-20)
                    analyzer_out_zero.position_on_right_edge(vertical_offset=0)
                    analyzer_out_minus.position_on_right_edge(vertical_offset=20)
                    component.output_ports = [analyzer_out_plus, analyzer_out_zero, analyzer_out_minus]

            elif comp_type == "magnet":
                component = SpinRotationMagnet(x, y)
                component.set_beta(comp_data["beta"])

                # Create ports
                magnet_in = InputPort(component)
                magnet_in.position_on_left_edge(vertical_offset=0)
                component.input_ports = [magnet_in]

                magnet_out = OutputPort(component, eigenvalue=0.5)
                magnet_out.position_on_right_edge(vertical_offset=0)
                component.output_ports = [magnet_out]

            elif comp_type == "counter":
                label = comp_data.get("label", "Counter")
                component = ParticleCounter(x, y, label=label)
                component.set_count(comp_data.get("count", 0))

                # Create ports
                counter_in = InputPort(component)
                counter_in.position_on_left_edge(vertical_offset=0)
                component.input_ports = [counter_in]

            else:
                raise ValueError(f"Unknown component type: {comp_type}")

            # Add to scene and component list
            self._scene.addItem(component)
            self._components.append(component)
            id_to_component[comp_id] = component

        # Recreate connections
        for conn_data in data["connections"]:
            source_id = conn_data["source_id"]
            dest_id = conn_data["dest_id"]
            output_index = conn_data["output_index"]

            source_comp = id_to_component[source_id]
            dest_comp = id_to_component[dest_id]

            source_port = source_comp.output_ports[output_index]
            dest_port = dest_comp.input_ports[0]  # All components have single input

            # Create wire
            wire = WireItem(source_port, dest_port)
            self._scene.addItem(wire)

            # Create connection
            connection = Connection(source_port, dest_port, wire)
            self._connections.append(connection)

            # Update apparatus graph
            self._apparatus_graph.append((source_comp, output_index, dest_comp))

        # Update coherent mode checkboxes based on topology
        self._update_coherent_checkboxes()

    def clear_scene(self):
        """Clear all components and connections from the scene."""
        # Remove all wires
        for connection in list(self._connections):
            self.delete_wire(connection.wire_item)

        # Remove all components
        for component in list(self._components):
            self._scene.removeItem(component)

        # Clear lists
        self._components = []
        self._connections = []
        self._apparatus_graph = []

        # Reset component placement position
        self._next_component_x = 100
        self._next_component_y = 100

    def export_to_png(self, file_path: str):
        """
        Export the current scene to a PNG image.

        Args:
            file_path: Path to save the PNG file

        Uses QGraphicsScene.render() to draw the scene onto a QImage.
        Only exports the bounding rect of items, not the full scene rect.
        """
        # Get the bounding rect of all items (avoid exporting huge empty scene)
        items_rect = self._scene.itemsBoundingRect()

        # Add padding around the content (20px on each side)
        padding = 20
        export_rect = items_rect.adjusted(-padding, -padding, padding, padding)

        # Create QImage with appropriate size
        # Use 2x scaling for high-DPI export
        scale_factor = 2.0
        image_width = int(export_rect.width() * scale_factor)
        image_height = int(export_rect.height() * scale_factor)

        image = QImage(image_width, image_height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)  # White background

        # Create painter and render scene onto image
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Scale up for high-DPI
        painter.scale(scale_factor, scale_factor)

        # Render the scene
        self._scene.render(painter, QRectF(), export_rect)
        painter.end()

        # Save to file
        image.save(file_path, "PNG")
