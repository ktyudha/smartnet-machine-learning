from src.config import get_logger
from src.preprocessing import load_train, load_test, split_features
from src.training.tuning import tune
from src.training.evaluate import evaluate
from src.training.save_model import save

logger = get_logger(__name__)


def run(args):
    logger.info("=== Tuning Pipeline ===")

    # Load train set (sudah scaled dari prepare)
    df_train = load_train()
    X_train, y_train = split_features(df_train)

    # GridSearchCV pada train set
    model, best_params, best_cv_score = tune(X_train, y_train)

    print(f"\nBest CV F1 (macro) : {best_cv_score:.4f}")
    print(f"Best params        : {best_params}")

    # Evaluasi final pada test set — angka yang valid
    df_test = load_test()
    X_test, y_test = split_features(df_test)

    metrics = evaluate(model, X_test, y_test)

    print(f"\nTest Accuracy : {metrics['accuracy']:.4f}")
    print(f"\nClassification Report:\n{metrics['report']}")
    print(f"Confusion Matrix:\n{metrics['confusion_matrix']}")

    # Simpan model terbaik (replace decision_tree.pkl)
    save(model)

    logger.info("=== Tuning Done ===")
