"""Tests for building, wiring and simulating apparatus on the real canvas."""

import json

import pytest

from pyspins.physics.network import LOST
from pyspins.physics.states import UNKNOWN_STATES, SpinState
from pyspins.ui.canvas import ExperimentCanvas
from pyspins.ui.components.analyzer import SternGerlachAnalyzer
from pyspins.ui.components.counter import ParticleCounter
from pyspins.ui.connections import WireItem
from pyspins.ui.dialogs import StatePickerDialog


@pytest.fixture
def canvas(qapp):
    return ExperimentCanvas()


@pytest.fixture
def empty_canvas(canvas):
    canvas.clear_scene()
    return canvas


def _wires(canvas):
    return [item for item in canvas.scene().items() if isinstance(item, WireItem)]


def _counters(canvas):
    return [c for c in canvas._components if isinstance(c, ParticleCounter)]


def test_default_scene_has_visible_wires(canvas):
    assert len(canvas._connections) == 3
    assert len(_wires(canvas)) == 3
    for connection in canvas._connections:
        assert connection in connection.source_port.connections
        assert connection in connection.dest_port.connections


def test_default_scene_ports_are_occupied(canvas):
    gun = canvas._components[0]
    sg = canvas._components[1]
    assert canvas.connect_ports(gun.output_ports[0], sg.input_ports[0]) is None
    assert len(canvas._connections) == 3


def test_default_scene_wire_can_be_deleted(canvas):
    upper = canvas._connections[1]
    canvas.delete_wire(upper.wire_item)
    assert len(canvas._connections) == 2
    assert len(_wires(canvas)) == 2
    assert not upper.source_port.connections
    probs = canvas.outcome_probabilities()
    assert probs == {LOST: pytest.approx(1.0)}


def test_default_scene_saves_connections(canvas):
    data = canvas.to_json()
    assert len(data["connections"]) == 3


def test_default_scene_batch(canvas):
    canvas.run_batch(1000)
    upper, lower = sorted(_counters(canvas), key=lambda c: c.y())
    assert upper.get_count() == 1000
    assert lower.get_count() == 0


def test_run_single_adds_one_particle(canvas):
    canvas.run_single()
    canvas.run_single()
    assert sum(c.get_count() for c in _counters(canvas)) == 2


def _build_recombination(canvas):
    """Gun(+z) → SGz(+) → SGx (both outputs into) → SGz → two counters."""
    gun = canvas.add_gun(0, 0)
    z1 = canvas.add_analyzer(0.5, 100, 0)
    x = canvas.add_analyzer(0.5, 200, 0, axis_label="+x")
    z2 = canvas.add_analyzer(0.5, 300, 0)
    up = canvas.add_counter(400, -50)
    down = canvas.add_counter(400, 50)
    pairs = [
        (gun.output_ports[0], z1.input_ports[0]),
        (z1.output_ports[0], x.input_ports[0]),
        (x.output_ports[0], z2.input_ports[0]),
        (x.output_ports[1], z2.input_ports[0]),
        (z2.output_ports[0], up.input_ports[0]),
        (z2.output_ports[1], down.input_ports[0]),
    ]
    for source, dest in pairs:
        assert canvas.connect_ports(source, dest) is not None
    return z2, up, down


def test_input_port_accepts_two_beams(empty_canvas):
    z2, _, _ = _build_recombination(empty_canvas)
    assert len(z2.input_ports[0].connections) == 2
    assert z2._coherent_checkbox is not None


def test_recombination_coherent_and_incoherent(empty_canvas):
    z2, up, down = _build_recombination(empty_canvas)

    z2.coherent_mode = True
    probs = empty_canvas.outcome_probabilities()
    assert probs[up] == pytest.approx(1.0)
    assert down not in probs

    z2.coherent_mode = False
    probs = empty_canvas.outcome_probabilities()
    assert probs[up] == pytest.approx(0.5)
    assert probs[down] == pytest.approx(0.5)


def test_checkbox_hidden_after_one_beam_removed(empty_canvas):
    z2, _, _ = _build_recombination(empty_canvas)
    empty_canvas.delete_wire(z2.input_ports[0].connections[0].wire_item)
    assert z2._coherent_checkbox is None


