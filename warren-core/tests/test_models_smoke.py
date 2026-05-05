import pytest

from app.models.db import Incident, ScenarioNode, ProbabilityHistory, OsintEvent, IncidentStatus, NodeDirection


def test_incident_status_values():
    assert IncidentStatus.active.value == "active"
    assert IncidentStatus.archived.value == "archived"


def test_node_direction_values():
    assert NodeDirection.left.value == "left"
    assert NodeDirection.right.value == "right"


@pytest.mark.asyncio
async def test_tables_create(db):
    from sqlalchemy import text
    result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    tables = {row[0] for row in result.fetchall()}
    assert "incidents" in tables
    assert "scenario_nodes" in tables
    assert "probability_history" in tables
    assert "osint_events" in tables
