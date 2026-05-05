# warren-core/app/services/probability_engine.py
import copy
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.db import ScenarioNode, ProbabilityHistory, NodeDirection, Incident
from app.config import get_settings


# ── Pure functions (testable without DB) ────────────────────────────────────

def normalize(nodes: list[dict]) -> list[dict]:
    """Re-normalize list of node dicts so probabilities sum to 1.0."""
    total = sum(max(0.0, n["probability"]) for n in nodes)
    if total == 0:
        equal = 1.0 / len(nodes)
        for n in nodes:
            n["probability"] = equal
    else:
        for n in nodes:
            n["probability"] = max(0.0, n["probability"]) / total
    return nodes


def compute_deltas(
    nodes: list[dict],
    direction_score: float,
    severity: float,
    dampening: float,
) -> tuple[list[dict], float]:
    """
    Apply event to node probability dicts.
    direction_score: 0.0=de-escalatory, 1.0=escalatory
    Returns (updated_nodes, max_absolute_delta).
    """
    nodes = copy.deepcopy(nodes)
    original_probs = [n["probability"] for n in nodes]   # capture BEFORE event_weight
    # Centre direction_score at 0.5: score=1.0 → full escalatory weight,
    # score=0.0 → full de-escalatory weight, score=0.5 → zero net change.
    event_weight = severity * (direction_score - 0.5) * 2.0 * dampening

    for node in nodes:
        if node["direction"] == "right":
            node["probability"] += event_weight
        else:
            node["probability"] -= event_weight

    nodes = normalize(nodes)

    max_d = max(
        abs(nodes[i]["probability"] - original_probs[i])
        for i in range(len(nodes))
    )
    return nodes, max_d


# ── DB operations ────────────────────────────────────────────────────────────

async def get_or_create_nodes(
    db: AsyncSession, incident: Incident, labels: list[str]
) -> list[ScenarioNode]:
    stmt = select(ScenarioNode).where(
        ScenarioNode.incident_id == incident.id,
        ScenarioNode.parent_id == None,
    )
    result = await db.execute(stmt)
    nodes = list(result.scalars().all())
    if nodes:
        return nodes

    initial_prob = 1.0 / len(labels)
    mid = len(labels) // 2
    new_nodes = []
    for i, label in enumerate(labels):
        direction = NodeDirection.right if i >= mid else NodeDirection.left
        node = ScenarioNode(
            id=uuid.uuid4(),
            incident_id=incident.id,
            parent_id=None,
            label=label,
            probability=initial_prob,
            direction=direction,
        )
        db.add(node)
        new_nodes.append(node)
    await db.flush()
    return new_nodes


async def apply_and_persist(
    db: AsyncSession,
    nodes: list[ScenarioNode],
    direction_score: float,
    severity: float,
    trigger_event_id: Optional[uuid.UUID],
) -> float:
    """Apply delta to DB nodes, persist history. Returns max_delta."""
    settings = get_settings()
    node_dicts = [
        {"id": n.id, "label": n.label, "probability": n.probability, "direction": n.direction.value}
        for n in nodes
    ]
    updated, max_d = compute_deltas(node_dicts, direction_score, severity, settings.prob_dampening)

    if max_d < 0.01:
        return max_d

    prob_map = {d["id"]: d["probability"] for d in updated}
    for node in nodes:
        node.probability = prob_map[node.id]
        db.add(ProbabilityHistory(
            id=uuid.uuid4(),
            node_id=node.id,
            probability=node.probability,
            recorded_at=datetime.now(timezone.utc),
            trigger_event_id=trigger_event_id,
        ))
    await db.flush()
    return max_d
