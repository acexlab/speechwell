# Technical Report Correction & Rewrite Plan

## Purpose

This correction blueprint audits the existing Phase II SpeechWell report against the current repository and defines what must be rewritten so the final academic document matches the implemented system. The review is based on the code in `backend/app`, `ml`, and `speechwell-frontend`, the stored evaluation artifacts in `ml/evaluation`, and the original DOCX structure extracted from `phase2_report_speechwell (1) on work.docx`.

## Codebase Baseline

### Real System Architecture

SpeechWell is a full-stack application with a React and Vite frontend, a FastAPI backend, SQLite persistence, and a modular ML plus rules pipeline. The backend normalizes uploaded audio with FFmpeg, extracts transcript and timing data with Whisper, computes waveform-level raw-audio features, runs dysarthria inference, stuttering scoring, grammar analysis, and phonological proxy scoring, then stores results and generates PDF reports.

### Real End-To-End Data Flow

Audio upload or recording enters the frontend and is submitted to `POST /api/analyze`. The backend saves the original file, normalizes it to mono 16 kHz WAV, calls `run_full_analysis(...)`, and collects transcript, pause, grammar, dysarthria, stuttering, and phonological outputs. The final payload is stored in the `analyses` table, rendered into a PDF report, and returned to Results, History, and Dashboard views. A separate training flow starts guided practice sessions, evaluates text or audio attempts, stores `training_sessions`, and aggregates `training_progress`.

### Key Implementation Facts The Report Must Respect

- The current preferred runtime dysarthria path is not the legacy logistic-regression model. The backend prefers `ml/models/dysarthria_best_comparison_model.pkl`, whose saved comparison report selects `HistGradientBoostingClassifier` as the best holdout model.
- The active dysarthria feature path uses raw-audio descriptors from `ml/feature_extraction/raw_audio_features.py`, not MFCC-only input.
- Wav2Vec2 embeddings still exist, but they now support the legacy fallback path more than the main runtime classifier.
- Stuttering and phonological outputs are rule-based heuristics, not separately trained deep-learning classifiers.
- Grammar quality is produced by a separate transcript-correction service with OpenAI, Gemini, or Ollama support plus local scoring heuristics.
- The application includes a real guided training subsystem with module catalog, session evaluation, progress aggregation, and Therapy Hub video content.

---

## 1. ABSTRACT

### What Is Currently Written

The current abstract describes SpeechWell as an automated speech-disorder assessment framework that uses acoustic and linguistic features, MFCCs, logistic regression, severity classification, PDF reports, and personalized video recommendations.

### What Is Wrong Or Outdated

- It treats logistic regression as the main project model.
- It overstates MFCC-centric processing and pitch extraction as the deployed core.
- It presents the output as severity classification plus recommendations rather than the actual multi-output payload.

### What Is Missing

- The FastAPI plus React full-stack architecture.
- Whisper transcript and pause extraction.
- Raw-audio feature extraction and symptom-gated dysarthria inference.
- The training-session and progress subsystem.

### What Should Be Replaced

Replace the abstract with a code-aligned summary that explains upload normalization, transcription, raw-audio feature extraction, multi-output analysis, persistence, PDF reporting, and guided training support.

### Correct Updated Content

SpeechWell is a full-stack speech analysis and guided practice platform built with a React frontend, a FastAPI backend, SQLite persistence, and a modular machine-learning pipeline. The current system accepts recorded or uploaded audio, normalizes it to mono 16 kHz WAV, generates transcripts and timing features with Whisper, extracts raw waveform descriptors from the recording, and returns multi-output analysis results that include dysarthria probability and label, stuttering probability, grammar quality feedback, phonological-error risk, and speech-timing metrics. The preferred runtime dysarthria path uses a saved comparison-model artifact together with symptom-gated post-processing, while stuttering and phonological outputs are derived through transparent rule-based logic and grammar feedback is produced through configurable transcript correction plus local scoring heuristics. SpeechWell stores analysis history, generates downloadable PDF reports, and provides guided training modules with session-wise progress tracking and supplementary Therapy Hub videos. The implemented system therefore functions as an integrated speech-support application rather than a single standalone classifier.

---

