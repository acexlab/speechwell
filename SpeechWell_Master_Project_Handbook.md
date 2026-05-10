# SpeechWell Master Project Handbook

Complete A-to-Z Mastery Guide for Project Evaluation, Viva, Technical Understanding, Debugging, Architecture, and Future Development

Generated on May 10, 2026

This handbook is written for a fresher student who must explain SpeechWell confidently in a university evaluation, viva, interview, demo, or technical walkthrough. It starts from beginner concepts, then moves into internal code behavior, architecture, ML logic, metrics, deployment, security, debugging, and future improvements.

Important disclaimer: SpeechWell is an assistive speech analysis and training platform. It produces software-based indicators such as probability, risk, fluency, and quality scores. These are not medical diagnoses. A licensed speech-language pathologist or clinician is required for clinical diagnosis.

## 1. Project Overview

### 1.1 Project Goal

SpeechWell is a full-stack AI speech improvement platform. The project helps a user upload or record speech audio, analyzes the speech for dysarthria-like patterns, stuttering/disfluency, grammar quality, and articulation-risk signals, then generates results, history, reports, dashboards, video practice, and guided training workflows.

Beginner explanation: The project listens to a speech recording, converts it into text and numbers, uses algorithms to judge speech quality indicators, and shows the user a readable report.

Technical explanation: SpeechWell combines a React/Vite frontend, a FastAPI backend, SQLite persistence, audio preprocessing with FFmpeg/librosa/soundfile, transcription with Whisper, acoustic feature extraction, scikit-learn dysarthria classification, rule-based stuttering/phonological scoring, LLM-assisted grammar correction, ReportLab PDF generation, and JWT authentication.

### 1.2 Real-World Problem Solved

Many people want feedback on speech clarity, fluency, pacing, grammar, and articulation practice, but expert feedback is not always available immediately. SpeechWell provides an accessible first layer of analysis and practice support.

Real-world use cases:

- A student practicing presentation speech.
- A person monitoring fluency over repeated recordings.
- A speech therapy learner practicing exercises between sessions.
- A teacher or evaluator reviewing a project that combines AI, web development, databases, and deployment.
- A demo showing how speech audio can become structured metrics.

### 1.3 Target Users

- Users who want speech feedback.
- Students and freshers learning AI web application architecture.
- Speech therapy learners needing guided practice.
- Project evaluators looking for full-stack and ML integration.

### 1.4 Why This Project Matters

SpeechWell matters because it integrates several industry-relevant skills:

- User authentication and session management.
- File upload and browser microphone recording.
- REST API design.
- Audio preprocessing.
- Machine learning inference.
- Rule-based signal interpretation.
- Database persistence.
- PDF report generation.
- Deployment with Vercel and Docker-friendly backend hosting.
- Human-readable explanations of AI outputs.

### 1.5 End-to-End Workflow

```text
User records/uploads audio
        |
        v
React frontend validates file and sends request
        |
        v
FastAPI backend stores original file
        |
        v
FFmpeg converts audio to mono 16 kHz WAV
        |
        v
Whisper transcribes speech and extracts timing
        |
        v
Raw audio features and acoustic embeddings are extracted
        |
        v
Dysarthria, stuttering, grammar, and phonological modules run
        |
        v
Scores are saved in SQLite
        |
        v
PDF report is generated
        |
        v
Frontend displays results, dashboard, history, reports, and training options
```

## 2. Complete Architecture

### 2.1 High-Level Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                       Browser User                         │
│  Upload page, dashboard, reports, therapy videos, AI chat   │
└─────────────────────────────┬──────────────────────────────┘
                              │ HTTP/JSON/FormData
                              v
┌────────────────────────────────────────────────────────────┐
│                    React + Vite Frontend                   │
│ App.tsx routes, pages, components, api.ts, CSS modules      │
└─────────────────────────────┬──────────────────────────────┘
                              │ REST API
                              v
┌────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                       │
│ main.py endpoints, services, auth, database, report logic   │
└───────────────┬───────────────────┬────────────────────────┘
                │                   │
                v                   v
┌─────────────────────────┐ ┌────────────────────────────────┐
│ SQLite / SQLAlchemy     │ │ ML + Audio Processing           │
│ users, analyses,        │ │ Whisper, raw features,          │
│ training sessions,      │ │ dysarthria model, stuttering,   │
│ progress                │ │ grammar, phonology              │
└─────────────────────────┘ └────────────────────────────────┘
                │                   │
                v                   v
