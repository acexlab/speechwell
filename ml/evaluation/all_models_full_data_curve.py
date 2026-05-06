"""
Plot learning curves for all current dysarthria comparison models.

This uses the same comparison dataset and split strategy as the current model-comparison
pipeline, samples 50% to 100% of the comparison training split, evaluates on the fixed
holdout test split with each model's selected threshold, and renders all five models
into a single 2x2 learning-curve PNG.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.training.train_dysarthria_model_comparison import (
    build_model_pipelines,
    build_sample_weights,
    rebalance_training_frame,
    stratified_three_way_split,
)

REPORT_PATH = Path("ml/evaluation/dysarthria_model_comparison_report.json")
OUT_CSV = Path("ml/evaluation/learning_curves/all_dysarthria_models_learning_curve.csv")
OUT_JSON = Path("ml/evaluation/learning_curves/all_dysarthria_models_learning_curve.json")
OUT_PNG = Path("ml/evaluation/learning_curves/all_dysarthria_models_learning_curve.png")

TRAINING_FRACTIONS = [fraction / 100 for fraction in range(50, 101, 5)]
MODEL_ORDER = [
    "logistic_calibrated",
    "svc_rbf",
    "random_forest",
    "rf_svc_ensemble",
    "hist_gradient_boosting",
]
MODEL_STYLES = {
    "logistic_calibrated": {"color": "#f59e0b", "marker": "s", "linestyle": "--", "label": "Logistic calibrated"},
    "svc_rbf": {"color": "#8b5cf6", "marker": "D", "linestyle": "-", "label": "SVC RBF"},
    "random_forest": {"color": "#10b981", "marker": "^", "linestyle": "-", "label": "Random forest"},
    "rf_svc_ensemble": {"color": "#2563eb", "marker": "o", "linestyle": "-", "label": "RF + SVC ensemble"},
    "hist_gradient_boosting": {"color": "#dc2626", "marker": "*", "linestyle": "-", "label": "Hist gradient boosting"},
}
METRIC_NAMES = {
    "accuracy": "Accuracy",
    "precision": "Precision",
    "recall": "Recall",
    "f1_score": "F1 Score",
}


def fit_pipeline_with_weights(pipeline, train_df: pd.DataFrame, feature_columns: list[str], positive_weight: float) -> None:
    balanced_train_df = rebalance_training_frame(train_df, max_positive_ratio=0.55)
    sample_weights = build_sample_weights(balanced_train_df["dysarthria"], positive_weight)
    pipeline.fit(
        balanced_train_df[feature_columns],
        balanced_train_df["dysarthria"],
        model__sample_weight=sample_weights,
    )


def evaluate_on_full_dataset(
    pipeline,
    evaluation_df: pd.DataFrame,
    feature_columns: list[str],
    threshold: float,
) -> dict[str, object]:
    probabilities = pipeline.predict_proba(evaluation_df[feature_columns])[:, 1]
    predictions = (probabilities >= threshold).astype(int)
    y_true = evaluation_df["dysarthria"]
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1_score": float(f1_score(y_true, predictions, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, predictions).tolist(),
        "classification_report": classification_report(
            y_true,
            predictions,
            digits=4,
            zero_division=0,
            output_dict=True,
        ),
    }


def main() -> None:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Comparison report not found: {REPORT_PATH}")

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    data_path = Path(report["data_path"])
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    feature_columns = list(report.get("feature_columns") or [])
    if not feature_columns:
        raise ValueError("Comparison report did not include feature columns.")

    all_models_report = report.get("all_models") or {}
    df = pd.read_csv(data_path)
    train_df, _, test_df = stratified_three_way_split(
        df,
        group_aware=bool(report.get("group_aware_split", False)),
        group_by_dataset=bool(report.get("group_by_dataset", False)),
    )
    pipelines = build_model_pipelines()
    positive_weight = 1.0

    rows: list[dict[str, object]] = []

    for fraction in TRAINING_FRACTIONS:
        label = f"{int(fraction * 100)}%"
        print(f"Processing {label}...")
        if fraction < 1.0:
            sampled_train_df, _ = train_test_split(
                train_df,
                train_size=fraction,
                random_state=42,
                stratify=train_df["dysarthria"],
            )
        else:
            sampled_train_df = train_df.copy()

        for model_name in MODEL_ORDER:
            threshold = float(all_models_report[model_name]["selected_threshold"])
            pipeline = clone(pipelines[model_name])
            fit_pipeline_with_weights(pipeline, sampled_train_df, feature_columns, positive_weight)
            metrics = evaluate_on_full_dataset(pipeline, test_df, feature_columns, threshold)
            rows.append(
                {
                    "model": model_name,
                    "training_fraction": fraction,
                    "training_size_label": label,
                    "training_samples": int(len(sampled_train_df)),
                    "selected_threshold": threshold,
                    "evaluation_scope": "fixed_holdout_learning_curve",
                    "accuracy": metrics["accuracy"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1_score": metrics["f1_score"],
                    "confusion_matrix": json.dumps(metrics["confusion_matrix"]),
                    "classification_report": json.dumps(metrics["classification_report"]),
                }
            )
            print(
                f"  {model_name}: "
                f"accuracy={metrics['accuracy']:.4f}, "
                f"precision={metrics['precision']:.4f}, "
                f"recall={metrics['recall']:.4f}, "
                f"f1={metrics['f1_score']:.4f}"
            )

    results_df = pd.DataFrame(rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUT_CSV, index=False)
    OUT_JSON.write_text(results_df.to_json(orient="records", indent=2), encoding="utf-8")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.ravel()
    labels = [f"{int(fraction * 100)}%" for fraction in TRAINING_FRACTIONS]
    annotation_offsets = {
        "logistic_calibrated": (3, -12),
        "svc_rbf": (3, -2),
        "random_forest": (3, 8),
        "rf_svc_ensemble": (3, 18),
        "hist_gradient_boosting": (3, 28),
    }

    for idx, (metric_key, metric_label) in enumerate(METRIC_NAMES.items()):
        ax = axes[idx]
        for model_name in MODEL_ORDER:
            model_rows = results_df.loc[results_df["model"] == model_name].copy()
            values = model_rows[metric_key].tolist()
            style = MODEL_STYLES[model_name]
            ax.plot(
                labels,
                values,
                marker=style["marker"],
                linestyle=style["linestyle"],
                linewidth=2,
                markersize=7,
                color=style["color"],
                label=style["label"],
            )
            offset_x, offset_y = annotation_offsets[model_name]
            for size, value in zip(labels, values):
                ax.annotate(
                    f"{value:.4f}",
                    xy=(size, value),
                    xytext=(offset_x, offset_y),
                    textcoords="offset points",
                    fontsize=7.5,
                    color=style["color"],
                )

        ax.set_title(f"All Dysarthria Models Curve: {metric_label}")
        ax.set_xlabel("Training Dataset Size")
        ax.set_ylabel(metric_label)
        ax.set_ylim(0.90 if metric_key != "precision" else 0.97, 1.01)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc="lower right")

    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved all-model curve CSV to {OUT_CSV}")
    print(f"Saved all-model curve JSON to {OUT_JSON}")
    print(f"Saved all-model curve PNG to {OUT_PNG}")


if __name__ == "__main__":
    main()
