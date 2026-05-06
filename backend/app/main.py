"""
File Logic Summary: FastAPI entrypoint. It validates uploads, normalizes audio, calls the ML pipeline, stores analysis results, and serves auth/history/report endpoints.
"""

import os
import sys
import warnings
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None

from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Depends, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .paths import (
    PROJECT_ROOT,
    UPLOADED_AUDIO_DIR,
    PROCESSED_AUDIO_DIR,
    REPORTS_DIR as REPORTS_PATH,
)

# Suppress noisy third-party warnings that do not affect runtime correctness.
warnings.filterwarnings(
    "ignore",
    message=r"`resume_download` is deprecated.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"Passing `gradient_checkpointing` to a config initialization is deprecated.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"Some weights of Wav2Vec2Model were not initialized from the model checkpoint.*",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"pkg_resources is deprecated as an API.*",
    category=UserWarning,
)

# Ensure project root is on PYTHONPATH so this app starts from either
# `SpeechWell` root or `SpeechWell/backend` working directory.
project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)
if load_dotenv is not None:
    load_dotenv(str(PROJECT_ROOT / ".env"))

from backend.app.database.db import engine, SessionLocal
from backend.app.database.models import Base, Analysis, User, TrainingSession, TrainingProgress

from backend.app.services.auth_service import (
    hash_password, verify_password, create_access_token, verify_token
)
from backend.app.schemas import (
    UserRegister, UserLogin, TokenResponse,
    AnalysisDetailResponse, HistoryResponse,
    UserProfileUpdate, UserProfileResponse,
    ChatRequest, ChatResponse,
    TrainingModuleResponse, TrainingSessionStartRequest,
    TrainingSessionStartResponse, TrainingEvaluationResponse,
    TrainingSessionResponse, TrainingProgressResponse,
)

import shutil
import subprocess
import uuid
import re
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from requests import RequestException

from backend.app.services.training_catalog import list_modules, get_exercise
from backend.app.services.grammar_service import estimate_grammar_metrics
from backend.app.services.training_service import (
    evaluate_audio_attempt,
    evaluate_text_attempt,
    sync_progress,
)

app = FastAPI(title="SpeechWell API")


def get_cors_origins() -> list[str]:
    configured_origins = os.getenv("CORS_ORIGINS", "")
    if configured_origins.strip():
        return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://localhost:3000"]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)


