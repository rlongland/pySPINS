import numpy as np
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtCore import Qt, QMarginsF, QPointF, QRectF, QSizeF, Signal
from PySide6.QtGui import QKeyEvent, QPageSize, QPainter, QImage, QPdfWriter

from pyspins.ui.components.gun import ParticleGun
from pyspins.ui.components.analyzer import SternGerlachAnalyzer
from pyspins.ui.components.counter import ParticleCounter
from pyspins.ui.components.magnet import SpinRotationMagnet
from pyspins.ui.port import InputPort, OutputPort
from pyspins.ui.connections import Connection, WireItem
from pyspins.physics.network import LOST, outcome_probabilities
from pyspins.physics.states import UNKNOWN_STATES, SpinState


class ExperimentCanvas(QGraphicsView):
    """Canvas for the Stern-Gerlach apparatus with zoom support."""

    #: Emitted whenever the apparatus or the counts change, so the window
    #: can refresh the status bar (Req 18).
    scene_changed = Signal()

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

        # Component storage
        self._components = []

        # Connection storage
        self._connections = []

        # Wire drawing state
        self._drawing_wire = False
        self._temp_wire = None
        self._wire_source_port = None

        # Particles fired since the counters were last reset (Req 18)
        self._particles_fired = 0
        self._mode = "Ready"

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
        if source_port.connections:
            return

        self._drawing_wire = True
        self._wire_source_port = source_port

        # Create temporary wire (removed again on mouse release)
        self._temp_wire = WireItem(source_port, None)
        self._scene.addItem(self._temp_wire)

        # Set initial position to source port
        self._temp_wire.set_temporary_end_point(source_port.scenePos())

    def complete_wire_drawing(self, dest_port):
        """
        Complete wire drawing by connecting to an input port.

        The temporary wire is discarded and, if the connection is valid,
        replaced by a permanent one.

        Args:
            dest_port: InputPort where wire drawing ended
        """
        if not self._drawing_wire or not self._temp_wire:
            return

        source_port = self._wire_source_port
        self.cancel_wire_drawing()
        self.connect_ports(source_port, dest_port)

    def connect_ports(self, source_port, dest_port):
        """
        Connect an output port to an input port with a wire.

        Args:
            source_port: OutputPort where the connection starts
            dest_port: InputPort where the connection ends

        Returns:
            Connection, or None if the connection is not valid
        """
        if not self._is_valid_connection(source_port, dest_port):
            return None

        wire = WireItem(source_port, dest_port)
        self._scene.addItem(wire)
        connection = Connection(source_port, dest_port, wire)
        self._connections.append(connection)

        # Update coherent mode checkboxes (topology may have changed)
        self._update_coherent_checkboxes()
        self.notify_changed()
        return connection

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
        - Source is an OutputPort that is not already connected
        - Destination is an InputPort (it may already receive other beams)
        - Ports belong to different components
        - The connection does not close a loop

        Args:
            source_port: Port where connection starts
            dest_port: Port where connection ends

        Returns:
            bool: True if connection is valid
        """
        if not isinstance(source_port, OutputPort):
            return False
        if not isinstance(dest_port, InputPort):
            return False

        if source_port.connections:
            return False

        source_component = source_port._parent_item
        dest_component = dest_port._parent_item
        if source_component is dest_component:
            return False

        # Reject if the source is already reachable from the destination
        downstream = {}
        for src, _, dest in self._apparatus_graph:
            downstream.setdefault(src, []).append(dest)
        stack, seen = [dest_component], set()
        while stack:
            component = stack.pop()
            if component is source_component:
                return False
            if component not in seen:
                seen.add(component)
                stack.extend(downstream.get(component, []))

        return True

    @property
    def _apparatus_graph(self):
        """Connections as (source_component, output_index, dest_component) tuples."""
        graph = []
        for connection in self._connections:
            source = connection.source_port._parent_item
            graph.append((
                source,
                source.output_ports.index(connection.source_port),
                connection.dest_port._parent_item,
            ))
        return graph

    def delete_wire(self, wire_item: WireItem):
        """
        Delete a wire connection.

        Removes the wire from the scene, detaches it from its ports and
        removes it from the connections list.

        Args:
            wire_item: The WireItem to delete
        """
        connection = next(
            (conn for conn in self._connections if conn.wire_item is wire_item), None
        )

        if connection is not None:
            connection.source_port.connections.remove(connection)
            connection.dest_port.connections.remove(connection)
            self._connections.remove(connection)

        self._scene.removeItem(wire_item)

        # Update coherent mode checkboxes (topology may have changed)
        self._update_coherent_checkboxes()
        self.notify_changed()

    def delete_component(self, component):
        """Remove a component and all its connected wires from the canvas."""
        all_ports = component.input_ports + component.output_ports
        for conn in list(self._connections):
            if conn.source_port in all_ports or conn.dest_port in all_ports:
                self.delete_wire(conn.wire_item)

        # Remove from component list and scene
        self._components = [c for c in self._components if c is not component]
        self._scene.removeItem(component)
        self.notify_changed()

    def run_batch(self, n: int = 10_000):
        """
        Run batch simulation of n particles through the apparatus.

        Counters are reset first, then each particle's final destination is
        drawn from the exact outcome probabilities.

        Args:
            n: Number of particles to simulate (default: 10,000)
        """
        self.reset_counts()
        self.highlight_path_to(None)
        self._fire(n)
        self._mode = "Batch"
        self.notify_changed()

    def run_single(self):
        """
        Fire one particle and highlight the beam paths that could have carried it.

        Where beams recombine a particle has no single path, so every wire on a
        path from the gun to the counter that fired is highlighted.
        """
        fired = self._fire(1)
        terminal = next((t for t, count in fired if count), None)
        self.highlight_path_to(terminal if terminal is not LOST else None)
        self._mode = "Single"
        self.notify_changed()

    def highlight_path_to(self, counter):
        """Highlight the wires on any path from the gun to counter (None clears)."""
        on_path = set()
        if counter is not None:
            graph = self._apparatus_graph
            gun = next((c for c in self._components if isinstance(c, ParticleGun)), None)
            forward = self._reachable(gun, [(src, dest) for src, _, dest in graph])
            backward = self._reachable(counter, [(dest, src) for src, _, dest in graph])
            on_path = {
                (src, dest) for src, _, dest in graph
                if src in forward and dest in backward
            }

        for connection in self._connections:
            edge = (connection.source_port._parent_item, connection.dest_port._parent_item)
            connection.wire_item.set_highlighted(edge in on_path)

    @staticmethod
    def _reachable(start, edges) -> set:
        """Components reachable from start along edges, including start itself."""
        if start is None:
            return set()
        following = {}
        for src, dest in edges:
            following.setdefault(src, []).append(dest)
        seen, stack = set(), [start]
        while stack:
            node = stack.pop()
            if node not in seen:
                seen.add(node)
                stack.extend(following.get(node, []))
        return seen

    def reset_counts(self):
        """Reset all counter displays, shares and the fired total to zero."""
        for component in self._components:
            if isinstance(component, ParticleCounter):
                component.reset()
        self._particles_fired = 0
        self._mode = "Ready"
        self.notify_changed()

    def notify_changed(self):
        """Announce that the apparatus or the counts changed."""
        self.scene_changed.emit()

    def spin_type(self) -> float | None:
        """Spin type of the gun that fires, or None if there is no gun."""
        gun = next((c for c in self._components if isinstance(c, ParticleGun)), None)
        return None if gun is None else gun.get_spin_type()

    def particles_fired(self) -> int:
        """Particles fired since the counters were last reset."""
        return self._particles_fired

    def mode(self) -> str:
        """How the last particles were fired: "Batch", "Single" or "Ready"."""
        return self._mode

    def add_gun(self, x: float | None = None, y: float | None = None):
        """
        Add a new particle gun to the canvas.

        Args:
            x, y: Scene position; omitted places it at the next free slot
        """
        gun = ParticleGun()

        gun_out = OutputPort(gun, eigenvalue=0.5)
        gun_out.position_on_right_edge(vertical_offset=0)
        gun.output_ports = [gun_out]

        return self._place(gun, x, y)

    def add_analyzer(self, spin_type: float = 0.5, x: float | None = None,
                     y: float | None = None, axis_label: str = "+z",
                     phi_deg: float = 0.0):
        """
        Add a new Stern-Gerlach analyzer to the canvas.

        Args:
            spin_type: Spin type for the analyzer (0.5 or 1.0, default 0.5)
            x, y: Scene position; omitted places it at the next free slot
            axis_label: Measurement axis label (default "+z")
            phi_deg: Angle in the x-y plane for a custom axis
        """
        analyzer = SternGerlachAnalyzer(
            axis_label=axis_label, phi_deg=phi_deg, spin_type=spin_type
        )

        # Create ports: 1 input, multiple outputs based on spin type (Req 26)
        analyzer_in = InputPort(analyzer)
        analyzer_in.position_on_left_edge(vertical_offset=0)
        analyzer.input_ports = [analyzer_in]

        if spin_type == 0.5:
            # Spin-1/2: 2 ports labeled "+" and "−"
            eigenvalues, offsets = [0.5, -0.5], [-15, 15]
        else:
            # Spin-1: 3 ports labeled "+1", "0", "−1"
            eigenvalues, offsets = [1.0, 0.0, -1.0], [-20, 0, 20]
        analyzer.output_ports = []
        for eigenvalue, offset in zip(eigenvalues, offsets):
            port = OutputPort(analyzer, eigenvalue=eigenvalue)
            port.position_on_right_edge(vertical_offset=offset)
            analyzer.output_ports.append(port)

        return self._place(analyzer, x, y)

    def add_magnet(self, x: float | None = None, y: float | None = None):
        """
        Add a new spin rotation magnet to the canvas.

        Args:
            x, y: Scene position; omitted places it at the next free slot
        """
        magnet = SpinRotationMagnet()

        # Create ports: 1 input, 1 output (no beam splitting)
        magnet_in = InputPort(magnet)
        magnet_in.position_on_left_edge(vertical_offset=0)
        magnet.input_ports = [magnet_in]

        magnet_out = OutputPort(magnet, eigenvalue=0.5)
        magnet_out.position_on_right_edge(vertical_offset=0)
        magnet.output_ports = [magnet_out]

        return self._place(magnet, x, y)

    def add_counter(self, x: float | None = None, y: float | None = None,
                    label: str = "Counter"):
        """
        Add a new particle counter to the canvas.

        Args:
            x, y: Scene position; omitted places it at the next free slot
            label: Counter label
        """
        counter = ParticleCounter(label=label)

        # Create ports: 1 input (terminal component)
        counter_in = InputPort(counter)
        counter_in.position_on_left_edge(vertical_offset=0)
        counter.input_ports = [counter_in]

        return self._place(counter, x, y)

    def _place(self, component, x, y):
        """Position a new component, add it to the scene and return it."""
        if x is None or y is None:
            x, y = self._next_component_x, self._next_component_y
            self._next_component_x += 150
            if self._next_component_x > 500:
                self._next_component_x = 100
                self._next_component_y += 100
        component.setPos(x, y)

        self._scene.addItem(component)
        self._components.append(component)
        self.notify_changed()
        return component

    def _update_coherent_checkboxes(self):
        """
        Update the visibility of coherent mode checkboxes on all analyzers.

        Checkboxes are shown only on analyzers whose input receives more than
        one beam (recombination points).
        """
        incoming = {}
        for _, _, dest in self._apparatus_graph:
            incoming[dest] = incoming.get(dest, 0) + 1
        for component in self._components:
            if isinstance(component, SternGerlachAnalyzer):
                component.update_coherent_checkbox_visibility(incoming.get(component, 0) > 1)

    def outcome_probabilities(self) -> dict:
        """
        Exact probability of a particle ending at each counter.

        Returns:
            dict: {ParticleCounter or LOST: probability}; LOST collects particles
                  leaving through unconnected outputs. Empty if there is no gun.
        """
        gun = next((c for c in self._components if isinstance(c, ParticleGun)), None)
        if gun is None:
            return {}
        return outcome_probabilities(gun, gun.emit(), self._apparatus_graph)

    def _fire(self, n: int) -> list:
        """
        Fire n particles and add them to the counters where they are detected.

        Returns:
            list of (terminal, count) pairs; the terminal is LOST for particles
            that left through an unconnected output
        """
        probs = self.outcome_probabilities()
        if not probs:
            return []
        terminals = list(probs)
        counts = np.random.multinomial(n, [probs[t] for t in terminals])
        for terminal, count in zip(terminals, counts):
            if terminal is not LOST and count:
                terminal.increment(int(count))
        self._particles_fired += n
        self._update_counter_shares()
        return list(zip(terminals, (int(count) for count in counts)))

    def _update_counter_shares(self):
        """Give each counter its share of all counted particles (Req 20)."""
        counters = [c for c in self._components if isinstance(c, ParticleCounter)]
        total = sum(counter.get_count() for counter in counters)
        for counter in counters:
            counter.set_share(counter.get_count() / total if total else 0.0)

    def _build_default_scene(self):
        """Build the default apparatus: Gun → SG_z → Counter(+z) + Counter(−z).

        The gun fires |+z⟩ so the scene opens on Experiment 1 (Req 21): measuring
        Sz on a beam prepared in |+z⟩ gives 100% in the upper counter. Guns added
        from the toolbar start in |+x⟩ instead.
        """
        gun = self.add_gun(50, 150)
        gun.set_initial_state(SpinState.HALF_PLUS_Z.copy())
        sg_z = self.add_analyzer(0.5, 200, 150, axis_label="+z")
        counter_upper = self.add_counter(350, 100, label="Counter(+z)")
        counter_lower = self.add_counter(350, 200, label="Counter(-z)")

        self.connect_ports(gun.output_ports[0], sg_z.input_ports[0])
        self.connect_ports(sg_z.output_ports[0], counter_upper.input_ports[0])  # +z
        self.connect_ports(sg_z.output_ports[1], counter_lower.input_ports[0])  # -z

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
                unknown = component.get_unknown_label()
                if unknown:
                    # Save the letter only, so the file does not reveal the state
                    comp_data["unknown"] = unknown
                else:
                    # JSON has no complex type: store each amplitude as [re, im]
                    comp_data["state_vector"] = [
                        [amp.real, amp.imag] for amp in component.get_initial_state_vector()
                    ]

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

        Raises:
            ValueError: If the data is not a valid scene
        """
        # Validate version
        if data.get("version") != 1:
            raise ValueError(f"Unsupported file version: {data.get('version')}")

        # Clear current scene
        self.clear_scene()

        # Map from serialized ID to recreated component
        id_to_component = {}

        for comp_data in data["components"]:
            comp_type = comp_data["type"]
            x = comp_data["x"]
            y = comp_data["y"]

            if comp_type == "gun":
                component = self.add_gun(x, y)
                component.set_spin_type(comp_data["spin_type"])
                unknown = comp_data.get("unknown")
                if unknown:
                    if unknown not in UNKNOWN_STATES:
                        raise ValueError(f"Unknown state: {unknown}")
                    component.set_initial_state(UNKNOWN_STATES[unknown].copy(), unknown)
                else:
                    component.set_initial_state(np.array(
                        [complex(*amp) for amp in comp_data["state_vector"]], dtype=complex
                    ))

            elif comp_type == "analyzer":
                component = self.add_analyzer(
                    comp_data["spin_type"], x, y,
                    axis_label=comp_data["axis_label"], phi_deg=comp_data["phi_deg"],
                )
                component.coherent_mode = comp_data.get("coherent_mode", False)

            elif comp_type == "magnet":
                component = self.add_magnet(x, y)
                component.set_beta(comp_data["beta"])

            elif comp_type == "counter":
                component = self.add_counter(x, y, label=comp_data.get("label", "Counter"))
                component.set_count(comp_data.get("count", 0))

            else:
                raise ValueError(f"Unknown component type: {comp_type}")

            id_to_component[comp_data["id"]] = component

        for conn_data in data["connections"]:
            source_comp = id_to_component[conn_data["source_id"]]
            dest_comp = id_to_component[conn_data["dest_id"]]
            source_port = source_comp.output_ports[conn_data["output_index"]]
            dest_port = dest_comp.input_ports[0]  # All components have single input
            if self.connect_ports(source_port, dest_port) is None:
                raise ValueError("File contains an invalid connection")

    def clear_scene(self):
        """Clear all components and connections from the scene."""
        for component in list(self._components):
            self.delete_component(component)

        # Reset component placement position
        self._next_component_x = 100
        self._next_component_y = 100

    def new_scene(self):
        """Replace everything on the canvas with the default apparatus."""
        self.clear_scene()
        self._build_default_scene()

    def _export_rect(self) -> QRectF:
        """Bounds of the apparatus with a small margin, for image export."""
        padding = 20
        return self._scene.itemsBoundingRect().adjusted(-padding, -padding, padding, padding)

    def export_to_png(self, file_path: str):
        """
        Export the current scene to a PNG image.

        Args:
            file_path: Path to save the PNG file

        Only the apparatus is exported, not the whole empty scene rect, and it is
        rendered at 2x for a crisp image in a student lab report.
        """
        export_rect = self._export_rect()
        scale_factor = 2.0
        image = QImage(
            int(export_rect.width() * scale_factor),
            int(export_rect.height() * scale_factor),
            QImage.Format.Format_ARGB32,
        )
        image.fill(Qt.GlobalColor.white)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self._scene.render(painter, QRectF(), export_rect)
        painter.end()

        if not image.save(file_path, "PNG"):
            raise OSError(f"Could not write {file_path}")

    def export_to_pdf(self, file_path: str):
        """
        Export the current scene to a PDF, as vector graphics.

        Args:
            file_path: Path to save the PDF file
        """
        export_rect = self._export_rect()

        writer = QPdfWriter(file_path)
        writer.setResolution(300)
        writer.setPageSize(QPageSize(
            QSizeF(export_rect.width(), export_rect.height()),
            QPageSize.Unit.Point, "apparatus", QPageSize.SizeMatchPolicy.ExactMatch,
        ))
        writer.setPageMargins(QMarginsF(0, 0, 0, 0))

        painter = QPainter(writer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._scene.render(painter, QRectF(), export_rect)
        painter.end()
