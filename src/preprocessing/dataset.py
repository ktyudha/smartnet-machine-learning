import pandas as pd

from src.config import get_logger
from src.config.core import BASE_DIR

logger = get_logger(__name__)

RAW_PATH       = BASE_DIR / "data" / "raw"       / "dataset_rssi_snr.csv"
INTERIM_PATH   = BASE_DIR / "data" / "interim"   / "dataset_cleaned.csv"
TRAIN_PATH     = BASE_DIR / "data" / "processed" / "train.csv"
TEST_PATH      = BASE_DIR / "data" / "processed" / "test.csv"


def load():
    logger.info(f"Loading dataset from {RAW_PATH}")
    df = pd.read_csv(RAW_PATH)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def save_interim(df: pd.DataFrame):
    df.to_csv(INTERIM_PATH, index=False)
    logger.info(f"Saved interim → {INTERIM_PATH} ({len(df)} rows)")


def save_splits(X_train, y_train, X_test, y_test, columns):
    train = pd.DataFrame(X_train, columns=columns)
    train["relay"] = y_train.values

    test = pd.DataFrame(X_test, columns=columns)
    test["relay"] = y_test.values

    train.to_csv(TRAIN_PATH, index=False)
    test.to_csv(TEST_PATH, index=False)

    logger.info(f"Saved train → {TRAIN_PATH} ({len(train)} rows)")
    logger.info(f"Saved test  → {TEST_PATH} ({len(test)} rows)")


def load_train():
    return pd.read_csv(TRAIN_PATH)


def load_test():
    return pd.read_csv(TEST_PATH)
