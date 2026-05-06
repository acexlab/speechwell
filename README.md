<!-- File Logic Summary: Project-level documentation for SpeechWell covering architecture, module integration, algorithms, formulas, data flow, and current implementation behavior. -->

# SpeechWell

SpeechWell is a React + FastAPI speech improvement platform with two connected layers:

- `Speech Analysis`
  - upload or record speech, run analysis, save results, generate reports
- `Guided Speech Training Module`
  - structured practice sessions for breath, articulation, fluency, and grammar

This README documents how the modules connect, how each one works, and the exact scoring logic currently implemented in the codebase.

---

## 1. System Overview

SpeechWell is built from:

- Frontend: `speechwell-frontend/`
  - React + Vite
  - routes, dashboards, training UI, embedded video practice, theme system
- Backend: `backend/app/`
  - FastAPI
  - auth, profile, analysis APIs, training APIs, persistence
- ML / speech logic: `ml/` and `backend/app/services/`
  - Whisper transcript + timing features
  - acoustic features / embeddings
  - dysarthria classifier
  - rule-based fluency / phonology logic
  - grammar improvement through configured provider or local Ollama
- Database: SQLite
  - user records
  - analysis records
  - training sessions
  - training progress

---

## Deployment Notes

The deployable web app lives in `speechwell-frontend/`. The FastAPI + ML backend is intentionally kept separate because it depends on Python audio/ML packages, FFmpeg, model files, runtime storage, and SQLite state.

### Vercel frontend

This repo includes a root `vercel.json` so Vercel can be connected directly to the GitHub repository:

- Build command: `cd speechwell-frontend && npm run build`
- Install command: `cd speechwell-frontend && npm ci`
- Output directory: `speechwell-frontend/dist`
- SPA routes rewrite to `index.html`

Set this Vercel environment variable for production:

```text
VITE_API_URL=https://your-backend-api.example.com
```

### GitHub workflows

Two workflows are included:

- `.github/workflows/frontend-build.yml` checks install, lint, and build on pushes/PRs.
- `.github/workflows/github-pages.yml` publishes the Vite frontend to GitHub Pages from `main`.

### Backend deployment

Deploy the backend to a Docker-friendly host such as Render, Railway, Fly.io, a VM, or a container platform. This repository includes:

- `Dockerfile`
- `.dockerignore`
- `render.yaml`
- `backend/DEPLOYMENT.md`

Recommended Render flow:

1. Push this repo to GitHub.
2. In Render, create a new Blueprint from the repository.
3. Render reads `render.yaml`, builds the Docker backend, and attaches a persistent `/var/data` disk.
4. Configure:

```text
CORS_ORIGINS=https://your-vercel-app.vercel.app,https://your-github-username.github.io
```

5. After Render gives you the backend URL, set this in Vercel:

```text
VITE_API_URL=https://your-render-service.onrender.com
```

6. Redeploy the Vercel frontend.

Large local artifacts are excluded from future commits/deployments through `.gitignore` and `.vercelignore`, including `ml/datasets/`, virtual environments, SQLite files, generated PDFs/DOCX files, and runtime storage.

---

## 2. Core Modules

SpeechWell now has 4 practical runtime modules:

1. `Authentication + User Context`
2. `Speech Analysis Pipeline`
3. `Guided Speech Training Module`
4. `Progress, Reporting, and Frontend Presentation`

---

## 3. Module 1: Authentication + User Context

### Purpose

This module identifies the user and connects both analysis history and training progress to the same account.

### Main files

- `backend/app/main.py`
- `backend/app/services/auth_service.py`
- `backend/app/database/models.py`
- `speechwell-frontend/src/api/api.ts`

### Flow

1. user registers or logs in
2. backend returns JWT bearer token
3. frontend stores token in `localStorage`
4. every protected request sends `Authorization: Bearer <token>`
5. backend resolves the current user through `get_current_user()`

### Connected features

The same authenticated user is used for:

- analysis upload ownership
- results/history/report access
- training session ownership
- training progress summaries
- profile and theme preferences

So the training module is not a separate app. It is attached directly to the same user context already used by the analysis system.

---

## 4. Module 2: Speech Analysis Pipeline

### Purpose

This module accepts an uploaded or recorded speech sample and computes:

- dysarthria probability
- stuttering probability
- grammar error probability
- phonological error probability
- transcript and timing metrics

### Main files

