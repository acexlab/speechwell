# SpeechWell A to Z Project Guide

Generated on May 10, 2026

This guide explains how the SpeechWell project works from the user interface down to the signal features, machine learning decisions, equations, API flow, database records, reports, and training module. It is written as a complete project reference for presentations, reviews, and implementation understanding.

Important note: SpeechWell is an assistive speech analysis and practice application. Its outputs are risk or quality indicators from software models and rules. They are not a medical diagnosis and should not replace a licensed speech-language pathologist or clinician.

## 1. What SpeechWell Is

SpeechWell is a full-stack speech improvement platform. It accepts a user's speech recording, analyzes it with speech recognition, acoustic signal features, machine learning models, and rule-based estimators, then returns a readable report and training suggestions.

The project has two main parts:

- Speech analysis: upload or record speech, transcribe it, compute speech metrics, estimate dysarthria risk, estimate stuttering/disfluency, estimate grammar quality, estimate articulation/phonological risk, save the result, and generate a PDF report.
- Guided speech training: give the user structured practice modules for breath and voice control, articulation, fluency, and grammar; evaluate attempts; save progress; and show feedback.

The application is made from these layers:

- Frontend: React, Vite, TypeScript in `speechwell-frontend/`.
- Backend: FastAPI in `backend/app/`.
- ML and audio processing: Python modules in `ml/` and `backend/app/services/`.
- Database: SQLite using SQLAlchemy models.
- Runtime storage: uploaded audio, processed audio, and generated PDF reports.

## 2. User Journey

A typical analysis journey looks like this:

1. The user registers or logs in.
2. The frontend stores a JWT token in `localStorage`.
3. The user records or uploads an audio file.
4. The frontend sends the file to `POST /api/analyze`.
5. The backend stores the original file.
6. FFmpeg converts it to mono 16 kHz WAV.
7. Whisper transcribes the audio and extracts timing metrics.
8. Raw audio signal features are extracted for the dysarthria model.
9. Wav2Vec2 acoustic embeddings are extracted if available.
10. Dysarthria, stuttering, grammar, and phonological modules run.
11. The backend saves the analysis row in SQLite.
12. A clinical-style PDF report is generated.
13. The frontend displays result cards, history, dashboard summaries, and report download links.

A typical training journey looks like this:

1. The user opens the Therapy Hub.
2. The frontend loads `GET /api/training/modules`.
3. The user starts an exercise.
4. The backend creates a `TrainingSession`.
5. The user submits text or a microphone recording.
6. The training evaluator computes accuracy, fluency, confidence, pauses, repeated words, and feedback.
7. The session is saved as completed.
8. `TrainingProgress` is synced for dashboard summaries.

## 3. Project Folder Map

Main project files:

- `README.md`: project documentation and deployment notes.
- `backend/app/main.py`: FastAPI entrypoint, endpoints, upload handling, audio normalization, persistence, report creation.
- `backend/app/services/`: backend service modules for auth, grammar, stuttering, phonology, dysarthria inference, training, chat, and report generation.
- `backend/app/database/models.py`: SQLAlchemy database schema.
- `backend/app/schemas.py`: API request/response schemas.
- `ml/services/speech_analysis_service.py`: end-to-end ML orchestration.
- `ml/feature_extraction/extract_whisper.py`: transcript and timing features.
- `ml/feature_extraction/raw_audio_features.py`: raw signal feature extraction.
- `ml/feature_extraction/extract_acoustic.py`: Wav2Vec2 embedding extraction.
- `ml/training/`: scripts for building datasets and training classifiers.
- `ml/evaluation/`: validation scripts and model metric JSON files.
- `ml/models/`: saved model artifacts.
- `speechwell-frontend/src/`: React pages, components, API client, and styles.

## 4. Backend Architecture

The backend is a FastAPI server titled `SpeechWell API`. Its responsibilities are:

- Define REST endpoints.
- Accept and validate uploads.
- Normalize audio.
- Call the analysis pipeline.
- Store analysis results.
- Generate and serve PDF reports.
- Authenticate users with JWT.
- Manage profile fields.
- Serve training modules.
- Start and evaluate training sessions.
- Serve AI chat responses.

