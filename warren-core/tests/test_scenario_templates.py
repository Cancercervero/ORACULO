# warren-core/tests/test_scenario_templates.py
import pytest
from pathlib import Path
from app.services.scenario_templates import get_node_labels, list_templates


def test_military_conflict_returns_four_labels():
    labels = get_node_labels("military_conflict")
    assert len(labels) == 4
    assert "Escalacion militar" in labels


def test_economic_crisis_labels():
    labels = get_node_labels("economic_crisis")
    assert len(labels) == 4


def test_unknown_template_raises():
    with pytest.raises(ValueError, match="Unknown template"):
        get_node_labels("nonexistent")


def test_list_templates_contains_all_four():
    templates = list_templates()
    assert set(templates) == {"military_conflict", "economic_crisis", "diplomatic", "cyber_incident"}
