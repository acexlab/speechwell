"""
Strict speaker-wise train/validation/test learning curves for dysarthria v2.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
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
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.dysarthria_pipeline_config import (
    DYSARTHRIA_V2_DATA_PATH,
    DYSARTHRIA_V2_SVC_PARAMS,
    get_dysarthria_numeric_columns,
)

NUMERIC_COLUMNS = get_dysarthria_numeric_columns()
TRAINING_FRACTIONS = [fraction / 100 for fraction in range(50, 101, 5)]


def build_pipeline() -> Pipeline:
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
            ("model", SVC(**DYSARTHRIA_V2_SVC_PARAMS)),
        ]
    )


def split_speakerwise(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    first_split = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_val_idx, test_idx = next(
        first_split.split(df, df["dysarthria"], groups=df["speaker_id"])
    )
    train_val_df = df.iloc[train_val_idx].copy()
    test_df = df.iloc[test_idx].copy()

    second_split = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, val_idx = next(
        second_split.split(
            train_val_df,
            train_val_df["dysarthria"],
            groups=train_val_df["speaker_id"],
        )
    )
    train_df = train_val_df.iloc[train_idx].copy()
    val_df = train_val_df.iloc[val_idx].copy()
    return train_df, val_df, test_df


def sample_training_subset(train_df: pd.DataFrame, fraction: float) -> pd.DataFrame:
    if fraction >= 1.0:
        return train_df.copy()
    subset_df, _ = train_test_split(
        train_df,
        train_size=fraction,
        random_state=42,
        stratify=train_df["dysarthria"],
    )
    return subset_df.copy()


def select_best_threshold(y_true: pd.Series, probabilities: np.ndarray) -> tuple[float, float]:
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in np.arange(0.1, 0.91, 0.02):
        predictions = (probabilities >= threshold).astype(int)
        score = f1_score(y_true, predictions, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_threshold = float(round(threshold, 2))
    return best_threshold, best_f1


def main() -> None:
    data_path = Path(DYSARTHRIA_V2_DATA_PATH)
    out_csv = Path("ml/evaluation/learning_curves/final_dysarthria_strict_speakerwise_curve.csv")
    out_png = Path("ml/evaluation/learning_curves/final_dysarthria_strict_speakerwise_curve.png")

    df = pd.read_csv(data_path)
    train_df, val_df, test_df = split_speakerwise(df)

    rows: list[dict[str, object]] = []
    for fraction in TRAINING_FRACTIONS:
        label = f"{int(fraction * 100)}%"
        sampled_train_df = sample_training_subset(train_df, fraction)

        pipeline = build_pipeline()
        pipeline.fit(sampled_train_df[NUMERIC_COLUMNS], sampled_train_df["dysarthria"])

        val_probabilities = pipeline.predict_proba(val_df[NUMERIC_COLUMNS])[:, 1]
        threshold, val_best_f1 = select_best_threshold(val_df["dysarthria"], val_probabilities)

        test_probabilities = pipeline.predict_proba(test_df[NUMERIC_COLUMNS])[:, 1]
        test_predictions = (test_probabilities >= threshold).astype(int)

        rows.append(
            {
                "training_fraction": fraction,
                "training_size_label": label,
                "training_samples": int(len(sampled_train_df)),
                "split_type": "speakerwise_train_val_test",
                "validation_samples": int(len(val_df)),
                "test_samples": int(len(test_df)),
                "selected_threshold": threshold,
                "validation_best_f1": float(val_best_f1),
                "accuracy": float(accuracy_score(test_df["dysarthria"], test_predictions)),
                "precision": float(
                    precision_score(test_df["dysarthria"], test_predictions, zero_division=0)
                ),
                "recall": float(
                    recall_score(test_df["dysarthria"], test_predictions, zero_division=0)
                ),
                "f1_score": float(f1_score(test_df["dysarthria"], test_predictions, zero_division=0)),
                "confusion_matrix": json.dumps(
                    confusion_matrix(test_df["dysarthria"], test_predictions).tolist()
                ),
                "classification_report": json.dumps(
                    classification_report(
                        test_df["dysarthria"],
                        test_predictions,
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
        axes[idx].plot(labels, values, "go-", linewidth=2, markersize=7)
        axes[idx].set_title(f"Strict Speaker-wise Learning Curve: {metric_label}")
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

    print(f"Saved strict learning curve CSV to {out_csv}")
    print(f"Saved strict learning curve PNG to {out_png}")


if __name__ == "__main__":
    main()
