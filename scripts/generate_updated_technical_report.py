from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.update_phase2_report import apply_range, build_replacements, iter_non_empty_paragraphs

INPUT_CANDIDATES = [
    Path(r"c:\Users\franc\Downloads\phase2_report_speechwell (1) on work.docx"),
    ROOT / "phase2_report_speechwell (1) on work.docx",
]
OUTPUT_DOCX = ROOT / "Updated_Technical_Report.docx"


def resolve_input_docx() -> Path:
    for candidate in INPUT_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not find the source DOCX. Checked:\n"
        + "\n".join(f"- {candidate}" for candidate in INPUT_CANDIDATES)
    )


def build_overrides() -> dict[tuple[int, int], list[str]]:
    return {
        (361, 372): [
            "The proposed SpeechWell system is an integrated speech analysis and guided training platform that combines a browser-based user interface, a FastAPI backend, persistent storage, and modular analysis services. Instead of treating the project as a single speech-disorder classifier, the implemented system coordinates several specialized components that work together on each user session.",
            "At the interaction layer, users register or log in, upload or record speech, review results, revisit history, download reports, and access guided practice modules through the React frontend. Shared navigation, dashboard views, results pages, history pages, the Therapy Hub, training flows, profile management, and AI chat all connect to the same backend API.",
            "On the backend, the analysis request starts when the frontend sends `POST /api/analyze`. The server validates the file type, saves the original upload, creates an analysis row with status `processing`, and normalizes the audio to mono 16 kHz WAV using FFmpeg.",
            "The normalized file is then passed to `ml/services/speech_analysis_service.py`, which orchestrates transcript generation, timing analysis, grammar scoring, acoustic embedding extraction, dysarthria inference, stuttering scoring, and phonological scoring. This orchestration layer returns a combined result dictionary rather than a single prediction.",
            "The first practical analysis stage is transcript and timing extraction. `ml/feature_extraction/extract_whisper.py` loads the preferred Whisper model available locally, transcribes the audio, records segment boundaries, computes speaking rate, measures pause durations, and tracks long-pause counts.",
            "The second stage derives waveform-based evidence for dysarthria. `ml/feature_extraction/raw_audio_features.py` extracts a broad numeric descriptor set from the waveform, and the dysarthria service feeds the corresponding 98-feature schema into the active saved model.",
            "The deployed dysarthria decision path does not stop at the model probability. `backend/app/services/dysarthria_inference_service.py` computes a symptom score, applies healthy-speech guardrails, and only confirms dysarthria when both the probability and the symptom evidence remain strong after post-processing.",
            "The remaining analysis services operate in parallel but remain logically separate. `stuttering_service.py` estimates fluency disruption from repetitions, prolongations, blocks, pause variability, and rate variability; `grammar_service.py` evaluates transcript quality and corrected text; and `phonological_service.py` estimates articulation instability from transcript and segment behavior.",
            "After inference, the backend stores the resulting transcript, probabilities, counts, timing metrics, and status fields in SQLite. This persistence layer supports history views, dashboard summaries, and later report downloads.",
            "SpeechWell also contains a guided training subsystem. Static modules and exercises are defined in `backend/app/services/training_catalog.py`; sessions are created and evaluated through the training API endpoints; and training progress is synchronized into a dedicated `training_progress` table for later dashboard use.",
            "When a user practices a guided exercise, the backend evaluates either microphone or text input, computes accuracy, fluency, confidence, repeated-word count, long-pause count, and corrected text, then stores the completed session. This turns the project into a continuous practice tool rather than a one-time screening app.",
            "The Therapy Hub additionally embeds curated YouTube practice videos, so the proposed system combines formal analysis, stored reporting, guided exercises, saved progress, and supplementary practice material inside one full-stack architecture.",
        ],
        (374, 379): [
            "The system performs multi-output analysis instead of limiting itself to one classifier output, returning dysarthria, stuttering, grammar, phonological, and timing results from the same uploaded sample.",
            "It uses a stronger runtime dysarthria pipeline based on raw-audio features and symptom-gated post-processing, which improves reliability over the legacy logistic-regression path.",
            "The architecture is fully deployable as a web platform with React-based interaction, FastAPI APIs, SQLite persistence, audio/report file storage, and downloadable PDF summaries.",
            "Beyond analysis, SpeechWell provides a guided training subsystem with predefined practice modules, exercise-by-exercise session evaluation, and progress synchronization linked to the authenticated user account.",
            "Grammar feedback is actionable because the backend stores corrected text, grammar quality estimates, and transcript context rather than only a binary error flag.",
            "The Therapy Hub also presents curated YouTube practice videos, giving the system both structured internal exercises and lightweight external support resources.",
        ],
        (385, 398): [
            "The implemented SpeechWell architecture is better described as a full-stack workflow than as three isolated blocks. The actual system contains a React frontend, a FastAPI backend, a modular analysis layer, SQLite persistence, and file storage for uploaded audio, processed audio, and generated reports.",
            "At the frontend layer, routes such as Landing, Upload, Results, History, Dashboard, Therapy Hub, Training Module, Training Exercise, Training Result, Profile, and AI Chat provide the user-facing entry points. These pages call a shared API client in `speechwell-frontend/src/api/api.ts`.",
            "The backend layer exposes authentication endpoints, profile endpoints, analysis endpoints, report download endpoints, training endpoints, progress endpoints, and a chat endpoint. This makes the speech-analysis workflow part of a broader user account and practice system.",
            "Audio handling begins when the backend saves the original recording and normalizes it with FFmpeg. The normalized file is then passed to the ML orchestration layer, which performs Whisper transcription, pause analysis, dysarthria inference, grammar scoring, phonological scoring, and stuttering analysis.",
            "The dysarthria branch uses raw-audio features and the active saved model artifact. The grammar branch corrects transcript text through a configured provider and estimates grammar quality locally. The stuttering and phonological branches remain transparent heuristic services rather than hidden black-box models.",
            "All analysis outputs are written into SQLite through the `analyses` table, where transcript text, probabilities, counts, timing values, report filename, status, and ownership are preserved.",
            "A report-generation block then converts the stored outputs into a styled PDF through ReportLab so that the user can download a clinical-style summary from the frontend.",
            "Parallel to the analysis branch, the training branch starts guided practice sessions. The training catalog defines fixed modules and exercises, session-start endpoints create practice records, and evaluation endpoints score text or audio attempts using transcript matching, repeated-word counting, long-pause counting, grammar cleanup, and confidence scoring.",
            "Completed training sessions are aggregated into the `training_progress` table so the dashboard and Therapy Hub can display sessions completed, average accuracy, average fluency, and best score for each module.",
            "The Therapy Hub also contains a curated YouTube video library that supports self-guided practice. These videos complement the internal exercise engine rather than replacing it.",
            "Because each block communicates through explicit APIs and stored fields, the architecture is maintainable and extensible. New models can be swapped into the dysarthria service, and new exercises can be added to the training catalog without rewriting the whole system.",
            "Therefore, the corrected block diagram explanation should present SpeechWell as a full-stack architecture: frontend interaction, backend routing, audio normalization, speech-analysis services, training/session evaluation, persistence/reporting, and supplementary practice-video guidance all participate in the final system behavior.",
            "This code-based explanation is more accurate than the original generic diagram text because it directly matches the files and APIs implemented in the repository.",
            "The design also shows why the project is suitable for academic evaluation: it combines software engineering, machine learning, data persistence, and user-facing speech support inside one coherent system.",
        ],
        (403, 416): [
            "The Level 0 Data Flow Diagram should show two main external actors: the user and the SpeechWell platform. The user submits audio or training responses, while SpeechWell returns analysis results, reports, stored history, guided exercise scores, and therapy support resources.",
            "At this level, the core platform receives speech input, performs backend and ML analysis, stores the resulting records, and returns structured outputs to the frontend. The output is not just a yes-or-no disorder label; it includes transcripts, probabilities, counts, metrics, reports, and practice feedback.",
            "The Level 1 Data Flow Diagram should then expand SpeechWell into its major service groups: authentication and profile context, analysis upload and normalization, speech-analysis orchestration, persistence and reporting, guided training evaluation, and Therapy Hub support content.",
            "In the analysis branch, audio enters through the upload interface, is validated and normalized by the backend, and is passed to the combined analysis pipeline. The pipeline produces dysarthria, stuttering, grammar, phonological, and timing outputs that are stored and returned to the Results and History views.",
            "In the training branch, the user opens the Therapy Hub, selects a module and exercise, starts a session, submits either text or audio, and receives practice scores plus feedback. Completed sessions update progress statistics tied to the same account.",
            "The Level 2 Data Flow Diagram for analysis should begin with file upload, backend validation, storage of the original file, and FFmpeg normalization. These are the real preprocessing steps implemented in `backend/app/main.py`.",
            "After normalization, Whisper transcription and pause analysis run first. This stage outputs transcript text, segment timestamps, pause durations, speaking rate, and total duration.",
            "The next Level 2 stage extracts raw-audio waveform features for the current dysarthria model. In parallel, the system may also compute a Wav2Vec2 acoustic embedding that is retained for legacy compatibility and safe fallback behavior.",
            "The dysarthria service then loads the active model artifact, predicts a raw probability, computes symptom evidence, applies healthy-speech guardrails, and returns a final label with explanation.",
            "The stuttering service analyzes repetitions, prolongations, and blocks together with pause variability and rate instability to return a probability-like fluency disruption score.",
            "The grammar service corrects transcript text through the configured provider, estimates error count, and computes grammar quality metrics. The phonological service separately estimates articulation instability from transcript and segment behavior.",
            "A separate Level 2 flow for training begins with session creation, continues with text or audio submission, derives transcript or normalized text, calculates accuracy and fluency measures, attaches grammar cleanup when relevant, saves the session, and updates module progress aggregates.",
            "All module outputs are then merged into final payloads, persisted in the database, and forwarded either to the PDF report generator or to the training-result view. This makes the corrected data flow more faithful to the actual implementation than the original single-branch description.",
            "Hence, the real high-level flow is upload or practice input -> normalization/transcription -> specialized analysis or exercise evaluation -> storage/report generation/progress sync -> UI visualization and follow-up support.",
        ],
        (420, 423): [
            "The implementation of the SpeechWell system follows a connected frontend-backend-service architecture. The React frontend handles authentication, audio upload, results presentation, history browsing, guided training pages, AI chat, and profile management, while the FastAPI backend exposes the REST endpoints that coordinate these features.",
            "On each analysis request, the backend validates the uploaded file, stores the original audio, normalizes it to mono 16 kHz WAV with FFmpeg, and calls `run_full_analysis(...)` in `ml/services/speech_analysis_service.py`. That orchestration layer then invokes Whisper timing extraction, grammar scoring, acoustic embedding extraction, symptom-gated dysarthria inference, heuristic stuttering detection, and phonological proxy detection with safe fallbacks for runtime robustness.",
            "The analysis outputs are written to the `analyses` table together with transcript text, dysarthria label, stuttering event counts, grammar metrics, phonological counts, timing metrics, report filename, and processing status. A dedicated ReportLab service then generates a downloadable PDF report from those stored values.",
            "The implementation also includes a guided training subsystem. Fixed practice modules are exposed through `/api/training/modules`, new sessions are created through `/api/training/session/start`, responses are evaluated through `/api/training/session/evaluate`, and training progress is stored in `training_sessions` and `training_progress`. The Therapy Hub then combines this structured exercise engine with curated YouTube practice videos for additional support.",
        ],
        (515, 523): [
            "Module 3 is the exercise, reporting, and progress stage of SpeechWell. Its role is to turn analysis outputs into usable feedback while also supporting repeated guided practice and long-term tracking.",
            "For analysis requests, the backend writes the final result fields into the `analyses` table and generates a PDF report through `backend/app/services/pdf_report_service.py`. The report summarizes overall score, dysarthria and stuttering analysis, timing metrics, transcript review, and language analysis.",
            "For guided practice, the Therapy Hub exposes static modules and exercises defined in `backend/app/services/training_catalog.py`. These modules cover breath and voice control, articulation practice, fluency training, and sentence or grammar practice.",
            "When a learner starts an exercise, the backend creates a `training_sessions` record before the attempt begins. The evaluation endpoint then accepts either microphone input or text input, computes transcript quality, expected-text accuracy, fluency score, confidence score, long-pause count, repeated-word count, duration, and corrected text, and saves the finished session.",
            "Completed sessions are summarized per module in the `training_progress` table through `sync_progress(...)`, which updates sessions completed, average accuracy, average fluency, best score, and last practiced time. This gives the project a real progress-monitoring subsystem instead of a generic placeholder claim.",
            "The frontend Training Result page then shows the saved transcript, cleaned sentence, practical feedback items, and numerical scores for the attempt, allowing the user to retry the same exercise or return to the module overview.",
            "The Therapy Hub also includes curated YouTube practice videos grouped by support category. These videos complement the internal exercise engine and provide additional self-practice material after analysis or training.",
            "Module 3 therefore combines three user-facing outputs: downloadable reports, guided exercise evaluation, and persisted progress tracking.",
            "This description matches the actual repository more accurately than the original text, which claimed a recommendation engine that is not present in the current codebase.",
        ],
        (525, 534): [
            "Step 1: Store the completed analysis outputs in the `analyses` table and generate a PDF report when possible.",
            "Step 2: Load the guided module catalog from the static training definitions.",
            "Step 3: Start a new training session by saving the selected module and exercise in `training_sessions`.",
            "Step 4: Accept either text input or recorded audio for the active exercise attempt.",
            "Step 5: For text exercises, score expected-word accuracy, repeated words, grammar cleanup, and confidence.",
            "Step 6: For audio exercises, normalize/transcribe the recording and score accuracy, long pauses, repeated words, fluency, and confidence.",
            "Step 7: Save transcript, corrected text, feedback summary, and numerical scores in the session record.",
            "Step 8: Update `training_progress` with sessions completed, average accuracy, average fluency, best score, and last practiced time.",
            "Step 9: Return the saved result to the Training Result page so the learner can review feedback and retry.",
            "Step 10: Provide supplementary practice videos inside the Therapy Hub for continued self-guided support.",
        ],
        (651, 653): [
            "The corrected performance and implementation review shows that SpeechWell is currently a full-stack speech analysis and guided practice application rather than a narrow single-model prototype. The deployed workflow starts with browser-based audio upload or recording, normalizes audio in the FastAPI backend, extracts transcript and timing information with Whisper, derives raw waveform features for dysarthria inference, and combines this with separate stuttering, grammar, and phonological services. Analysis results are stored in SQLite, rendered into PDF reports, surfaced through results and history pages, and connected to a Therapy Hub that also supports guided training sessions and persisted progress tracking. The preferred runtime dysarthria path uses the saved comparison-model artifact backed by HistGradientBoosting and symptom-gated decision logic, while legacy logistic-regression artifacts remain only as fallback compatibility paths.",
            "Future enhancement should therefore focus on areas that are genuinely unfinished in the codebase: broader and more balanced clinically validated datasets, formal offline evaluation for the stuttering and phonological services, stronger calibration and explanation for dysarthria probability under symptom gating, richer adaptive exercise generation beyond the fixed training catalog, better linkage between analysis findings and training recommendations, and multilingual or clinician-supervised expansion. These directions align with the actual repository and provide a realistic path for improving SpeechWell without overstating functionality that is not yet implemented.",
        ],
    }


def main() -> None:
    input_docx = resolve_input_docx()
    replacements = build_replacements()
    overrides = build_overrides()
    final_replacements: list[tuple[int, int, list[str]]] = []

    for start, end, lines in replacements:
        final_replacements.append((start, end, overrides.get((start, end), lines)))

    with zipfile.ZipFile(input_docx, "r") as zin:
        root = ET.fromstring(zin.read("word/document.xml"))
        paragraphs = iter_non_empty_paragraphs(root)

        for start, end, replacement_texts in final_replacements:
            apply_range(paragraphs, start, end, replacement_texts)

        updated_document = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        with zipfile.ZipFile(OUTPUT_DOCX, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = updated_document
                zout.writestr(item, data)

    print(f"Updated report written to: {OUTPUT_DOCX}")


if __name__ == "__main__":
    main()
