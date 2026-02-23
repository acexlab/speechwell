"""
File Logic Summary: Validation utility for dysarthria model artifacts. It loads dataset/features, applies saved scaler/PCA when needed, runs predictions, and reports accuracy metrics.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate dysarthria model accuracy")
    parser.add_argument(
        "--data",
        default="ml/training/torgo_features_full.pkl",
        help="Path to dataset (.pkl or .csv)",
    )
    parser.add_argument(
        "--model",
        default="ml/models/dysarthria_model_v1.pkl",
        help="Path to trained classifier",
    )
    parser.add_argument(
        "--scaler",
        default="ml/models/dysarthria_scaler_v1.pkl",
        help="Path to fitted scaler for acoustic embedding",
    )
    parser.add_argument(
        "--pca",
        default="ml/models/dysarthria_pca_v1.pkl",
        help="Path to fitted PCA for acoustic embedding",
    )
    parser.add_argument(
        "--target",
        default="dysarthria",
        help="Target label column name",
    )
    parser.add_argument(
        "--save-json",
        default="",
        help="Optional path to save metrics JSON report",
    )
    return parser.parse_args()


def load_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    if path.suffix.lower() == ".pkl":
        return pd.read_pickle(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)

    raise ValueError("Unsupported dataset type. Use .pkl or .csv")


def parse_embedding_cell(value: Any) -> np.ndarray:
    if isinstance(value, np.ndarray):
        return value
    if isinstance(value, list):
        return np.asarray(value, dtype=np.float32)
    if isinstance(value, str):
        parsed = ast.literal_eval(value)
        return np.asarray(parsed, dtype=np.float32)
    raise ValueError("Unsupported embedding value type")


def pick_fluency_columns(df: pd.DataFrame) -> list[str]:
    speaking_col = "speaking_rate_wps"
    pause_col = "average_pause_sec" if "average_pause_sec" in df.columns else "avg_pause_sec"
    max_pause_col = "max_pause_sec"

    missing = [
        col
        for col in [speaking_col, pause_col, max_pause_col]
        if col not in df.columns
    ]
    if missing:
        raise ValueError(f"Missing required fluency columns: {missing}")

    return [speaking_col, pause_col, max_pause_col]


def build_feature_matrix(
    df: pd.DataFrame,
    scaler: Any | None,
    pca: Any | None,
) -> np.ndarray:
    fluency_cols = pick_fluency_columns(df)
    x_fluency = df[fluency_cols].to_numpy(dtype=np.float32)

    if "embedding" not in df.columns:
        return x_fluency

    acoustic_vectors = np.vstack(df["embedding"].map(parse_embedding_cell).values)

    if scaler is None or pca is None:
        raise ValueError(
            "Dataset contains 'embedding' but scaler/pca artifacts were not loaded."
        )

    acoustic_scaled = scaler.transform(acoustic_vectors)
    acoustic_pca = pca.transform(acoustic_scaled)
    return np.hstack([x_fluency, acoustic_pca])


def main() -> None:
    args = parse_args()

    data_path = Path(args.data)
    model_path = Path(args.model)
    scaler_path = Path(args.scaler)
    pca_path = Path(args.pca)

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    df = load_dataset(data_path)
    if args.target not in df.columns:
        raise ValueError(f"Target column '{args.target}' not found in dataset")

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path) if scaler_path.exists() else None
    pca = joblib.load(pca_path) if pca_path.exists() else None

    x = build_feature_matrix(df, scaler=scaler, pca=pca)
    y = df[args.target].to_numpy()

    if hasattr(model, "n_features_in_") and model.n_features_in_ != x.shape[1]:
        raise ValueError(
            "Feature mismatch between model and dataset. "
            f"Model expects {model.n_features_in_}, but built features have {x.shape[1]}."
        )

    y_pred = model.predict(x)

    acc = accuracy_score(y, y_pred)
    precision = precision_score(y, y_pred, zero_division=0)
    recall = recall_score(y, y_pred, zero_division=0)
    f1 = f1_score(y, y_pred, zero_division=0)
    cm = confusion_matrix(y, y_pred)

    print("\\n=== Validation Results ===")
    print(f"Samples: {len(df)}")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print("\\nConfusion Matrix:")
    print(cm)
    print("\\nClassification Report:")
    print(classification_report(y, y_pred, digits=4, zero_division=0))

    if args.save_json:
        report = {
            "data_path": str(data_path),
            "model_path": str(model_path),
            "samples": int(len(df)),
            "accuracy": float(acc),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "confusion_matrix": cm.tolist(),
        }
        out_path = Path(args.save_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\\nSaved JSON report: {out_path}")


if __name__ == "__main__":
    main()
