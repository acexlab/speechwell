"""
File Logic Summary: FastAPI entrypoint. It validates uploads, normalizes audio, calls the ML pipeline, stores analysis results, and serves auth/history/report endpoints.
"""

import os
import sys

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is on PYTHONPATH so this app starts from either
# `SpeechWell` root or `SpeechWell/backend` working directory.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.database.db import engine, SessionLocal
from backend.app.database.models import Base, Analysis, User

from backend.app.services.auth_service import (
    hash_password, verify_password, create_access_token, verify_token
)
from backend.app.schemas import (
    UserRegister, UserLogin, TokenResponse,
    AnalysisDetailResponse, HistoryResponse
)

import shutil
import subprocess
import uuid
import re
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

app = FastAPI(title="SpeechWell API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)


def ensure_sqlite_schema_compatibility():
    """Add missing columns for older local SQLite databases."""
    required_columns = {
        "analyses": [
            ("user_id", "INTEGER"),
            ("filename", "VARCHAR"),
            ("transcript", "TEXT"),
            ("dysarthria_label", "VARCHAR"),
            ("stuttering_repetitions", "INTEGER DEFAULT 0"),
            ("stuttering_prolongations", "INTEGER DEFAULT 0"),
            ("stuttering_blocks", "INTEGER DEFAULT 0"),
            ("grammar_error_count", "INTEGER DEFAULT 0"),
            ("corrected_text", "TEXT"),
            ("phonological_error_count", "INTEGER DEFAULT 0"),
            ("speaking_rate_wps", "FLOAT"),
            ("average_pause_sec", "FLOAT"),
            ("max_pause_sec", "FLOAT"),
            ("total_duration_sec", "FLOAT"),
            ("audio_path", "VARCHAR"),
            ("status", "VARCHAR DEFAULT 'completed'"),
            ("error_message", "VARCHAR"),
            ("updated_at", "DATETIME"),
        ],
        "users": [
            ("full_name", "VARCHAR"),
            ("updated_at", "DATETIME"),
        ],
    }

    with engine.begin() as conn:
        for table_name, columns in required_columns.items():
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            existing_columns = {row[1] for row in result.fetchall()}
            for column_name, column_type in columns:
                if column_name not in existing_columns:
                    conn.execute(
                        text(
                            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                        )
                    )


ensure_sqlite_schema_compatibility()

UPLOAD_DIR = "storage/uploaded_audio"
PROCESSED_DIR = "storage/processed_audio"
REPORTS_DIR = "storage/reports"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Optional[User]:
    """Extract and validate user from JWT token"""
    if not authorization:
        return None
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = verify_token(token)
        if not payload:
            return None
        
        email = payload.get("email")
        user = db.query(User).filter(User.email == email).first()
        return user
    except Exception:
        return None


def normalize_audio(input_path: str, output_path: str):
    """Normalize audio to 16kHz mono using ffmpeg"""
    command = [
        "ffmpeg", "-y",
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
        raise RuntimeError("Audio normalization failed")


@app.get("/")
def root():
    return {"message": "SpeechWell backend is running 🚀"}


# ============ AUTHENTICATION ENDPOINTS ============

@app.post("/api/auth/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    # Validate passwords match
    if user_data.password != user_data.password_confirm:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create token
    access_token = create_access_token(data={"sub": new_user.email})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name
        }
    )


@app.post("/api/auth/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login a user"""
    user = db.query(User).filter(User.email == user_data.email).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    access_token = create_access_token(data={"sub": user.email})
    
    return TokenResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    )


@app.post("/api/analyze", response_model=AnalysisDetailResponse)
async def analyze_and_classify(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Analyze audio file and run ML models for dysarthria, stuttering, grammar, and phonological errors.
    Returns comprehensive analysis results.
    """
    filename = (file.filename or "").lower()
    valid_content_types = {
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/mpg",
        "audio/webm",
        "audio/ogg",
        "audio/mp4",
        "application/octet-stream",
    }
    valid_extension = filename.endswith((".wav", ".mp3", ".webm", ".ogg", ".m4a"))
    if file.content_type not in valid_content_types and not valid_extension:
        raise HTTPException(
            status_code=400,
            detail="Only WAV, MP3, WEBM, OGG, or M4A files are allowed"
        )

    audio_id = str(uuid.uuid4())
    user_id = current_user.id if current_user else None

    safe_filename = os.path.basename(file.filename or "upload.wav")
    original_path = os.path.join(UPLOAD_DIR, f"{audio_id}_{safe_filename}")
    processed_path = os.path.join(PROCESSED_DIR, f"{audio_id}.wav")

    # Save uploaded file
    with open(original_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    analysis_record = None
    try:
        from backend.app.services.pdf_report_service import generate_pdf_report
        from ml.services.speech_analysis_service import run_full_analysis

        # Create analysis record in DB with "processing" status
        analysis_record = Analysis(
            user_id=user_id,
            audio_id=audio_id,
            filename=safe_filename,
            audio_path=original_path,
            status="processing"
        )
        db.add(analysis_record)
        db.commit()
        db.refresh(analysis_record)

        # 1️⃣ Normalize audio
        normalize_audio(original_path, processed_path)

        # 2) Run ML pipeline from /ml
        ml_result = run_full_analysis(processed_path)
        transcript = ml_result["transcript"]
        whisper_features = ml_result["whisper_features"]
        grammar_result = ml_result["grammar_result"]
        dysarthria_result = ml_result["dysarthria_result"]
        stuttering_result = ml_result["stuttering_result"]
        phonological_result = ml_result["phonological_result"]

        # 8️⃣ Generate PDF report
        classification_results = {
            "dysarthria": dysarthria_result,
            "stuttering": stuttering_result,
            "phonological": phonological_result,
            "grammar": grammar_result
        }

        raw_user_name = (
            current_user.full_name
            if current_user and current_user.full_name
            else (current_user.email.split("@")[0] if current_user else "guest")
        )
        safe_user_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", raw_user_name).strip("_").lower() or "guest"
        report_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{safe_user_name}_{report_timestamp}_{audio_id}.pdf"

        try:
            pdf_path = generate_pdf_report(
                audio_id=audio_id,
                whisper_features=whisper_features,
                classification_result=classification_results,
                report_filename=report_filename,
            )
        except Exception:
            pdf_path = None

        # 9️⃣ Update analysis record with results
        analysis_record.transcript = transcript
        analysis_record.dysarthria_probability = dysarthria_result.get("probability", 0.0)
        analysis_record.dysarthria_label = dysarthria_result.get("label", "unknown")
        analysis_record.stuttering_probability = stuttering_result.get("stuttering_probability", 0.0)
        analysis_record.stuttering_repetitions = stuttering_result.get("repetitions", 0)
        analysis_record.stuttering_prolongations = stuttering_result.get("prolongations", 0)
        analysis_record.stuttering_blocks = stuttering_result.get("blocks", 0)
        analysis_record.grammar_score = grammar_result.get("grammar_error_probability", 0.0)
        analysis_record.grammar_error_count = grammar_result.get("error_count_estimate", 0)
        analysis_record.corrected_text = grammar_result.get("corrected_text", "")
        analysis_record.phonological_score = phonological_result.get("phonological_error_probability", 0.0)
        analysis_record.phonological_error_count = phonological_result.get("error_count", 0)
        analysis_record.speaking_rate_wps = whisper_features.get("speaking_rate_wps", 0.0)
        analysis_record.average_pause_sec = whisper_features.get("average_pause_sec", 0.0)
        analysis_record.max_pause_sec = whisper_features.get("max_pause_sec", 0.0)
        analysis_record.total_duration_sec = whisper_features.get("total_duration_sec", 0.0)
        analysis_record.pdf_path = pdf_path
        analysis_record.status = "completed"

        db.commit()
        db.refresh(analysis_record)

        return analysis_record

    except Exception as e:
        # Update record with error status when record exists
        if analysis_record is not None:
            analysis_record.status = "failed"
            analysis_record.error_message = str(e)
            db.commit()

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analyze/{audio_id}", response_model=AnalysisDetailResponse)
def get_analysis(
    audio_id: str, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get detailed analysis results for a specific audio"""
    analysis = db.query(Analysis).filter(Analysis.audio_id == audio_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Check if user has permission (if they own it)
    if current_user and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return analysis
@app.get("/api/analyses", response_model=list[HistoryResponse])
def get_history(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get all analyses for current user or all if not authenticated"""
    if current_user:
        records = db.query(Analysis).filter(
            Analysis.user_id == current_user.id
        ).order_by(Analysis.created_at.desc()).all()
    else:
        records = db.query(Analysis).order_by(Analysis.created_at.desc()).all()

    normalized = []
    for r in records:
        normalized.append(
            {
                "id": r.id,
                "audio_id": r.audio_id or f"legacy-{r.id}",
                "filename": r.filename or "unknown.wav",
                "dysarthria_probability": float(r.dysarthria_probability or 0.0),
                "stuttering_probability": float(r.stuttering_probability or 0.0),
                "grammar_score": float(r.grammar_score or 0.0),
                "created_at": r.created_at,
            }
        )

    return normalized


@app.get("/api/reports/{audio_id}")
def download_report(
    audio_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Download PDF report for an analysis"""
    analysis = db.query(Analysis).filter(Analysis.audio_id == audio_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Check authorization
    if current_user and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if not analysis.pdf_path or not os.path.exists(analysis.pdf_path):
        raise HTTPException(status_code=404, detail="PDF report not found")
    
    return FileResponse(
        path=analysis.pdf_path,
        filename=os.path.basename(analysis.pdf_path),
        media_type="application/pdf"
    )


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SpeechWell API"}

