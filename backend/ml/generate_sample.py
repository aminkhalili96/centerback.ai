"""
Generate sample training data for quick demo.
This creates a small synthetic dataset mimicking CICIDS2017 structure.
For production, download the full CICIDS2017 dataset.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Attack types from CICIDS2017
ATTACK_LABELS = [
    "BENIGN",
    "Bot",
    "DDoS",
    "DoS GoldenEye",
    "DoS Hulk",
    "DoS Slowhttptest",
    "DoS Slowloris",
    "FTP-Patator",
    "Heartbleed",
    "Infiltration",
    "PortScan",
    "SSH-Patator",
    "Web Attack - Brute Force",
    "Web Attack - SQL Injection",
    "Web Attack - XSS",
]

# Subset of CICIDS2017 feature names
FEATURE_NAMES = [
    'Destination Port', 'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
    'Total Length of Fwd Packets', 'Total Length of Bwd Packets', 'Fwd Packet Length Max',
    'Fwd Packet Length Min', 'Fwd Packet Length Mean', 'Fwd Packet Length Std',
    'Bwd Packet Length Max', 'Bwd Packet Length Min', 'Bwd Packet Length Mean',
    'Bwd Packet Length Std', 'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean',
    'Flow IAT Std', 'Flow IAT Max', 'Flow IAT Min', 'Fwd IAT Total', 'Fwd IAT Mean',
    'Fwd IAT Std', 'Fwd IAT Max', 'Fwd IAT Min', 'Bwd IAT Total', 'Bwd IAT Mean',
    'Bwd IAT Std', 'Bwd IAT Max', 'Bwd IAT Min', 'Fwd PSH Flags', 'Bwd PSH Flags',
    'Fwd URG Flags', 'Bwd URG Flags', 'Fwd Header Length', 'Bwd Header Length',
    'Fwd Packets/s', 'Bwd Packets/s', 'Min Packet Length', 'Max Packet Length',
    'Packet Length Mean', 'Packet Length Std', 'Packet Length Variance', 'FIN Flag Count',
    'SYN Flag Count', 'RST Flag Count', 'PSH Flag Count', 'ACK Flag Count', 'URG Flag Count',
    'CWE Flag Count', 'ECE Flag Count', 'Down/Up Ratio', 'Average Packet Size',
    'Avg Fwd Segment Size', 'Avg Bwd Segment Size', 'Fwd Header Length.1',
    'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk', 'Fwd Avg Bulk Rate',
    'Bwd Avg Bytes/Bulk', 'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate',
    'Subflow Fwd Packets', 'Subflow Fwd Bytes', 'Subflow Bwd Packets', 'Subflow Bwd Bytes',
    'Init_Win_bytes_forward', 'Init_Win_bytes_backward', 'act_data_pkt_fwd',
    'min_seg_size_forward', 'Active Mean', 'Active Std', 'Active Max', 'Active Min',
    'Idle Mean', 'Idle Std', 'Idle Max', 'Idle Min',
]


def generate_attack_profile(attack_type: str, n_samples: int) -> np.ndarray:
    """Generate feature profiles for different attack types."""
    np.random.seed(hash(attack_type) % 2**32)
    
    base_features = np.random.randn(n_samples, len(FEATURE_NAMES))
    
    # Add attack-specific characteristics
    if attack_type == "BENIGN":
        base_features[:, 0] = np.random.choice([80, 443, 8080, 22], n_samples)  # Common ports
        base_features[:, 1] *= 1000  # Normal duration
        base_features[:, 2:4] = np.abs(base_features[:, 2:4]) * 10  # Moderate packets
    elif "DDoS" in attack_type or "DoS" in attack_type:
        base_features[:, 0] = np.random.choice([80, 443], n_samples)
        base_features[:, 1] *= 100  # Short bursts
        base_features[:, 2:4] = np.abs(base_features[:, 2:4]) * 1000  # Many packets
        base_features[:, 14:16] *= 100  # High bytes/packets per second
    elif "PortScan" in attack_type:
        base_features[:, 0] = np.random.randint(1, 65535, n_samples)  # Random ports
        base_features[:, 1] *= 10  # Very short
        base_features[:, 2] = np.abs(base_features[:, 2]) * 5  # Few fwd packets
    elif "Brute Force" in attack_type or "Patator" in attack_type:
        base_features[:, 0] = np.random.choice([22, 21], n_samples)  # SSH/FTP
        base_features[:, 2:4] = np.abs(base_features[:, 2:4]) * 50
    elif "SQL Injection" in attack_type or "XSS" in attack_type:
        base_features[:, 0] = np.random.choice([80, 443, 8080], n_samples)
        base_features[:, 4:6] *= 10  # Larger payloads
    elif "Bot" in attack_type:
        base_features[:, 14:16] *= 50  # Moderate traffic rate
    
    return np.abs(base_features)  # Ensure positive values


def generate_sample_data(total_samples: int = 50000) -> pd.DataFrame:
    """Generate synthetic CICIDS2017-like dataset."""
    print(f"Generating {total_samples} synthetic samples...")
    
    # Distribution: 70% benign, 30% attacks
    benign_samples = int(total_samples * 0.7)
    attack_samples = total_samples - benign_samples
    samples_per_attack = attack_samples // (len(ATTACK_LABELS) - 1)
    
    all_data = []
    
    # Generate benign samples
    features = generate_attack_profile("BENIGN", benign_samples)
    df = pd.DataFrame(features, columns=FEATURE_NAMES)
    df['Label'] = "BENIGN"
    all_data.append(df)
    print(f"  BENIGN: {benign_samples}")
    
    # Generate attack samples
    for attack in ATTACK_LABELS[1:]:
        features = generate_attack_profile(attack, samples_per_attack)
        df = pd.DataFrame(features, columns=FEATURE_NAMES)
        df['Label'] = attack
        all_data.append(df)
        print(f"  {attack}: {samples_per_attack}")
    
    # Combine and shuffle
    combined = pd.concat(all_data, ignore_index=True)
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)
    
    return combined


def main():
    DATA_DIR = Path(__file__).parent.parent / 'data'
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    output_file = DATA_DIR / 'sample_data.csv'
    
    df = generate_sample_data(50000)
    df.to_csv(output_file, index=False)
    
    print(f"\nSample data saved to: {output_file}")
    print(f"Total samples: {len(df)}")
    print(f"Features: {len(df.columns) - 1}")
    print(f"\nNow run: python ml/train.py")


if __name__ == '__main__':
    main()
