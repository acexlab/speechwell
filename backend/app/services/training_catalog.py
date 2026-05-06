"""
File Logic Summary: Static catalog of guided training modules and exercises used
by the Therapy Hub MVP. This keeps training content lightweight and avoids
requiring database-managed exercise authoring.
"""

from __future__ import annotations

from typing import Any


TRAINING_MODULES: list[dict[str, Any]] = [
    {
        "key": "breath_voice",
        "title": "Breath & Voice Control",
        "description": "Build steadier airflow, sustained sounds, and controlled voice release.",
        "focus_area": "Clarity and voice stability",
        "exercises": [
            {
                "key": "vowel_hold",
                "title": "Vowel Hold",
                "description": "Hold a long vowel steadily for a calm, supported voice.",
                "input_mode": "mic",
                "difficulty": "Easy",
                "prompt_text": "Take one calm breath and hold 'aaa' for as long and as steadily as you can.",
                "expected_text": "aaa",
            },
            {
                "key": "count_on_breath",
                "title": "Count On One Breath",
                "description": "Count smoothly from one to five using one breath.",
                "input_mode": "mic",
                "difficulty": "Easy",
                "prompt_text": "Count from one to five on one steady breath.",
                "expected_text": "one two three four five",
            },
            {
                "key": "soft_loud_repeat",
                "title": "Soft To Strong",
                "description": "Say the same phrase gently, then clearly with more voice energy.",
                "input_mode": "mic",
                "difficulty": "Medium",
                "prompt_text": "Say: good morning. First softly, then clearly and confidently.",
                "expected_text": "good morning",
            },
        ],
    },
    {
        "key": "articulation",
        "title": "Articulation Practice",
        "description": "Target clearer consonants and more precise word production.",
        "focus_area": "Speech clarity",
        "exercises": [
            {
                "key": "minimal_pairs",
                "title": "Minimal Pairs",
                "description": "Practice pairs that differ by one sound.",
                "input_mode": "mic",
                "difficulty": "Medium",
                "prompt_text": "Say clearly: pat, bat, pat, bat.",
                "expected_text": "pat bat pat bat",
            },
            {
                "key": "tongue_tip_drill",
                "title": "Tongue Tip Drill",
                "description": "Repeat crisp tongue-tip sounds for t, d, n, and l.",
                "input_mode": "mic",
                "difficulty": "Medium",
                "prompt_text": "Say: tea, day, no, light.",
                "expected_text": "tea day no light",
            },
            {
                "key": "sentence_repeat_clear",
                "title": "Clear Sentence Repeat",
                "description": "Repeat a short sentence slowly and clearly.",
                "input_mode": "mic",
                "difficulty": "Easy",
                "prompt_text": "Repeat: Today I will speak slowly and clearly.",
                "expected_text": "today i will speak slowly and clearly",
            },
        ],
    },
    {
        "key": "fluency",
        "title": "Fluency Training",
        "description": "Reduce rush, manage pauses, and practice smoother speech starts.",
        "focus_area": "Pacing and smooth speech",
        "exercises": [
            {
                "key": "slow_read",
                "title": "Slow Read",
                "description": "Read a short phrase slowly with smooth pacing.",
                "input_mode": "mic",
                "difficulty": "Easy",
                "prompt_text": "Read slowly: I can speak calmly one word at a time.",
                "expected_text": "i can speak calmly one word at a time",
            },
            {
                "key": "easy_onset_phrase",
                "title": "Easy Onset Phrase",
                "description": "Begin each phrase gently instead of pushing into the first sound.",
                "input_mode": "mic",
                "difficulty": "Medium",
                "prompt_text": "Say: I am ready. I feel calm. I can continue.",
                "expected_text": "i am ready i feel calm i can continue",
            },
            {
                "key": "pause_and_continue",
                "title": "Pause And Continue",
                "description": "Use planned pauses and then continue smoothly.",
                "input_mode": "mic",
                "difficulty": "Medium",
                "prompt_text": "Say: I took a breath, then I finished my sentence.",
                "expected_text": "i took a breath then i finished my sentence",
            },
        ],
    },
    {
        "key": "grammar",
        "title": "Sentence & Grammar Practice",
        "description": "Build confidence with complete spoken sentences and simple corrections.",
        "focus_area": "Sentence building",
        "exercises": [
            {
                "key": "complete_sentence",
                "title": "Complete The Sentence",
                "description": "Finish the idea using a full sentence.",
                "input_mode": "text",
                "difficulty": "Easy",
                "prompt_text": "Complete the sentence: Every morning, I...",
                "expected_text": "",
            },
            {
                "key": "fix_and_say",
                "title": "Fix And Say",
                "description": "Correct the sentence, then speak or type it clearly.",
                "input_mode": "text",
                "difficulty": "Medium",
                "prompt_text": "Correct this sentence: He go to school every day.",
                "expected_text": "he goes to school every day",
            },
            {
                "key": "daily_topic",
                "title": "Daily Topic",
                "description": "Speak or type two short sentences about your day.",
                "input_mode": "text",
                "difficulty": "Medium",
                "prompt_text": "Write or say two short sentences about what you did today.",
                "expected_text": "",
            },
        ],
    },
]


def list_modules() -> list[dict[str, Any]]:
    return TRAINING_MODULES


def get_module(module_key: str) -> dict[str, Any] | None:
    return next((module for module in TRAINING_MODULES if module["key"] == module_key), None)


def get_exercise(module_key: str, exercise_key: str) -> dict[str, Any] | None:
    module = get_module(module_key)
    if not module:
        return None
    return next((exercise for exercise in module["exercises"] if exercise["key"] == exercise_key), None)
