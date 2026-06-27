from src.config import get_logger
from src.preprocessing import load_test, split_features
from src.training.evaluate import evaluate
from src.inference.load_model import load

logger = get_logger(__name__)


def run(args):
    logger.info("=== Evaluation Pipeline ===")

    df = load_test()
    X, y = split_features(df)

    model, _ = load()
    metrics = evaluate(model, X, y)

    print(f"\nTest Accuracy : {metrics['accuracy']:.4f}")
    print(f"\nClassification Report:\n{metrics['report']}")
    print(f"Confusion Matrix:\n{metrics['confusion_matrix']}")