┌─────────────────────────┐ ┌────────────────────────────────┐
│ Runtime Storage         │ │ Generated Reports               │
│ uploaded audio,         │ │ ReportLab PDF files             │
│ processed WAV files     │ │                                │
└─────────────────────────┘ └────────────────────────────────┘
```

### 2.2 Frontend Architecture

The frontend is a Single Page Application. A Single Page Application means the browser loads one main HTML page, then React changes what the user sees without reloading the whole browser page.

Main responsibilities:

- Route URLs to pages.
- Show login/register/dashboard/upload/history/results/training/chat screens.
- Manage local UI state with React hooks.
- Validate forms and files before API calls.
- Use `api.ts` to communicate with backend.
- Store auth token in browser `localStorage`.
- Use `sessionStorage` for temporary values such as latest audio id.
- Use browser `MediaRecorder` for microphone recording.
- Use CSS files for styling and responsiveness.

### 2.3 Backend Architecture

The backend is an API server. It does not render pages. It receives requests, runs logic, and returns JSON or PDF files.

Main responsibilities:

- User registration/login.
- JWT token verification.
- Audio upload processing.
- Audio normalization.
- ML pipeline orchestration.
- Database writes and reads.
- Report generation.
- Training session lifecycle.
- AI chat response generation.

### 2.4 Database Architecture

The database is accessed through SQLAlchemy. SQLAlchemy lets Python classes represent database tables.

Tables:

- `users`: account and profile information.
- `analyses`: speech analysis results.
- `training_sessions`: individual exercise attempts.
- `training_progress`: summary progress per user and module.

### 2.5 AI/ML Architecture

The ML system is modular:

- Whisper: speech-to-text and timing.
- Raw audio feature extraction: waveform, spectral, MFCC, and statistical features.
- Wav2Vec2 embedding: 768-dimensional acoustic vector fallback/legacy support.
- Dysarthria classifier: saved scikit-learn model artifacts.
- Symptom gate: rule-based guardrail around dysarthria probability.
- Stuttering estimator: repetitions, prolongations, blocks, pause variability, rate variability.
- Grammar estimator: model correction plus structural scoring.
- Phonological estimator: fragment and articulation-instability proxy.

### 2.6 Request-Response Lifecycle

Example: audio upload.

```text
1. User clicks Upload or Stop Recording.
2. Upload.tsx creates a File object.
3. api.ts creates FormData.
4. XMLHttpRequest sends POST /api/analyze.
5. FastAPI receives UploadFile.
6. Backend writes original file.
7. Backend normalizes to WAV.
8. run_full_analysis executes ML services.
9. Backend stores Analysis row.
10. Backend creates PDF report.
11. Backend returns AnalysisDetailResponse JSON.
12. Upload page redirects to Results page.
13. Results page fetches by audio_id.
14. UI displays the analysis.
```

## 3. Folder-by-Folder Explanation

### 3.1 Repository Root

Purpose: contains project-level configs, docs, Docker deployment, generated reports, database, and the main subprojects.

Important files:

- `README.md`: main documentation.
- `requirements.txt`: Python dependencies.
- `Dockerfile`: backend container.
- `render.yaml`: Render deployment blueprint.
- `vercel.json`: frontend deployment configuration.
- `.env` and `.env.example`: environment variables.
- `speechwell.db`: local SQLite database.
- generated PDF/DOCX/Markdown reports.

What breaks if removed: root configs control deployment, environment setup, and documentation. Removing them makes the project harder to run and deploy.

### 3.2 `backend/`

Purpose: backend application code. It contains the FastAPI app, database models, schemas, paths, and services.

Depends on:

- FastAPI
- SQLAlchemy
- Pydantic
- ReportLab
- ML modules under `ml/`
- FFmpeg installed on system/container

What breaks if removed: no API, no authentication, no analysis, no reports, no database access.

### 3.3 `backend/app/`

Purpose: actual backend package imported as `backend.app.main:app`.

Important files:

- `main.py`: API entrypoint.
- `schemas.py`: request and response models.
- `paths.py`: canonical filesystem paths.
- `database/`: DB engine and ORM classes.
- `services/`: business logic.

### 3.4 `backend/app/services/`

Purpose: separates domain logic from route functions.

Services:

- `auth_service.py`: password hashing and JWT.
- `dysarthria_inference_service.py`: dysarthria model loading and inference.
- `stuttering_service.py`: disfluency estimation.
- `grammar_service.py`: grammar correction and scoring.
- `phonological_service.py`: articulation-risk proxy.
- `score_service.py`: shared scoring formulas.
- `pdf_report_service.py`: PDF rendering.
- `training_catalog.py`: exercise definitions.
- `training_service.py`: training attempt evaluation.
- `chat_service.py`: AI speech coach.
- `whisper_service.py`: older/simple wrapper.
- `acoustic_service.py`: acoustic helper service.

Why it exists: route functions stay readable. Each service can be tested and explained independently.

### 3.5 `ml/`

Purpose: ML and audio-processing layer.

Contains:

- `feature_extraction/`: Whisper, Wav2Vec2, raw audio features.
- `services/`: ML orchestration.
- `training/`: dataset building and model training.
- `evaluation/`: model validation and plots.
- `models/`: saved `.pkl` artifacts.
- `dysarthria_pipeline_config.py`: shared feature/model paths.

What breaks if removed: speech analysis cannot run.

### 3.6 `speechwell-frontend/`

Purpose: React frontend.

Contains:

- `src/pages/`: screens.
- `src/components/`: reusable UI components.
- `src/api/api.ts`: backend client.
- `src/styles/`: CSS files.
- `src/utils/`: helper utilities.
- `src/data/`: practice videos.

What breaks if removed: users cannot interact with the app visually.

### 3.7 `scripts/`

Purpose: report/document generation scripts and helper automation.

Important scripts:

- `render_markdown_pdf.py`: converts Markdown to PDF with ReportLab.
- `generate_comprehensive_guide.py`: earlier PDF generator.
- `render_markdown_to_docx.py`: Markdown to DOCX.
- update/render scripts for technical reports.

What breaks if removed: app runtime may still work, but project documentation/report-generation workflow becomes weaker.

### 3.8 `.github/`

Purpose: CI/CD workflows.

Examples:

- frontend build checks.
- GitHub Pages deployment workflow.

What breaks if removed: automated checks and publishing disappear.

### 3.9 `storage/`

Purpose: runtime storage for uploaded audio, processed audio, and generated reports.

What breaks if removed: backend may recreate folders, but existing uploads/reports are lost.

## 4. File-by-File Explanation

### 4.1 Root Files

`README.md`: Explains the project, architecture, module flow, algorithms, deployment, and scoring logic. Evaluators often read this first.

`requirements.txt`: Lists backend and ML Python packages. This file is used by Docker and local setup.

`Dockerfile`: Builds a Python 3.11 backend image, installs FFmpeg/libsndfile, installs requirements, copies backend and ML code, creates storage folders, and starts Uvicorn.

`render.yaml`: Render blueprint. It defines a web service, Docker environment, health check path, persistent disk, and environment variables.

`vercel.json`: Tells Vercel how to build the Vite frontend from the subfolder and rewrite SPA routes to `index.html`.

`.env.example`: Shows which environment variables must be configured.

### 4.2 Backend Core Files

`backend/app/main.py`: The most important backend file. It creates the FastAPI app, configures CORS, creates database tables, performs SQLite compatibility migrations, defines dependencies, normalizes audio, and declares all API routes.

`backend/app/schemas.py`: Defines Pydantic models. Pydantic validates incoming data and shapes outgoing JSON. Example: `UserRegister` requires `email`, `password`, and `password_confirm`.

`backend/app/paths.py`: Centralizes paths for project root, ML model paths, database path, uploaded audio, processed audio, and reports. This avoids hardcoding paths everywhere.

`backend/app/database/db.py`: Creates SQLAlchemy engine and session factory. The `SessionLocal` object is used by request handlers to talk to the database.

`backend/app/database/models.py`: Defines database tables as Python classes. `Analysis.overall_score` is a computed property based on dysarthria, stuttering, and grammar.

### 4.3 Backend Service Files

`auth_service.py`: Hashes passwords using PBKDF2-SHA256 and verifies JWT tokens. It also includes fallback JWT creation/verification when `python-jose` is unavailable.

`score_service.py`: Contains shared formulas for grammar quality, overall score, word counts, probability clamping, and percent display.

`dysarthria_inference_service.py`: Loads latest or legacy dysarthria artifacts, extracts/sanitizes features, computes raw model probability, applies symptom gating, and returns label/probability/explanation.

`stuttering_service.py`: Counts repetitions, prolongations, blocks, severe blocks, pause variability, rate variability, and combines them into `stuttering_probability`.

`grammar_service.py`: Corrects transcript using OpenAI, Gemini, or Ollama if configured, then estimates grammar-error probability from diff and structural rules.

`phonological_service.py`: Estimates articulation/phonological risk from transcript fragments, repaired words, elongated spellings, slow short segments, and segment-rate instability.

`pdf_report_service.py`: Uses low-level ReportLab canvas drawing to render a polished clinical-style analysis PDF.

`training_catalog.py`: Static list of training modules and exercises.

`training_service.py`: Evaluates training attempts for accuracy, fluency, confidence, and feedback.

`chat_service.py`: Multi-provider AI chat service with off-topic guardrails and local fallback coaching.

`whisper_service.py`: Simple wrapper around Whisper/audio analysis, kept for compatibility.

### 4.4 ML Files

`ml/services/speech_analysis_service.py`: Orchestrates the full analysis pipeline.

`ml/feature_extraction/extract_whisper.py`: Loads Whisper, transcribes audio, calculates timing, segment, pause, and speaking-rate features.

`ml/feature_extraction/raw_audio_features.py`: Extracts waveform, spectral, chroma, contrast, MFCC, delta, and delta-delta features.

`ml/feature_extraction/extract_acoustic.py`: Extracts Wav2Vec2 embeddings, or returns a zero vector if local model files are unavailable.

`ml/dysarthria_pipeline_config.py`: Defines saved model paths and the exact numeric feature columns expected by the dysarthria model.

`ml/training/*.py`: Build datasets and train dysarthria models.

`ml/evaluation/*.py`: Validate models, generate learning curves, compare classifiers, and plot metrics.

### 4.5 Frontend Core Files

`speechwell-frontend/src/App.tsx`: Registers routes and applies the stored visual theme.

`speechwell-frontend/src/api/api.ts`: Central frontend API client. Every backend call should go through this file.

`speechwell-frontend/src/main.tsx`: React entrypoint that mounts the app.

`speechwell-frontend/src/index.css` and `App.css`: global styles and layout behavior.

### 4.6 Frontend Pages

`Landing.tsx`: Public landing page that introduces the app.

`Login.tsx`: Login form with email/password validation and token storage.

`Register.tsx`: Registration form with password matching and basic validation.

`Dashboard.tsx`: Aggregates analysis history into metrics, charts, streaks, and practice activity.

`Upload.tsx`: Drag/drop file upload and live microphone recording page.

`Results.tsx`: Fetches one analysis and renders detailed output interpretation.

`History.tsx`: Lists analysis records, filters by date/severity, opens results, downloads PDFs.

`Profile.tsx`: User profile view/edit screen.

`AIChat.tsx`: Chat interface for SpeechWell coaching.

`TherapyHub.tsx`: Video practice page using embedded YouTube videos and local access counts.

`TrainingModule.tsx`, `TrainingExercise.tsx`, `TrainingResult.tsx`: Guided exercise pages. Some current UI routing focuses more on video sessions, but backend support for structured exercises exists.

### 4.7 Frontend Components and Utilities

`Navbar.tsx`: Top navigation.

`Sidebar.tsx`: App navigation sidebar.

`InteractiveButton.tsx`: Reusable button.

`LoadingState.tsx`: Loading indicator.

`RefreshButton.tsx`: Refresh control.

`ProgressBar.tsx`: Visual percentage bar.

`TrainingModuleCard.tsx`: Training module preview.

`VideoCard.tsx` and `VideoGrid.tsx`: Practice video display.

`IntroAnimation.tsx`: First-session intro animation.

`utils/theme.ts`: Reads and applies selected theme.

`utils/youtube.ts`: Extracts YouTube video IDs, thumbnails, and embed URLs.

`utils/videoAnalytics.ts`: Stores video-open counts in localStorage.

## 5. Section-by-Section Code Explanation

### 5.1 React Hooks

React hooks are functions that let a component remember state or run side effects.

Examples:

- `useState`: stores values such as `loading`, `error`, `selectedFile`.
- `useEffect`: runs code when a component loads or dependencies change.
- `useRef`: stores mutable browser objects such as `MediaRecorder` without causing re-render.
- `useMemo`: recalculates expensive derived data only when dependencies change.

In `Upload.tsx`, `useRef` holds `mediaRecorderRef`, `mediaStreamRef`, and `recordedChunksRef`. These are not normal display values; they are live browser objects. Using refs prevents unnecessary rendering.

### 5.2 Upload Page Runtime Behavior

When user drags a file:

1. `handleDrag` prevents browser default behavior.
2. `handleDrop` gets file from `dataTransfer`.
3. `validateAndSetFile` checks MIME type, extension, and max 50 MB size.
4. If valid, `selectedFile` is updated.
5. User clicks Analyze.
6. `analyzeFile` calls `uploadAndAnalyzeAudio`.
7. Progress is shown from XHR upload events.
8. On success, audio id is stored in `sessionStorage`.
9. User is navigated to `/results?audioId=...`.

What happens if validation is removed: invalid file types or very large files may reach the backend, causing conversion failures, memory pressure, slow processing, or poor user experience.

### 5.3 Results Page Runtime Behavior

The Results page finds `audioId` from three possible places:

- navigation state
- URL query parameter
- `sessionStorage`

This makes the page more resilient. If a user refreshes the page, the query or session value still identifies the analysis.

Then:

1. `getAnalysisResult(audioId)` fetches backend data.
2. State is updated with analysis.
3. UI computes risk tones and descriptions.
4. Download PDF calls `downloadReport`.
5. Share uses `navigator.clipboard`.

### 5.4 Backend `main.py` Sections

Important sections:

- Imports and warning filters: keep startup quiet.
- Path setup: ensures project root is importable.
- Environment loading: loads `.env` if `python-dotenv` exists.
- FastAPI app creation.
- CORS setup: allows frontend origin.
- `Base.metadata.create_all`: creates missing database tables.
- SQLite compatibility functions: add missing columns for older DB files.
- Storage folder creation.
- Dependency `get_db`: opens/closes DB session per request.
- Dependency `get_current_user`: decodes bearer token.
- `normalize_audio`: runs FFmpeg.
- Route definitions.

Beginner concept: A dependency in FastAPI is a function that FastAPI automatically calls before a route. Here `get_db` gives each route a database connection.

### 5.5 `POST /api/analyze` Internal Flow

The route:

1. Receives `UploadFile`.
2. Checks filename and extension.
3. Generates a unique `audio_id`.
4. Saves original file.
5. Creates processed WAV path.
6. Calls `normalize_audio`.
7. Calls `run_full_analysis`.
8. Extracts sub-results.
9. Creates an `Analysis` database object.
10. Generates a report filename.
11. Calls `generate_pdf_report`.
12. Saves PDF path/report filename.
13. Commits database transaction.
14. Returns a Pydantic response.

If one part fails, the route can mark status as failed or raise HTTP errors.

### 5.6 Pydantic Schemas

Pydantic models define the shape of data. Example:

```python
class UserLogin(BaseModel):
    email: str
    password: str
```

This means FastAPI expects JSON containing an email and password. If fields are missing or wrong type, FastAPI returns validation errors automatically.

Industry relevance: schemas are contracts between frontend and backend.

### 5.7 SQLAlchemy ORM Classes

An ORM class maps Python attributes to database columns.

Example:

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
```

Meaning:

- `users` is the table name.
- `id` is primary key.
- `email` must be unique.
- index improves lookup speed for login.

## 6. Frontend Masterclass

### 6.1 Routing

`App.tsx` uses `BrowserRouter`, `Routes`, and `Route`.

Route examples:

- `/`: Landing.
- `/login`: Login page.
- `/dashboard`: Dashboard.
- `/upload`: Upload analysis.
- `/history`: Analysis history.
- `/results`: Analysis result.
- `/therapy-hub`: Practice videos.
- `/ai-chat`: AI coach.

Why routing exists: users need different screens without separate HTML files.

### 6.2 State Management

This project uses local component state rather than Redux or Zustand. That is appropriate because most state is page-specific.

Examples:

- Login stores email/password/error/loading.
- Upload stores selectedFile/isRecording/uploadProgress.
- Results stores analysis/loading/error.
- Dashboard stores history/period/pagination.

Alternative: Redux/Zustand would be useful if many distant components needed shared state.

### 6.3 API Integration

All API functions are in `api.ts`. This is good architecture because:

- backend URL is defined once.
- request/response types are centralized.
- auth header logic is reused.
- pages remain cleaner.

`fetch` is used for JSON requests. `XMLHttpRequest` is used for upload progress because native `fetch` upload progress is still not straightforward in browsers.

### 6.4 Form Handling and Validation

Frontend validation examples:

- Login checks empty fields and email format.
- Register checks email, password length, and matching password.
- Upload checks allowed audio extension and file size.
- TrainingExercise checks text answer or recorded audio before submit.

Frontend validation improves UX, but backend validation is still required because users can bypass frontend code.

### 6.5 Error Handling

Pattern:

```text
try API call
    update success state
catch error
    show readable message
finally
    stop loading state
```

This prevents the UI from staying stuck in loading mode.

### 6.6 Rendering Lifecycle

When a React component first appears:

1. Initial state values are used.
2. JSX renders.
3. `useEffect` runs after render.
4. API call begins.
5. Loading state is visible.
6. API returns.
7. `setState` triggers re-render.
8. Final data UI appears.

### 6.7 Styling System

The project uses CSS files by feature/page:

- `auth.css`
- `dashboard.css`
- `history.css`
- `results.css`
- `training.css`
- `upload.css`
- etc.

This helps keep styles near their feature. The project also includes Tailwind in dependencies, but the current UI is primarily custom CSS.

## 7. Backend Masterclass

### 7.1 Server Architecture

FastAPI creates an ASGI application. Uvicorn runs it.

Key beginner terms:

- HTTP request: message from browser to server.
- Route/endpoint: URL + method handled by a function.
- JSON: common data format for API responses.
- Middleware: logic that runs around requests.
- CORS: browser security rule controlling which frontend origin may call backend.

### 7.2 Middleware

CORS middleware allows frontend origins like:

- `http://localhost:5173`
- `http://localhost:3000`
- production domains configured by `CORS_ORIGINS`

Without CORS, the browser may block frontend requests even if backend is running.

### 7.3 Controllers vs Services

This project does not use a separate controller folder. Route functions in `main.py` act as controllers. Service files contain reusable business logic.

Example:

- Controller: `analyze_and_classify` receives request and returns response.
- Service: `run_full_analysis` performs ML analysis.

### 7.4 Authentication

Register:

```text
frontend sends email/password/password_confirm
backend verifies passwords match
backend checks email uniqueness
backend hashes password
backend saves user
backend creates JWT
backend returns token and user info
```

Login:

```text
frontend sends email/password
backend finds user by email
backend verifies password hash
backend creates JWT
frontend stores token
```

Protected request:

```text
Authorization: Bearer <token>
```

Backend extracts token, verifies it, reads `sub`, and finds the user.

### 7.5 Password Hashing

The project uses PBKDF2-SHA256:

```text
hash = PBKDF2(password, salt, 100000 rounds)
stored = pbkdf2_sha256$100000$salt$digest
```

Why not store raw password: if the database leaks, attackers should not see actual passwords.

Why salt exists: the same password should not produce the same stored value for every user.

### 7.6 Error Handling

Backend uses:

- `HTTPException` for expected API errors.
- try/except around provider calls and ML modules.
- fallback values when non-critical analysis modules fail.

Good evaluator answer: "The design favors graceful degradation. If grammar provider fails, the whole speech analysis does not collapse; a fallback grammar result is returned."

## 8. Database Masterclass

### 8.1 ER Diagram

```text
┌──────────────┐          ┌────────────────┐
│ users        │ 1      * │ analyses       │
│ id PK        ├─────────▶│ id PK          │
│ email        │          │ user_id FK     │
│ password     │          │ audio_id       │
│ profile      │          │ transcript     │
└──────┬───────┘          │ scores         │
       │                  │ file paths     │
       │                  └────────────────┘
       │
       │ 1      *
       v
┌──────────────────┐       ┌───────────────────┐
│ training_sessions│       │ training_progress │
│ id PK            │       │ id PK             │
│ user_id FK       │       │ user_id FK        │
│ module/exercise  │       │ module_key        │
│ scores/feedback  │       │ averages/best     │
└──────────────────┘       └───────────────────┘
```

### 8.2 Why Each Table Exists

`users`: identity and ownership.

`analyses`: permanent record of speech analysis outputs and report path.

`training_sessions`: each practice attempt.

`training_progress`: summary table for fast dashboard display.

### 8.3 Relationships

One user can have many analyses. One user can have many training sessions. One user can have many progress rows, one per module.

### 8.4 Indexing

Indexes exist on:

- user id
- email
- audio id
- module key
- exercise key

Why: queries like "find user by email" and "find analysis by audio_id" should be fast.

### 8.5 Normalization

The schema is mostly normalized:

- user info stored once.
- analysis rows reference user id.
- training rows reference user id.

Some fields like PDF path and report filename are stored directly because they are runtime artifacts tied to one analysis.

## 9. AI/ML/Data Processing Masterclass

### 9.1 Audio Preprocessing

The backend uses FFmpeg:

```text
ffmpeg -y -i input -ac 1 -ar 16000 output.wav
```

Meaning:

- `-y`: overwrite output if exists.
- `-i`: input file.
- `-ac 1`: mono.
- `-ar 16000`: 16 kHz sample rate.

Why 16 kHz: many speech ML models are trained or commonly used with 16 kHz audio.

### 9.2 Whisper

Whisper converts speech audio to text. SpeechWell uses it for:

- transcript
- word count
- segment timings
- speaking rate
- pauses
- duration

If Whisper cannot load, the app returns empty transcription features rather than crashing.

### 9.3 Pause Detection

The code first tries waveform-based pause detection using `librosa.effects.split`. This detects non-silent intervals. Gaps between intervals become pauses.

Formula:

```text
pause = current_non_silent_start - previous_non_silent_end
```

Why waveform pause detection is useful: Whisper segments can be continuous even when real waveform pauses exist.

### 9.4 Raw Audio Features

Raw features are numerical descriptions of the sound wave.

Important formulas:

```text
RMS = sqrt(mean(signal^2))
Silence ratio = count(abs(signal) < 0.01) / total samples
ZCR = sign changes / adjacent sample pairs
Power spectrum = abs(FFT(signal))^2
Centroid = sum(frequency * power) / sum(power)
Bandwidth = sqrt(sum((frequency - centroid)^2 * power) / sum(power))
Flatness = geometric_mean(power) / arithmetic_mean(power)
```

### 9.5 MFCC Features

MFCC means Mel-Frequency Cepstral Coefficients. Beginner explanation: MFCCs are compact numbers describing the shape of speech sound. They are widely used in speech recognition and speaker/audio classification.

SpeechWell computes 13 MFCCs plus:

- mean
- standard deviation
- delta
- delta-delta

Why delta matters: speech is dynamic. Not only the sound shape, but how the sound changes over time can indicate speech patterns.

### 9.6 Dysarthria Model

The dysarthria model estimates the probability that the audio belongs to the dysarthria class.

But SpeechWell does not trust probability alone. It applies a symptom gate.

Symptom score:

```text
score starts at 0
if rms < 0.01: score += 1
if silence_ratio > 0.45: score += 1
if flatness > 0.22: score += 1
if zcr < 0.03 or zcr > 0.18: score += 1
if mean(MFCC stds and MFCC delta stds) > 14.0: score += 1
```

Decision:

```text
if symptom_score <= 1:
    label = healthy
elif raw_probability >= 0.95 and symptom_score >= 2:
    label = dysarthria
elif final_probability >= 0.75 and symptom_score >= 2:
    label = dysarthria
else:
    label = healthy
```

### 9.7 What 40 Percent Dysarthria Means

`40% dysarthria` means:

```text
dysarthria_probability = 0.40
display = round(0.40 * 100)
```

It does not mean "the person has 40 percent disease." It means the model output and guardrails produced a 0.40 risk score for this recording.

Good ranges for project explanation:

- 0-29 percent: low risk signal.
- 30-59 percent: mixed/moderate signal.
- 60-74 percent: elevated signal but below main gated threshold.
- 75 percent or above with symptom score at least 2: stronger positive decision.

Best viva answer: "The percentage is a probability-like model confidence/risk indicator for the dysarthria class on this specific audio sample. It is not a clinical diagnosis. Our implementation also uses a symptom gate, so final label depends on both model probability and acoustic symptom evidence."

### 9.8 Stuttering/Disfluency Score

Stuttering probability combines event scores:

```text
stuttering_probability =
    repetition_score * 0.28
  + prolongation_score * 0.24
  + block_score * 0.26
  + severe_block_bonus * 0.08
  + pause_variability * 0.09
  + segment_rate_variability * 0.03
  + speaking_rate_penalty * 0.02
```

`40% disfluency` means `stuttering_probability = 0.40`. It means moderate evidence of disfluency events such as repeated words, long pauses, prolongations, and unstable pacing.

### 9.9 Grammar Score

Grammar module returns:

- `grammar_error_probability`: error/risk value where higher is worse.
- `grammar_quality_score`: quality value where higher is better.
- `corrected_text`: improved transcript.
- `error_count_estimate`: estimated number of issues.

Formula summary:

```text
grammar_quality_score = 1.0 - grammar_error_probability
```

If grammar quality is 0.80, display is 80 percent clarity.

### 9.10 Phonological Score

Phonological score is not a true clinical phoneme alignment. It is a proxy based on transcript symptoms:

```text
phonological_error_probability =
    fragment_ratio * 0.35
  + repair_ratio * 0.30
  + elongation_ratio * 0.15
  + segment_instability * 0.10
  + slow_segment_ratio * 0.10
```

### 9.11 Overall Score

```text
pronunciation = (1 - dysarthria_probability) * 100
fluency = (1 - stuttering_probability) * 100
clarity = grammar_score * 100

weighted_average =
    pronunciation * 0.35
  + fluency * 0.25
  + clarity * 0.40

weakest_skill = min(pronunciation, fluency, clarity)

overall_score =
    weighted_average * 0.70
  + weakest_skill * 0.30
```

Why weakest skill is included: it prevents one very weak skill from being hidden by two strong skills.

## 10. Complete Data Flow Walkthrough

### 10.1 User Click to UI

User selects a file or records audio. React stores it in state.

```text
selectedFile = File object
isUploading = false
uploadProgress = 0
```

### 10.2 UI to API

`api.ts` creates:

```text
FormData:
    file = selected audio
Headers:
    Authorization = Bearer token, if logged in
```

### 10.3 API to Backend

FastAPI receives multipart form data. `UploadFile` streams file contents.

### 10.4 Backend to Filesystem

Original file goes to uploaded-audio storage. Converted WAV goes to processed-audio storage.

### 10.5 Backend to ML

`run_full_analysis` executes modules in sequence:

```text
Whisper -> Grammar -> Acoustic embedding -> Dysarthria -> Stuttering -> Phonology
```

### 10.6 Backend to Database

An `Analysis` object is created and committed.

### 10.7 Backend to PDF

`generate_pdf_report` draws report sections and writes a PDF file.

### 10.8 Response to Frontend

Backend returns JSON. Frontend navigates to Results page.

### 10.9 Loading and Errors

Loading states prevent user confusion. Errors are shown when:

- file invalid
- microphone denied
- backend down
- analysis id missing
- report not found
- API provider unavailable

## 11. Technology Stack Explanation

### 11.1 React

What: JavaScript library for building UI components.

Why used: good for interactive dashboards, forms, route-based pages, and reusable components.

Alternative: Vue, Angular, Svelte.

### 11.2 Vite

What: frontend build tool and dev server.

Why used: fast development and optimized builds.

Alternative: Webpack, Parcel, Next.js.

### 11.3 TypeScript

What: JavaScript with static types.

Why used: catches type mistakes and documents API shapes.

### 11.4 FastAPI

What: modern Python web framework.

Why used: fast API development, automatic validation, Pydantic integration, async support, automatic OpenAPI docs.

Alternative: Flask, Django REST Framework, Express.

### 11.5 SQLite and SQLAlchemy

SQLite is a file-based database. SQLAlchemy is a Python ORM.

Why used: simple local development and enough for a student project.

Production alternative: PostgreSQL.

### 11.6 Whisper

What: speech recognition model.

Why used: turns audio into transcript and segment timings.

### 11.7 librosa and soundfile

Used for waveform loading, duration, silence splitting, and signal features.

### 11.8 scikit-learn

Used for dysarthria model training/inference artifacts.

### 11.9 ReportLab

Used for PDF report generation.

### 11.10 Docker

Packages backend, dependencies, FFmpeg, and runtime command into a deployable container.

### 11.11 Vercel and Render

Vercel hosts the frontend. Render can host the Docker backend with persistent disk.

## 12. Deployment and DevOps

### 12.1 Local Development

Backend:

```text
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```text
cd speechwell-frontend
npm install
npm run dev
```

### 12.2 Frontend Build

```text
npm run build
```

This runs TypeScript build and Vite production build.

### 12.3 Docker Backend

Dockerfile steps:

1. Start from Python 3.11 slim.
2. Set environment variables.
3. Install FFmpeg and libsndfile.
4. Install Python requirements.
5. Copy backend and ML folders.
6. Create persistent storage folders.
7. Run Uvicorn.

### 12.4 Environment Variables

Important variables:

- `SECRET_KEY`: JWT signing key.
- `CORS_ORIGINS`: frontend domains allowed to call backend.
- `VITE_API_URL`: backend URL for frontend.
- `SPEECHWELL_DATA_DIR`: storage/database base.
- `SPEECHWELL_STORAGE_DIR`: audio/report storage.
- `SQLITE_DB_PATH`: database file path.
- `WHISPER_MODEL`: transcription model.
- `CHAT_PROVIDER`: chat provider mode.
- `GRAMMAR_PROVIDER`: grammar provider mode.
- `OPENAI_API_KEY`, `GEMINI_API_KEY`: optional provider keys.

### 12.5 Scaling

Current design is suitable for demos and small usage. Scaling improvements:

- PostgreSQL instead of SQLite.
- Object storage for audio/PDFs.
- Background jobs for long ML inference.
- Separate ML worker service.
- Redis queue.
- Model caching and warm startup.
- Horizontal backend replicas.

## 13. Security Analysis

### 13.1 JWT Security

JWT contains signed claims. The backend verifies signature and expiry.

Risk: default `SECRET_KEY` must never be used in production.

Improvement: set strong random secret and rotate periodically.

### 13.2 Password Security

PBKDF2 with salt prevents raw password storage.

Improvement: Argon2id or bcrypt with strong configuration.

### 13.3 SQL Injection

SQLAlchemy ORM reduces SQL injection risk because queries are parameterized. Direct raw SQL is used only for SQLite schema compatibility and uses controlled table/column names from code, not user input.

### 13.4 XSS

React escapes text by default. Avoid rendering raw HTML from transcripts or AI responses.

### 13.5 CSRF

The app uses bearer tokens in Authorization headers, which reduces classic cookie-based CSRF exposure. If cookies are introduced later, CSRF protection should be added.

### 13.6 File Upload Security

Current controls:

- frontend extension/type/size checks.
- backend file handling.
- FFmpeg normalization.

Improvements:

- enforce backend file size limit.
- scan file MIME server-side.
- store files outside public web root.
- rate-limit uploads.

## 14. Performance Optimization

### 14.1 Frontend

Current optimizations:

- page-level state.
- `useMemo` in dashboard for derived metrics.
- Vite optimized build.

Possible improvements:

- lazy-load pages.
- virtualize long tables.
- memoize large chart components.
- compress CSS.
- use service workers for assets.

### 14.2 Backend

Current concerns:

- ML inference can be slow.
- Whisper loads model lazily.
- PDF generation runs in request path.

Improvements:

- background task queue.
- async job status endpoint.
- cache loaded models at process startup.
- separate inference worker.

### 14.3 Database

Current SQLite is fine for local/demo.

Improvements:

- PostgreSQL.
- indexes for date/user queries.
- pagination at database level.
- migrations with Alembic.

### 14.4 AI/ML

Improvements:

- smaller/faster Whisper model for speed.
- GPU inference.
- batch processing.
- quantized models.
- separate model server.

## 15. Project Evaluation Preparation

### 15.1 Architecture Questions

Question: What is SpeechWell?

Beginner answer: SpeechWell is a web app that analyzes speech recordings and gives feedback about speech health, fluency, grammar, and practice.

Professional answer: SpeechWell is a full-stack React/FastAPI speech analysis platform integrating audio preprocessing, ASR, acoustic feature extraction, ML classification, rule-based scoring, persistence, reports, and training workflows.

Advanced answer: It is a modular AI-assisted speech analytics system where the frontend handles capture and presentation, FastAPI orchestrates authenticated APIs and persistence, and the ML layer separates ASR, raw signal features, dysarthria classification with symptom gating, disfluency scoring, grammar correction, and articulation proxies.

Question: Why separate frontend and backend?

Beginner answer: The frontend shows pages. The backend does heavy processing.

Professional answer: React handles UX while FastAPI handles secure APIs, file processing, database access, and ML inference.

Advanced answer: Separation enables independent deployment, scaling, security boundaries, and replacement of ML services without rewriting UI code.

### 15.2 Backend Questions

Question: What does `main.py` do?

Beginner answer: It starts the backend and defines API routes.

Professional answer: It configures FastAPI, CORS, database setup, auth dependencies, audio normalization, analysis endpoints, report endpoints, training endpoints, and chat endpoint.

Advanced answer: It acts as the orchestration layer. It keeps request handling, dependency injection, persistence, schema responses, compatibility migrations, and service calls in one API entrypoint.

Question: Why use FastAPI?

Beginner answer: It makes Python APIs easy.

Professional answer: FastAPI provides typed request validation, automatic docs, dependency injection, async support, and good performance.

Advanced answer: It fits ML-backed APIs well because Python ML libraries can be called directly while preserving strong schema contracts through Pydantic.

### 15.3 Frontend Questions

Question: How does the upload page work?

Beginner answer: It lets the user choose or record audio and sends it to the backend.

Professional answer: `Upload.tsx` validates file type and size, records audio with MediaRecorder, sends FormData through `api.ts`, tracks XHR progress, stores audio id, and navigates to results.

Advanced answer: It combines browser file APIs, drag-drop events, media stream lifecycle cleanup, controlled error/loading states, and REST upload progress tracking.

### 15.4 AI/ML Questions

Question: What does 40 percent dysarthria mean?

Beginner answer: It means the system found some dysarthria-like signal, but not necessarily a diagnosis.

Professional answer: It is a probability-like risk score from the dysarthria model for that recording. The final label also depends on symptom gate rules.

Advanced answer: It represents the classifier's calibrated/probabilistic confidence after feature processing and guardrail adjustment. In this codebase, strong positive labeling requires both sufficient probability and acoustic symptom evidence, so 40 percent is usually interpreted as below the positive threshold.

Question: Why use symptom gating?

Beginner answer: To avoid false alarms.

Professional answer: It reduces false positives when model probability is high but actual acoustic symptoms are weak.

Advanced answer: It is a hybrid ML + rules guardrail that improves real-world robustness under accent mismatch, noise, short recordings, or unseen speakers.

### 15.5 Database Questions

Question: Why use SQLite?

Beginner answer: It is simple and works as one file.

Professional answer: SQLite is easy for local development and student projects because it requires no separate database server.

Advanced answer: SQLite is acceptable for prototype/demo scale, but production multi-user scaling should move to PostgreSQL with migrations, backups, and connection pooling.

### 15.6 Security Questions

Question: How are passwords protected?

Beginner answer: The app stores a hash, not the real password.

Professional answer: Passwords are salted and hashed with PBKDF2-SHA256 before storage.

Advanced answer: The implementation uses 100,000 PBKDF2 rounds with random salt and constant-time comparison; production could upgrade to Argon2id and enforce stronger password policy.

## 16. How to Present the Project

### 16.1 Opening Script

"SpeechWell is an AI-assisted speech analysis and training platform. It allows users to upload or record speech, then analyzes dysarthria risk, stuttering/disfluency, grammar clarity, and articulation-risk signals. The project combines React, FastAPI, SQLite, Whisper, acoustic signal processing, scikit-learn models, rule-based scoring, PDF reporting, and guided practice modules."

### 16.2 Architecture Explanation Script

"The frontend is built with React and Vite. It handles routing, forms, microphone recording, dashboards, reports, and practice videos. All API calls go through `api.ts`. The backend is FastAPI. It handles authentication, file upload, audio normalization, ML analysis, database storage, report generation, training evaluation, and chat. The ML layer is separated under `ml/`, where Whisper extracts transcript and timing, raw audio features feed the dysarthria model, and service modules calculate stuttering, grammar, and phonological indicators."

### 16.3 Demo Flow

Recommended demo:

1. Show landing page.
2. Login/register.
3. Open dashboard.
4. Upload or record speech.
5. Show progress.
6. Open results.
7. Explain each score.
8. Download PDF report.
9. Show history.
10. Show video practice / AI coach.

### 16.4 How to Answer Difficult Questions

If asked "Is this medically accurate?", answer:

"It is not a medical diagnosis. It is an assistive screening and practice tool. The project clearly treats outputs as probability-like indicators and includes a disclaimer. Clinical confirmation requires a qualified professional."

If asked "Why not use only deep learning?", answer:

"Because in real-world projects, hybrid systems are often more explainable and robust. Whisper handles ASR, ML handles dysarthria probability, and rule-based modules expose understandable evidence like pauses, repetitions, and grammar changes."

## 17. Debugging and Troubleshooting

### 17.1 Backend Not Starting

Check:

- Python environment active.
- dependencies installed.
- correct working directory.
- `uvicorn backend.app.main:app` command.
- missing FFmpeg.
- import path errors.

### 17.2 Frontend Cannot Call Backend

Check:

- backend running on correct port.
- `VITE_API_URL`.
- CORS origins.
- browser console network tab.
- backend `/api/health`.

### 17.3 Upload Fails

Check:

- file extension.
- file size.
- FFmpeg installed.
- storage directories writable.
- backend logs for normalization error.

### 17.4 Whisper Fails

Check:

- `openai-whisper` installed.
- model can download or exists locally.
- enough memory.
- audio is valid WAV after normalization.

### 17.5 Dysarthria Model Fails

Check:

- model `.pkl` files exist.
- feature columns match.
- scikit-learn/joblib versions.
- raw audio feature extraction works.

### 17.6 Grammar/Chat Provider Fails

Check:

- `GRAMMAR_PROVIDER` or `CHAT_PROVIDER`.
- Ollama server running.
- OpenAI/Gemini API key.
- network connectivity.
- provider quota/rate limits.

### 17.7 PDF Report Missing

Check:

- ReportLab installed.
- report directory writable.
- analysis row has `pdf_path` and `report_filename`.
- `/api/reports/{audio_id}` finds the file.

## 18. Future Improvements

### 18.1 Scalability

- Move from SQLite to PostgreSQL.
- Use S3-compatible object storage for audio/PDFs.
- Add Celery/RQ background workers.
- Add job status endpoints.
- Split ML inference into a separate microservice.

### 18.2 AI Improvements

- Train larger balanced dysarthria dataset.
- Use speaker-independent validation.
- Add confidence calibration.
- Add phoneme-level forced alignment.
- Add multilingual support.
- Add trend-based interpretation over many recordings.

### 18.3 Security Upgrades

- Strong password policy.
- Argon2id password hashing.
- Rate limiting.
- Virus scanning for uploaded files.
- Secure audit logs.
- OAuth login.
- Role-based access control.

### 18.4 Product Improvements

- Personalized therapy plans.
- Clinician dashboard.
- Exercise scheduling.
- Push/email reminders.
- Exportable progress reports.
- Mobile app.

## 19. Visual Learning Materials

### 19.1 Sequence Diagram: Analysis

```text
User -> Upload.tsx: select/record file
Upload.tsx -> api.ts: uploadAndAnalyzeAudio(file)
api.ts -> FastAPI: POST /api/analyze FormData
FastAPI -> filesystem: save original audio
FastAPI -> FFmpeg: normalize to WAV
FastAPI -> speech_analysis_service: run_full_analysis(path)
speech_analysis_service -> Whisper: transcript/timing
speech_analysis_service -> raw_audio_features: features
speech_analysis_service -> dysarthria_service: probability + label
speech_analysis_service -> stuttering_service: disfluency score
speech_analysis_service -> grammar_service: corrected text + grammar score
speech_analysis_service -> phonological_service: articulation proxy
FastAPI -> SQLite: save Analysis
FastAPI -> pdf_report_service: generate PDF
FastAPI -> api.ts: return JSON
api.ts -> Results.tsx: analysis object
Results.tsx -> User: render result cards
```

### 19.2 API Flow Diagram

```text
Frontend Page
   |
   v
api.ts function
   |
   v
HTTP request
   |
   v
FastAPI route
   |
   v
Service function
   |
   v
Database / ML / Filesystem
   |
   v
Pydantic response
   |
   v
Frontend state update
```

### 19.3 Folder Structure Diagram

```text
SpeechWell/
├── backend/
│   └── app/
│       ├── main.py
│       ├── schemas.py
│       ├── paths.py
│       ├── database/
│       └── services/
├── ml/
│   ├── feature_extraction/
│   ├── services/
│   ├── training/
│   ├── evaluation/
│   └── models/
├── speechwell-frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── api/
│       ├── utils/
│       ├── data/
│       └── styles/
├── scripts/
├── storage/
├── Dockerfile
├── render.yaml
├── vercel.json
└── requirements.txt
```

## 20. Final Revision Section

### 20.1 Quick Revision Notes

- SpeechWell is a React + FastAPI + ML speech analysis platform.
- Frontend captures files/audio and displays results.
- Backend authenticates users, processes uploads, runs ML, stores results, and generates PDFs.
- Database stores users, analyses, training sessions, and progress.
- Whisper provides transcript and timing.
- Raw audio features provide energy, silence, spectral, and MFCC values.
- Dysarthria model output is probability-like and guarded by symptom evidence.
- Stuttering score uses repetitions, prolongations, pauses, blocks, and variability.
- Grammar score uses correction plus structural rules.
- Phonology score is a proxy, not clinical phoneme diagnosis.
- Overall score combines pronunciation, fluency, clarity, and weakest skill.

### 20.2 Important Keywords

- ASR: automatic speech recognition.
- JWT: signed access token.
- ORM: object-relational mapper.
- Pydantic: request/response validation.
- CORS: browser origin access control.
- RMS: audio energy.
- ZCR: zero crossing rate.
- MFCC: speech spectral feature.
- Inference: using a trained model to predict.
- Threshold: cutoff for decision.
- Precision: how many positive predictions were correct.
- Recall: how many actual positives were found.
- F1 score: balance of precision and recall.

### 20.3 Viva Cheat Sheet

Best one-line explanation:

"SpeechWell is an AI-assisted speech analysis and training platform that converts user speech audio into transcript, acoustic features, ML/rule-based speech indicators, saved history, PDF reports, dashboards, and guided practice."

Best architecture answer:

"It has a React frontend, FastAPI backend, SQLite database, ML/audio-processing layer, and deployment configs for Vercel plus Docker backend hosting."

Best AI output answer:

"The percentages are probability-like indicators for a specific recording, not medical diagnoses. The dysarthria label depends on both model probability and symptom-gated acoustic evidence."

Best security answer:

"Passwords are hashed, tokens are signed, API requests use bearer auth, SQLAlchemy reduces injection risk, and CORS controls frontend origins."

Best future scope answer:

"I would move SQLite to PostgreSQL, add background ML jobs, use object storage, improve phoneme-level analysis, add clinician dashboards, and introduce production monitoring and rate limiting."

### 20.4 Last-Minute Demo Checklist

- Backend running.
- Frontend running.
- `/api/health` returns ok.
- Upload sample audio ready.
- Login credentials ready.
- PDF report download works.
- Explain one score clearly.
- Show database/history persistence.
- Mention limitations honestly.
- End with future improvements.

## 21. Rebuild Plan for a Student

To rebuild this project independently:

1. Create React/Vite frontend.
2. Add routes and pages.
3. Build auth forms.
4. Build upload page with file input first.
5. Add microphone recording with MediaRecorder.
6. Create FastAPI backend.
7. Add SQLite and SQLAlchemy models.
8. Add auth with password hashing and JWT.
9. Add audio upload endpoint.
10. Add FFmpeg normalization.
11. Add Whisper transcription.
12. Add raw audio feature extraction.
13. Train or load dysarthria classifier.
14. Add stuttering/grammar/phonology services.
15. Save results to database.
16. Add results/history pages.
17. Generate PDF reports.
18. Add training module.
19. Add AI chat.
20. Add deployment configs.

This is the mental model: build from UI to API to database to ML to report, then polish with dashboard, training, security, deployment, and documentation.
