"""
File Logic Summary: Dysarthria inference module. It prefers the latest full-audio
pipeline model and only falls back to the legacy v1 fluency+embedding stack when needed.
"""

import joblib
import numpy as np
import pandas as pd
from ..paths import (
    DYSARTHRIA_MODEL_PATH,
    DYSARTHRIA_MODEL_V2_PATH,
    DYSARTHRIA_RUNTIME_MODEL_FILE,
    DYSARTHRIA_PCA_PATH,
    DYSARTHRIA_SCALER_PATH,
)
from ml.feature_extraction.raw_audio_features import extract_raw_audio_features
from ml.dysarthria_pipeline_config import get_dysarthria_numeric_columns

model = None
pca = None
scaler = None
model_v2 = None
model_v2_threshold = None
model_v2_feature_columns = None
latest_artifacts_loaded = False
legacy_artifacts_loaded = False

CANONICAL_SAMPLE_RATE = 16000
CANONICAL_CHANNELS = 1
ACCENT_MISMATCH_FLOOR = 0.65
SYMPTOM_GATED_DYSARTHRIA_THRESHOLD = 0.75
RAW_PROBABILITY_OVERRIDE_THRESHOLD = 0.95
LEAKY_FEATURE_COLUMNS = {"sample_rate", "channels"}
NUMERIC_COLUMNS = get_dysarthria_numeric_columns()


def _ensure_latest_artifacts_loaded():
    global model_v2, model_v2_threshold, model_v2_feature_columns, latest_artifacts_loaded
    if latest_artifacts_loaded:
        return
    active_path = DYSARTHRIA_RUNTIME_MODEL_FILE if DYSARTHRIA_RUNTIME_MODEL_FILE.exists() else DYSARTHRIA_MODEL_V2_PATH
    if active_path.exists():
        loaded = joblib.load(active_path)
        if isinstance(loaded, dict):
            model_v2 = loaded.get("pipeline")
            model_v2_threshold = float(loaded.get("threshold", SYMPTOM_GATED_DYSARTHRIA_THRESHOLD))
            model_v2_feature_columns = list(loaded.get("feature_columns") or NUMERIC_COLUMNS)
        else:
            model_v2 = loaded
            model_v2_threshold = SYMPTOM_GATED_DYSARTHRIA_THRESHOLD
            model_v2_feature_columns = NUMERIC_COLUMNS
    else:
        model_v2 = None
        model_v2_threshold = None
        model_v2_feature_columns = None
    latest_artifacts_loaded = True


def _ensure_legacy_artifacts_loaded():
    global model, pca, scaler, legacy_artifacts_loaded
    if legacy_artifacts_loaded:
        return
    model = joblib.load(DYSARTHRIA_MODEL_PATH) if DYSARTHRIA_MODEL_PATH.exists() else None
    pca = joblib.load(DYSARTHRIA_PCA_PATH) if DYSARTHRIA_PCA_PATH.exists() else None
    scaler = joblib.load(DYSARTHRIA_SCALER_PATH) if DYSARTHRIA_SCALER_PATH.exists() else None
    legacy_artifacts_loaded = True


def compute_symptom_score(features: dict) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []

    rms = float(features.get("rms") or 0.0)
    silence_ratio = float(features.get("silence_ratio") or 0.0)
    spectral_flatness = float(features.get("flatness") or 0.0)
    zcr = float(features.get("zcr") or 0.0)

    mfcc_stds = [
        float(features.get(f"mfcc_{idx}_std") or 0.0)
        for idx in range(1, 14)
    ]
    mfcc_delta_stds = [
        float(features.get(f"mfcc_delta_{idx}_std") or 0.0)
        for idx in range(1, 14)
    ]
    mfcc_variance_proxy = float(np.mean(mfcc_stds + mfcc_delta_stds)) if (mfcc_stds or mfcc_delta_stds) else 0.0

    if rms < 0.01:
        score += 1
        reasons.append("low RMS energy")
    if silence_ratio > 0.45:
        score += 1
        reasons.append("high silence ratio")
    if spectral_flatness > 0.22:
        score += 1
        reasons.append("elevated spectral flatness")
    if zcr < 0.03 or zcr > 0.18:
        score += 1
        reasons.append("abnormal zero-crossing rate")
    if mfcc_variance_proxy > 14.0:
        score += 1
        reasons.append("high MFCC variance")

    return min(score, 5), reasons


def _sanitize_v2_feature_row(feature_row: dict) -> dict:
    sanitized = dict(feature_row)

    # Neutralize train-set specific fields at inference time. We keep the
    # columns present so the saved pipeline still accepts the input schema.
    sanitized["sample_rate"] = CANONICAL_SAMPLE_RATE
    sanitized["channels"] = CANONICAL_CHANNELS

    # Enforce the exact training column order and fill any missing values.
    feature_columns = model_v2_feature_columns or NUMERIC_COLUMNS
    ordered = {column: sanitized.get(column, np.nan) for column in feature_columns}
    return ordered


