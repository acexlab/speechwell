"""
File Logic Summary: Canonical filesystem paths for runtime artifacts (DB, models, storage) resolved from repository root.
"""

import os
import sys
from pathlib import Path

# backend/app/paths.py -> backend/app -> backend -> repo root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
project_root_str = str(PROJECT_ROOT)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

from ml.dysarthria_pipeline_config import DYSARTHRIA_RUNTIME_MODEL_PATH, DYSARTHRIA_V2_MODEL_PATH

ML_DIR = PROJECT_ROOT / "ml"
MODELS_DIR = ML_DIR / "models"

DATA_DIR = Path(os.getenv("SPEECHWELL_DATA_DIR", str(PROJECT_ROOT))).expanduser()
STORAGE_DIR = Path(os.getenv("SPEECHWELL_STORAGE_DIR", str(DATA_DIR / "storage"))).expanduser()

SQLITE_DB_PATH = Path(os.getenv("SQLITE_DB_PATH", str(DATA_DIR / "speechwell.db"))).expanduser()

DYSARTHRIA_MODEL_PATH = MODELS_DIR / "dysarthria_model_v1.pkl"
DYSARTHRIA_PCA_PATH = MODELS_DIR / "dysarthria_pca_v1.pkl"
DYSARTHRIA_SCALER_PATH = MODELS_DIR / "dysarthria_scaler_v1.pkl"
DYSARTHRIA_MODEL_V2_PATH = PROJECT_ROOT / DYSARTHRIA_V2_MODEL_PATH
DYSARTHRIA_RUNTIME_MODEL_FILE = PROJECT_ROOT / DYSARTHRIA_RUNTIME_MODEL_PATH

UPLOADED_AUDIO_DIR = STORAGE_DIR / "uploaded_audio"
PROCESSED_AUDIO_DIR = STORAGE_DIR / "processed_audio"
REPORTS_DIR = STORAGE_DIR / "reports"
