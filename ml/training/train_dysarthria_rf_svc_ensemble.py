"""
Train and evaluate a soft-voting Random Forest + SVC ensemble for dysarthria detection.

This version supports:
- TORGO-only or combined TORGO + dysarthria-only augmentation datasets
- dataset-aware / speaker-aware splits
- class balancing through sample weights
- validation-based threshold selection
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
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
from sklearn.utils.class_weight import compute_sample_weight

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.dysarthria_pipeline_config import (
    DYSARTHRIA_V2_DATA_PATH,
    DYSARTHRIA_V2_SVC_PARAMS,
    get_dysarthria_numeric_columns,
)

NUMERIC_COLUMNS = [
    column
    for column in get_dysarthria_numeric_columns()
    if column not in {"sample_rate", "channels"}
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train RF + SVC dysarthria ensemble.")
    parser.add_argument(
        "--data",
        default=DYSARTHRIA_V2_DATA_PATH,
        help="Feature CSV path.",
    )
    parser.add_argument(
        "--model-out",
        default="ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl",
        help="Path to save ensemble model artifact.",
    )
    parser.add_argument(
        "--report-out",
        default="ml/evaluation/dysarthria_model_v2_rf_svc_ensemble_report.json",
        help="Path to save evaluation report.",
    )
    parser.add_argument(
        "--group-aware",
        action="store_true",
        help="Use grouped split instead of utterance-wise split.",
    )
    parser.add_argument(
        "--group-by-dataset",
        action="store_true",
        help="Prefix groups with dataset name so no dataset-speaker pair leaks across splits.",
    )
    parser.add_argument(
        "--positive-weight",
        type=float,
        default=1.0,
        help="Extra multiplier applied to dysarthria samples in the training split.",
    )
    parser.add_argument(
        "--max-positive-ratio",
        type=float,
        default=0.55,
        help="Downsample the positive class in the training split if it exceeds this ratio.",
    )
    parser.add_argument(
        "--min-recall",
        type=float,
        default=0.80,
        help="Threshold tuning target: prefer thresholds meeting at least this recall when possible.",
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
            )
        ]
    )


def build_voter(weight_rf: float, weight_svc: float) -> VotingClassifier:
    rf = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=1,
    )
    svc = SVC(**DYSARTHRIA_V2_SVC_PARAMS)
    return VotingClassifier(
        estimators=[("random_forest", rf), ("svc_rbf", svc)],
        voting="soft",
        weights=[weight_rf, weight_svc],
        n_jobs=1,
        flatten_transform=True,
    )


def validate_dataset(df: pd.DataFrame) -> None:
    required_columns = NUMERIC_COLUMNS + ["speaker_id", "dysarthria"]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in feature dataset: {missing_columns}")


def build_group_labels(df: pd.DataFrame, *, group_by_dataset: bool) -> pd.Series:
    speaker_groups = df["speaker_id"].astype(str)
    if group_by_dataset and "dataset" in df.columns:
        return df["dataset"].astype(str) + "::" + speaker_groups
    return speaker_groups


def stratified_three_way_split(
    df: pd.DataFrame,
    *,
    group_aware: bool,
    group_by_dataset: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not group_aware:
        train_df, temp_df = train_test_split(
            df,
            test_size=0.30,
            random_state=42,
            stratify=df["dysarthria"],
        )
        val_df, test_df = train_test_split(
            temp_df,
            test_size=0.50,
            random_state=42,
            stratify=temp_df["dysarthria"],
        )
        return train_df.copy(), val_df.copy(), test_df.copy()

    groups = build_group_labels(df, group_by_dataset=group_by_dataset)
    first_split = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=42)
    train_idx, temp_idx = next(first_split.split(df, df["dysarthria"], groups=groups))
    train_df = df.iloc[train_idx].copy()
    temp_df = df.iloc[temp_idx].copy()

    temp_groups = build_group_labels(temp_df, group_by_dataset=group_by_dataset)
    second_split = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=42)
    val_idx, test_idx = next(second_split.split(temp_df, temp_df["dysarthria"], groups=temp_groups))
    val_df = temp_df.iloc[val_idx].copy()
    test_df = temp_df.iloc[test_idx].copy()
    return train_df, val_df, test_df


def rebalance_training_frame(
    train_df: pd.DataFrame,
    *,
    max_positive_ratio: float,
) -> pd.DataFrame:
    if train_df.empty:
        return train_df

    positives = train_df[train_df["dysarthria"] == 1]
    negatives = train_df[train_df["dysarthria"] == 0]
    total = len(train_df)
    if total == 0:
        return train_df

    current_positive_ratio = len(positives) / total
    if current_positive_ratio <= max_positive_ratio or negatives.empty:
        return train_df

    max_positive_count = int((max_positive_ratio / max(1e-9, 1 - max_positive_ratio)) * len(negatives))
    max_positive_count = max(1, min(len(positives), max_positive_count))
    positives = positives.sample(n=max_positive_count, random_state=42)
    rebalanced = pd.concat([negatives, positives], axis=0).sample(frac=1.0, random_state=42)
    return rebalanced.reset_index(drop=True)


def build_sample_weights(y_train: pd.Series, positive_weight: float) -> np.ndarray:
    weights = compute_sample_weight(class_weight="balanced", y=y_train)
    if positive_weight != 1.0:
        multiplier = np.where(y_train.to_numpy() == 1, positive_weight, 1.0)
        weights = weights * multiplier
    return weights.astype(float)


def select_best_threshold(
    y_true: pd.Series,
    probabilities: np.ndarray,
    *,
    min_recall: float,
) -> tuple[float, dict[str, float]]:
    best_threshold = 0.50
    best_metrics = {
        "accuracy": 0.0,
        "precision": 0.0,
        "recall": 0.0,
        "f1_score": -1.0,
    }

    preferred_threshold = None
    preferred_metrics: dict[str, float] | None = None
    for threshold in np.arange(0.25, 0.91, 0.02):
        predictions = (probabilities >= threshold).astype(int)
        metrics = {
            "accuracy": float(accuracy_score(y_true, predictions)),
            "precision": float(precision_score(y_true, predictions, zero_division=0)),
            "recall": float(recall_score(y_true, predictions, zero_division=0)),
            "f1_score": float(f1_score(y_true, predictions, zero_division=0)),
        }
        if metrics["f1_score"] > best_metrics["f1_score"]:
            best_threshold = float(round(threshold, 2))
            best_metrics = metrics

        if metrics["recall"] >= min_recall:
            if preferred_metrics is None or metrics["precision"] > preferred_metrics["precision"]:
                preferred_threshold = float(round(threshold, 2))
                preferred_metrics = metrics

    if preferred_threshold is not None and preferred_metrics is not None:
        return preferred_threshold, preferred_metrics
    return best_threshold, best_metrics


def evaluate_predictions(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, object]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            digits=4,
            zero_division=0,
            output_dict=True,
        ),
    }


def fit_pipeline(
    pipeline: Pipeline,
    train_df: pd.DataFrame,
    *,
    sample_weights: np.ndarray,
) -> None:
    pipeline.fit(
        train_df[NUMERIC_COLUMNS],
        train_df["dysarthria"],
        ensemble__sample_weight=sample_weights,
    )


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)
    model_out = Path(args.model_out)
    report_out = Path(args.report_out)

    if not data_path.exists():
        raise FileNotFoundError(f"Feature dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    validate_dataset(df)

    train_df, val_df, test_df = stratified_three_way_split(
        df,
        group_aware=args.group_aware,
        group_by_dataset=args.group_by_dataset,
    )
    train_df = rebalance_training_frame(
        train_df,
        max_positive_ratio=args.max_positive_ratio,
    )

    candidate_weights = [
        (1.0, 1.0),
        (1.0, 2.0),
        (1.0, 3.0),
        (2.0, 3.0),
    ]

    weight_results: list[dict[str, object]] = []
    best_weights: tuple[float, float] | None = None
    best_threshold = 0.50
    best_metrics: dict[str, object] | None = None
    best_score = -1.0

    sample_weights = build_sample_weights(train_df["dysarthria"], args.positive_weight)

    for weight_rf, weight_svc in candidate_weights:
        pipeline = Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                ("ensemble", build_voter(weight_rf, weight_svc)),
            ]
        )
        fit_pipeline(pipeline, train_df, sample_weights=sample_weights)
        val_probabilities = pipeline.predict_proba(val_df[NUMERIC_COLUMNS])[:, 1]
        threshold, threshold_metrics = select_best_threshold(
            val_df["dysarthria"],
            val_probabilities,
            min_recall=args.min_recall,
        )
        test_probabilities = pipeline.predict_proba(test_df[NUMERIC_COLUMNS])[:, 1]
        test_predictions = (test_probabilities >= threshold).astype(int)
        metrics = evaluate_predictions(test_df["dysarthria"], test_predictions)
        metrics["weights"] = {
            "random_forest": weight_rf,
            "svc_rbf": weight_svc,
        }
        metrics["selected_threshold"] = threshold
        metrics["validation_threshold_metrics"] = threshold_metrics
        weight_results.append(metrics)

        print(
            f"rf={weight_rf}, svc={weight_svc}, threshold={threshold:.2f}: "
            f"accuracy={metrics['accuracy']:.4f}, "
            f"precision={metrics['precision']:.4f}, "
            f"recall={metrics['recall']:.4f}, "
            f"f1={metrics['f1_score']:.4f}"
        )

        if metrics["f1_score"] > best_score:
            best_score = float(metrics["f1_score"])
            best_weights = (weight_rf, weight_svc)
            best_threshold = float(threshold)
            best_metrics = metrics

    if best_metrics is None or best_weights is None:
        raise RuntimeError("No ensemble model was trained successfully.")

    final_pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("ensemble", build_voter(best_weights[0], best_weights[1])),
        ]
    )
    full_train_weights = build_sample_weights(df["dysarthria"], args.positive_weight)
    final_pipeline.fit(
        df[NUMERIC_COLUMNS],
        df["dysarthria"],
        ensemble__sample_weight=full_train_weights,
    )

    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": final_pipeline,
            "threshold": best_threshold,
            "feature_columns": NUMERIC_COLUMNS,
            "metadata": {
                "positive_weight": args.positive_weight,
                "max_positive_ratio": args.max_positive_ratio,
            },
        },
        model_out,
    )

    dataset_breakdown = (
        df.groupby(["dataset", "dysarthria"]).size().to_dict()
        if "dataset" in df.columns
        else {}
    )
    report = {
        "data_path": str(data_path),
        "rows": int(len(df)),
        "group_aware_split": bool(args.group_aware),
        "group_by_dataset": bool(args.group_by_dataset),
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "dataset_breakdown": {str(key): int(value) for key, value in dataset_breakdown.items()},
        "feature_columns": NUMERIC_COLUMNS,
        "selected_threshold": best_threshold,
        "best_weights": {
            "random_forest": best_weights[0],
            "svc_rbf": best_weights[1],
        },
        "holdout_metrics": best_metrics,
        "all_weight_trials": weight_results,
        "saved_model_refit_on_full_dataset": True,
    }
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Saved ensemble model to {model_out}")
    print(f"Saved ensemble report to {report_out}")


if __name__ == "__main__":
    main()
