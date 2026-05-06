"""
Fast raw-audio feature extraction utilities for dysarthria experiments.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf

try:
    import torch
    import torchaudio
    import torchaudio.functional as torchaudio_functional
except ImportError:
    torch = None
    torchaudio = None
    torchaudio_functional = None
    import librosa


TARGET_FRAMES = 8000
EPSILON = 1e-8
SILENCE_THRESHOLD = 0.01
SPEAKER_PATTERN = re.compile(r"wav_(?:arrayMic|headMic)_([A-Z]{1,2}\d{2}(?:S\d{2})?)_")
MFCC_COUNT = 13
N_FFT = 512
HOP_LENGTH = 256
CHROMA_BINS = 12
SPECTRAL_CONTRAST_BANDS = 6


def _summarize_feature(prefix: str, values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float32)
    return {
        f"{prefix}_mean": float(values.mean()),
        f"{prefix}_std": float(values.std()),
    }


def _ensure_min_signal_length(signal: np.ndarray, min_length: int = N_FFT) -> np.ndarray:
    if signal.size >= min_length:
        return signal
    pad_width = min_length - signal.size
    return np.pad(signal, (0, pad_width), mode="constant")


def _compute_chroma(power_spectrum: np.ndarray, sample_rate: int) -> np.ndarray:
    freqs = np.fft.rfftfreq((len(power_spectrum) - 1) * 2, d=1.0 / sample_rate)
    chroma = np.zeros(CHROMA_BINS, dtype=np.float32)
    for idx, freq in enumerate(freqs):
        if freq <= 0:
            continue
        midi = 69 + 12 * np.log2(freq / 440.0)
        chroma_bin = int(np.round(midi)) % CHROMA_BINS
        chroma[chroma_bin] += power_spectrum[idx]
    chroma_sum = chroma.sum()
    if chroma_sum > 0:
        chroma /= chroma_sum
    return chroma


def _compute_spectral_contrast(power_spectrum: np.ndarray, sample_rate: int) -> np.ndarray:
    freqs = np.fft.rfftfreq((len(power_spectrum) - 1) * 2, d=1.0 / sample_rate)
    valid = freqs > 0
    freqs = freqs[valid]
    spectrum = power_spectrum[valid]
    if freqs.size == 0:
        return np.zeros(SPECTRAL_CONTRAST_BANDS, dtype=np.float32)

    band_edges = np.geomspace(max(freqs.min(), 1.0), freqs.max(), num=SPECTRAL_CONTRAST_BANDS + 1)
    contrast = []
    for lower, upper in zip(band_edges[:-1], band_edges[1:]):
        band = spectrum[(freqs >= lower) & (freqs < upper)]
        if band.size == 0:
            contrast.append(0.0)
            continue
        low_energy = np.percentile(band, 10)
        high_energy = np.percentile(band, 90)
        contrast.append(float(high_energy - low_energy))
    return np.asarray(contrast, dtype=np.float32)


def parse_speaker_id(audio_path: str | Path) -> str:
    match = SPEAKER_PATTERN.search(str(audio_path).replace("/", "\\"))
    return match.group(1) if match else "unknown"


def _load_audio_prefix(
    audio_path: str | Path,
    target_frames: int | None = TARGET_FRAMES,
) -> tuple[np.ndarray, sf._SoundFileInfo]:
    info = sf.info(str(audio_path))
    frames = info.frames if target_frames is None else min(info.frames, target_frames)
    signal, _ = sf.read(
        str(audio_path),
        frames=frames,
        dtype="float32",
        always_2d=False,
    )

    signal = np.asarray(signal, dtype=np.float32)
    if signal.ndim > 1:
        signal = signal.mean(axis=1)
    if signal.size == 0:
        signal = np.zeros(1, dtype=np.float32)

    return signal, info


def extract_raw_audio_features(
    audio_path: str | Path,
    target_frames: int | None = TARGET_FRAMES,
) -> dict[str, Any]:
    signal, info = _load_audio_prefix(audio_path, target_frames=target_frames)
    signal = _ensure_min_signal_length(signal)
    sample_rate = int(info.samplerate)

    abs_signal = np.abs(signal)
    rms = float(np.sqrt(np.mean(signal**2)))
    zcr = float((signal[:-1] * signal[1:] < 0).mean()) if signal.size > 1 else 0.0

    power = np.abs(np.fft.rfft(signal)) ** 2
    freqs = np.fft.rfftfreq(signal.size, d=1.0 / info.samplerate)
    power_sum = float(power.sum()) + EPSILON

    centroid = float((freqs * power).sum() / power_sum)
    bandwidth = float(np.sqrt((((freqs - centroid) ** 2) * power).sum() / power_sum))
    cumulative_power = np.cumsum(power)
    rolloff_index = int(np.searchsorted(cumulative_power, 0.85 * power_sum))
    rolloff_index = min(rolloff_index, max(len(freqs) - 1, 0))
    rolloff_85 = float(freqs[rolloff_index]) if freqs.size else 0.0
    flatness = float(np.exp(np.mean(np.log(power + EPSILON))) / (np.mean(power) + EPSILON))
    if torchaudio is not None and torch is not None and torchaudio_functional is not None:
        waveform = torch.from_numpy(signal).unsqueeze(0)
        mfcc_transform = torchaudio.transforms.MFCC(
            sample_rate=sample_rate,
            n_mfcc=MFCC_COUNT,
            melkwargs={"n_fft": N_FFT, "hop_length": HOP_LENGTH, "n_mels": 40},
        )
        mfcc = mfcc_transform(waveform).squeeze(0)
        mfcc_delta = torchaudio_functional.compute_deltas(mfcc)
        mfcc_delta2 = torchaudio_functional.compute_deltas(mfcc_delta)
        mfcc_np = mfcc.numpy()
        mfcc_delta_np = mfcc_delta.numpy()
        mfcc_delta2_np = mfcc_delta2.numpy()
    else:
        mfcc_np = librosa.feature.mfcc(
            y=signal,
            sr=sample_rate,
            n_mfcc=MFCC_COUNT,
            n_fft=N_FFT,
            hop_length=HOP_LENGTH,
        )
        mfcc_delta_np = librosa.feature.delta(mfcc_np)
        mfcc_delta2_np = librosa.feature.delta(mfcc_np, order=2)

    zcr_frames = ((signal[:-1] * signal[1:]) < 0).astype(np.float32) if signal.size > 1 else np.zeros(1, dtype=np.float32)
    chroma = _compute_chroma(power, sample_rate)
    spectral_contrast = _compute_spectral_contrast(power, sample_rate)

    feature_row = {
        "audio_path": str(audio_path),
        "speaker_id": parse_speaker_id(audio_path),
        "duration_sec": float(info.frames / info.samplerate) if info.samplerate else 0.0,
        "sample_rate": sample_rate,
        "channels": int(info.channels),
        "rms": rms,
        "mean_abs": float(abs_signal.mean()),
        "std": float(signal.std()),
        "max_abs": float(abs_signal.max()),
        "q25_abs": float(np.quantile(abs_signal, 0.25)),
        "q50_abs": float(np.quantile(abs_signal, 0.50)),
        "q75_abs": float(np.quantile(abs_signal, 0.75)),
        "silence_ratio": float((abs_signal < SILENCE_THRESHOLD).mean()),
        "zcr": zcr,
        "centroid": centroid,
        "bandwidth": bandwidth,
        "rolloff_85": rolloff_85,
        "flatness": flatness,
        **_summarize_feature("zcr_frame", zcr_frames),
        **_summarize_feature("chroma", chroma),
        **_summarize_feature("spectral_contrast", spectral_contrast),
    }

    for idx in range(MFCC_COUNT):
        feature_row[f"mfcc_{idx + 1}_mean"] = float(mfcc_np[idx].mean())
        feature_row[f"mfcc_{idx + 1}_std"] = float(mfcc_np[idx].std())
        feature_row[f"mfcc_delta_{idx + 1}_mean"] = float(mfcc_delta_np[idx].mean())
        feature_row[f"mfcc_delta_{idx + 1}_std"] = float(mfcc_delta_np[idx].std())
        feature_row[f"mfcc_delta2_{idx + 1}_mean"] = float(mfcc_delta2_np[idx].mean())
        feature_row[f"mfcc_delta2_{idx + 1}_std"] = float(mfcc_delta2_np[idx].std())

    return feature_row
