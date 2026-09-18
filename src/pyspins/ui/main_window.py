from PySide6.QtWidgets import QMainWindow, QToolBar, QAction, QLabel
from pyspins.ui.canvas import ExperimentCanvas


class MainWindow(QMainWindow):
    """Main application window for pySPINS."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("pySPINS")
        self.resize(1024, 700)

        self._canvas = ExperimentCanvas(self)
        self.setCentralWidget(self._canvas)

        # Simulation toolbar
        sim_toolbar = QToolBar("Simulation")
        self.addToolBar(sim_toolbar)
        run_batch = QAction("Run Batch (10k)", self)
        run_single = QAction("Run Single", self)
        reset = QAction("Reset Counts", self)
        run_batch.triggered.connect(self._canvas.run_batch)
        run_single.triggered.connect(self._canvas.run_single)
        reset.triggered.connect(self._canvas.reset_counts)
        for a in (run_batch, run_single, reset):
            sim_toolbar.addAction(a)

        # Component toolbar
        comp_toolbar = QToolBar("Add Components")
        self.addToolBar(comp_toolbar)
        add_gun = QAction("Add Gun", self)
        add_analyzer = QAction("Add Analyzer", self)
        add_magnet = QAction("Add Magnet", self)
        add_counter = QAction("Add Counter", self)
        add_gun.triggered.connect(self._canvas.add_gun)
        add_analyzer.triggered.connect(self._canvas.add_analyzer)
        add_magnet.triggered.connect(self._canvas.add_magnet)
        add_counter.triggered.connect(self._canvas.add_counter)
        for a in (add_gun, add_analyzer, add_magnet, add_counter):
            comp_toolbar.addAction(a)

        self._status = QLabel("Spin-1/2 | Ready")
        self.statusBar().addWidget(self._status)
