"""Classification endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import List
import pandas as pd
import io

from app.services.classifier import ClassifierService
from app.services.session_store import session_store

router = APIRouter()
classifier = ClassifierService()

MAX_CSV_BYTES = 25 * 1024 * 1024  # 25MB


class FlowFeatures(BaseModel):
    """Single network flow features for classification."""
    features: List[float] = Field(min_length=78, max_length=78)


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


@router.post("/classify", response_model=dict)
async def classify_single(flow: FlowFeatures):
    """
    Classify a single network flow.
    
    Expects 78 features as input.
    Returns prediction with confidence score.
    """
    result = classifier.predict_single(flow.features)
    
    # Track in session
    session_store.add_classification(
        prediction=result["prediction"],
        is_threat=result["is_threat"],
        confidence=result["confidence"],
    )
    
    return {
        "success": True,
        "data": result,
        "message": "Classification complete",
    }


@router.post("/classify/batch", response_model=dict)
async def classify_batch(file: UploadFile = File(...)):
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
        
        results = classifier.predict_batch(df)
        
        # Track in session
        session_store.add_batch_classification(results.get("results", []))
        
        return {
            "success": True,
            "data": results,
            "message": f"Classified {results['total']} flows",
        }
    except HTTPException:
        raise
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="CSV file is empty")
    except pd.errors.ParserError:
        raise HTTPException(status_code=400, detail="Invalid CSV format")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Error processing file"
        )


@router.post("/classify/sample", response_model=dict)
async def classify_sample():
    """
    Classify sample data from pre-loaded CICIDS2017 dataset.
    
    Useful for demo purposes.
    """
    results = classifier.predict_sample()
    
    # Track in session
    session_store.add_batch_classification(results.get("results", []))
    
    return {
        "success": True,
        "data": results,
        "message": "Sample classification complete",
    }
