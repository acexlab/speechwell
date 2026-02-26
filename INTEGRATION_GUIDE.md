<!-- File Logic Summary: Integration documentation describing how frontend, backend, and ML components connect. -->

# SpeechWell - Complete Backend & Frontend Integration Guide

## Overview
The entire SpeechWell application has been connected end-to-end with:
- **ML Pipeline**: Audio → Whisper → Dysarthria/Stuttering/Grammar/Phonological Detection
- **Backend API**: FastAPI with authentication, database persistence, and PDF report generation
- **Frontend**: React/TypeScript with real API integration across all pages
- **Database**: SQLite with User and Analysis models

---

## Installation & Setup

### Step 1: Install Backend Dependencies

```bash
cd <project-root>
pip install -r requirements.txt
```

**Key Dependencies Installed:**
- `fastapi` & `uvicorn` - Backend framework
- `torch` & `transformers` - ML models (Whisper, WAV2Vec2, Grammar)
- `joblib` & `scikit-learn` - ML model inference
- `librosa` & `soundfile` - Audio processing
- `reportlab` - PDF generation
- `passlib` & `python-jose` - Authentication

### Step 2: Verify ML Models Are Present

Check that these files exist in `ml/models/`:
```
dysarthria_model_v1.pkl
dysarthria_pca_v1.pkl
dysarthria_scaler_v1.pkl
speechwell_classifier.pkl
```

**If models are missing**, train them:
```bash
python ml/training/train_dysarthria_model.py
```

### Step 3: Start the Backend API

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Install Frontend Dependencies

```bash
cd speechwell-frontend
npm install
```

### Step 5: Start the Frontend

```bash
npm run dev
```

**Expected output:**
```
  VITE v4.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
```

---

## System Architecture

### Audio Processing Pipeline

```
User Upload (3MB MP3)
    ↓
FFmpeg Normalization (16kHz mono)
    ↓
Whisper Model (Transcription + Fluency)
    ↓
┌─────────────────────────────────┐
│  Parallel Analysis              │
├─────────────────────────────────┤
│ • WAV2Vec2 (Acoustic Embedding) │
│ • Dysarthria Classifier         │
│ • Stuttering Detection          │
│ • Grammar Error Detection       │
│ • Phonological Analysis         │
└─────────────────────────────────┘
    ↓
Database Storage + PDF Generation
    ↓
Results Display in Frontend
```

### Database Schema

**Users Table:**
```sql
id, email (unique), password_hash, full_name, created_at, updated_at
```

**Analyses Table:**
```sql
id, user_id, audio_id, filename, transcript
dysarthria_probability, dysarthria_label
stuttering_probability, stuttering_repetitions, stuttering_prolongations, stuttering_blocks
grammar_score, grammar_error_count, corrected_text
phonological_score, phonological_error_count
speaking_rate_wps, average_pause_sec, max_pause_sec, total_duration_sec
pdf_path, audio_path, status
created_at, updated_at
```

### API Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

#### Analysis
- `POST /api/analyze` - Upload and analyze audio
- `GET /api/analyze/{audio_id}` - Get detailed analysis results
- `GET /api/analyses` - Get user's analysis history

#### Reports
- `GET /api/reports/{audio_id}` - Download PDF report

#### Health
- `GET /api/health` - Health check

---

## Frontend Components Connected

### 1. Landing Page (`Landing.tsx`)
- ✅ Hero section with call-to-action
- ✅ Auth-aware "Start Analysis" button

### 2. Authentication (`Login.tsx`, `Register.tsx`)
- ✅ Connected to `/api/auth/login` and `/api/auth/register`
- ✅ Token storage in localStorage
- ✅ Automatic redirect to dashboard on success

### 3. Dashboard (`Dashboard.tsx`)
- ✅ Fetches user's analysis history from API
- ✅ Calculates real statistics (avg dysarthria, stuttering, grammar)
- ✅ Displays recent analyses in paginated table
- ✅ Click "View Report" to navigate to results

### 4. Upload (`Upload.tsx`)
- ✅ Drag-and-drop file upload
- ✅ Real-time progress tracking via XHR
- ✅ Connected to `POST /api/analyze`
- ✅ Automatic navigation to results on completion
- ⏳ Live recording (UI ready, needs Web Audio API implementation)

