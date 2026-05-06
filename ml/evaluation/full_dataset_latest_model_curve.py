"""
Plot full-dataset fitted-model performance for the latest deployed dysarthria model.

This script follows the current runtime comparison model, not the legacy TORGO-only
RF+SVC ensemble. It retrains the deployed model family and a logistic baseline on
50% to 100% of the combined feature dataset, evaluates each retrained model on the
full dataset, and overlays the validated holdout score for the deployed model.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
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

from ml.dysarthria_pipeline_config import (
    DYSARTHRIA_RUNTIME_MODEL_PATH,
    DYSARTHRIA_V2_LEARNING_CURVE_CSV,
    DYSARTHRIA_V2_LEARNING_CURVE_PNG,
)
from ml.training.train_dysarthria_model_comparison import (
    build_model_pipelines,
    build_sample_weights,
    rebalance_training_frame,
)

TRAINING_FRACTIONS = [fraction / 100 for fraction in range(50, 101, 5)]


def fit_pipeline_with_optional_weights(
    pipeline,
    train_df: pd.DataFrame,
    feature_columns: list[str],
    sample_weights,
) -> None:
    fit_kwargs = {}
    if sample_weights is not None:
        fit_kwargs["model__sample_weight"] = sample_weights
    try:
        pipeline.fit(train_df[feature_columns], train_df["dysarthria"], **fit_kwargs)
    except TypeError:
        pipeline.fit(train_df[feature_columns], train_df["dysarthria"])


def evaluate_curve_point(
    pipeline,
    train_df: pd.DataFrame,
    full_df: pd.DataFrame,
    feature_columns: list[str],
    threshold: float,
    positive_weight: float,
) -> dict[str, float]:
    balanced_train_df = rebalance_training_frame(train_df, max_positive_ratio=0.55)
    sample_weights = build_sample_weights(balanced_train_df["dysarthria"], positive_weight)
    fit_pipeline_with_optional_weights(
        pipeline,
        balanced_train_df,
        feature_columns,
        sample_weights,
    )
    probabilities = pipeline.predict_proba(full_df[feature_columns])[:, 1]
    predictions = (probabilities >= threshold).astype(int)
    y_true = full_df["dysarthria"]
    return {
        "accuracy": float(accuracy_score(y_true, predictions)),
        "precision": float(precision_score(y_true, predictions, zero_division=0)),
        "recall": float(recall_score(y_true, predictions, zero_division=0)),
        "f1_score": float(f1_score(y_true, predictions, zero_division=0)),
        "confusion_matrix": json.dumps(confusion_matrix(y_true, predictions).tolist()),
        "classification_report": json.dumps(
            classification_report(
                y_true,
                predictions,
                digits=4,
                zero_division=0,
                output_dict=True,
            )
        ),
    }


def main() -> None:
    report_path = Path("ml/evaluation/dysarthria_model_comparison_report.json")
    model_path = Path(DYSARTHRIA_RUNTIME_MODEL_PATH)
    out_csv = Path(DYSARTHRIA_V2_LEARNING_CURVE_CSV)
    out_png = Path(DYSARTHRIA_V2_LEARNING_CURVE_PNG)
    if not report_path.exists():
        raise FileNotFoundError(f"Comparison report not found: {report_path}")
    if not model_path.exists():
        raise FileNotFoundError(f"Runtime model not found: {model_path}")

    comparison_report = json.loads(report_path.read_text(encoding="utf-8"))
    data_path = Path(comparison_report["data_path"])
    if not data_path.exists():
        raise FileNotFoundError(f"Comparison dataset not found: {data_path}")

    model_artifact = joblib.load(model_path)
    if not isinstance(model_artifact, dict) or "pipeline" not in model_artifact:
        raise ValueError("Runtime model artifact is expected to be a dict containing a pipeline.")

    best_model_name = str(model_artifact.get("best_model_name") or comparison_report.get("best_model") or "latest_model")
    feature_columns = list(model_artifact.get("feature_columns") or comparison_report.get("feature_columns") or [])
    latest_threshold = float(model_artifact.get("threshold") or comparison_report.get("best_model_threshold") or 0.5)
    positive_weight = float(model_artifact.get("metadata", {}).get("positive_weight", 1.0))

    df = pd.read_csv(data_path)
    if not feature_columns:
        excluded = {"audio_path", "speaker_id", "dataset", "dysarthria"}
        feature_columns = [column for column in df.columns if column not in excluded]

    rows: list[dict[str, object]] = []
    logistic_rows: list[dict[str, float]] = []
    all_pipelines = build_model_pipelines()
    latest_template = clone(model_artifact["pipeline"])
    logistic_template = all_pipelines["logistic_calibrated"]
    logistic_threshold = float(
        comparison_report.get("all_models", {})
        .get("logistic_calibrated", {})
        .get("selected_threshold", 0.5)
    )

    for fraction in TRAINING_FRACTIONS:
        label = f"{int(fraction * 100)}%"
        print(f"Processing {label}...")
        if fraction < 1.0:
            train_df, _ = train_test_split(
                df,
                train_size=fraction,
                random_state=42,
                stratify=df["dysarthria"],
            )
        else:
            train_df = df.copy()

        latest_pipeline = clone(latest_template)
        latest_metrics = evaluate_curve_point(
            latest_pipeline,
            train_df,
            df,
            feature_columns,
            latest_threshold,
            positive_weight,
        )
        rows.append(
            {
                "training_fraction": fraction,
                "training_size_label": label,
                "training_samples": int(len(train_df)),
                "evaluation_scope": "full_dataset_runtime_model",
                "best_model_name": best_model_name,
                "selected_threshold": latest_threshold,
                **latest_metrics,
            }
        )

        logistic_pipeline = clone(logistic_template)
        logistic_metrics = evaluate_curve_point(
            logistic_pipeline,
            train_df,
            df,
            feature_columns,
            logistic_threshold,
            positive_weight,
        )
        logistic_rows.append(
            {
                "training_fraction": fraction,
                "training_size_label": label,
                "selected_threshold": logistic_threshold,
                **logistic_metrics,
            }
        )
        print(
            f"Completed {label}: "
            f"{best_model_name} accuracy={rows[-1]['accuracy']:.4f}, "
            f"precision={rows[-1]['precision']:.4f}, "
            f"recall={rows[-1]['recall']:.4f}, "
            f"f1={rows[-1]['f1_score']:.4f}"
        )

    results_df = pd.DataFrame(rows)
    logistic_df = pd.DataFrame(logistic_rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(out_csv, index=False)

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))
    axes = axes.ravel()
    metric_names = {
        "accuracy": "Accuracy",
        "precision": "Precision",
        "recall": "Recall",
        "f1_score": "F1 Score",
    }
    labels = results_df["training_size_label"].tolist()
    final_label = labels[-1]
    reference_metrics = {
        "accuracy": float(comparison_report["best_model_holdout_metrics"]["accuracy"]),
        "precision": float(comparison_report["best_model_holdout_metrics"]["precision"]),
        "recall": float(comparison_report["best_model_holdout_metrics"]["recall"]),
        "f1_score": float(comparison_report["best_model_holdout_metrics"]["f1_score"]),
    }
    logistic_metric_map = {
        metric_key: {
            row["training_size_label"]: float(row[metric_key])
            for row in logistic_rows
        }
        for metric_key in metric_names
    }

    for idx, (metric_key, metric_label) in enumerate(metric_names.items()):
        values = results_df[metric_key].tolist()
        axes[idx].plot(
            labels,
            values,
            "o-",
            linewidth=2,
            markersize=7,
            color="#2563eb",
            label="Latest deployed model",
        )
        logistic_values = [logistic_metric_map[metric_key][label] for label in labels]
        axes[idx].plot(
            labels,
            logistic_values,
            "s--",
            linewidth=2,
            markersize=6,
            color="#f59e0b",
            label="Logistic baseline",
        )
        axes[idx].scatter(
            [final_label],
            [reference_metrics[metric_key]],
            s=140,
            color="#dc2626",
            marker="*",
            label="Validated holdout model",
            zorder=5,
        )
        axes[idx].set_title(f"Latest Full-Data Model Curve: {metric_label}")
        axes[idx].set_xlabel("Training Dataset Size")
        axes[idx].set_ylabel(metric_label)
        axes[idx].set_ylim(0, 1.05)
        axes[idx].grid(True, alpha=0.3)
        axes[idx].legend()
        for size, value in zip(labels, values):
            axes[idx].annotate(
                f"{value:.4f}",
                xy=(size, value),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=9,
            )
        for size, value in zip(labels, logistic_values):
            axes[idx].annotate(
                f"{value:.4f}",
                xy=(size, value),
                xytext=(4, -14),
                textcoords="offset points",
                fontsize=8,
                color="#d97706",
            )
        axes[idx].annotate(
            f"{reference_metrics[metric_key]:.4f}",
            xy=(final_label, reference_metrics[metric_key]),
            xytext=(6, -14),
            textcoords="offset points",
            fontsize=9,
            color="#dc2626",
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved full-data latest-model curve CSV to {out_csv}")
    print(f"Saved full-data latest-model curve PNG to {out_png}")


if __name__ == "__main__":
    main()
