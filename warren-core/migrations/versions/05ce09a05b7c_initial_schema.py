"""initial schema

Revision ID: 05ce09a05b7c
Revises:
Create Date: 2026-05-03 20:57:20.679643

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05ce09a05b7c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'incidents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('region', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('active', 'archived', name='incidentstatus'), nullable=False),
        sa.Column('scenario_template', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'osint_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('incident_id', sa.Uuid(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('severity', sa.Float(), nullable=False),
        sa.Column('payload', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'scenario_nodes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('incident_id', sa.Uuid(), nullable=False),
        sa.Column('parent_id', sa.Uuid(), nullable=True),
        sa.Column('label', sa.Text(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('direction', sa.Enum('left', 'right', name='nodedirection'), nullable=False),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['scenario_nodes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table(
        'probability_history',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('node_id', sa.Uuid(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trigger_event_id', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['node_id'], ['scenario_nodes.id'], ),
        sa.ForeignKeyConstraint(['trigger_event_id'], ['osint_events.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('probability_history')
    op.drop_table('scenario_nodes')
    op.drop_table('osint_events')
    op.drop_table('incidents')