The central file is `backend/app/main.py`.

Key endpoint groups:

- Auth: `/api/auth/register`, `/api/auth/login`.
- Profile: `/api/profile`.
- Analysis: `/api/analyze`, `/api/analyze/{audio_id}`, `/api/analyses`.
- Reports: `/api/reports/{audio_id}`.
- Training: `/api/training/modules`, `/api/training/session/start`, `/api/training/session/evaluate`, `/api/training/session/{session_id}`, `/api/training/sessions`, `/api/training/progress`.
- Health: `/api/health`.
- Chat: `/api/chat`.

## 5. Frontend Architecture

The frontend is a React and Vite app in `speechwell-frontend/`.

Important areas:

- `src/api/api.ts`: API client that talks to the FastAPI backend.
- `src/App.tsx`: application routing and page composition.
- `src/pages/Upload.tsx`: upload or record audio for analysis.
- `src/pages/Results.tsx`: display a single analysis.
- `src/pages/History.tsx`: show previous analyses.
- `src/pages/Dashboard.tsx`: user dashboard.
- `src/pages/TherapyHub.tsx`: training module hub.
- `src/pages/TrainingModule.tsx`: module details.
- `src/pages/TrainingExercise.tsx`: exercise flow and submission.
- `src/pages/AIChat.tsx`: speech assistant chat interface.
- `src/components/`: shared UI pieces such as Navbar, Sidebar, VideoCard, progress bars, and training cards.

The frontend should set `VITE_API_URL` in production so API calls reach the deployed backend.

## 6. Audio Normalization

Before analysis, the backend converts uploaded audio to a predictable format:

```text
ffmpeg -y -i input_audio -ac 1 -ar 16000 output.wav
```

Meaning:

- `-ac 1`: one audio channel, mono.
- `-ar 16000`: 16,000 samples per second.
- `output.wav`: normalized WAV file used by all downstream modules.

Why this matters:

- Speech models expect consistent sample rates.
- Feature extraction becomes comparable across files.
- Stereo recordings, phone recordings, and browser recordings are made more uniform.

## 7. End-to-End Analysis Pipeline

The orchestrator is `ml/services/speech_analysis_service.py`.

The main function is:

```python
run_full_analysis(audio_path)
```

It performs:

1. `analyze_audio_features(audio_path)` for Whisper transcript and timing.
2. `detect_grammar_errors(transcript)` for grammar probability, grammar quality, corrected text.
3. `extract_acoustic_embedding(audio_path)` for Wav2Vec2 embedding.
4. `predict_dysarthria(whisper_features, acoustic_embedding, audio_path)` for dysarthria label and probability.
5. `detect_stuttering(whisper_features, audio_path)` for disfluency probability and event counts.
6. `detect_phonological_errors(whisper_features)` for articulation/phonological risk.

The combined return object includes:

- `transcript`
- `whisper_features`
- `grammar_result`
- `acoustic_embedding`
- `dysarthria_result`
- `stuttering_result`
- `phonological_result`

If one module fails, the pipeline uses safe fallback values so the whole analysis endpoint does not crash.

## 8. Whisper Transcript and Timing Features

File: `ml/feature_extraction/extract_whisper.py`

SpeechWell uses Whisper with preferred model candidates:

- configured `WHISPER_MODEL`, if set
- `small.en`
- `base.en`
- `base`

Transcription options include:

- English language.
- Deterministic temperature `0`.
- Beam search settings.
- Previous-text conditioning.

The module returns:

- `transcript`: recognized text.
- `total_words`: number of words in the transcript.
- `speaking_rate_wps`: words per second.
- `average_pause_sec`: average detected pause length.
- `max_pause_sec`: longest detected pause.
- `total_duration_sec`: full audio duration.
- `pause_durations`: list of pause lengths.
- `long_pause_count`: count of pauses at least 0.75 seconds.
- `segments`: per-segment text, timing, word count, and local speech rate.
- `transcription_model`: loaded Whisper model name.

