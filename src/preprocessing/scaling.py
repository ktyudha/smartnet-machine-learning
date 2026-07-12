import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.config import get_logger

logger = get_logger(__name__)

FEATURES = [
    "rssi_t2", "rssi_t1", "rssi_t0",
    "snr_t2", "snr_t1", "snr_t0",
    "delta_rssi_1", "delta_rssi_2",
    "delta_snr_1", "delta_snr_2",
]
TARGET = "label"


def split_features(df: pd.DataFrame):
    X = df[FEATURES]
    y = df[TARGET]
    return X, y


def split_data(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"Split → train: {len(X_train)}, test: {len(X_test)}")
    return X_train, X_test, y_train, y_test


def fit_scale(X_train):
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_train)
    logger.info(f"Scaler fitted on {len(X_train)} training samples")
    return X_scaled, scaler


def apply_scale(X, scaler):
    return scaler.transform(X)
