"""Physics reference dialog displaying quantum measurement postulates."""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox
from PySide6.QtCore import Qt


class PhysicsReferenceDialog(QDialog):
    """Dialog displaying quantum mechanics reference for Stern-Gerlach experiments.

    Provides a summary of measurement postulates, state representation,
    and key concepts for understanding the simulation.
    """

    def __init__(self, parent=None):
        """Initialize physics reference dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Physics Reference — Quantum Measurement")
        self.setModal(True)
        self.resize(700, 600)

        # Main layout
        layout = QVBoxLayout(self)

        # Text browser for HTML content
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.setHtml(self._get_reference_html())
        layout.addWidget(self._browser)

        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _get_reference_html(self) -> str:
        """Generate HTML content for physics reference.

        Returns:
            HTML string with formatted physics reference
        """
        return """
        <html>
        <head>
            <style>
                body { font-family: sans-serif; font-size: 11pt; line-height: 1.5; }
                h1 { color: #1a237e; font-size: 18pt; margin-top: 0; }
                h2 { color: #1565c0; font-size: 14pt; margin-top: 16pt; margin-bottom: 8pt; }
                h3 { color: #424242; font-size: 12pt; margin-top: 12pt; margin-bottom: 6pt; }
                p { margin: 8pt 0; }
                ul { margin: 4pt 0; padding-left: 24pt; }
                li { margin: 4pt 0; }
                .equation {
                    font-family: 'Courier New', monospace;
                    background: #f5f5f5;
                    padding: 8pt;
                    margin: 8pt 0;
                    border-left: 3px solid #1565c0;
                }
                .key-point {
                    background: #e3f2fd;
                    padding: 8pt;
                    margin: 8pt 0;
                    border-radius: 4px;
                }
            </style>
        </head>
        <body>
            <h1>Quantum Measurement in Stern-Gerlach Experiments</h1>

            <h2>1. State Representation</h2>
            <p>Spin states are represented as normalized complex vectors in a finite-dimensional Hilbert space:</p>
            <div class="equation">
                Spin-1/2: |ψ⟩ = α|+⟩ + β|−⟩  where |α|² + |β|² = 1<br>
                Spin-1:   |ψ⟩ = α|+1⟩ + β|0⟩ + γ|−1⟩  where |α|² + |β|² + |γ|² = 1
            </div>
            <p>The coefficients α, β, γ are complex numbers called probability amplitudes.</p>

            <h2>2. Measurement Postulate (Born Rule)</h2>
            <p>When measuring spin along axis <b>n̂</b>, the probability of obtaining eigenvalue <i>m</i> is:</p>
            <div class="equation">
                P(m) = |⟨m|ψ⟩|²
            </div>
            <p>where |m⟩ is the eigenstate of operator <b>n̂·S</b> with eigenvalue <i>m</i>.</p>

            <div class="key-point">
                <b>Key Point:</b> Measurement is probabilistic. Each particle's outcome is random,
                but probabilities are determined by the quantum state. Run many particles (batch mode)
                to see the statistical distribution.
            </div>

            <h2>3. State Collapse</h2>
            <p>After measurement yields eigenvalue <i>m</i>, the state instantly collapses:</p>
            <div class="equation">
                |ψ⟩  →  |m⟩
            </div>
            <p>This is a non-unitary, irreversible process. Subsequent measurements along the same
            axis always give the same result.</p>

            <h2>4. Spin Operators</h2>
            <p>The angular momentum operators satisfy the fundamental commutation relation:</p>
            <div class="equation">
                [Sₓ, Sᵧ] = i ℏ Sᵤ  (and cyclic permutations)
            </div>
            <p>In this simulation, ℏ = 1 (natural units). The eigenvalues are:</p>
            <ul>
                <li><b>Spin-1/2:</b> m = ±1/2</li>
                <li><b>Spin-1:</b> m = +1, 0, −1</li>
            </ul>

            <h2>5. Spin Rotation (Magnet Component)</h2>
            <p>A magnetic field oriented along the x-axis rotates the spin state via the unitary operator:</p>
            <div class="equation">
                R(β) = exp(−i β Sₓ / ℏ)
            </div>
            <p>This is a <i>unitary</i> transformation (reversible) that changes the state continuously
            without measurement. The angle β is in radians.</p>

            <h2>6. Coherent Recombination</h2>
            <p>When two output beams from a Stern-Gerlach analyzer are brought back together
            <i>before measurement</i>, quantum interference can occur:</p>
            <div class="key-point">
                <b>Coherent Mode (checkbox enabled):</b> Amplitudes are summed before the final measurement.
                The intermediate analyzer does not collapse the state — both paths contribute to a quantum superposition.<br><br>
                <b>Incoherent Mode (checkbox disabled):</b> Each particle is measured at the intermediate analyzer.
                The beams represent a classical mixture, not a quantum superposition.
            </div>
            <p>Experiment 4 demonstrates this difference: coherent recombination can give 100% probability
            for one outcome, while incoherent gives 50/50.</p>

            <h2>7. Standard Experiments</h2>
            <ul>
                <li><b>Experiment 1:</b> Verify |+z⟩ through SG_z gives 100% upper beam</li>
                <li><b>Experiment 2:</b> Verify |+z⟩ through SG_x gives 50/50 split</li>
                <li><b>Experiment 3:</b> Sequential measurements (e.g., SG_z → SG_x → SG_z) demonstrate state collapse</li>
                <li><b>Experiment 4:</b> Coherent recombination shows quantum interference</li>
                <li><b>Experiment 5:</b> Spin rotation with magnet shows continuous state evolution</li>
            </ul>

            <h2>References</h2>
            <p>For more details, see:</p>
            <ul>
                <li>Griffiths, <i>Introduction to Quantum Mechanics</i>, Chapter 4</li>
                <li>McIntyre, Manogue, Tate, <i>Quantum Mechanics: A Paradigms Approach</i></li>
                <li>OSP SPINS documentation:
                    <a href="https://sites.science.oregonstate.edu/~mcintyre/ph425/spins/">
                    oregonstate.edu/~mcintyre/ph425/spins/</a>
                </li>
            </ul>
        </body>
        </html>
        """
