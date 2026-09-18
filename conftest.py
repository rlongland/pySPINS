"""Top-level pytest configuration.

In headless environments that lack libEGL.so.1, pytest-qt fails to load.
The physics tests (Phase 1) have no Qt dependency; to run them in a headless
environment temporarily uninstall pytest-qt before running pytest:

    pip uninstall pytest-qt && pytest tests/ && pip install pytest-qt
"""