Core equations:

```text
total_words = number of words in transcript

segment_duration = segment_end - segment_start

speaking_duration = sum(segment_duration for all valid segments)

speaking_rate_wps = total_words / speaking_duration

pause = current_speech_start - previous_speech_end

average_pause_sec = sum(pause_durations) / count(pause_durations)

max_pause_sec = max(pause_durations)
```

Meaning of common timing values:

- Low speaking rate may suggest slow, effortful, hesitant, or unclear speech, but it may also be caused by reading style or microphone silence.
- High speaking rate may suggest rushing or reduced control.
- Long pauses may indicate blocks, breath issues, hesitation, or natural sentence breaks.
- More context is needed before treating timing values as clinical signs.

## 9. Raw Audio Signal Features

File: `ml/feature_extraction/raw_audio_features.py`

This module reads the waveform and computes signal-level features used by the dysarthria model and symptom gate.

Basic waveform features:

- `duration_sec`: length of the audio.
- `sample_rate`: samples per second.
- `channels`: number of audio channels.
- `rms`: root mean square energy.
- `mean_abs`: average absolute amplitude.
- `std`: waveform standard deviation.
- `max_abs`: maximum absolute amplitude.
- `q25_abs`, `q50_abs`, `q75_abs`: amplitude quantiles.
- `silence_ratio`: proportion of samples under the silence threshold.
- `zcr`: zero crossing rate.

Spectral features:

- `centroid`: center of mass of the spectrum.
- `bandwidth`: spread around the spectral centroid.
- `rolloff_85`: frequency below which 85 percent of spectral power lies.
- `flatness`: how noise-like the spectrum is.
- `chroma_mean`, `chroma_std`: pitch-class energy summary.
- `spectral_contrast_mean`, `spectral_contrast_std`: contrast between high and low energy bands.

Cepstral features:

- `mfcc_1_mean` through `mfcc_13_mean`
- `mfcc_1_std` through `mfcc_13_std`
- `mfcc_delta_*`: first-order change over time.
- `mfcc_delta2_*`: second-order change over time.

Important equations:

```text
rms = sqrt(mean(signal^2))

mean_abs = mean(abs(signal))

silence_ratio = count(abs(signal) < 0.01) / total_sample_count

zcr = count(sign changes between adjacent samples) / adjacent_pair_count

power_spectrum = abs(FFT(signal))^2

spectral_centroid = sum(frequency * power) / sum(power)

spectral_bandwidth = sqrt(sum((frequency - centroid)^2 * power) / sum(power))

spectral_flatness = geometric_mean(power) / arithmetic_mean(power)
```

Signal meanings:

- RMS energy: how strong or quiet the recording is.
- Silence ratio: how much of the recording is near silence.
- Zero crossing rate: how often the signal changes sign; high or very low values can indicate unusual signal texture.
- Spectral centroid: brightness of the sound.
- Spectral flatness: noisy or breathy texture indicator.
- MFCCs: compact representation of vocal tract and spectral envelope shape.
- MFCC deltas: how quickly the spectral envelope changes over time.

## 10. Acoustic Embedding

File: `ml/feature_extraction/extract_acoustic.py`

SpeechWell can extract a Wav2Vec2 embedding:

- Model: `facebook/wav2vec2-base`.
- The audio is converted to mono 16 kHz.
- The waveform is passed through Wav2Vec2.
- Hidden states are mean-pooled into a 768-dimensional vector.

Equation:

```text
embedding = mean(last_hidden_state over time)
```

If the local Wav2Vec2 model is not available, the module returns a zero vector of length 768. The latest dysarthria path mainly uses raw audio features, while this embedding remains useful for the legacy path.

## 11. Dysarthria Detection

File: `backend/app/services/dysarthria_inference_service.py`

Dysarthria detection uses saved model artifacts in `ml/models/`. The current inference logic prefers the latest full-audio pipeline model:

- Runtime model: `ml/models/dysarthria_best_comparison_model.pkl`, if present.
- Fallback model: `ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl`.
- Legacy fallback: `ml/models/dysarthria_model_v1.pkl` plus scaler and PCA artifacts.