## 2. INTRODUCTION

### 2.1 Background And Motivation

#### What Is Currently Written

The current introduction explains speech disorders in generic academic terms, then motivates the project using acoustic analysis, logistic regression, severity levels, progress tracking, and video-mapping logic.

#### What Is Wrong Or Outdated

- The discussion repeatedly frames logistic regression as the deployed model.
- It claims MFCC, pitch, and generic feature extraction as the central runtime pipeline.
- It presents video recommendation logic as if it were the main follow-up mechanism.

#### What Is Missing

- Real backend preprocessing with FFmpeg normalization.
- Whisper-based transcript, segment, and pause extraction.
- The modern raw-audio dysarthria feature path.
- Separate grammar, stuttering, and phonological services.
- The actual guided training APIs and stored progress records.

### What Should Be Replaced

Replace theory-heavy motivation with repository-backed motivation: accessible speech analysis, interpretable multi-service inference, persistence, report generation, and guided practice in one deployable system.

### Correct Updated Content

SpeechWell is motivated by the need for an accessible, interpretable, and deployable speech-support platform that can combine automated analysis with practical follow-up. In the implemented system, uploaded or recorded audio is normalized to mono 16 kHz WAV, transcribed with Whisper, analyzed using raw waveform features and rule-based speech heuristics, stored in SQLite, and returned through a web interface that supports reporting and later review. This design addresses an important gap between manual speech assessment and software that users can operate independently. The project is also motivated by the need to combine motor-speech indicators, fluency cues, transcript quality, and guided practice inside one architecture instead of scattering them across disconnected tools. Rather than relying on a single opaque classifier, SpeechWell separates dysarthria inference, stuttering logic, grammar analysis, phonological proxy scoring, report generation, and guided training so that each part reflects the actual input evidence available at runtime.

### 2.2 Objectives

#### What Is Currently Written

The current objectives focus on extracting acoustic features, classifying disorders with rules plus logistic regression, and recommending therapy videos with progress tracking.

#### What Is Wrong Or Outdated

- The objectives do not match the actual code modules closely enough.
- They reduce the system to one classifier plus recommendation flow.
- They ignore the training-session evaluation subsystem.

#### What Is Missing

- End-to-end audio normalization and transcription.
- Multi-output analysis from specialized services.
- Database-backed history, report generation, and guided training progress.

### What Should Be Replaced

State objectives in terms of implemented software capabilities rather than idealized theory.

### Correct Updated Content

The objectives of SpeechWell are to normalize and analyze real user speech recordings in a consistent backend pipeline, to generate interpretable multi-output analysis results from specialized dysarthria, stuttering, grammar, and phonological services, and to support continued user improvement through report generation, stored history, guided training sessions, and progress synchronization. In implementation terms, this means standardizing uploaded audio, extracting transcript and timing evidence, computing raw-audio feature tables for the dysarthria model, persisting results in SQLite, generating PDF reports, and evaluating guided practice attempts through training-session APIs. These objectives align directly with the current repository and are more accurate than describing the project as a purely theoretical disorder-classification framework.

---

## 3. LITERATURE SURVEY

### What Is Currently Written

The current literature survey summarizes ten external papers in a largely generic way and emphasizes deep learning, CAE, CNN, BLSTM, BiLSTM, CTC, and broad disorder-detection trends.

### What Is Wrong Or Outdated

- The survey reads like a standalone paper summary chapter rather than a comparison against the implemented system.
- It implies the project itself uses deep architectures similar to the surveyed papers.
- It does not distinguish clearly between the repository’s current classical-ML plus heuristic design and the deeper models from prior work.

### What Is Missing

- A direct comparison between surveyed systems and SpeechWell.
- A clarification that SpeechWell uses a modular, practical deployment stack rather than fully end-to-end deep learning.
- Discussion of why the current repository favors interpretable classical models plus heuristics for runtime use.

### What Should Be Replaced

Retain relevant paper references, but rewrite the section as implementation-oriented comparison: what earlier systems do, what SpeechWell actually implements, and where SpeechWell is intentionally simpler or more modular.

### Correct Updated Content

