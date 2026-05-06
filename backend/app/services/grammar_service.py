"""
File Logic Summary: Grammar analysis module. It uses a configured API provider
to correct transcript grammar and estimates grammar-error probability from the
word-level diff between original and corrected text.
"""

from __future__ import annotations

import difflib
import os
import re
from typing import Callable

import requests

from .chat_service import OLLAMA_API_BASE_DEFAULT, _read_env_value
from .score_service import calculate_grammar_quality_score


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
OPENAI_API_BASE = "https://api.openai.com/v1/chat/completions"
GRAMMAR_SYSTEM_PROMPT = (
    "You are a grammar correction engine for speech transcripts. "
    "Correct grammar, punctuation, casing, and obvious transcription issues "
    "without changing the meaning. Return only the corrected transcript."
)
GRAMMAR_TRAINING_SYSTEM_PROMPT = (
    "You are a SpeechWell grammar training assistant. "
    "You will receive an exercise prompt and the learner's answer. "
    "Rewrite the learner answer so it becomes grammatically correct, natural, "
    "and easy to understand without changing the core meaning. "
    "Return only the improved answer text."
)
COMMON_VERBS = {
    "am", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    "can", "could", "will", "would", "should", "may", "might", "must",
    "go", "goes", "went", "read", "reads", "look", "looks", "scored",
    "score", "say", "says", "said", "need", "needs", "needed",
}
COMMON_FILLERS = {
    "uh", "um", "er", "ah", "like", "you", "know", "hmm",
}
FUNCTION_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "than",
    "to", "for", "of", "in", "on", "at", "with", "from", "by",
    "is", "am", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "their", "our",
}
OBJECT_PRONOUNS = {"me", "him", "her", "us", "them"}


def _normalize_text(text: str) -> str:
    return " ".join((text or "").split()).strip()