def test_output_port_accepts_one_wire(empty_canvas):
    gun = empty_canvas.add_gun(0, 0)
    a = empty_canvas.add_counter(100, 0)
    b = empty_canvas.add_counter(100, 100)
    assert empty_canvas.connect_ports(gun.output_ports[0], a.input_ports[0])
    assert empty_canvas.connect_ports(gun.output_ports[0], b.input_ports[0]) is None


def test_loop_is_rejected(empty_canvas):
    a = empty_canvas.add_analyzer(0.5, 0, 0)
    b = empty_canvas.add_analyzer(0.5, 100, 0)
    assert empty_canvas.connect_ports(a.output_ports[0], b.input_ports[0])
    assert empty_canvas.connect_ports(b.output_ports[0], a.input_ports[0]) is None
    assert empty_canvas.connect_ports(a.output_ports[1], a.input_ports[0]) is None


def test_delete_component_removes_its_wires(canvas):
    sg = next(c for c in canvas._components if isinstance(c, SternGerlachAnalyzer))
    canvas.delete_component(sg)
    assert canvas._connections == []
    assert _wires(canvas) == []


def test_json_round_trip_restores_recombination(empty_canvas, qapp):
    z2, _, _ = _build_recombination(empty_canvas)
    z2.coherent_mode = True
    data = json.loads(json.dumps(empty_canvas.to_json()))

    restored = ExperimentCanvas()
    restored.from_json(data)
    assert len(restored._connections) == 6
    assert len(_wires(restored)) == 6
    upper, lower = sorted(_counters(restored), key=lambda c: c.y())
    probs = restored.outcome_probabilities()
    assert probs[upper] == pytest.approx(1.0)
    assert _topology(restored.to_json()) == _topology(data)


def _topology(data):
    """Connections keyed by component position rather than the per-save ids."""
    index = {comp["id"]: i for i, comp in enumerate(data["components"])}
    return sorted(
        (index[c["source_id"]], c["output_index"], index[c["dest_id"]])
        for c in data["connections"]
    )


def test_from_json_rejects_invalid_connection(empty_canvas):
    data = {
        "version": 1,
        "components": [
            {"id": "g", "type": "gun", "x": 0, "y": 0, "spin_type": 0.5,
             "state_vector": [[1, 0], [0, 0]]},
            {"id": "c", "type": "counter", "x": 100, "y": 0},
        ],
        "connections": [
            {"source_id": "g", "output_index": 0, "dest_id": "c"},
            {"source_id": "g", "output_index": 0, "dest_id": "c"},
        ],
    }
    with pytest.raises(ValueError):
        empty_canvas.from_json(data)


def test_unknown_state_is_not_revealed_by_the_gun(canvas):
    gun = canvas._components[0]
    gun.set_initial_state(UNKNOWN_STATES["B"].copy(), "B")
    assert gun.label == "s=½\nB"
    assert "x" not in gun.label

    # ... and the gun still emits it
    assert gun.emit().vector == pytest.approx(SpinState.HALF_PLUS_X)


def test_unknown_state_is_not_revealed_by_the_save_file(canvas):
    gun = canvas._components[0]
    gun.set_initial_state(UNKNOWN_STATES["D"].copy(), "D")
    saved = json.dumps(canvas.to_json())
    assert '"unknown": "D"' in saved
    assert "state_vector" not in saved
    for amplitude in UNKNOWN_STATES["D"]:
        assert repr(amplitude.real) not in saved


def test_unknown_state_survives_round_trip(canvas):
    canvas._components[0].set_initial_state(UNKNOWN_STATES["C"].copy(), "C")
    data = json.loads(json.dumps(canvas.to_json()))

    restored = ExperimentCanvas()
    restored.from_json(data)
    gun = restored._components[0]
    assert gun.get_unknown_label() == "C"
    assert gun.emit().vector == pytest.approx(UNKNOWN_STATES["C"])


