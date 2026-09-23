from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox
from PySide6.QtCore import Qt


class AboutDialog(QDialog):
    """About dialog showing application information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About pySPINS")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # Create text browser for HTML content
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)  # Allow clicking links
        browser.setHtml(self._get_about_html())

        layout.addWidget(browser)

        # Add OK button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _get_about_html(self) -> str:
        """Generate HTML content for the About dialog."""
        return """
        <html>
        <head>
        <style>
            body {
                font-family: sans-serif;
                margin: 20px;
            }
            h1 {
                color: #1565c0;
                font-size: 24px;
                margin-bottom: 10px;
            }
            h2 {
                color: #424242;
                font-size: 18px;
                margin-top: 20px;
                margin-bottom: 10px;
            }
            .version {
                color: #757575;
                font-size: 14px;
                margin-bottom: 20px;
            }
            .info-section {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }
            .label {
                font-weight: bold;
                color: #424242;
            }
            a {
                color: #1565c0;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .acknowledgment {
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #1565c0;
            }
        </style>
        </head>
        <body>
            <h1>pySPINS</h1>
            <div class="version">Version 0.1.0</div>

            <div class="info-section">
                <p><span class="label">Description:</span> Interactive Stern-Gerlach quantum spin simulation for physics education</p>
                <p><span class="label">Author:</span> Richard Longland</p>
                <p><span class="label">License:</span> MIT License</p>
            </div>

            <h2>About This Application</h2>
            <p>
                pySPINS is a Python/Qt port of the Open Source Physics (OSP) SPINS simulation,
                designed to help students understand quantum mechanics through interactive
                Stern-Gerlach experiments.
            </p>

            <p>
                Build apparatus by connecting particle guns, Stern-Gerlach analyzers,
                spin rotation magnets, and particle counters. Run single particles or batch
                simulations to explore quantum measurement, state collapse, and coherent recombination.
            </p>

            <h2>Features</h2>
            <ul>
                <li>Spin-1/2 and spin-1 particle simulations</li>
                <li>Drag-and-connect graphical apparatus builder</li>
                <li>Correct quantum mechanics including coherent recombination</li>
                <li>Standard OSP SPINS curriculum experiments (1-5)</li>
                <li>Save and load apparatus configurations</li>
            </ul>

            <div class="acknowledgment">
                <h2 style="margin-top: 0;">Acknowledgments</h2>
                <p>
                    This application is based on the
                    <a href="https://sites.science.oregonstate.edu/~mcintyre/ph425/spins/index_SPINS_OSP.html">
                    OSP SPINS Stern-Gerlach simulation</a> developed by the Paradigms in Physics group
                    at Oregon State University.
                </p>
                <p>
                    pySPINS is an independent reimplementation written from published
                    descriptions of the OSP SPINS program; it contains no code from the
                    original. It follows the OSP pedagogical approach and experiment design.
                </p>
                <p>
                    For more information, visit:
                    <br>
                    <a href="https://sites.science.oregonstate.edu/~mcintyre/ph425/spins/">
                    OSP SPINS Documentation</a>
                </p>
            </div>

            <h2>Resources</h2>
            <ul>
                <li><a href="https://github.com/rlongland/pyspins">Source Code Repository</a></li>
                <li><a href="https://pypi.org/project/pyspins/">PyPI Package</a></li>
                <li><a href="https://sites.science.oregonstate.edu/~mcintyre/ph425/spins/">
                    Original OSP SPINS</a></li>
            </ul>

            <p style="margin-top: 30px; color: #757575; font-size: 12px;">
                Copyright © 2026 Richard Longland<br>
                Released under the MIT License
            </p>
        </body>
        </html>
        """
