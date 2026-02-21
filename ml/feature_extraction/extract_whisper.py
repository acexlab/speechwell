"""
File Logic Summary: Extracts transcript and timing features from audio using Whisper. Algorithm computes speaking rate, average pause, max pause, and duration from segment timestamps.
"""

from typing import Any

model = None
_load_attempted = False


def _ensure_model_loaded() -> bool:
    global model, _load_attempted
    if model is not None:
        return True
    if _load_attempted:
        return False

    _load_attempted = True

    try:
        import whisper  # type: ignore

        model = whisper.load_model("base")
        return True
    except Exception:
        model = None
        return False


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
            "segments": [],
        }

    result = model.transcribe(audio_path, fp16=False, language="en")

    transcript = result.get("text", "").strip()
    segments = result.get("segments", [])

    total_words = len(transcript.split())
    total_duration = 0.0
    pauses: list[float] = []
    previous_end = None

    for seg in segments:
        start = float(seg["start"])
        end = float(seg["end"])
        segment_duration = end - start
        total_duration += segment_duration

        if previous_end is not None:
            pause = start - previous_end
            if pause > 0:
                pauses.append(pause)

        previous_end = end

    avg_pause = round(sum(pauses) / len(pauses), 3) if pauses else 0.0
    max_pause = round(max(pauses), 3) if pauses else 0.0
    speaking_rate = round(total_words / total_duration, 3) if total_duration > 0 else 0.0

    return {
        "transcript": transcript,
        "total_words": total_words,
        "speaking_rate_wps": speaking_rate,
        "average_pause_sec": avg_pause,
        "max_pause_sec": max_pause,
        "total_duration_sec": round(total_duration, 3),
        "segments": [
            {
                "start": round(float(seg.get("start", 0.0)), 2),
                "end": round(float(seg.get("end", 0.0)), 2),
                "text": seg.get("text", "").strip(),
            }
            for seg in segments
        ],
    }

