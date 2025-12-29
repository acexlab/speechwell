import whisper
import os
import json

# Load Whisper model ONCE
model = whisper.load_model("base")


def analyze_chunk(chunk_path: str):
    """
    Analyze a single audio chunk and extract fluency features
    """
    result = model.transcribe(chunk_path, fp16=False)

    text = result.get("text", "").strip()
    segments = result.get("segments", [])

    total_words = len(text.split())
    total_duration = 0.0
    pauses = []

    previous_end = None

    for segment in segments:
        start = segment["start"]
        end = segment["end"]
        total_duration += (end - start)

        if previous_end is not None:
            pause = start - previous_end
            if pause > 0:
                pauses.append(pause)

        previous_end = end

    avg_pause = round(sum(pauses) / len(pauses), 2) if pauses else 0.0
    max_pause = round(max(pauses), 2) if pauses else 0.0
    speaking_rate = round(total_words / total_duration, 2) if total_duration > 0 else 0.0

    return {
        "transcript": text,
        "total_words": total_words,
        "speaking_rate_wps": speaking_rate,
        "average_pause_sec": avg_pause,
        "max_pause_sec": max_pause
    }


def analyze_whisper(audio_id: str):
    """
    Runs Whisper analysis on the full processed audio file
    and saves results as JSON.
    """

    audio_path = f"storage/processed_audio/{audio_id}.wav"

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Processed audio not found: {audio_path}")

    # For now, we treat the full audio as one chunk
    features = analyze_chunk(audio_path)

    os.makedirs("storage/results/whisper", exist_ok=True)

    with open(f"storage/results/whisper/{audio_id}.json", "w") as f:
        json.dump([features], f, indent=2)

    return features
