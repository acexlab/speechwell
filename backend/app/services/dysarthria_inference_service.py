"""
File Logic Summary: Dysarthria inference module. Algorithm combines fluency metrics with PCA-reduced acoustic embeddings and uses a trained logistic model to output probability/label.
"""

import joblib
import numpy as np

# Load artifacts once
model = joblib.load("ml/models/dysarthria_model_v1.pkl")
pca = joblib.load("ml/models/dysarthria_pca_v1.pkl")
scaler = joblib.load("ml/models/dysarthria_scaler_v1.pkl")


def predict_dysarthria(whisper_features, acoustic_embedding):
    """
    whisper_features: dict
    acoustic_embedding: list[float]
    """

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
