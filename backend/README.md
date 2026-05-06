# Backend

This folder contains the FastAPI application, persistence layer, and runtime services.

## Active ML Connection

The backend does not hardcode the current dysarthria production model path directly.

It resolves the active model through:

- `backend/app/paths.py`
- `ml/dysarthria_pipeline_config.py`

Runtime dysarthria inference is handled by:

- `backend/app/services/dysarthria_inference_service.py`

## Request Flow

Frontend upload:

- `speechwell-frontend/src/api/api.ts` -> `POST /api/analyze`

Backend handler:

- `backend/app/main.py`

ML orchestration:

- `ml/services/speech_analysis_service.py`

## Start Command

```powershell
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```
