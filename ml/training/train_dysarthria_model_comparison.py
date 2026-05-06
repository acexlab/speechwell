"""
Train and compare multiple dysarthria classifiers on TORGO-only or combined features.

Models compared:
- calibrated logistic regression baseline
- RBF SVM
- Random Forest
- RF + SVM soft-voting ensemble
- HistGradientBoostingClassifier
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
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

from ml.dysarthria_pipeline_config import DYSARTHRIA_V2_SVC_PARAMS, get_dysarthria_numeric_columns

NUMERIC_COLUMNS = [
    column
    for column in get_dysarthria_numeric_columns()
    if column not in {"sample_rate", "channels"}
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare dysarthria models on feature CSVs.")
    parser.add_argument(
        "--data",
        default="ml/training/combined_audio_features.csv",
        help="Feature CSV path.",
    )
    parser.add_argument(
        "--report-out",
        default="ml/evaluation/dysarthria_model_comparison_report.json",
        help="Path to save comparison report.",
    )
    parser.add_argument(
        "--best-model-out",
        default="ml/models/dysarthria_best_comparison_model.pkl",
        help="Path to save the best-performing model.",
    )
    parser.add_argument(
        "--group-aware",
        action="store_true",
        help="Use grouped split instead of utterance-wise split.",
    )
    parser.add_argument(
        "--group-by-dataset",
        action="store_true",
        help="Prefix groups with dataset name so dataset-speaker pairs never leak across splits.",
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


def rebalance_training_frame(train_df: pd.DataFrame, *, max_positive_ratio: float) -> pd.DataFrame:
    positives = train_df[train_df["dysarthria"] == 1]
    negatives = train_df[train_df["dysarthria"] == 0]
    if train_df.empty or negatives.empty:
        return train_df

    current_positive_ratio = len(positives) / len(train_df)
    if current_positive_ratio <= max_positive_ratio:
        return train_df

    max_positive_count = int((max_positive_ratio / max(1e-9, 1 - max_positive_ratio)) * len(negatives))
    max_positive_count = max(1, min(len(positives), max_positive_count))
    positives = positives.sample(n=max_positive_count, random_state=42)
    return (
        pd.concat([negatives, positives], axis=0)
        .sample(frac=1.0, random_state=42)
        .reset_index(drop=True)
    )


def build_sample_weights(y_train: pd.Series, positive_weight: float) -> np.ndarray:
    weights = compute_sample_weight(class_weight="balanced", y=y_train)
    if positive_weight != 1.0:
        weights = weights * np.where(y_train.to_numpy() == 1, positive_weight, 1.0)
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


def build_model_pipelines() -> dict[str, Pipeline]:
    calibrated_logistic = CalibratedClassifierCV(
        estimator=LogisticRegression(
            max_iter=4000,
            class_weight="balanced",
            random_state=42,
        ),
        method="sigmoid",
        cv=3,
    )
    svm = SVC(**DYSARTHRIA_V2_SVC_PARAMS)
    rf = RandomForestClassifier(
        n_estimators=350,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=1,
    )
    ensemble = VotingClassifier(
        estimators=[
            ("random_forest", rf),
            ("svc_rbf", SVC(**DYSARTHRIA_V2_SVC_PARAMS)),
        ],
        voting="soft",
        weights=[2.0, 3.0],
        n_jobs=1,
        flatten_transform=True,
    )
    hgb = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_depth=6,
        max_iter=250,
        random_state=42,
    )

    estimators = {
        "logistic_calibrated": calibrated_logistic,
        "svc_rbf": svm,
        "random_forest": rf,
        "rf_svc_ensemble": ensemble,
        "hist_gradient_boosting": hgb,
    }
    return {
        name: Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                ("model", estimator),
            ]
        )
        for name, estimator in estimators.items()
    }


def fit_pipeline(
    pipeline: Pipeline,
    train_df: pd.DataFrame,
    *,
    sample_weights: np.ndarray,
) -> None:
    model = pipeline.named_steps["model"]
    fit_kwargs = {}
    if isinstance(model, VotingClassifier):
        fit_kwargs["model__sample_weight"] = sample_weights
    elif isinstance(model, (RandomForestClassifier, HistGradientBoostingClassifier, SVC, LogisticRegression)):
        fit_kwargs["model__sample_weight"] = sample_weights
    pipeline.fit(
        train_df[NUMERIC_COLUMNS],
        train_df["dysarthria"],
        **fit_kwargs,
    )


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)
    report_out = Path(args.report_out)
    best_model_out = Path(args.best_model_out)

    if not data_path.exists():
        raise FileNotFoundError(f"Feature dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    validate_dataset(df)
    train_df, val_df, test_df = stratified_three_way_split(
        df,
        group_aware=args.group_aware,
        group_by_dataset=args.group_by_dataset,
    )
    train_df = rebalance_training_frame(train_df, max_positive_ratio=args.max_positive_ratio)
    sample_weights = build_sample_weights(train_df["dysarthria"], args.positive_weight)

    comparison_results: dict[str, dict[str, object]] = {}
    best_name = ""
    best_threshold = 0.50
    best_holdout_metrics: dict[str, object] | None = None
    best_score = -1.0

    for model_name, pipeline in build_model_pipelines().items():
        try:
            fit_pipeline(pipeline, train_df, sample_weights=sample_weights)
            val_probabilities = pipeline.predict_proba(val_df[NUMERIC_COLUMNS])[:, 1]
            threshold, threshold_metrics = select_best_threshold(
                val_df["dysarthria"],
                val_probabilities,
                min_recall=args.min_recall,
            )
            test_probabilities = pipeline.predict_proba(test_df[NUMERIC_COLUMNS])[:, 1]
            test_predictions = (test_probabilities >= threshold).astype(int)
            holdout_metrics = evaluate_predictions(test_df["dysarthria"], test_predictions)
            holdout_metrics["selected_threshold"] = threshold
            holdout_metrics["validation_threshold_metrics"] = threshold_metrics
            comparison_results[model_name] = holdout_metrics

            print(
                f"{model_name}: threshold={threshold:.2f}, "
                f"accuracy={holdout_metrics['accuracy']:.4f}, "
                f"precision={holdout_metrics['precision']:.4f}, "
                f"recall={holdout_metrics['recall']:.4f}, "
                f"f1={holdout_metrics['f1_score']:.4f}"
            )

            if holdout_metrics["f1_score"] > best_score:
                best_score = float(holdout_metrics["f1_score"])
                best_name = model_name
                best_threshold = float(threshold)
                best_holdout_metrics = holdout_metrics
        except Exception as exc:
            comparison_results[model_name] = {"error": str(exc)}
            print(f"{model_name}: failed ({exc})")

    if not best_name or best_holdout_metrics is None:
        raise RuntimeError("No comparison model completed successfully.")

    final_pipeline = build_model_pipelines()[best_name]
    full_weights = build_sample_weights(df["dysarthria"], args.positive_weight)
    fit_pipeline(final_pipeline, df, sample_weights=full_weights)

    best_model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "pipeline": final_pipeline,
            "threshold": best_threshold,
            "feature_columns": NUMERIC_COLUMNS,
            "best_model_name": best_name,
            "metadata": {
                "positive_weight": args.positive_weight,
                "max_positive_ratio": args.max_positive_ratio,
            },
        },
        best_model_out,
    )

    ranking = sorted(
        (
            {
                "model": model_name,
                "f1_score": result.get("f1_score", -1),
                "precision": result.get("precision", 0),
                "recall": result.get("recall", 0),
                "accuracy": result.get("accuracy", 0),
                "selected_threshold": result.get("selected_threshold"),
            }
            for model_name, result in comparison_results.items()
            if "error" not in result
        ),
        key=lambda item: item["f1_score"],
        reverse=True,
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
        "feature_columns": NUMERIC_COLUMNS,
        "dataset_breakdown": {str(key): int(value) for key, value in dataset_breakdown.items()},
        "best_model": best_name,
        "best_model_threshold": best_threshold,
        "best_model_holdout_metrics": best_holdout_metrics,
        "ranking": ranking,
        "all_models": comparison_results,
    }
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Saved comparison report to {report_out}")
    print(f"Saved best comparison model to {best_model_out}")


if __name__ == "__main__":
    main()
