import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.algorithms.decision_tree import build
from src.config import BASE_DIR, get_logger
from src.preprocessing import load_train, split_features
from src.training.tuning import PARAM_GRID

logger = get_logger(__name__)

REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

HEADER_COLOR = "#2a78d6"
BEST_COLOR = "#eaf2fc"
LINE_PARAMS = ["max_depth", "min_samples_leaf", "min_samples_split"]
BAR_PARAMS = ["criterion", "class_weight"]
PARAM_COL = {p: f"param_{p}" for p in PARAM_GRID}


def run(args):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df_train = load_train()
    X_train, y_train = split_features(df_train)

    total = 1
    for v in PARAM_GRID.values():
        total *= len(v)
    logger.info(f"Re-running GridSearchCV for tuning evidence — {total} combinations, cv=5")

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    grid = GridSearchCV(
        estimator=build(),
        param_grid=PARAM_GRID,
        cv=skf,
        scoring="f1_macro",
        n_jobs=-1,
        verbose=1,
    )
    grid.fit(X_train, y_train)
    logger.info(f"Best CV F1 (macro): {grid.best_score_:.4f}")
    logger.info(f"Best params: {grid.best_params_}")

    cv_results = _normalize(pd.DataFrame(grid.cv_results_))
    _save_tables(cv_results)
    _plot_param_grid_table(grid.best_params_, total)
    _plot_param_sensitivity(cv_results, grid.best_params_, grid.best_score_)

    logger.info(f"Tuning evidence saved to {REPORTS_DIR}")


def _fmt(v):
    return "None" if v is None or pd.isna(v) else v


def _fmt_int(v):
    return "None" if v is None or pd.isna(v) else int(v)


def _normalize(df):
    df = df.copy()
    for col in PARAM_COL.values():
        df[col] = df[col].apply(lambda v: None if (pd.isna(v) or v == "None") else v)
    return df


def _save_tables(cv_results):
    path = REPORTS_DIR / "gridsearch_cv_results.csv"
    cv_results.to_csv(path, index=False)
    logger.info(f"Saved {path}")

    top15 = cv_results.sort_values("mean_test_score", ascending=False, kind="stable").head(15)[
        ["mean_test_score", "std_test_score"] + list(PARAM_COL.values())
    ]
    top15.columns = ["cv_f1_macro_mean", "cv_f1_macro_std"] + list(PARAM_GRID.keys())
    path = REPORTS_DIR / "gridsearch_top15.csv"
    top15.to_csv(path, index=False)
    logger.info(f"Saved {path}")


def _plot_param_grid_table(best_params, total_combinations):
    rows = [
        [name, ", ".join(str(_fmt(v)) for v in values), str(_fmt(best_params[name]))]
        for name, values in PARAM_GRID.items()
    ]
    rows.append(["random_state", "42 (fixed, tidak di-tuning)", "42"])
    col_labels = ["Hyperparameter", "Nilai yang diuji (Grid Search)", "Terpilih (Best Params)"]

    fig, ax = plt.subplots(figsize=(9.5, 0.6 * len(rows) + 1.6))
    ax.axis("off")
    table = ax.table(
        cellText=rows, colLabels=col_labels, cellLoc="center", loc="center",
        colWidths=[0.22, 0.5, 0.28],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.8)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cccccc")
        if row == 0:
            cell.set_facecolor(HEADER_COLOR)
            cell.set_text_props(color="white", weight="bold")
        elif col == 2:
            cell.set_facecolor(BEST_COLOR)
            cell.set_text_props(weight="bold")

    ax.set_title(
        "Ruang Pencarian GridSearchCV — DecisionTreeClassifier\n"
        f"untuk Klasifikasi Kualitas Link (5-fold StratifiedKFold, scoring=f1_macro, "
        f"{total_combinations} kombinasi)",
        fontsize=11, pad=14,
    )
    fig.tight_layout()
    path = FIGURES_DIR / "param_grid_search.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Saved {path}")


def _slice_for(df, fixed):
    mask = pd.Series(True, index=df.index)
    for col, val in fixed.items():
        mask &= df[col].isna() if val is None else (df[col] == val)
    return df[mask]


