# warren-core/tests/test_incident_classifier.py
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.services.incident_classifier import classify, REGION_EVENT_TEMPLATE_MAP
from app.models.db import Incident, IncidentStatus


def make_mock_incident(region="Baltic"):
    inc = MagicMock(spec=Incident)
    inc.id = uuid.uuid4()
    inc.region = region
    inc.status = IncidentStatus.active
    inc.created_at = datetime.now(timezone.utc)
    return inc


@pytest.mark.asyncio
async def test_assigns_existing_incident_same_region():
    existing = make_mock_incident("Baltic")
    db = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = existing
    db.execute.return_value = execute_result

    result = await classify(db, "gps_jamming", "Baltic", severity=0.85)
    assert result is existing


@pytest.mark.asyncio
async def test_creates_new_incident_for_high_severity_no_existing():
    db = AsyncMock()
    db.add = MagicMock()  # session.add() is sync; override AsyncMock default
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute.return_value = execute_result

    result = await classify(db, "gps_jamming", "Baltic", severity=0.85)
    assert result is not None
    assert result.region == "Baltic"
    assert result.scenario_template == "military_conflict"
    db.add.assert_called_once()
    db.flush.assert_called_once()


@pytest.mark.asyncio
async def test_discards_low_severity_with_no_existing_incident():
    db = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute.return_value = execute_result

    result = await classify(db, "gps_jamming", "Baltic", severity=0.3)
    assert result is None
    db.add.assert_not_called()


def test_event_type_template_mapping():
    assert REGION_EVENT_TEMPLATE_MAP["gps_jamming"] == "military_conflict"
    assert REGION_EVENT_TEMPLATE_MAP["market_crash"] == "economic_crisis"
    assert REGION_EVENT_TEMPLATE_MAP["cyber_incident"] == "cyber_incident"
    assert REGION_EVENT_TEMPLATE_MAP["diplomatic_incident"] == "diplomatic"
