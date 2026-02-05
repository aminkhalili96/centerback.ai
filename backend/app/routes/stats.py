"""Statistics endpoints."""

from fastapi import APIRouter
from app.services.stats_service import StatsService

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
    Alias for attack distribution (frontend compatibility).
    """
    distribution = stats_service.get_attack_distribution()
    return distribution  # Return array directly for frontend
