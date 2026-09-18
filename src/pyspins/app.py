import sys
from PySide6.QtWidgets import QApplication
from pyspins.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