### 5. Results (`Results.tsx`)
- ✅ Fetches detailed analysis from `/api/analyze/{audioId}`
- ✅ Displays circular SVG progress chart
- ✅ Shows dysarthria, stuttering, grammar, and speech metrics
- ✅ Download PDF report functionality
- ✅ Share analysis results

### 6. History (`History.tsx`)
- ✅ Lists all analyses with date range filtering
- ✅ Filter by severity (High/Moderate/Low)
- ✅ Pagination with customizable rows per page
- ✅ View full report for any analysis

### 7. Therapy Hub (`TherapyHub.tsx`)
- ✅ Exercise library with category filtering
- ⏳ Exercise implementation pending

---

## Key Features & ML Models

### 1. Dysarthria Detection
**Model**: `dysarthria_model_v1.pkl` (trained classifier)
**Inputs**: Fluency metrics (speaking rate, pause duration) + Acoustic features (WAV2Vec2 embedding)
**Output**: Probability score (0-1) and label (dysarthria/healthy)

### 2. Stuttering Detection
**Algorithm**: Pattern matching + statistical analysis
**Detects**: Repetitions, prolongations, blocks
**Output**: Probability score + detailed metrics

### 3. Grammar Error Detection
**Model**: Hugging Face `prithivida/grammar_error_correcter_v1`
**Output**: Error probability, corrected text, error count estimate

### 4. Phonological Error Detection
**Algorithm**: CMU Pronouncing + phonological rules
**Output**: Error probability, affected words list

### 5. Acoustic Analysis
**Model**: Facebook WAV2Vec2
**Output**: 768-dimensional acoustic embedding for dysarthria classification

---

## Testing the Pipeline

### Test 1: Register and Login
1. Go to `http://localhost:5173/register`
2. Register with: `test@example.com` / `password123`
3. You'll be auto-redirected to `/dashboard`
4. Verify token stored in localStorage

### Test 2: Upload and Analyze
1. Go to `/upload`
2. Upload a test audio file (WAV or MP3)
3. Watch progress bar update in real-time
4. Results page should display after analysis completes
5. Check that all ML scores are populated

### Test 3: View History
1. Go to `/history`
2. See list of all your analyses
3. Filter by date range and severity
4. Click "View Report" on any analysis

### Test 4: Download PDF
1. From results page, click "Download PDF"
2. PDF should contain full clinical report with:
   - Patient metrics
   - Dysarthria/Stuttering/Grammar scores with severity levels
   - Original and corrected transcripts
   - Speech timing analysis

---

## Database Management

### View Database Contents
```bash
# Open SQLite browser
sqlite3 speechwell.db

# View tables
.tables

# View users
SELECT * FROM users;

# View analyses
SELECT id, audio_id, filename, dysarthria_probability, stuttering_probability, created_at FROM analyses;
```

### Reset Database
```bash
# Delete database
rm speechwell.db

# Recreate empty database on next API run
# Tables will be created automatically
```

---

## Troubleshooting

### Issue: "Module not found: transformers"
**Solution**: `pip install transformers --no-cache-dir`

### Issue: CUDA out of memory
**Solution**: Models run on CPU. Set `device=-1` in services:
```python
device=-1  # CPU mode
```

### Issue: "No speech detected in audio"
**Solution**: Audio must be:
- Minimum 3 seconds
- Clear speech (not music/noise)
- 16kHz mono preferred

### Issue: Frontend can't connect to backend
**Solution**: Check:
1. Backend running on `http://localhost:8000`
2. CORS is enabled (should be automatic)
3. Check browser console for errors

### Issue: PDF download fails
**Solution**: Check `storage/reports/` exists and has write permissions

---

## Performance Optimization

### For Production Deployment
1. Remove `--reload` from uvicorn (production should use gunicorn/hypercorn)
2. Set `fp16=True` in Whisper for faster inference
3. Use PostgreSQL instead of SQLite
4. Implement audio file caching
5. Add result caching in Redis

### Estimated Inference Times (First Run)
- Whisper loading: ~3-5 seconds
- Whisper transcription (20s audio): ~5-10 seconds
- Grammar correction: ~2-3 seconds
- Dysarthria prediction: ~1 second
- **Total**: ~10-20 seconds per analysis

