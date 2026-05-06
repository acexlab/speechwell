"""
File Logic Summary: Extracts transcript and timing features from audio using
Whisper. The runtime prefers a stronger English-only model for cleaner local
transcripts and computes speaking rate, pause, and duration metrics.
"""

import os
from typing import Any

import librosa

model = None
loaded_model_name = None
_load_attempted = False
DEFAULT_MODEL_CANDIDATES = ("small.en", "base.en", "base")
TRANSCRIBE_OPTIONS = {
    "fp16": False,
    "task": "transcribe",
    "language": "en",
    "temperature": 0,
    "beam_size": 5,
    "best_of": 5,
    "condition_on_previous_text": True,
    "suppress_tokens": "-1",
}


def _candidate_model_names() -> list[str]:
    configured = (os.getenv("WHISPER_MODEL") or "").strip()
    names: list[str] = []
    if configured:
        names.append(configured)
    for name in DEFAULT_MODEL_CANDIDATES:
        if name not in names:
            names.append(name)
    return names


def _ensure_model_loaded() -> bool:
    global model, loaded_model_name, _load_attempted
    if model is not None:
        return True
    if _load_attempted:
        return False

    _load_attempted = True

    try:
        import whisper  # type: ignore

        for candidate in _candidate_model_names():
            try:
                model = whisper.load_model(candidate)
                loaded_model_name = candidate
                return True
            except Exception:
                continue
        model = None
        loaded_model_name = None
        return False
    except Exception:
        model = None
        loaded_model_name = None
        return False


def _calculate_segment_pause_metrics(segments: list[dict[str, Any]]) -> tuple[float, float, list[float]]:
    pauses: list[float] = []
    previous_end = None

    for seg in segments:
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", 0.0))
        if previous_end is not None:
            pause = round(start - previous_end, 3)
            if pause > 0:
                pauses.append(pause)
        previous_end = end

    avg_pause = round(sum(pauses) / len(pauses), 3) if pauses else 0.0
    max_pause = round(max(pauses), 3) if pauses else 0.0
    return avg_pause, max_pause, pauses


def _calculate_audio_pause_metrics(audio_path: str) -> tuple[float, float, float, list[float]]:
    """
    Detect pauses from the waveform instead of Whisper segments.
    Whisper segments are often contiguous, which hides real pauses.
    """
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    total_duration = round(librosa.get_duration(y=y, sr=sr), 3)

    if y.size == 0 or total_duration <= 0:
        return 0.0, 0.0, 0.0, []

    non_silent_intervals = librosa.effects.split(
        y,
        top_db=28,
        frame_length=2048,
        hop_length=512,
    )

    if len(non_silent_intervals) < 2:
        return 0.0, 0.0, total_duration, []

    pauses: list[float] = []
    min_pause_sec = 0.12

    for previous, current in zip(non_silent_intervals, non_silent_intervals[1:]):
        previous_end = previous[1] / sr
        current_start = current[0] / sr
        pause = round(current_start - previous_end, 3)
        if pause >= min_pause_sec:
            pauses.append(pause)

    avg_pause = round(sum(pauses) / len(pauses), 3) if pauses else 0.0
    max_pause = round(max(pauses), 3) if pauses else 0.0
    return avg_pause, max_pause, total_duration, pauses


def analyze_audio_features(audio_path: str) -> dict[str, Any]:
    """Extract transcript and fluency metrics from audio."""
    if not _ensure_model_loaded():
        return {
            "transcript": "",
            "total_words": 0,
            "speaking_rate_wps": 0.0,
            "average_pause_sec": 0.0,
            "max_pause_sec": 0.0,
            "total_duration_sec": 0.0,
            "pause_durations": [],
            "long_pause_count": 0,
            "segments": [],
            "transcription_model": None,
        }

    result = model.transcribe(audio_path, **TRANSCRIBE_OPTIONS)

    transcript = result.get("text", "").strip()
    segments = result.get("segments", [])

    total_words = len(transcript.split())
    segment_total_duration = 0.0
    for seg in segments:
        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", 0.0))
        if end > start:
            segment_total_duration += end - start

    try:
        avg_pause, max_pause, total_duration, pause_durations = _calculate_audio_pause_metrics(audio_path)
    except Exception:
        avg_pause, max_pause, pause_durations = _calculate_segment_pause_metrics(segments)
        total_duration = round(segment_total_duration, 3)

    speaking_duration = segment_total_duration if segment_total_duration > 0 else total_duration
    speaking_rate = round(total_words / speaking_duration, 3) if speaking_duration > 0 else 0.0
    long_pause_count = sum(1 for pause in pause_durations if pause >= 0.75)

    return {
        "transcript": transcript,
        "total_words": total_words,
        "speaking_rate_wps": speaking_rate,
        "average_pause_sec": avg_pause,
        "max_pause_sec": max_pause,
        "total_duration_sec": round(total_duration, 3),
        "pause_durations": [round(float(pause), 3) for pause in pause_durations],
        "long_pause_count": long_pause_count,
        "segments": [
            {
                "start": round(float(seg.get("start", 0.0)), 2),
                "end": round(float(seg.get("end", 0.0)), 2),
                "duration_sec": round(max(0.0, float(seg.get("end", 0.0)) - float(seg.get("start", 0.0))), 2),
                "word_count": len((seg.get("text") or "").strip().split()),
                "rate_wps": round(
                    len((seg.get("text") or "").strip().split()) /
                    max(0.01, float(seg.get("end", 0.0)) - float(seg.get("start", 0.0))),
                    3,
                ),
                "text": seg.get("text", "").strip(),
            }
            for seg in segments
        ],
        "transcription_model": loaded_model_name,
    }

