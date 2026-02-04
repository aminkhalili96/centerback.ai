"""
CICIDS2017 Dataset Downloader
Downloads the dataset from Kaggle or UNB
"""

import os
import sys
import subprocess
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / 'data'


def download_from_kaggle():
    """Download dataset from Kaggle."""
    print("Downloading CICIDS2017 from Kaggle...")
    print("This requires kaggle CLI to be configured.")
    print()
    
    # Create data directory
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download from Kaggle
        subprocess.run([
            'kaggle', 'datasets', 'download', 
            '-d', 'cicdataset/cicids2017',
            '-p', str(DATA_DIR),
            '--unzip'
        ], check=True)
        
        print(f"\nDataset downloaded to: {DATA_DIR}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error downloading from Kaggle: {e}")
        return False
    except FileNotFoundError:
        print("Kaggle CLI not found. Please install with: pip install kaggle")
        print("Then configure with your API key from https://www.kaggle.com/account")
        return False


def manual_instructions():
    """Print manual download instructions."""
    print("=" * 60)
    print("MANUAL DOWNLOAD INSTRUCTIONS")
    print("=" * 60)
    print()
    print("Option 1: Kaggle (Recommended)")
    print("  1. Go to: https://www.kaggle.com/datasets/cicdataset/cicids2017")
    print("  2. Click 'Download' button")
    print("  3. Extract ZIP files to:")
    print(f"     {DATA_DIR}")
    print()
    print("Option 2: UNB Official")
    print("  1. Go to: http://205.174.165.80/CICDataset/CIC-IDS-2017/Dataset/")
    print("  2. Download 'MachineLearningCSV.zip'")
    print("  3. Extract to:")
    print(f"     {DATA_DIR}")
    print()
    print("Required CSV files:")
    print("  - Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
    print("  - Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv")
    print("  - Friday-WorkingHours-Morning.pcap_ISCX.csv")
    print("  - Monday-WorkingHours.pcap_ISCX.csv")
    print("  - Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv")
    print("  - Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv")
    print("  - Tuesday-WorkingHours.pcap_ISCX.csv")
    print("  - Wednesday-workingHours.pcap_ISCX.csv")
    print()
    print("After downloading, run: python ml/train.py")
    print("=" * 60)


def check_data_exists():
    """Check if dataset already exists."""
    if not DATA_DIR.exists():
        return False
    
    csv_files = list(DATA_DIR.glob('*.csv'))
    return len(csv_files) >= 1


def main():
    print("CICIDS2017 Dataset Downloader")
    print()
    
    if check_data_exists():
        csv_files = list(DATA_DIR.glob('*.csv'))
        print(f"Dataset already exists with {len(csv_files)} CSV files in:")
        print(f"  {DATA_DIR}")
        print()
        response = input("Re-download? (y/N): ").strip().lower()
        if response != 'y':
            print("Using existing data.")
            return
    
    print("Download options:")
    print("  1. Kaggle CLI (requires setup)")
    print("  2. Manual download instructions")
    print()
    
    choice = input("Select option (1/2): ").strip()
    
    if choice == '1':
        success = download_from_kaggle()
        if not success:
            manual_instructions()
    else:
        manual_instructions()


if __name__ == '__main__':
    main()
