<!-- File Logic Summary: Step-by-step installation and setup requirements for running backend and frontend. -->

# SpeechWell Requirements & Setup (Backend + Frontend)

This file is a step-by-step, commented setup guide for running the full project locally.

## 1) Prerequisites (install first)

Required:
- Python 3.9+ (matches `quickstart.ps1` check)
- Node.js 18+ (includes npm)
- FFmpeg (must be on PATH for audio normalization)

Optional but recommended:
- Git (for cloning/pulling updates)

Notes:
- Windows users can confirm FFmpeg by running `ffmpeg -version` in PowerShell.
- If FFmpeg is missing, audio normalization will fail.

## 2) Backend Setup (Python + ML)

### Step 2.1: Create and activate a virtual environment (optional but recommended)
```powershell
# Create venv
python -m venv venv

# Activate venv (PowerShell)
.\venv\Scripts\Activate.ps1
```

### Step 2.2: Install backend + ML dependencies
```powershell
# Install all backend + ML dependencies
pip install -r requirements.txt
```

### Step 2.3: Configure environment variables
```powershell
# Copy example env file and edit it with your API keys
Copy-Item .env.example .env

# Edit .env and set keys for chat features (optional)
# OPENAI_API_KEY=...
# OPENAI_MODEL=gpt-4o-mini
# GEMINI_API_KEY=...
# GEMINI_MODEL=gemini-1.5-flash
```

Notes:
- Chat features require `OPENAI_API_KEY` or `GEMINI_API_KEY`.
- Core analysis (upload + ML pipeline) runs without chat keys.

### Step 2.4: Ensure ML model artifacts exist
Required files in `ml/models/`:
- `dysarthria_model_v1.pkl`
- `dysarthria_pca_v1.pkl`
- `dysarthria_scaler_v1.pkl`

If any are missing:
```powershell
# Train baseline dysarthria model (generates model artifacts)
python ml/training/train_dysarthria_model.py
```

### Step 2.5: Start the backend API
```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected:
- API running at `http://localhost:8000`
- Health check: `GET /api/health`

## 3) Frontend Setup (React)

### Step 3.1: Install frontend dependencies
```powershell
cd speechwell-frontend
npm install
```

### Step 3.2: Start the frontend dev server
```powershell
npm run dev
```

Expected:
- Frontend running at `http://localhost:5173`

## 4) Full System Run (two terminals)

Terminal 1 (Backend):
```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (Frontend):
```powershell
cd speechwell-frontend
npm run dev
```

## 5) Quick Smoke Test

1. Open `http://localhost:5173`
2. Register or log in
3. Upload a short WAV/MP3 file
4. Confirm results page loads with scores and transcript
5. Download PDF report from results page

## 6) Common Issues

- **FFmpeg not found**
  - Fix: Install FFmpeg and ensure `ffmpeg` is on PATH.

- **Module not found errors**
  - Fix: Re-run `pip install -r requirements.txt`

- **Frontend can’t reach backend**
  - Fix: Confirm backend is running on `http://localhost:8000`
  - Check CORS in `backend/app/main.py`

- **Missing ML models**
  - Fix: Run `python ml/training/train_dysarthria_model.py`

## 7) Optional: One-command Bootstrap (Windows)

If you want a guided setup script:
```powershell
.\quickstart.ps1
```