The literature survey should compare prior speech-disorder systems with the actual SpeechWell implementation rather than listing unrelated deep-learning methods in isolation. Many surveyed works rely on large labeled corpora, specialized acoustic encoders, or phoneme-level supervision, whereas SpeechWell currently adopts a more deployable hybrid design: Whisper for transcription and timing, raw-audio statistical descriptors for dysarthria modeling, separate rule-based stuttering and phonological services, and provider-assisted grammar correction with local score estimation. This makes the project more practical to run in a web application, even if it is less end-to-end than some research-grade deep models. The revised survey should therefore highlight that SpeechWell prioritizes modularity, interpretability, and product integration over reproducing every deep-learning architecture from the literature, while still borrowing ideas such as acoustic modeling, transcript-assisted analysis, and guided at-home support.

---

## 4. SYSTEM REQUIREMENTS

### What Is Currently Written

The current section lists software and hardware requirements in a conventional project-report format.

### What Is Wrong Or Outdated

- The stack description is too generic and does not accurately name the repository technologies.
- It does not distinguish runtime dependencies from model-training dependencies.

### What Is Missing

- React, Vite, TypeScript, FastAPI, SQLAlchemy, SQLite, Whisper, transformers, ReportLab, and scikit-learn.
- FFmpeg as an operational dependency.
- Optional LLM provider configuration for grammar and chat services.

### What Should Be Replaced

Update the software requirements to reflect the repository and the backend plus ML stack precisely.

### Correct Updated Content

The software requirements should state that the frontend is built with React, Vite, and TypeScript, while the backend uses FastAPI, SQLAlchemy, JWT-based authentication, and SQLite. The ML and audio stack includes Whisper, librosa, soundfile, scikit-learn, joblib, torch, transformers, torchaudio or librosa fallback for MFCC extraction, and ReportLab for PDF generation. FFmpeg is required for backend audio normalization. Optional provider configuration is also needed for OpenAI, Gemini, or local Ollama when grammar correction and AI coaching features are enabled. Hardware requirements can remain modest for application use, but model extraction and offline training benefit from greater CPU, RAM, and storage capacity.

---

## 5. SYSTEM ANALYSIS

### 5.1 Existing System

#### What Is Currently Written

The current text discusses broad categories of automated speech-disorder systems and deep-learning approaches as if they collectively represent the “existing system.”

#### What Is Wrong Or Outdated

- It does not anchor the existing-system discussion to the actual limitations SpeechWell addresses.
- It blends literature review content into system analysis.

#### What Is Missing

- A practical baseline: manual clinical assessment, siloed speech-analysis tools, and disconnected therapy support.

### What Should Be Replaced

Rewrite the existing-system subsection around manual assessment and fragmented software workflows rather than generic paper summaries.

### Correct Updated Content

The existing system should be described as a combination of manual speech-language evaluation and fragmented digital tools. Traditional assessment depends heavily on expert listening, repeated sessions, and specialist availability. Separate software tools may offer transcription, audio processing, or grammar assistance, but they often do not combine speech upload, disorder-oriented analysis, persistent storage, downloadable reports, and guided practice inside one deployable interface. This fragmented baseline motivates SpeechWell’s integrated design.

### 5.2 Drawbacks

#### What Is Currently Written

The current report contains a drawbacks subsection, but it is not tightly connected to the implemented architecture.

#### What Is Wrong Or Outdated

- Drawbacks are described too abstractly.
- They do not explain why a modular full-stack system is needed.

#### What Is Missing

- Time cost, lack of repeatable metrics, disconnected reporting, lack of user-owned history, and weak continuity between assessment and practice.

### What Should Be Replaced

Use repository-backed drawbacks that justify SpeechWell’s storage, reporting, and training design.

### Correct Updated Content

The drawbacks of the existing approach are high dependence on manual evaluation, limited access to specialists, lack of repeatable computational metrics across sessions, poor continuity between one assessment and the next, and the absence of a unified workflow linking screening results to user-visible reports and guided follow-up practice. These drawbacks are directly addressed by SpeechWell’s persistent analysis records, report downloads, dashboard history, guided training sessions, and Therapy Hub support.

### 5.3 Proposed System

#### What Is Currently Written

