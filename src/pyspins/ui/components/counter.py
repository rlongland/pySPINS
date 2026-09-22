"""Counter component - terminal component that counts detected particles."""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor

from .base import ApparatusItem


class ParticleCounter(ApparatusItem):
    """
    Particle counter - terminal component that counts detected particles.

    Displays the count in large digits. Has one input port, no output ports.
    """

    # Visual style per Req 25
    COLOR = "#2e7d32"  # Dark green

    def __init__(self, x: float = 0, y: float = 0, label: str = "Counter"):
        """
        Initialize particle counter.

        Args:
            x: Initial x position on canvas
            y: Initial y position on canvas
            label: Optional label (e.g., "Counter(+z)", "Counter(-z)")
        """
        super().__init__(label=label, color=self.COLOR, x=x, y=y)

        self._count = 0
        # Share of all counted particles, drawn as a fill bar (Req 20)
        self._share = 0.0
        self._update_label()

        # Counter has one input port (left), no output ports
        # Ports will be created in Phase 2 Task 2.5
        self.input_ports = []  # Will be populated when Port class exists
        self.output_ports = []  # Counters are terminal - no outputs

    def transfer(self, vector, s: float):
        """Counters are terminal: the particle is detected here."""
        return None

    def increment(self, n: int = 1):
        """Increment the counter by n (default one)."""
        self._count += n
        self._update_label()

    def reset(self):
        """Reset the counter to zero."""
        self._count = 0
        self._share = 0.0
        self._update_label()

    def set_share(self, share: float):
        """
        Set this counter's share of all counted particles.

        Args:
            share: Fraction from 0 to 1, shown as a percentage and a fill bar
        """
        self._share = share
        self._update_label()
        self.update()

    def get_share(self) -> float:
        """This counter's share of all counted particles."""
        return self._share

    def get_count(self) -> int:
        """Get the current count."""
        return self._count

    def set_count(self, count: int):
        """
        Set the counter to a specific value.

        Args:
            count: New count value
        """
        self._count = count
        self._update_label()

    def _update_label(self):
        """Show the count, with its percentage of the total once anything is counted."""
        if self._count and self._share:
            self.set_label(f"{self._count}\n{self._share * 100:.1f}%")
        else:
            self.set_label(str(self._count))

    def paint(self, painter, option, widget=None):
        """Draw the counter, with a progress-bar style fill for its share (Req 20)."""
        super().paint(painter, option, widget)
        if self._share <= 0:
            return
        height, margin = 6, 4
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#a5d6a7")))
        painter.drawRoundedRect(
            QRectF(margin, self.HEIGHT - height - margin,
                   (self.WIDTH - 2 * margin) * self._share, height),
            2, 2,
        )