def _plot_line_param(ax, df, pname, best_params):
    fixed = {PARAM_COL[k]: v for k, v in best_params.items() if k != pname}
    s = _slice_for(df, fixed).set_index(PARAM_COL[pname]).reindex(PARAM_GRID[pname]).reset_index()
    labels = [str(_fmt(v)) for v in PARAM_GRID[pname]]

    ax.plot(labels, s["mean_test_score"], marker="o", color=HEADER_COLOR)
    ax.fill_between(
        labels, s["mean_test_score"] - s["std_test_score"], s["mean_test_score"] + s["std_test_score"],
        alpha=0.15, color=HEADER_COLOR,
    )
    best_idx = labels.index(str(_fmt(best_params[pname])))
    ax.scatter([labels[best_idx]], [s["mean_test_score"].iloc[best_idx]], color="crimson", zorder=5, s=80, label="Terpilih")
    ax.set_title(f"{pname}\n(lainnya fixed di nilai terbaik)")
    ax.set_xlabel(pname)
    ax.set_ylabel("CV F1-macro")
    ax.legend(fontsize=8)


def _plot_bar_param(ax, df, pname, best_params):
    fixed = {PARAM_COL[k]: v for k, v in best_params.items() if k != pname}
    s = _slice_for(df, fixed).set_index(PARAM_COL[pname]).reindex(PARAM_GRID[pname]).reset_index()
    labels = [str(_fmt(v)) for v in PARAM_GRID[pname]]
    best_label = str(_fmt(best_params[pname]))
    colors = ["crimson" if lbl == best_label else HEADER_COLOR for lbl in labels]

    ax.bar(labels, s["mean_test_score"], color=colors)
    ax.errorbar(labels, s["mean_test_score"], yerr=s["std_test_score"], fmt="none", ecolor="black", capsize=4)
    ax.set_title(f"{pname}\n(lainnya fixed di nilai terbaik)")
    ax.set_ylabel("CV F1-macro")
    lo, hi = s["mean_test_score"].min(), s["mean_test_score"].max()
    ax.set_ylim(lo - 0.05, hi + 0.02)


def _plot_top_table(ax, df):
    ax.axis("off")
    # stable sort so exact ties keep GridSearchCV's own tie-break order
    # (np.argmax picks the first max in cv_results_ row order == ParameterGrid order)
    top = df.sort_values("mean_test_score", ascending=False, kind="stable").head(8)
    rows = [
        [
            f"{r['mean_test_score']:.4f}", _fmt(r["param_criterion"]),
            _fmt_int(r["param_max_depth"]), _fmt_int(r["param_min_samples_split"]),
            _fmt_int(r["param_min_samples_leaf"]), _fmt(r["param_class_weight"]),
        ]
        for _, r in top.iterrows()
    ]
    tbl = ax.table(
        cellText=rows,
        colLabels=["F1-macro", "criterion", "max_depth", "min_split", "min_leaf", "class_wt"],
        cellLoc="center", loc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7.5)
    tbl.scale(1, 1.4)
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor("#cccccc")
        if row == 0:
            cell.set_facecolor(HEADER_COLOR)
            cell.set_text_props(color="white", weight="bold")
        elif row == 1:
            cell.set_facecolor(BEST_COLOR)
            cell.set_text_props(weight="bold")
    ax.set_title("Top-8 kombinasi — rank #1 = terpilih", fontsize=10)


def _plot_param_sensitivity(cv_results, best_params, best_score):
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))

    for ax, pname in zip(axes[0], LINE_PARAMS):
        _plot_line_param(ax, cv_results, pname, best_params)
    for ax, pname in zip(axes[1, :2], BAR_PARAMS):
        _plot_bar_param(ax, cv_results, pname, best_params)
    _plot_top_table(axes[1, 2], cv_results)

    fig.suptitle(
        "Sensitivitas Hyperparameter DecisionTreeClassifier terhadap CV F1-macro\n"
        f"(GridSearchCV, 5-fold StratifiedKFold — Best CV F1-macro = {best_score:.4f})",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    path = FIGURES_DIR / "gridsearch_param_sensitivity.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    logger.info(f"Saved {path}")
