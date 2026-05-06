# SpeechWell Project Deep Learning Manual

This manual reverse-engineers the full `SpeechWell` repository for a beginner who needs to understand how the system works, how the parts connect, and how to rebuild or modify it confidently.

Two important reading notes:

1. This repository contains a mix of authored source code, generated artifacts, large datasets, dependency folders, and local runtime outputs. To keep the manual useful, every meaningful authored file is documented individually, while very large repetitive collections such as `venv/`, `node_modules/`, raw dataset WAV files, and generated report/audio outputs are documented as grouped file patterns. That still covers every folder in the repository, but avoids writing thousands of identical one-line descriptions for third-party or generated files.
2. Some project documents are older than the current runtime code. Where there is a mismatch, this manual treats the code as the source of truth. The biggest example is dysarthria model selection: many older docs describe the RF+SVC ensemble as the main model, but the live inference code now prefers `ml/models/dysarthria_best_comparison_model.pkl` when it exists.

## Requested Section Map

This deep manual follows the verified code paths in the repository, but it also maps cleanly to the learning blueprint requested for reverse-engineering:

1. Complete system overview: Section 1
2. Exact execution flow trace: Section 2
3. Folder and file deep breakdown: Section 3
4. Data flow and transformations: Section 6
5. Feature engineering logic: Section 6 plus Section 7
6. Machine learning models: Section 7
7. Algorithms and formulas: Section 8
8. Model training pipeline: Section 10
9. Module-level logic: Section 9
10. Backend internal flow: Section 5
11. Frontend and backend connection: Section 4 plus Section 5
12. Inference engine runtime flow: Section 11 plus Section 13
13. Performance evaluation: Section 12
14. Debugging and edge cases: Section 15
15. System design decisions: Section 18
16. Rebuild from scratch: Section 14
17. Interview and viva preparation: Section 17
18. Improvements and future work: Section 16

## Section 1: Project Overview

### What problem is this project solving?

SpeechWell is a speech-analysis and guided-practice application. A user uploads or records speech, and the system analyzes several dimensions of speech performance:

- dysarthria risk
- stuttering/disfluency risk
- grammar quality
- phonological/articulation instability proxy
- basic timing measures such as speaking rate and pauses

It then stores the result, generates a PDF report, shows the result in a React dashboard, and offers lightweight therapy exercises through the "Therapy Hub."

In simple terms, the project is trying to answer this question:

"Can we give a non-expert user a usable, immediate, local-first speech analysis and practice experience without needing a clinician in the loop for every step?"

### Real-world problem explanation

People with speech difficulties often face three practical problems:

1. Access is hard. Formal evaluation can be expensive, geographically difficult, or slow to schedule.
2. Practice is inconsistent. Even when exercises exist, people need reminders, structure, and feedback.
3. Raw audio is hard to interpret. A user may know they "sound off," but not whether the issue is fluency, articulation, pacing, grammar, or a combination.

SpeechWell addresses this by combining:

- a web UI for uploading and reviewing speech
- a backend API that stores user history
- speech-to-text and audio feature extraction
- dysarthria detection models
- rule-based fluency and articulation heuristics
- AI-assisted grammar correction and coaching
- a training workflow that turns results into practice sessions

This is not a medical device. The code behaves more like an educational or assistive speech analytics tool than a clinically validated diagnostic platform.

### High-level system architecture

At a high level, the system has four layers:

1. **Frontend UI** in React/Vite/TypeScript.
2. **Backend API** in FastAPI.
3. **Analysis/ML layer** in the `ml/` package plus backend service wrappers.
4. **Persistence/output layer** made of SQLite plus filesystem storage for audio and PDFs.

ASCII architecture diagram:

```text
User
  |
  v
React Frontend (speechwell-frontend)
  |
  | HTTP / JSON / multipart upload
  v
FastAPI Backend (backend/app/main.py)
  |
  |-- Auth + profile + chat routes
  |-- Analysis route
  |-- Training routes
  |
  +--> SQLite database (speechwell.db)
  +--> Filesystem storage (storage/)
  |
  +--> Speech analysis orchestration (ml/services/speech_analysis_service.py)
         |
         +--> Whisper transcription + timing features
         +--> Grammar correction / grammar scoring
         +--> Acoustic embedding extraction
         +--> Dysarthria inference
         +--> Stuttering scoring
         +--> Phonological proxy scoring
  |
  +--> PDF report generator
  |
  v
Frontend receives result and renders dashboard/history/report pages
```

### End-to-end data flow

When a user uploads audio, the real pipeline is:

1. The React frontend collects an audio file from drag-drop, file browse, or microphone recording.
2. The frontend sends the file as `multipart/form-data` to `POST /api/analyze`.
3. FastAPI validates the MIME type and extension.
4. The original upload is saved under `storage/uploaded_audio/`.
5. `ffmpeg` converts the file to mono 16 kHz WAV and saves it in `storage/processed_audio/`.
6. `ml/services/speech_analysis_service.py` runs the analysis pipeline.
7. Whisper transcribes the audio and calculates pause/speaking-rate features.
8. Grammar logic corrects the transcript and estimates grammar error probability.
9. Dysarthria inference extracts raw acoustic features, loads the active classifier, and applies symptom-gated decision logic.
10. Stuttering logic analyzes repetitions, prolongations, blocks, pause variability, and segment timing.
11. Phonological logic estimates articulation instability from transcript patterns.
12. The backend stores the result in SQLite.
13. The backend renders a PDF report into `storage/reports/`.
14. The API returns a JSON response containing the probabilities, transcript, derived metrics, and report metadata.
15. The frontend navigates to the results page and later can fetch history, reports, analytics, and training progress.

The same architecture also supports:

- user registration and login
- editable profiles
- therapy and training sessions
- AI chat coaching

## Section 2: Execution Flow Trace

This section answers the most practical reverse-engineering question in the project:

"When a real user uploads one audio file, what runs first, what runs next, which file owns the decision, and what data shape moves between each stage?"

### Call stack style flow for one uploaded audio file

```text
Browser UI
  speechwell-frontend/src/pages/Upload.tsx
    Upload.analyzeFile(file: File)
      -> uploadAndAnalyzeAudio(file, onProgress)

HTTP client
  speechwell-frontend/src/api/api.ts
    uploadAndAnalyzeAudio(...)
      -> XMLHttpRequest POST /api/analyze
      -> multipart/form-data with field name "file"

Backend entry
  backend/app/main.py
    analyze_audio(file: UploadFile, db: Session, current_user: Optional[User])
      -> validate MIME type / extension
      -> save original file to storage/uploaded_audio/
      -> create Analysis row with status="processing"
      -> normalize_audio(input_path, output_path)
           -> ffmpeg -ac 1 -ar 16000
      -> run_full_analysis(processed_audio_path)

Analysis orchestrator
  ml/services/speech_analysis_service.py
    run_full_analysis(audio_path: str)
      -> analyze_audio_features(audio_path)
           from ml/feature_extraction/extract_whisper.py
      -> detect_grammar_errors(transcript)
           from backend/app/services/grammar_service.py
      -> extract_acoustic_embedding(audio_path)
           from ml/feature_extraction/extract_acoustic.py
      -> predict_dysarthria(whisper_features, acoustic_embedding, audio_path=audio_path)
           from backend/app/services/dysarthria_inference_service.py
      -> detect_stuttering(whisper_features, audio_path=audio_path)
           from backend/app/services/stuttering_service.py
      -> detect_phonological_errors(whisper_features)
           from backend/app/services/phonological_service.py
      -> return nested result dict

Dysarthria branch
  backend/app/services/dysarthria_inference_service.py
    predict_dysarthria(...)
      -> load active artifact from ml/models/dysarthria_best_comparison_model.pkl if present
      -> extract_raw_audio_features(audio_path) for model features
      -> pipeline.predict_proba(feature_row)
      -> extract_raw_audio_features(audio_path, target_frames=None) for symptom gating
      -> compute_symptom_score(full_audio_feature_row)
      -> _apply_symptom_gated_decision(...)
      -> return label + probability + explanation + model_version

Stuttering branch
  backend/app/services/stuttering_service.py
    detect_stuttering(...)
      -> inspect transcript words, pause durations, segment rates
      -> compute heuristic sub-scores
      -> combine them into stuttering_probability

Grammar branch
  backend/app/services/grammar_service.py
    detect_grammar_errors(transcript)
      -> improve_grammar_text(...) via provider or fallback
      -> estimate_grammar_metrics(original, corrected)
      -> return corrected_text + error_count + grammar_error_probability + grammar_quality_score

Phonological branch
  backend/app/services/phonological_service.py
    detect_phonological_errors(...)
      -> inspect fragments, repairs, elongations, unstable segment pacing
      -> return proxy probability and explanation

Persist + report
  backend/app/main.py
    analyze_audio(...)
      -> write all results into Analysis ORM object
      -> generate_pdf_report(...)
           from backend/app/services/pdf_report_service.py
      -> commit transaction
      -> return JSON response

Frontend results page
  speechwell-frontend/src/pages/Results.tsx
    -> getAnalysisResult(audio_id)
    -> render charts, labels, transcript, download link
```

### Exact function-level runtime trace

1. The user clicks upload in [`speechwell-frontend/src/pages/Upload.tsx`](/c:/Users/franc/OneDrive/Documents/Projects/SpeechWell/speechwell-frontend/src/pages/Upload.tsx), which triggers `handleUpload()`.
2. `handleUpload()` calls `analyzeFile(selectedFile)`.
3. `analyzeFile()` calls `uploadAndAnalyzeAudio()` in [`speechwell-frontend/src/api/api.ts`](/c:/Users/franc/OneDrive/Documents/Projects/SpeechWell/speechwell-frontend/src/api/api.ts).
4. `uploadAndAnalyzeAudio()` creates `FormData`, appends the file under the `file` field, and sends `POST /api/analyze`.
5. FastAPI routes that request to `analyze_audio()` in [`backend/app/main.py`](/c:/Users/franc/OneDrive/Documents/Projects/SpeechWell/backend/app/main.py).
6. `analyze_audio()` saves the raw upload, inserts an `Analysis` database row, then calls `normalize_audio()`.
7. `normalize_audio()` shells out to `ffmpeg` so every downstream extractor receives mono 16 kHz WAV.
8. `analyze_audio()` then calls `run_full_analysis(processed_path)`.
9. `run_full_analysis()` first calls `analyze_audio_features()` in [`ml/feature_extraction/extract_whisper.py`](/c:/Users/franc/OneDrive/Documents/Projects/SpeechWell/ml/feature_extraction/extract_whisper.py), which returns a dictionary containing transcript text, durations, pause statistics, segment-level timing, and speaking-rate features.
10. The transcript string from that dictionary is passed into `detect_grammar_errors()`.
11. The same audio path is passed into `extract_acoustic_embedding()`, which returns a `numpy.ndarray` of length `768` if the local Wav2Vec2 model exists, otherwise a zero vector of the same length.
12. `predict_dysarthria()` receives three things: Whisper timing features, the acoustic embedding, and the normalized audio path.
13. Inside `predict_dysarthria()`, the active v2 or comparison-model pipeline usually ignores the embedding and instead extracts a fresh tabular feature row from raw audio by calling `extract_raw_audio_features()`.
14. The classifier outputs a raw dysarthria probability. That probability is then filtered through symptom-gating logic using full-audio features and healthy-signal guardrails.
15. `detect_stuttering()` uses the Whisper transcript, per-segment timing, and pause list to compute a heuristic fluency probability.
16. `detect_phonological_errors()` uses transcript artifacts and segment instability to compute an articulation-instability proxy.
17. `run_full_analysis()` returns a nested dictionary with `whisper`, `grammar`, `acoustic`, `dysarthria`, `stuttering`, and `phonological` sections.
18. `analyze_audio()` writes those values into the `Analysis` ORM row, calls `generate_pdf_report()`, commits, and returns a JSON body that includes `audio_id`, `transcript`, probabilities, scores, and report metadata.
19. The frontend stores `audio_id` in `sessionStorage`, routes to `/results`, and later fetches `GET /api/analyze/{audio_id}` for display and `GET /api/reports/{audio_id}` for PDF download.

### Data objects passed between major functions

- Frontend upload payload: browser `File` object -> `multipart/form-data`
- Backend persisted upload: original file bytes -> `storage/uploaded_audio/<uuid>_<filename>`
- Backend normalized audio: WAV file path -> `storage/processed_audio/<uuid>.wav`
- Whisper output: Python `dict` with transcript string, speaking-rate floats, pause arrays, and segment dictionaries
- Acoustic model output: `numpy.ndarray` with shape `(768,)`
- Raw dysarthria model input: single-row `pandas.DataFrame` with about `98` numeric columns used by the saved pipeline
- Database persistence object: SQLAlchemy `Analysis` instance
- API response object: JSON matching the response schema used by the React pages

### Where prediction truly happens

The most important clinical-style prediction in the repository is dysarthria inference. The final yes or no decision is not made in Whisper, not in the frontend, and not in the training scripts. It is made at runtime in [`backend/app/services/dysarthria_inference_service.py`](/c:/Users/franc/OneDrive/Documents/Projects/SpeechWell/backend/app/services/dysarthria_inference_service.py), where:

1. the saved classifier computes a raw probability,
2. the code computes a symptom score from handcrafted audio markers,
3. the code checks for strong healthy-speech signals,
4. the code applies threshold plus safety rules,
5. then the backend stores the final label and probability.

That means the true decision function is a hybrid:

```text
final_decision = model_probability + rule_based_symptom_gating + safety_guardrails
```

## Section 3: Folder and File Breakdown

### Repository tree

This tree is logic-focused. All authored files are shown explicitly. Massive repetitive collections are shown as grouped patterns with counts.

