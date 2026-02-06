"""Statistics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.entities import Alert, ClassificationEvent, IngestionMessage, User, UserRole
from app.services.audit_service import audit_service
from app.services.stats_service import stats_service

router = APIRouter()


@router.get("/stats", dependencies=[Depends(require_roles(UserRole.viewer.value, UserRole.analyst.value, UserRole.admin.value))])
async def get_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    stats = stats_service.get_dashboard_stats(db)
    return {
        "success": True,
        "data": stats,
        "message": "Stats retrieved",
    }


@router.get("/stats/session", dependencies=[Depends(require_roles(UserRole.viewer.value, UserRole.analyst.value, UserRole.admin.value))])
async def get_session_stats(db: Session = Depends(get_db)):
    """Get aggregate statistics used by dashboard session view."""
    stats = stats_service.get_session_stats(db)
    return {
        "success": True,
        "data": stats,
        "message": "Session stats retrieved",
    }


@router.post("/stats/session/reset", dependencies=[Depends(require_roles(UserRole.admin.value))])
async def reset_session_stats(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """Reset detection data (admin-only)."""
    db.execute(delete(Alert))
    db.execute(delete(ClassificationEvent))
    db.execute(delete(IngestionMessage))
    audit_service.log(
        db=db,
        action="stats.reset",
        target_type="dataset",
        target_id=None,
        actor=current_user,
        details={"scope": "all_detection_data"},
    )
    db.commit()
    return {
        "success": True,
        "data": None,
        "message": "Session stats reset",
    }


@router.get("/stats/attacks", dependencies=[Depends(require_roles(UserRole.viewer.value, UserRole.analyst.value, UserRole.admin.value))])
async def get_attack_distribution(db: Session = Depends(get_db)):
    """Get attack type distribution."""
    distribution = stats_service.get_attack_distribution(db)
    return {
        "success": True,
        "data": distribution,
        "message": "Attack distribution retrieved",
    }


@router.get("/stats/distribution", dependencies=[Depends(require_roles(UserRole.viewer.value, UserRole.analyst.value, UserRole.admin.value))])
async def get_distribution(db: Session = Depends(get_db)):
    """Alias for attack distribution (deprecated)."""
    distribution = stats_service.get_attack_distribution(db)
    return {
        "success": True,
        "data": distribution,
        "message": "Attack distribution retrieved",
    }
