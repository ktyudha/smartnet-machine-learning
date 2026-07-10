from src.algorithms.decision_tree import build
from src.config import get_logger

logger = get_logger(__name__)


def train(X, y):
    model = build()
    model.fit(X, y)
    logger.info(f"Trained on {len(X)} samples")
    return model