```text
SpeechWell/
|-- .git/                                  (Git metadata, 118 files)
|-- .env
|-- .env.example
|-- .gitattributes
|-- .gitignore
|-- INTEGRATION.md
|-- phase2_report_extracted.txt
|-- phase2_report_speechwell (1) on work.docx
|-- phase2_report_speechwell_final.docx
|-- PHASE2_REPORT_UPDATE_GUIDE.md
|-- PHASE2_REPORT_UPDATE_GUIDE.pdf
|-- PROJECT_LEARNING_MANUAL.md
|-- PROJECT_LEARNING_MANUAL.pdf
|-- PROJECT_STRUCTURE.md
|-- PROJECT_TECHNICAL_REPORT.md
|-- PROJECT_TECHNICAL_REPORT.pdf
|-- README.md
|-- REQUIREMENTS.md
|-- requirements.txt
|-- quickstart.ps1
|-- quickstart.sh
|-- speechwell.db                          (active runtime SQLite DB)
|-- SpeechWell_Technical_Report.pdf
|-- start_speechwell.bat
|-- backend/
|   |-- README.md
|   |-- speechwell.db                      (stale or legacy SQLite DB)
|   |-- __init__.py
|   |-- app/
|   |   |-- __init__.py
|   |   |-- main.py
|   |   |-- paths.py
|   |   |-- schemas.py
|   |   |-- database/
|   |   |   |-- __init__.py
|   |   |   |-- db.py
|   |   |   `-- models.py
|   |   `-- services/
|   |       |-- __init__.py
|   |       |-- acoustic_service.py
|   |       |-- auth_service.py
|   |       |-- chat_service.py
|   |       |-- dysarthria_inference_service.py
|   |       |-- grammar_service.py
|   |       |-- pdf_report_service.py
|   |       |-- phonological_service.py
|   |       |-- score_service.py
|   |       |-- stuttering_service.py
|   |       |-- training_catalog.py
|   |       |-- training_service.py
|   |       `-- whisper_service.py
|   `-- storage/
|       `-- uploaded_audio/
|           `-- a3f4e966-ba17-49b5-a240-0559be668b26_test1.mp3
|-- ml/
|   |-- README.md
|   |-- __init__.py
|   |-- dysarthria_pipeline_config.py
|   |-- datasets/
|   |   `-- torgo/
|   |       `-- TORGO_RAW/                (17,635 WAV files across F_Con/F_Dys/M_Con/M_Dys)
|   |-- evaluation/
|   |   |-- README.md
|   |   |-- dysarthria_model_comparison_report.json
|   |   |-- dysarthria_model_v2_report_group.json
|   |   |-- dysarthria_model_v2_rf_svc_ensemble_report.json
|   |   |-- evaluate_speechwell_multiclass.py
|   |   |-- full_dataset_final_model_curve.py
|   |   |-- full_dataset_latest_model_curve.py
|   |   |-- plot_final_metrics.py
|   |   |-- plot_model_metric_comparison.py
|   |   |-- simple_learning_curve.py
|   |   |-- speakerwise_strict_learning_curve.py
|   |   |-- v2_learning_curve.py
|   |   |-- validate_accuracy.py
|   |   |-- validation_report.json
|   |   |-- validation_report_v2_group.json
|   |   |-- validation_report_v2_rf_svc_ensemble.json
|   |   `-- learning_curves/             (CSV, JSON, and PNG training-curve outputs)
|   |-- feature_extraction/
|   |   |-- __init__.py
|   |   |-- extract_acoustic.py
|   |   |-- extract_torgo_features.py
|   |   |-- extract_whisper.py
|   |   `-- raw_audio_features.py
|   |-- models/
|   |   |-- dysarthria_best_comparison_model.pkl
|   |   |-- dysarthria_model_v1.pkl
|   |   |-- dysarthria_model_v2_group.pkl
|   |   |-- dysarthria_model_v2_rf_svc_ensemble.pkl
|   |   |-- dysarthria_pca_v1.pkl
|   |   `-- dysarthria_scaler_v1.pkl
|   |-- services/
|   |   |-- __init__.py
|   |   `-- speech_analysis_service.py
|   `-- training/
|       |-- README.md
|       |-- build_combined_dysarthria_index.py
|       |-- build_torgo_audio_features.py
|       |-- build_torgo_dataset.py
|       |-- combined_audio_features.csv
|       |-- combined_dysarthria_index.csv
|       |-- inspect_dataset.py
|       |-- torgo_audio_features_v4.csv
|       |-- torgo_features_sample.csv
|       |-- torgo_index.csv
|       |-- train_dysarthria_full.py
|       |-- train_dysarthria_model.py
|       |-- train_dysarthria_model_comparison.py
|       |-- train_dysarthria_optimized.py
|       |-- train_dysarthria_rf_svc_ensemble.py
|       `-- train_dysarthria_with_acoustics.py
|-- scripts/
|   |-- render_learning_manual_pdf.py
|   `-- render_report_pdf.py
|-- speechwell-frontend/
|   |-- README.md
|   |-- eslint.config.js
|   |-- index.html
|   |-- package-lock.json
|   |-- package.json
|   |-- tsconfig.app.json
|   |-- tsconfig.json
|   |-- tsconfig.node.json
|   |-- vite.config.ts
|   |-- public/vite.svg
|   |-- dist/                             (generated build output, 4 files)
|   |-- node_modules/                     (frontend dependencies, 6,449 files)
|   `-- src/
|       |-- App.css
|       |-- App.tsx
|       |-- index.css
|       |-- main.tsx
|       |-- api/api.ts
|       |-- assets/react.svg
|       |-- components/                   (10 reusable UI components)
|       |-- data/practiceVideos.ts
|       |-- pages/                        (13 route pages)
|       |-- styles/                       (15 CSS files)
|       `-- utils/                        (theme and YouTube helpers)
|-- storage/
|   |-- chunks/                           (currently empty)
|   |-- processed_audio/                  (normalized WAV outputs)
|   |   `-- debug/
|   |       |-- dys1_debug.wav
|   |       `-- test4_debug.wav
|   |-- reports/                          (generated PDF reports)
|   |-- results/
|   |   |-- acoustic/8873eed0-2dac-40a0-b891-b96c855dd2f4.json
|   |   `-- whisper/8873eed0-2dac-40a0-b891-b96c855dd2f4.json
|   `-- uploaded_audio/                   (raw user uploads)
`-- venv/                                 (Python virtual environment, 37,051 files)
```

### Root level breakdown

#### `.git/`
Why it exists: it stores Git history and repository metadata. What it does: tracks commits, branches, staging information, and refs. How it connects: it does not affect app runtime, but it is the source of version control. Execution dependency: none for the app itself.

#### `.env`
Why it exists: it stores local runtime configuration and secrets. What it does: chooses chat and grammar providers, specifies model names, and can hold API keys. How it connects: `backend/app/main.py` loads it with `python-dotenv`, while `chat_service.py` and `grammar_service.py` also contain fallback `.env` parsing. Execution dependency: optional for basic local execution, but important for chat and grammar features. Because this file is sensitive, it should never be copied into public docs or commits.

#### `.env.example`
Why it exists: it gives a safe template for environment variables. What it does: documents expected keys such as `CHAT_PROVIDER`, `OLLAMA_BASE_URL`, `WHISPER_MODEL`, `OPENAI_MODEL`, and `GEMINI_MODEL`. How it connects: new developers should copy this into `.env` and fill in real values. Execution dependency: documentation-only, but crucial for onboarding.

#### `.gitattributes`
Why it exists: it configures Git LFS behavior. What it does: marks `*.pkl` files as large-file artifacts. How it connects: model binaries in `ml/models/` are affected by this setting. Execution dependency: only relevant when cloning or syncing the repository.

#### `.gitignore`
Why it exists: it prevents local-only and generated files from being committed. What it does: ignores caches, `venv/`, `node_modules/`, storage outputs, `.env`, and build directories. How it connects: it keeps the repository clean despite many generated artifacts. Execution dependency: none at runtime.

#### `INTEGRATION.md`
Why it exists: it documents setup and integration guidance from an earlier stage of the project. What it does: describes how pieces fit together at a high level. How it connects: helpful context, but not authoritative when it disagrees with the live code. Execution dependency: documentation-only.

#### `phase2_report_extracted.txt`
Why it exists: it appears to be extracted text from a project report document. What it does: preserves report content in plain text for review or editing. How it connects: it describes the project history, not the runtime. Execution dependency: none.

#### `phase2_report_speechwell (1) on work.docx`
Why it exists: it is an editable report draft. What it does: stores a Word-format project report. How it connects: useful for academic and reporting context only. Execution dependency: none.

#### `phase2_report_speechwell_final.docx`
Why it exists: it is likely the finalized report document. What it does: captures a polished project write-up outside the source code. How it connects: background documentation only. Execution dependency: none.

#### `PHASE2_REPORT_UPDATE_GUIDE.md`
Why it exists: it explains how to update the Phase 2 report. What it does: serves as maintenance guidance for project documentation. How it connects: document workflow, not app workflow. Execution dependency: none.

#### `PHASE2_REPORT_UPDATE_GUIDE.pdf`
Why it exists: it is the rendered PDF form of the update guide. What it does: gives a shareable version of the Markdown guide. How it connects: documentation output only. Execution dependency: none.

#### `PROJECT_LEARNING_MANUAL.md`
Why it exists: this is the learning manual you asked for. What it does: explains the codebase end to end for a beginner developer. How it connects: it references all the major runtime modules, data artifacts, and workflows. Execution dependency: none for runtime, but high value for onboarding.

#### `PROJECT_LEARNING_MANUAL.pdf`
Why it exists: rendered PDF version of this manual. What it does: gives you a shareable, printable version of the project explanation. How it connects: generated by `scripts/render_learning_manual_pdf.py`. Execution dependency: none.

#### `PROJECT_STRUCTURE.md`
Why it exists: it documents a prior view of the repository layout. What it does: provides a manually written structure summary. How it connects: helpful orientation, but should be checked against the real tree because the code has evolved. Execution dependency: none.

#### `PROJECT_TECHNICAL_REPORT.md`
Why it exists: it is a technical report describing the project. What it does: explains architecture, methods, and outcomes in report form. How it connects: useful as background, but not always current with the newest runtime code paths. Execution dependency: none.

#### `PROJECT_TECHNICAL_REPORT.pdf`
Why it exists: PDF export of the technical report. What it does: provides a portable shareable report. How it connects: generated from the Markdown report by `scripts/render_report_pdf.py`. Execution dependency: none.

#### `README.md`
Why it exists: it is the main repository landing document. What it does: explains the project concept, stack, and startup steps. How it connects: it is useful for a first read, but some model descriptions are older than the live inference logic. Execution dependency: none.

#### `REQUIREMENTS.md`
Why it exists: it documents project requirements in prose. What it does: captures product or academic requirement statements. How it connects: useful for understanding intent, not direct execution. Execution dependency: none.

#### `requirements.txt`
Why it exists: it defines Python dependencies. What it does: installs FastAPI, SQLAlchemy, Whisper, librosa, transformers, scikit-learn, ReportLab, and supporting libraries. How it connects: required by backend and ML code. Execution dependency: high for backend startup and model inference.

#### `quickstart.ps1`
Why it exists: it is a Windows bootstrap helper. What it does: checks Python, installs dependencies, checks for the RF+SVC model, installs frontend packages, and prints startup instructions. How it connects: helpful for local setup, but it still points users to a deleted `INTEGRATION_GUIDE.md`, so it is slightly outdated. Execution dependency: optional convenience tool.

#### `quickstart.sh`
Why it exists: it is the Unix shell version of the quick-start script. What it does: installs backend and frontend dependencies and prints manual startup commands. How it connects: same role as the PowerShell script, but for Bash-like environments. Execution dependency: optional convenience tool.

#### `speechwell.db`
Why it exists: this is the active runtime SQLite database. What it does: stores users, analyses, training sessions, and training progress. How it connects: `backend/app/paths.py` points the app at this root-level file, not `backend/speechwell.db`. Execution dependency: core runtime persistence.

#### `SpeechWell_Technical_Report.pdf`
Why it exists: it is another PDF report artifact. What it does: preserves a report version under a slightly different filename. How it connects: report/archive only. Execution dependency: none.

#### `start_speechwell.bat`
Why it exists: it is a Windows launcher. What it does: opens one terminal for the backend and one for the frontend. How it connects: it starts `uvicorn app.main:app` from inside `backend/` and `npm run dev` from the frontend directory. Execution dependency: optional startup convenience.

#### `backend/`
Why it exists: this is the server-side application package. What it does: hosts FastAPI routes, persistence models, auth logic, scoring services, chat integration, report generation, and training evaluation. How it connects: it is the bridge between the frontend and the ML layer. Execution dependency: core runtime.

#### `ml/`
Why it exists: this folder holds feature extraction, training, evaluation, and saved model artifacts. What it does: contains both offline experimentation and online inference helpers. How it connects: runtime imports some ML code directly, while training and evaluation scripts are developer tools. Execution dependency: partly runtime, partly offline.

#### `scripts/`
Why it exists: it stores small utility scripts. What it does: currently holds Markdown-to-PDF report and manual rendering scripts. How it connects: used for documentation artifact generation. Execution dependency: optional.

#### `scripts/render_learning_manual_pdf.py`
Why it exists: manual PDF renderer. What it does: converts `PROJECT_LEARNING_MANUAL.md` into `PROJECT_LEARNING_MANUAL.pdf` using ReportLab with basic heading, paragraph, list, and code-block styling. How it connects: created specifically so this manual can be regenerated reproducibly. Execution dependency: documentation-only.

#### `scripts/render_report_pdf.py`
Why it exists: technical-report PDF renderer. What it does: converts `PROJECT_TECHNICAL_REPORT.md` into `PROJECT_TECHNICAL_REPORT.pdf`. How it connects: same role as the new manual renderer, but for the older technical report. Execution dependency: documentation-only.

#### `speechwell-frontend/`
Why it exists: this is the browser UI application. What it does: renders routes, forms, dashboards, upload screens, chat, results, and training pages. How it connects: it calls the backend API and displays stored results. Execution dependency: core user-facing layer.

#### `storage/`
Why it exists: it stores runtime-generated artifacts. What it does: holds raw uploads, normalized audio, reports, and some older experiment caches. How it connects: backend analysis routes write into it, and report downloads read from it. Execution dependency: important for runtime I/O.

#### `venv/`
Why it exists: it is the local Python virtual environment. What it does: stores installed Python packages and executables. How it connects: many startup and validation commands assume `venv/Scripts/python.exe` on Windows. Execution dependency: optional if another Python environment is used, but usually practical.

### Backend breakdown

#### `backend/README.md`
Why it exists: backend-specific documentation. What it does: describes the API side of the project. How it connects: onboarding material only. Execution dependency: none.

#### `backend/speechwell.db`
Why it exists: older local database artifact. What it does: appears to be a stale or unused SQLite file. How it connects: the current app does not point to it, because `backend/app/paths.py` resolves the active DB as root-level `speechwell.db`. Execution dependency: effectively none in the current setup.

#### `backend/__init__.py`
Why it exists: marks `backend` as a Python package. What it does: allows package imports such as `backend.app.main`. How it connects: needed for Python module resolution. Execution dependency: low but necessary for clean imports.

#### `backend/app/__init__.py`
Why it exists: package marker for `backend.app`. What it does: enables package-relative imports. How it connects: supports FastAPI app loading and internal imports. Execution dependency: low.

#### `backend/app/main.py`
Why it exists: it is the backend entrypoint and the most important server file. What it does: creates the FastAPI app, adds CORS, ensures schema compatibility, backfills old rows, defines all API routes, normalizes uploaded audio, calls the analysis pipeline, saves DB results, and serves PDFs. How it connects: imports nearly every important backend service and calls `ml/services/speech_analysis_service.py`. Execution dependency: highest on the backend; `uvicorn backend.app.main:app` starts here.

#### `backend/app/paths.py`
Why it exists: central path configuration. What it does: resolves project root, model locations, DB path, and runtime storage directories. How it connects: removes path ambiguity between running from repo root and from `backend/`. Execution dependency: high because many modules import these path constants.

#### `backend/app/schemas.py`
Why it exists: API schema definitions. What it does: defines Pydantic request and response models for auth, analysis, history, profile, training, and chat endpoints. How it connects: route handlers in `main.py` use these to validate inputs and shape outputs. Execution dependency: high for API typing and validation.

#### `backend/app/database/__init__.py`
Why it exists: package marker for the database subpackage. What it does: keeps imports orderly. How it connects: supports `backend.app.database.*` imports. Execution dependency: low.