---

## Next Steps & Enhancements

### High Priority
1. ✅ ML Model Integration - DONE
2. ✅ Backend API - DONE
3. ✅ Frontend Connection - DONE
4. ⏳ **Web Audio API for Live Recording** - Upload page ready, needs implementation
5. ⏳ **PDF Export Optimization** - Works, needs styling improvements

### Medium Priority
1. Add user profile page
2. Add individual report detail view
3. Implement sharing functionality (email/social)
4. Add export to CSV functionality
5. Implement result comparison (before/after)

### Low Priority
1. Add data visualization dashboard
2. Implement chatbot for guidance
3. Add therapy exercise gamification
4. Multi-language support
5. Mobile app development

---

## File Structure

```
backend/
├── app/
│   ├── main.py (API endpoints)
│   ├── schemas.py (Request/Response models)
│   ├── database/
│   │   ├── db.py (Database config)
│   │   └── models.py (User, Analysis tables)
│   └── services/
│       ├── auth_service.py (JWT auth)
│       ├── whisper_service.py (Transcription)
│       ├── dysarthria_inference_service.py (ML model)
│       ├── stuttering_service.py (Analysis)
│       ├── grammar_service.py (Analysis)
│       ├── phonological_service.py (Analysis)
│       ├── pdf_report_service.py (Report generation)
│       └── acoustic_service.py (Audio embedding)

ml/
├── models/ (Trained ML models)
├── training/ (Training scripts)
└── feature_extraction/ (Feature extraction)

speechwell-frontend/
├── src/
│   ├── api/
│   │   └── api.ts (API client with all endpoints)
│   ├── pages/
│   │   ├── Landing.tsx
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx (Real data)
│   │   ├── Upload.tsx (Real upload)
│   │   ├── Results.tsx (Real results)
│   │   ├── History.tsx (Real history)
│   │   └── TherapyHub.tsx
│   ├── components/
│   │   ├── Sidebar.tsx
│   │   └── Navbar.tsx
│   └── styles/ (CSS files for each page)

storage/
├── uploaded_audio/ (User uploads)
├── processed_audio/ (Normalized audio)
└── reports/ (Generated PDFs)
```

---

## API Response Examples

### POST /api/analyze (Success)
```json
{
  "id": 1,
  "audio_id": "abc123...",
  "filename": "speech_sample.wav",
  "dysarthria_probability": 0.39,
  "dysarthria_label": "dysarthria",
  "stuttering_probability": 0.24,
  "stuttering_repetitions": 4,
  "stuttering_prolongations": 2,
  "stuttering_blocks": 1,
  "grammar_score": 0.84,
  "grammar_error_count": 3,
  "phonological_score": 0.12,
  "phonological_error_count": 1,
  "speaking_rate_wps": 3.2,
  "average_pause_sec": 0.45,
  "max_pause_sec": 2.1,
  "total_duration_sec": 23.5,
  "status": "completed",
  "created_at": "2026-02-21T15:30:00Z"
}
```

### GET /api/analyses (Success)
```json
[
  {
    "id": 1,
    "audio_id": "abc123...",
    "filename": "speech_sample.wav",
    "dysarthria_probability": 0.39,
    "stuttering_probability": 0.24,
    "grammar_score": 0.84,
    "created_at": "2026-02-21T15:30:00Z"
  }
]
```

---

## Security Notes

⚠️ **For Development Only:**
- Secret key is hardcoded (change in production)
- CORS allows all origins (restrict in production)
- No rate limiting (implement in production)

✅ **For Production:**
```python
# Update in auth_service.py
SECRET_KEY = os.getenv("SECRET_KEY")  # Load from environment

# Update CORS in main.py
allow_origins=["https://yourdomain.com"]  # Restrict to your domain
```

---

## Support & Debugging

1. **Check logs**: Both frontend and backend output logs to console
2. **Database inspection**: Use SQLite browser to inspect data
3. **API testing**: Use Postman/Insomnia to test endpoints directly
4. **Performance**: Check browser DevTools Network tab for API latency

---

Created: February 2026
Version: 1.0 - Complete Integration

