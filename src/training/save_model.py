import joblib

from src.config import get_logger, MODELS_DIR

logger = get_logger(__name__)


def save_scaler(scaler):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / "scaler.pkl"
    joblib.dump(scaler, path)
    logger.info(f"Scaler saved to {path}")


def save(model):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / "decision_tree.pkl"
    joblib.dump(model, path)
    logger.info(f"Model saved to {path}")