- `backend/app/main.py`
- `ml/services/speech_analysis_service.py`
- `ml/feature_extraction/extract_whisper.py`
- `ml/feature_extraction/extract_acoustic.py`
- `backend/app/services/dysarthria_inference_service.py`
- `backend/app/services/stuttering_service.py`
- `backend/app/services/grammar_service.py`
- `backend/app/services/phonological_service.py`
- `backend/app/services/pdf_report_service.py`

### End-to-end request flow

1. frontend sends `POST /api/analyze`
2. backend validates file format
3. backend stores original upload
4. backend normalizes audio with FFmpeg to mono 16kHz WAV
5. backend calls `run_full_analysis(...)`
6. pipeline builds transcript, acoustic features, and speech metrics
7. dysarthria / stuttering / grammar / phonology outputs are calculated
8. result is saved in `analyses`
9. PDF report is generated
10. frontend loads the result page and dashboard views

---

## 5. Analysis Algorithms and Equations

## 5.1 Audio normalization

File:

- `backend/app/main.py`

Operation:

```text
ffmpeg -i input -ac 1 -ar 16000 output.wav
```

Why:

- standardizes sample rate
- standardizes channel count
- reduces downstream model input variation

## 5.2 Transcript and timing features

File:

- `ml/feature_extraction/extract_whisper.py`

Model:

- Whisper `base`

Outputs:

- transcript
- segment timestamps
- word count
- speaking rate
- pause metrics
- total duration

### Equations

Let:

- `W = total number of transcript words`
- `T = speaking duration in seconds`
- `pause_i = start_i - end_(i-1)` for each positive pause

Then:

```text
speaking_rate_wps = W / T
average_pause_sec = mean(pause_i)
max_pause_sec = max(pause_i)
total_duration_sec = total audio duration
```

## 5.3 Acoustic embedding extraction

File:

- `ml/feature_extraction/extract_acoustic.py`

Model:

- `facebook/wav2vec2-base`

Steps:

1. load waveform
2. convert to mono if needed
3. resample to 16kHz
4. run Wav2Vec2
5. mean-pool hidden states

Output:

- 768-dimensional acoustic embedding

## 5.4 Dysarthria inference

File:

- `backend/app/services/dysarthria_inference_service.py`

Inputs:

- fluency features:
  - `speaking_rate_wps`
  - `average_pause_sec`
  - `max_pause_sec`
- acoustic embedding

Artifacts:

- scaler
- PCA transform
- logistic regression model

### Logic

```text
X_fluency = [speaking_rate_wps, average_pause_sec, max_pause_sec]
X_acoustic_scaled = scaler.transform(acoustic_embedding)
X_acoustic_pca = pca.transform(X_acoustic_scaled)
X = concat(X_fluency, X_acoustic_pca)
p_dys = model.predict_proba(X)[0][1]
label = "dysarthria" if p_dys >= 0.5 else "healthy"
```

## 5.5 Stuttering probability

File:

- `backend/app/services/stuttering_service.py`

Signals used:

- consecutive repeated words
- prolongations through character repetition
- long inter-segment gaps treated as blocks

### Equations

```text
repetitions = count(words[i] == words[i-1])
prolongations = count(regex "(.)\1{3,}")
blocks = count(segment_gap >= 1.0 sec)

raw_stutter = 0.4 * repetitions + 0.4 * prolongations + 0.2 * blocks
stuttering_probability = min(raw_stutter / 5, 1.0)
```

## 5.6 Grammar analysis

File:

- `backend/app/services/grammar_service.py`
- `backend/app/services/score_service.py`
- `backend/app/main.py`

Current behavior:

- corrects transcript using configured provider
- provider can be local Ollama or configured remote provider
- estimates grammar-error probability from original vs corrected text
- converts that error probability into a positive grammar quality score before persistence

### Equations

```text
error_estimate = token-level difference between original and corrected text
structural_error_probability =
  min(
    0.08 * fragment_count +
    0.05 * repeated_word_count +
    0.04 * odd_token_count +
    0.02 * lowercase_sentence_restart_count,
    1.0
  )

grammar_error_probability =
  max(
    min(error_estimate / max(total_words, 1), 1.0),
    structural_error_probability
  )

grammar_quality_score = 1.0 - grammar_error_probability
```

Persisted analysis meaning:

- DB field name remains `grammar_score`
- stored meaning is now `grammar_quality_score`
- higher is better
- `grammar_error_count` remains the raw count signal
- `grammar_error_probability` is derived when needed for results, chat, and documentation

Code path:

