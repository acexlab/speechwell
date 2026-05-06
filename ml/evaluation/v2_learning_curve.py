"""
Learning curves for the v2 dysarthria models trained on raw-audio features.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.dysarthria_pipeline_config import (
    DYSARTHRIA_V2_DATA_PATH,
    DYSARTHRIA_V2_LEARNING_CURVE_CSV,
    DYSARTHRIA_V2_SVC_PARAMS,
    get_dysarthria_numeric_columns,
)

NUMERIC_COLUMNS = get_dysarthria_numeric_columns()
TRAINING_FRACTIONS = [fraction / 100 for fraction in range(50, 101, 5)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate v2 dysarthria learning curves.")
    parser.add_argument("--data", default=DYSARTHRIA_V2_DATA_PATH)
    parser.add_argument(
        "--model",
        default="svc_rbf",
        choices=["logistic_regression", "random_forest", "extra_trees", "svc_rbf"],
    )
    parser.add_argument("--group-aware", action="store_true")
    parser.add_argument(
        "--output",
        default=DYSARTHRIA_V2_LEARNING_CURVE_CSV,
    )
    parser.add_argument(
        "--png-output",
        default="",
        help="Optional PNG path for plotted learning curves. Defaults next to CSV output.",
    )
    parser.add_argument(
        "--title-prefix",
        default="Dysarthria Final Learning Curve",
        help="Prefix used in chart titles.",
    )
    parser.add_argument(
        "--reference-metrics-json",
        default="",
        help="Optional validation report JSON whose metrics are overlaid at the 100%% point.",
    )
    return parser.parse_args()


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
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
            ),
        ]
    )


def build_model(name: str):
    models = {
        "logistic_regression": LogisticRegression(
            max_iter=5000,
            class_weight="balanced",
            random_state=42,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=1,
        ),
        "extra_trees": ExtraTreesClassifier(
            n_estimators=400,
            class_weight="balanced",
            random_state=42,
            n_jobs=1,
        ),
        "svc_rbf": SVC(
            **DYSARTHRIA_V2_SVC_PARAMS,
        ),
    }
    return models[name]


def make_split(df: pd.DataFrame, group_aware: bool):
    x = df[NUMERIC_COLUMNS]
    y = df["dysarthria"]
    if not group_aware:
        return train_test_split(x, y, test_size=0.2, random_state=42, stratify=y)

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(x, y, groups=df["speaker_id"]))
    return x.iloc[train_idx], x.iloc[test_idx], y.iloc[train_idx], y.iloc[test_idx]


def sample_training_subset(x_train: pd.DataFrame, y_train: pd.Series, fraction: float):
    if fraction >= 1.0:
        return x_train, y_train
    sampled_x, _, sampled_y, _ = train_test_split(
        x_train,
        y_train,
        train_size=fraction,
        random_state=42,
        stratify=y_train,
    )
    return sampled_x, sampled_y


def main() -> None:
    args = parse_args()
    df = pd.read_csv(args.data)
    x_train_full, x_test, y_train_full, y_test = make_split(df, args.group_aware)

    rows: list[dict[str, object]] = []
    for fraction in TRAINING_FRACTIONS:
        label = f"{int(fraction * 100)}%"
        x_train, y_train = sample_training_subset(x_train_full, y_train_full, fraction)
        pipeline = Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                ("model", build_model(args.model)),
            ]
        )
        pipeline.fit(x_train, y_train)
        y_pred = pipeline.predict(x_test)
        row = {
            "training_fraction": fraction,
            "training_size_label": label,
            "training_samples": int(len(x_train)),
            "model": args.model,
            "group_aware": args.group_aware,
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
            "confusion_matrix": json.dumps(confusion_matrix(y_test, y_pred).tolist()),
            "classification_report": json.dumps(
                classification_report(y_test, y_pred, zero_division=0, digits=4, output_dict=True)
            ),
        }
        rows.append(row)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results_df = pd.DataFrame(rows)
    results_df.to_csv(out_path, index=False)

    png_path = Path(args.png_output) if args.png_output else out_path.with_suffix(".png")
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()
    metric_names = {
        "accuracy": "Accuracy",
        "precision": "Precision",
        "recall": "Recall",
        "f1_score": "F1 Score",
    }
    reference_metrics = None
    if args.reference_metrics_json:
        reference_metrics = json.loads(Path(args.reference_metrics_json).read_text(encoding="utf-8"))
    labels = results_df["training_size_label"].tolist()
    for idx, (metric_key, metric_label) in enumerate(metric_names.items()):
        values = results_df[metric_key].tolist()
        axes[idx].plot(labels, values, "bo-", linewidth=2, markersize=7)
        axes[idx].set_title(f"{args.title_prefix}: {metric_label}")
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
        if reference_metrics is not None and metric_key in reference_metrics:
            reference_value = float(reference_metrics[metric_key])
            axes[idx].scatter(["100%"], [reference_value], color="red", s=90, marker="*", zorder=5)
            axes[idx].annotate(
                f"final {reference_value:.4f}",
                xy=("100%", reference_value),
                xytext=(8, -14),
                textcoords="offset points",
                fontsize=9,
                color="red",
            )
    plt.tight_layout()
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Saved learning curve CSV to {out_path}")
    print(f"Saved learning curve PNG to {png_path}")


if __name__ == "__main__":
    main()
