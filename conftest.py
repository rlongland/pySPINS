"""Top-level pytest configuration.

Qt tests run on the offscreen platform so no display is needed.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
