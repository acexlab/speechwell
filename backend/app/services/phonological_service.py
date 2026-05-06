"""
File Logic Summary: Lightweight phonological/articulation proxy. Because the
app does not know the target word sequence, it estimates articulation risk from
pronunciation-unstable transcript patterns instead of attempting a false
phoneme-for-phoneme diagnosis.
"""

from __future__ import annotations

import re
from statistics import mean, pstdev


WORD_PATTERN = re.compile(r"[a-z']+")
FRAGMENT_PATTERN = re.compile(r"\b([a-z])(?:[-\s]+)([a-z]{2,})")


def _tokenize(text: str) -> list[str]:
    return WORD_PATTERN.findall((text or "").lower())


def _segment_rate_variability(segments: list[dict]) -> float:
    rates = [
        float(seg.get("rate_wps") or 0.0)
        for seg in segments
        if float(seg.get("duration_sec") or 0.0) >= 0.2 and int(seg.get("word_count") or 0) > 0
    ]
    if len(rates) < 2:
        return 0.0
    average = mean(rates)
    if average <= 0:
        return 0.0
    return min((pstdev(rates) / average) / 0.8, 1.0)


def detect_phonological_errors(whisper_features: dict) -> dict:
    transcript = whisper_features.get("transcript", "")
    segments = whisper_features.get("segments") or []
    words = _tokenize(transcript)

    if not words:
        return {
            "phonological_error_probability": 0.0,
            "error_count": 0,
            "affected_words": [],
        }

    one_letter_fragments = [word for word in words if len(word) == 1 and word not in {"a", "i"}]
    repaired_words = [
        word
        for fragment, word in FRAGMENT_PATTERN.findall((transcript or "").lower())
        if word.startswith(fragment)
    ]
    elongated_spelling_words = re.findall(r"\b[a-z]*(?:[aeiou]){3,}[a-z]*\b", (transcript or "").lower())

    slow_short_segments = 0
    for seg in segments:
        duration = float(seg.get("duration_sec") or 0.0)
        word_count = int(seg.get("word_count") or 0)
        if word_count in {1, 2} and duration / max(word_count, 1) >= 0.8:
            slow_short_segments += 1

    fragment_ratio = min(len(one_letter_fragments) / max(len(words), 1), 1.0)
    repair_ratio = min(len(repaired_words) / max(len(words), 1), 1.0)
    elongation_ratio = min(len(elongated_spelling_words) / max(len(words), 1), 1.0)
    segment_instability = _segment_rate_variability(segments)
    slow_segment_ratio = min(slow_short_segments / max(len(segments), 1), 1.0) if segments else 0.0

    probability = min(
        fragment_ratio * 0.35
        + repair_ratio * 0.3
        + elongation_ratio * 0.15
        + segment_instability * 0.1
        + slow_segment_ratio * 0.1,
        1.0,
    )

    affected_words = sorted(set(repaired_words + one_letter_fragments))
    error_count = len(one_letter_fragments) + len(repaired_words) + slow_short_segments
    return {
        "phonological_error_probability": round(probability, 3),
        "error_count": error_count,
        "affected_words": affected_words[:10],
    }
