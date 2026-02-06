"""enterprise baseline schema

Revision ID: 0001_enterprise_baseline
Revises:
Create Date: 2026-02-06
"""

from __future__ import annotations

from alembic import op

from app.db import Base
from app.models import entities  # noqa: F401

revision = "0001_enterprise_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
