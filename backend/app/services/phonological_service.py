"""
File Logic Summary: Phonological analysis module. Algorithm applies rule-based phoneme substitution checks per word and computes a normalized phonological-error probability.
"""

PHONOLOGICAL_RULES = {
    "R": ["W"],
    "K": ["T"],
    "G": ["D"],
    "S": ["TH"],
    "TH": ["F", "D"],
    "L": ["W"]
}


def detect_phonological_errors(whisper_features: dict) -> dict:
    try:
        import pronouncing
    except Exception:
        return {
            "phonological_error_probability": 0.0,
            "error_count": 0,
            "affected_words": [],
        }

    transcript = whisper_features["transcript"].lower()
    words = transcript.split()

    error_count = 0
    affected_words = []

    for word in words:
        phones_list = pronouncing.phones_for_word(word)
        if not phones_list:
            continue

        expected_phones = phones_list[0].split()

        for phoneme, substitutions in PHONOLOGICAL_RULES.items():
            if phoneme in expected_phones:
                for sub in substitutions:
                    if sub in expected_phones:
                        error_count += 1
                        affected_words.append(word)
                        break

    probability = min(error_count / max(len(words), 1), 1.0)

    return {
        "phonological_error_probability": round(probability, 3),
        "error_count": error_count,
        "affected_words": list(set(affected_words))
    }

