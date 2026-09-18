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

        toolbar = QToolBar("Simulation")
        self.addToolBar(toolbar)
        run_batch = QAction("Run Batch (10k)", self)
        run_single = QAction("Run Single", self)
        reset = QAction("Reset Counts", self)
        run_batch.triggered.connect(self._canvas.run_batch)
        run_single.triggered.connect(self._canvas.run_single)
        reset.triggered.connect(self._canvas.reset_counts)
        for a in (run_batch, run_single, reset):
            toolbar.addAction(a)

        self._status = QLabel("Spin-1/2 | Ready")
        self.statusBar().addWidget(self._status)