#### `backend/app/database/db.py`
Why it exists: database connection setup. What it does: creates the SQLAlchemy engine, session factory, and declarative base. How it connects: `main.py` and `models.py` depend on it for persistence. Execution dependency: high because no database work happens without it.

#### `backend/app/database/models.py`
Why it exists: data schema for persistence. What it does: defines `User`, `Analysis`, `TrainingSession`, and `TrainingProgress`. It also exposes `Analysis.overall_score`, which computes a derived score from dysarthria, stuttering, and grammar. How it connects: every major backend workflow stores or reads these models. Execution dependency: high.

#### `backend/app/services/__init__.py`
Why it exists: package marker for backend services. What it does: groups service modules under one namespace. How it connects: internal organization. Execution dependency: low.

#### `backend/app/services/acoustic_service.py`
Why it exists: thin wrapper around acoustic feature extraction. What it does: re-exports `extract_acoustic_embedding` from the ML layer. How it connects: provides backward-compatible backend-side imports. Execution dependency: low, but used as a compatibility layer.

#### `backend/app/services/auth_service.py`
Why it exists: authentication utilities. What it does: hashes passwords with PBKDF2, verifies PBKDF2 or bcrypt hashes, creates JWT-like tokens, and falls back to a local HMAC token implementation if `python-jose` is unavailable. How it connects: `main.py` uses it for register, login, and current-user logic. Execution dependency: high for protected routes.

#### `backend/app/services/chat_service.py`
Why it exists: AI chat integration. What it does: supports OpenAI, Gemini, and Ollama chat calls, constrains responses to SpeechWell topics, formats analysis context, limits reply length, and falls back to locally written advice if the provider is unavailable. How it connects: `POST /api/chat` calls `generate_chat_reply()`. Execution dependency: optional runtime feature.

#### `backend/app/services/dysarthria_inference_service.py`
Why it exists: dysarthria decision engine. What it does: loads the preferred saved classifier, extracts raw audio features, computes a symptom score, applies healthy-speech guardrails, and returns a final label, probability, and explanation. How it connects: `ml/services/speech_analysis_service.py` calls it during every analysis. Execution dependency: core runtime analysis module.

#### `backend/app/services/grammar_service.py`
Why it exists: transcript correction and grammar scoring. What it does: calls OpenAI, Gemini, or Ollama for correction, estimates structural grammar errors from the transcript itself, blends the two views into a probability, and also improves free-form training responses. How it connects: used during analysis, score normalization, and grammar training exercises. Execution dependency: high for grammar-related features.

#### `backend/app/services/pdf_report_service.py`
Why it exists: report rendering. What it does: draws a single-page PDF using ReportLab with severity cards, transcript blocks, timing metrics, and an overall score ring. How it connects: `main.py` uses it after analysis to create downloadable reports. Execution dependency: optional output feature, but important for the report flow.

#### `backend/app/services/phonological_service.py`
Why it exists: articulation instability proxy. What it does: estimates phonological risk from transcript fragments, repaired starts, elongated spellings, and unstable segment timing. How it connects: called from the main analysis pipeline. Execution dependency: medium.

#### `backend/app/services/score_service.py`
Why it exists: shared scoring math. What it does: clamps probabilities, converts grammar errors into a quality score, and calculates the final overall speech score. How it connects: used by database models, grammar logic, and PDF rendering. Execution dependency: high because multiple modules rely on its formulas.

#### `backend/app/services/stuttering_service.py`
Why it exists: fluency and disfluency scoring module. What it does: counts repetitions, prolongations, and blocks; adds pause-variability and pacing signals; and outputs a conservative stuttering probability. How it connects: called during analysis and displayed in results and PDFs. Execution dependency: core runtime analysis module.

#### `backend/app/services/training_catalog.py`
Why it exists: static exercise catalog. What it does: defines the Breath and Voice, Articulation, Fluency, and Grammar modules along with their exercises, prompts, input modes, and expected text. How it connects: both backend and frontend training pages rely on this structure via the API. Execution dependency: high for Therapy Hub.

#### `backend/app/services/training_service.py`
Why it exists: training attempt evaluator. What it does: scores typed or spoken exercise attempts, counts repeated words and long pauses, optionally applies grammar correction, builds user-friendly feedback, and updates aggregate training progress. How it connects: training routes in `main.py` call it directly. Execution dependency: high for guided practice.

#### `backend/app/services/whisper_service.py`
Why it exists: thin compatibility wrapper. What it does: forwards calls to `ml.feature_extraction.extract_whisper.analyze_audio_features()`. How it connects: keeps older import paths working. Execution dependency: low.

#### `backend/storage/uploaded_audio/a3f4e966-ba17-49b5-a240-0559be668b26_test1.mp3`
Why it exists: leftover uploaded audio in the legacy backend-local storage tree. What it does: preserves one historical upload. How it connects: the current app writes to root-level `storage/uploaded_audio/`, not this folder. Execution dependency: none for current runtime.

#### `backend/**/__pycache__/`
Why it exists: Python creates bytecode caches automatically. What it does: stores `.pyc` files for faster import. How it connects: no direct logic value; safe to delete because Python will recreate them. Execution dependency: none.

### ML breakdown

#### `ml/README.md`
Why it exists: ML-folder documentation. What it does: explains the purpose of the ML package at a high level. How it connects: orientation only. Execution dependency: none.

#### `ml/__init__.py`
Why it exists: package marker. What it does: enables imports like `import ml.services...`. How it connects: Python package plumbing. Execution dependency: low.

#### `ml/dysarthria_pipeline_config.py`
Why it exists: centralized dysarthria pipeline constants. What it does: stores active data paths, model artifact paths, report output paths, default SVC parameters, and the full numeric feature column list. How it connects: training, evaluation, and runtime code all use it as a shared contract. Execution dependency: high.

#### `ml/datasets/torgo/TORGO_RAW/F_Con/**`
Why it exists: healthy or control female TORGO recordings. What it does: provides negative-class speech examples. How it connects: `build_torgo_dataset.py` indexes these files into `torgo_index.csv`. Execution dependency: training-only data.

#### `ml/datasets/torgo/TORGO_RAW/F_Dys/**`
Why it exists: dysarthric female TORGO recordings. What it does: provides positive-class speech examples. How it connects: same indexing pipeline as above. Execution dependency: training-only data.

#### `ml/datasets/torgo/TORGO_RAW/M_Con/**`
Why it exists: healthy or control male TORGO recordings. What it does: expands negative-class diversity. How it connects: used in the same dataset build scripts. Execution dependency: training-only data.

#### `ml/datasets/torgo/TORGO_RAW/M_Dys/**`
Why it exists: dysarthric male TORGO recordings. What it does: expands positive-class diversity. How it connects: used in the same dataset build scripts. Execution dependency: training-only data.

#### `ml/evaluation/README.md`
Why it exists: evaluation workflow documentation. What it does: explains which validation and report files matter and how to run validation. How it connects: useful reference when retraining or validating models. Execution dependency: none.

#### `ml/evaluation/dysarthria_model_comparison_report.json`
Why it exists: saved comparison results across multiple model families. What it does: records metrics for logistic, SVC, random forest, RF+SVC ensemble, and hist-gradient-boosting models, and identifies the winner. How it connects: the best saved model artifact `dysarthria_best_comparison_model.pkl` comes from this comparison workflow. Execution dependency: offline evaluation artifact.

#### `ml/evaluation/dysarthria_model_v2_report_group.json`
Why it exists: grouped evaluation report from an older v2 experiment. What it does: stores metrics for a stricter speaker-grouped setup. How it connects: useful historically, but it is not the runtime source of truth. Execution dependency: offline artifact.

#### `ml/evaluation/dysarthria_model_v2_rf_svc_ensemble_report.json`
Why it exists: main RF+SVC ensemble training report. What it does: stores holdout metrics, selected threshold, and weights for the ensemble. How it connects: corresponds to `ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl`. Execution dependency: offline artifact used to understand the model.

#### `ml/evaluation/evaluate_speechwell_multiclass.py`
Why it exists: earlier generalized evaluation script. What it does: evaluates multiclass predictions and confidence filtering for labels such as `Healthy`, `Stuttering`, and `SLI`. How it connects: this is not part of the current runtime pipeline, which is modular rather than a single multiclass classifier. Execution dependency: offline and legacy.

#### `ml/evaluation/full_dataset_final_model_curve.py`
Why it exists: learning-curve analysis for a final model variant. What it does: evaluates how model performance changes as more training data is used. How it connects: helps understand data-efficiency, not runtime inference. Execution dependency: offline.

#### `ml/evaluation/full_dataset_latest_model_curve.py`
Why it exists: learning-curve analysis for the latest active model family. What it does: measures performance as training-set fraction increases. How it connects: useful for judging whether more data would likely help. Execution dependency: offline.

#### `ml/evaluation/plot_final_metrics.py`
Why it exists: result visualization script. What it does: plots final metric figures. How it connects: reads saved JSON and CSV metrics and produces images in `learning_curves/`. Execution dependency: offline.

#### `ml/evaluation/plot_model_metric_comparison.py`
Why it exists: comparison plotting script. What it does: creates a side-by-side metric comparison figure. How it connects: visualizes the saved comparison results. Execution dependency: offline.

#### `ml/evaluation/simple_learning_curve.py`
Why it exists: older learning curve utility. What it does: likely supports the legacy logistic workflow. How it connects: historical analysis only. Execution dependency: offline and legacy.

#### `ml/evaluation/speakerwise_strict_learning_curve.py`
Why it exists: stricter generalization analysis. What it does: evaluates performance when speaker overlap is prevented more aggressively. How it connects: useful for realistic generalization estimates. Execution dependency: offline.

#### `ml/evaluation/v2_learning_curve.py`
Why it exists: v2-model learning-curve script. What it does: studies performance growth for the newer tabular-feature models. How it connects: model development only. Execution dependency: offline.

#### `ml/evaluation/validate_accuracy.py`
Why it exists: validation utility. What it does: loads a trained artifact and a dataset, builds the feature matrix, runs predictions, computes accuracy, precision, recall, F1, and confusion matrix, and saves a JSON report. How it connects: helpful for checking whether a saved model is readable and works on a compatible dataset. Execution dependency: offline validation.

#### `ml/evaluation/validation_report.json`
Why it exists: saved metrics for the legacy v1 model. What it does: documents the older logistic and PCA pipeline performance. How it connects: useful as a baseline to show improvement over time. Execution dependency: none.

#### `ml/evaluation/validation_report_v2_group.json`
Why it exists: grouped validation results for v2. What it does: shows more realistic generalization performance when speaker grouping is enforced. How it connects: this report is more trustworthy than the full-dataset validation for judging real robustness. Execution dependency: none.

#### `ml/evaluation/validation_report_v2_rf_svc_ensemble.json`
Why it exists: saved validation report for the v2 ensemble on the full dataset. What it does: shows extremely strong metrics when predicting the full available feature set. How it connects: useful, but optimistic because it is not the same as a clean unseen holdout. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_dysarthria_learning_curve.csv`
Why it exists: numeric learning-curve data for one dysarthria experiment. What it does: stores the performance points used to render the matching PNG. How it connects: offline analysis only. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_dysarthria_learning_curve.png`
Why it exists: plot of the above learning curve. What it does: gives a visual picture of performance growth. How it connects: report support asset only. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_dysarthria_strict_speakerwise_curve.csv`
Why it exists: strict speakerwise learning-curve data. What it does: records performance under stronger anti-leakage grouping. How it connects: helps evaluate generalization honestly. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_dysarthria_strict_speakerwise_curve.png`
Why it exists: rendered speakerwise curve plot. What it does: visualizes the stricter generalization pattern. How it connects: report asset only. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_full_dataset_model_curve.csv`
Why it exists: full-dataset curve data. What it does: stores one model's behavior as training size changes. How it connects: offline experiment output. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_full_dataset_model_curve.png`
Why it exists: PNG version of the full-dataset curve. What it does: visualizes that training-size experiment. How it connects: report support asset only. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_latest_model_full_data_curve.csv`
Why it exists: latest-model full-data curve data. What it does: stores the curve points for the newer active family. How it connects: analysis output only. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_latest_model_full_data_curve.png`
Why it exists: PNG of the latest-model full-data curve. What it does: gives a visual version of the same experiment. How it connects: report support asset only. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_metrics_separate_tables.png`
Why it exists: visualization asset for final metrics. What it does: presents metrics in a more digestible image format. How it connects: report support only. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_metrics_table_chart.png`
Why it exists: another metrics visualization. What it does: renders a metrics table or chart for reporting. How it connects: analysis presentation asset. Execution dependency: none.

#### `ml/evaluation/learning_curves/final_trained_model_metrics.png`
Why it exists: final trained-model metric summary image. What it does: visualizes core final metrics. How it connects: reporting and presentation only. Execution dependency: none.

#### `ml/evaluation/learning_curves/full_data_fitted_model_accuracy_all_three.json`
Why it exists: saved metric summary for a fitted-model experiment. What it does: preserves numeric outputs underlying a chart or report. How it connects: analysis support only. Execution dependency: none.

#### `ml/evaluation/learning_curves/logistic_regression_full_data_curve.json`
Why it exists: older curve summary for logistic regression. What it does: preserves experiment metrics for a legacy baseline. How it connects: historical comparison only. Execution dependency: none.

#### `ml/evaluation/learning_curves/model_metric_comparison_holdout.png`
Why it exists: visual comparison of holdout metrics across model families. What it does: helps a human compare model quality quickly. How it connects: complements `dysarthria_model_comparison_report.json`. Execution dependency: none.

#### `ml/feature_extraction/__init__.py`
Why it exists: package marker. What it does: supports imports from the feature extraction subpackage. How it connects: import organization only. Execution dependency: low.

#### `ml/feature_extraction/extract_acoustic.py`
Why it exists: Wav2Vec2 embedding extraction. What it does: loads a local offline `facebook/wav2vec2-base` model, resamples audio to 16 kHz, mean-pools hidden states, and returns a 768-dimensional vector. How it connects: used by `speech_analysis_service.py` and by older dysarthria training pipelines. Execution dependency: optional for the newest runtime path but still part of the legacy path.

#### `ml/feature_extraction/extract_torgo_features.py`
Why it exists: older feature builder for TORGO. What it does: creates combined Whisper and acoustic-embedding feature sets for earlier experiments. How it connects: legacy training and validation tooling. Execution dependency: offline and legacy.

#### `ml/feature_extraction/extract_whisper.py`
Why it exists: transcription and timing feature extraction. What it does: loads Whisper, transcribes English audio, computes word count, segment data, speaking rate, pause durations, long pause count, and total duration. How it connects: this is the first step of nearly every runtime analysis and also helps training evaluation. Execution dependency: high.

#### `ml/feature_extraction/raw_audio_features.py`
Why it exists: fast tabular feature extraction from raw audio. What it does: computes RMS, ZCR, spectral centroid, bandwidth, rolloff, flatness, silence ratio, chroma summaries, spectral contrast summaries, and MFCC plus delta statistics. How it connects: the modern dysarthria classifiers depend on these columns. Execution dependency: high for dysarthria inference and training.

