"""
Learning Curve Analysis for Dysarthria Model
"""

import argparse
import os
import ast
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


TRAINING_FRACTIONS = [fraction / 100 for fraction in range(50, 101, 5)]
METRIC_NAMES = {
    "accuracy": "Accuracy",
    "precision": "Precision",
    "recall": "Recall",
    "f1_score": "F1 Score",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot learning curves for evaluation metrics.")
    parser.add_argument(
        "--data",
        default="ml/training/torgo_features_full.pkl",
        help="Path to dataset (.pkl or .csv).",
    )
    return parser.parse_args()


def format_fraction_label(fraction: float) -> str:
    return f"{int(fraction * 100)}%"


def sample_training_subset(
    x_train_full: np.ndarray,
    y_train_full: np.ndarray,
    fraction: float,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    if fraction >= 1.0:
        return x_train_full, y_train_full

    x_subset, _, y_subset, _ = train_test_split(
        x_train_full,
        y_train_full,
        train_size=fraction,
        random_state=random_state,
        stratify=y_train_full,
    )
    return x_subset, y_subset


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
    }


def calculate_full_evaluation(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, object]:
    metric_values = calculate_metrics(y_true, y_pred)
    return {
        **metric_values,
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "classification_report": classification_report(
            y_true,
            y_pred,
            digits=4,
            zero_division=0,
            output_dict=True,
        ),
    }


def print_metrics_table(results_df: pd.DataFrame) -> None:
    table_df = results_df.copy()
    for metric in METRIC_NAMES:
        table_df[metric] = table_df[metric].map(lambda value: f"{value:.4f}")

    print("\n=== Learning Curve Metrics ===")
    print(table_df.to_string(index=False))


def load_dataset(data_path: Path) -> pd.DataFrame:
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    if data_path.suffix.lower() == ".pkl":
        return pd.read_pickle(data_path)
    if data_path.suffix.lower() == ".csv":
        return pd.read_csv(data_path)

    raise ValueError("Unsupported dataset type. Use .pkl or .csv")


def parse_embedding_cell(value: object) -> np.ndarray:
    if isinstance(value, np.ndarray):
        return value.astype(np.float32)
    if isinstance(value, list):
        return np.asarray(value, dtype=np.float32)
    if isinstance(value, str):
        return np.asarray(ast.literal_eval(value), dtype=np.float32)
    raise ValueError("Unsupported embedding value type")


def build_feature_matrix(df: pd.DataFrame) -> np.ndarray:
    fluency_cols = ["speaking_rate_wps", "avg_pause_sec", "max_pause_sec"]
    missing_cols = [col for col in fluency_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required fluency columns: {missing_cols}")

    x_fluency = df[fluency_cols].to_numpy(dtype=np.float32)

    if "embedding" not in df.columns:
        print("Embedding column not found. Running learning curves with fluency features only.")
        return x_fluency

    acoustic_vectors = np.vstack(df["embedding"].map(parse_embedding_cell).values)

    scaler = StandardScaler()
    x_acoustic_scaled = scaler.fit_transform(acoustic_vectors)
    pca = PCA(n_components=min(40, x_acoustic_scaled.shape[1]), random_state=42)
    x_acoustic_pca = pca.fit_transform(x_acoustic_scaled)
    return np.hstack([x_fluency, x_acoustic_pca])


def main():
    args = parse_args()
    print("Starting learning curve analysis...")

    # Load data
    data_path = Path(args.data)
    df = load_dataset(data_path)

    # Prepare features
    X = build_feature_matrix(df)
    y = df["dysarthria"].values

    # Fixed test set
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    results = []

    for fraction in TRAINING_FRACTIONS:
        label = format_fraction_label(fraction)
        print(f"Training on {label}...")

        X_train, y_train = sample_training_subset(
            X_train_full,
            y_train_full,
            fraction=fraction,
            random_state=42,
        )

        # Train model
        model = LogisticRegression(max_iter=5000, class_weight="balanced", random_state=42)
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        evaluation = calculate_full_evaluation(y_test, y_pred)

        results.append(
            {
                "training_fraction": fraction,
                "training_size_label": label,
                "training_samples": len(X_train),
                "accuracy": evaluation["accuracy"],
                "precision": evaluation["precision"],
                "recall": evaluation["recall"],
                "f1_score": evaluation["f1_score"],
                "confusion_matrix": json.dumps(evaluation["confusion_matrix"]),
                "classification_report": json.dumps(evaluation["classification_report"]),
            }
        )

        print(
            "  "
            + ", ".join(
                f"{display_name}: {evaluation[metric_key]:.4f}"
                for metric_key, display_name in METRIC_NAMES.items()
            )
        )
        print(f"  Confusion Matrix: {evaluation['confusion_matrix']}")

    # Save results
    os.makedirs("ml/evaluation/learning_curves", exist_ok=True)
    results_df = pd.DataFrame(results)
    results_df.to_csv("ml/evaluation/learning_curves/learning_curve_metrics.csv", index=False)
    print_metrics_table(results_df)
    results_df.to_json(
        "ml/evaluation/learning_curves/learning_curve_metrics.json",
        orient="records",
        indent=2,
    )

    # Create plot
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()

    labels = results_df["training_size_label"].tolist()

    for i, (metric, name) in enumerate(METRIC_NAMES.items()):
        values = results_df[metric].tolist()
        axes[i].plot(labels, values, "bo-", linewidth=2, markersize=8)
        axes[i].set_title(f'{name} vs Training Dataset Size')
        axes[i].set_xlabel('Training Dataset Size')
        axes[i].set_ylabel(name)
        axes[i].grid(True, alpha=0.3)
        axes[i].set_ylim(0, 1.05)

        for size, value in zip(labels, values):
            axes[i].annotate(
                f"{value:.4f}",
                xy=(size, value),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8),
            )

    plt.tight_layout()
    plt.savefig("ml/evaluation/learning_curves/learning_curves.png", dpi=300, bbox_inches='tight')
    print("Results saved!")

if __name__ == "__main__":
    main()
