import numpy as np

def classify_speech(whisper_features, acoustic_embeddings):
    # Aggregate acoustic info
    embedding_matrix = np.array(acoustic_embeddings)
    embedding_variance = float(np.var(embedding_matrix))

    avg_speaking_rate = np.mean([
        f["speaking_rate_wps"] for f in whisper_features
    ])
    avg_pause = np.mean([
        f["average_pause_sec"] for f in whisper_features
    ])
    max_pause = max([
        f["max_pause_sec"] for f in whisper_features
    ])

    # Initialize probabilities
    stuttering = 0.0
    dysarthria = 0.0
    phonological = 0.0

    # Stuttering logic
    if max_pause > 1.5:
        stuttering += 0.4
    if avg_speaking_rate < 2.5:
        stuttering += 0.4
    stuttering = min(stuttering, 1.0)

    # Dysarthria logic
    if embedding_variance > 0.5:
        dysarthria = 0.7

    # Phonological logic
    if avg_pause < 0.7 and embedding_variance > 0.3:
        phonological = 0.6

    # Healthy score
    healthy = max(0.0, 1 - max(stuttering, dysarthria, phonological))

    return {
        "healthy": round(healthy, 2),
        "stuttering": round(stuttering, 2),
        "dysarthria": round(dysarthria, 2),
        "phonological": round(phonological, 2),
        "apraxia": 0.1  # placeholder for future model
    }