#### `ml/models/dysarthria_best_comparison_model.pkl`
Why it exists: saved best model from the comparison script. What it does: stores a fitted pipeline plus threshold and metadata; in the current repository it points to a HistGradientBoosting-based tabular model. How it connects: `dysarthria_inference_service.py` prefers this file first at runtime. Execution dependency: currently the most important dysarthria artifact.

#### `ml/models/dysarthria_model_v1.pkl`
Why it exists: first-generation dysarthria classifier. What it does: stores the legacy logistic regression model. How it connects: used only as a fallback when newer pipeline artifacts are unavailable. Execution dependency: fallback-only.

#### `ml/models/dysarthria_model_v2_group.pkl`
Why it exists: grouped-split v2 experiment artifact. What it does: preserves a stricter experimental model. How it connects: not the default runtime model, but useful for comparison. Execution dependency: offline and experimental.

#### `ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl`
Why it exists: second-generation ensemble model artifact. What it does: stores the preprocessing pipeline, a soft-voting RF+SVC classifier, selected threshold, feature columns, and metadata. How it connects: runtime uses it if `dysarthria_best_comparison_model.pkl` is absent. Execution dependency: high fallback and secondary active artifact.

#### `ml/models/dysarthria_pca_v1.pkl`
Why it exists: PCA transform for the legacy pipeline. What it does: reduces 768-dimensional acoustic embeddings before the v1 classifier. How it connects: only used with `dysarthria_model_v1.pkl`. Execution dependency: legacy fallback.

#### `ml/models/dysarthria_scaler_v1.pkl`
Why it exists: scaler for the legacy embedding pipeline. What it does: standardizes acoustic embeddings before PCA. How it connects: only used with `dysarthria_model_v1.pkl` and `dysarthria_pca_v1.pkl`. Execution dependency: legacy fallback.

#### `ml/services/__init__.py`
Why it exists: package marker for ML services. What it does: organizes the runtime orchestration layer. How it connects: import plumbing. Execution dependency: low.

#### `ml/services/speech_analysis_service.py`
Why it exists: top-level runtime analysis orchestrator. What it does: calls Whisper features, grammar detection, acoustic embedding extraction, dysarthria inference, stuttering detection, and phonological detection; then combines them into one dictionary with fallbacks. How it connects: `backend/app/main.py` calls this during `POST /api/analyze`. Execution dependency: extremely high.

#### `ml/training/README.md`
Why it exists: training workflow documentation. What it does: explains the main trainers, legacy scripts, and optional UASpeech augmentation. How it connects: important for retraining the dysarthria models. Execution dependency: none.

#### `ml/training/build_combined_dysarthria_index.py`
Why it exists: combined dataset index builder. What it does: indexes TORGO and optionally the Kaggle UASpeech dysarthria-only dataset, adds dataset and speaker labels, and writes `combined_dysarthria_index.csv`. How it connects: first step when building the larger comparison dataset. Execution dependency: offline data prep.

#### `ml/training/build_torgo_audio_features.py`
Why it exists: raw-audio feature table builder. What it does: reads an index CSV, extracts tabular audio features row by row, and writes a resumable CSV. How it connects: produces the training table used by the newer dysarthria models. Execution dependency: offline data prep.

#### `ml/training/build_torgo_dataset.py`
Why it exists: TORGO index builder. What it does: walks the four label folders and writes `torgo_index.csv` with file path and label columns. How it connects: first step in the TORGO-only training pipeline. Execution dependency: offline data prep.

#### `ml/training/combined_audio_features.csv`
Why it exists: expanded feature dataset from TORGO plus optional UASpeech. What it does: stores row-wise acoustic features plus labels and metadata for comparison experiments. How it connects: `train_dysarthria_model_comparison.py` uses it by default. Execution dependency: offline training data.

#### `ml/training/combined_dysarthria_index.csv`
Why it exists: combined audio index. What it does: stores file paths and labels before feature extraction. How it connects: input to `build_torgo_audio_features.py` when creating the larger feature table. Execution dependency: offline.

#### `ml/training/inspect_dataset.py`
Why it exists: developer inspection utility. What it does: helps quickly inspect training data content. How it connects: convenience during experimentation. Execution dependency: none.

#### `ml/training/torgo_audio_features_v4.csv`
Why it exists: main TORGO feature dataset. What it does: stores the tabular features used by the v2 trainers and validation scripts. How it connects: default data path in `dysarthria_pipeline_config.py`. Execution dependency: offline training and validation input.

#### `ml/training/torgo_features_sample.csv`
Why it exists: small legacy or sample dataset. What it does: provides a fallback feature table for some older validation flows. How it connects: mostly historical. Execution dependency: low.

#### `ml/training/torgo_index.csv`
Why it exists: TORGO file index. What it does: enumerates the corpus and labels. How it connects: input to downstream feature extraction. Execution dependency: offline.

#### `ml/training/train_dysarthria_full.py`
Why it exists: older full legacy trainer. What it does: trains the v1 fluency plus embedding plus scaler plus PCA plus logistic regression stack. How it connects: produces the legacy fallback artifacts. Execution dependency: offline and legacy.

#### `ml/training/train_dysarthria_model.py`
Why it exists: simple baseline trainer. What it does: trains an early dysarthria model from a simpler feature set. How it connects: useful as a historical baseline. Execution dependency: offline and legacy.

#### `ml/training/train_dysarthria_model_comparison.py`
Why it exists: modern model-selection script. What it does: trains and compares calibrated logistic regression, RBF SVC, random forest, RF+SVC soft-voting ensemble, and HistGradientBoosting; tunes thresholds; saves the best model and a report. How it connects: currently responsible for the preferred runtime artifact. Execution dependency: offline, but strategically important.

#### `ml/training/train_dysarthria_optimized.py`
Why it exists: model experimentation utility. What it does: compares several classical models on the tabular feature set and explores improvements. How it connects: development tool that sits between older and newer training flows. Execution dependency: offline.

#### `ml/training/train_dysarthria_rf_svc_ensemble.py`
Why it exists: second-generation main trainer. What it does: builds a preprocessing pipeline, trains a soft-voting RF+SVC ensemble, optionally uses group-aware splits, rebalances classes, tunes thresholds, and saves the artifact and report. How it connects: creates `dysarthria_model_v2_rf_svc_ensemble.pkl`. Execution dependency: offline, but historically the main trainer.

#### `ml/training/train_dysarthria_with_acoustics.py`
Why it exists: earlier acoustics-based trainer. What it does: trains a dysarthria model using acoustic embeddings. How it connects: old experimentation path retained for reproducibility. Execution dependency: offline and legacy.

#### `ml/**/__pycache__/`
Why it exists: Python bytecode cache. What it does: stores compiled `.pyc` imports. How it connects: generated automatically and not part of project logic. Execution dependency: none.

### Frontend breakdown

#### `speechwell-frontend/README.md`
Why it exists: default Vite and React template README. What it does: explains generic React plus TypeScript plus Vite setup rather than SpeechWell-specific behavior. How it connects: mostly leftover starter documentation. Execution dependency: none.

#### `speechwell-frontend/package.json`
Why it exists: frontend dependency and script manifest. What it does: defines the React 19, React Router 7, and Vite 7 stack plus scripts like `dev`, `build`, `lint`, and `preview`. How it connects: `npm install`, `npm run dev`, and `npm run build` all depend on it. Execution dependency: high for the frontend.

#### `speechwell-frontend/package-lock.json`
Why it exists: exact dependency lock file. What it does: pins the precise frontend package versions for reproducible installs. How it connects: used by npm during install. Execution dependency: low at runtime, high for reproducibility.

#### `speechwell-frontend/eslint.config.js`
Why it exists: linting configuration. What it does: sets code-quality rules for the frontend source. How it connects: used by `npm run lint`. Execution dependency: development-only.

#### `speechwell-frontend/index.html`
Why it exists: Vite entry HTML. What it does: hosts the root DOM node and loads the frontend bundle. How it connects: browser entry document for the SPA. Execution dependency: high for frontend boot.

#### `speechwell-frontend/tsconfig.json`
Why it exists: top-level TypeScript config. What it does: coordinates TypeScript project references. How it connects: build and editor tooling depend on it. Execution dependency: development and build.

#### `speechwell-frontend/tsconfig.app.json`
Why it exists: app-specific TypeScript config. What it does: configures compilation for the browser app code. How it connects: `tsc -b` uses it. Execution dependency: build-time.

#### `speechwell-frontend/tsconfig.node.json`
Why it exists: Node-side TypeScript config. What it does: supports typed build and config files such as the Vite config. How it connects: build tooling only. Execution dependency: build-time.

#### `speechwell-frontend/vite.config.ts`
Why it exists: Vite dev and build configuration. What it does: enables the React plugin and whitelists a specific Cloudflare tunnel host for development access. How it connects: affects the frontend dev server. Execution dependency: high for local frontend startup.

#### `speechwell-frontend/public/vite.svg`
Why it exists: default public favicon asset from Vite. What it does: appears in the browser tab. How it connects: referenced by `index.html`. Execution dependency: cosmetic only.

#### `speechwell-frontend/dist/`
Why it exists: built frontend output. What it does: stores the static bundle created by `npm run build`. How it connects: useful for deployment or testing a production build, but not hand-edited. Execution dependency: generated output only.

#### `speechwell-frontend/node_modules/`
Why it exists: installed frontend dependencies. What it does: stores thousands of third-party package files. How it connects: required for local development and build, but not authored project logic. Execution dependency: high for local frontend execution.

#### `speechwell-frontend/src/main.tsx`
Why it exists: frontend boot entrypoint. What it does: mounts the React app into the DOM. How it connects: imports `App.tsx` and global styles. Execution dependency: high.

#### `speechwell-frontend/src/App.tsx`
Why it exists: route registry and shell wiring. What it does: wraps the app in `BrowserRouter`, shows the shared `Navbar`, optionally displays the intro animation, applies the stored theme on load, and maps routes to page components. How it connects: central frontend navigation file. Execution dependency: highest on the frontend.

#### `speechwell-frontend/src/App.css`
Why it exists: app-level CSS helpers. What it does: adds route and page transition styling. How it connects: imported by `App.tsx`. Execution dependency: low but visible in UX.

#### `speechwell-frontend/src/index.css`
Why it exists: global style system. What it does: defines CSS variables, theme tokens, base typography, layout defaults, and theme-specific palettes. How it connects: every page depends on it. Execution dependency: high for visual consistency.

#### `speechwell-frontend/src/api/api.ts`
Why it exists: API client layer. What it does: defines typed request and response interfaces, stores and retrieves auth tokens from `localStorage`, sends auth, profile, chat, and training requests with `fetch`, and uploads audio with `XMLHttpRequest` so progress can be tracked. How it connects: every page that talks to the backend imports functions from here. Execution dependency: very high.

#### `speechwell-frontend/src/assets/react.svg`
Why it exists: default starter asset. What it does: preserves a Vite template icon in source assets. How it connects: it is not meaningfully used by the SpeechWell UI. Execution dependency: none; effectively a leftover.

#### `speechwell-frontend/src/components/InteractiveButton.tsx`
Why it exists: reusable button wrapper. What it does: centralizes interactive button styling and variants. How it connects: used across pages for primary actions. Execution dependency: medium.

#### `speechwell-frontend/src/components/IntroAnimation.tsx`
Why it exists: landing animation overlay. What it does: shows the first-session intro screen and then hides itself. How it connects: `App.tsx` gates it through `sessionStorage`. Execution dependency: optional UX layer.

#### `speechwell-frontend/src/components/LoadingState.tsx`
Why it exists: reusable loading placeholder. What it does: gives visual feedback while data is fetching. How it connects: dashboard, history, and other pages can use it. Execution dependency: low.

#### `speechwell-frontend/src/components/Navbar.tsx`
Why it exists: top navigation bar. What it does: renders the shared header, checks backend health on a timer, and exposes theme-changing behavior depending on the page. How it connects: always visible because `App.tsx` wraps all routes with it. Execution dependency: medium.

#### `speechwell-frontend/src/components/ProgressBar.tsx`
Why it exists: reusable visual progress display. What it does: shows percent-based progress for training or analytics cards. How it connects: used by training-related UI. Execution dependency: low.

#### `speechwell-frontend/src/components/RefreshButton.tsx`
Why it exists: retry and refresh convenience component. What it does: provides a consistent refresh action in data-driven pages. How it connects: used where data reload is exposed. Execution dependency: low.

#### `speechwell-frontend/src/components/Sidebar.tsx`
Why it exists: authenticated-app side navigation. What it does: renders links to dashboard, upload, history, profile, therapy hub, and logout. How it connects: most app pages outside landing and auth use it. Execution dependency: medium.

#### `speechwell-frontend/src/components/TrainingModuleCard.tsx`
Why it exists: card view for therapy modules. What it does: displays module titles, descriptions, and progress summary. How it connects: used in `TherapyHub.tsx`. Execution dependency: medium for training UI.

#### `speechwell-frontend/src/components/VideoCard.tsx`
Why it exists: presentation component for practice videos. What it does: displays a single video title, thumbnail, and link. How it connects: used by the video grid in the therapy hub. Execution dependency: low.

#### `speechwell-frontend/src/components/VideoGrid.tsx`
Why it exists: layout component for grouped practice videos. What it does: arranges multiple `VideoCard` items. How it connects: used in therapy-related views. Execution dependency: low.

#### `speechwell-frontend/src/data/practiceVideos.ts`
Why it exists: hardcoded practice-video catalog. What it does: stores a list of YouTube resources grouped by practice theme. How it connects: the Therapy Hub displays these videos without needing a backend content CMS. Execution dependency: medium for the coaching experience.

#### `speechwell-frontend/src/pages/AIChat.tsx`
Why it exists: AI coach page. What it does: stores message history locally in component state, sends user prompts to `/api/chat`, shows typing animation, and exposes a microphone button that currently only toggles UI state. How it connects: depends on `api.ts` and backend chat service. Execution dependency: optional route.

#### `speechwell-frontend/src/pages/Dashboard.tsx`
Why it exists: analytics dashboard page. What it does: fetches analysis history and training progress, computes trends, streaks, averages, risk buckets, and skill bars, and renders summary cards and quick actions. How it connects: depends on `getAnalysisHistory()` and `getTrainingProgress()`. Execution dependency: high for logged-in analytics.

#### `speechwell-frontend/src/pages/History.tsx`
Why it exists: historical results page. What it does: fetches saved analyses, filters by date and severity, paginates results, opens result views, and downloads PDFs. How it connects: reads `/api/analyses` and `/api/reports/{audio_id}`. Execution dependency: high for reviewing old analyses.

#### `speechwell-frontend/src/pages/Landing.tsx`
Why it exists: marketing-style home page. What it does: introduces SpeechWell and routes visitors into auth or upload and report flows depending on login state. How it connects: default route `/`. Execution dependency: high for first impressions.

#### `speechwell-frontend/src/pages/Login.tsx`
Why it exists: user sign-in screen. What it does: posts credentials to `/api/auth/login`, saves token and user to `localStorage`, and navigates into the app. How it connects: frontend auth flow starts here. Execution dependency: high for authenticated features.

#### `speechwell-frontend/src/pages/Profile.tsx`
Why it exists: editable user-profile page. What it does: fetches and saves profile fields and theme preference. How it connects: uses `/api/profile` plus frontend theme helpers. Execution dependency: medium.

