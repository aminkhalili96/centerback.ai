"""Model info and registry endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.entities import ModelEvaluationEvent, User, UserRole
from app.services.audit_service import audit_service
from app.services.canary_service import canary_service
from app.services.drift_service import drift_service
from app.services.model_registry_service import model_registry_service
from ml.inference import inference

router = APIRouter()


class RegisterModelRequest(BaseModel):
    version: str = Field(min_length=2, max_length=120)
    path: str = Field(min_length=3, max_length=512)
    accuracy: float | None = Field(default=None, ge=0.0, le=1.0)


class CanaryConfigRequest(BaseModel):
    model_path: str = Field(min_length=3, max_length=512)
    traffic_percent: int = Field(default=5, ge=1, le=100)


@router.get("/model/info", dependencies=[Depends(require_roles(UserRole.viewer.value, UserRole.analyst.value, UserRole.admin.value))])
async def get_model_info():
    """Return loaded model metadata."""
    info = inference.get_model_info()
    accuracy = info.get("accuracy")
    accuracy_pct = round(float(accuracy) * 100, 2) if isinstance(accuracy, (int, float)) else None
    return {
        "success": True,
        "data": {
            **info,
            "accuracy_pct": accuracy_pct,
        },
        "message": "Model info retrieved",
    }


@router.get("/model/versions", response_model=dict, dependencies=[Depends(require_roles(UserRole.analyst.value, UserRole.admin.value))])
async def list_model_versions(db: Session = Depends(get_db)):
    versions = model_registry_service.list_versions(db)
    return {
        "success": True,
        "data": versions,
        "message": "Model versions retrieved",
    }


@router.post("/model/versions", response_model=dict, dependencies=[Depends(require_roles(UserRole.admin.value))])
async def register_model_version(
    payload: RegisterModelRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    model = model_registry_service.register_version(
        db=db,
        version=payload.version,
        path=payload.path,
        accuracy=payload.accuracy,
    )
    audit_service.log(
        db=db,
        action="model.register",
        target_type="model_version",
        target_id=model.id,
        actor=current_user,
        details={"version": payload.version, "path": payload.path},
    )
    db.commit()
    return {
        "success": True,
        "data": {
            "id": model.id,
            "version": model.version,
            "path": model.path,
            "accuracy": model.accuracy,
            "status": model.status,
        },
        "message": "Model version registered",
    }


@router.post("/model/versions/{version_id}/promote", response_model=dict, dependencies=[Depends(require_roles(UserRole.admin.value))])
async def promote_model_version(
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    model = model_registry_service.promote_version(db, version_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Model version not found")

    resolved_model_path = Path(model.path)
    if not resolved_model_path.is_absolute():
        resolved_model_path = Path(__file__).resolve().parents[2] / model.path
    if not resolved_model_path.exists():
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Model artifact not found at {resolved_model_path}")
    if not inference.load_model(str(resolved_model_path)):
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to load promoted model artifact")

    audit_service.log(
        db=db,
        action="model.promote",
        target_type="model_version",
        target_id=version_id,
        actor=current_user,
        details={"version": model.version, "path": str(resolved_model_path)},
    )
    db.commit()

    return {
        "success": True,
        "data": {
            "id": model.id,
            "version": model.version,
            "status": model.status,
        },
        "message": "Model version promoted",
    }


@router.get("/model/canary/status", response_model=dict, dependencies=[Depends(require_roles(UserRole.analyst.value, UserRole.admin.value))])
async def get_canary_status():
    return {
        "success": True,
        "data": canary_service.status(),
        "message": "Canary status retrieved",
    }


@router.post("/model/canary/enable", response_model=dict, dependencies=[Depends(require_roles(UserRole.admin.value))])
async def enable_canary(
    payload: CanaryConfigRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    try:
        status = canary_service.enable(payload.model_path, payload.traffic_percent)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_service.log(
        db=db,
        action="model.canary.enable",
        target_type="model_rollout",
        actor=current_user,
        details={"model_path": payload.model_path, "traffic_percent": payload.traffic_percent},
    )
    db.commit()
    return {
        "success": True,
        "data": status,
        "message": "Canary rollout enabled",
    }


@router.post("/model/canary/disable", response_model=dict, dependencies=[Depends(require_roles(UserRole.admin.value))])
async def disable_canary(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    status = canary_service.disable()
    audit_service.log(
        db=db,
        action="model.canary.disable",
        target_type="model_rollout",
        actor=current_user,
        details={},
    )
    db.commit()
    return {
        "success": True,
        "data": status,
        "message": "Canary rollout disabled",
    }


@router.get("/model/drift", response_model=dict, dependencies=[Depends(require_roles(UserRole.analyst.value, UserRole.admin.value))])
async def get_model_drift(
    db: Session = Depends(get_db),
    window_events: int | None = None,
):
    report = drift_service.get_drift_report(db=db, window_events=window_events)
    return {
        "success": True,
        "data": report,
        "message": "Model drift report retrieved",
    }


@router.get("/model/evaluations", response_model=dict, dependencies=[Depends(require_roles(UserRole.analyst.value, UserRole.admin.value))])
async def get_model_evaluations(
    db: Session = Depends(get_db),
    limit: int = 500,
):
    total = db.scalar(select(func.count(ModelEvaluationEvent.id))) or 0
    diverged = db.scalar(
        select(func.count(ModelEvaluationEvent.id)).where(ModelEvaluationEvent.diverged.is_(True))
    ) or 0
    rows = db.execute(
        select(ModelEvaluationEvent)
        .order_by(ModelEvaluationEvent.created_at.desc())
        .limit(max(1, min(limit, 5000)))
    ).scalars().all()
    return {
        "success": True,
        "data": {
            "total": int(total),
            "diverged": int(diverged),
            "divergence_rate": round((diverged / total), 6) if total else 0.0,
            "recent": [
                {
                    "id": row.id,
                    "source": row.source,
                    "production_model_version": row.production_model_version,
                    "canary_model_version": row.canary_model_version,
                    "production_prediction": row.production_prediction,
                    "canary_prediction": row.canary_prediction,
                    "production_confidence": row.production_confidence,
                    "canary_confidence": row.canary_confidence,
                    "diverged": row.diverged,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows[:100]
            ],
        },
        "message": "Model evaluation metrics retrieved",
    }
