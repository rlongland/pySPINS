"""Particle gun component - emits particles in a specified spin state."""

import numpy as np
from pyspins.physics.states import SpinState
from .base import ApparatusItem


class ParticleGun(ApparatusItem):
    """
    Particle gun that emits particles in a specified spin state.

    For Phase 2 scaffold: emits spin-1/2 particles in |+z⟩ state.
    Phase 3 will add state selection dialog.
    """

    # Visual style per Req 25
    COLOR = "#1a237e"  # Dark blue

    def __init__(self, x: float = 0, y: float = 0):
        """
        Initialize particle gun.

        Args:
            x: Initial x position on canvas
            y: Initial y position on canvas
        """
        super().__init__(label="Gun", color=self.COLOR, x=x, y=y)

        # Default state: spin-1/2 |+z⟩
        self._spin_type = 0.5
        self._initial_state_vector = SpinState.HALF_PLUS_Z

        # Gun has no input ports, one output port (right side)
        # Ports will be created in Phase 2 Task 2.5
        self.input_ports = []
        self.output_ports = []  # Will be populated when Port class exists

    def simulate(self, state=None, output_index: int = 0) -> SpinState:
        """
        Emit a particle in the gun's configured spin state.

        Args:
            state: Ignored (gun is always first in chain)
            output_index: Ignored (gun has single output)

        Returns:
            SpinState: The initial state configured for this gun
        """
        return SpinState(self._initial_state_vector, self._spin_type)

    def set_spin_type(self, s: float):
        """
        Set the spin type (0.5 or 1.0).

        Args:
            s: Spin quantum number (0.5 or 1.0)
        """
        if s not in (0.5, 1.0):
            raise ValueError("Spin type must be 0.5 or 1.0")
        self._spin_type = s
        # Reset to default state for new spin type
        if s == 0.5:
            self._initial_state_vector = SpinState.HALF_PLUS_Z
        else:
            self._initial_state_vector = SpinState.ONE_PLUS

    def set_initial_state(self, state_vector: np.ndarray):
        """
        Set the initial state vector the gun will emit.

        Args:
            state_vector: Complex numpy array representing the state
        """
        self._initial_state_vector = state_vector