def _count_healthy_signals(whisper_features: dict, feature_row: dict) -> int:
    transcript = (whisper_features.get("transcript") or "").strip()
    word_count = len(transcript.split())
    speaking_rate = float(whisper_features.get("speaking_rate_wps") or 0.0)
    average_pause = float(whisper_features.get("average_pause_sec") or 0.0)
    max_pause = float(whisper_features.get("max_pause_sec") or 0.0)
    whisper_duration_sec = float(whisper_features.get("total_duration_sec") or 0.0)
    duration_sec = float(whisper_duration_sec or feature_row.get("duration_sec") or 0.0)
    silence_ratio = float(feature_row.get("silence_ratio") or 0.0)
    rms = float(feature_row.get("rms") or 0.0)
    has_transcript_features = word_count > 0 and whisper_duration_sec > 0

    signals = 0
    if word_count >= 6:
        signals += 1
    if has_transcript_features and 1.0 <= speaking_rate <= 4.5:
        signals += 1
    if has_transcript_features and average_pause <= 0.8:
        signals += 1
    if has_transcript_features and max_pause <= 2.0:
        signals += 1
    if duration_sec >= 2.5:
        signals += 1
    if silence_ratio <= 0.55:
        signals += 1
    if rms >= 0.003:
        signals += 1
    return signals


def _apply_symptom_gated_decision(
    raw_probability: float,
    whisper_features: dict,
    symptom_feature_row: dict,
) -> tuple[float, str, int, str]:
    probability = max(0.0, min(1.0, float(raw_probability)))
    healthy_signal_count = _count_healthy_signals(whisper_features, symptom_feature_row)
    symptom_score, symptom_reasons = compute_symptom_score(symptom_feature_row)
    explanation = "Symptoms and model probability do not support dysarthria."

    # Strongly protect against false positives when no symptom evidence exists.
    if symptom_score <= 1:
        if probability >= ACCENT_MISMATCH_FLOOR:
            probability *= 0.4
            explanation = "Likely accent or unseen-speaker mismatch; no strong dysarthria symptoms detected."
        else:
            probability *= 0.3
            explanation = "No strong dysarthria symptoms detected."
        return round(max(0.0, min(1.0, probability)), 3), "healthy", symptom_score, explanation

    # Preserve obvious positives when the model is very confident and the
    # full-recording symptom profile shows multiple dysarthria-like signals.
    if probability >= RAW_PROBABILITY_OVERRIDE_THRESHOLD and symptom_score >= 2:
        probability = round(max(probability, RAW_PROBABILITY_OVERRIDE_THRESHOLD), 3)
        explanation = (
            "Dysarthria predicted because the model remained highly confident and the "
            "full recording showed multiple abnormal speech symptoms: "
            + ", ".join(symptom_reasons or ["multiple abnormal speech features"])
        )
        return probability, "dysarthria", symptom_score, explanation

    # Keep the existing healthy-speech guardrail for moderate raw probabilities.
    if symptom_score <= 2:
        if probability >= 0.6 and healthy_signal_count >= 6:
            probability *= 0.35
        elif probability >= 0.6 and healthy_signal_count >= 5:
            probability *= 0.45
        elif probability >= 0.6 and healthy_signal_count >= 4:
            probability *= 0.6
        elif probability >= 0.6 and healthy_signal_count >= 3:
            probability *= 0.75

    probability = round(max(0.0, min(1.0, probability)), 3)

    if probability >= SYMPTOM_GATED_DYSARTHRIA_THRESHOLD and symptom_score >= 2:
        explanation = (
            "Dysarthria predicted because model probability remained high and symptom evidence was present: "
            + ", ".join(symptom_reasons or ["multiple abnormal speech features"])
        )
        return probability, "dysarthria", symptom_score, explanation

    explanation = (
        "Classified as healthy because dysarthria requires both high model probability "
        f"and symptom evidence. Symptom score={symptom_score}/5."
    )
    return probability, "healthy", symptom_score, explanation


def _predict_with_v2(audio_path: str, whisper_features: dict):
    model_feature_row = extract_raw_audio_features(audio_path)
    symptom_feature_row = extract_raw_audio_features(audio_path, target_frames=None)
    x = pd.DataFrame([_sanitize_v2_feature_row(model_feature_row)])
    raw_prob = float(model_v2.predict_proba(x)[0][1])
    prob, label, symptom_score, explanation = _apply_symptom_gated_decision(
        raw_prob, whisper_features, symptom_feature_row
    )
    threshold = float(model_v2_threshold or SYMPTOM_GATED_DYSARTHRIA_THRESHOLD)
    if symptom_score >= 2 and prob >= threshold:
        label = "dysarthria"
    elif symptom_score <= 1:
        label = "healthy"
    elif label == "dysarthria" and prob < threshold:
        label = "healthy"
    return {
        "label": label,
        "probability": prob,
        "symptom_score": symptom_score,
        "explanation": explanation,
        "model_version": "runtime_comparison_model" if DYSARTHRIA_RUNTIME_MODEL_FILE.exists() else "rf_svc_ensemble",
    }


def predict_dysarthria(whisper_features, acoustic_embedding, audio_path: str | None = None):
    """
    whisper_features: dict
    acoustic_embedding: list[float]
    """
    _ensure_latest_artifacts_loaded()

    if model_v2 is not None and audio_path:
        return _predict_with_v2(audio_path, whisper_features)

    _ensure_legacy_artifacts_loaded()

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
    raw_prob = float(model.predict_proba(X)[0][1])
    prob = raw_prob
    label = "dysarthria" if prob >= 0.5 else "healthy"
    symptom_score = None
    explanation = "Legacy prediction path used."
    if audio_path:
        try:
            feature_row = extract_raw_audio_features(audio_path, target_frames=None)
            prob, label, symptom_score, explanation = _apply_symptom_gated_decision(
                raw_prob, whisper_features, feature_row
            )
        except Exception:
            prob = round(raw_prob, 3)
    else:
        prob = round(raw_prob, 3)

    return {
        "label": label,
        "probability": round(float(prob), 3),
        "symptom_score": symptom_score,
        "explanation": explanation,
        "model_version": "v1",
    }