The latest path:

1. Extract raw audio features from the normalized WAV.
2. Sanitize train-set-specific fields by forcing sample rate to 16000 and channels to 1.
3. Order features exactly as expected by the saved model.
4. Compute raw probability using `predict_proba`.
5. Apply symptom-gated decision logic.
6. Return label, probability, symptom score, explanation, and model version.

## 12. Dysarthria Symptom Gate

The symptom gate is a guardrail that helps reduce false positives. It requires more than raw model probability. It also checks whether the full recording shows dysarthria-like symptom evidence.

The symptom score is from 0 to 5:

```text
score starts at 0

if rms < 0.01:
    score += 1

if silence_ratio > 0.45:
    score += 1

if spectral_flatness > 0.22:
    score += 1

if zcr < 0.03 or zcr > 0.18:
    score += 1

if mean(MFCC stds and MFCC delta stds) > 14.0:
    score += 1

symptom_score = min(score, 5)
```

What each symptom means:

- Low RMS energy: speech is very quiet or weak in the recording.
- High silence ratio: large parts of the file are silent or near-silent.
- Elevated spectral flatness: the audio is more noise-like, which can reflect breathy or unstable signal quality, but can also be background noise.
- Abnormal zero crossing rate: unusual waveform texture.
- High MFCC variance: unstable spectral shape over time.

Healthy-speech signals are also counted:

```text
healthy_signal_count increases when:

word_count >= 6
1.0 <= speaking_rate_wps <= 4.5
average_pause_sec <= 0.8
max_pause_sec <= 2.0
duration_sec >= 2.5
silence_ratio <= 0.55
rms >= 0.003
```

The decision rules include:

- If symptom score is 0 or 1, the system protects against false positives by reducing probability and labeling as healthy.
- If raw probability is very high, at least 0.95, and symptom score is at least 2, the system can preserve a dysarthria prediction.
- Otherwise the system requires both high probability and symptom evidence.
- The main dysarthria threshold is `0.75` in runtime gating, while saved model metadata may include its own threshold.

Simplified decision:

```text
if symptom_score <= 1:
    label = healthy
    probability is reduced

elif raw_probability >= 0.95 and symptom_score >= 2:
    label = dysarthria

elif final_probability >= 0.75 and symptom_score >= 2:
    label = dysarthria

else:
    label = healthy
```

## 13. What "40% Dysarthria" Means

If the UI or report shows `40% dysarthria`, that means:

```text
dysarthria_probability = 0.40
display_percent = round(0.40 * 100) = 40%
```

It does not mean the user "has 40 percent of a disease." It means the model and guardrail currently estimate a 0.40 risk score for the dysarthria class based on this recording.

How to interpret it in this project:

- 0 to 29 percent: low dysarthria risk signal.
- 30 to 59 percent: moderate or mixed signal; the system sees some patterns but not enough for a strong positive decision.
- 60 to 74 percent: elevated probability, but the symptom gate may still classify healthy unless symptom evidence is strong.
- 75 percent and above: high enough to support dysarthria only when symptom score is at least 2.

Example:

```text
raw model probability = 0.70
symptom_score = 1
final probability may be reduced
label = healthy

raw model probability = 0.82
symptom_score = 3
final probability may remain high
label = dysarthria
```

So a number like 40 percent should be read as an indicator: "some model evidence exists, but it is below the project threshold for a dysarthria label."

## 14. Dysarthria Model Training and Metrics

Evaluation artifacts show the project used group-aware splits and audio-feature datasets.

One available validation report for the RF/SVC ensemble shows:

- Samples: 17,612.
- Accuracy: 0.9846.
- Precision: 0.9940.
- Recall: 0.9618.
- F1 score: 0.9776.
- Confusion matrix: `[[11419, 36], [235, 5922]]`.

The broader comparison report used:

- Rows: 160,890.
- Training rows: 13,682.
- Validation rows: 18,547.
- Test rows: 12,207.
- Dataset breakdown: TORGO healthy, TORGO dysarthria, and UASPEECH dysarthria samples.