def _tokenize_words(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9']+", (text or "").lower())


def _extract_corrected_text(raw_text: str, fallback: str) -> str:
    cleaned = (raw_text or "").strip().strip("`")
    for prefix in ("Corrected transcript:", "Corrected text:", "Corrected:"):
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
            break
    return _normalize_text(cleaned) or fallback


def _estimate_error_count(original: str, corrected: str) -> int:
    original_words = original.split()
    corrected_words = corrected.split()
    if not original_words:
        return 0
    matcher = difflib.SequenceMatcher(
        a=[word.lower() for word in original_words],
        b=[word.lower() for word in corrected_words],
    )
    changes = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            changes += max(i2 - i1, j2 - j1)
    return changes


def _has_likely_verb(words: list[str]) -> bool:
    for word in words:
        if word in COMMON_VERBS:
            return True
        if word.endswith(("ed", "ing")) and len(word) > 4:
            return True
    return False


def _estimate_structural_error_probability(transcript: str) -> float:
    words = _tokenize_words(transcript)
    if not words:
        return 1.0

    sentence_candidates = [fragment.strip() for fragment in re.split(r"[.!?]+", transcript) if fragment.strip()]
    if not sentence_candidates:
        sentence_candidates = [transcript.strip()]

    repeated_words = sum(1 for idx in range(1, len(words)) if words[idx] == words[idx - 1])
    filler_words = sum(1 for word in words if word in COMMON_FILLERS)
    function_words = sum(1 for word in words if word in FUNCTION_WORDS)
    odd_tokens = sum(
        1
        for word in words
        if any(ch.isdigit() for ch in word) or (len(word) == 1 and word not in {"a", "i"})
    )
    sentence_starts_lowercase = len(re.findall(r"[.!?]\s+[a-z]", transcript))
    missing_terminal_punctuation = 1 if transcript.strip() and transcript.strip()[-1] not in ".!?" else 0

    fragments = 0
    sentence_verb_gaps = 0
    for fragment in sentence_candidates:
        fragment_words = _tokenize_words(fragment)
        if len(fragment_words) <= 2:
            fragments += 1
            continue
        has_verb = _has_likely_verb(fragment_words)
        if len(fragment_words) <= 5 and not has_verb:
            fragments += 1
        elif not has_verb:
            sentence_verb_gaps += 1

    word_count = max(len(words), 1)
    sentence_count = max(len(sentence_candidates), 1)
    fragment_ratio = fragments / sentence_count
    verb_gap_ratio = sentence_verb_gaps / sentence_count
    repetition_ratio = repeated_words / word_count
    filler_ratio = filler_words / word_count
    function_word_ratio = function_words / word_count
    odd_token_ratio = odd_tokens / word_count
    boundary_issue_ratio = min(
        (sentence_starts_lowercase + missing_terminal_punctuation) / sentence_count,
        1.0,
    )
    telegraphic_ratio = 1.0 if word_count >= 6 and function_word_ratio < 0.22 else 0.0
    subject_case_ratio = 1.0 if len(words) >= 2 and words[0] in OBJECT_PRONOUNS and _has_likely_verb(words[1:3]) else 0.0

    structural_probability = min(
        fragment_ratio * 0.28
        + verb_gap_ratio * 0.16
        + repetition_ratio * 0.15
        + filler_ratio * 0.1
        + odd_token_ratio * 0.12
        + boundary_issue_ratio * 0.07
        + telegraphic_ratio * 0.07
        + subject_case_ratio * 0.05,
        1.0,
    )
    return round(structural_probability, 3)


def estimate_grammar_metrics(
    transcript: str,
    corrected_text: str | None = None,
    base_error_count: int | None = None,
) -> tuple[float, int, float]:
    normalized = _normalize_text(transcript)
    if not normalized:
        return 1.0, 0, 0.0

    original_words = _tokenize_words(normalized)
    word_count = max(len(original_words), 1)
    diff_error_count = 0
    if corrected_text:
        diff_error_count = _estimate_error_count(normalized, corrected_text)
    elif base_error_count is not None:
        diff_error_count = max(0, int(base_error_count))

    odd_token_count = sum(
        1
        for word in original_words
        if any(ch.isdigit() for ch in word) or (len(word) == 1 and word not in {"a", "i"})
    )
    filler_count = sum(1 for word in original_words if word in COMMON_FILLERS)
    artifact_ratio = min((odd_token_count + filler_count * 0.5) / word_count, 0.45)

    diff_probability = min(diff_error_count / word_count, 1.0)
    structural_probability = _estimate_structural_error_probability(normalized)
    trusted_diff_probability = diff_probability * (1.0 - artifact_ratio)
    blended_probability = structural_probability * 0.6 + trusted_diff_probability * 0.4
    probability = min(
        max(structural_probability, blended_probability),
        1.0,
    )
    structural_error_estimate = round(structural_probability * word_count)
    error_estimate = max(diff_error_count, structural_error_estimate, round(probability * word_count))
    quality_score = calculate_grammar_quality_score(
        error_count=error_estimate,
        transcript=normalized,
        error_probability=probability,
    )
    return round(probability, 3), error_estimate, quality_score


def _call_openai(api_key: str, transcript: str) -> tuple[str | None, str | None]:
    model = os.getenv("OPENAI_MODEL") or _read_env_value("OPENAI_MODEL") or "gpt-4o-mini"
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": 512,
        "messages": [
            {"role": "system", "content": GRAMMAR_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(OPENAI_API_BASE, json=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        return None, f"OpenAI grammar request failed: {exc}"
    if not response.ok:
        return None, f"OpenAI grammar request failed with status {response.status_code}"
    choices = response.json().get("choices") or []
    message = ((choices[0] or {}).get("message") or {}).get("content") if choices else ""
    return _extract_corrected_text(message or "", transcript), None


def _call_gemini(api_key: str, transcript: str) -> tuple[str | None, str | None]:
    model = os.getenv("GEMINI_MODEL") or _read_env_value("GEMINI_MODEL") or "gemini-1.5-flash"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": GRAMMAR_SYSTEM_PROMPT}]},
            {"role": "user", "parts": [{"text": transcript}]},
        ],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 512},
    }
    url = f"{GEMINI_API_BASE}/{model}:generateContent?key={api_key}"
    try:
        response = requests.post(url, json=payload, timeout=30)
    except requests.RequestException as exc:
        return None, f"Gemini grammar request failed: {exc}"
    if not response.ok:
        return None, f"Gemini grammar request failed with status {response.status_code}"
    candidates = response.json().get("candidates") or []
    parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
    text = " ".join((part.get("text") or "").strip() for part in parts if isinstance(part, dict))
    return _extract_corrected_text(text, transcript), None


def _call_ollama(_: str | None, transcript: str) -> tuple[str | None, str | None]:
    base_url = os.getenv("OLLAMA_BASE_URL") or _read_env_value("OLLAMA_BASE_URL") or OLLAMA_API_BASE_DEFAULT
    model = (
        os.getenv("GRAMMAR_OLLAMA_MODEL")
        or _read_env_value("GRAMMAR_OLLAMA_MODEL")
        or os.getenv("OLLAMA_MODEL")
        or _read_env_value("OLLAMA_MODEL")
        or "qwen2.5:30b"
    )
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": GRAMMAR_SYSTEM_PROMPT},
            {"role": "user", "content": transcript},
        ],
        "options": {"temperature": 0, "num_predict": 512},
    }
    try:
        response = requests.post(f"{base_url.rstrip('/')}/api/chat", json=payload, timeout=60)
    except requests.RequestException as exc:
        return None, f"Ollama grammar request failed: {exc}"
    if not response.ok:
        return None, f"Ollama grammar request failed with status {response.status_code}"
    data = response.json()
    text = ((data.get("message") or {}).get("content") or data.get("response") or "").strip()
    return _extract_corrected_text(text, transcript), None


