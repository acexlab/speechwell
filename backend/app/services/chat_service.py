"""
File Logic Summary: Multi-provider chat integration service. It supports OpenAI and Gemini keys, sends chat context, and returns assistant guidance with graceful fallback.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import requests


GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
OPENAI_API_BASE = "https://api.openai.com/v1/chat/completions"
SYSTEM_PROMPT = (
    "You are SpeechWell AI coach. Keep guidance practical, empathetic, and concise. "
    "Focus on speech training for fluency, clarity, pacing, breathing, and confidence."
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


def _build_contents(history: Iterable[dict], user_message: str) -> list[dict]:
    contents: list[dict] = [
        {
            "role": "user",
            "parts": [{"text": SYSTEM_PROMPT}],
        }
    ]

    for item in history:
        text = (item.get("text") or "").strip()
        role = item.get("role") or "user"
        if not text:
            continue
        contents.append({"role": _to_gemini_role(role), "parts": [{"text": text}]})

    contents.append({"role": "user", "parts": [{"text": user_message.strip()}]})
    return contents


def _build_openai_messages(history: Iterable[dict], user_message: str) -> list[dict]:
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
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


def _parse_openai_reply(data: dict) -> str:
    choices = data.get("choices") or []
    if not choices:
        return "I could not generate a response right now. Please try again."
    message = (choices[0] or {}).get("message") or {}
    content = (message.get("content") or "").strip()
    return content or "I could not generate a response right now. Please try again."


def _call_openai(api_key: str, user_message: str, history: list[dict]) -> tuple[str | None, str | None]:
    model = os.getenv("OPENAI_MODEL") or _read_env_value("OPENAI_MODEL") or "gpt-4o-mini"
    payload = {
        "model": model,
        "messages": _build_openai_messages(history, user_message),
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


def _parse_gemini_reply(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return "I could not generate a response right now. Please try again."
    parts = (((candidates[0] or {}).get("content") or {}).get("parts") or [])
    text_chunks = [p.get("text", "") for p in parts if isinstance(p, dict)]
    reply = " ".join(chunk.strip() for chunk in text_chunks if chunk and chunk.strip()).strip()
    return reply or "I could not generate a response right now. Please try again."


def _call_gemini(api_key: str, user_message: str, history: list[dict]) -> tuple[str | None, str | None]:
    model_name = os.getenv("GEMINI_MODEL") or _read_env_value("GEMINI_MODEL") or "gemini-1.5-flash"
    payload = {
        "contents": _build_contents(history, user_message),
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


def generate_chat_reply(user_message: str, history: list[dict] | None = None) -> str:
    if not user_message or not user_message.strip():
        raise ValueError("Message cannot be empty")

    history = history or []
    openai_key = os.getenv("OPENAI_API_KEY") or _read_env_value("OPENAI_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or _read_env_value("GEMINI_API_KEY")

    if openai_key:
        reply, err = _call_openai(openai_key, user_message, history)
        if reply:
            return reply
        lowered = (err or "").lower()
        if "quota" in lowered or "429" in lowered or "rate limit" in lowered:
            return _local_coach_fallback(user_message)
        if not gemini_key:
            raise RuntimeError(err or "OpenAI call failed")

    if gemini_key:
        reply, err = _call_gemini(gemini_key, user_message, history)
        if reply:
            return reply
        lowered = (err or "").lower()
        if "quota" in lowered or "429" in lowered or "rate limit" in lowered:
            return _local_coach_fallback(user_message)
        raise RuntimeError(err or "Gemini call failed")

    raise RuntimeError("No chat API key configured. Set OPENAI_API_KEY or GEMINI_API_KEY on backend.")