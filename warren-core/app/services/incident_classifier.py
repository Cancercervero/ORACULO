# warren-core/app/services/incident_classifier.py
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.db import Incident, IncidentStatus

REGION_EVENT_TEMPLATE_MAP: dict[str, str] = {
    "gps_jamming": "military_conflict",
    "carrier_movement": "military_conflict",
    "ukraine_alert": "military_conflict",
    "gdelt_spike": "military_conflict",
    "financial_spike": "economic_crisis",
    "market_crash": "economic_crisis",
    "diplomatic_incident": "diplomatic",
    "cyber_incident": "cyber_incident",
}

_DEFAULT_TEMPLATE = "military_conflict"


async def classify(
    db: AsyncSession,
    event_type: str,
    region: str,
    severity: float,
) -> Optional[Incident]:
    """
    Map an OSINT event to an active incident.
    - Returns existing incident in same region (within 24h window).
    - Creates new incident if severity >= 0.6 and no match.
    - Returns None (discard) if severity < 0.6 and no match.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    stmt = select(Incident).where(
        and_(
            Incident.region == region,
            Incident.status == IncidentStatus.active,
            Incident.created_at >= cutoff,
        )
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    if severity < 0.6:
        return None

    template = REGION_EVENT_TEMPLATE_MAP.get(event_type, _DEFAULT_TEMPLATE)
    incident = Incident(
        id=uuid.uuid4(),
        title=f"{region} {event_type.replace('_', ' ').title()} Incident",
        region=region,
        scenario_template=template,
        status=IncidentStatus.active,
        created_at=datetime.now(timezone.utc),
    )
    db.add(incident)
    await db.flush()
    return incident
