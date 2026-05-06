"""
File Logic Summary: Stuttering analysis module. It derives repetitions,
prolongations, and blocks from transcript/timing evidence, then combines the
event rates with pause and articulation irregularity into a conservative
real-world disfluency score.
"""

from __future__ import annotations

import re
from statistics import mean, pstdev

from ml.feature_extraction.raw_audio_features import extract_raw_audio_features


WORD_PATTERN = re.compile(r"[a-z0-9']+")
FRAGMENT_PATTERN = re.compile(r"\b([a-z])(?:[-\s]+)([a-z]{2,})")
STRETCHED_PATTERN = re.compile(r"([aeiou])\1{2,}")
BLOCK_THRESHOLD_SEC = 0.9
SEVERE_BLOCK_THRESHOLD_SEC = 1.5


def _normalized_tokens(transcript: str) -> list[str]:
    return WORD_PATTERN.findall((transcript or "").lower())


def _count_repetitions(transcript: str, segments: list[dict]) -> int:
    words = _normalized_tokens(transcript)
    repetitions = 0

    for index in range(1, len(words)):
        if words[index] == words[index - 1]:
            repetitions += 1
            continue
        if (
            len(words[index - 1]) == 1
            and len(words[index]) > 1
            and words[index].startswith(words[index - 1])
        ):
            repetitions += 1

    for seg in segments:
        seg_words = _normalized_tokens(seg.get("text", ""))
        for index in range(1, len(seg_words)):
            if seg_words[index] == seg_words[index - 1]:
                repetitions += 1

    return repetitions


def _count_prolongations(
    transcript: str,
    segments: list[dict],
    speaking_rate_wps: float,
    acoustic_features: dict | None,
) -> int:
    raw_text = (transcript or "").lower()

    stretched_text_events = len(STRETCHED_PATTERN.findall(raw_text))
    fragment_events = sum(
        1
        for fragment, word in FRAGMENT_PATTERN.findall(raw_text)
        if word.startswith(fragment)
    )

    slow_segment_events = 0
    for seg in segments:
        duration = float(seg.get("duration_sec") or 0.0)
        word_count = int(seg.get("word_count") or 0)
        if word_count <= 0 or duration <= 0:
            continue
        duration_per_word = duration / word_count
        if word_count <= 3 and duration_per_word >= 0.85:
            slow_segment_events += 1
        elif word_count == 1 and duration >= 1.1:
            slow_segment_events += 1

    acoustic_hint_events = 0
    if acoustic_features:
        zcr = float(acoustic_features.get("zcr") or 0.0)
        flatness = float(acoustic_features.get("flatness") or 0.0)
        if speaking_rate_wps > 0 and speaking_rate_wps < 1.45 and zcr < 0.045 and flatness < 0.12:
            acoustic_hint_events += 1

    return stretched_text_events + fragment_events + slow_segment_events + acoustic_hint_events


def _count_blocks(whisper_features: dict) -> tuple[int, int]:
    pause_durations = [float(pause) for pause in (whisper_features.get("pause_durations") or [])]
    if not pause_durations:
        segments = whisper_features.get("segments") or []
        previous_end = None
        for seg in segments:
            start = float(seg.get("start", 0.0))
            if previous_end is not None:
                gap = start - previous_end
                if gap > 0:
                    pause_durations.append(gap)
            previous_end = float(seg.get("end", 0.0))

    blocks = sum(1 for pause in pause_durations if pause >= BLOCK_THRESHOLD_SEC)
    severe_blocks = sum(1 for pause in pause_durations if pause >= SEVERE_BLOCK_THRESHOLD_SEC)
    return blocks, severe_blocks


