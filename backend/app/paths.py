"""
File Logic Summary: Canonical filesystem paths for runtime artifacts (DB, models, storage) resolved from repository root.
"""

from pathlib import Path


# backend/app/paths.py -> backend/app -> backend -> repo root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

ML_DIR = PROJECT_ROOT / "ml"
MODELS_DIR = ML_DIR / "models"
STORAGE_DIR = PROJECT_ROOT / "storage"

SQLITE_DB_PATH = PROJECT_ROOT / "speechwell.db"

DYSARTHRIA_MODEL_PATH = MODELS_DIR / "dysarthria_model_v1.pkl"
DYSARTHRIA_PCA_PATH = MODELS_DIR / "dysarthria_pca_v1.pkl"
DYSARTHRIA_SCALER_PATH = MODELS_DIR / "dysarthria_scaler_v1.pkl"

UPLOADED_AUDIO_DIR = STORAGE_DIR / "uploaded_audio"
PROCESSED_AUDIO_DIR = STORAGE_DIR / "processed_audio"
REPORTS_DIR = STORAGE_DIR / "reports"
