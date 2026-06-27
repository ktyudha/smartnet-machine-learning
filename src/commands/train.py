from src.config import get_logger
from src.preprocessing import load_train, split_features
from src.training.train import train
from src.training.evaluate import evaluate
from src.training.save_model import save

logger = get_logger(__name__)


def run(args):
    logger.info("=== Training Pipeline ===")

    df = load_train()
    X, y = split_features(df)

    model = train(X, y)

    metrics = evaluate(model, X, y)
    logger.info(f"Train accuracy: {metrics['accuracy']:.4f}")

    save(model)
    logger.info("=== Training Done ===")
