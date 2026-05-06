"""
Plot current holdout metric comparison for all dysarthria models in one PNG.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPORT_PATH = Path("ml/evaluation/dysarthria_model_comparison_report.json")
PNG_PATH = Path("ml/evaluation/learning_curves/all_dysarthria_models_metric_comparison.png")

METRIC_KEYS = {
    "accuracy": "Accuracy",
    "precision": "Precision",
    "recall": "Recall",
    "f1_score": "F1 Score",
}

MODEL_COLORS = {
    "logistic_calibrated": "#f59e0b",
    "svc_rbf": "#8b5cf6",
    "random_forest": "#10b981",
    "rf_svc_ensemble": "#2563eb",
    "hist_gradient_boosting": "#dc2626",
}


def load_report() -> dict:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Comparison report not found: {REPORT_PATH}")
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def ordered_model_names(report: dict) -> list[str]:
    ranking = report.get("ranking") or []
    if ranking:
        return [str(entry["model"]) for entry in ranking]
    all_models = report.get("all_models") or {}
    return list(all_models.keys())


def main() -> None:
    report = load_report()
    model_names = ordered_model_names(report)
    all_models = report["all_models"]
    x = np.arange(len(model_names))
    display_labels = [name.replace("_", "\n") for name in model_names]
    colors = [MODEL_COLORS.get(name, "#334155") for name in model_names]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.ravel()

    for index, (metric_key, metric_label) in enumerate(METRIC_KEYS.items()):
        ax = axes[index]
        values = [float(all_models[name][metric_key]) for name in model_names]
        bars = ax.bar(x, values, color=colors, width=0.68)
        ax.set_title(f"All Dysarthria Models: {metric_label}")
        ax.set_ylabel(metric_label)
        ax.set_xticks(x)
        ax.set_xticklabels(display_labels, fontsize=9)
        ax.set_ylim(0, 1.05)
        ax.grid(axis="y", alpha=0.25)

        for bar, value in zip(bars, values):
            ax.annotate(
                f"{value:.4f}",
                xy=(bar.get_x() + bar.get_width() / 2, value),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
            )

    best_model = str(report.get("best_model") or model_names[0])
    best_threshold = report.get("best_model_threshold")
    fig.suptitle(
        f"Current Dysarthria Model Comparison (Best: {best_model}, threshold={best_threshold})",
        fontsize=15,
        fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.97))

    PNG_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(PNG_PATH, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved comparison PNG to {PNG_PATH}")


if __name__ == "__main__":
    main()
