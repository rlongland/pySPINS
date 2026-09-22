"""Tests for the main window's menus, actions and exports."""

import pytest
from PySide6.QtWidgets import QToolBar

from pyspins.ui.main_window import MainWindow


@pytest.fixture
def window(qapp):
    return MainWindow()


def _menu_titles(window):
    return [action.menu().title() for action in window.menuBar().actions()]


def _item_texts(window, title):
    menu = next(a.menu() for a in window.menuBar().actions() if a.menu().title() == title)
    return [a.text() for a in menu.actions() if not a.isSeparator()]


def test_menu_bar_has_the_three_menus(window):
    assert _menu_titles(window) == ["&File", "&Simulation", "&Help"]


def test_simulation_menu_items(window):
    assert _item_texts(window, "&Simulation") == [
        "Run &Batch (10k)", "Run &Single", "&Reset Counts"
    ]


def test_file_menu_items(window):
    assert _item_texts(window, "&File") == [
        "&New", "&Open...", "&Save", "Save &As...",
        "Export as &PNG...", "Export as P&DF...", "E&xit",
    ]


def test_toolbars_share_the_menu_actions(window):
    toolbar_actions = set()
    for toolbar in window.findChildren(QToolBar):
        toolbar_actions.update(toolbar.actions())
    assert window._actions["run_batch"] in toolbar_actions
    assert window._actions["add_gun"] in toolbar_actions


def test_new_restores_the_default_apparatus(window):
    canvas = window._canvas
    canvas.add_counter()
    canvas.delete_wire(canvas._connections[0].wire_item)

    window._actions["new"].trigger()
    assert len(canvas._components) == 4
    assert len(canvas._connections) == 3
    assert window._current_file_path is None


def test_run_actions_fire_particles(window):
    canvas = window._canvas
    window._actions["run_single"].trigger()
    assert sum(c.get_count() for c in canvas._components if hasattr(c, "get_count")) == 1

    window._actions["run_batch"].trigger()
    assert sum(c.get_count() for c in canvas._components if hasattr(c, "get_count")) == 10_000

    window._actions["reset"].trigger()
    assert sum(c.get_count() for c in canvas._components if hasattr(c, "get_count")) == 0


def test_export_png(window, tmp_path):
    target = tmp_path / "apparatus.png"
    window._canvas.export_to_png(str(target))
    assert target.stat().st_size > 0


def test_export_pdf(window, tmp_path):
    target = tmp_path / "apparatus.pdf"
    window._canvas.export_to_pdf(str(target))
    assert target.read_bytes().startswith(b"%PDF")
