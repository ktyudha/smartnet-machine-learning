from sklearn.model_selection import GridSearchCV, StratifiedKFold

from src.algorithms.decision_tree import build
from src.config import get_logger

logger = get_logger(__name__)

PARAM_GRID = {
    "criterion":         ["gini", "entropy"],
    "max_depth":         [3, 5, 7, 9, 11, None],
    "min_samples_split": [2, 5, 10, 20],
    "min_samples_leaf":  [1, 5, 10, 20],
    "class_weight":      [None, "balanced"],
}


def tune(X, y, cv=5):
    total = _count_combinations()
    logger.info(f"Starting GridSearchCV — {total} combinations, cv={cv}, scoring=f1_macro")

    # StratifiedKFold menjaga proporsi kelas Direct/Relay tetap seimbang
    # di setiap fold — penting untuk klasifikasi biner
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)

    grid = GridSearchCV(
        estimator=build(),
        param_grid=PARAM_GRID,
        cv=skf,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=1,
    )

    grid.fit(X, y)

    logger.info(f"Best CV F1 (macro) : {grid.best_score_:.4f}")
    logger.info(f"Best params        : {grid.best_params_}")

    return grid.best_estimator_, grid.best_params_, grid.best_score_


def _count_combinations():
    total = 1
    for v in PARAM_GRID.values():
        total *= len(v)
    return total
