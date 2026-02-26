"""
File Logic Summary: Multi-provider chat integration service supporting local
Ollama, OpenAI, and Gemini with graceful fallback.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

import requests


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
OPENAI_API_BASE = "https://api.openai.com/v1/chat/completions"
OLLAMA_API_BASE_DEFAULT = "http://127.0.0.1:11434"
SYSTEM_PROMPT = (
    "You are SpeechWell AI coach. You must only discuss SpeechWell-related topics: "
    "speech analysis, fluency, stuttering, pronunciation, articulation, pacing, breathing, "
    "confidence, transcript feedback, grammar issues, and report interpretation. "
    "If asked about anything outside SpeechWell speech coaching, refuse briefly and redirect "
    "to a SpeechWell-related next step. Keep guidance practical, empathetic, and concise. "
    "Reply in plain text with a maximum of 6 sentences."
)


def _read_env_value(key: str) -> str | None:
    # Fallback parser so chat works even when python-dotenv isn't installed.
    root = Path(__file__).resolve().parents[3]
    candidates = [root / ".env", root / "backend" / ".env"]
    for env_path in candidates:
        if not env_path.exists():
            continue
        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                if name.strip() != key:
                    continue
                cleaned = value.strip().strip('"').strip("'")
                if cleaned:
                    return cleaned
        except Exception:
            continue
    return None


def _to_gemini_role(role: str) -> str:
    return "model" if role == "assistant" else "user"


def _format_analysis_context(analysis_context: dict | None) -> str | None:
    if not analysis_context:
        return None

    lines = [
        "Use this SpeechWell analysis context for personalization when relevant:",
        f"- audio_id: {analysis_context.get('audio_id') or 'n/a'}",
        f"- filename: {analysis_context.get('filename') or 'n/a'}",
        f"- dysarthria_probability: {analysis_context.get('dysarthria_probability', 0)}",
        f"- dysarthria_label: {analysis_context.get('dysarthria_label') or 'n/a'}",
        f"- stuttering_probability: {analysis_context.get('stuttering_probability', 0)}",
        f"- stuttering_repetitions: {analysis_context.get('stuttering_repetitions', 0)}",
        f"- stuttering_prolongations: {analysis_context.get('stuttering_prolongations', 0)}",
        f"- stuttering_blocks: {analysis_context.get('stuttering_blocks', 0)}",
        f"- grammar_error_probability: {analysis_context.get('grammar_score', 0)}",
        f"- grammar_error_count: {analysis_context.get('grammar_error_count', 0)}",
        f"- phonological_error_probability: {analysis_context.get('phonological_score', 0)}",
        f"- speaking_rate_wps: {analysis_context.get('speaking_rate_wps', 0)}",
        f"- average_pause_sec: {analysis_context.get('average_pause_sec', 0)}",
        f"- max_pause_sec: {analysis_context.get('max_pause_sec', 0)}",
    ]
    transcript = (analysis_context.get("transcript") or "").strip()
    corrected_text = (analysis_context.get("corrected_text") or "").strip()
    if transcript:
        lines.append(f"- transcript_excerpt: {transcript[:500]}")
    if corrected_text:
        lines.append(f"- corrected_text_excerpt: {corrected_text[:500]}")
    return "\n".join(lines)


def _build_contents(
    history: Iterable[dict], user_message: str, analysis_context_text: str | None
) -> list[dict]:
    contents: list[dict] = [
        {
            "role": "user",
            "parts": [{"text": SYSTEM_PROMPT}],
        }
    ]
    if analysis_context_text:
        contents.append(
            {
                "role": "user",
                "parts": [{"text": analysis_context_text}],
            }
        )

    for item in history:
        text = (item.get("text") or "").strip()
        role = item.get("role") or "user"
        if not text:
            continue
        contents.append({"role": _to_gemini_role(role), "parts": [{"text": text}]})

    contents.append({"role": "user", "parts": [{"text": user_message.strip()}]})
    return contents


def _build_openai_messages(
    history: Iterable[dict], user_message: str, analysis_context_text: str | None
) -> list[dict]:
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if analysis_context_text:
        messages.append({"role": "system", "content": analysis_context_text})
    for item in history:
        text = (item.get("text") or "").strip()
        role = item.get("role") or "user"
        if not text:
            continue
        messages.append({"role": "assistant" if role == "assistant" else "user", "content": text})
    messages.append({"role": "user", "content": user_message.strip()})
    return messages


def _build_chat_messages(
    history: Iterable[dict], user_message: str, analysis_context_text: str | None
) -> list[dict]:
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if analysis_context_text:
        messages.append({"role": "system", "content": analysis_context_text})
    for item in history:
        text = (item.get("text") or "").strip()
        role = item.get("role") or "user"
        if not text:
            continue
        messages.append({"role": "assistant" if role == "assistant" else "user", "content": text})
    messages.append({"role": "user", "content": user_message.strip()})
    return messages


def _local_coach_fallback(user_message: str) -> str:
    text = (user_message or "").lower()
    if any(k in text for k in ["stutter", "stuttering", "fluency"]):
        return (
            "The AI provider is currently unavailable, so here is a quick fluency drill: "
            "take a slow breath, speak one short sentence at 80% speed, pause for 1 second, "
            "and repeat for 5 rounds. Focus on smooth starts and gentle pacing."
        )
    if any(k in text for k in ["clarity", "pronunciation", "articulation"]):
        return (
            "The AI provider is currently unavailable, so here is a clarity drill: "
            "practice vowel elongation (aa, ee, oo) for 2 minutes, then read 5 lines aloud "
            "with clear mouth opening and controlled volume."
        )
    if any(k in text for k in ["breath", "breathing", "pace"]):
        return (
            "The AI provider is currently unavailable, so try this breathing/pace routine: "
            "inhale for 4 counts, exhale for 6 counts, then speak one phrase per exhale. "
            "Do this for 3 minutes to stabilize rhythm and reduce rushing."
        )
    return (
        "The AI provider is currently unavailable. For now, do a 5-minute routine: "
        "1 minute breathing control, 2 minutes slow reading with pauses, "
        "and 2 minutes replay-and-correct practice using your last analysis transcript."
    )


def _limit_to_max_sentences(text: str, max_sentences: int = 6) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return "I could not generate a response right now. Please try again."

    # Split on sentence boundaries and keep only the first N sentences.
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences = [p.strip() for p in parts if p and p.strip()]
    if not sentences:
        return cleaned

    limited = " ".join(sentences[:max_sentences]).strip()
    return limited or cleaned


def _is_obviously_off_topic(user_message: str) -> bool:
    text = (user_message or "").lower()
    off_topic_markers = {
        "stock", "crypto", "bitcoin", "ethereum", "politics", "election",
        "football", "soccer", "nba", "recipe", "cooking", "movie", "series",
        "travel", "hotel", "visa", "weather", "code", "programming", "debug",
        "leetcode", "sql", "javascript", "python", "gaming",
    }
    return any(token in text for token in off_topic_markers)


def _off_topic_reply() -> str:
    return (
        "I can only help with SpeechWell-related speech coaching and report interpretation. "
        "Ask about your fluency, stuttering, grammar issues, pronunciation, pacing, breathing, "
        "or how to improve based on your latest SpeechWell analysis."
    )


def _parse_openai_reply(data: dict) -> str:
    choices = data.get("choices") or []
    if not choices:
        return "I could not generate a response right now. Please try again."
    message = (choices[0] or {}).get("message") or {}
    content = (message.get("content") or "").strip()
    parsed = content or "I could not generate a response right now. Please try again."
    return _limit_to_max_sentences(parsed)


def _parse_ollama_reply(data: dict) -> str:
    message = data.get("message") or {}
    content = (message.get("content") or "").strip()
    if content:
        return _limit_to_max_sentences(content)
    fallback = (data.get("response") or "").strip()
    parsed = fallback or "I could not generate a response right now. Please try again."
    return _limit_to_max_sentences(parsed)


def _call_openai(
    api_key: str, user_message: str, history: list[dict], analysis_context_text: str | None
) -> tuple[str | None, str | None]:
    model = os.getenv("OPENAI_MODEL") or _read_env_value("OPENAI_MODEL") or "gpt-4o-mini"
    payload = {
        "model": model,
        "messages": _build_openai_messages(history, user_message, analysis_context_text),
        "temperature": 0.7,
        "max_tokens": 512,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(OPENAI_API_BASE, json=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        return None, f"Network error while calling OpenAI: {exc}"

    if response.ok:
        return _parse_openai_reply(response.json()), None

    provider_msg = response.text
    try:
        provider_json = response.json()
        provider_msg = (provider_json.get("error") or {}).get("message") or provider_msg
    except Exception:
        pass
    return None, f"OpenAI API error {response.status_code} on model '{model}': {provider_msg}"


def _call_ollama(
    base_url: str,
    model: str,
    user_message: str,
    history: list[dict],
    analysis_context_text: str | None,
) -> tuple[str | None, str | None]:
    url = f"{base_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": _build_chat_messages(history, user_message, analysis_context_text),
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 512,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
    except requests.RequestException as exc:
        return None, f"Network error while calling Ollama: {exc}"

    if response.ok:
        return _parse_ollama_reply(response.json()), None

    provider_msg = response.text
    try:
        provider_json = response.json()
        provider_msg = provider_json.get("error") or provider_msg
    except Exception:
        pass

    return None, f"Ollama API error {response.status_code} on model '{model}': {provider_msg}"


def _parse_gemini_reply(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return "I could not generate a response right now. Please try again."
    parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
    text_chunks = [p.get("text", "") for p in parts if isinstance(p, dict)]
    reply = " ".join(chunk.strip() for chunk in text_chunks if chunk and chunk.strip()).strip()
    parsed = reply or "I could not generate a response right now. Please try again."
    return _limit_to_max_sentences(parsed)


def _call_gemini(
    api_key: str, user_message: str, history: list[dict], analysis_context_text: str | None
) -> tuple[str | None, str | None]:
    model_name = os.getenv("GEMINI_MODEL") or _read_env_value("GEMINI_MODEL") or "gemini-1.5-flash"
    payload = {
        "contents": _build_contents(history, user_message, analysis_context_text),
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 512,
        },
    }

    model_candidates = [model_name, "gemini-2.0-flash", "gemini-1.5-flash"]
    last_error = "Unknown Gemini API error"
    for model in model_candidates:
        url = f"{GEMINI_API_BASE}/{model}:generateContent?key={api_key}"
        try:
            response = requests.post(url, json=payload, timeout=30)
        except requests.RequestException as exc:
            last_error = f"Network error while calling Gemini: {exc}"
            continue

        if response.ok:
            return _parse_gemini_reply(response.json()), None

        provider_msg = response.text
        try:
            provider_json = response.json()
            provider_msg = (provider_json.get("error") or {}).get("message") or provider_msg
        except Exception:
            pass

        last_error = f"Gemini API error {response.status_code} on model '{model}': {provider_msg}"

        if response.status_code not in (400, 404):
            break

    return None, last_error


def generate_chat_reply(
    user_message: str,
    history: list[dict] | None = None,
    analysis_context: dict | None = None,
) -> str:
    if not user_message or not user_message.strip():
        raise ValueError("Message cannot be empty")
    if _is_obviously_off_topic(user_message):
        return _off_topic_reply()

    history = history or []
    analysis_context_text = _format_analysis_context(analysis_context)
    chat_provider = (os.getenv("CHAT_PROVIDER") or _read_env_value("CHAT_PROVIDER") or "auto").lower()
    ollama_base = os.getenv("OLLAMA_BASE_URL") or _read_env_value("OLLAMA_BASE_URL") or OLLAMA_API_BASE_DEFAULT
    ollama_model = os.getenv("OLLAMA_MODEL") or _read_env_value("OLLAMA_MODEL") or "qwen2.5:30b"
    openai_key = os.getenv("OPENAI_API_KEY") or _read_env_value("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or _read_env_value("GEMINI_API_KEY")

    valid_providers = {"auto", "ollama", "openai", "gemini"}
    if chat_provider not in valid_providers:
        raise RuntimeError(
            "Invalid CHAT_PROVIDER. Use one of: auto, ollama, openai, gemini."
        )

    if chat_provider in {"auto", "ollama"}:
        reply, err = _call_ollama(
            ollama_base, ollama_model, user_message, history, analysis_context_text
        )
        if reply:
            return reply
        if chat_provider == "ollama":
            raise RuntimeError(err or "Ollama call failed")

    if chat_provider in {"auto", "openai"} and openai_key:
        reply, err = _call_openai(openai_key, user_message, history, analysis_context_text)
        if reply:
            return reply
        lowered = (err or "").lower()
        if "quota" in lowered or "429" in lowered or "rate limit" in lowered:
            return _local_coach_fallback(user_message)
        if chat_provider == "openai":
            raise RuntimeError(err or "OpenAI call failed")

    if chat_provider in {"auto", "gemini"} and gemini_key:
        reply, err = _call_gemini(gemini_key, user_message, history, analysis_context_text)
        if reply:
            return reply
        lowered = (err or "").lower()
        if "quota" in lowered or "429" in lowered or "rate limit" in lowered:
            return _local_coach_fallback(user_message)
        if chat_provider == "gemini":
            raise RuntimeError(err or "Gemini call failed")

    if chat_provider == "openai":
        raise RuntimeError("OpenAI provider selected but OPENAI_API_KEY is not configured.")
    if chat_provider == "gemini":
        raise RuntimeError("Gemini provider selected but GEMINI_API_KEY is not configured.")
    if chat_provider == "ollama":
        raise RuntimeError(
            "Ollama provider selected but request failed. Verify OLLAMA_BASE_URL and OLLAMA_MODEL."
        )

    raise RuntimeError(
        "No chat provider available. Start Ollama or configure OPENAI_API_KEY / GEMINI_API_KEY."
    )