```text
transcript
-> detect_grammar_errors()
-> estimate_grammar_metrics()
-> grammar_error_probability
-> grammar_quality_score = 1 - grammar_error_probability
-> analyses.grammar_score
```

Why this changed:

- the earlier implementation relied too heavily on `original vs corrected` text diff
- if the grammar model returned a transcript very close to the original, clearly poor transcript structure could still produce `0` estimated errors
- fragmented or noisy transcripts could therefore receive an unrealistically high clarity score
- the current implementation now combines:
  - correction diff signal
  - fragment detection
  - repeated-word signal
  - malformed token signal
  - sentence restart/casing signal

## 5.7 Phonological error probability

File:

- `backend/app/services/phonological_service.py`

Method:

- rule-based phoneme substitution checks using pronunciation lookup

### Equation

```text
phonological_error_probability = min(error_count / max(word_count, 1), 1.0)
```

## 5.8 Overall analysis score

File:

- `backend/app/services/score_service.py`

### Equation

```text
overall_score =
round(
  0.7 * weighted_average +
  0.3 * weakest_skill
)

where

pronunciation = (1 - dysarthria_probability) * 100
fluency = (1 - stuttering_probability) * 100
clarity = grammar_quality_score * 100

weighted_average =
  0.35 * pronunciation +
  0.25 * fluency +
  0.40 * clarity

weakest_skill = min(pronunciation, fluency, clarity)
```

Interpretation:

- dysarthria and stuttering are risk probabilities, so lower is better
- grammar is a quality score, so higher is better
- all three are now aligned directionally before the weighted sum
- the weakest domain now pulls the total score down, so one inflated metric cannot hide a bad sample

## 5.9 Dashboard and UI metric mapping

Files:

- `speechwell-frontend/src/pages/Dashboard.tsx`
- `speechwell-frontend/src/pages/Results.tsx`

The frontend now uses the same metric direction as the backend:

```text
pronunciation = (1 - dysarthria_probability) * 100
fluency = (1 - stuttering_probability) * 100
clarity = grammar_quality_score * 100
```

Dashboard logic:

- `Pronunciation` is the average inverse dysarthria risk
- `Fluency` is the average inverse stuttering risk
- `Clarity` is the average grammar quality score
- `Recent Average Score` uses the same weighted equation as `overall_score`

Code path:

```text
analysis row
-> dysarthria_probability / stuttering_probability / grammar_score
-> dashboard aggregates
-> progress bars and trend charts
```

Results page logic:

- `Clarity Score` shows `grammar_score * 100`
- stuttering detail shows:
  - `repetitions`
  - `prolongations`
  - `blocks`
  - `Fluency Score = (1 - stuttering_probability) * 100`

Example of the fixed behavior:

- if dysarthria risk is high and the transcript is fragmented/noisy, the overall score will now fall sharply
- a transcript no longer gets `100%` clarity just because the correction model failed to rewrite it

---

## 6. Module 3: Guided Speech Training Module

### Purpose

This add-on module helps users practice speech directly inside SpeechWell instead of only uploading speech for diagnosis-style feedback.

### Integration point

Frontend route:

- `speechwell-frontend/src/pages/TherapyHub.tsx`

Backend routes:

- `GET /api/training/modules`
- `POST /api/training/session/start`
- `POST /api/training/session/evaluate`
- `GET /api/training/session/{session_id}`
- `GET /api/training/sessions`
- `GET /api/training/progress`

### How it connects to the main system

The training module reuses:

- the same logged-in user
- the same JWT auth flow
- the same database engine
- the same timing/transcript extraction style used in analysis
- the same dashboard for progress summaries

This means:

- training is attached to the same `users` table
- training progress is visible from the same app shell
- training history uses the same account identity as speech analysis history

---

## 7. Training Mini-Modules

Training catalog is defined in:

- `backend/app/services/training_catalog.py`

Current modules:

1. `breath_voice`
2. `articulation`
3. `fluency`
4. `grammar`

### 7.1 Breath & Voice Control

Exercises:

- `vowel_hold`
- `count_on_breath`
- `soft_loud_repeat`

Input:

- microphone

Focus:

- breath support
- steady sound production
- smooth voice onset

### 7.2 Articulation Practice

Exercises:

- `minimal_pairs`
- `tongue_tip_drill`
- `sentence_repeat_clear`

Input:

- microphone

Focus:

- consonant precision
- clear word production
- intelligibility

### 7.3 Fluency Training

Exercises:

- `slow_read`
- `easy_onset_phrase`
- `pause_and_continue`

Input:

- microphone

Focus:

