"""Classification endpoints."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import io

from app.services.classifier import ClassifierService

router = APIRouter()
classifier = ClassifierService()


class FlowFeatures(BaseModel):
    """Single network flow features for classification."""
    features: List[float]


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
    if len(flow.features) != 78:
        raise HTTPException(
            status_code=400,
            detail=f"Expected 78 features, got {len(flow.features)}"
        )
    
    result = classifier.predict_single(flow.features)
    
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
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        results = classifier.predict_batch(df)
        
        return {
            "success": True,
            "data": results,
            "message": f"Classified {results['total']} flows",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )


@router.post("/classify/sample", response_model=dict)
async def classify_sample():
    """
    Classify sample data from pre-loaded CICIDS2017 dataset.
    
    Useful for demo purposes.
    """
    results = classifier.predict_sample()
    
    return {
        "success": True,
        "data": results,
        "message": "Sample classification complete",
    }
