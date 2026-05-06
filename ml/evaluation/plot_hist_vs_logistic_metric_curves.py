"""
Create separate learning-curve comparison plots for HistGradientBoosting and
Logistic Regression across key holdout metrics.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

CSV_PATH = Path("ml/evaluation/learning_curves/all_dysarthria_models_learning_curve.csv")
OUTPUT_DIR = CSV_PATH.parent

MODEL_KEYS = {
    "logistic_calibrated": "Logistic Regression",
    "hist_gradient_boosting": "HistGradientBoosting",
}

MODEL_COLORS = {
    "logistic_calibrated": "#f59e0b",
    "hist_gradient_boosting": "#dc2626",
}

METRICS = {
    "accuracy": "Accuracy",
    "precision": "Precision",
    "recall": "Recall",
    "f1_score": "F1 Score",
}


def load_curve_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Learning curve CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    filtered_df = df[df["model"].isin(MODEL_KEYS)].copy()
    filtered_df["training_fraction"] = filtered_df["training_fraction"].astype(float)
    filtered_df.sort_values(["training_fraction", "model"], inplace=True)

    if filtered_df.empty:
        raise ValueError(
            "No matching model rows found in learning curve CSV for "
            f"{', '.join(MODEL_KEYS)}"
        )

    return filtered_df


def build_metric_plot(df: pd.DataFrame, metric_key: str, metric_label: str) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6))

    for model_key, display_name in MODEL_KEYS.items():
        model_df = df[df["model"] == model_key].copy()
        if model_df.empty:
            continue

        ax.plot(
            model_df["training_fraction"],
            model_df[metric_key],
            marker="o",
            linewidth=2.5,
            markersize=6,
            color=MODEL_COLORS[model_key],
            label=display_name,
        )

        final_row = model_df.iloc[-1]
        ax.annotate(
            f"{final_row[metric_key]:.4f}",
            xy=(final_row["training_fraction"], final_row[metric_key]),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=MODEL_COLORS[model_key],
        )

    ax.set_title(f"{metric_label}: HistGradientBoosting vs Logistic Regression")
    ax.set_xlabel("Training Fraction")
    ax.set_ylabel(metric_label)
    ax.set_xticks(sorted(df["training_fraction"].unique()))
    ax.set_xticklabels([f"{fraction:.0%}" for fraction in sorted(df["training_fraction"].unique())])
    ax.set_ylim(0.85, 1.0 if metric_key != "f1_score" else 0.98)
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()

    output_path = OUTPUT_DIR / f"hist_gradient_boosting_vs_logistic_regression_{metric_key}.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    df = load_curve_data()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated_paths = [
        build_metric_plot(df, metric_key, metric_label)
        for metric_key, metric_label in METRICS.items()
    ]

    for path in generated_paths:
        print(f"Saved plot to {path}")


if __name__ == "__main__":
    main()
