"""
File Logic Summary: Extracts acoustic embeddings using Wav2Vec2. Algorithm converts waveform to mono/16kHz, runs model inference, and mean-pools hidden states into a fixed vector.
"""

processor = None
model = None
_MODEL_NAME = "facebook/wav2vec2-base"
_load_attempted = False


def _ensure_model_loaded() -> bool:
    global processor, model, _load_attempted
    if processor is not None and model is not None:
        return True
    if _load_attempted:
        return False

    _load_attempted = True

    try:
        import os
        from transformers import Wav2Vec2Model, Wav2Vec2Processor  # type: ignore

        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

        processor = Wav2Vec2Processor.from_pretrained(_MODEL_NAME, local_files_only=True)
        model = Wav2Vec2Model.from_pretrained(_MODEL_NAME, local_files_only=True)
        model.eval()
        return True
    except Exception:
        processor = None
        model = None
        return False


def extract_acoustic_embedding(audio_path: str) -> list[float]:
    if not _ensure_model_loaded():
        return [0.0] * 768

    import librosa  # type: ignore
    import soundfile as sf  # type: ignore
    import torch  # type: ignore

    waveform, sample_rate = sf.read(audio_path)

    if waveform.ndim > 1:
        waveform = waveform.mean(axis=1)

    if sample_rate != 16000:
        waveform = librosa.resample(waveform, orig_sr=sample_rate, target_sr=16000)

    inputs = processor(
        waveform,
        sampling_rate=16000,
        return_tensors="pt",
        padding=True,
    )

    with torch.no_grad():
        outputs = model(**inputs)

    embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
    return embedding.tolist()

