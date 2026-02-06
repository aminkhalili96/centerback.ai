"""Model registry and governance service."""

from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.entities import ModelVersion


class ModelRegistryService:
    """Tracks model versions and active deployment marker."""

    def list_versions(self, db: Session) -> list[dict[str, Any]]:
        rows = db.execute(select(ModelVersion).order_by(desc(ModelVersion.created_at))).scalars().all()
        return [self._serialize(row) for row in rows]

    def register_version(self, db: Session, version: str, path: str, accuracy: float | None) -> ModelVersion:
        model = ModelVersion(version=version, path=path, accuracy=accuracy, status="registered")
        db.add(model)
        db.flush()
        return model

    def promote_version(self, db: Session, version_id: str) -> ModelVersion | None:
        target = db.get(ModelVersion, version_id)
        if target is None:
            return None

        rows = db.execute(select(ModelVersion)).scalars().all()
        for row in rows:
            row.status = "archived"
        target.status = "active"
        db.flush()
        return target

    @staticmethod
    def _serialize(model: ModelVersion) -> dict[str, Any]:
        return {
            "id": model.id,
            "version": model.version,
            "path": model.path,
            "accuracy": model.accuracy,
            "status": model.status,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }


model_registry_service = ModelRegistryService()