#### `speechwell-frontend/src/pages/Register.tsx`
Why it exists: sign-up screen. What it does: posts registration data to `/api/auth/register`, stores the returned token, and onboards the user into the app. How it connects: frontend auth flow starts here for new users. Execution dependency: high for new accounts.

#### `speechwell-frontend/src/pages/Results.tsx`
Why it exists: detailed analysis view. What it does: loads one analysis by `audioId`, renders probabilities, transcript, corrected text, timing metrics, and provides report download and share actions. How it connects: receives `audioId` from upload flow, history flow, or `sessionStorage`. Execution dependency: high.

#### `speechwell-frontend/src/pages/TherapyHub.tsx`
Why it exists: training home page. What it does: shows available modules, progress summaries, and practice videos. How it connects: fetches static module metadata from the backend and combines it with local video data. Execution dependency: medium and high for practice features.

#### `speechwell-frontend/src/pages/TrainingExercise.tsx`
Why it exists: single-exercise practice screen. What it does: starts a session with the backend, captures typed or microphone input, submits the attempt, and routes to the result screen. How it connects: it is the main bridge between UI practice and backend scoring. Execution dependency: high for therapy mode.

#### `speechwell-frontend/src/pages/TrainingModule.tsx`
Why it exists: module-detail page. What it does: explains a single therapy module and lists its exercises. How it connects: receives `moduleKey` from the route and backend catalog. Execution dependency: medium.

#### `speechwell-frontend/src/pages/TrainingResult.tsx`
Why it exists: training attempt result screen. What it does: reads the stored training-session outcome and renders transcript, scores, corrected text, and coaching feedback. How it connects: follows `TrainingExercise.tsx`. Execution dependency: medium and high for practice review.

#### `speechwell-frontend/src/pages/Upload.tsx`
Why it exists: audio upload and recording page. What it does: validates files, handles drag and drop, records microphone audio via `MediaRecorder`, shows upload progress, sends the file for analysis, and navigates to the result page. How it connects: this is the frontend entry to the main analysis pipeline. Execution dependency: highest user-action route.

#### `speechwell-frontend/src/styles/ai-chat.css`
Why it exists: styling for the AI chat page. What it does: controls chat-bubble layout, typing animation, and mic-button visuals. How it connects: imported by `AIChat.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/auth.css`
Why it exists: shared auth-page styling. What it does: styles login and registration layouts. How it connects: imported by auth pages. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/dashboard.css`
Why it exists: dashboard styling. What it does: styles analytics cards, trend sections, and summary layouts. How it connects: imported by `Dashboard.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/history.css`
Why it exists: history-page styling. What it does: styles filters, tables, pagination, and download buttons. How it connects: imported by `History.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/interactive-button.css`
Why it exists: shared button styling. What it does: defines the look and interaction states for `InteractiveButton`. How it connects: imported by the button component. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/intro-animation.css`
Why it exists: intro animation styling. What it does: controls the opening overlay visuals. How it connects: imported by `IntroAnimation.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/landing.css`
Why it exists: landing-page styling. What it does: defines the marketing and hero layout. How it connects: imported by `Landing.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/loading-state.css`
Why it exists: loading component styling. What it does: defines placeholders and animation for loading states. How it connects: imported by `LoadingState.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/navbar.css`
Why it exists: navbar styling. What it does: styles the global top navigation and theme controls. How it connects: imported by `Navbar.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/profile.css`
Why it exists: profile-page styling. What it does: styles user-profile forms and theme controls. How it connects: imported by `Profile.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/results.css`
Why it exists: results-page styling. What it does: styles probability cards, transcript panels, and download/share actions. How it connects: imported by `Results.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/sidebar.css`
Why it exists: sidebar styling. What it does: styles the app navigation sidebar and link states. How it connects: imported by `Sidebar.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/therapy-hub.css`
Why it exists: therapy-hub styling file. What it does: appears intended for Therapy Hub visuals. How it connects: in the current code, `TherapyHub.tsx` imports `training.css` instead, so this file looks unused or leftover. Execution dependency: likely none at present.

#### `speechwell-frontend/src/styles/training.css`
Why it exists: therapy and training styling. What it does: styles module cards, exercise pages, and training result layouts. How it connects: imported by Therapy Hub and training pages. Execution dependency: visual only.

#### `speechwell-frontend/src/styles/upload.css`
Why it exists: upload-page styling. What it does: styles drag-and-drop, recording controls, and progress bars. How it connects: imported by `Upload.tsx`. Execution dependency: visual only.

#### `speechwell-frontend/src/utils/theme.ts`
Why it exists: shared theme helper. What it does: defines theme options, persists the chosen theme in `localStorage`, and applies the active theme to the document root. How it connects: used by `App.tsx`, `Navbar.tsx`, and `Profile.tsx`. Execution dependency: medium.

#### `speechwell-frontend/src/utils/youtube.ts`
Why it exists: YouTube helper utilities. What it does: extracts IDs and builds thumbnail and embed URLs. How it connects: used by practice-video components. Execution dependency: low.

### Storage and generated artifact breakdown

#### `storage/chunks/`
Why it exists: placeholder directory for chunked or temporary uploads or processing artifacts. What it does: currently nothing visible; it is empty in the checked workspace. How it connects: the current backend does not actively use it. Execution dependency: none.

#### `storage/processed_audio/*.wav`
Why it exists: normalized runtime audio. What it does: stores the mono 16 kHz WAV files produced by `ffmpeg` before analysis. How it connects: the ML pipeline reads these normalized files rather than the raw uploads. Execution dependency: important runtime intermediate.

#### `storage/processed_audio/debug/*.wav`
Why it exists: developer debug copies. What it does: stores a couple of named debug WAVs such as `dys1_debug.wav` and `test4_debug.wav`. How it connects: useful for troubleshooting the preprocessing chain. Execution dependency: none.

#### `storage/reports/*.pdf`
Why it exists: generated user-facing reports. What it does: stores the PDFs rendered after completed analyses. How it connects: `GET /api/reports/{audio_id}` serves these files back to the frontend. Execution dependency: optional output feature, but important to the reporting workflow.

#### `storage/results/whisper/8873eed0-2dac-40a0-b891-b96c855dd2f4.json`
Why it exists: older cached experimental result. What it does: stores a Whisper-related output snapshot for one analysis. How it connects: current runtime does not actively read it. Execution dependency: none.

#### `storage/results/acoustic/8873eed0-2dac-40a0-b891-b96c855dd2f4.json`
Why it exists: older cached acoustic result. What it does: stores a saved acoustic output snapshot for one analysis. How it connects: current runtime does not actively read it. Execution dependency: none.

#### `storage/uploaded_audio/*`
Why it exists: raw uploaded user audio. What it does: stores the original files before normalization and analysis. How it connects: `POST /api/analyze` and training-audio evaluation both write into this directory. Execution dependency: runtime input archive.

## Section 4: Frontend Explanation

### Technologies used

The frontend stack is:

- React 19
- TypeScript
- React Router 7
- Vite 7
- plain CSS files rather than a heavy component framework
- browser storage through `localStorage` and `sessionStorage`

Even though `axios` exists in `package.json`, the app does not actually use it. All HTTP calls are made with:

- `fetch()` for standard JSON requests
- `XMLHttpRequest` for upload progress on audio files

### Frontend component structure

The routing shell lives in `src/App.tsx`. It maps URLs to pages:

- `/` -> `Landing`
- `/login` -> `Login`
- `/register` -> `Register`
- `/dashboard` and `/analytics` -> `Dashboard`
- `/upload` -> `Upload`
- `/history` and `/reports` -> `History`
- `/results` -> `Results`
- `/profile` -> `Profile`
- `/therapy-hub` -> `TherapyHub`
- `/therapy-hub/:moduleKey` -> `TrainingModule`
- `/therapy-hub/:moduleKey/:exerciseKey` -> `TrainingExercise`
- `/therapy-hub/session/:sessionId/result` -> `TrainingResult`
- `/ai-chat` -> `AIChat`

Shared layout pieces:

- `Navbar` is global and appears above all routes.
- `Sidebar` appears on most authenticated or app-like pages.
- `IntroAnimation` is session-based and only shows until `speechwell_intro_seen` is set in `sessionStorage`.

### State management

This app does **not** use Redux, Zustand, MobX, or React Context for major business state. Instead it uses:

- local component state with `useState`
- side effects with `useEffect`
- derived calculations with `useMemo`
- `localStorage` for auth token, theme, and user metadata
- `sessionStorage` for transient UI state such as the most recent `audioId`

This makes the app easy to follow for a beginner, but it also means:

- state is somewhat scattered across pages
- auth state is manually managed
- there is some duplication of data-fetching behavior

### API calls and UI-to-backend connection

All API calls are centralized in `src/api/api.ts`.

Important patterns:

- `VITE_API_URL` controls the backend base URL, with a fallback to `http://127.0.0.1:8000`.
- `getAuthHeader()` reads `accessToken` from `localStorage` and attaches `Authorization: Bearer ...` when available.
- upload uses `XMLHttpRequest` so the UI can display percent progress while the file is being transmitted.

Key frontend-to-backend links:

- `Login` -> `POST /api/auth/login`
- `Register` -> `POST /api/auth/register`
- `Profile` -> `GET/PUT /api/profile`
- `Upload` -> `POST /api/analyze`
- `Results` -> `GET /api/analyze/{audio_id}`
- `History` -> `GET /api/analyses` and `GET /api/reports/{audio_id}`
- `TherapyHub` -> `GET /api/training/modules` and `GET /api/training/progress`
- `TrainingExercise` -> `POST /api/training/session/start` then `POST /api/training/session/evaluate`
- `TrainingResult` -> `GET /api/training/session/{session_id}`
- `AIChat` -> `POST /api/chat`

### Important frontend logic details

#### Upload flow

`Upload.tsx` supports both file selection and live recording.

For recorded audio:

1. Browser microphone permission is requested.
2. `MediaRecorder` captures audio chunks.
3. On stop, the chunks are turned into a `File`.
4. The file is immediately sent to the backend for analysis.
5. The result's `audio_id` is stored in `sessionStorage`.
6. The page navigates to `/results?audioId=...`.

This is a very direct flow. There is no background queue and no polling stage. The request stays open while analysis happens.

#### Results flow

`Results.tsx` tries to find the current `audioId` from three places:

- route navigation state
- query string
- `sessionStorage`

That makes the page resilient if the user refreshes the browser after upload.

#### Dashboard logic

`Dashboard.tsx` computes many analytics on the client side:

- streaks
- risk buckets
- activity summaries
- recent trend charts
- practice hours estimate
- skill bars

A subtle but important detail: the dashboard's "Recent Average Score" is **not** the same formula as the backend's `overall_score`. The dashboard computes its own blended metric from grammar and max-risk values, so numbers there can differ from what the backend returns on an individual result.

#### AI chat page

The chat page is functional for text chat, but the microphone button is currently cosmetic. It toggles `isRecording` in state, but does not record or upload audio.

## Section 5: Backend Explanation

### Framework used

The backend is built with:

- FastAPI for the web framework
- SQLAlchemy for persistence
- SQLite for local database storage
- Pydantic for request and response validation
- ReportLab for PDF creation
- `ffmpeg` as an external tool for audio normalization

`backend/app/main.py` is the entrypoint.

### Middleware and startup behavior

The backend adds CORS middleware for:

- `http://localhost:5173`
- `http://localhost:3000`
- `*`

and allows credentials, all methods, and all headers.

That is convenient for development, but very permissive.

On startup, the backend also:

- creates tables through SQLAlchemy
- checks for missing SQLite columns and adds them to older DBs
- backfills grammar-score consistency
- backfills missing `report_filename` values for older rows

This tells us the project evolved over time and the developer chose schema compatibility over formal migrations.

### Route-by-route explanation

#### `GET /`

Purpose: basic root test route. It takes no input and returns a small JSON message proving the backend is alive.

#### `POST /api/auth/register`

Purpose: create a new user and immediately authenticate them.

Processing:

- validates password match
- checks for existing email
- hashes the password with PBKDF2
- inserts a `User`
- creates an access token

Response:

- token
- token type
- user summary

#### `POST /api/auth/login`

Purpose: authenticate an existing user.

Processing:

- looks up the email
- verifies the password hash
- creates a token

Response:

- token
- user summary

#### `GET /api/profile`

Purpose: fetch the current authenticated user profile. It reads the `Authorization` header, verifies the token, resolves the `User` from the database, and returns profile fields such as `full_name`, `age`, `gender`, `location`, `occupation`, `primary_goal`, and `bio`.

#### `PUT /api/profile`

Purpose: update editable profile fields. It requires authentication, overwrites the editable fields on the current user, commits the change, and returns the updated profile.

#### `POST /api/analyze`

Purpose: main audio analysis endpoint.

Processing in order:

1. Validate file type and extension.
2. Generate a UUID `audio_id`.
3. Save the original upload to `storage/uploaded_audio/`.
4. Create a DB `Analysis` row with status `processing`.
5. Normalize audio with `ffmpeg` into `storage/processed_audio/{audio_id}.wav`.
6. Run `run_full_analysis(processed_path)`.
7. Generate a report filename based on user and date.
8. Try to generate a PDF.
9. Update the database record with transcript, probabilities, counts, scores, PDF path, and status `completed`.
10. Return the ORM object as the response model.

If any error occurs:

- the DB row is marked `failed`
- `error_message` is stored
- FastAPI returns HTTP 500

#### `GET /api/analyze/{audio_id}`

Purpose: fetch one saved analysis in detail.

Processing:

- query `Analysis` by `audio_id`
- if a current user exists and does not own the record, deny access
- normalize grammar metrics

Important security nuance:

If there is **no authenticated user**, the code does not reject the request. It returns the analysis if the `audio_id` is known. That makes this effectively public-by-default unless login is present.

#### `GET /api/analyses`

Purpose: fetch analysis history.

Processing:

- if logged in, return only the current user's analyses
- if not logged in, return **all analyses**
- normalize grammar score before returning

This is another important security limitation. In a production system, unauthenticated users should not receive everyone else's analysis history.

#### `GET /api/reports/{audio_id}`

Purpose: download the PDF report for an analysis.

Processing:

- look up the analysis
- if a current user exists and does not own it, deny access
- verify the PDF path exists
- stream the file with `FileResponse`

Again, if no user is authenticated and the `audio_id` is known, the route is still reachable.

#### `GET /api/training/modules`

Purpose: return the static guided-practice catalog. It loads the module list from `training_catalog.py` and reshapes it into response objects.

#### `POST /api/training/session/start`

Purpose: create a session record before a user attempts an exercise.

Processing:

- requires authentication
- validates the requested module and exercise key
- inserts a `TrainingSession` with status `started`

Response includes:

- `session_id`
- module and exercise metadata
- input mode
- prompt and expected text

#### `POST /api/training/session/evaluate`

Purpose: score one practice attempt.

Processing:

- requires authentication
- loads the user's session
- if a file is present:
  - saves upload
  - normalizes audio
  - calls `evaluate_audio_attempt()`
- otherwise:
  - calls `evaluate_text_attempt()`
