"""Classification endpoints."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List
import logging
import pandas as pd
import io

from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.entities import User, UserRole
from app.services.audit_service import audit_service
from app.services.classifier import ClassifierService
from app.services.detection_service import detection_service

router = APIRouter()
classifier = ClassifierService()
logger = logging.getLogger(__name__)

MAX_CSV_BYTES = 25 * 1024 * 1024  # 25MB


class FlowFeatures(BaseModel):
    """Single network flow features for classification."""
    features: List[float] = Field(min_length=78, max_length=78)
    source_ip: str = "unknown"
    destination_ip: str = "unknown"


class ClassificationResult(BaseModel):
    """Classification result for a single flow."""
    prediction: str
    confidence: float
    is_threat: bool


class BatchClassificationResult(BaseModel):
    """Batch classification results."""
    total: int
    benign: int
    threats: int
    results: List[ClassificationResult]


@router.post("/classify", response_model=dict, dependencies=[Depends(require_roles(UserRole.analyst.value, UserRole.admin.value))])
async def classify_single(
    flow: FlowFeatures,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    Classify a single network flow.
    
    Expects 78 features as input.
    Returns prediction with confidence score.
    """
    try:
        result = classifier.predict_single(flow.features)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    event, alert = detection_service.record_classification(
        db=db,
        prediction=result["prediction"],
        confidence=float(result["confidence"]),
        is_threat=bool(result["is_threat"]),
        source="api.classify_single",
        source_ip=flow.source_ip,
        destination_ip=flow.destination_ip,
        features=flow.features,
        model_version=result.get("model_version"),
    )

    audit_service.log(
        db=db,
        action="classify.single",
        target_type="classification_event",
        target_id=event.id,
        actor=current_user,
        details={
            "is_threat": event.is_threat,
            "prediction": event.prediction,
            "alert_id": alert.id if alert else None,
        },
    )
    db.commit()
    
    return {
        "success": True,
        "data": {
            **result,
            "event_id": event.id,
            "alert_id": alert.id if alert else None,
        },
        "message": "Classification complete",
    }


@router.post("/classify/batch", response_model=dict, dependencies=[Depends(require_roles(UserRole.analyst.value, UserRole.admin.value))])
async def classify_batch(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    Classify multiple network flows from CSV file.
    
    CSV should contain 78 feature columns.
    Returns classification for each flow.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )
    
    try:
        contents = await file.read(MAX_CSV_BYTES + 1)
        if len(contents) > MAX_CSV_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"CSV file too large (max {MAX_CSV_BYTES // (1024 * 1024)}MB)",
            )

        df = pd.read_csv(io.BytesIO(contents))
        df.columns = df.columns.astype(str).str.strip()
        
        try:
            summary, all_results = classifier.predict_batch(df)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        stored_events = 0
        for row in all_results:
            detection_service.record_classification(
                db=db,
                prediction=str(row["prediction"]),
                confidence=float(row["confidence"]),
                is_threat=bool(row["is_threat"]),
                source="api.classify_batch",
                source_ip="unknown",
                destination_ip="unknown",
                features=None,
                model_version=row.get("model_version"),
                extra_metadata={"file_name": file.filename},
            )
            stored_events += 1

        audit_service.log(
            db=db,
            action="classify.batch",
            target_type="classification_batch",
            target_id=None,
            actor=current_user,
            details={"file_name": file.filename, "rows": stored_events},
        )
        db.commit()
        
        return {
            "success": True,
            "data": summary,
            "message": f"Classified {summary['total']} flows",
        }
    except HTTPException:
        raise
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="Invalid CSV format")
    except Exception as exc:
        logger.exception("Error processing CSV file", exc_info=exc)
        raise HTTPException(
            status_code=500,
            detail="Error processing file"
        ) from exc


@router.post("/classify/sample", response_model=dict)
async def classify_sample(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    """
    Classify sample data from pre-loaded CICIDS2017 dataset.
    
    Useful for demo purposes.
    """
    try:
        results = classifier.predict_sample()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    for row in results.get("results", []):
        detection_service.record_classification(
            db=db,
            prediction=str(row["prediction"]),
            confidence=float(row["confidence"]),
            is_threat=bool(row["is_threat"]),
            source="api.classify_sample",
            source_ip="sample",
            destination_ip="sample",
            features=None,
            model_version=row.get("model_version"),
        )

    audit_service.log(
        db=db,
        action="classify.sample",
        target_type="classification_batch",
        target_id=None,
        actor=current_user,
        details={"rows": results.get("total", 0)},
    )
    db.commit()
    
    return {
        "success": True,
        "data": results,
        "message": "Sample classification complete",
    }
