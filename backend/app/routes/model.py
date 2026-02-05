"""Model endpoints."""

from fastapi import APIRouter

from ml.inference import inference

router = APIRouter()


@router.get("/model/info")
async def get_model_info():
    """Return loaded model metadata (if available)."""
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

