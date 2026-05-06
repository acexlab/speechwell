"""
Train and compare stronger dysarthria classifiers on fast raw-audio features.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import GridSearchCV, GroupShuffleSplit, StratifiedGroupKFold, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.dysarthria_pipeline_config import (
    DYSARTHRIA_V2_DATA_PATH,
    DYSARTHRIA_V2_MODEL_PATH,
    DYSARTHRIA_V2_REPORT_PATH,
    DYSARTHRIA_V2_SVC_PARAMS,
    get_dysarthria_numeric_columns,
)

NUMERIC_COLUMNS = get_dysarthria_numeric_columns()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train optimized dysarthria classifiers.")
    parser.add_argument(
        "--data",
        default=DYSARTHRIA_V2_DATA_PATH,
        help="Feature CSV path.",
    )
    parser.add_argument(
        "--model-out",
        default=DYSARTHRIA_V2_MODEL_PATH,
        help="Path to save best pipeline artifact.",
    )
    parser.add_argument(
        "--report-out",
        default=DYSARTHRIA_V2_REPORT_PATH,
        help="Path to save model comparison report.",
    )
    parser.add_argument(
        "--group-aware",
        action="store_true",
        help="Evaluate with speaker-wise split instead of utterance-wise random split.",
    )
    parser.add_argument(
        "--only-model",
        choices=["logistic_regression", "random_forest", "extra_trees", "svc_rbf"],
        default="",
        help="Optional single model to train/evaluate.",
    )
    return parser.parse_args()


def build_preprocessor() -> ColumnTransformer:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_transformer, NUMERIC_COLUMNS),
        ]
    )


def build_models() -> dict[str, object]:
    return {
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


def build_svm_search(group_aware: bool) -> GridSearchCV:
    svm_pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            (
                "model",
                SVC(**DYSARTHRIA_V2_SVC_PARAMS),
            ),
        ]
    )
    param_grid = {
        "model__C": [0.5, 1, 5, 10, 20],
        "model__gamma": ["scale", 0.005, 0.01, 0.05, 0.1],
    }
    cv = (
        StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=42)
        if group_aware
        else StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    )
    return GridSearchCV(
        estimator=svm_pipeline,
        param_grid=param_grid,
        scoring="f1",
        cv=cv,
        n_jobs=1,
        refit=True,
        verbose=0,
    )


def evaluate_predictions(y_true: pd.Series, y_pred: pd.Series) -> dict[str, object]:
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


def split_dataset(
    df: pd.DataFrame,
    feature_columns: list[str],
    group_aware: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    x = df[feature_columns]
    y = df["dysarthria"]

    if not group_aware:
        return train_test_split(
            x,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y,
        )

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(x, y, groups=df["speaker_id"]))
    return x.iloc[train_idx], x.iloc[test_idx], y.iloc[train_idx], y.iloc[test_idx]


def main() -> None:
    args = parse_args()
    data_path = Path(args.data)
    model_out = Path(args.model_out)
    report_out = Path(args.report_out)

    if not data_path.exists():
        raise FileNotFoundError(
            f"Feature dataset not found: {data_path}. "
            "Run python ml/training/build_torgo_audio_features.py first."
        )

    df = pd.read_csv(data_path)
    required_columns = NUMERIC_COLUMNS + ["speaker_id", "dysarthria"]
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in feature dataset: {missing_columns}")

    x_train, x_test, y_train, y_test = split_dataset(
        df,
        feature_columns=NUMERIC_COLUMNS,
        group_aware=args.group_aware,
    )

    comparison: dict[str, dict[str, object]] = {}
    best_name = ""
    best_pipeline = None
    best_metrics: dict[str, object] | None = None
    best_score = -1.0
    feature_columns = NUMERIC_COLUMNS
    best_svm_params: dict[str, object] | None = None

    model_items = build_models().items()
    if args.only_model:
        model_items = [(args.only_model, build_models()[args.only_model])]

    for model_name, estimator in model_items:
        try:
            if model_name == "svc_rbf":
                pipeline = build_svm_search(group_aware=args.group_aware)
                fit_kwargs = {"groups": df.loc[x_train.index, "speaker_id"]} if args.group_aware else {}
                pipeline.fit(x_train, y_train, **fit_kwargs)
                y_pred = pipeline.predict(x_test)
                metrics = evaluate_predictions(y_test, y_pred)
                metrics["best_params"] = pipeline.best_params_
                fitted_pipeline = pipeline.best_estimator_
                svm_params = pipeline.best_params_
            else:
                pipeline = Pipeline(
                    steps=[
                        ("preprocessor", build_preprocessor()),
                        ("model", estimator),
                    ]
                )
                pipeline.fit(x_train, y_train)
                y_pred = pipeline.predict(x_test)
                metrics = evaluate_predictions(y_test, y_pred)
                fitted_pipeline = pipeline
                svm_params = None
            comparison[model_name] = metrics

            if metrics["f1_score"] > best_score:
                best_name = model_name
                best_score = metrics["f1_score"]
                best_pipeline = fitted_pipeline
                best_metrics = metrics
                best_svm_params = svm_params

            print(
                f"{model_name}: accuracy={metrics['accuracy']:.4f}, "
                f"precision={metrics['precision']:.4f}, "
                f"recall={metrics['recall']:.4f}, f1={metrics['f1_score']:.4f}"
            )
        except Exception as exc:
            comparison[model_name] = {"error": str(exc)}
            print(f"{model_name}: failed ({exc})")

    if best_pipeline is None or best_metrics is None:
        raise RuntimeError("No model was trained successfully.")

    if best_name == "svc_rbf" and best_svm_params is not None:
        final_pipeline = Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                (
                    "model",
                    SVC(
                        class_weight=DYSARTHRIA_V2_SVC_PARAMS["class_weight"],
                        probability=DYSARTHRIA_V2_SVC_PARAMS["probability"],
                        random_state=DYSARTHRIA_V2_SVC_PARAMS["random_state"],
                        kernel=DYSARTHRIA_V2_SVC_PARAMS["kernel"],
                        C=best_svm_params["model__C"],
                        gamma=best_svm_params["model__gamma"],
                    ),
                ),
            ]
        )
    else:
        final_pipeline = Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                ("model", build_models()[best_name]),
            ]
        )
    final_pipeline.fit(df[feature_columns], df["dysarthria"])

    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_pipeline, model_out)

    report = {
        "data_path": str(data_path),
        "rows": int(len(df)),
        "group_aware_split": bool(args.group_aware),
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "best_model": best_name,
        "holdout_metrics": best_metrics,
        "all_models": comparison,
        "feature_columns": feature_columns,
        "saved_model_refit_on_full_dataset": True,
    }
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Saved best model to {model_out}")
    print(f"Saved report to {report_out}")


if __name__ == "__main__":
    main()