The comparison report ranked models including:

- Hist Gradient Boosting.
- RF/SVC ensemble.
- RBF SVC.
- Random Forest.
- Calibrated Logistic model.

Metric meanings:

```text
accuracy = correct_predictions / all_predictions

precision = true_positives / (true_positives + false_positives)

recall = true_positives / (true_positives + false_negatives)

f1_score = 2 * precision * recall / (precision + recall)
```

Why group-aware splitting matters:

- Speech datasets often contain multiple samples from the same speaker.
- If the same speaker appears in both train and test, metrics can be overly optimistic.
- Group-aware splitting tries to make evaluation more realistic by preventing speaker or dataset leakage where possible.

## 15. Stuttering and Fluency Detection

File: `backend/app/services/stuttering_service.py`

The stuttering module estimates disfluency using transcript patterns, timing pauses, segment rate variation, and optional acoustic hints.

It computes:

- `repetitions`: repeated words or repeated initial fragments.
- `prolongations`: stretched vowels, fragments, unusually slow short segments, and acoustic hints.
- `blocks`: pauses at least 0.9 seconds.
- `severe_blocks`: pauses at least 1.5 seconds.
- `stuttering_probability`: weighted disfluency score from 0 to 1.
- `fluency_score`: `round((1 - stuttering_probability) * 100)`.
- `disfluency_events`: repetitions + prolongations + blocks.

Repetition examples:

- "I I want water" counts as a repeated word.
- "w water" can count as an initial fragment repetition.

Prolongation examples:

- "sooo" or "aaa" can count as stretched vowel text evidence.
- Very slow one-word or short segments may count as possible prolongations.

Block examples:

- A pause of 0.9 seconds or more can count as a block.
- A pause of 1.5 seconds or more can count as a severe block.

Core equation:

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

Supporting equations:

```text
event_rate_score = event_count / max(total_words * expected_ratio, 1.0)
event_rate_score is capped at 1.0

block_rate_per_min = blocks / max(total_duration_sec / 60.0, 0.25)
block_score = min(block_rate_per_min / 4.0, 1.0)

fluency_score = round((1.0 - stuttering_probability) * 100)
```

Interpretation:

- 20 percent stuttering probability means low disfluency evidence in the sample.
- 50 percent means mixed or moderate disfluency evidence.
- 80 percent means high disfluency evidence in the sample.

As with dysarthria, this is not a diagnosis. It is a software estimate from the available audio and transcript.

## 16. Grammar Detection

File: `backend/app/services/grammar_service.py`

The grammar module corrects the transcript and estimates grammar-error probability.

Provider options:

- OpenAI, if configured.
- Gemini, if configured.
- Ollama, usually the local default.
- If no provider works, the corrected text falls back to the original transcript.

The grammar system prompt asks the model to correct grammar, punctuation, casing, and obvious transcription issues without changing meaning.

The module then compares original and corrected text and blends that with structural rules.

Important features:

- Repeated words.
- Filler words such as `uh`, `um`, `er`, `ah`, `like`, `you know`.
- Odd tokens.
- Sentence fragments.
- Missing verbs.
- Missing punctuation or boundary issues.
- Low function-word ratio.
- Subject case issues such as object pronouns at sentence start.

Core formulas:

```text
diff_error_count = number of changed word spans between original and corrected text

diff_probability = min(diff_error_count / word_count, 1.0)

structural_probability =
    fragment_ratio * 0.28
  + verb_gap_ratio * 0.16
  + repetition_ratio * 0.15
  + filler_ratio * 0.10
  + odd_token_ratio * 0.12
  + boundary_issue_ratio * 0.07
  + telegraphic_ratio * 0.07
  + subject_case_ratio * 0.05

trusted_diff_probability = diff_probability * (1.0 - artifact_ratio)

blended_probability = structural_probability * 0.6 + trusted_diff_probability * 0.4

grammar_error_probability = max(structural_probability, blended_probability)

grammar_quality_score = 1.0 - grammar_error_probability
```

Meaning:

