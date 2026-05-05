# warren-core/app/api/incidents.py
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

from app.models.db import Incident, ScenarioNode, ProbabilityHistory, IncidentStatus
from app.services import scenario_templates as tmpl
from app.dependencies import get_db, get_redis

router = APIRouter(prefix="/incidents", tags=["incidents"])


class CreateIncidentRequest(BaseModel):
    title: str
    region: str
    template: str = "military_conflict"


@router.get("")
async def list_incidents(db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)):
    stmt = select(Incident).where(Incident.status == IncidentStatus.active)
    result = await db.execute(stmt)
    incidents = result.scalars().all()
    out = []
    for inc in incidents:
        raw = await redis.get(f"incident:{inc.id}")
        if raw:
            out.append(json.loads(raw))
        else:
            out.append({"id": str(inc.id), "title": inc.title, "region": inc.region, "nodes": []})
    return out


@router.get("/{incident_id}")
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    raw = await redis.get(f"incident:{incident_id}")
    if raw:
        return json.loads(raw)
    try:
        inc_uuid = uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
    stmt = select(Incident).where(Incident.id == inc_uuid)
    result = await db.execute(stmt)
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    nodes_stmt = select(ScenarioNode).where(ScenarioNode.incident_id == inc.id)
    nodes_result = await db.execute(nodes_stmt)
    nodes = nodes_result.scalars().all()
    return {
        "id": str(inc.id),
        "title": inc.title,
        "region": inc.region,
        "template": inc.scenario_template,
        "nodes": [
            {"id": str(n.id), "label": n.label, "probability": n.probability, "direction": n.direction.value}
            for n in nodes
        ],
    }


@router.get("/{incident_id}/history")
async def get_incident_history(incident_id: str, db: AsyncSession = Depends(get_db)):
    try:
        inc_uuid = uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
    inc_stmt = select(Incident).where(Incident.id == inc_uuid)
    inc_result = await db.execute(inc_stmt)
    if not inc_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Incident not found")
    nodes_stmt = select(ScenarioNode).where(ScenarioNode.incident_id == inc_uuid)
    nodes_result = await db.execute(nodes_stmt)
    node_map = {str(n.id): n.label for n in nodes_result.scalars().all()}
    node_uuids = [uuid.UUID(nid) for nid in node_map.keys()]
    hist_stmt = (
        select(ProbabilityHistory)
        .where(ProbabilityHistory.node_id.in_(node_uuids))
        .order_by(ProbabilityHistory.recorded_at)
    )
    hist_result = await db.execute(hist_stmt)
    return [
        {
            "node_id": str(h.node_id),
            "node_label": node_map.get(str(h.node_id)),
            "probability": h.probability,
            "recorded_at": h.recorded_at.isoformat(),
            "trigger_event_id": str(h.trigger_event_id) if h.trigger_event_id else None,
        }
        for h in hist_result.scalars().all()
    ]


@router.post("", status_code=201)
async def create_incident(body: CreateIncidentRequest, db: AsyncSession = Depends(get_db)):
    if body.template not in tmpl.list_templates():
        raise HTTPException(status_code=400, detail=f"Unknown template: {body.template!r}")
    inc = Incident(
        id=uuid.uuid4(),
        title=body.title,
        region=body.region,
        scenario_template=body.template,
        status=IncidentStatus.active,
        created_at=datetime.now(timezone.utc),
    )
    db.add(inc)
    await db.commit()
    await db.refresh(inc)
    return {"id": str(inc.id), "title": inc.title, "region": inc.region}


@router.post("/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    try:
        inc_uuid = uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
    stmt = select(Incident).where(Incident.id == inc_uuid)
    result = await db.execute(stmt)
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc.status = IncidentStatus.archived
    inc.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    await redis.srem("active_incidents", incident_id)
    await redis.delete(f"incident:{incident_id}")
    return {"status": "archived", "id": incident_id}
