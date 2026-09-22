"""Counter component - terminal component that counts detected particles."""

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
        self._update_label()

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
        """Update the displayed label with current count."""
        # Display count in large digits
        # Format: just the number for simplicity in Phase 2
        # Phase 3+ may add more styling
        self.set_label(str(self._count))
