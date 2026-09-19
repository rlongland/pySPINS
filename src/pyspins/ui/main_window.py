from PySide6.QtWidgets import QMainWindow, QToolBar, QLabel, QFileDialog, QMessageBox
from PySide6.QtGui import QAction, QKeySequence, QIcon
from pyspins.ui.canvas import ExperimentCanvas
from pyspins.ui.dialogs import PhysicsReferenceDialog
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

        # Create menu bar
        self._create_menu_bar()

        # Simulation toolbar
        sim_toolbar = QToolBar("Simulation")
        self.addToolBar(sim_toolbar)
        run_batch = QAction(self._load_icon("run_batch.svg"), "Run Batch (10k)", self)
        run_single = QAction(self._load_icon("run_single.svg"), "Run Single", self)
        reset = QAction(self._load_icon("reset.svg"), "Reset Counts", self)
        run_batch.triggered.connect(lambda: self._canvas.run_batch())
        run_single.triggered.connect(lambda: self._canvas.run_single())
        reset.triggered.connect(lambda: self._canvas.reset_counts())
        for a in (run_batch, run_single, reset):
            sim_toolbar.addAction(a)

        # Component toolbar (Req 26: separate buttons for spin-1/2 and spin-1 analyzers)
        comp_toolbar = QToolBar("Add Components")
        self.addToolBar(comp_toolbar)
        add_gun = QAction(self._load_icon("add_gun.svg"), "Add Gun", self)
        add_analyzer_half = QAction(self._load_icon("add_analyzer.svg"), "Add Analyzer (s=1/2)", self)
        add_analyzer_one = QAction(self._load_icon("add_analyzer.svg"), "Add Analyzer (s=1)", self)
        add_magnet = QAction(self._load_icon("add_magnet.svg"), "Add Magnet", self)
        add_counter = QAction(self._load_icon("add_counter.svg"), "Add Counter", self)
        add_gun.triggered.connect(self._canvas.add_gun)
        add_analyzer_half.triggered.connect(lambda: self._canvas.add_analyzer(spin_type=0.5))
        add_analyzer_one.triggered.connect(lambda: self._canvas.add_analyzer(spin_type=1.0))
        add_magnet.triggered.connect(self._canvas.add_magnet)
        add_counter.triggered.connect(self._canvas.add_counter)
        for a in (add_gun, add_analyzer_half, add_analyzer_one, add_magnet, add_counter):
            comp_toolbar.addAction(a)

        self._status = QLabel("Spin-1/2 | Ready")
        self.statusBar().addWidget(self._status)

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
        """Create the menu bar with File and Help menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Save action (Ctrl+S)
        save_action = QAction(self._load_icon("save.svg"), "&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        # Save As action (Ctrl+Shift+S)
        save_as_action = QAction(self._load_icon("save.svg"), "Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)

        # Open action (Ctrl+O)
        open_action = QAction(self._load_icon("open.svg"), "&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # Physics Reference action
        physics_ref_action = QAction("&Physics Reference", self)
        physics_ref_action.triggered.connect(self._on_physics_reference)
        help_menu.addAction(physics_ref_action)

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
