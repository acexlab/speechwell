"""
File Logic Summary: Stuttering scoring module. Algorithm counts repetitions, prolongations, and block pauses, then applies weighted scoring to produce stuttering probability.
"""

import re

def detect_stuttering(whisper_features: dict) -> dict:
    transcript = whisper_features["transcript"]
    segments = whisper_features["segments"]

    # Repetitions
    words = transcript.lower().split()
    repetitions = sum(
        1 for i in range(1, len(words)) if words[i] == words[i - 1]
    )

    # Prolongations
    prolongations = len(re.findall(r"(.)\1{3,}", transcript.lower()))

    # Blocks
    blocks = 0
    prev_end = None
    for seg in segments:
        if prev_end is not None:
            if seg["start"] - prev_end >= 1.0:
                blocks += 1
        prev_end = seg["end"]

    # Score
    score = min(
        (repetitions * 0.4 + prolongations * 0.4 + blocks * 0.2) / 5,
        1.0
    )

    return {
        "stuttering_probability": round(score, 3),
        "repetitions": repetitions,
        "prolongations": prolongations,
        "blocks": blocks
    }