- `grammar_error_probability` near 0 means the transcript appears grammatically stable.
- `grammar_error_probability` near 1 means the transcript has many grammar, structure, or artifact issues.
- `grammar_quality_score` is the inverse: higher is better.

Example:

```text
grammar_error_probability = 0.25
grammar_quality_score = 0.75
display quality = 75%
```

## 17. Phonological and Articulation Risk

File: `backend/app/services/phonological_service.py`

This module is a lightweight articulation proxy. It does not know the intended target word sequence during general analysis, so it cannot perform true phoneme-by-phoneme diagnosis. Instead, it estimates risk from transcript patterns that often appear when pronunciation is unstable.

Signals:

- One-letter fragments, except normal words `a` and `i`.
- Repaired words such as `b ball` where a fragment is followed by a matching word.
- Elongated spelling patterns.
- Slow short segments.
- Segment rate instability.

Core formula:

```text
phonological_error_probability =
    fragment_ratio * 0.35
  + repair_ratio * 0.30
  + elongation_ratio * 0.15
  + segment_instability * 0.10
  + slow_segment_ratio * 0.10
```

The result is capped at 1.0.

Returned values:

- `phonological_error_probability`: risk from 0 to 1.
- `error_count`: rough count of detected fragment/repair/slow-segment events.
- `affected_words`: up to 10 words that contributed to the signal.

Interpretation:

- Low value: little articulation-risk evidence in transcript patterns.
- Medium value: some unstable word production signals.
- High value: many fragment, repair, elongation, or unstable-rate signals.

## 18. Overall Score

File: `backend/app/services/score_service.py`

The project combines three dimensions:

- Pronunciation from dysarthria probability.
- Fluency from stuttering probability.
- Clarity from grammar quality.

Equations:

```text
pronunciation = (1 - dysarthria_probability) * 100

fluency = (1 - stuttering_probability) * 100

clarity = grammar_quality_score * 100

weighted_average =
    pronunciation * 0.35
  + fluency * 0.25
  + clarity * 0.40

weakest_skill = min(pronunciation, fluency, clarity)

overall_score =
    weighted_average * 0.70
  + weakest_skill * 0.30
```

Why the weakest skill matters:

- A user with two strong areas and one very weak area should not receive an overly high total.
- The final score rewards balance across pronunciation, fluency, and clarity.

Example:

```text
dysarthria_probability = 0.40
stuttering_probability = 0.20
grammar_quality_score = 0.75

pronunciation = 60
fluency = 80
clarity = 75

weighted_average = 60*0.35 + 80*0.25 + 75*0.40 = 71
weakest_skill = 60

overall_score = 71*0.70 + 60*0.30 = 67.7
rounded overall score = 68
```

## 19. Report Generation

File: `backend/app/services/pdf_report_service.py`

Each completed analysis can generate a PDF report. The report includes:

- Header and report date.
- User name.
- Overall score ring.
- Status summary.
- Dysarthria, stuttering, grammar, and phonology sections.
- Timing metrics.
- Transcript preview.
- Corrected text or grammar summary.

Report filenames are built from the user name and date. If a name already exists, the backend adds a numeric suffix.

The report is saved under the configured reports directory and can be downloaded from:

```text
GET /api/reports/{audio_id}
```

## 20. Database Schema

File: `backend/app/database/models.py`

Main tables:

### users

Stores:

- `id`
- `email`
- `password_hash`
- profile fields such as full name, age, gender, location, occupation, primary goal, bio
- timestamps

### analyses

Stores:

- `audio_id`
- original filename
- transcript
- dysarthria probability and label
- stuttering probability, repetitions, prolongations, blocks
- grammar score, grammar error count, corrected text
- phonological score and error count
- speaking rate, average pause, max pause, duration
- audio path
- PDF path and report filename
- status and error message
- timestamps

### training_sessions

Stores:

- user id
- module key
- exercise key
- prompt and expected text
- transcript
- input mode
- accuracy, fluency, confidence
- pause and repeated-word counts
- duration
- feedback
- corrected text
- status
- timestamps

