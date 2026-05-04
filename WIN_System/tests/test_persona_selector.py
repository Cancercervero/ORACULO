import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agents.persona_selector import select_personas


def test_baltic_military_returns_known_personas():
    personas = select_personas("Baltic", "military_conflict")
    assert len(personas) >= 2
    assert all(isinstance(p, str) for p in personas)


def test_taiwan_military_returns_xi():
    personas = select_personas("Taiwan", "military_conflict")
    assert any("xi" in p.lower() for p in personas)


def test_unknown_region_returns_default():
    personas = select_personas("Antarctica", "military_conflict")
    assert len(personas) >= 2


def test_economic_template_returns_financial_personas():
    personas = select_personas("Global", "economic_crisis")
    assert any("dalio" in p.lower() or "powell" in p.lower() for p in personas)
