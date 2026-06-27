from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from src.config import get_logger

logger = get_logger(__name__)


def evaluate(model, X_test, y_test):
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=["Direct", "Relay"])
    cm = confusion_matrix(y_test, y_pred)

    logger.info(f"Accuracy: {accuracy:.4f}")
    logger.info(f"\n{report}")

    return {
        "accuracy": accuracy,
        "report": report,
        "confusion_matrix": cm,
    }
