import torch
import soundfile as sf
import librosa
from transformers import Wav2Vec2Model, Wav2Vec2Processor
import os
import json

# Load model + processor ONCE
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base")
model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base")
model.eval()


def analyze_acoustic(audio_id: str):
    """
    Extracts acoustic embedding from processed audio
    and saves it as JSON.
    """

    audio_path = f"storage/processed_audio/{audio_id}.wav"

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Processed audio not found: {audio_path}")

    # Load audio
    waveform, sample_rate = sf.read(audio_path)

    # Convert to mono
    if waveform.ndim > 1:
        waveform = waveform.mean(axis=1)

    # Resample to 16kHz
    if sample_rate != 16000:
        waveform = librosa.resample(
            waveform,
            orig_sr=sample_rate,
            target_sr=16000
        )
        sample_rate = 16000

    # Prepare input
    inputs = processor(
        waveform,
        sampling_rate=sample_rate,
        return_tensors="pt",
        padding=True
    )

    with torch.no_grad():
        outputs = model(**inputs)

    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().tolist()

    os.makedirs("storage/results/acoustic", exist_ok=True)

    with open(f"storage/results/acoustic/{audio_id}.json", "w") as f:
        json.dump([embedding], f)

    return embedding