### training_progress

Stores:

- user id
- module key
- sessions completed
- average accuracy
- average fluency
- best score
- last practiced time

## 21. Authentication

Authentication uses:

- password hashing in `auth_service.py`
- JWT access tokens
- `Authorization: Bearer <token>` headers

Flow:

1. User registers or logs in.
2. Backend verifies credentials.
3. Backend returns token.
4. Frontend stores token.
5. Protected requests include bearer token.
6. Backend resolves current user from token.

The current user connects:

- analyses
- history
- reports
- training sessions
- training progress
- profile

## 22. Guided Training Module

File: `backend/app/services/training_catalog.py`

SpeechWell includes four static training modules:

- Breath and Voice Control.
- Articulation Practice.
- Fluency Training.
- Sentence and Grammar Practice.

Each module has three exercises. Examples:

- Vowel Hold: hold `aaa` steadily.
- Count On One Breath: count one to five on one breath.
- Minimal Pairs: repeat `pat, bat, pat, bat`.
- Tongue Tip Drill: practice `tea, day, no, light`.
- Slow Read: speak a phrase slowly.
- Easy Onset Phrase: begin phrases gently.
- Complete The Sentence: finish a sentence.
- Fix And Say: correct a sentence.

Training can be microphone-based or text-based depending on the exercise.

## 23. Training Evaluation

File: `backend/app/services/training_service.py`

Training evaluation computes:

- `accuracy_score`: how closely spoken or typed words match expected text.
- `fluency_score`: penalty-based score from long pauses and repeated words.
- `confidence_score`: combined score from accuracy, fluency, and completion.
- `long_pause_count`: pauses at least 1.2 seconds in training segments.
- `repeated_word_count`: adjacent or near-adjacent repeated words.
- `corrected_text`: simple or model-improved sentence.
- `feedback`: short practical suggestions.

Accuracy equation:

```text
accuracy = matched_expected_words / total_expected_words
accuracy_score = round(accuracy * 100)
```

Open response scoring:

```text
open_response_score = min(word_count / 6, 1.0)
```

Text fluency:

```text
fluency_ratio = 1.0 - repeated_word_count * 0.1
fluency_score = round(clamp(fluency_ratio, 0, 1) * 100)
```

Audio fluency:

```text
fluency_ratio = 1.0
fluency_ratio -= long_pause_count * 0.15
fluency_ratio -= repeated_word_count * 0.10
fluency_score = round(clamp(fluency_ratio, 0, 1) * 100)
```

Confidence:

```text
confidence_ratio =
    accuracy_ratio * 0.50
  + fluency_ratio * 0.30
  + completion_bonus * 0.20

confidence_score = round(confidence_ratio * 100)
```

For text grammar training, grammar quality can also boost confidence.

## 24. AI Chat

The backend includes a chat endpoint:

```text
POST /api/chat
```

It can use analysis context when available. The purpose is to give user-facing speech improvement guidance based on current or previous results.

The chat provider behavior depends on configured environment variables and the service implementation.

## 25. Environment and Configuration

Common configuration values:

- `VITE_API_URL`: frontend API base URL.
- `CORS_ORIGINS`: comma-separated allowed frontend origins.
- `WHISPER_MODEL`: optional Whisper model override.
- `GRAMMAR_PROVIDER`: `openai`, `gemini`, `ollama`, or `auto`.
- `OPENAI_API_KEY`: OpenAI key for grammar/chat if used.
- `OPENAI_MODEL`: OpenAI model name if used.
- `GEMINI_API_KEY`: Gemini key if used.
- `GEMINI_MODEL`: Gemini model name if used.
- `OLLAMA_BASE_URL`: local or remote Ollama endpoint.
- `OLLAMA_MODEL` or `GRAMMAR_OLLAMA_MODEL`: local model name.

Deployment:

- Frontend can deploy to Vercel using root `vercel.json`.
- Backend can deploy to Docker-friendly hosts such as Render, Railway, Fly.io, a VM, or container platform.
- Backend needs Python audio and ML dependencies, FFmpeg, model files, storage, and database state.