The current proposed-system subsection already attempts to explain modules, but it still claims logistic regression as the main model and exaggerates recommendation-engine logic.

#### What Is Wrong Or Outdated

- Main model is outdated.
- Preprocessing description is too theoretical.
- The third module is mischaracterized.

#### What Is Missing

- Symptom-gated dysarthria inference.
- Separate heuristic services.
- Training-session APIs and progress storage.

### What Should Be Replaced

Describe the system as a connected web application with specialized analysis services and guided practice support.

### Correct Updated Content

The proposed system is an integrated speech analysis and guided practice platform. It accepts uploaded or recorded speech, normalizes the audio, extracts transcript and timing features, runs specialized dysarthria, stuttering, grammar, and phonological services, stores results in SQLite, generates PDF reports, and supports guided training sessions with per-module progress tracking. The dysarthria subsystem uses raw-audio descriptors and a saved classical ML pipeline with symptom-gated post-processing, while the other outputs are produced through transparent heuristics and provider-assisted transcript correction. This proposal is more accurate and more academically defensible than presenting SpeechWell as a single-model severity classifier.

### 5.4 Advantages

#### What Is Currently Written

The report lists general advantages of the proposed system.

#### What Is Wrong Or Outdated

- The listed benefits do not fully reflect the implemented features.

#### What Is Missing

- Multi-output analysis, persisted history, downloadable reports, training progress, and modular extensibility.

### What Should Be Replaced

State the advantages that can be verified from the repository.

### Correct Updated Content

The main advantages of the implemented system are multi-output analysis from a single recording, conservative and interpretable dysarthria inference, transcript-based language feedback, persisted session history, downloadable PDF reports, guided training modules with stored progress, and a modular backend that can be extended without redesigning the entire application. These are concrete advantages supported by the codebase rather than generic claims about AI in healthcare.

---

## 6. SYSTEM DESIGN

### 6.1 Block Diagram Explanation

#### What Is Currently Written

The report currently explains the block diagram as three clean modules: feature extraction, classification, and exercise or recommendation.

#### What Is Wrong Or Outdated

- It oversimplifies the actual full-stack architecture.
- It hides the backend API, database, storage, and training subsystem.

#### What Is Missing

- Frontend, backend, ML orchestration, database, report service, and training branch.

### What Should Be Replaced

Interpret the diagram as a layered web architecture rather than a narrow research pipeline.

### Correct Updated Content

The corrected block-diagram explanation should show the React frontend, FastAPI backend, audio normalization block, ML-orchestration block, SQLite storage, PDF-report generation, guided training evaluation, and Therapy Hub support content. This better matches the actual project structure in which analysis, persistence, reporting, and training all operate as connected components.

### 6.2 Data Flow Diagrams

#### What Is Currently Written

The report includes Level 0, 1, and 2 DFD sections, but the written explanation is generic.

#### What Is Wrong Or Outdated

- It treats the flow as if one classifier consumes extracted features and emits exercises.
- It does not show storage or training-session branches.

#### What Is Missing

- Original-file save, FFmpeg normalization, Whisper features, specialized analysis services, database write, PDF generation, and progress sync.

### What Should Be Replaced

Rewrite each DFD explanation around the real request and response flows implemented in the backend.

### Correct Updated Content

Level 0 should present the user exchanging audio, analysis results, reports, and training responses with the SpeechWell platform. Level 1 should break the platform into authentication/profile, analysis upload and normalization, speech-analysis orchestration, storage and report generation, and guided training evaluation. Level 2 should show the concrete sequence: save upload, normalize audio, transcribe and compute pauses, extract raw-audio features, run dysarthria plus heuristic services, merge outputs, store results, generate report, and return the analysis. A separate Level 2 training flow should show session start, text or audio submission, attempt scoring, session save, and progress aggregation.

---

## 7. SYSTEM IMPLEMENTATION

### What Is Currently Written

The current implementation chapter has the correct broad theme, but it still refers to generic acoustic embeddings, logistic regression, and a decision-tree recommendation engine.

### What Is Wrong Or Outdated

- The main dysarthria implementation is outdated.
- Training implementation is understated or mischaracterized.
- The real API structure is missing.

### What Is Missing

