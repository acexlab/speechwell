"""
File Logic Summary: Dysarthria inference module. Algorithm combines fluency metrics with PCA-reduced acoustic embeddings and uses a trained logistic model to output probability/label.
"""

import joblib
import numpy as np
from ..paths import (
    DYSARTHRIA_MODEL_PATH,
    DYSARTHRIA_PCA_PATH,
    DYSARTHRIA_SCALER_PATH,
)

model = None
pca = None
scaler = None


def _ensure_artifacts_loaded():
    global model, pca, scaler
    if model is not None and pca is not None and scaler is not None:
        return
    model = joblib.load(DYSARTHRIA_MODEL_PATH)
    pca = joblib.load(DYSARTHRIA_PCA_PATH)
    scaler = joblib.load(DYSARTHRIA_SCALER_PATH)


def predict_dysarthria(whisper_features, acoustic_embedding):
    """
    whisper_features: dict
    acoustic_embedding: list[float]
    """
    _ensure_artifacts_loaded()

    # Fluency features
    X_fluency = np.array([[
        whisper_features["speaking_rate_wps"],
        whisper_features["average_pause_sec"],
        whisper_features["max_pause_sec"]
    ]])

    # Acoustic features
    X_acoustic = np.array([acoustic_embedding])
    X_acoustic_scaled = scaler.transform(X_acoustic)
    X_acoustic_pca = pca.transform(X_acoustic_scaled)

    # Combine
    X = np.hstack([X_fluency, X_acoustic_pca])

    # Predict
    prob = model.predict_proba(X)[0][1]
    label = "dysarthria" if prob >= 0.5 else "healthy"

    return {
        "label": label,
        "probability": round(float(prob), 3)
    }