- reduced rush
- smoother starts
- controlled pauses

### 7.4 Sentence & Grammar Practice

Exercises:

- `complete_sentence`
- `fix_and_say`
- `daily_topic`

Input:

- text input

Focus:

- sentence completion
- correction of grammar
- natural spoken sentence formation

---

## 8. Training Session Lifecycle

### Start

1. frontend loads module list from `GET /api/training/modules`
2. user selects an exercise
3. frontend calls `POST /api/training/session/start`
4. backend creates one `training_sessions` row with `status="started"`

### Evaluate

Two possible input paths:

- text response
- audio response

Frontend submits:

- `session_id`
- `transcript_text` for text exercises, or
- audio file for microphone exercises

Backend evaluates and writes:

- transcript
- accuracy score
- fluency score
- confidence score
- pause and repetition counts
- corrected text
- feedback summary
- final status

### Save progress

If a session is valid and completed:

- backend recalculates module progress
- `training_progress` is updated

If a session is invalid:

- status becomes `failed`
- progress summary is not updated

---

## 9. Training Algorithms and Equations

File:

- `backend/app/services/training_service.py`

## 9.1 Text normalization

### Function

```text
normalize_text(text)
```

Rules:

- lowercase
- remove punctuation
- collapse repeated spaces

## 9.2 Accuracy for expected-answer drills

Used when an exercise has a fixed expected text.

### Equation

```text
accuracy = matched_words / total_expected_words
```

Where:

- words are compared positionally after normalization

## 9.3 Accuracy for open-response drills

Used when `expected_text` is empty.

### Equation

```text
open_response_score = min(word_count / OPEN_RESPONSE_TARGET_WORDS, 1.0)
```

Current constant:

```text
OPEN_RESPONSE_TARGET_WORDS = 6
```

Meaning:

- longer complete responses get better completion scores
- empty or very short responses score lower

## 9.4 Repeated-word count

### Logic

Count repeated tokens when:

- current word equals previous word
- or current word equals the word two positions earlier

Used as a simple fluency/stability signal.

## 9.5 Long pause count

### Logic

Using transcript segments:

```text
long_pause_count = count(start_i - end_(i-1) >= 1.2 sec)
```

Current threshold:

```text
LONG_PAUSE_THRESHOLD_SEC = 1.2
```

## 9.6 Fluency for text drills

### Equation

```text
fluency_ratio = clamp(1.0 - repeated_word_count * 0.1, 0, 1)
```

Because text exercises do not have pause timing.

## 9.7 Fluency for audio drills

### Equation

```text
fluency_ratio = 1.0
fluency_ratio -= long_pause_count * 0.15
fluency_ratio -= repeated_word_count * 0.1
fluency_ratio = clamp(fluency_ratio, 0, 1)
```

## 9.8 Confidence score

### Base equation

```text
confidence_ratio =
min(
  1.0,
  accuracy_ratio * 0.5 +
  fluency_ratio * 0.3 +
  completion_bonus * 0.2
)
```

For grammar text exercises, confidence is then blended with grammar improvement quality:

```text
grammar_boost = 1.0 - grammar_error_probability
confidence_score = min(1.0, confidence_ratio * 0.8 + grammar_boost * 0.2)
```

## 9.9 Grammar training improvement

For grammar exercises:

- the training prompt and learner response are sent to grammar improvement logic
- this uses the configured provider, with local Ollama as the intended local-model path
- corrected output is saved as `corrected_text`

Practical flow:

```text
exercise prompt + learner answer -> grammar improvement model -> improved sentence
```

## 9.10 No-speech / no-response handling

Silent audio and empty text are now explicitly rejected in the training path.

If no speech or no answer is detected:

- `accuracy_score = 0`
- `fluency_score = 0`
- `confidence_score = 0`
- session is marked `failed`
- progress summary is not updated

This prevents empty attempts from appearing successful.

---

## 10. Training Feedback Algorithm

Training feedback is not generic anymore.

Feedback logic is module-aware and exercise-aware:

- `breath_voice`
  - emphasizes breath support, vowel steadiness, and smooth voice onset
- `articulation`
  - emphasizes consonant clarity, mouth movement, minimal pairs, tongue-tip release
- `fluency`
  - emphasizes easy onset, pacing, natural pauses, reduced repeated starts
- `grammar`
  - emphasizes complete sentence building, corrected sentence comparison, and improved output reuse

File:

- `backend/app/services/training_service.py`

This means the feedback shown after each session is tied to the specific training objective rather than using the same generic sentence for every exercise.

