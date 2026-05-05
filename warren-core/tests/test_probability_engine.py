# warren-core/tests/test_probability_engine.py
import pytest
from app.services.probability_engine import compute_deltas, normalize


def make_nodes(probs: list[float], directions: list[str]) -> list[dict]:
    """Helper: create node dicts for testing without DB."""
    return [
        {"label": f"node_{i}", "probability": p, "direction": d}
        for i, (p, d) in enumerate(zip(probs, directions))
    ]


def test_normalize_sums_to_one():
    nodes = make_nodes([0.6, 0.6, 0.6, 0.6], ["right", "right", "left", "left"])
    normalized = normalize(nodes)
    assert abs(sum(n["probability"] for n in normalized) - 1.0) < 1e-9


def test_escalatory_event_increases_right_nodes():
    nodes = make_nodes([0.25, 0.25, 0.25, 0.25], ["right", "right", "left", "left"])
    result, max_d = compute_deltas(nodes, direction_score=1.0, severity=0.8, dampening=0.15)
    right_probs = [n["probability"] for n in result if n["direction"] == "right"]
    left_probs = [n["probability"] for n in result if n["direction"] == "left"]
    assert all(p > 0.25 for p in right_probs)
    assert all(p < 0.25 for p in left_probs)


def test_de_escalatory_event_decreases_right_nodes():
    nodes = make_nodes([0.25, 0.25, 0.25, 0.25], ["right", "right", "left", "left"])
    result, max_d = compute_deltas(nodes, direction_score=0.0, severity=0.8, dampening=0.15)
    right_probs = [n["probability"] for n in result if n["direction"] == "right"]
    left_probs = [n["probability"] for n in result if n["direction"] == "left"]
    assert all(p < 0.25 for p in right_probs)
    assert all(p > 0.25 for p in left_probs)


def test_result_always_sums_to_one():
    nodes = make_nodes([0.25, 0.25, 0.25, 0.25], ["right", "right", "left", "left"])
    result, _ = compute_deltas(nodes, direction_score=0.7, severity=0.9, dampening=0.15)
    assert abs(sum(n["probability"] for n in result) - 1.0) < 1e-9


def test_low_severity_produces_small_delta():
    nodes = make_nodes([0.25, 0.25, 0.25, 0.25], ["right", "right", "left", "left"])
    _, max_d = compute_deltas(nodes, direction_score=1.0, severity=0.01, dampening=0.15)
    assert max_d < 0.01  # below publish threshold
    assert max_d > 0.0   # confirms delta was actually computed


def test_neutral_event_minimal_net_change():
    nodes = make_nodes([0.25, 0.25, 0.25, 0.25], ["right", "right", "left", "left"])
    result, _ = compute_deltas(nodes, direction_score=0.5, severity=0.8, dampening=0.15)
    # Symmetric: right and left deltas cancel, probs should stay near 0.25
    for n in result:
        assert abs(n["probability"] - 0.25) < 0.05
