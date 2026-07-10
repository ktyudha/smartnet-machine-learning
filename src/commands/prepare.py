from src.config import get_logger
from src.preprocessing import (
    load_dataset, clean, save_interim,
    split_features, split_data, fit_scale, apply_scale, save_splits,
)
from src.training.save_model import save_scaler

logger = get_logger(__name__)


def run(args):
    logger.info("=== Prepare Data Pipeline ===")

    # 1. Raw → clean → interim
    df = load_dataset()
    df = clean(df)
    save_interim(df)

    # 2. Split features dan target
    X, y = split_features(df)

    # 3. Split train/test — scaler HANYA di-fit dari train set
    X_train, X_test, y_train, y_test = split_data(X, y)
    X_train_scaled, scaler = fit_scale(X_train)
    X_test_scaled = apply_scale(X_test, scaler)

    # 4. Simpan scaler dan split ke disk
    save_scaler(scaler)
    save_splits(X_train_scaled, y_train, X_test_scaled, y_test, X.columns.tolist())

    logger.info("=== Prepare Done ===")