---

## 11. Training Progress Aggregation

File:

- `backend/app/services/training_service.py`

The progress table stores one aggregated row per user per module.

### Equations

```text
sessions_completed = count(completed sessions for user and module)
avg_accuracy = mean(session.accuracy_score)
avg_fluency = mean(session.fluency_score)
best_score = max(session.confidence_score)
```

These values feed:

- training home cards
- dashboard snapshot
- future module recommendations

---

## 12. Database Design

File:

- `backend/app/database/models.py`

### Tables

#### `users`

Stores:

- email
- password hash
- profile metadata

#### `analyses`

Stores one row per uploaded speech analysis:

- transcript
- dysarthria fields
- stuttering fields
- grammar fields
- phonology fields
- pause metrics
- audio/report paths
- status

#### `training_sessions`

Stores one row per training attempt:

- user
- module key
- exercise key
- prompt text
- expected text
- transcript
- scores
- counts
- corrected text
- feedback summary
- status

#### `training_progress`

Stores per-user per-module aggregate progress:

- sessions completed
- average accuracy
- average fluency
- best score
- last practiced time

---

## 13. Frontend Integration

### Main route wiring

File:

- `speechwell-frontend/src/App.tsx`

Training routes:

- `/therapy-hub`
- `/therapy-hub/:moduleKey`
- `/therapy-hub/:moduleKey/:exerciseKey`
- `/therapy-hub/session/:sessionId/result`

### Main training UI files

- `speechwell-frontend/src/pages/TherapyHub.tsx`
- `speechwell-frontend/src/pages/TrainingModule.tsx`
- `speechwell-frontend/src/pages/TrainingExercise.tsx`
- `speechwell-frontend/src/pages/TrainingResult.tsx`
- `speechwell-frontend/src/components/TrainingModuleCard.tsx`
- `speechwell-frontend/src/components/ProgressBar.tsx`

### Video practice integration

The Therapy Hub also contains practice videos:

- source data in `speechwell-frontend/src/data/practiceVideos.ts`
- thumbnail extraction from YouTube video IDs
- embedded video player on-page
- original URLs preserved exactly

This creates a hybrid training page:

- structured exercises from backend
- optional video-guided practice from curated YouTube links

---

## 14. Theme System

Frontend theme behavior now uses:

- `speechwell-frontend/src/utils/theme.ts`

Current themes:

- Lavender
- Ocean
- Forest
- Dark

Theme is applied through:

- `data-theme` on `document.documentElement`
- global CSS variables in `speechwell-frontend/src/index.css`

Theme can be changed from:

- navbar quick switch
- profile settings page

---

## 15. API Summary

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/profile`
- `PUT /api/profile`

### Analysis

- `POST /api/analyze`
- `GET /api/analyze/{audio_id}`
- `GET /api/analyses`
- `GET /api/reports/{audio_id}`

### Training

- `GET /api/training/modules`
- `POST /api/training/session/start`
- `POST /api/training/session/evaluate`
- `GET /api/training/session/{session_id}`
- `GET /api/training/sessions`
- `GET /api/training/progress`

### Chat

- `POST /api/chat`

### Health

- `GET /api/health`

---

## 16. Important Current Limitations

1. Analysis upload still needs stricter no-speech rejection in the main analysis path, not only the training path.
2. Stuttering repetition/prolongation detection is intentionally lightweight and transcript-driven, so it should be treated as screening logic rather than a clinical measurement.
3. Training scoring is explainable and practical, but it is still rule-based rather than a full custom local acoustic model.
4. The embedded YouTube player supports playback but does not replicate every full youtube.com feature.
5. Video pagination for long categories is not yet implemented.

---

## 17. Recommended Next Improvements

1. Add silence detection directly into the analysis upload path so empty recordings fail before scoring.
2. Introduce MFCC / mel-frequency features for training inference if moving toward a richer local speech model.
3. Add pagination for video categories at 5 videos per page.
4. Add automated tests for:
   - auth
   - upload analysis
   - training start/evaluate/result
   - theme switch persistence
5. If schema cleanup is acceptable later, rename `grammar_score` to `grammar_quality_score` in the database for even clearer semantics.

---

## 18. Practical Architecture Summary

In one sentence:

SpeechWell uses one authenticated user system, one shared frontend shell, one shared backend/API layer, and two connected speech workflows:

- `analysis workflow` for upload -> inference -> report
- `training workflow` for exercise -> evaluation -> progress

That is the core design of the project as it exists now.