- writes transcript, scores, counts, corrected text, and feedback into the session row
- marks session `completed` or `failed`
- syncs aggregate `TrainingProgress` if completed

#### `GET /api/training/session/{session_id}`

Purpose: fetch a single training attempt. It requires authentication and restricts results to the current user's session.

#### `GET /api/training/sessions`

Purpose: fetch recent training attempts. It requires authentication and returns up to 20 latest sessions for that user.

#### `GET /api/training/progress`

Purpose: fetch module-level aggregate progress. It requires authentication, queries `TrainingProgress`, rounds scores, and returns module stats.

#### `GET /api/health`

Purpose: health check for frontend or deployment tools. It returns a small service-status JSON.

#### `POST /api/chat`

Purpose: SpeechWell AI coach endpoint.

Processing:

- validates the message
- if authenticated, optionally loads the user's latest or selected analysis
- converts the analysis into context text
- calls `generate_chat_reply()`
- maps provider and network errors into HTTP errors

### Controllers, services, and persistence layers

Although the project does not use a strict "controllers, services, repositories" architecture, the code naturally separates into:

- **Route/controller layer**: `backend/app/main.py`
- **Schema layer**: `backend/app/schemas.py`
- **Persistence layer**: `backend/app/database/db.py` and `models.py`
- **Service layer**: `backend/app/services/*.py`
- **ML orchestration layer**: `ml/services/speech_analysis_service.py`
- **Feature extraction and model layer**: `ml/feature_extraction/*.py` and `ml/models/*.pkl`

That separation makes the code much easier to reason about than if all logic were in one route file.

## Section 6: Data Pipeline

### Two different pipelines exist

This project has **two** major data pipelines:

1. **Runtime inference pipeline** for a user-uploaded file.
2. **Offline training pipeline** for building dysarthria models from datasets.

You need to understand both.

### Runtime input data

At runtime, the input is one user audio file. It may come in as:

- WAV
- MP3
- WEBM
- OGG
- M4A

The backend accepts these formats and then standardizes them.

### Runtime preprocessing

#### Audio normalization

`main.py` calls `normalize_audio()` which runs:

```text
ffmpeg -y -i input -ac 1 -ar 16000 output.wav
```

This means:

- `-ac 1` -> convert to mono
- `-ar 16000` -> resample to 16 kHz

Why that matters:

- speech models often expect a consistent sample rate
- mono audio removes channel mismatch
- standardization makes features comparable across files

#### Whisper feature extraction

`extract_whisper.py` handles transcription and timing features.

Outputs include:

- `transcript`
- `total_words`
- `speaking_rate_wps`
- `average_pause_sec`
- `max_pause_sec`
- `total_duration_sec`
- `pause_durations`
- `long_pause_count`
- `segments`
- `transcription_model`

Pause calculation uses a smart fallback strategy:

1. It first tries to detect pauses directly from waveform silence using `librosa.effects.split()`.
2. If that fails, it computes pauses from the gaps between Whisper segments.

That is a good design choice because Whisper segments can be artificially continuous and may hide true acoustic pauses.

#### Acoustic embedding extraction

`extract_acoustic.py` creates a 768-dimensional embedding using offline `facebook/wav2vec2-base`.

If the model is unavailable locally, it returns a zero vector instead of crashing the entire analysis.

#### Raw audio feature extraction

`raw_audio_features.py` is central to the modern dysarthria pipeline and produces approximately 98 numeric features.

It computes:

**Basic statistics (10 features):**
- amplitude statistics: `rms`, `mean_abs`, `std`, `max_abs` plus quantiles `q25_abs`, `q50_abs`, `q75_abs`
- `silence_ratio` - fraction of signal below silence threshold
- `duration_sec` - total audio duration

**Frequency domain baseline (8 features):**
- zero-crossing rate: `zcr` (global) plus `zcr_frame_mean` and `zcr_frame_std` (frame-level statistics)
- spectral centroid
- spectral bandwidth
- spectral rolloff at 85 percent
- spectral flatness

**Timbre and harmonic features (4 features):**
- chroma: `chroma_mean` and `chroma_std`
- spectral contrast: `spectral_contrast_mean` and `spectral_contrast_std`

**MFCC coefficients and temporal derivatives (78 features):**
- MFCC: mean and std for 13 coefficients = 26 features
- delta MFCC: mean and std for 13 coefficients = 26 features
- delta-delta MFCC: mean and std for 13 coefficients = 26 features

**Metadata (2 features):**
- `sample_rate` - resampling confirmation (always 16000 Hz)
- `channels` - channel count confirmation (always 1)

**Total: ~98 features per audio sample**

Important nuance:

- the default model feature row uses only the first `TARGET_FRAMES = 8000` samples
- at 16 kHz, that is about 0.5 seconds of audio
- symptom-gating later re-extracts features from the **full recording**

So the system uses:

- a fast prefix snapshot for the classifier
- a full-recording feature pass for sanity-checking symptoms

That hybrid design is unusual, and important to understand.

### Feature engineering logic

The modern dysarthria classifiers work on hand-engineered tabular features.

The feature engineering idea is:

1. Convert a variable-length waveform into a fixed set of numbers.
2. Make those numbers capture energy, rhythm, noisiness, and spectral shape.
3. Feed the fixed-size numeric vector into classical ML models like SVC, Random Forest, or HistGradientBoosting.

This is different from an end-to-end deep neural network. It is more interpretable and easier to train on smaller tabular datasets.

### JSON and CSV structure usage

Main training CSVs:

- `torgo_index.csv`: file paths and labels
- `torgo_audio_features_v4.csv`: extracted tabular features from TORGO
- `combined_dysarthria_index.csv`: TORGO plus optional UASpeech index
- `combined_audio_features.csv`: extracted tabular features from the combined set

JSON is used mainly for:

- saved validation reports
- comparison reports
- cached runtime outputs in `storage/results/`

## Section 7: Machine Learning and Models

### Model 1: Whisper transcription model

Type: speech-to-text model.

Why it is used: everything else depends on having a transcript and timing structure. Stuttering, grammar, and phonological heuristics all use transcript content or segment timing.

Training process: not trained in this repository. The app loads a pretrained Whisper model, preferring:

- configured `WHISPER_MODEL`
- then `small.en`
- then `base.en`
- then `base`

Input features: normalized mono 16 kHz audio.

Output:

- transcript text
- segment boundaries
- derived timing features

### Model 2: Wav2Vec2 acoustic embedding model

Type: pretrained self-supervised speech representation model.

Why it is used: acoustic embeddings can capture voice characteristics beyond simple timing features.

Training process: not trained here. It loads `facebook/wav2vec2-base` locally in offline mode.

Input features: normalized waveform.

Output prediction: not a class label by itself; it outputs a 768-dimensional vector.

Where it is used:

- legacy dysarthria pipeline
- runtime acoustic embedding field in `speech_analysis_service.py`

### Model 3: Dysarthria v1 logistic regression pipeline

Type: classical binary classifier.

Why it was used: it was a reasonable early baseline because it is easy to train and interpret.

Training process:

- extract Whisper fluency features
- extract Wav2Vec2 embedding
- standardize embedding
- reduce embedding with PCA
- concatenate with fluency features
- fit logistic regression with `max_iter=5000` and `class_weight="balanced"`

Input features:

- speaking rate
- average pause
- max pause
- PCA-reduced acoustic embedding

Output prediction:

- probability of dysarthria
- binary label using threshold 0.5, later optionally adjusted by symptom gating

What happens when one sample enters:

1. The sample is turned into a 43-dimensional vector: 3 fluency features plus 40 PCA components.
2. Logistic regression computes a weighted sum `z = w^T x + b`.
3. The sigmoid function converts that into a probability between 0 and 1.
4. A threshold turns that probability into a label.
5. In newer runtime code, symptom gating can still override or dampen that raw label.

Loss function intuition:

- logistic regression minimizes binary cross-entropy
- wrong confident predictions are penalized heavily
- `class_weight="balanced"` increases pressure to fit the minority class

Saved artifacts:

- `dysarthria_model_v1.pkl`
- `dysarthria_scaler_v1.pkl`
- `dysarthria_pca_v1.pkl`

Evaluation snapshot from `validation_report.json`:

- accuracy about `0.8309`
- precision about `0.7461`
- recall about `0.7827`
- F1 about `0.7640`

### Model 4: Dysarthria v2 RF+SVC ensemble

Type: soft-voting ensemble of:

- Random Forest
- RBF-kernel SVC with probability output

Why it is used:

- Random Forest is strong on nonlinear tabular data and robust to mixed feature interactions.
- SVC is often strong on medium-sized feature spaces with nonlinear boundaries.
- Soft voting can combine their strengths by averaging probabilities.

Training process:

1. Load tabular audio features from CSV.
2. Drop leaky runtime-specific columns such as `sample_rate` and `channels` from the effective feature list.
3. Impute missing numeric values with the median.
4. Standardize numeric features.
5. Split into train, validation, and test, either stratified or group-aware.
6. Rebalance overly positive-heavy training sets.
7. Apply sample weights.
8. Train candidate RF and SVC voting-weight combinations.
9. Pick a threshold on the validation set.
10. Retrain on combined train and validation and save the final artifact.

Key hyperparameters in the dedicated trainer:

- Random Forest: `n_estimators=300`, `class_weight="balanced_subsample"`, `random_state=42`
- SVC: `kernel="rbf"`, `C=5`, `gamma="scale"`, `probability=True`, `class_weight="balanced"`, `random_state=42`
- Voting weights searched: `(1,1)`, `(1,2)`, `(1,3)`, `(2,3)`
- Saved artifact in this repository: threshold `0.81`

Input features:

- raw audio tabular features from `raw_audio_features.py`

Output prediction:

- probability of dysarthria
- label determined by the saved threshold plus runtime symptom gating

What happens when one sample enters:

1. The single-row feature frame goes through median imputation, so any missing numeric feature is filled.
2. StandardScaler shifts and scales features using the training-set mean and standard deviation.
3. The Random Forest produces a probability by averaging the votes of many decision trees.
4. The SVC maps the sample into an RBF kernel space, computes a margin-based score, and converts that score into a probability because `probability=True`.
5. The ensemble averages those probabilities using the chosen RF and SVC weights.
6. The saved threshold converts the blended probability into a provisional label.
7. Runtime symptom gating performs the final safety adjustment.

Saved artifact behavior in this repo:

- saved threshold `0.81`
- saved feature column count `98`

Holdout metrics from `dysarthria_model_v2_rf_svc_ensemble_report.json`:

- accuracy `0.9367`
- precision `1.0000`
- recall `0.9232`
- F1 `0.9600`

Full-dataset validation metrics from `validation_report_v2_rf_svc_ensemble.json`:

- accuracy `0.9846`
- precision `0.9940`
- recall `0.9618`
- F1 `0.9776`

### Model 5: Dysarthria best comparison model

Type: currently HistGradientBoosting-based binary classifier.

Why it is used:

- the comparison script tested several model families
- HistGradientBoosting won under that comparison report
- the runtime now prefers this saved artifact when present

Compared models:

- calibrated logistic regression
- RBF SVC
- Random Forest
- RF+SVC ensemble
- HistGradientBoostingClassifier

Training process:

- same tabular features as the v2 pipeline
- same preprocessors
- same train, validation, test logic
- same threshold tuning concept
- compare all candidate model families and save the single best-performing pipeline

Key hyperparameters from the comparison script:

- Calibrated logistic regression: `max_iter=4000`, `class_weight="balanced"`, `cv=3`, calibration `method="sigmoid"`
- Random Forest: `n_estimators=350`, `class_weight="balanced_subsample"`, `random_state=42`
- RF+SVC ensemble: weights `[2.0, 3.0]`
- HistGradientBoosting: `learning_rate=0.05`, `max_depth=6`, `max_iter=250`, `random_state=42`
- Threshold sweep: `0.25` to `0.89` in steps of `0.02`, preferring thresholds that satisfy recall `>= 0.80`

Saved artifact behavior in this repo:

- `best_model_name = hist_gradient_boosting`
- threshold `0.85`

Holdout metrics from `dysarthria_model_comparison_report.json`:

- accuracy `0.9449`
- precision `0.9996`
- recall `0.9335`
- F1 `0.9654`

What happens when one sample enters the active comparison-model artifact:

1. The normalized audio is converted into the same numeric feature schema used during training.
2. Missing values are imputed and all features are standardized.
3. HistGradientBoosting routes the sample through many shallow trees learned stage-by-stage on residual errors.
4. Each boosting stage adds a small correction to the previous score.
5. The final raw score is passed through a logistic link to obtain a class probability.
6. The saved threshold `0.85` converts that probability into a provisional label.
7. The dysarthria service then applies symptom gating, which means the deployment decision is stricter than the bare model output.

### Model 6: Grammar correction providers

Type: external large language models.

Supported providers:

- OpenAI chat completion models
- Gemini models
- local Ollama chat models

Why they are used: the project wants a corrected version of the transcript so it can estimate grammar error probability and display a cleaner suggested sentence.

Important note: grammar scoring is **not** purely LLM-based. The project also performs structural heuristics locally so it still has a fallback if no provider is reachable.

### Model 7: Stuttering and phonological modules

Type: rule-based heuristic modules rather than trained ML classifiers.

Why they are used:

- the project has enough signal to build useful heuristics
- the repository does not include a separate labeled stuttering or phonological training corpus

Input:

- transcript
- segment timing
- some acoustic features

Output:

- probability-like risk scores
- event counts

These are best understood as engineered scoring modules, not clinically validated classifiers.

## Section 8: Algorithms and Formulas

### Audio feature formulas

#### RMS energy

```text
RMS = sqrt((1 / N) * sum(x_n^2))
```

Intuition: square the waveform values, average them, then take the square root. Louder or more energetic speech gives higher RMS.

#### Zero-crossing rate

```text
ZCR = number of sign changes / (N - 1)
```

Intuition: count how often the waveform crosses zero. Very noisy or high-frequency content can increase this.

#### Spectral centroid

```text
centroid = sum(f_k * S_k) / sum(S_k)
```

Intuition: this is the "center of mass" of the spectrum. Brighter sound pushes the centroid upward.

#### Spectral bandwidth

```text
bandwidth = sqrt(sum((f_k - centroid)^2 * S_k) / sum(S_k))
```

Intuition: how spread out the spectral energy is around the centroid.

#### Spectral rolloff

Definition: the frequency where cumulative energy reaches a chosen fraction of total energy. In this code, the fraction is 85 percent.

#### Spectral flatness

```text
flatness = geometric_mean(power) / arithmetic_mean(power)
```

Intuition:

- close to 0 -> tone-like or peaky spectrum
- closer to 1 -> noise-like or flat spectrum

#### MFCCs

High-level pipeline:

```text
waveform
-> short-time Fourier transform
-> mel filterbank energies
-> log energies
-> discrete cosine transform
-> MFCC coefficients
```

Compact formula idea:

```text
MFCC = DCT(log(MelFilterBank(|STFT(x)|^2)))
```

#### Delta and delta-delta MFCC

Meaning:

- delta = first temporal derivative
- delta-delta = second temporal derivative

Intuition: not just "what spectral shape is present," but "how fast is it changing?"

### Machine-learning formulas