def test_known_state_is_still_labelled(canvas):
    gun = canvas._components[0]
    gun.set_initial_state(SpinState.HALF_MINUS_Y.copy())
    assert gun.label == "s=½\n|-y⟩"
    assert gun.get_unknown_label() is None


def test_picker_reports_unknown_letter(qapp):
    dialog = StatePickerDialog()
    dialog._state_combo.setCurrentText("A")
    spin_type, vector = dialog.get_state()
    assert dialog.get_unknown_label() == "A"
    assert vector == pytest.approx(UNKNOWN_STATES["A"])


def test_picker_preselects_current_state(qapp):
    assert StatePickerDialog(0.5, SpinState.HALF_MINUS_X.copy())._state_combo.currentText() == "-x"
    assert StatePickerDialog(1.0, SpinState.ONE_ZERO.copy())._state_combo.currentText() == "0"
    dialog = StatePickerDialog(0.5, UNKNOWN_STATES["B"].copy(), current_unknown="B")
    assert dialog._state_combo.currentText() == "B"


def test_counters_show_their_share(canvas):
    upper, lower = sorted(_counters(canvas), key=lambda c: c.y())
    canvas.run_batch(500)
    assert upper.get_share() == pytest.approx(1.0)
    assert lower.get_share() == pytest.approx(0.0)
    assert upper.label == "500\n100.0%"
    assert lower.label == "0"


def test_counter_shares_split_on_a_50_50_experiment(empty_canvas):
    gun = empty_canvas.add_gun(0, 0)
    sg = empty_canvas.add_analyzer(0.5, 100, 0, axis_label="+x")
    up = empty_canvas.add_counter(200, -50)
    down = empty_canvas.add_counter(200, 50)
    empty_canvas.connect_ports(gun.output_ports[0], sg.input_ports[0])
    empty_canvas.connect_ports(sg.output_ports[0], up.input_ports[0])
    empty_canvas.connect_ports(sg.output_ports[1], down.input_ports[0])

    empty_canvas.run_batch(10_000)
    assert up.get_share() + down.get_share() == pytest.approx(1.0)
    assert up.get_share() == pytest.approx(0.5, abs=0.05)
    assert "%" in up.label


def test_reset_clears_shares(canvas):
    canvas.run_batch(100)
    canvas.reset_counts()
    assert all(c.get_share() == 0.0 for c in _counters(canvas))
    assert canvas.particles_fired() == 0


def _highlighted(canvas):
    return {w for w in _wires(canvas) if w.is_highlighted()}


def test_single_shot_highlights_the_path_taken(canvas):
    gun, sg, upper, lower = canvas._components
    canvas.run_single()

    # |+z> on SGz always lands in the upper counter, never the lower one
    assert upper.get_count() == 1
    highlighted = _highlighted(canvas)
    assert len(highlighted) == 2
    lower_wire = lower.input_ports[0].connections[0].wire_item
    assert lower_wire not in highlighted


def test_batch_clears_highlighting(canvas):
    canvas.run_single()
    assert _highlighted(canvas)
    canvas.run_batch(100)
    assert not _highlighted(canvas)


def test_blocked_particle_highlights_nothing(empty_canvas):
    gun = empty_canvas.add_gun(0, 0)
    sg = empty_canvas.add_analyzer(0.5, 100, 0)
    empty_canvas.connect_ports(gun.output_ports[0], sg.input_ports[0])

    empty_canvas.run_single()
    assert not _highlighted(empty_canvas)


def test_recombination_highlights_every_contributing_wire(empty_canvas):
    z2, up, _ = _build_recombination(empty_canvas)
    z2.coherent_mode = True
    empty_canvas.run_single()

    assert up.get_count() == 1
    # gun→z1, z1→x, both x→z2 arms, z2→up; not z2→down
    assert len(_highlighted(empty_canvas)) == 5


def test_highlighted_wire_keeps_its_colour_when_cleared(canvas):
    wire = canvas._connections[1].wire_item
    normal = wire.pen().color().name()
    wire.set_highlighted(True)
    assert wire.pen().color().name() != normal
    wire.set_highlighted(False)
    assert wire.pen().color().name() == normal
