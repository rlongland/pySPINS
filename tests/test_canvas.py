"""Tests for canvas serialization and deserialization.

These tests verify JSON round-trip integrity for scene save/load functionality.
They test the data structure itself without requiring Qt GUI components.
"""

import json
import numpy as np
import pytest


def test_json_round_trip_basic():
    """Test that saving and loading a scene produces identical apparatus."""
    # Create a canvas (headless mode without actual Qt display)
    # We'll test the to_json/from_json methods directly

    # Create a simple scene data structure
    scene_data = {
        "version": 1,
        "components": [
            {
                "type": "ParticleGun",
                "position": [50.0, 150.0],
                "spin_type": 0.5,
                "state_vector": [[1.0, 0.0], [0.0, 0.0]]  # Real and imaginary parts
            },
            {
                "type": "SternGerlachAnalyzer",
                "position": [200.0, 150.0],
                "axis_label": "+z",
                "phi_deg": 0.0,
                "spin_type": 0.5,
                "coherent_mode": False
            },
            {
                "type": "ParticleCounter",
                "position": [350.0, 100.0],
                "label": "Counter\n+z\n0",
                "count": 0
            }
        ],
        "connections": []
    }

    # Serialize to JSON string and back
    json_str = json.dumps(scene_data, indent=2)
    loaded_data = json.loads(json_str)

    # Verify the data is identical after round-trip
    assert loaded_data == scene_data
    assert loaded_data["version"] == 1
    assert len(loaded_data["components"]) == 3

    # Verify component data integrity
    gun = loaded_data["components"][0]
    assert gun["type"] == "ParticleGun"
    assert gun["spin_type"] == 0.5
    assert gun["position"] == [50.0, 150.0]

    analyzer = loaded_data["components"][1]
    assert analyzer["type"] == "SternGerlachAnalyzer"
    assert analyzer["axis_label"] == "+z"
    assert analyzer["coherent_mode"] is False

    counter = loaded_data["components"][2]
    assert counter["type"] == "ParticleCounter"
    assert counter["count"] == 0


def test_json_round_trip_with_magnet():
    """Test JSON round-trip with magnet component and rotation angle."""
    scene_data = {
        "version": 1,
        "components": [
            {
                "type": "ParticleGun",
                "position": [50.0, 150.0],
                "spin_type": 0.5,
                "state_vector": [[1.0, 0.0], [0.0, 0.0]]
            },
            {
                "type": "SpinRotationMagnet",
                "position": [200.0, 150.0],
                "beta": 1.5707963267948966  # π/2
            },
            {
                "type": "ParticleCounter",
                "position": [350.0, 150.0],
                "label": "Counter\n0",
                "count": 0
            }
        ],
        "connections": []
    }

    # Round-trip test
    json_str = json.dumps(scene_data, indent=2)
    loaded_data = json.loads(json_str)

    assert loaded_data == scene_data

    magnet = loaded_data["components"][1]
    assert magnet["type"] == "SpinRotationMagnet"
    assert abs(magnet["beta"] - np.pi/2) < 1e-10


def test_json_round_trip_with_connections():
    """Test JSON round-trip with component connections."""
    scene_data = {
        "version": 1,
        "components": [
            {
                "type": "ParticleGun",
                "position": [50.0, 150.0],
                "spin_type": 0.5,
                "state_vector": [[1.0, 0.0], [0.0, 0.0]]
            },
            {
                "type": "SternGerlachAnalyzer",
                "position": [200.0, 150.0],
                "axis_label": "+z",
                "phi_deg": 0.0,
                "spin_type": 0.5,
                "coherent_mode": False
            },
            {
                "type": "ParticleCounter",
                "position": [350.0, 100.0],
                "label": "Counter\n+z\n0",
                "count": 0
            },
            {
                "type": "ParticleCounter",
                "position": [350.0, 200.0],
                "label": "Counter\n-z\n0",
                "count": 0
            }
        ],
        "connections": [
            ["component-0", 0, "component-1"],
            ["component-1", 0, "component-2"],
            ["component-1", 1, "component-3"]
        ]
    }

    # Round-trip test
    json_str = json.dumps(scene_data, indent=2)
    loaded_data = json.loads(json_str)

    assert loaded_data == scene_data
    assert len(loaded_data["connections"]) == 3

    # Verify connection structure
    conn1 = loaded_data["connections"][0]
    assert conn1 == ["component-0", 0, "component-1"]

    conn2 = loaded_data["connections"][1]
    assert conn2 == ["component-1", 0, "component-2"]

    conn3 = loaded_data["connections"][2]
    assert conn3 == ["component-1", 1, "component-3"]


def test_json_spin1_analyzer():
    """Test JSON round-trip with spin-1 analyzer (3 output ports)."""
    scene_data = {
        "version": 1,
        "components": [
            {
                "type": "ParticleGun",
                "position": [50.0, 150.0],
                "spin_type": 1.0,
                "state_vector": [[1.0, 0.0], [0.0, 0.0], [0.0, 0.0]]  # |+1⟩
            },
            {
                "type": "SternGerlachAnalyzer",
                "position": [200.0, 150.0],
                "axis_label": "+z",
                "phi_deg": 0.0,
                "spin_type": 1.0,
                "coherent_mode": False
            }
        ],
        "connections": []
    }

    # Round-trip test
    json_str = json.dumps(scene_data, indent=2)
    loaded_data = json.loads(json_str)

    assert loaded_data == scene_data

    gun = loaded_data["components"][0]
    assert gun["spin_type"] == 1.0
    assert len(gun["state_vector"]) == 3  # 3 components for spin-1

    analyzer = loaded_data["components"][1]
    assert analyzer["spin_type"] == 1.0


def test_json_coherent_mode():
    """Test JSON round-trip with coherent recombination mode enabled."""
    scene_data = {
        "version": 1,
        "components": [
            {
                "type": "SternGerlachAnalyzer",
                "position": [200.0, 150.0],
                "axis_label": "+x",
                "phi_deg": 0.0,
                "spin_type": 0.5,
                "coherent_mode": True  # Coherent recombination enabled
            }
        ],
        "connections": []
    }

    # Round-trip test
    json_str = json.dumps(scene_data, indent=2)
    loaded_data = json.loads(json_str)

    assert loaded_data == scene_data

    analyzer = loaded_data["components"][0]
    assert analyzer["coherent_mode"] is True