def _call_ollama_training(prompt_text: str, user_response: str) -> tuple[str | None, str | None]:
    base_url = os.getenv("OLLAMA_BASE_URL") or _read_env_value("OLLAMA_BASE_URL") or OLLAMA_API_BASE_DEFAULT
    model = (
        os.getenv("GRAMMAR_OLLAMA_MODEL")
        or _read_env_value("GRAMMAR_OLLAMA_MODEL")
        or os.getenv("OLLAMA_MODEL")
        or _read_env_value("OLLAMA_MODEL")
        or "qwen2.5:30b"
    )
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": GRAMMAR_TRAINING_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Exercise prompt: {prompt_text}\nLearner answer: {user_response}",
            },
        ],
        "options": {"temperature": 0, "num_predict": 512},
    }
    try:
        response = requests.post(f"{base_url.rstrip('/')}/api/chat", json=payload, timeout=60)
    except requests.RequestException as exc:
        return None, f"Ollama grammar training request failed: {exc}"
    if not response.ok:
        return None, f"Ollama grammar training request failed with status {response.status_code}"
    data = response.json()
    text = ((data.get("message") or {}).get("content") or data.get("response") or "").strip()
    return _extract_corrected_text(text, user_response), None


def _correct_transcript_with_api(transcript: str) -> str:
    provider = (os.getenv("GRAMMAR_PROVIDER") or _read_env_value("GRAMMAR_PROVIDER") or "ollama").lower()
    if not provider:
        provider = (os.getenv("CHAT_PROVIDER") or _read_env_value("CHAT_PROVIDER") or "auto").lower()

    openai_key = os.getenv("OPENAI_API_KEY") or _read_env_value("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or _read_env_value("GEMINI_API_KEY")
    providers: list[tuple[str, Callable[[str | None, str], tuple[str | None, str | None]], str | None]] = []

    if provider in {"auto", "openai"} and openai_key:
        providers.append(("openai", _call_openai, openai_key))
    if provider in {"auto", "gemini"} and gemini_key:
        providers.append(("gemini", _call_gemini, gemini_key))
    if provider in {"auto", "ollama"}:
        providers.append(("ollama", _call_ollama, None))

    for _, handler, credential in providers:
        corrected, _ = handler(credential, transcript)
        if corrected:
            return corrected

    return transcript

def detect_grammar_errors(transcript: str) -> dict:
    transcript = _normalize_text(transcript)

    if not transcript.strip():
        return {
            "grammar_error_probability": 1.0,
            "grammar_quality_score": 0.0,
            "error_count_estimate": 0,
            "corrected_text": transcript
        }

    corrected = _correct_transcript_with_api(transcript)
    probability, error_estimate, quality_score = estimate_grammar_metrics(
        transcript,
        corrected_text=corrected,
    )

    return {
        "grammar_error_probability": round(probability, 3),
        "grammar_quality_score": quality_score,
        "error_count_estimate": error_estimate,
        "corrected_text": corrected,
    }


def improve_training_response(prompt_text: str, user_response: str) -> dict:
    original = _normalize_text(user_response)
    prompt = _normalize_text(prompt_text)

    if not original:
        return {
            "grammar_error_probability": 1.0,
            "grammar_quality_score": 0.0,
            "error_count_estimate": 0,
            "corrected_text": "",
        }

    corrected = None
    if prompt:
        corrected, _ = _call_ollama_training(prompt, original)
    if not corrected:
        corrected = _correct_transcript_with_api(original)

    probability, error_estimate, quality_score = estimate_grammar_metrics(
        original,
        corrected_text=corrected,
    )

    return {
        "grammar_error_probability": round(probability, 3),
        "grammar_quality_score": quality_score,
        "error_count_estimate": error_estimate,
        "corrected_text": corrected,
    }
