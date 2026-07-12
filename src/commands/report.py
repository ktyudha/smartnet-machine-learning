import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.tree import plot_tree

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import BASE_DIR, get_logger
from src.inference.load_model import load
from src.preprocessing import load_test, split_features
from src.preprocessing.scaling import FEATURES

logger = get_logger(__name__)

REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Best-to-worst, not alphabetical — the target is an ordinal quality scale,
# so every table/plot here reads in the order a person expects.
SEVERITY_ORDER = ["Excellent", "Good", "Fair", "Weak", "Poor"]


def run(args):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df_test = load_test()
    X_test, y_test = split_features(df_test)

    model, _ = load()
    y_pred = model.predict(X_test)

    _plot_confusion_matrix(y_test, y_pred)
    _save_classification_report(y_test, y_pred)
    _plot_feature_importance(model)
    _plot_decision_tree(model)

    logger.info(f"Report figures saved to {FIGURES_DIR}")


def _plot_confusion_matrix(y_true, y_pred):
    # sklearn gives rows=true/cols=predicted; transpose + normalize per true
    # class (columns sum to 1) to match the Predicted-vertical/True-horizontal
    # convention used elsewhere in the thesis.
    cm = confusion_matrix(y_true, y_pred, labels=SEVERITY_ORDER).T.astype(float)
    col_sums = cm.sum(axis=0, keepdims=True)
    cm_norm = np.divide(cm, col_sums, out=np.zeros_like(cm), where=col_sums != 0)

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)

    ax.set_xticks(range(len(SEVERITY_ORDER)))
    ax.set_xticklabels(SEVERITY_ORDER, rotation=45, ha="right")
    ax.set_yticks(range(len(SEVERITY_ORDER)))
    ax.set_yticklabels(SEVERITY_ORDER)
    ax.set_xlabel("True")
    ax.set_ylabel("Predicted")
    ax.set_title("Confusion Matrix Model Decision Tree\nuntuk Klasifikasi Kualitas Link")

    for i in range(len(SEVERITY_ORDER)):
        for j in range(len(SEVERITY_ORDER)):
            val = cm_norm[i, j]
            ax.text(
                j, i, f"{val:.2f}", ha="center", va="center",
                color="white" if val > 0.5 else "black", fontsize=9,
            )

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    path = FIGURES_DIR / "confusion_matrix.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    logger.info(f"Saved {path}")


def _save_classification_report(y_true, y_pred):
    report = classification_report(
        y_true, y_pred, labels=SEVERITY_ORDER, output_dict=True
    )
    rows = [
        {
            "class": label,
            "precision": report[label]["precision"],
            "recall": report[label]["recall"],
            "f1_score": report[label]["f1-score"],
            "support": int(report[label]["support"]),
        }
        for label in SEVERITY_ORDER
    ]
    df = pd.DataFrame(rows)

    path = REPORTS_DIR / "classification_report.csv"
    df.to_csv(path, index=False)
    logger.info(f"Saved {path}")
    print(df.to_string(index=False))


def _plot_feature_importance(model):
    importances = model.feature_importances_
    order = np.argsort(importances)[::-1]
    names = [FEATURES[i] for i in order][::-1]
    values = importances[order][::-1]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(range(len(names)), values, color="#2a78d6")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names)
    ax.set_xlabel("Feature Importance (Gini)")
    ax.set_title("Feature Importance — Decision Tree Klasifikasi Kualitas Link")
    for i, v in enumerate(values):
        ax.text(v + values.max() * 0.01, i, f"{v:.3f}", va="center", fontsize=8)
    fig.tight_layout()
    path = FIGURES_DIR / "feature_importance.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    logger.info(f"Saved {path}")


def _plot_decision_tree(model, max_depth: int = 3):
    # The full tree is far too deep to render (dozens of levels, hundreds of
    # leaves) — this shows only the top `max_depth` levels for illustration.
    # Thresholds are in the model's actual (standardized) input space.
    fig, ax = plt.subplots(figsize=(20, 10))
    plot_tree(
        model,
        max_depth=max_depth,
        feature_names=FEATURES,
        class_names=list(model.classes_),
        filled=False,
        rounded=True,
        fontsize=9,
        ax=ax,
    )
    ax.set_title(
        f"Struktur Decision Tree (depth={max_depth} dari total depth "
        f"{model.get_depth()}, {model.get_n_leaves()} leaves)"
    )
    fig.tight_layout()
    path = FIGURES_DIR / "decision_tree.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    logger.info(f"Saved {path}")
