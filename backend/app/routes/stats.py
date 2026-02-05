"""Statistics endpoints."""

from fastapi import APIRouter
from app.services.stats_service import StatsService
from app.services.session_store import session_store

router = APIRouter()
stats_service = StatsService()


@router.get("/stats")
async def get_stats():
    """
    Get dashboard statistics.
    
    Returns total flows analyzed, threat counts, accuracy, etc.
    """
    stats = stats_service.get_dashboard_stats()
    
    return {
        "success": True,
        "data": stats,
        "message": "Stats retrieved",
    }


@router.get("/stats/session")
async def get_session_stats():
    """
    Get session-based statistics from user's analysis runs.
    
    Returns accumulated stats from classifications during this session.
    """
    stats = session_store.get_stats()
    
    # Include model accuracy from inference
    from ml.inference import inference
    if inference.is_loaded() and inference.accuracy is not None:
        stats["model_accuracy"] = round(float(inference.accuracy) * 100, 2)
    else:
        stats["model_accuracy"] = None
    
    return {
        "success": True,
        "data": stats,
        "message": "Session stats retrieved",
    }


@router.post("/stats/session/reset")
async def reset_session_stats():
    """
    Reset session statistics.
    """
    session_store.reset()
    
    return {
        "success": True,
        "data": None,
        "message": "Session stats reset",
    }


@router.get("/stats/attacks")
async def get_attack_distribution():
    """
    Get attack type distribution.
    
    Returns breakdown by attack category.
    """
    distribution = stats_service.get_attack_distribution()
    
    return {
        "success": True,
        "data": distribution,
        "message": "Attack distribution retrieved",
    }


@router.get("/stats/distribution")
async def get_distribution():
    """
    Alias for attack distribution (deprecated).
    """
    distribution = stats_service.get_attack_distribution()
    return {
        "success": True,
        "data": distribution,
        "message": "Attack distribution retrieved",
    }