- Backend endpoint flow.
- Storage schema.
- Symptom-gated runtime behavior.
- Guided training session lifecycle.

### What Should Be Replaced

Replace the chapter with backend, frontend, ML pipeline, API flow, and audio processing details derived from the repository.

### Correct Updated Content

The implementation chapter should explain that the frontend submits uploads through `speechwell-frontend/src/api/api.ts`, the backend handles `POST /api/analyze` in `backend/app/main.py`, and the analysis logic is orchestrated by `ml/services/speech_analysis_service.py`. Audio is normalized with FFmpeg, transcribed with Whisper, and routed through separate dysarthria, stuttering, grammar, and phonological services. Result fields are stored in the `analyses` table and used to generate a ReportLab PDF report. The frontend then presents these values on Results, History, and Dashboard pages. In parallel, the training implementation uses `/api/training/modules`, `/api/training/session/start`, `/api/training/session/evaluate`, `/api/training/session/{id}`, and `/api/training/progress` to support guided exercises, session scoring, saved feedback, and progress summaries. This implementation-level account is much stronger academically because it corresponds directly to the deployed code.

---

## 8. MODULES

### 8.1 Feature Extraction Module

#### What Is Currently Written

The report currently describes preprocessing, noise removal, VAD, framing, and Wav2Vec2-based extraction in a very generic sequence.

#### What Is Wrong Or Outdated

- Noise removal and VAD are overstated as primary deployed steps.
- Wav2Vec2 is presented as the core feature path.

#### What Is Missing

- FFmpeg normalization.
- Whisper transcript and pause analysis.
- Raw waveform descriptor extraction.

### What Should Be Replaced

Explain exactly what `extract_whisper.py`, `extract_acoustic.py`, and `raw_audio_features.py` do.

### Correct Updated Content

The feature-extraction module starts with backend audio normalization to mono 16 kHz WAV. `ml/feature_extraction/extract_whisper.py` then transcribes the audio with the preferred locally available Whisper model and derives transcript text, segment timing, speaking rate, pause durations, long-pause count, and total duration. `ml/feature_extraction/raw_audio_features.py` extracts the waveform-level numeric descriptor set used by the current dysarthria model, including RMS, amplitude quantiles, silence ratio, zero-crossing rate, spectral centroid, bandwidth, rolloff, flatness, chroma summaries, spectral-contrast summaries, and MFCC, delta-MFCC, and delta-delta MFCC statistics. `ml/feature_extraction/extract_acoustic.py` still computes a 768-dimensional Wav2Vec2 embedding, but this now mainly supports legacy fallback behavior rather than the main runtime classifier.

### 8.2 Classification Module

#### What Is Currently Written

The report currently treats classification as normalized features entering a logistic-regression model, with rule logic around it.

#### What Is Wrong Or Outdated

- The primary model is wrong.
- The runtime symptom-gating layer is omitted.
- The other services are oversimplified as generic classification outputs.

#### What Is Missing

- Best-model artifact selection.
- Raw probability plus symptom score adjustment.
- Separate grammar, stuttering, and phonological logic.

### What Should Be Replaced

Document the actual classifier and the heuristics around it.

### Correct Updated Content

The classification stage is now a modular decision stage rather than one monolithic classifier. Dysarthria inference uses `backend/app/services/dysarthria_inference_service.py`, which loads the preferred runtime comparison-model artifact, prepares the raw-audio feature row in the saved schema order, predicts a raw probability, computes a waveform-based symptom score, counts healthy-speech signals, and adjusts the final decision conservatively before returning label, probability, explanation, and model version. Stuttering detection estimates repetitions, prolongations, blocks, pause variability, segment-rate variability, and speaking-rate penalty to produce a stuttering probability. Grammar analysis corrects transcript text through the configured provider, estimates error count, and computes grammar quality score. Phonological analysis acts as an articulation-instability proxy using transcript fragments, repaired words, elongated spellings, and segment instability. This is the real analytical core of the current repository.

### 8.3 Exercise And Progress Module

#### What Is Currently Written

The existing report implies a recommendation engine that maps disorder severity to exercises and tracks progress.

#### What Is Wrong Or Outdated

- There is no decision-tree recommendation engine in the current code.
- The report does not describe the real training-session pipeline.