#### Logistic regression

```text
p(y = 1 | x) = sigma(w^T x + b)
sigma(z) = 1 / (1 + e^(-z))
```

Decision boundary:

```text
predict dysarthria if p >= threshold
```

Training loss:

```text
L = -[y log(p) + (1 - y) log(1 - p)]
```

Meaning:

- if the true label `y` is 1, the model is rewarded for making `p` large
- if the true label `y` is 0, the model is rewarded for making `p` small
- confident mistakes create large loss

#### StandardScaler

```text
z = (x - mu) / sigma
```

#### PCA

```text
z_reduced = W^T z
```

#### SVC with RBF kernel

```text
f(x) = sign(sum(alpha_i * y_i * K(x_i, x)) + b)
K(x_i, x) = exp(-gamma * ||x_i - x||^2)
```

Intuition:

- `C` controls how harshly margin violations are punished
- `gamma` controls how local or global the nonlinear boundary is
- support vectors are the training samples that define the decision boundary

#### Random Forest probability

```text
p_rf(y = 1 | x) = (1 / T) * sum(tree_t_prediction)
```

where `T` is the number of trees and each tree contributes a class probability from the terminal leaf that receives the sample.

#### Soft-voting ensemble

```text
p_ensemble = weighted_average(p_rf, p_svc)
```

#### HistGradientBoosting

Conceptual additive model:

```text
F_m(x) = F_(m-1)(x) + eta * h_m(x)
```

Probability view for binary classification:

```text
p(y = 1 | x) = sigma(F_M(x))
```

Intuition:

- start with a rough score
- fit a new tree to the remaining mistakes
- add a small correction with learning rate `eta`
- repeat for many boosting rounds until the model captures complex nonlinear structure

### Thresholding logic

The training scripts:

- scan thresholds from `0.25` to `0.89` in steps of `0.02`
- compute accuracy, precision, recall, and F1
- prefer thresholds that meet a minimum recall target (default `0.80`)
- among thresholds meeting the recall floor, choose the one with better precision
- if none meet the recall floor, fall back to the threshold with best F1

Runtime dysarthria classification is **not** just `probability >= threshold`. It also considers symptom evidence and healthy-speech signals before finalizing the label.

## Section 9: Module Logic

### Dysarthria detection module

Input:

- normalized audio file path
- Whisper timing features
- acoustic embedding vector

Processing:

1. Load the newest available dysarthria artifact.
2. Extract raw-audio tabular features for the model input.
3. Extract raw-audio features again across the full recording for symptom analysis.
4. Predict a raw dysarthria probability.
5. Compute symptom score from:
   - low RMS
   - high silence ratio
   - high spectral flatness
   - abnormal ZCR
   - high MFCC variance
6. Count healthy-speech signals such as enough words, normal speaking rate, acceptable pauses, enough duration, acceptable silence ratio, and sufficient RMS.
7. Apply symptom-gated decision logic.
8. Return:
   - `label`
   - `probability`
   - `symptom_score`
   - `explanation`
   - `model_version`

Important thresholds:

- `ACCENT_MISMATCH_FLOOR = 0.65`
- `SYMPTOM_GATED_DYSARTHRIA_THRESHOLD = 0.75`
- `RAW_PROBABILITY_OVERRIDE_THRESHOLD = 0.95`
- saved ensemble threshold `0.81`
- saved comparison-model threshold `0.85`

In plain English: if the model says "high risk" but the recording does **not** show enough dysarthria-like symptoms, the system distrusts the model and pushes the probability down.

### Stuttering detection module

Input:

- transcript
- Whisper segments
- pause durations
- speaking rate
- optionally full-recording acoustic features

Processing:

1. Tokenize transcript words.
2. Count repetitions from repeated tokens and repaired starts.
3. Count prolongations from stretched vowel spellings, fragment patterns, and abnormally slow short segments.
4. Count blocks from pauses above thresholds.
5. Compute normalized sub-scores.
6. Blend them into one final stuttering probability.

Output:

- `stuttering_probability`
- repetition, prolongation, and block counts
- `fluency_score`
- total disfluency events

Important thresholds:

- block threshold: `0.9` seconds
- severe block threshold: `1.5` seconds

Weighted final score:

```text
0.28 * repetition_score
0.24 * prolongation_score
0.26 * block_score
0.08 * severe_block_bonus
0.09 * pause_variability
0.03 * segment_rate_variability
0.02 * speaking_rate_penalty
```

### Phonological or articulation proxy module

Input:

- transcript
- segment timing

Processing:

1. Find one-letter fragments that look like broken starts.
2. Find repaired words like a fragmented onset followed by the full word.
3. Detect exaggerated elongated spellings.
4. Count very slow short segments.
5. Measure segment-rate variability.
6. Combine them into a probability-like score using weighted components:
   - `fragment_ratio * 0.35` - proportion of one-letter fragments
   - `repair_ratio * 0.30` - proportion of repaired/restarted words
   - `elongation_ratio * 0.15` - proportion of words with prolonged vowels
   - `segment_instability * 0.10` - coefficient of variation in segment rates
   - `slow_segment_ratio * 0.10` - proportion of unusually slow short segments

Output:

- `phonological_error_probability` - bounded [0.0, 1.0]
- `error_count` - total number of articulation-proxy events detected
- `affected_words` - up to 10 examples of affected words (fragments, repairs)

Special handling:

- If fewer than 2 segments with adequate data, variability score is 0.0
- Fragment ratio excludes articles like "a" and "i"
- Slow segment threshold depends on word count: ≤3 words requires ≥0.85 sec/word, single word requires ≥1.1 sec

This is called a proxy because true phonological diagnosis usually requires expected target words, phoneme-level alignment, and clinical interpretation. The app does not have those. Instead, it estimates articulation-instability risk from observable transcript patterns.

### Grammar analysis module

Input:

- transcript text

Processing:

1. Normalize whitespace and tokens.
2. Ask a configured provider to produce a corrected transcript, if available.
3. Estimate raw edit count between original and corrected text.
4. Estimate structural grammar issues from fragments, verb gaps, fillers, odd tokens, punctuation issues, and telegraphic structure.
5. Blend the structural estimate and diff estimate into a probability.
6. Convert that into a quality score.

Output:

- `grammar_error_probability`
- `grammar_quality_score`
- `error_count_estimate`
- `corrected_text`

Important distinction: the code stores `grammar_score` as a **quality** score where higher is better, but the grammar service also computes a **grammar error probability** where higher means worse.

### Overall speech score module

This is not a separate classifier. It is a score combiner.

Inputs:

- dysarthria probability
- stuttering probability
- grammar quality score

Processing:

```text
pronunciation = (1 - dysarthria) * 100
fluency = (1 - stuttering) * 100
clarity = grammar * 100
weighted_average = 0.35 * pronunciation + 0.25 * fluency + 0.40 * clarity
weakest_skill = min(pronunciation, fluency, clarity)
overall = 0.7 * weighted_average + 0.3 * weakest_skill
```

Output:

- integer `overall_score` between 0 and 100

This means the system rewards balanced performance. One very weak dimension can pull the final score down more than a plain weighted average would.

## Section 10: Training Process

### Dataset used

The main dysarthria dataset in the repository is **TORGO**.

Observed corpus organization:

- `F_Con`: female control recordings
- `F_Dys`: female dysarthric recordings
- `M_Con`: male control recordings
- `M_Dys`: male dysarthric recordings

Observed counts in this workspace:

- total WAV files: `17,635`
- control rows in indexed TORGO data: `11,456`
- dysarthria rows in indexed TORGO data: `6,179`

Optional augmentation:

- `build_combined_dysarthria_index.py` can also include a Kaggle UASpeech dysarthria-only dataset
- that creates a larger **positive-heavy** combined dataset
- because UASpeech is treated as dysarthria-only, it cannot replace healthy samples from TORGO

### How data is split

The modern training scripts support two styles:

1. **Standard stratified split**
2. **Group-aware split** using `GroupShuffleSplit`

Default proportions:

- 70 percent train
- 15 percent validation
- 15 percent test

In group-aware mode, grouping is usually by:

- speaker
- or dataset plus speaker

That is important because speech from the same speaker leaking across train and test can make performance look better than it really is.

### How CSV and JSON are used in training

Training CSV sequence:

1. raw WAV dataset
2. `torgo_index.csv` or `combined_dysarthria_index.csv`
3. `torgo_audio_features_v4.csv` or `combined_audio_features.csv`
4. model training script loads the feature CSV
5. model artifact is saved as `.pkl`
6. evaluation report is saved as `.json`

JSON reports save:

- selected threshold
- holdout metrics
- confusion matrix
- sometimes metadata such as class weighting

### Model training pipeline

TORGO-only modern path:

1. Run `build_torgo_dataset.py` to create an index.
2. Run `build_torgo_audio_features.py` to extract features into a CSV.
3. Train either:
   - `train_dysarthria_rf_svc_ensemble.py`
   - or `train_dysarthria_model_comparison.py`
4. Save the resulting model artifact to `ml/models/`.
5. Save evaluation JSON to `ml/evaluation/`.

Combined-data path:

1. Run `build_combined_dysarthria_index.py`.
2. Run `build_torgo_audio_features.py --index ... --output ...`.
3. Run `train_dysarthria_model_comparison.py` or the ensemble trainer on the combined CSV.

### Saving and loading models

The project uses `joblib` for model artifacts.

Artifact styles:

- plain classifier object
- or dictionary with:
  - `pipeline`
  - `threshold`
  - `feature_columns`
  - `metadata`
  - possibly `best_model_name`

Runtime loading behavior in `dysarthria_inference_service.py`:

1. load `ml/models/dysarthria_best_comparison_model.pkl` if it exists
2. else load `ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl`
3. else load the legacy v1 model, scaler, and PCA

That fallback chain is one of the most important architectural facts in the repository.

## Section 11: Inference Flow (Real-World Usage)

### When a user uploads audio

Step-by-step real execution flow:

1. User picks a file or records audio in the browser.
2. `Upload.tsx` validates the file type and size.
3. Frontend sends the file to `POST /api/analyze`.
4. Backend creates `audio_id`.
5. Backend stores the raw file in `storage/uploaded_audio/`.
6. Backend inserts an `Analysis` row with status `processing`.
7. Backend calls `ffmpeg` to create a mono 16 kHz WAV in `storage/processed_audio/`.
8. `ml/services/speech_analysis_service.py` runs.
9. Whisper creates transcript and timing features.
10. Grammar service corrects the transcript and estimates grammar quality.
11. Acoustic embedding extraction runs; if it fails, a zero vector is used.
12. Dysarthria inference runs using the active saved model plus symptom gating.
13. Stuttering detection runs using transcript, segment, pause, and optional acoustic features.
14. Phonological proxy detection runs using transcript instability patterns.
15. Backend computes report filename and tries to generate a PDF.
16. Backend writes all final values into the `Analysis` row and marks it `completed`.
17. JSON response is returned to the frontend.
18. Frontend stores `audio_id` in `sessionStorage` and navigates to `Results`.
19. Results page can re-fetch the stored analysis with `GET /api/analyze/{audio_id}`.

### How prediction is generated

The most important prediction path is the dysarthria path:

1. extract raw features
2. load the best pipeline artifact
3. get raw probability from `predict_proba`
4. compute symptom score from full-audio signals
5. count healthy-speech signals
6. adjust probability downward if the model looks overconfident without symptoms
7. compare against threshold
8. return final label and explanation

So the final answer is a hybrid of:

- learned model probability
- hand-authored symptom logic

### How results are returned to UI

The analysis response includes fields such as:

- `audio_id`
- `filename`
- `overall_score`
- `dysarthria_probability`
- `dysarthria_label`
- `stuttering_probability`
- `grammar_score`
- `grammar_error_probability`
- `phonological_score`
- `transcript`
- `corrected_text`
- timing metrics
- `pdf_path`
- `report_filename`
- `status`

The React pages then decide how to present this:

- `Results.tsx` shows the detailed one-analysis view
- `History.tsx` shows summary rows
- `Dashboard.tsx` computes trends from the history list

## Section 12: Performance and Evaluation

### Metrics used

For dysarthria models, the repo uses:

- accuracy
- precision
- recall
- F1 score
- confusion matrix
- classification report

These are standard binary-classification metrics.

### Why thresholds matter

The saved probability threshold matters because the model is not judged only by "what is the highest probability," but also by how that probability is converted into a yes or no label.

Examples from this repo:

- RF+SVC ensemble threshold: `0.81`
- best comparison model threshold: `0.85`

Higher thresholds usually:

- reduce false positives
- risk missing some true positives

### Validation numbers in this repository

#### Legacy v1 model

From `validation_report.json`:

- accuracy `0.8309`
- precision `0.7461`
- recall `0.7827`
- F1 `0.7640`

#### Group-aware v2 validation

From `validation_report_v2_group.json`:

- accuracy `0.9563`
- precision `0.9611`
- recall `0.9118`
- F1 `0.9358`

This is one of the more realistic performance summaries because it is grouped by speaker.

#### Full-dataset v2 validation

From `validation_report_v2_rf_svc_ensemble.json`:

- accuracy `0.9846`
- precision `0.9940`
- recall `0.9618`
- F1 `0.9776`
- confusion matrix `[[11419, 36], [235, 5922]]`

This number looks excellent, but beginners should understand that it is more optimistic because the validation script predicts over the full available dataset rather than a clean grouped holdout.

#### Comparison-script best model

From `dysarthria_model_comparison_report.json`:

- accuracy `0.9449`
- precision `0.9996`
- recall `0.9335`
- F1 `0.9654`
- threshold `0.85`

#### RF+SVC ensemble on combined data

From `dysarthria_model_v2_rf_svc_ensemble_report.json`:

- accuracy `0.9367`
- precision `1.0000`
- recall `0.9232`
- F1 `0.9600`
- threshold `0.81`

### Confusion matrix interpretation

For a binary dysarthria detector:

```text
[[TN, FP],
 [FN, TP]]
```

Meaning:

- `TN`: healthy speech correctly labeled healthy
- `FP`: healthy speech incorrectly labeled dysarthria
- `FN`: dysarthria incorrectly labeled healthy
- `TP`: dysarthria correctly labeled dysarthria

This is useful because raw accuracy can hide the difference between missing real cases and raising false alarms.

### What is not formally evaluated here

The repository does **not** contain equally rigorous offline evaluation files for:

- stuttering scoring
- grammar scoring
- phonological proxy scoring
- overall-score calibration

Those modules are still operational, but they are less empirically validated than the dysarthria pipeline.

## Section 13: Complete System Flow

Here is the complete end-to-end system flow in one view:

```text
User
  |
  | records or uploads audio
  v
Frontend Upload Page
  |
  | POST /api/analyze (multipart/form-data)
  v
FastAPI Backend
  |
  |-- save original file
  |-- create analysis row
  |-- ffmpeg normalize
  |-- run speech_analysis_service
  |     |-- Whisper transcription
  |     |-- Grammar correction and scoring
  |     |-- Acoustic embedding
  |     |-- Dysarthria model + symptom gating
  |     |-- Stuttering scoring
  |     `-- Phonological proxy scoring
  |
  |-- save results in SQLite
  |-- generate PDF report
  v
