"""Dataset endpoints - explore and download sample data."""

from fastapi import APIRouter
from fastapi.responses import FileResponse
import pandas as pd
import os
from pathlib import Path

router = APIRouter()

# Path to sample data
SAMPLE_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "sample_data.csv"


@router.get("/dataset/info")
async def get_dataset_info():
    """
    Get dataset metadata and overview.
    """
    info = {
        "name": "CICIDS2017 Sample Dataset",
        "description": "Synthetic network traffic data based on the CICIDS2017 dataset format. Contains 78 network flow features for intrusion detection.",
        "source": "Canadian Institute for Cybersecurity",
        "rows": 50000,
        "features": 78,
        "attack_types": [
            {"name": "BENIGN", "description": "Normal network traffic"},
            {"name": "DDoS", "description": "Distributed Denial of Service attack"},
            {"name": "PortScan", "description": "Network reconnaissance scanning"},
            {"name": "DoS Hulk", "description": "HTTP flood attack"},
            {"name": "DoS GoldenEye", "description": "HTTP keep-alive attack"},
            {"name": "DoS Slowloris", "description": "Slow HTTP headers attack"},
            {"name": "DoS Slowhttptest", "description": "Slow HTTP body attack"},
            {"name": "Bot", "description": "Botnet command & control traffic"},
            {"name": "FTP-Patator", "description": "FTP brute force attack"},
            {"name": "SSH-Patator", "description": "SSH brute force attack"},
            {"name": "Web Attack - Brute Force", "description": "Web login brute force"},
            {"name": "Web Attack - XSS", "description": "Cross-site scripting attack"},
            {"name": "Web Attack - SQL Injection", "description": "SQL injection attack"},
            {"name": "Infiltration", "description": "Network infiltration attempt"},
            {"name": "Heartbleed", "description": "OpenSSL Heartbleed exploit"},
        ],
        "key_features": [
            "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
            "Flow Bytes/s", "Flow Packets/s", "Fwd Packet Length Mean",
            "Bwd Packet Length Mean", "SYN Flag Count", "ACK Flag Count"
        ],
    }
    
    # Check if sample data exists
    if SAMPLE_DATA_PATH.exists():
        df = pd.read_csv(SAMPLE_DATA_PATH, nrows=1)
        info["features"] = len(df.columns) - 1  # Exclude label column
        info["file_exists"] = True
    else:
        info["file_exists"] = False
    
    return {
        "success": True,
        "data": info,
        "message": "Dataset info retrieved",
    }


@router.get("/dataset/preview")
async def get_dataset_preview(rows: int = 20):
    """
    Get first N rows of dataset for preview table.
    """
    if not SAMPLE_DATA_PATH.exists():
        return {
            "success": False,
            "data": None,
            "error": "Sample data file not found. Run 'python ml/generate_sample.py' first.",
        }
    
    try:
        df = pd.read_csv(SAMPLE_DATA_PATH, nrows=min(rows, 100))
        
        # Select key columns for preview (not all 78)
        preview_columns = [
            "Label", "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
            "Flow Bytes/s", "Flow Packets/s", "Fwd Packet Length Mean"
        ]
        
        # Filter to available columns
        available_cols = [c for c in preview_columns if c in df.columns]
        if not available_cols:
            available_cols = df.columns[:7].tolist()
        
        preview_df = df[available_cols]
        
        return {
            "success": True,
            "data": {
                "columns": available_cols,
                "rows": preview_df.values.tolist(),
                "total_rows": 50000,
                "preview_rows": len(preview_df),
            },
            "message": "Dataset preview retrieved",
        }
    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
        }


@router.get("/dataset/download")
async def download_dataset():
    """
    Download the sample dataset CSV file.
    """
    if not SAMPLE_DATA_PATH.exists():
        return {
            "success": False,
            "error": "Sample data file not found.",
        }
    
    return FileResponse(
        path=SAMPLE_DATA_PATH,
        media_type="text/csv",
        filename="centerback_sample_data.csv",
    )
