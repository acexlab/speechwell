from backend.app.services.classifier_service import classify_speech


def test_classifier_basic():
    whisper_features = [
        {
            "speaking_rate_wps": 2.0,
            "average_pause_sec": 0.8,
            "max_pause_sec": 2.0
        },
        {
            "speaking_rate_wps": 1.9,
            "average_pause_sec": 0.9,
            "max_pause_sec": 1.8
        }
    ]

    acoustic_embeddings = [
        [0.2] * 768,
        [0.4] * 768,
        [0.6] * 768
    ]

    result = classify_speech(whisper_features, acoustic_embeddings)

    print("\n=== CLASSIFIER OUTPUT ===")
    print(result)

    assert "stuttering" in result
    assert result["stuttering"] > 0.0


# 👇 THIS IS THE KEY LINE
if __name__ == "__main__":
    test_classifier_basic()