def _pause_variability_score(pause_durations: list[float], total_duration_sec: float) -> float:
    if not pause_durations:
        return 0.0

    avg_pause = mean(pause_durations)
    pause_std = pstdev(pause_durations) if len(pause_durations) > 1 else 0.0
    long_pause_ratio = sum(1 for pause in pause_durations if pause >= BLOCK_THRESHOLD_SEC) / len(pause_durations)
    score = (
        min(avg_pause / 1.4, 1.0) * 0.35
        + min(pause_std / 0.9, 1.0) * 0.35
        + min(long_pause_ratio / 0.5, 1.0) * 0.3
    )

    if total_duration_sec < 2.0:
        score *= 0.7
    return min(score, 1.0)


def _segment_rate_variability_score(segments: list[dict]) -> float:
    rates = [
        float(seg.get("rate_wps") or 0.0)
        for seg in segments
        if float(seg.get("duration_sec") or 0.0) >= 0.2 and int(seg.get("word_count") or 0) > 0
    ]
    if len(rates) < 2:
        return 0.0

    avg_rate = mean(rates)
    if avg_rate <= 0:
        return 0.0
    coefficient_of_variation = pstdev(rates) / avg_rate
    return min(coefficient_of_variation / 0.85, 1.0)


def _speaking_rate_penalty(speaking_rate_wps: float) -> float:
    if speaking_rate_wps <= 0:
        return 0.0
    if 1.6 <= speaking_rate_wps <= 4.3:
        return 0.0
    distance = min(abs(speaking_rate_wps - 2.75), 2.5)
    return min(distance / 2.5, 1.0)


def _event_rate_score(event_count: int, total_words: int, expected_ratio: float) -> float:
    baseline = max(total_words * expected_ratio, 1.0)
    return min(event_count / baseline, 1.0)


def detect_stuttering(whisper_features: dict, audio_path: str | None = None) -> dict:
    transcript = whisper_features.get("transcript", "")
    segments = whisper_features.get("segments", [])
    pause_durations = [float(pause) for pause in (whisper_features.get("pause_durations") or [])]
    total_duration_sec = float(whisper_features.get("total_duration_sec") or 0.0)
    speaking_rate_wps = float(whisper_features.get("speaking_rate_wps") or 0.0)

    acoustic_features = None
    if audio_path:
        try:
            acoustic_features = extract_raw_audio_features(audio_path, target_frames=None)
        except Exception:
            acoustic_features = None

    tokens = _normalized_tokens(transcript)
    total_words = max(int(whisper_features.get("total_words") or len(tokens)), len(tokens))
    repetitions = _count_repetitions(transcript, segments)
    prolongations = _count_prolongations(transcript, segments, speaking_rate_wps, acoustic_features)
    blocks, severe_blocks = _count_blocks(whisper_features)

    repetition_score = _event_rate_score(repetitions, total_words, expected_ratio=0.14)
    prolongation_score = _event_rate_score(prolongations, total_words, expected_ratio=0.12)
    block_rate_per_min = blocks / max(total_duration_sec / 60.0, 0.25)
    block_score = min(block_rate_per_min / 4.0, 1.0)
    severe_block_bonus = min(severe_blocks / max(total_words * 0.06, 1.0), 1.0)
    pause_variability = _pause_variability_score(pause_durations, total_duration_sec)
    segment_rate_variability = _segment_rate_variability_score(segments)
    speaking_rate_penalty = _speaking_rate_penalty(speaking_rate_wps)

    score = (
        repetition_score * 0.28
        + prolongation_score * 0.24
        + block_score * 0.26
        + severe_block_bonus * 0.08
        + pause_variability * 0.09
        + segment_rate_variability * 0.03
        + speaking_rate_penalty * 0.02
    )

    if total_words < 4 and blocks == 0 and prolongations <= 1:
        score *= 0.7
    if total_duration_sec < 1.5:
        score *= 0.65

    stuttering_probability = round(max(0.0, min(score, 1.0)), 3)
    return {
        "stuttering_probability": stuttering_probability,
        "repetitions": repetitions,
        "prolongations": prolongations,
        "blocks": blocks,
        "fluency_score": round((1.0 - stuttering_probability) * 100),
        "disfluency_events": repetitions + prolongations + blocks,
    }
