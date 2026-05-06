"""
Evaluate SpeechWell multiclass predictions with confidence filtering.

Expected input columns:
- audio_id
- true_label
- predicted_label
- confidence_score
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    hamming_loss,
    jaccard_score,
    precision_recall_fscore_support,
)

LABELS = ["Healthy", "Stuttering", "SLI"]
DEFAULT_THRESHOLD = 0.7


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate SpeechWell multiclass predictions with confidence filtering."
    )
    parser.add_argument("--input", required=True, help="Path to CSV or JSON predictions file")
    parser.add_argument(
        "--output-json",
        default="ml/evaluation/speechwell_multiclass_metrics.json",
        help="Path to save structured metrics JSON",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Confidence threshold for accepted predictions",
    )
    return parser.parse_args()


def load_predictions(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {path}")

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() == ".json":
        return pd.read_json(path)

    raise ValueError("Unsupported input format. Use .csv or .json")


def validate_columns(df: pd.DataFrame) -> None:
    required = {"audio_id", "true_label", "predicted_label", "confidence_score"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def validate_labels(df: pd.DataFrame) -> None:
    observed = set(df["true_label"].dropna().unique()).union(
        set(df["predicted_label"].dropna().unique())
    )
    unknown = observed.difference(LABELS)
    if unknown:
        raise ValueError(f"Unsupported class labels found: {sorted(unknown)}")


def average_confidence(frame: pd.DataFrame, column: str) -> dict[str, float]:
    result: dict[str, float] = {}
    for label in LABELS:
        subset = frame.loc[frame[column] == label, "confidence_score"]
        result[label] = float(subset.mean()) if not subset.empty else 0.0
    return result


def find_most_confused_pair(cm: list[list[int]]) -> str:
    best_pair = None
    best_count = -1
    for i, left in enumerate(LABELS):
        for j, right in enumerate(LABELS):
            if i == j:
                continue
            if cm[i][j] > best_count:
                best_count = cm[i][j]
                best_pair = f"{left} -> {right}"
    if best_pair is None or best_count <= 0:
        return "No substantial class confusion after confidence filtering."
    return f"{best_pair} ({best_count} samples)"


def build_improvement_suggestions(
    uncertain_predictions: int,
    total_samples: int,
    worst_class: str,
    most_confused_classes: str,
) -> str:
    suggestions: list[str] = []
    uncertain_rate = uncertain_predictions / total_samples if total_samples else 0.0

    if uncertain_rate > 0.15:
        suggestions.append(
            "A large uncertain set was filtered out, so calibrate probabilities or review the threshold."
        )
    suggestions.append(
        f"Prioritize more labeled examples and feature refinement for {worst_class}, which is currently the weakest class."
    )
    if "->" in most_confused_classes:
        suggestions.append(
            f"Investigate features that separate the most confused pair: {most_confused_classes}."
        )
    return " ".join(suggestions)


def evaluate(df: pd.DataFrame, threshold: float) -> dict:
    df = df.copy()
    df["confidence_score"] = pd.to_numeric(df["confidence_score"], errors="coerce")
    if df["confidence_score"].isna().any():
        raise ValueError("confidence_score contains non-numeric values")

    uncertain_predictions = int((df["confidence_score"] < threshold).sum())
    accepted = df.loc[df["confidence_score"] >= threshold].copy()
    if accepted.empty:
        raise ValueError(
            "No predictions remain after confidence filtering. Lower the threshold or inspect the model outputs."
        )

    y_true = accepted["true_label"]
    y_pred = accepted["predicted_label"]

    precision, recall, f1_per_class, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=LABELS,
        average=None,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=LABELS)

    class_f1 = {label: float(score) for label, score in zip(LABELS, f1_per_class)}
    best_class = max(class_f1, key=class_f1.get)
    worst_class = min(class_f1, key=class_f1.get)
    most_confused_classes = find_most_confused_pair(cm.tolist())

    result = {
        "threshold": float(threshold),
        "total_samples": int(len(df)),
        "evaluated_samples": int(len(accepted)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": {
            label: float(score) for label, score in zip(LABELS, precision)
        },
        "recall": {
            label: float(score) for label, score in zip(LABELS, recall)
        },
        "f1_score": {
            "macro": float(f1_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)),
            "micro": float(f1_score(y_true, y_pred, labels=LABELS, average="micro", zero_division=0)),
            "weighted": float(
                f1_score(y_true, y_pred, labels=LABELS, average="weighted", zero_division=0)
            ),
        },
        "jaccard_score": float(
            jaccard_score(y_true, y_pred, labels=LABELS, average="macro", zero_division=0)
        ),
        "hamming_loss": float(hamming_loss(y_true, y_pred)),
        "confusion_matrix": cm.tolist(),
        "uncertain_predictions": uncertain_predictions,
        "insights": {
            "best_class": best_class,
            "worst_class": worst_class,
            "most_confused_classes": most_confused_classes,
            "confidence_distribution": {
                "by_true_label": average_confidence(accepted, "true_label"),
                "by_predicted_label": average_confidence(accepted, "predicted_label"),
            },
            "improvement_suggestions": build_improvement_suggestions(
                uncertain_predictions=uncertain_predictions,
                total_samples=len(df),
                worst_class=worst_class,
                most_confused_classes=most_confused_classes,
            ),
        },
    }

    if result["accuracy"] >= 0.97:
        comparison_note = (
            "Performance meets or exceeds the ~97% research benchmark, while retaining SpeechWell's practical real-time workflow."
        )
    else:
        comparison_note = (
            f"Performance is below the ~97% research benchmark by {0.97 - result['accuracy']:.4f} accuracy points, "
            "but SpeechWell still has a practical advantage because it can operate in a real-time application flow."
        )
    result["comparison_note"] = comparison_note
    return result


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output_json)

    df = load_predictions(input_path)
    validate_columns(df)
    validate_labels(df)

    report = evaluate(df, threshold=args.threshold)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nSaved JSON report: {output_path}")


if __name__ == "__main__":
    main()
