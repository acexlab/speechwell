"""
Plot full-dataset fitted-model performance across training fractions.

This curve trains on increasing fractions of the full dataset and evaluates on the
same full dataset so the 100% point matches the final saved-model validation style.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.dysarthria_pipeline_config import (
    DYSARTHRIA_V2_DATA_PATH,
    DYSARTHRIA_V2_LEARNING_CURVE_PNG,
    DYSARTHRIA_V2_SVC_PARAMS,
    get_dysarthria_numeric_columns,
)

NUMERIC_COLUMNS = get_dysarthria_numeric_columns()
TRAINING_FRACTIONS = [fraction / 100 for fraction in range(50, 101, 5)]


def build_pipeline() -> Pipeline:
    svc_params = {**DYSARTHRIA_V2_SVC_PARAMS, "probability": False}
    return Pipeline(
        steps=[
            (
                "preprocessor",
                ColumnTransformer(
                    transformers=[
                        (
                            "numeric",
                            Pipeline(
                                steps=[
                                    ("imputer", SimpleImputer(strategy="median")),
                                    ("scaler", StandardScaler()),
                                ]
                            ),
                            NUMERIC_COLUMNS,
                        )
                    ]
                ),
            ),
            ("model", SVC(**svc_params)),
        ]
    )


def main() -> None:
    data_path = Path(DYSARTHRIA_V2_DATA_PATH)
    out_csv = Path("ml/evaluation/learning_curves/final_full_dataset_model_curve.csv")
    out_png = Path("ml/evaluation/learning_curves/final_full_dataset_model_curve.png")

    df = pd.read_csv(data_path)
    x_full = df[NUMERIC_COLUMNS]
    y_full = df["dysarthria"]

    rows: list[dict[str, object]] = []
    for fraction in TRAINING_FRACTIONS:
        label = f"{int(fraction * 100)}%"
        if fraction < 1.0:
            x_train, _, y_train, _ = train_test_split(
                x_full,
                y_full,
                train_size=fraction,
                random_state=42,
                stratify=y_full,
            )
        else:
            x_train = x_full
            y_train = y_full

        pipeline = build_pipeline()
        pipeline.fit(x_train, y_train)
        y_pred = pipeline.predict(x_full)

        rows.append(
            {
                "training_fraction": fraction,
                "training_size_label": label,
                "training_samples": int(len(x_train)),
                "evaluation_scope": "full_dataset",
                "accuracy": float(accuracy_score(y_full, y_pred)),
                "precision": float(precision_score(y_full, y_pred, zero_division=0)),
                "recall": float(recall_score(y_full, y_pred, zero_division=0)),
                "f1_score": float(f1_score(y_full, y_pred, zero_division=0)),
                "confusion_matrix": json.dumps(confusion_matrix(y_full, y_pred).tolist()),
                "classification_report": json.dumps(
                    classification_report(
                        y_full,
                        y_pred,
                        digits=4,
                        zero_division=0,
                        output_dict=True,
                    )
                ),
            }
        )

    results_df = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(out_csv, index=False)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()
    metric_names = {
        "accuracy": "Accuracy",
        "precision": "Precision",
        "recall": "Recall",
        "f1_score": "F1 Score",
    }
    labels = results_df["training_size_label"].tolist()
    for idx, (metric_key, metric_label) in enumerate(metric_names.items()):
        values = results_df[metric_key].tolist()
        axes[idx].plot(labels, values, "mo-", linewidth=2, markersize=7)
        axes[idx].set_title(f"Full Dataset Final Model Curve: {metric_label}")
        axes[idx].set_xlabel("Training Dataset Size")
        axes[idx].set_ylabel(metric_label)
        axes[idx].set_ylim(0, 1.05)
        axes[idx].grid(True, alpha=0.3)
        for size, value in zip(labels, values):
            axes[idx].annotate(
                f"{value:.4f}",
                xy=(size, value),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=9,
            )

    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved full-dataset curve CSV to {out_csv}")
    print(f"Saved full-dataset curve PNG to {out_png}")


if __name__ == "__main__":
    main()
