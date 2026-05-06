"""
File Logic Summary: Lightweight training evaluation service. It compares
expected and spoken text, counts repeated words, derives pause-based fluency
from Whisper timing features, and produces short practical feedback.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend.app.database.models import TrainingProgress, TrainingSession
from backend.app.services.grammar_service import improve_training_response
from ml.feature_extraction.extract_whisper import analyze_audio_features


LONG_PAUSE_THRESHOLD_SEC = 1.2
OPEN_RESPONSE_TARGET_WORDS = 6


def normalize_text(text: str | None) -> str:
    lowered = (text or "").lower()
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def split_words(text: str | None) -> list[str]:
    normalized = normalize_text(text)
    return [word for word in normalized.split(" ") if word]


def calculate_accuracy(expected_text: str | None, spoken_text: str | None) -> tuple[float, list[str]]:
    expected_words = split_words(expected_text)
    spoken_words = split_words(spoken_text)
    if not expected_words:
        if spoken_words:
            return 1.0, []
        return 0.0, []

    matched_words = 0
    missed_words: list[str] = []
    for index, expected_word in enumerate(expected_words):
        if index < len(spoken_words) and spoken_words[index] == expected_word:
            matched_words += 1
        else:
            missed_words.append(expected_word)

    return matched_words / len(expected_words), missed_words[:5]


def calculate_open_response_score(spoken_text: str | None) -> float:
    word_count = len(split_words(spoken_text))
    if word_count <= 0:
        return 0.0
    return min(word_count / OPEN_RESPONSE_TARGET_WORDS, 1.0)


def count_repeated_words(text: str | None) -> int:
    words = split_words(text)
    repeats = 0
    for index in range(1, len(words)):
        if words[index] == words[index - 1]:
            repeats += 1
        elif index > 1 and words[index] == words[index - 2]:
            repeats += 1
    return repeats


def count_long_pauses(segments: list[dict[str, Any]]) -> int:
    long_pauses = 0
    previous_end = None
    for segment in segments:
        start = float(segment.get("start", 0.0))
        end = float(segment.get("end", 0.0))
        if previous_end is not None and start - previous_end >= LONG_PAUSE_THRESHOLD_SEC:
            long_pauses += 1
        previous_end = end
    return long_pauses


def infer_simple_correction(text: str | None) -> str:
    content = " ".join((text or "").split()).strip()
    if not content:
        return ""
    capitalized = content[0].upper() + content[1:] if content else ""
    if capitalized[-1] not in ".!?":
        capitalized += "."
    return capitalized


def _module_specific_feedback(
    module_key: str,
    exercise_key: str,
    accuracy_score: int,
    fluency_score: int,
    repeated_word_count: int,
    long_pause_count: int,
    missed_words: list[str],
    corrected_text: str | None = None,
) -> list[str]:
    feedback: list[str] = []

    if module_key == "breath_voice":
        if exercise_key == "vowel_hold":
            if fluency_score >= 85:
                feedback.append("Your vowel release sounded steady. Keep the sound smooth from start to finish.")
            else:
                feedback.append("Focus on one calm breath and keep the vowel steady instead of restarting the sound.")
        elif exercise_key == "count_on_breath":
            if long_pause_count == 0:
                feedback.append("Good breath support. You kept the count moving without extra pauses.")
            else:
                feedback.append("Try a slightly deeper breath so you can finish the count without breaking.")
        else:
            feedback.append("Aim for a soft start first, then add stronger voice energy without rushing.")

    elif module_key == "articulation":
        if accuracy_score >= 85:
            feedback.append("Your word shapes were clear. Keep the mouth movement deliberate and crisp.")
        elif missed_words:
            feedback.append(f"Repeat these words more clearly: {', '.join(missed_words[:3])}.")
        else:
            feedback.append("Slow down and exaggerate the target consonants to improve clarity.")

        if exercise_key == "tongue_tip_drill":
            feedback.append("For t, d, n, and l, lift the tongue tip cleanly and release each sound fully.")
        elif exercise_key == "minimal_pairs":
            feedback.append("Make the contrast between each pair stronger so the listener can hear the change immediately.")

    elif module_key == "fluency":
        if long_pause_count >= 2:
            feedback.append("Your pacing broke in a few places. Use shorter phrases and planned breaths.")
        elif repeated_word_count >= 2:
            feedback.append("Repeated starts were detected. Begin each phrase gently instead of pushing the first word.")
        else:
            feedback.append("Nice pacing. Your speech stayed smooth through most of the exercise.")

        if exercise_key == "easy_onset_phrase":
            feedback.append("Try easing into the first sound of each phrase instead of starting hard.")
        elif exercise_key == "pause_and_continue":
            feedback.append("Pause only at natural breaks, then continue without restarting the sentence.")

    elif module_key == "grammar":
        if exercise_key == "complete_sentence":
            if accuracy_score >= 85:
                feedback.append("You completed the idea clearly. Keep using full sentences with a clear ending.")
            else:
                feedback.append("Try turning the phrase into one complete sentence with a subject and action.")
        elif exercise_key == "fix_and_say":
            feedback.append("Compare your answer with the corrected version and notice the verb change.")
        else:
            feedback.append("Add one more detail so your response sounds complete and natural.")

        if corrected_text:
            feedback.append("Use the improved sentence below as your model for the next attempt.")

    return feedback


def build_feedback(
    module_key: str,
    exercise_key: str,
    accuracy_score: int,
    fluency_score: int,
    repeated_word_count: int,
    long_pause_count: int,
    missed_words: list[str],
    corrected_text: str | None = None,
) -> list[str]:
    feedback: list[str] = []

    feedback.extend(
        _module_specific_feedback(
            module_key,
            exercise_key,
            accuracy_score,
            fluency_score,
            repeated_word_count,
            long_pause_count,
            missed_words,
            corrected_text,
        )
    )

    if module_key != "grammar":
        if accuracy_score >= 85:
            feedback.append("Most target words matched the prompt.")
        elif accuracy_score >= 60:
            feedback.append("You are close. Slow down slightly to improve word matching.")
        else:
            feedback.append("Repeat the prompt more carefully and aim for a clearer match.")

    if module_key in {"breath_voice", "fluency"} and long_pause_count >= 2:
        feedback.append("Several long pauses were detected. Try shorter breaths and smoother pacing.")

    if module_key in {"fluency", "articulation"} and repeated_word_count >= 2:
        feedback.append("Repeated words were detected. Reset your breath and start the phrase gently.")

    if not feedback:
        feedback.append("Strong attempt. Move to the next exercise when ready.")

    return feedback[:4]


def evaluate_text_attempt(
    module_key: str,
    exercise_key: str,
    expected_text: str | None,
    transcript: str | None,
    prompt_text: str | None = None,
) -> dict[str, Any]:
    normalized_transcript = (transcript or "").strip()
    if not split_words(normalized_transcript):
        return {
            "is_valid": False,
            "transcript": "",
            "accuracy_score": 0,
            "fluency_score": 0,
            "confidence_score": 0,
            "long_pause_count": 0,
            "repeated_word_count": 0,
            "duration_sec": 0.0,
            "corrected_text": "",
            "feedback": ["No response detected. Please type or say your answer before submitting."],
        }

    if split_words(expected_text):
        accuracy_ratio, missed_words = calculate_accuracy(expected_text, normalized_transcript)
    else:
        accuracy_ratio = calculate_open_response_score(normalized_transcript)
        missed_words = []

    repeated_word_count = count_repeated_words(normalized_transcript)
    long_pause_count = 0
    fluency_ratio = max(0.0, min(1.0, 1.0 - (repeated_word_count * 0.1)))
    completion_bonus = 1.0 if split_words(normalized_transcript) else 0.0
    confidence_ratio = min(1.0, (accuracy_ratio * 0.5) + (fluency_ratio * 0.3) + (completion_bonus * 0.2))

    grammar_result = improve_training_response(prompt_text or "", normalized_transcript)

    accuracy_score = round(accuracy_ratio * 100)
    fluency_score = round(fluency_ratio * 100)
    grammar_boost = max(0.0, 1.0 - float(grammar_result.get("grammar_error_probability") or 0.0))
    confidence_score = round(min(1.0, confidence_ratio * 0.8 + grammar_boost * 0.2) * 100)
    feedback = build_feedback(
        module_key,
        exercise_key,
        accuracy_score,
        fluency_score,
        repeated_word_count,
        long_pause_count,
        missed_words,
        grammar_result.get("corrected_text"),
    )

    return {
        "is_valid": True,
        "transcript": normalized_transcript,
        "accuracy_score": accuracy_score,
        "fluency_score": fluency_score,
        "confidence_score": confidence_score,
        "long_pause_count": long_pause_count,
        "repeated_word_count": repeated_word_count,
        "duration_sec": 0.0,
        "corrected_text": grammar_result.get("corrected_text") or infer_simple_correction(normalized_transcript),
        "feedback": feedback + (
            ["Improved version generated from the local grammar model."]
            if grammar_result.get("corrected_text")
            and grammar_result.get("corrected_text") != normalized_transcript
            else []
        ),
    }
def evaluate_audio_attempt(
    module_key: str,
    exercise_key: str,
    audio_path: str,
    expected_text: str | None,
) -> dict[str, Any]:
    features = analyze_audio_features(audio_path)
    transcript = (features.get("transcript") or "").strip()
    segments = features.get("segments") or []
    duration_sec = round(float(features.get("total_duration_sec") or 0.0), 2)
    if not split_words(transcript):
        return {
            "is_valid": False,
            "transcript": "",
            "accuracy_score": 0,
            "fluency_score": 0,
            "confidence_score": 0,
            "long_pause_count": 0,
            "repeated_word_count": 0,
            "duration_sec": duration_sec,
            "corrected_text": "",
            "feedback": ["No speech was detected in the recording. Please record again and speak clearly into the microphone."],
        }

    accuracy_ratio, missed_words = calculate_accuracy(expected_text, transcript)
    repeated_word_count = count_repeated_words(transcript)
    long_pause_count = count_long_pauses(segments)

    fluency_ratio = 1.0
    fluency_ratio -= long_pause_count * 0.15
    fluency_ratio -= repeated_word_count * 0.1
    fluency_ratio = max(0.0, min(1.0, fluency_ratio))

    completion_bonus = 1.0 if transcript else 0.0
    confidence_ratio = min(1.0, (accuracy_ratio * 0.5) + (fluency_ratio * 0.3) + (completion_bonus * 0.2))

    accuracy_score = round(accuracy_ratio * 100)
    fluency_score = round(fluency_ratio * 100)
    confidence_score = round(confidence_ratio * 100)
    feedback = build_feedback(
        module_key,
        exercise_key,
        accuracy_score,
        fluency_score,
        repeated_word_count,
        long_pause_count,
        missed_words,
        None,
    )

    return {
        "is_valid": True,
        "transcript": transcript,
        "accuracy_score": accuracy_score,
        "fluency_score": fluency_score,
        "confidence_score": confidence_score,
        "long_pause_count": long_pause_count,
        "repeated_word_count": repeated_word_count,
        "duration_sec": duration_sec,
        "corrected_text": infer_simple_correction(transcript),
        "feedback": feedback,
    }


def sync_progress(db: Session, training_session: TrainingSession) -> TrainingProgress:
    module_sessions = (
        db.query(TrainingSession)
        .filter(
            TrainingSession.user_id == training_session.user_id,
            TrainingSession.module_key == training_session.module_key,
            TrainingSession.status == "completed",
        )
        .all()
    )

    sessions_completed = len(module_sessions)
    avg_accuracy = (
        sum(float(session.accuracy_score or 0.0) for session in module_sessions) / sessions_completed
        if sessions_completed
        else 0.0
    )
    avg_fluency = (
        sum(float(session.fluency_score or 0.0) for session in module_sessions) / sessions_completed
        if sessions_completed
        else 0.0
    )
    best_score = (
        max(float(session.confidence_score or 0.0) for session in module_sessions)
        if sessions_completed
        else 0.0
    )

    progress = (
        db.query(TrainingProgress)
        .filter(
            TrainingProgress.user_id == training_session.user_id,
            TrainingProgress.module_key == training_session.module_key,
        )
        .first()
    )

    if progress is None:
        progress = TrainingProgress(
            user_id=training_session.user_id,
            module_key=training_session.module_key,
        )
        db.add(progress)

    progress.sessions_completed = sessions_completed
    progress.avg_accuracy = round(avg_accuracy, 2)
    progress.avg_fluency = round(avg_fluency, 2)
    progress.best_score = round(best_score, 2)
    progress.last_practiced_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(progress)
    return progress