#### What Is Missing

- Static training catalog.
- Session start and evaluation endpoints.
- Saved training scores and aggregated progress rows.

### What Should Be Replaced

Explain the real guided training subsystem and the supplementary video library honestly.

### Correct Updated Content

The exercise and progress module is implemented as a guided training subsystem rather than an adaptive recommendation engine. `backend/app/services/training_catalog.py` defines fixed modules and exercises for breath and voice control, articulation, fluency, and grammar practice. When a learner starts an exercise, the backend creates a `training_sessions` record. The evaluation service then accepts text or audio input, computes transcript accuracy, repeated-word count, long-pause count, fluency score, confidence score, and corrected text, stores the finished attempt, and returns practical feedback. `sync_progress(...)` updates the `training_progress` table with sessions completed, average accuracy, average fluency, best score, and last practiced time for each module. The Therapy Hub also contains curated YouTube practice videos, which supplement the internal exercise engine rather than replacing it.

---

## 9. DATASET DETAILS

### What Is Currently Written

The report currently points to older or incorrect datasets, including UCLASS-oriented descriptions.

### What Is Wrong Or Outdated

- UCLASS is not the main dataset for the deployed dysarthria pipeline.
- The current training tables are not documented correctly.

### What Is Missing

- TORGO as the primary source.
- Optional UASpeech positive-class augmentation.
- Actual row counts and artifact file names.

### What Should Be Replaced

Replace the dataset chapter with the datasets and feature tables used in the repository.

### Correct Updated Content

The primary dysarthria training dataset in the repository is TORGO, represented through the extracted feature table `ml/training/torgo_audio_features_v4.csv`, which contains 17,612 rows with 11,455 healthy samples and 6,157 dysarthria samples across 31 unique speakers. The repository also supports optional positive-class augmentation from UASpeech through `ml/training/build_combined_dysarthria_index.py` and `ml/training/combined_audio_features.csv`. The combined feature table contains 160,890 rows and is used by the model-comparison workflow that produced the preferred runtime artifact. Dataset documentation should clearly note that UASpeech is treated as dysarthria-positive augmentation only and does not replace the healthy control speech provided by TORGO.

---

## 10. PERFORMANCE ANALYSIS

### What Is Currently Written

The current performance chapter compares broad module-wise percentages and still presents the project as a logistic-regression system.

### What Is Wrong Or Outdated

- It does not use the actual saved evaluation artifacts.
- It mixes theory with unsupported metrics for heuristic modules.

### What Is Missing

- Validation figures from `ml/evaluation`.
- Best-model holdout metrics.
- Honest clarification that only dysarthria has strong offline evaluation artifacts.

### What Should Be Replaced

Rewrite the chapter around saved dysarthria metrics and explain the evaluation limits for the other modules.

### Correct Updated Content

The corrected performance chapter should use the saved dysarthria evaluation artifacts rather than unsupported module-wide claims. The strongest deployment-relevant report is `ml/evaluation/dysarthria_model_comparison_report.json`, which selects `hist_gradient_boosting` as the best holdout model with 94.49% accuracy, 99.96% precision, 93.35% recall, and 96.54% F1 score at a threshold of 0.85. The TORGO-only RF plus SVC validation report remains useful for comparison, but the runtime path now prefers the saved comparison-model artifact. The chapter should also state explicitly that stuttering and phonological components are heuristic services and grammar depends on provider-assisted correction plus local heuristics, so their behavior should be explained qualitatively rather than falsely benchmarked as trained classifiers with formal offline accuracy tables.

---

## 11. CONCLUSION

### What Is Currently Written

The conclusion presents SpeechWell as a speech-disorder classifier with exercise recommendation and progress tracking.

### What Is Wrong Or Outdated

- It understates the current full-stack product scope.
- It overstates recommendation logic.

### What Is Missing

- Full-stack integration, report generation, and guided training implementation.

### What Should Be Replaced

Conclude with what the system actually does today.

### Correct Updated Content

