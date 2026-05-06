"""
Shared configuration for the dysarthria v2/v4 pipeline.
"""

from __future__ import annotations


DYSARTHRIA_V2_DATA_PATH = "ml/training/torgo_audio_features_v4.csv"
DYSARTHRIA_V2_MODEL_PATH = "ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl"
DYSARTHRIA_RUNTIME_MODEL_PATH = "ml/models/dysarthria_best_comparison_model.pkl"
DYSARTHRIA_V2_REPORT_PATH = "ml/evaluation/dysarthria_model_v2_rf_svc_ensemble_report.json"
DYSARTHRIA_V2_VALIDATION_PATH = "ml/evaluation/validation_report_v2_rf_svc_ensemble.json"
DYSARTHRIA_V2_LEARNING_CURVE_CSV = "ml/evaluation/learning_curves/final_latest_model_full_data_curve.csv"
DYSARTHRIA_V2_LEARNING_CURVE_PNG = "ml/evaluation/learning_curves/final_latest_model_full_data_curve.png"

DYSARTHRIA_V2_SVC_PARAMS = {
    "kernel": "rbf",
    "class_weight": "balanced",
    "probability": True,
    "random_state": 42,
    "C": 5,
    "gamma": "scale",
}


def get_dysarthria_numeric_columns() -> list[str]:
    columns = [
        "duration_sec",
        "sample_rate",
        "channels",
        "rms",
        "mean_abs",
        "std",
        "max_abs",
        "q25_abs",
        "q50_abs",
        "q75_abs",
        "silence_ratio",
        "zcr",
        "centroid",
        "bandwidth",
        "rolloff_85",
        "flatness",
        "zcr_frame_mean",
        "zcr_frame_std",
        "chroma_mean",
        "chroma_std",
        "spectral_contrast_mean",
        "spectral_contrast_std",
    ]
    for idx in range(1, 14):
        columns.extend(
            [
                f"mfcc_{idx}_mean",
                f"mfcc_{idx}_std",
                f"mfcc_delta_{idx}_mean",
                f"mfcc_delta_{idx}_std",
                f"mfcc_delta2_{idx}_mean",
                f"mfcc_delta2_{idx}_std",
            ]
        )
    return columns
