import json
import os

def load_whisper_features(audio_id):
    path = f"storage/results/whisper/{audio_id}.json"
    with open(path) as f:
        return json.load(f)

def load_acoustic_embeddings(audio_id):
    path = f"storage/results/acoustic/{audio_id}.json"
    with open(path) as f:
        return json.load(f)