def ensure_sqlite_schema_compatibility():
    """Add missing columns for older local SQLite databases."""
    if engine.url.get_backend_name() != "sqlite":
        return

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
            ("report_filename", "VARCHAR"),
            ("status", "VARCHAR DEFAULT 'completed'"),
            ("error_message", "VARCHAR"),
            ("updated_at", "DATETIME"),
        ],
        "users": [
            ("full_name", "VARCHAR"),
            ("age", "INTEGER"),
            ("gender", "VARCHAR"),
            ("location", "VARCHAR"),
            ("occupation", "VARCHAR"),
            ("primary_goal", "VARCHAR"),
            ("bio", "TEXT"),
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

UPLOAD_DIR = str(UPLOADED_AUDIO_DIR)
PROCESSED_DIR = str(PROCESSED_AUDIO_DIR)
REPORTS_DIR = str(REPORTS_PATH)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def normalize_analysis_grammar_metrics(analysis: Analysis) -> tuple[float, float]:
    error_probability, error_estimate, quality_score = estimate_grammar_metrics(
        analysis.transcript or "",
        corrected_text=analysis.corrected_text or "",
        base_error_count=int(analysis.grammar_error_count or 0),
    )
    analysis.grammar_error_count = error_estimate
    return round(error_probability, 3), round(quality_score, 3)


def backfill_analysis_metric_consistency():
    """Keep persisted analysis rows aligned with current metric semantics."""
    db = SessionLocal()
    try:
        analyses = db.query(Analysis).all()
        changed = False
        for analysis in analyses:
            previous_error_count = int(analysis.grammar_error_count or 0)
            _, quality_score = normalize_analysis_grammar_metrics(analysis)
            existing_score = round(float(analysis.grammar_score or 0.0), 3)
            if (
                abs(existing_score - quality_score) > 0.001
                or previous_error_count != int(analysis.grammar_error_count or 0)
            ):
                analysis.grammar_score = quality_score
                changed = True
        if changed:
            db.commit()
    finally:
        db.close()


backfill_analysis_metric_consistency()


def backfill_report_filenames():
    """Populate report_filename for existing rows that only stored pdf_path."""
    db = SessionLocal()
    try:
        analyses = db.query(Analysis).filter(Analysis.report_filename.is_(None)).all()
        changed = False
        for analysis in analyses:
            if analysis.pdf_path:
                analysis.report_filename = os.path.basename(analysis.pdf_path)
                changed = True
        if changed:
            db.commit()
    finally:
        db.close()


backfill_report_filenames()


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


def build_report_owner_name(current_user: Optional[User]) -> str:
    if current_user and current_user.full_name:
        return current_user.full_name.strip()
    if current_user and current_user.email:
        return current_user.email.split("@")[0].strip()
    return "SpeechWell User"


def build_unique_report_filename(db: Session, user_name: str, report_date: str) -> str:
    safe_user_name = re.sub(r"[^a-zA-Z0-9]+", "_", (user_name or "").strip().lower()).strip("_") or "speechwell_user"
    base_stem = f"{safe_user_name}_{report_date}"

    existing_names = {
        row[0]
        for row in db.query(Analysis.report_filename)
        .filter(Analysis.report_filename.like(f"{base_stem}%"))
        .all()
        if row[0]
    }
    existing_names.update(path.name for path in REPORTS_PATH.glob(f"{base_stem}*.pdf"))

    candidate = f"{base_stem}.pdf"
    if candidate not in existing_names:
        return candidate

    suffix = 1
    while True:
        candidate = f"{base_stem}_{suffix}.pdf"
        if candidate not in existing_names:
            return candidate
        suffix += 1


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


@app.get("/api/profile", response_model=UserProfileResponse)
def get_profile(current_user: Optional[User] = Depends(get_current_user)):
    """Get logged-in user's profile details."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user


@app.put("/api/profile", response_model=UserProfileResponse)
def update_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Update logged-in user's editable profile fields."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    current_user.full_name = profile_data.full_name
    current_user.age = profile_data.age
    current_user.gender = profile_data.gender
    current_user.location = profile_data.location
    current_user.occupation = profile_data.occupation
    current_user.primary_goal = profile_data.primary_goal
    current_user.bio = profile_data.bio

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


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

        report_owner_name = build_report_owner_name(current_user)
        report_date = datetime.now().strftime("%Y-%m-%d")
        report_filename = build_unique_report_filename(db, report_owner_name, report_date)

        try:
            pdf_path = generate_pdf_report(
                audio_id=audio_id,
                whisper_features=whisper_features,
                classification_result=classification_results,
                report_filename=report_filename,
                user_name=report_owner_name,
                report_date=report_date,
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
        analysis_record.grammar_score = grammar_result.get("grammar_quality_score", 0.0)
        analysis_record.grammar_error_count = grammar_result.get("error_count_estimate", 0)
        analysis_record.corrected_text = grammar_result.get("corrected_text", "")
        analysis_record.phonological_score = phonological_result.get("phonological_error_probability", 0.0)
        analysis_record.phonological_error_count = phonological_result.get("error_count", 0)
        analysis_record.speaking_rate_wps = whisper_features.get("speaking_rate_wps", 0.0)
        analysis_record.average_pause_sec = whisper_features.get("average_pause_sec", 0.0)
        analysis_record.max_pause_sec = whisper_features.get("max_pause_sec", 0.0)
        analysis_record.total_duration_sec = whisper_features.get("total_duration_sec", 0.0)
        analysis_record.pdf_path = pdf_path
        analysis_record.report_filename = report_filename if pdf_path else None
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

    error_probability, quality_score = normalize_analysis_grammar_metrics(analysis)
    analysis.grammar_score = quality_score
    setattr(analysis, "grammar_error_probability", error_probability)
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
        _, grammar_quality = normalize_analysis_grammar_metrics(r)
        normalized.append(
            {
                "id": r.id,
                "audio_id": r.audio_id or f"legacy-{r.id}",
                "filename": r.filename or "unknown.wav",
                "report_filename": r.report_filename,
                "dysarthria_probability": float(r.dysarthria_probability or 0.0),
                "stuttering_probability": float(r.stuttering_probability or 0.0),
                "grammar_score": grammar_quality,
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
        filename=analysis.report_filename or os.path.basename(analysis.pdf_path),
        media_type="application/pdf"
    )


# ============ TRAINING ENDPOINTS ============

@app.get("/api/training/modules", response_model=list[TrainingModuleResponse])
def get_training_modules():
    """Return the static guided training catalog used by the Therapy Hub."""
    modules = []
    for module in list_modules():
        modules.append(
            {
                "key": module["key"],
                "title": module["title"],
                "description": module["description"],
                "focus_area": module["focus_area"],
                "exercise_count": len(module["exercises"]),
                "exercises": module["exercises"],
            }
        )
    return modules


@app.post("/api/training/session/start", response_model=TrainingSessionStartResponse)
def start_training_session(
    payload: TrainingSessionStartRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Create a training session record before the user performs an exercise."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    exercise = get_exercise(payload.module_key, payload.exercise_key)
    if not exercise:
        raise HTTPException(status_code=404, detail="Training exercise not found")

    session = TrainingSession(
        user_id=current_user.id,
        module_key=payload.module_key,
        exercise_key=payload.exercise_key,
        prompt_text=exercise.get("prompt_text"),
        expected_text=exercise.get("expected_text"),
        input_mode=exercise.get("input_mode", "mic"),
        status="started",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "module_key": session.module_key,
        "exercise_key": session.exercise_key,
        "prompt_text": session.prompt_text,
        "expected_text": session.expected_text,
        "input_mode": session.input_mode,
        "status": session.status,
    }


@app.post("/api/training/session/evaluate", response_model=TrainingEvaluationResponse)
async def evaluate_training_session(
    session_id: int = Form(...),
    transcript_text: str = Form(""),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Evaluate one training attempt using either text input or uploaded audio."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    session = (
        db.query(TrainingSession)
        .filter(
            TrainingSession.id == session_id,
            TrainingSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Training session not found")

    try:
        if file is not None:
            audio_id = str(uuid.uuid4())
            safe_filename = os.path.basename(file.filename or "training.wav")
            original_path = os.path.join(UPLOAD_DIR, f"{audio_id}_{safe_filename}")
            processed_path = os.path.join(PROCESSED_DIR, f"training_{audio_id}.wav")

            with open(original_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            normalize_audio(original_path, processed_path)
            evaluation = evaluate_audio_attempt(
                session.module_key,
                session.exercise_key,
                processed_path,
                session.expected_text,
            )
        else:
            evaluation = evaluate_text_attempt(
                session.module_key,
                session.exercise_key,
                session.expected_text,
                transcript_text,
                prompt_text=session.prompt_text,
            )

        session.transcript = evaluation["transcript"]
        session.accuracy_score = evaluation["accuracy_score"]
        session.fluency_score = evaluation["fluency_score"]
        session.confidence_score = evaluation["confidence_score"]
        session.long_pause_count = evaluation["long_pause_count"]
        session.repeated_word_count = evaluation["repeated_word_count"]
        session.duration_sec = evaluation["duration_sec"]
        session.corrected_text = evaluation.get("corrected_text")
        session.feedback_summary = "\n".join(evaluation["feedback"])
        session.status = "completed" if evaluation.get("is_valid", True) else "failed"

        db.add(session)
        db.commit()
        db.refresh(session)
        if session.status == "completed":
            sync_progress(db, session)

        return {
            "session_id": session.id,
            "transcript": session.transcript or "",
            "accuracy_score": round(float(session.accuracy_score or 0.0)),
            "fluency_score": round(float(session.fluency_score or 0.0)),
            "confidence_score": round(float(session.confidence_score or 0.0)),
            "long_pause_count": int(session.long_pause_count or 0),
            "repeated_word_count": int(session.repeated_word_count or 0),
            "duration_sec": round(float(session.duration_sec or 0.0), 2),
            "corrected_text": session.corrected_text,
            "feedback": evaluation["feedback"],
        }
    except Exception as exc:
        session.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/training/session/{session_id}", response_model=TrainingSessionResponse)
def get_training_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    session = (
        db.query(TrainingSession)
        .filter(
            TrainingSession.id == session_id,
            TrainingSession.user_id == current_user.id,
        )
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Training session not found")
    return session


@app.get("/api/training/sessions", response_model=list[TrainingSessionResponse])
def get_training_sessions(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    return (
        db.query(TrainingSession)
        .filter(TrainingSession.user_id == current_user.id)
        .order_by(TrainingSession.created_at.desc())
        .limit(20)
        .all()
    )


@app.get("/api/training/progress", response_model=list[TrainingProgressResponse])
def get_training_progress(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    progress_rows = (
        db.query(TrainingProgress)
        .filter(TrainingProgress.user_id == current_user.id)
        .order_by(TrainingProgress.module_key.asc())
        .all()
    )

    return [
        {
            "module_key": row.module_key,
            "sessions_completed": int(row.sessions_completed or 0),
            "avg_accuracy": round(float(row.avg_accuracy or 0.0)),
            "avg_fluency": round(float(row.avg_fluency or 0.0)),
            "best_score": round(float(row.best_score or 0.0)),
            "last_practiced_at": row.last_practiced_at,
        }
        for row in progress_rows
    ]


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SpeechWell API"}


@app.post("/api/chat", response_model=ChatResponse)
def chat_with_ai(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """SpeechWell AI coach endpoint backed by configured chat provider."""
    try:
        from backend.app.services.chat_service import generate_chat_reply

        history = [{"role": m.role, "text": m.text} for m in payload.history]
        analysis_context = None
        if current_user:
            query = db.query(Analysis).filter(Analysis.user_id == current_user.id)
            if payload.audio_id:
                query = query.filter(Analysis.audio_id == payload.audio_id)
            analysis = query.order_by(Analysis.created_at.desc()).first()
            if analysis:
                grammar_error_probability, grammar_quality_score = normalize_analysis_grammar_metrics(analysis)
                analysis_context = {
                    "audio_id": analysis.audio_id,
                    "filename": analysis.filename,
                    "transcript": analysis.transcript,
                    "dysarthria_probability": float(analysis.dysarthria_probability or 0.0),
                    "dysarthria_label": analysis.dysarthria_label,
                    "stuttering_probability": float(analysis.stuttering_probability or 0.0),
                    "stuttering_repetitions": int(analysis.stuttering_repetitions or 0),
                    "stuttering_prolongations": int(analysis.stuttering_prolongations or 0),
                    "stuttering_blocks": int(analysis.stuttering_blocks or 0),
                    "grammar_score": grammar_quality_score,
                    "grammar_error_probability": grammar_error_probability,
                    "grammar_error_count": int(analysis.grammar_error_count or 0),
                    "corrected_text": analysis.corrected_text,
                    "phonological_score": float(analysis.phonological_score or 0.0),
                    "phonological_error_count": int(analysis.phonological_error_count or 0),
                    "speaking_rate_wps": float(analysis.speaking_rate_wps or 0.0),
                    "average_pause_sec": float(analysis.average_pause_sec or 0.0),
                    "max_pause_sec": float(analysis.max_pause_sec or 0.0),
                    "total_duration_sec": float(analysis.total_duration_sec or 0.0),
                }

        reply = generate_chat_reply(payload.message, history, analysis_context=analysis_context)
        return ChatResponse(reply=reply)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RequestException as e:
        raise HTTPException(status_code=502, detail=f"Chat provider request failed: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to generate AI response")

