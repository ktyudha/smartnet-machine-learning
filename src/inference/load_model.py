import joblib

from src.config import get_logger, MODELS_DIR

logger = get_logger(__name__)


def load():
    model_path = MODELS_DIR / "decision_tree.pkl"
    scaler_path = MODELS_DIR / "scaler.pkl"

    logger.info(f"Loading model from {model_path}")
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    return model, scaler
