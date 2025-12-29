from fastapi import FastAPI, UploadFile, File, HTTPException
import os
import shutil
import subprocess
import json
import uuid

from backend.app.services.whisper_service import analyze_whisper
from backend.app.services.acoustic_service import analyze_acoustic
from backend.app.services.classifier_service import classify_speech
from backend.app.services.data_loader import (
    load_whisper_features,
    load_acoustic_embeddings
)
from backend.app.services.report_service import generate_pdf_report


app = FastAPI(title="SpeechWell API")

UPLOAD_DIR = "storage/uploaded_audio"
PROCESSED_DIR = "storage/processed_audio"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


# -------------------------
# Utility functions
# -------------------------

def get_audio_metadata(file_path: str):
    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=duration,sample_rate,channels",
        "-of", "json",
        file_path
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise Exception("FFprobe failed")

    metadata = json.loads(result.stdout)
    stream = metadata["streams"][0]

    return {
        "duration_seconds": round(float(stream["duration"]), 2),
        "sample_rate_hz": int(stream["sample_rate"]),
        "channels": stream["channels"]
    }


def normalize_audio(input_path: str, output_path: str):
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-ac", "1",
        "-ar", "16000",
        output_path
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.returncode != 0:
        raise Exception("Audio normalization failed")


# -------------------------
# API endpoints
# -------------------------

@app.get("/")
def root():
    return {"message": "SpeechWell backend is running 🚀"}


@app.post("/analyze/upload")
async def upload_audio(file: UploadFile = File(...)):
    if file.content_type not in ["audio/wav", "audio/mpeg"]:
        raise HTTPException(
            status_code=400,
            detail="Only WAV or MP3 files are allowed"
        )

    audio_id = str(uuid.uuid4())

    original_path = os.path.join(
        UPLOAD_DIR, f"{audio_id}_{file.filename}"
    )

    processed_path = os.path.join(
        PROCESSED_DIR, f"{audio_id}.wav"
    )

    with open(original_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        normalize_audio(original_path, processed_path)
        metadata = get_audio_metadata(processed_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Audio uploaded and normalized successfully",
        "audio_id": audio_id,
        "processed_metadata": metadata
    }


@app.get("/analyze/whisper/{audio_id}")
def run_whisper_analysis(audio_id: str):
    try:
        result = analyze_whisper(audio_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "audio_id": audio_id,
        "whisper_features": result
    }


@app.get("/analyze/acoustic/{audio_id}")
def run_acoustic_analysis(audio_id: str):
    try:
        embedding = analyze_acoustic(audio_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "audio_id": audio_id,
        "embedding_dimension": len(embedding)
    }


@app.get("/analyze/classify/{audio_id}")
def classify_audio(audio_id: str):
    try:
        whisper_features = load_whisper_features(audio_id)
        acoustic_embeddings = load_acoustic_embeddings(audio_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    result = classify_speech(
        whisper_features,
        acoustic_embeddings
    )

    return {
        "audio_id": audio_id,
        "classification": result
    }
@app.get("/analyze/report/{audio_id}")
def generate_report(audio_id: str):
    try:
        whisper_features = load_whisper_features(audio_id)
        acoustic_embeddings = load_acoustic_embeddings(audio_id)

        classification = classify_speech(
            whisper_features,
            acoustic_embeddings
        )

        pdf_path = generate_pdf_report(audio_id, classification)

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "audio_id": audio_id,
        "message": "PDF report generated successfully",
        "report_path": pdf_path
    }
