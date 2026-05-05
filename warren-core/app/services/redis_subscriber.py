# warren-core/app/services/redis_subscriber.py
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, Awaitable

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.db import OsintEvent
from app.services import (
    incident_classifier,
    probability_engine as prob_eng,
    scenario_templates as tmpl,
)
from app.services.llm_client import classify_direction

logger = logging.getLogger(__name__)


async def _handle_osint_alert(
    redis: Redis,
    db: AsyncSession,
    data: dict,
    notify_ws: Callable[[dict], Awaitable[None]],
) -> None:
    event_type = data.get("type", "unknown")
    region = data.get("region", "Unknown")
    severity = float(data.get("severity", 0.5))
    payload = data.get("payload", {})

    incident = await incident_classifier.classify(db, event_type, region, severity)
    if incident is None:
        logger.debug("Discarding event %s severity=%.2f region=%s", event_type, severity, region)
        return

    osint_event = OsintEvent(
        id=uuid.uuid4(),
        incident_id=incident.id,
        source=data.get("source", "shadowbroker"),
        event_type=event_type,
        severity=severity,
        payload=json.dumps(payload),
        received_at=datetime.now(timezone.utc),
    )
    db.add(osint_event)
    await db.flush()

    labels = tmpl.get_node_labels(incident.scenario_template)
    nodes = await prob_eng.get_or_create_nodes(db, incident, labels)

    direction_score = await classify_direction(event_type, region, str(payload))
    max_d = await prob_eng.apply_and_persist(db, nodes, direction_score, severity, osint_event.id)

    await db.commit()

    if max_d >= 0.01:
        update = {
            "incident_id": str(incident.id),
            "incident_title": incident.title,
            "nodes": [
                {
                    "id": str(n.id),
                    "label": n.label,
                    "probability": n.probability,
                    "direction": n.direction.value,
                }
                for n in nodes
            ],
            "triggered_by": {"event_type": event_type, "severity": severity},
        }
        payload_str = json.dumps(update)
        await redis.publish("scenario.updated", payload_str)
        await redis.set(f"incident:{incident.id}", payload_str)
        await redis.sadd("active_incidents", str(incident.id))
        await notify_ws(update)


async def _handle_council_briefing(db: AsyncSession, data: dict) -> None:
    logger.info(
        "Council briefing received incident=%s personas=%s",
        data.get("incident_id"),
        data.get("personas"),
    )


async def _handle_sim_result(db: AsyncSession, data: dict) -> None:
    logger.info(
        "Sim result incident=%s sentiment=%.2f",
        data.get("incident_id"),
        data.get("sentiment_score", 0.0),
    )


async def run(
    redis: Redis,
    session_factory: async_sessionmaker,
    notify_ws: Callable[[dict], Awaitable[None]],
) -> None:
    pubsub = redis.pubsub()
    await pubsub.subscribe("osint.alert", "council.briefing", "sim.result")
    logger.info("RedisSubscriber listening on osint.alert, council.briefing, sim.result")

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            channel = message["channel"]
            if isinstance(channel, bytes):
                channel = channel.decode()
            try:
                data = json.loads(message["data"])
                async with session_factory() as db:
                    if channel == "osint.alert":
                        await _handle_osint_alert(redis, db, data, notify_ws)
                    elif channel == "council.briefing":
                        await _handle_council_briefing(db, data)
                    elif channel == "sim.result":
                        await _handle_sim_result(db, data)
            except Exception:
                logger.exception("Error handling message on channel=%s", channel)
    except asyncio.CancelledError:
        await pubsub.unsubscribe()
        await pubsub.aclose()
        raise
