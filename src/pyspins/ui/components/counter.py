"""Counter component - terminal component that counts detected particles."""

from pyspins.physics.states import SpinState
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

    def simulate(self, state: SpinState, output_index: int = 0):
        """
        Count the particle (terminal component).

        Args:
            state: Incoming SpinState (acknowledged but not modified)
            output_index: Ignored (counters have no outputs)

        Returns:
            None (terminal component)
        """
        # Counter is terminal - doesn't output anything
        return None

    def increment(self):
        """Increment the counter by one."""
        self._count += 1
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