## 26. API Response Meaning

Common analysis fields:

- `dysarthria_probability`: probability-like risk score from 0 to 1.
- `dysarthria_label`: `healthy`, `dysarthria`, or fallback `unknown`.
- `stuttering_probability`: disfluency score from 0 to 1.
- `grammar_score`: grammar quality from 0 to 1, where higher is better.
- `phonological_score`: articulation/phonological risk score depending on API naming, often probability-like.
- `speaking_rate_wps`: words per second.
- `average_pause_sec`: average pause duration.
- `max_pause_sec`: longest pause.
- `total_duration_sec`: audio length.
- `overall_score`: combined 0 to 100 score.

Display conversion:

```text
percent = round(probability * 100)
```

For risk probabilities:

- Higher is worse.
- Example: dysarthria 40 percent means moderate risk signal.

For quality scores:

- Higher is better.
- Example: grammar quality 80 percent means strong grammar clarity.

## 27. Practical Output Interpretation

Read the output as a set of indicators:

- Dysarthria probability: motor-speech risk evidence.
- Symptom score: acoustic evidence supporting or weakening dysarthria risk.
- Stuttering probability: disfluency evidence.
- Repetitions, prolongations, blocks: event counts behind fluency score.
- Grammar quality: how stable the transcript is as a sentence.
- Corrected text: suggested cleaned-up sentence.
- Phonological probability: articulation instability proxy.
- Overall score: combined practical score, not a diagnosis.

Example interpretation:

```text
Dysarthria: 40%
Stuttering: 20%
Grammar quality: 75%
Overall: 68%
```

This means:

- The dysarthria model sees some risk evidence, but likely below the project threshold for a positive label.
- Fluency/disfluency evidence is low.
- Grammar is fairly good but has room for improvement.
- The overall score is limited mostly by pronunciation risk and grammar clarity.

## 28. Known Limitations

Important limitations:

- Audio quality strongly affects results.
- Background noise can affect spectral features.
- Microphone distance can affect RMS and silence ratio.
- Whisper transcription errors can affect grammar, stuttering, and phonology estimates.
- The phonological module is a proxy, not true phoneme alignment.
- Grammar correction can depend on the configured provider.
- Model metrics are based on available datasets and may not represent every real-world accent, age group, condition, language variety, or microphone setup.
- Dysarthria labels require careful interpretation because clinical diagnosis requires professional assessment.

## 29. Why Multiple Modules Are Used

Speech is complex. One number cannot explain everything.

SpeechWell separates:

- Motor speech risk: dysarthria module.
- Fluency and disfluency: stuttering module.
- Language structure: grammar module.
- Articulation pattern risk: phonology module.
- Practice progress: training module.

This modular design lets the app say not just "score is low", but "why it may be low."

## 30. A to Z Summary

SpeechWell works like this:

1. A user logs in.
2. The frontend records or uploads speech.
3. FastAPI receives the file.
4. The file is stored.
5. FFmpeg normalizes audio to mono 16 kHz WAV.
6. Whisper transcribes the speech.
7. Whisper timing and waveform silence detection produce duration, speaking rate, pauses, and segments.
8. Raw signal extraction computes energy, silence, zero crossing, spectral, chroma, contrast, and MFCC features.
9. Wav2Vec2 can produce a 768-dimensional acoustic embedding.
10. The dysarthria model estimates raw class probability.
11. Symptom gating adjusts or confirms the dysarthria decision.
12. The stuttering module counts repetitions, prolongations, blocks, and rate instability.
13. The grammar module corrects the transcript and estimates grammar error probability.
14. The phonology module estimates articulation instability risk from transcript and segment patterns.
15. Scores are combined into an overall 0 to 100 score.
16. Results are saved in SQLite.
17. A PDF report is generated.
18. The frontend displays results, history, dashboard cards, and report links.
19. The user can practice in guided training modules.
20. Training attempts are evaluated and saved as progress.

In short: SpeechWell turns an audio recording into transcript data, signal features, model probabilities, explainable event counts, a report, and a path for practice.
