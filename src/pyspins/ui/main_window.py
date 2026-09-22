from PySide6.QtWidgets import QMainWindow, QToolBar, QLabel, QFileDialog, QMessageBox
from PySide6.QtGui import QAction, QKeySequence, QIcon
from pyspins.ui.canvas import ExperimentCanvas
from pyspins.ui.dialogs import PhysicsReferenceDialog, AboutDialog
import json
from pathlib import Path


class MainWindow(QMainWindow):
    """Main application window for pySPINS."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("pySPINS")
        self.resize(1024, 700)

        self._canvas = ExperimentCanvas(self)
        self.setCentralWidget(self._canvas)

        # Track current file path for Save/Save As
        self._current_file_path = None

        # Icon base path
        self._icon_path = Path(__file__).parent.parent / "resources" / "icons"

        self._actions = {}
        self._create_actions()
        self._create_menu_bar()
        self._create_toolbars()

        self._status = QLabel()
        self.statusBar().addWidget(self._status)

    def _add_action(self, name: str, text: str, handler, icon: str = None,
                    shortcut=None) -> QAction:
        """Create an action, shared between the menus and the toolbars."""
        action = QAction(self._load_icon(icon) if icon else QIcon(), text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        action.triggered.connect(handler)
        self._actions[name] = action
        return action

    def _create_actions(self):
        """Create every menu and toolbar action (Req 18)."""
        canvas = self._canvas

        self._add_action("new", "&New", self._on_new,
                         shortcut=QKeySequence.StandardKey.New)
        self._add_action("open", "&Open...", self._on_open, "open.svg",
                         QKeySequence.StandardKey.Open)
        self._add_action("save", "&Save", self._on_save, "save.svg",
                         QKeySequence.StandardKey.Save)
        self._add_action("save_as", "Save &As...", self._on_save_as, "save.svg",
                         QKeySequence.StandardKey.SaveAs)
        self._add_action("export_png", "Export as &PNG...", self._on_export_png)
        self._add_action("export_pdf", "Export as P&DF...", self._on_export_pdf)
        self._add_action("exit", "E&xit", self.close, shortcut=QKeySequence.StandardKey.Quit)

        self._add_action("run_batch", "Run &Batch (10k)",
                         lambda: self._run(batch=True), "run_batch.svg", "F5")
        self._add_action("run_single", "Run &Single",
                         lambda: self._run(batch=False), "run_single.svg", "F6")
        self._add_action("reset", "&Reset Counts", self._on_reset, "reset.svg", "F7")

        self._add_action("add_gun", "Add Gun", lambda: canvas.add_gun(), "add_gun.svg")
        self._add_action("add_analyzer_half", "Add Analyzer (s=1/2)",
                         lambda: canvas.add_analyzer(spin_type=0.5), "add_analyzer.svg")
        self._add_action("add_analyzer_one", "Add Analyzer (s=1)",
                         lambda: canvas.add_analyzer(spin_type=1.0), "add_analyzer.svg")
        self._add_action("add_magnet", "Add Magnet", lambda: canvas.add_magnet(),
                         "add_magnet.svg")
        self._add_action("add_counter", "Add Counter", lambda: canvas.add_counter(),
                         "add_counter.svg")

        self._add_action("physics_reference", "&Physics Reference",
                         self._on_physics_reference)
        self._add_action("about", "&About pySPINS", self._on_about)

    def _create_toolbars(self):
        """Simulation and component toolbars, sharing the menu actions."""
        sim_toolbar = QToolBar("Simulation")
        self.addToolBar(sim_toolbar)
        for name in ("run_batch", "run_single", "reset"):
            sim_toolbar.addAction(self._actions[name])

        # Req 26: separate buttons for spin-1/2 and spin-1 analyzers
        comp_toolbar = QToolBar("Add Components")
        self.addToolBar(comp_toolbar)
        for name in ("add_gun", "add_analyzer_half", "add_analyzer_one",
                     "add_magnet", "add_counter"):
            comp_toolbar.addAction(self._actions[name])

    def _load_icon(self, icon_name: str) -> QIcon:
        """
        Load an icon from the resources/icons directory.

        Args:
            icon_name: Name of the icon file (without path)

        Returns:
            QIcon object, or empty QIcon if file doesn't exist
        """
        icon_file = self._icon_path / icon_name
        if icon_file.exists():
            return QIcon(str(icon_file))
        return QIcon()  # Empty icon as fallback

    def _create_menu_bar(self):
        """Create the File, Simulation and Help menus (Req 18)."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        for name in ("new", "open", "save", "save_as"):
            file_menu.addAction(self._actions[name])
        file_menu.addSeparator()
        for name in ("export_png", "export_pdf"):
            file_menu.addAction(self._actions[name])
        file_menu.addSeparator()
        file_menu.addAction(self._actions["exit"])

        sim_menu = menubar.addMenu("&Simulation")
        for name in ("run_batch", "run_single"):
            sim_menu.addAction(self._actions[name])
        sim_menu.addSeparator()
        sim_menu.addAction(self._actions["reset"])

        help_menu = menubar.addMenu("&Help")
        for name in ("physics_reference", "about"):
            help_menu.addAction(self._actions[name])

    def _on_new(self):
        """Replace the scene with the default apparatus."""
        self._canvas.new_scene()
        self._current_file_path = None
        self._status.setText("New apparatus")

    def _run(self, batch: bool):
        """Fire particles, in a batch of 10,000 or one at a time."""
        if batch:
            self._canvas.run_batch()
        else:
            self._canvas.run_single()

    def _on_reset(self):
        self._canvas.reset_counts()


    def _on_save(self):
        """Save the current scene to a file."""
        if self._current_file_path is None:
            # No file path set yet, use Save As
            self._on_save_as()
        else:
            # Save to current file
            self._save_to_file(self._current_file_path)

    def _on_save_as(self):
        """Save the current scene to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Apparatus",
            "",
            "SPINS Files (*.spins);;All Files (*)"
        )

        if file_path:
            # Ensure .spins extension
            if not file_path.endswith('.spins'):
                file_path += '.spins'

            self._save_to_file(file_path)

    def _on_open(self):
        """Open a scene from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Apparatus",
            "",
            "SPINS Files (*.spins);;All Files (*)"
        )

        if file_path:
            self._load_from_file(file_path)

    def _on_export_png(self):
        """Export the canvas as a PNG image for lab reports."""
        self._export("PNG", "png", self._canvas.export_to_png)

    def _on_export_pdf(self):
        """Export the canvas as a PDF for lab reports."""
        self._export("PDF", "pdf", self._canvas.export_to_pdf)

    def _export(self, kind: str, suffix: str, export):
        """Ask for a file name and hand it to the canvas exporter."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Export as {kind}", "", f"{kind} Images (*.{suffix});;All Files (*)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith(f".{suffix}"):
            file_path += f".{suffix}"
        try:
            export(file_path)
            self._status.setText(f"Exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export:\n{str(e)}")


    def _save_to_file(self, file_path: str):
        """
        Save the scene to a JSON file.

        Args:
            file_path: Path to save the file
        """
        try:
            # Serialize scene to dict
            scene_data = self._canvas.to_json()

            # Write to file
            with open(file_path, 'w') as f:
                json.dump(scene_data, f, indent=2)

            self._current_file_path = file_path
            self._status.setText(f"Saved to {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save file:\n{str(e)}"
            )

    def _load_from_file(self, file_path: str):
        """
        Load a scene from a JSON file.

        Args:
            file_path: Path to load the file from
        """
        try:
            # Read file
            with open(file_path, 'r') as f:
                scene_data = json.load(f)

            # Restore scene
            self._canvas.from_json(scene_data)

            self._current_file_path = file_path
            self._status.setText(f"Loaded from {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load file:\n{str(e)}"
            )

    def _on_physics_reference(self):
        """Open the Physics Reference dialog."""
        dialog = PhysicsReferenceDialog(self)
        dialog.exec()

    def _on_about(self):
        """Open the About dialog."""
        dialog = AboutDialog(self)
        dialog.exec()
