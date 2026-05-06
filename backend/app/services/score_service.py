"""
File Logic Summary: Shared scoring helpers used by API responses and report rendering.
"""

import re


def _clamp_probability(value: float | int | None) -> float:
    try:
        numeric = float(value or 0.0)
    except (TypeError, ValueError):
        numeric = 0.0
    return max(0.0, min(1.0, numeric))


def count_words(text: str | None) -> int:
    return len(re.findall(r"\b[\w']+\b", text or ""))


def calculate_grammar_error_probability(
    error_count: int | float | None,
    transcript: str | None = None,
    *,
    fallback_probability: float | int | None = None,
) -> float:
    total_words = count_words(transcript)
    if total_words > 0:
        try:
            numeric_errors = max(0.0, float(error_count or 0.0))
        except (TypeError, ValueError):
            numeric_errors = 0.0
        return _clamp_probability(numeric_errors / total_words)
    return _clamp_probability(fallback_probability)


def calculate_grammar_quality_score(
    error_count: int | float | None = None,
    transcript: str | None = None,
    *,
    error_probability: float | int | None = None,
    fallback_score: float | int | None = None,
) -> float:
    if transcript and count_words(transcript) > 0:
        probability = calculate_grammar_error_probability(
            error_count,
            transcript,
            fallback_probability=error_probability,
        )
        return round(1.0 - probability, 3)

    if error_probability is not None:
        return round(1.0 - _clamp_probability(error_probability), 3)

    return round(_clamp_probability(fallback_score), 3)


def calculate_overall_score(
    dysarthria_probability: float | int | None,
    stuttering_probability: float | int | None,
    grammar_score: float | int | None,
) -> int:
    dysarthria = _clamp_probability(dysarthria_probability)
    stuttering = _clamp_probability(stuttering_probability)
    grammar = calculate_grammar_quality_score(fallback_score=grammar_score)
    pronunciation = (1 - dysarthria) * 100
    fluency = (1 - stuttering) * 100
    clarity = grammar * 100
    weighted_average = (pronunciation * 0.35) + (fluency * 0.25) + (clarity * 0.4)
    weakest_skill = min(pronunciation, fluency, clarity)
    overall_score = (weighted_average * 0.7) + (weakest_skill * 0.3)
    return round(max(0.0, min(100.0, overall_score)))


def percent_display(value: float | int | None) -> int:
    return round(_clamp_probability(value) * 100)
