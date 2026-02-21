"""
File Logic Summary: Main ML orchestration pipeline. It runs transcription, grammar, acoustic embedding, dysarthria, stuttering, and phonological modules, then returns a combined result with safe fallbacks.
"""

from backend.app.services.dysarthria_inference_service import predict_dysarthria
from backend.app.services.grammar_service import detect_grammar_errors
from backend.app.services.phonological_service import detect_phonological_errors
from backend.app.services.stuttering_service import detect_stuttering
from ml.feature_extraction.extract_acoustic import extract_acoustic_embedding
from ml.feature_extraction.extract_whisper import analyze_audio_features


def run_full_analysis(audio_path: str) -> dict:
    """Run end-to-end analysis using ML modules in /ml."""
    whisper_features = analyze_audio_features(audio_path)
    transcript = whisper_features.get("transcript", "").strip()

    if not transcript:
        transcript = "Transcription unavailable for this audio."
        whisper_features = {**whisper_features, "transcript": transcript}

    try:
        grammar_result = detect_grammar_errors(transcript)
    except Exception:
        grammar_result = {
            "grammar_error_probability": 0.0,
            "error_count_estimate": 0,
            "corrected_text": transcript,
        }

    try:
        acoustic_embedding = extract_acoustic_embedding(audio_path)
    except Exception:
        acoustic_embedding = [0.0] * 768

    try:
        dysarthria_result = predict_dysarthria(whisper_features, acoustic_embedding)
    except Exception:
        dysarthria_result = {"label": "unknown", "probability": 0.0}

    try:
        stuttering_result = detect_stuttering(whisper_features)
    except Exception:
        stuttering_result = {
            "stuttering_probability": 0.0,
            "repetitions": 0,
            "prolongations": 0,
            "blocks": 0,
        }

    try:
        phonological_result = detect_phonological_errors(whisper_features)
    except Exception:
        phonological_result = {
            "phonological_error_probability": 0.0,
            "error_count": 0,
            "affected_words": [],
        }

    return {
        "transcript": transcript,
        "whisper_features": whisper_features,
        "grammar_result": grammar_result,
        "acoustic_embedding": acoustic_embedding,
        "dysarthria_result": dysarthria_result,
        "stuttering_result": stuttering_result,
        "phonological_result": phonological_result,
    }

