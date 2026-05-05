import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Enum, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class IncidentStatus(PyEnum):
    active = "active"
    archived = "archived"


class NodeDirection(PyEnum):
    left = "left"    # de-escalatory
    right = "right"  # escalatory


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    region = Column(String(100), nullable=False)
    status = Column(Enum(IncidentStatus), nullable=False, default=IncidentStatus.active)
    scenario_template = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    nodes = relationship("ScenarioNode", back_populates="incident", lazy="raise")


class ScenarioNode(Base):
    __tablename__ = "scenario_nodes"

    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    incident_id = Column(Uuid(), ForeignKey("incidents.id"), nullable=False)
    parent_id = Column(Uuid(), ForeignKey("scenario_nodes.id"), nullable=True)
    label = Column(Text, nullable=False)
    probability = Column(Float, nullable=False, default=0.25)
    direction = Column(Enum(NodeDirection), nullable=False)

    incident = relationship("Incident", back_populates="nodes", lazy="raise")


class ProbabilityHistory(Base):
    __tablename__ = "probability_history"

    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    node_id = Column(Uuid(), ForeignKey("scenario_nodes.id"), nullable=False)
    probability = Column(Float, nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    trigger_event_id = Column(Uuid(), ForeignKey("osint_events.id"), nullable=True)


class OsintEvent(Base):
    __tablename__ = "osint_events"

    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    incident_id = Column(Uuid(), ForeignKey("incidents.id"), nullable=True)
    source = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    severity = Column(Float, nullable=False)
    payload = Column(Text, nullable=True)  # JSON string (Text for SQLite compat in tests)
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
