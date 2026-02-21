"""
File Logic Summary: Python module for backend/ML logic that contributes to request handling, analysis, or model workflow.
"""

from ml.feature_extraction.extract_whisper import analyze_audio_features


def analyze_audio(audio_path: str) -> dict:
    """Backward-compatible wrapper around ML feature extraction module."""
    return analyze_audio_features(audio_path)

