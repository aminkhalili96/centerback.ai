"""Audit logging service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entities import AuditLog, User


class AuditService:
    """Writes immutable audit trail entries."""

    def log(
        self,
        db: Session,
        action: str,
        target_type: str,
        target_id: str | None = None,
        actor: User | None = None,
        details: dict | None = None,
    ) -> None:
        db.add(
            AuditLog(
                actor_user_id=actor.id if actor else None,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details,
            )
        )


audit_service = AuditService()

