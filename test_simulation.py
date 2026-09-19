#!/usr/bin/env python3
"""
Quick test of the batch simulation engine.

Expected result for hardcoded apparatus (Gun→SG_z→Counter(+z)+Counter(-z)):
- Gun emits |+z⟩ state
- SG_z measures along z-axis
- Counter(+z) should get ~10,000 counts (100% probability)
- Counter(-z) should get ~0 counts (0% probability)
"""

import sys
from PySide6.QtWidgets import QApplication
from pyspins.ui.canvas import ExperimentCanvas

# Create minimal Qt application
app = QApplication(sys.argv)

# Create canvas with hardcoded apparatus
canvas = ExperimentCanvas()

# Run batch simulation
print("Running batch simulation with 10,000 particles...")
canvas.run_batch(n=10_000)

# Check counter values
from pyspins.ui.components.counter import ParticleCounter

counters = [c for c in canvas._components if isinstance(c, ParticleCounter)]

for counter in counters:
    label = counter._label  # Access internal label to see which counter
    count = counter.get_count()
    print(f"{label}: {count} counts")

# Verify expected results
# Gun emits |+z⟩, SG_z measures z-axis
# Expected: Counter(+z) ≈ 10,000, Counter(-z) ≈ 0
if len(counters) == 2:
    # Find counters by position (upper is +z, lower is -z)
    # Based on _build_default_scene: counter_upper_y = 100, counter_lower_y = 200
    upper_counter = min(counters, key=lambda c: c.y())
    lower_counter = max(counters, key=lambda c: c.y())

    upper_count = upper_counter.get_count()
    lower_count = lower_counter.get_count()

    print(f"\nVerification:")
    print(f"Upper counter (+z): {upper_count}")
    print(f"Lower counter (-z): {lower_count}")
    print(f"Total: {upper_count + lower_count}")

    # For |+z⟩ measured on z-axis, we expect 100% in +z, 0% in -z
    if upper_count == 10_000 and lower_count == 0:
        print("\n✅ PASS: Simulation produced expected results!")
        sys.exit(0)
    else:
        print(f"\n❌ FAIL: Expected upper=10000, lower=0")
        sys.exit(1)
else:
    print(f"\n❌ FAIL: Expected 2 counters, found {len(counters)}")
    sys.exit(1)
