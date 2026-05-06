"""
Plot final validation metrics for the fully trained dysarthria model.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ml.dysarthria_pipeline_config import DYSARTHRIA_V2_VALIDATION_PATH

REPORT_PATH = Path(DYSARTHRIA_V2_VALIDATION_PATH)
PNG_PATH = Path("ml/evaluation/learning_curves/final_trained_model_metrics.png")


def main() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    metrics = {
        "Accuracy": float(report["accuracy"]),
        "Precision": float(report["precision"]),
        "Recall": float(report["recall"]),
        "F1 Score": float(report["f1_score"]),
    }

    labels = list(metrics.keys())
    values = list(metrics.values())
    colors = ["#1d4ed8", "#0f766e", "#b45309", "#7c3aed"]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(labels, values, color=colors, width=0.6)
    ax.set_title("Final Trained Dysarthria Model Metrics")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.25)

    for bar, value in zip(bars, values):
        ax.annotate(
            f"{value:.4f}",
            xy=(bar.get_x() + bar.get_width() / 2, value),
            xytext=(0, 6),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    fig.tight_layout()
    PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved final metrics PNG to {PNG_PATH}")


if __name__ == "__main__":
    main()
