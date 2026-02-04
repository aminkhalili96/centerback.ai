"""
CenterBack.AI - ML Training Pipeline
Downloads CICIDS2017 dataset and trains Random Forest classifier
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import warnings

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = BASE_DIR / 'ml' / 'models'

# CICIDS2017 CSV files (local paths after download)
DATASET_FILES = [
    'Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv',
    'Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv',
    'Friday-WorkingHours-Morning.pcap_ISCX.csv',
    'Monday-WorkingHours.pcap_ISCX.csv',
    'Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv',
    'Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv',
    'Tuesday-WorkingHours.pcap_ISCX.csv',
    'Wednesday-workingHours.pcap_ISCX.csv',
]

# Features to use (78 features from CICIDS2017)
FEATURE_COLUMNS = None  # Will be set after loading data


def load_data(sample_size: int = None) -> pd.DataFrame:
    """
    Load and combine all CICIDS2017 CSV files or sample data.
    
    Args:
        sample_size: Optional number of rows to sample per file
        
    Returns:
        Combined DataFrame
    """
    logger.info("Loading dataset...")
    
    all_data = []
    
    # First check for sample data
    sample_file = DATA_DIR / 'sample_data.csv'
    if sample_file.exists():
        logger.info(f"Loading sample data from {sample_file}...")
        df = pd.read_csv(sample_file)
        logger.info(f"Loaded {len(df)} rows from sample data")
        return df
    
    # Otherwise load CICIDS2017 files
    for filename in DATASET_FILES:
        filepath = DATA_DIR / filename
        if filepath.exists():
            logger.info(f"Loading {filename}...")
            try:
                df = pd.read_csv(filepath, low_memory=False)
                if sample_size:
                    df = df.sample(min(sample_size, len(df)), random_state=42)
                all_data.append(df)
                logger.info(f"  Loaded {len(df)} rows")
            except Exception as e:
                logger.error(f"  Error loading {filename}: {e}")
        else:
            logger.warning(f"  File not found: {filepath}")
    
    if not all_data:
        logger.error("No data files found!")
        logger.info("Options:")
        logger.info("  1. Run: python ml/generate_sample.py (quick demo)")
        logger.info("  2. Download CICIDS2017 from Kaggle")
        logger.info(f"  3. Place CSV files in: {DATA_DIR}")
        sys.exit(1)
    
    combined = pd.concat(all_data, ignore_index=True)
    logger.info(f"Total rows loaded: {len(combined)}")
    
    return combined


def preprocess_data(df: pd.DataFrame) -> tuple:
    """
    Preprocess the dataset for training.
    
    Returns:
        X (features), y (labels), feature_names, label_encoder
    """
    logger.info("Preprocessing data...")
    
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # Get label column
    label_col = 'Label'
    if label_col not in df.columns:
        # Try alternate name
        label_col = ' Label'
        if label_col not in df.columns:
            logger.error("Could not find Label column")
            sys.exit(1)
    
    # Separate features and labels
    y_raw = df[label_col].str.strip()
    X = df.drop(columns=[label_col])
    
    # Remove non-numeric columns
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    X = X[numeric_cols]
    
    logger.info(f"Feature columns: {len(X.columns)}")
    
    # Handle infinite values
    X = X.replace([np.inf, -np.inf], np.nan)
    
    # Fill NaN with median
    X = X.fillna(X.median())
    
    # Remove any remaining problematic rows
    mask = ~X.isna().any(axis=1)
    X = X[mask]
    y_raw = y_raw[mask]
    
    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_raw)
    
    logger.info(f"Classes: {list(label_encoder.classes_)}")
    logger.info(f"Class distribution:")
    for cls in label_encoder.classes_:
        count = (y_raw == cls).sum()
        logger.info(f"  {cls}: {count}")
    
    return X, y, X.columns.tolist(), label_encoder


def train_model(X: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
    """
    Train Random Forest classifier.
    
    Returns:
        Trained model
    """
    logger.info("Training Random Forest classifier...")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"Training samples: {len(X_train)}")
    logger.info(f"Test samples: {len(X_test)}")
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
        verbose=1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    logger.info("Evaluating model...")
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"\nAccuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    return model, X_test, y_test, y_pred


def save_model(model, label_encoder, feature_names, accuracy):
    """Save trained model and metadata."""
    logger.info("Saving model...")
    
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = MODEL_DIR / 'random_forest_v1.joblib'
    joblib.dump({
        'model': model,
        'label_encoder': label_encoder,
        'feature_names': feature_names,
        'accuracy': accuracy,
    }, model_path)
    
    logger.info(f"Model saved to: {model_path}")
    
    return model_path


def main():
    """Main training pipeline."""
    logger.info("=" * 60)
    logger.info("CenterBack.AI - ML Training Pipeline")
    logger.info("=" * 60)
    
    # Check if data exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    df = load_data()
    
    # Preprocess
    X, y, feature_names, label_encoder = preprocess_data(df)
    
    # Train
    model, X_test, y_test, y_pred = train_model(X.values, y)
    
    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    
    # Print classification report
    logger.info("\nClassification Report:")
    print(classification_report(
        y_test, y_pred,
        target_names=label_encoder.classes_
    ))
    
    # Save model
    model_path = save_model(model, label_encoder, feature_names, accuracy)
    
    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info(f"Model accuracy: {accuracy*100:.2f}%")
    logger.info(f"Model saved to: {model_path}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