The conclusion should state that SpeechWell has evolved into a full-stack speech analysis and guided practice application. It now integrates audio upload and recording, backend normalization, Whisper-based timing extraction, raw-audio dysarthria inference with symptom gating, heuristic fluency and phonological analysis, transcript-based grammar feedback, SQLite persistence, PDF report generation, guided training sessions, and progress tracking inside one web platform. This conclusion is more accurate and academically stronger because it reflects the implemented architecture instead of a simplified logistic-regression narrative.

---

## 12. FUTURE ENHANCEMENTS

### What Is Currently Written

The current future-work section is broad and generic.

### What Is Wrong Or Outdated

- It does not clearly separate finished features from unfinished directions.

### What Is Missing

- Formal evaluation for non-dysarthria modules.
- Better analysis-to-training linkage.
- Larger balanced clinical datasets.

### What Should Be Replaced

Base the future-enhancement section on real next steps suggested by the current repository.

### Correct Updated Content

Future enhancements should include broader and more balanced clinically validated datasets, stronger speaker-robust evaluation of the active dysarthria model, formal offline evaluation frameworks for stuttering and phonological services, richer explanation of symptom-gated decisions inside reports, adaptive exercise generation beyond the fixed training catalog, and tighter linkage between analysis findings and recommended practice modules. Multilingual support, clinician-review workflows, and better integration between structured training and Therapy Hub content are also realistic future directions for this repository.

---

## 13. APPENDICES

### What Is Currently Written

The original report keeps appendix sections for sample coding and screenshots.

### What Is Wrong Or Outdated

- The code appendix may not reflect the current repository.

### What Is Missing

- Representative current backend or report-generation code.
- Updated screenshots that match the present frontend.

### What Should Be Replaced

Appendix A should include current implementation excerpts, and Appendix B should retain or refresh screenshots from the present interface.

### Correct Updated Content

The appendices should be treated as supporting evidence. Appendix A should include a representative and current code excerpt, such as the PDF report service or a key backend analysis handler, because these are stable and demonstrably part of the deployed flow. Appendix B should preserve the screenshot appendix format while ensuring the included images match the current frontend pages such as Upload, Results, Dashboard, History, Therapy Hub, and guided training views.

---

## Recommended Rewrite Rules

- Keep the same section order, numbering, and overall document structure as the original DOCX.
- Preserve original paragraph styles and spacing wherever possible by editing the existing Word file in place.
- Replace generic theory with code-backed explanations.
- Do not describe any module as deep-learning-based unless the repository actually uses such a model in that module’s runtime path.
- Frame dysarthria metrics using saved evaluation artifacts only.
- Present the training subsystem honestly as fixed-module guided practice with stored progress, not as a dynamic recommendation engine.

## Source Files Used For Correction

- `backend/app/main.py`
- `backend/app/database/models.py`
- `backend/app/services/dysarthria_inference_service.py`
- `backend/app/services/stuttering_service.py`
- `backend/app/services/grammar_service.py`
- `backend/app/services/phonological_service.py`
- `backend/app/services/training_catalog.py`
- `backend/app/services/training_service.py`
- `backend/app/services/pdf_report_service.py`
- `ml/services/speech_analysis_service.py`
- `ml/feature_extraction/extract_whisper.py`
- `ml/feature_extraction/extract_acoustic.py`
- `ml/feature_extraction/raw_audio_features.py`
- `ml/training/build_torgo_audio_features.py`
- `ml/training/build_combined_dysarthria_index.py`
- `ml/training/train_dysarthria_rf_svc_ensemble.py`
- `ml/evaluation/validation_report_v2_rf_svc_ensemble.json`
- `ml/evaluation/dysarthria_model_comparison_report.json`
- `speechwell-frontend/src/App.tsx`
- `speechwell-frontend/src/api/api.ts`
- `speechwell-frontend/src/pages/Upload.tsx`
- `speechwell-frontend/src/pages/Results.tsx`
- `speechwell-frontend/src/pages/Dashboard.tsx`
- `speechwell-frontend/src/pages/History.tsx`
- `speechwell-frontend/src/pages/TherapyHub.tsx`
- `speechwell-frontend/src/pages/TrainingModule.tsx`
- `speechwell-frontend/src/pages/TrainingExercise.tsx`
- `speechwell-frontend/src/pages/TrainingResult.tsx`