JSON response
  |
  v
Frontend Results Page
  |
  |-- detailed result rendering
  |-- history view
  |-- dashboard analytics
  |-- report download
  `-- therapy and AI-coach follow-up
```

## Section 14: How to Rebuild This Project From Scratch

### Step 1: Install prerequisites

You need:

- Python 3.10+ or similar
- Node.js and npm
- `ffmpeg` available on your PATH
- Git
- optionally Git LFS for large `.pkl` artifacts
- optionally Ollama plus a local model if you want local chat and grammar correction

### Step 2: Clone and prepare Python

Example Windows steps:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Prepare frontend

```powershell
cd speechwell-frontend
npm install
cd ..
```

### Step 4: Configure environment

Copy `.env.example` to `.env` and set the values you want:

- `CHAT_PROVIDER`
- `GRAMMAR_PROVIDER`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `WHISPER_MODEL`
- optional cloud API keys and model names

If you want a fully local stack, keep providers on Ollama and make sure the local model is already available.

### Step 5: Start backend and frontend

Backend:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
cd speechwell-frontend
npm run dev
```

Then open:

- frontend: `http://localhost:5173`
- backend docs/status root: `http://localhost:8000`

### Step 6: Rebuild the dysarthria model from raw TORGO data

If you have the TORGO WAV folders under `ml/datasets/torgo/TORGO_RAW/`:

```powershell
python ml/training/build_torgo_dataset.py
python ml/training/build_torgo_audio_features.py --index ml/training/torgo_index.csv --output ml/training/torgo_audio_features_v4.csv
python ml/training/train_dysarthria_rf_svc_ensemble.py --data ml/training/torgo_audio_features_v4.csv
```

If you want to compare several model families:

```powershell
python ml/training/train_dysarthria_model_comparison.py --data ml/training/combined_audio_features.csv --group-aware --group-by-dataset --positive-weight 1.15 --max-positive-ratio 0.55
```

### Step 7: Validate the trained artifact

```powershell
python ml/evaluation/validate_accuracy.py
```

Read the generated JSON reports in `ml/evaluation/`.

### Step 8: Generate documentation PDFs

For the technical report:

```powershell
python scripts/render_report_pdf.py
```

For this learning manual:

```powershell
python scripts/render_learning_manual_pdf.py
```

### Step 9: Understand what is optional

You do **not** need to retrain models every time to run the app.

You only need retraining when:

- you changed the feature logic
- you changed the dataset
- you want a better or newer model
- the saved model pickle is missing or incompatible

## Section 15: Debugging, Edge Cases, and Common Confusions

### What happens if the audio is noisy?

The project does not run explicit denoising at inference time. The only guaranteed preprocessing step is format normalization through `ffmpeg`, which converts the input into mono 16 kHz WAV. That means noisy audio flows directly into Whisper and the handcrafted feature extractor.

Likely effects:

- Whisper transcript quality drops.
- Pause and segment timing become less trustworthy.
- Spectral flatness may rise because noise looks more noise-like than voiced speech.
- Zero-crossing behavior can become less stable.
- The dysarthria classifier may see abnormal tabular features even when the cause is recording quality rather than pathology.

Why this matters: dysarthria inference is protected by symptom gating, but the handcrafted symptom score itself still depends on noisy acoustic statistics. So the guardrail reduces some false alarms, but it cannot eliminate channel-quality bias.

### What happens if the input is too short?

Short clips stress almost every module:

- Whisper has less context, so transcript confidence drops.
- Pause statistics become unstable because one silence dominates the whole clip.
- Speaking rate becomes noisy because a tiny word count over a tiny duration can swing wildly.
- Heuristic stuttering and phonological rules have too little evidence.

The raw feature extractor handles short audio by padding the waveform when needed, but mathematically that means some summary features partly describe silence rather than speech. That can flatten the signal and reduce reliability.

### What happens if the acoustic embedding model is unavailable?

[`ml/feature_extraction/extract_acoustic.py`](/c:/Users/franc/OneDrive/Documents/Projects/SpeechWell/ml/feature_extraction/extract_acoustic.py) forces offline loading for `facebook/wav2vec2-base`. If the local files are not present, it returns a zero vector of length `768`.

Why this is acceptable in the current runtime:

- the active dysarthria pipeline usually uses raw tabular audio features instead of the embedding
- the embedding mainly matters for the legacy v1 fallback path

So the system degrades gracefully for the current preferred model, but the legacy path becomes much weaker.

### What happens if `ffmpeg` is missing?

`normalize_audio()` in [`backend/app/main.py`](/c:/Users/franc/OneDrive/Documents/Projects/SpeechWell/backend/app/main.py) depends on a subprocess call to `ffmpeg`. If `ffmpeg` is not installed or not on `PATH`, normalization fails and the analysis route returns an error.

Operational consequence: the whole audio-analysis pipeline is blocked, because downstream code assumes a normalized WAV path exists.

### What happens if grammar or chat providers are unavailable?

The grammar and chat services are intentionally multi-provider:

- OpenAI
- Gemini
- Ollama
- fallback local heuristics

If a provider is misconfigured or unreachable, the project can still fall back to heuristic correction behavior. That preserves the pipeline, but quality drops from model-based rewriting to rule-based approximation.

### What happens if a user is unauthenticated?

The upload route itself can still work because authentication is optional on several analysis endpoints. That is convenient for demos, but risky for production because a guessed analysis ID can expose stored results or reports.

This is not just a security note. It also changes debugging expectations: if you see analysis history loading without a login boundary, that is current code behavior, not a frontend bug.

### "Why are there two speechwell.db files?"

Analogy: one is the live notebook, the other is an old spare notebook left in the drawer.

- root `speechwell.db` is the active one
- `backend/speechwell.db` is stale or legacy

The source of truth is `backend/app/paths.py`.

### "Why does the dashboard score not always match the result score?"

Because the dashboard computes a client-side trend metric, while the backend computes `overall_score` using a different formula. They sound similar, but they are not the same number.

### "Is phonological detection a real diagnosis?"

No. It is closer to a warning light than a doctor. It notices unstable transcript patterns that may suggest articulation problems, but it is not a full phoneme-level clinical assessment.

### "Why does grammar_score go up when grammar_error_probability goes down?"

Because they measure opposite directions:

- `grammar_error_probability`: higher is worse
- `grammar_score` or grammar quality: higher is better

### "Why is the RF+SVC model mentioned so often if the code prefers another model?"

Because the project evolved. Older docs and scripts focused on the RF+SVC ensemble. Newer runtime code prefers the best comparison model when that artifact exists.

### "Why does the app use both rules and ML?"

Analogy: the ML model is like an experienced guesser, and the rules are like a cautious checklist. The project uses both because the checklist can catch obvious false alarms or edge cases that the model alone might mishandle.

### "Why are the full-dataset metrics so high?"

Because validating on the full available feature dataset is easier than testing on truly unseen grouped speakers. Group-aware holdout results are a better guide to real-world generalization.

### "Why is there an AI chat microphone button that does not record?"

That page is only partially implemented. The mic button currently changes the UI state but does not send audio anywhere.

### "Why are there so many generated folders?"

Because this repo mixes:

- application code
- machine-learning artifacts
- runtime uploads and reports
- frontend build output
- Python and npm dependencies

That is normal in local ML application projects, but it can feel overwhelming at first.

## Section 16: Improvements and Future Work

### Current limitations

1. Security is too weak for production.
   Unauthenticated access can currently expose all analyses and reports if IDs are known.
2. SQLite plus local filesystem storage do not scale well.
3. Grammar and chat depend on external or local LLM availability.
4. Stuttering and phonological scoring are heuristic rather than clinically trained models.
5. The dysarthria model uses a short prefix window for the main classifier features, which may miss later parts of the recording.
6. The frontend and backend do not use exactly the same aggregate scoring logic.
7. Some docs and helper scripts are outdated.
8. Some UI elements are unfinished, like the AI chat mic button and the login page's forgot-password link.
9. Runtime storage can grow without lifecycle cleanup.
10. This is not a clinically validated diagnostic system.

### How to improve accuracy

1. Use more speaker-diverse labeled datasets.
2. Add stronger speaker-normalization and channel-robustness handling.
3. Train with full-recording features instead of only the first 8000 frames for the main classifier.
4. Add calibrated probability evaluation and calibration curves.
5. Build a dedicated labeled stuttering dataset instead of relying only on heuristics.
6. Replace the phonological proxy with forced alignment or phoneme-level models.
7. Evaluate grammar correction quality against human-annotated references.
8. Run stricter grouped cross-validation more consistently.

### How to improve software architecture

1. Lock down all analysis and report routes behind real authorization.
2. Replace startup backfills with formal migrations such as Alembic.
3. Move long-running analysis into background jobs.
4. Store files in object storage rather than local disk for production.
5. Unify scoring formulas between frontend and backend.
6. Remove stale artifacts and update outdated docs.
7. Add tests around security, route behavior, and scoring formulas.
8. Split the backend into more explicit router and service modules if the codebase grows further.

### Real-world challenges

Speech is messy. Accent, microphone quality, room noise, emotion, fatigue, and recording length all affect the signal. A model that looks strong in controlled evaluation can still behave unpredictably in the wild.

That is why the code's best design choice is not just the model itself, but the **symptom-gated safety logic** layered on top of it. The developer clearly noticed that a raw probability was not enough and added rule-based realism checks.

## Section 17: Interview and Viva Preparation

### One-minute explanation of the project

SpeechWell is a full-stack speech-analysis system built with a React frontend, a FastAPI backend, SQLite persistence, and a hybrid ML pipeline. A user uploads or records speech, the backend normalizes the audio, extracts transcript and timing features with Whisper, computes tabular acoustic features, runs dysarthria inference using a saved scikit-learn classifier with symptom-gated safety logic, estimates stuttering and phonological instability using heuristics, scores grammar quality using an LLM-assisted or heuristic correction step, stores everything in the database, and generates a PDF report for the UI.

### Interview-ready architecture explanation

If someone asks "how is the system designed?" a strong answer is:

1. The frontend owns user interaction, recording, upload progress, history views, training UI, and report download.
2. The backend owns authentication, persistence, request orchestration, audio normalization, and API response formatting.
3. The `ml/` package owns feature extraction, datasets, training scripts, and saved model artifacts.
4. Runtime analysis is hybrid, not purely end-to-end deep learning: pretrained Whisper plus handcrafted DSP features plus classical classifiers plus heuristic guardrails.
5. The most important design choice is that the final dysarthria result is post-processed by symptom gating instead of trusting raw classifier probability blindly.

### Common viva questions with strong answers

#### "What problem does this solve?"

It helps users analyze speech recordings for possible dysarthria, stuttering-like disfluency, grammar quality issues, and articulation instability, while also providing training exercises and historical progress tracking.

#### "Why did you not use a single end-to-end neural network for everything?"

Because the repository is optimized for practicality and interpretability. Whisper already solves transcription well, classical models work strongly on structured acoustic features, and rule-based layers make the system easier to debug and safer to calibrate than a fully opaque end-to-end classifier.

#### "What is the core model in production?"

The live code prefers `ml/models/dysarthria_best_comparison_model.pkl`, which is a saved scikit-learn pipeline whose best model is `HistGradientBoostingClassifier`, and then wraps that probability with symptom-gated decision logic in `backend/app/services/dysarthria_inference_service.py`.

#### "Why are the reported metrics high?"

Because the dysarthria model is evaluated on curated datasets with strong class patterns, and some reports use combined data with a very large UASpeech positive class. Group-aware holdout splits are more trustworthy than naive utterance-wise splits for estimating real-world generalization.

#### "What would you improve first?"

I would fix authorization on analysis/report routes, add stricter grouped evaluation, replace heuristic stuttering and phonological modules with trained models, and align frontend and backend scoring formulas.

### Technical points worth mentioning in an interview

- The backend uses SQLAlchemy ORM models and computes `overall_score` as a weighted property rather than storing only a static number.
- Startup includes schema-compatibility and data-backfill routines, which is convenient but should ideally be replaced by proper migrations.
- The training pipeline separates dataset indexing, feature extraction, model comparison, validation, and artifact export.
- The runtime path and the training path are related but not identical, which is common in ML systems and important to explain honestly.
- The system is not a medical diagnostic device; it is a decision-support and practice-oriented application.

## Section 18: System Design Decisions

### Why this architecture was chosen

The codebase suggests a pragmatic design strategy rather than a research-pure one:

1. Use React for fast interactive UI development.
2. Use FastAPI because it is lightweight, Python-native, and works naturally with ML code.
3. Keep persistence simple with SQLite for local development and demoability.
4. Use pretrained models for expensive speech representation tasks instead of training everything from scratch.
5. Use classical tabular models for dysarthria because they are fast, compact, and easy to serialize as `.pkl` artifacts.
6. Add heuristics where labeled data is scarce, especially for stuttering and phonological behavior.

### Important trade-offs

#### Trade-off 1: speed and simplicity vs clinical rigor

The system is fast to run locally and easy to inspect, but it is not clinically validated and does not have the robustness guarantees of a regulated medical workflow.

#### Trade-off 2: local-first artifacts vs deployment scalability

SQLite files and local report storage are simple for a student or prototype project, but they do not scale gracefully to multi-user cloud production.

#### Trade-off 3: handcrafted features vs end-to-end representation learning

Handcrafted features are interpretable and easy to debug. End-to-end deep models may capture richer speech disorder patterns, but they require more labeled data, stronger compute, and more careful calibration.

#### Trade-off 4: rule-based safety vs model purity

Symptom gating makes the final dysarthria prediction less "pure" from a machine-learning perspective, but more realistic from a product perspective because it can suppress implausible false positives.

### Hidden architectural smells worth noticing

- `ml/services/speech_analysis_service.py` imports backend service modules, so the ML layer is not fully isolated from the application layer.
- Startup backfills mutate persisted data, which mixes bootstrapping, migration, and business logic.
- Some frontend scoring and interpretation logic is duplicated client-side instead of being served as one canonical backend result contract.
- Security policy is inconsistent across analysis endpoints.

### Sensible alternatives

If you rebuilt the system for production, a stronger architecture would be:

1. FastAPI routers split by domain with explicit service interfaces.
2. Background workers for long-running analysis jobs.
3. Object storage for audio and reports.
4. Postgres instead of SQLite.
5. A model registry with versioned artifacts and calibration metadata.
6. Forced-auth access to all user-owned analyses and reports.

## Final Understanding

If you understand the following five ideas, you understand the project:

1. The frontend is a React shell that uploads audio, displays stored results, and runs training and chat workflows.
2. The backend is a FastAPI server that owns the route logic, persistence, file I/O, and report generation.
3. The main analysis pipeline is orchestrated in `ml/services/speech_analysis_service.py`.
4. The most important ML decision happens in `backend/app/services/dysarthria_inference_service.py`, which combines model probability with symptom gating.
5. The repository mixes authored code with many generated and historical artifacts, so the current runtime truth lives in the code, not always in the older documents.

After reading this manual, you should be able to:

- explain what SpeechWell does
- trace an uploaded file through the full stack
- find the file that owns a given behavior
- retrain the dysarthria model
- understand why certain numbers appear in the UI
- identify current limitations and sensible next improvements
