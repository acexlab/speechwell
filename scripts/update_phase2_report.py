from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("w", W_NS)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_DOCX = PROJECT_ROOT / "phase2_report_speechwell (1) on work.docx"
OUTPUT_DOCX = PROJECT_ROOT / "phase2_report_speechwell_updated.docx"


def w_tag(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def load_json(rel_path: str) -> dict:
    return json.loads((PROJECT_ROOT / rel_path).read_text(encoding="utf-8"))


def paragraph_text(paragraph: ET.Element) -> str:
    text = "".join((node.text or "") for node in paragraph.findall(".//" + w_tag("t")))
    return text.strip()


def iter_non_empty_paragraphs(root: ET.Element) -> list[ET.Element]:
    paragraphs: list[ET.Element] = []
    for paragraph in root.findall(".//" + w_tag("p")):
        if paragraph_text(paragraph):
            paragraphs.append(paragraph)
    return paragraphs


def clear_paragraph(paragraph: ET.Element) -> None:
    for child in list(paragraph):
        if child.tag != w_tag("pPr"):
            paragraph.remove(child)


def set_paragraph_text(paragraph: ET.Element, text: str) -> None:
    clear_paragraph(paragraph)
    if not text:
        return

    run = ET.SubElement(paragraph, w_tag("r"))
    text_el = ET.SubElement(run, w_tag("t"))
    text_el.set(f"{{{XML_NS}}}space", "preserve")
    text_el.text = text


def apply_range(paragraphs: list[ET.Element], start: int, end: int, replacements: list[str]) -> None:
    slots = paragraphs[start - 1 : end]
    if len(replacements) > len(slots):
        raise ValueError(
            f"Replacement range {start}-{end} has {len(slots)} slots but {len(replacements)} paragraphs supplied."
        )

    for paragraph, text in zip(slots, replacements):
        set_paragraph_text(paragraph, text)

    for paragraph in slots[len(replacements) :]:
        set_paragraph_text(paragraph, "")


def metric_percent(value: float) -> str:
    return f"{value * 100:.2f}"


def build_replacements() -> list[tuple[int, int, list[str]]]:
    legacy = load_json("ml/evaluation/validation_report.json")
    group_v2 = load_json("ml/evaluation/validation_report_v2_group.json")
    full_v2 = load_json("ml/evaluation/validation_report_v2_rf_svc_ensemble.json")
    comparison = load_json("ml/evaluation/dysarthria_model_comparison_report.json")
    comparison_holdout = comparison["best_model_holdout_metrics"]

    accuracy_rows = [
        "Evaluation Snapshot",
        "Source File",
        "Accuracy (%)",
        "Legacy v1 logistic + PCA path",
        "validation_report.json",
        metric_percent(legacy["accuracy"]),
        "TORGO group-aware v2 model",
        "validation_report_v2_group.json",
        metric_percent(group_v2["accuracy"]),
        "TORGO full-data RF+SVC validation",
        "validation_report_v2_rf_svc_ensemble.json",
        metric_percent(full_v2["accuracy"]),
        "Runtime comparison model holdout",
        "dysarthria_model_comparison_report.json",
        metric_percent(comparison_holdout["accuracy"]),
    ]
    precision_rows = [
        "Evaluation Snapshot",
        "Source File",
        "Precision (%)",
        "Legacy v1 logistic + PCA path",
        "validation_report.json",
        metric_percent(legacy["precision"]),
        "TORGO group-aware v2 model",
        "validation_report_v2_group.json",
        metric_percent(group_v2["precision"]),
        "TORGO full-data RF+SVC validation",
        "validation_report_v2_rf_svc_ensemble.json",
        metric_percent(full_v2["precision"]),
        "Runtime comparison model holdout",
        "dysarthria_model_comparison_report.json",
        metric_percent(comparison_holdout["precision"]),
    ]
    f1_rows = [
        "Evaluation Snapshot",
        "Source File",
        "F1 Score (%)",
        "Legacy v1 logistic + PCA path",
        "validation_report.json",
        metric_percent(legacy["f1_score"]),
        "TORGO group-aware v2 model",
        "validation_report_v2_group.json",
        metric_percent(group_v2["f1_score"]),
        "TORGO full-data RF+SVC validation",
        "validation_report_v2_rf_svc_ensemble.json",
        metric_percent(full_v2["f1_score"]),
        "Runtime comparison model holdout",
        "dysarthria_model_comparison_report.json",
        metric_percent(comparison_holdout["f1_score"]),
    ]
    recall_rows = [
        "Evaluation Snapshot",
        "Source File",
        "Recall (%)",
        "Legacy v1 logistic + PCA path",
        "validation_report.json",
        metric_percent(legacy["recall"]),
        "TORGO group-aware v2 model",
        "validation_report_v2_group.json",
        metric_percent(group_v2["recall"]),
        "TORGO full-data RF+SVC validation",
        "validation_report_v2_rf_svc_ensemble.json",
        metric_percent(full_v2["recall"]),
        "Runtime comparison model holdout",
        "dysarthria_model_comparison_report.json",
        metric_percent(comparison_holdout["recall"]),
    ]

    appendix_lines = ["backend/app/services/pdf_report_service.py"]
    appendix_lines.extend((PROJECT_ROOT / "backend/app/services/pdf_report_service.py").read_text(encoding="utf-8").splitlines())
    appendix_lines = appendix_lines[:170]

    replacements: list[tuple[int, int, list[str]]] = []

    replacements.append(
        (
            49,
            49,
            [
                (
                    "SpeechWell is a full-stack speech analysis and guided practice platform built with a React frontend, "
                    "a FastAPI backend, SQLite persistence, and a modular machine-learning pipeline. The current system accepts "
                    "recorded or uploaded audio, normalizes it to mono 16 kHz WAV, generates transcripts and timing features with "
                    "Whisper, extracts raw-audio descriptors from the waveform, and returns multi-output analysis results that include "
                    "dysarthria probability and label, stuttering probability, grammar quality feedback, phonological-error risk, and "
                    "speech-timing metrics. The preferred deployed dysarthria path uses a symptom-gated HistGradientBoosting pipeline "
                    "saved in `ml/models/dysarthria_best_comparison_model.pkl`, while Wav2Vec2 embeddings remain available mainly for a "
                    "legacy fallback route. Grammar correction is handled through configurable OpenAI, Gemini, or Ollama providers with "
                    "local score estimation, and stuttering plus phonological analysis are implemented as transparent heuristic services. "
                    "SpeechWell also stores analysis history, generates PDF reports, and includes a Therapy Hub that displays curated "
                    "YouTube practice videos for different speech-support categories. The project therefore functions as an integrated speech analysis and "
                    "practice-support system rather than a single standalone classifier."
                )
            ],
        )
    )

    replacements.append(
        (
            193,
            205,
            [
                "Advancements in digital signal processing, automatic speech recognition, and practical machine-learning deployment have made it possible to build end-to-end speech analysis systems that operate on raw user audio instead of manually curated acoustic summaries alone.",
                "SpeechWell addresses this opportunity by combining runtime audio normalization, transcription, timing analysis, raw-audio feature extraction, disorder scoring, PDF reporting, and guided training inside one connected software stack.",
                "In the current implementation, every uploaded or recorded file is first stored by the backend and normalized with FFmpeg to a mono 16 kHz WAV file so that downstream extractors receive a consistent audio format regardless of the original recording source.",
                "After normalization, the system derives transcript and timing features with Whisper and computes speaking rate, pause durations, total duration, long-pause counts, and per-segment speech statistics that are later reused by multiple analysis services.",
                "For dysarthria detection, the project no longer relies on a simple fluency-only logistic regression workflow as the primary runtime path. Instead, it extracts a large raw-audio descriptor set from the waveform and feeds the current deployed model with the same schema used during offline training.",
                "The raw-audio extractor computes amplitude statistics, silence ratio, zero-crossing measures, spectral centroid, bandwidth, rolloff, flatness, chroma summaries, spectral-contrast summaries, and MFCC, delta-MFCC, and delta-delta MFCC statistics. The deployed comparison model consumes 98 numeric features after excluding the leakage-prone `sample_rate` and `channels` fields during training.",
                "The preferred deployed artifact is `ml/models/dysarthria_best_comparison_model.pkl`, whose saved best model is `HistGradientBoostingClassifier` with a tuned threshold of 0.85 according to `ml/evaluation/dysarthria_model_comparison_report.json`.",
                "Runtime dysarthria inference is intentionally stricter than a raw model score. The backend computes a symptom score from waveform evidence, counts healthy-speech signals such as adequate word count and acceptable pause behavior, and only returns a dysarthria label when probability and symptom evidence jointly support that decision.",
                "SpeechWell also separates the other analysis tasks instead of treating them as one classifier head. Stuttering detection is a heuristic fluency scorer, grammar correction is a configurable transcript-quality service, and phonological scoring is a lightweight articulation-instability proxy derived from transcript and segment patterns.",
                "From a software-architecture perspective, the project is implemented as a full-stack application. The React frontend exposes upload, results, dashboard, history, therapy, profile, and chat pages, while the FastAPI backend coordinates authentication, analysis APIs, training APIs, storage, and reporting.",
                "Analysis results are persisted in SQLite together with transcripts, dysarthria outputs, stuttering event counts, grammar scores, phonological counts, timing metrics, report filenames, and processing status so that users can revisit previous sessions and download generated reports.",
                "The platform is also motivated by the need for structured at-home support. SpeechWell includes a Therapy Hub that organizes curated YouTube practice videos for dysarthria, fluency, articulation, and grammar-related guidance, extending the system beyond one-time disorder screening.",
                "Overall, the project is motivated by the need for an interpretable, modular, and deployable speech-support system that combines speech analysis, persistence, reporting, and guided practice without mixing unsupported claims into the implemented runtime pipeline.",
            ],
        )
    )

    replacements.append(
        (
            208,
            213,
            [
                "To normalize user audio, transcribe it, and extract reliable waveform and timing features that can be reused across dysarthria, stuttering, grammar, and phonological analysis services.",
                "To implement a multi-output speech analysis pipeline in which dysarthria uses the currently deployed symptom-gated comparison model, while stuttering, grammar, and phonological scores are produced by separate specialized modules.",
                "To provide an end-to-end web application that stores analysis history, generates PDF reports, and connects analysis outputs to a Therapy Hub of curated YouTube practice videos.",
                "The first objective emphasizes building a reproducible preprocessing and feature-extraction path. In the current codebase this includes file upload handling, FFmpeg normalization, Whisper-based transcript and pause analysis, raw-audio feature extraction, and safe fallbacks when individual services fail.",
                "The second objective focuses on accurate and interpretable inference rather than a single opaque model. SpeechWell therefore combines a saved classical ML pipeline for dysarthria with rule-based or provider-assisted modules for stuttering, grammar, and phonological scoring so that each output matches the data actually available at runtime.",
                "The third objective is application-level usefulness. The system is designed not only to classify one sample but also to preserve session history, render downloadable reports, and connect users to a Therapy Hub of category-based YouTube practice videos.",
            ],
        )
    )

    replacements.append(
        (
            333,
            336,
            [
                "Frontend: React, Vite and TypeScript",
                "Backend: FastAPI, SQLAlchemy, SQLite and JWT-based authentication",
                "Speech / ML stack: Python, scikit-learn, Whisper, transformers, librosa, torchaudio and ReportLab",
                "Grammar / AI services: configurable OpenAI, Gemini or local Ollama providers",
            ],
        )
    )

    replacements.append(
        (
            361,
            372,
            [
                "The proposed SpeechWell system is an integrated speech analysis and guided training platform that combines a browser-based user interface, a FastAPI backend, persistent storage, and modular analysis services. Instead of treating the project as a single speech-disorder classifier, the implemented system coordinates several specialized components that work together on each user session.",
                "At the interaction layer, users register or log in, upload or record speech, review results, revisit history, download reports, and access guided practice modules through the React frontend. Shared navigation, dashboard views, results pages, history pages, and the Therapy Hub all connect to the same backend API.",
                "On the backend, the analysis request starts when the frontend sends `POST /api/analyze`. The server validates the file type, saves the original upload, creates an analysis row with status `processing`, and normalizes the audio to mono 16 kHz WAV using FFmpeg.",
                "The normalized file is then passed to `ml/services/speech_analysis_service.py`, which orchestrates transcript generation, timing analysis, grammar scoring, acoustic embedding extraction, dysarthria inference, stuttering scoring, and phonological scoring. This orchestration layer returns a combined result dictionary rather than a single prediction.",
                "The first practical analysis stage is transcript and timing extraction. `ml/feature_extraction/extract_whisper.py` loads the preferred Whisper model available locally, transcribes the audio, records segment boundaries, computes speaking rate, measures pause durations, and tracks long-pause counts.",
                "The second stage derives waveform-based evidence for dysarthria. `ml/feature_extraction/raw_audio_features.py` extracts a broad numeric descriptor set from the waveform, and the dysarthria service feeds the corresponding 98-feature schema into the active saved comparison model.",
                "The deployed dysarthria decision path does not stop at the model probability. `backend/app/services/dysarthria_inference_service.py` computes a symptom score, applies healthy-speech guardrails, and only confirms dysarthria when both the probability and the symptom evidence remain strong after post-processing.",
                "The remaining analysis services operate in parallel but remain logically separate. `stuttering_service.py` estimates fluency disruption from repetitions, prolongations, blocks, pause variability, and rate variability; `grammar_service.py` evaluates transcript quality and corrected text; and `phonological_service.py` estimates articulation instability from transcript and segment behavior.",
                "After inference, the backend stores the resulting transcript, probabilities, counts, timing metrics, and status fields in SQLite. This persistence layer supports history views, dashboard summaries, and later report downloads.",
                "Report generation is handled as a dedicated backend service. `backend/app/services/pdf_report_service.py` creates a polished clinical-style PDF that summarizes overall score, dysarthria and stuttering analysis, timing metrics, transcript review, and language analysis.",
                "SpeechWell also includes a Therapy Hub for supportive follow-up. In the simplified presentation used for the report and diagram, this hub displays curated YouTube practice videos grouped by speech-support category instead of relying on a heavier internal training-evaluation workflow.",
                "This proposed system therefore improves over a simplified analysis-only design by implementing an actual end-to-end application: frontend interaction, backend orchestration, analysis services, storage, reporting, and therapy-video guidance all operate as connected parts of the same architecture.",
            ],
        )
    )

    replacements.append(
        (
            374,
            379,
            [
                "The system performs multi-output analysis instead of limiting itself to one classifier output, returning dysarthria, stuttering, grammar, phonological, and timing results from the same uploaded sample.",
                "It uses a stronger runtime dysarthria pipeline based on raw-audio features and symptom-gated post-processing, which improves reliability over the legacy logistic-regression path.",
                "The architecture is fully deployable as a web platform with React-based interaction, FastAPI APIs, SQLite persistence, report storage, and downloadable PDF summaries.",
                "Grammar feedback is actionable because the backend stores corrected text, grammar quality estimates, and transcript context rather than only a binary error flag.",
                "The Therapy Hub can direct users to curated YouTube practice material for different speech-support needs without adding extra inference logic to the third module.",
                "The modular backend design also allows future UI or therapy-content changes without redesigning the core analysis workflow.",
            ],
        )
    )

    replacements.append(
        (
            385,
            398,
            [
                "The implemented SpeechWell architecture is better described as a full-stack workflow than as three isolated blocks. The actual system contains a React frontend, a FastAPI backend, a modular analysis layer, SQLite persistence, and file storage for uploaded audio, processed audio, and generated reports.",
                "At the frontend layer, routes such as Landing, Upload, Results, History, Dashboard, Therapy Hub, Training Result, Profile, and AI Chat provide the user-facing entry points. These pages call a shared API client in `speechwell-frontend/src/api/api.ts`.",
                "The backend layer exposes authentication endpoints, profile endpoints, analysis endpoints, training endpoints, report download endpoints, and a chat endpoint. This makes the analysis workflow part of a broader user account and progress-tracking system.",
                "Audio handling begins when the backend saves the original upload into `storage/uploaded_audio/` and writes the normalized WAV file into `storage/processed_audio/`. This explicit storage split preserves both raw and standardized versions of the sample.",
                "The first analysis block is transcript and timing extraction through Whisper. The system computes transcript text, word count, segment boundaries, pause durations, long-pause counts, total duration, and speaking rate from the normalized file.",
                "The second analysis block is raw-audio feature extraction. Instead of using MFCCs alone, the active dysarthria path extracts waveform, spectral, chroma, spectral-contrast, and MFCC-family statistics from the recording.",
                "The dysarthria decision block loads the preferred saved runtime artifact, predicts probability with the current comparison-model pipeline, and then applies symptom-gated logic before returning the final label and explanation.",
                "Stuttering analysis forms a separate block that combines transcript patterns, segment timing, pause variability, and optional acoustic hints into a conservative stuttering probability.",
                "Grammar analysis forms another block in which the transcript is corrected through a configured provider or fallback logic, and a grammar error probability, error estimate, and quality score are derived from both text differences and local structural heuristics.",
                "Phonological analysis is implemented as a lightweight articulation proxy rather than a phoneme-level recognizer. It looks for broken starts, repaired words, elongated spellings, and unstable short segments.",
                "The reporting and persistence block writes results into SQLite and generates a PDF summary through the PDF report service. This block also supports later retrieval by the History page and direct report download.",
                "The therapy-support block is independent from analysis inference but connected through the same frontend experience. It presents categorized YouTube practice videos so users can move from analysis results to relevant follow-up guidance without another internal inference stage.",
                "Because each block communicates through explicit APIs and stored fields, the architecture is maintainable and extensible. New models can be swapped into the dysarthria service, and new exercises can be added to the training catalog without rewriting the whole system.",
                "Therefore, the current block diagram should be interpreted as a full-stack architecture: frontend interaction, backend routing, audio normalization, speech-analysis services, storage/reporting, and therapy-video guidance all participate in the final system behavior.",
            ],
        )
    )

    replacements.append(
        (
            403,
            416,
            [
                "The Level 0 Data Flow Diagram should show two main external actors: the user and the SpeechWell platform. The user submits audio, while SpeechWell returns analysis results, reports, stored history, and therapy-video guidance.",
                "At this level, the core platform receives audio input, performs speech analysis through the backend and ML services, stores the resulting records, and returns structured outputs to the frontend. The output is not just a yes-or-no disorder label; it includes transcripts, probabilities, counts, metrics, reports, and follow-up guidance.",
                "The Level 1 Data Flow Diagram should then expand SpeechWell into its major service groups: authentication and profile context, analysis upload and normalization, speech-analysis orchestration, persistence and reporting, and Therapy Hub video guidance.",
                "In the analysis branch, audio enters through the upload interface, is validated and normalized by the backend, and is passed to the combined analysis pipeline. The pipeline produces dysarthria, stuttering, grammar, phonological, and timing outputs that are stored and returned to the Results and History views.",
                "In the therapy-support branch, the user opens the Therapy Hub and is guided to categorized YouTube practice videos that can be watched inside the application or opened directly on YouTube.",
                "The Level 2 Data Flow Diagram for analysis should begin with file upload, backend validation, storage of the original file, and FFmpeg normalization. These are the real preprocessing steps implemented in `backend/app/main.py`.",
                "After normalization, Whisper transcription and pause analysis run first. This stage outputs transcript text, segment timestamps, pause durations, speaking rate, and total duration.",
                "The next Level 2 stage extracts raw-audio waveform features for the current dysarthria model. In parallel, the system may also compute a Wav2Vec2 acoustic embedding that is retained for legacy compatibility and safe fallback behavior.",
                "The dysarthria service then loads the active model artifact, predicts a raw probability, computes symptom evidence, applies healthy-speech guardrails, and returns a final label with explanation.",
                "The stuttering service analyzes repetitions, prolongations, and blocks together with pause variability and rate instability to return a probability-like fluency disruption score.",
                "The grammar service corrects transcript text through the configured provider, estimates error count, and computes grammar quality metrics. The phonological service separately estimates articulation instability from transcript and segment behavior.",
                "All module outputs are then merged into a final analysis payload, persisted in the database, and forwarded to the PDF report generator and frontend response model.",
                "This Level 2 flow is important because it reflects the actual implemented pipeline: one normalized audio file drives several specialized services, and their combined outputs are stored as a single analysis record.",
                "Hence, the data flow is not MFCC extraction followed by one generic classifier and exercise mapping. The true high-level flow is upload -> normalization -> transcript/timing -> specialized analysis services -> storage/report generation -> UI visualization and therapy-video guidance.",
            ],
        )
    )

    replacements.append(
        (
            420,
            423,
            [
                "The implementation of SpeechWell follows a connected frontend-backend-service architecture. The React frontend handles authentication, audio upload, results presentation, history browsing, guided training pages, AI chat, and profile management, while the FastAPI backend exposes the REST endpoints that coordinate these features.",
                "On each analysis request, the backend validates the uploaded file, stores the original audio, normalizes it to mono 16 kHz WAV with FFmpeg, and calls `run_full_analysis(...)` in `ml/services/speech_analysis_service.py`. That orchestration layer then invokes Whisper timing extraction, grammar scoring, acoustic embedding extraction, symptom-gated dysarthria inference, heuristic stuttering detection, and phonological proxy detection with safe fallbacks for runtime robustness.",
                "The analysis outputs are written to the `analyses` table together with transcript text, dysarthria label, stuttering event counts, grammar metrics, phonological counts, timing metrics, report filename, and processing status. A dedicated ReportLab service then generates a downloadable PDF report from those stored values.",
                "The implementation also includes a Therapy Hub section in the frontend that presents categorized YouTube practice videos. This gives users immediate follow-up material after analysis without making the third module depend on an additional classification or recommendation engine in the report-level architecture.",
            ],
        )
    )

    replacements.append(
        (
            430,
            448,
            [
                "Module 1 is the speech ingestion and feature-building stage of SpeechWell. Its purpose is to transform a user recording into the normalized audio, transcript, timing signals, and waveform descriptors required by the downstream analysis services.",
                "The process begins when the user uploads a supported audio file or records speech through the browser interface. The backend stores the original file so that the raw input remains available for traceability and future report access.",
                "The backend then normalizes the file with FFmpeg by converting it to a mono 16 kHz WAV representation. This step provides a consistent audio format for later extractors and avoids differences caused by sample rate or channel count in the original recording.",
                "After normalization, Whisper transcription is executed through `ml/feature_extraction/extract_whisper.py`. The runtime prefers English Whisper models in the order `small.en`, `base.en`, and `base` depending on local availability.",
                "Whisper returns transcript text together with timestamped segments. Each segment stores start time, end time, duration, word count, and an estimated segment-level speaking rate.",
                "Pause analysis is then performed from the waveform using `librosa.effects.split(...)` when possible, because contiguous Whisper segments alone may hide real silent gaps in the recording.",
                "The total audio duration is computed from the waveform, while the speaking duration is obtained from the sum of valid segment durations. This distinction helps the system separate actual speech time from silence time.",
                "For consecutive speech regions, pause duration is measured as the difference between the start of the current region and the end of the previous region.",
                "Only positive waveform pauses of at least 0.12 seconds are retained for the pause statistics used by the runtime pipeline.",
                "Speaking rate is computed as `total_words / speaking_duration_sec`, so the metric reflects how quickly the speaker produced audible words rather than the raw wall-clock length of the recording.",
                "The average pause duration is computed as the mean of the retained pause list, and the maximum pause duration is the largest retained pause in that list.",
                "Speech timing output also includes `long_pause_count`, which is the number of pause durations greater than or equal to 0.75 seconds.",
                "In parallel with transcript timing extraction, the system can also compute a 768-dimensional Wav2Vec2 embedding through `ml/feature_extraction/extract_acoustic.py`. This vector is mainly retained for the legacy dysarthria fallback path and safe runtime fallback behavior.",
                "The current preferred dysarthria path additionally uses `ml/feature_extraction/raw_audio_features.py`, which extracts waveform statistics, silence ratio, spectral measures, chroma summaries, spectral contrast summaries, and MFCC-family statistics from the normalized recording.",
                "The raw extractor produces 100 numeric descriptors in total, while the currently deployed comparison model uses 98 of them after dropping `sample_rate` and `channels` during training to avoid leakage from recording format.",
                "These descriptors are organized in a structured row so the saved scikit-learn pipeline can receive the same schema that was used during offline training and evaluation.",
                "Module 1 therefore delivers three important outputs to later stages: transcript and timing features, optional acoustic embeddings, and raw-audio feature rows for the active dysarthria model.",
                "By standardizing audio first and then deriving both linguistic and acoustic evidence, this module creates the shared foundation used by all later analysis services in the current SpeechWell implementation.",
                "The output of Module 1 is not a final diagnosis; it is a reusable evidence package that supports dysarthria, fluency, grammar, phonological, report-generation, and training workflows.",
            ],
        )
    )

    replacements.append(
        (
            450,
            465,
            [
                "Step 1: Accept an uploaded or recorded speech sample from the frontend.",
                "Step 2: Store the original file path in backend storage and create an analysis record with status `processing`.",
                "Step 3: Normalize the input audio to mono 16 kHz WAV using FFmpeg.",
                "Step 4: Load the normalized file into the Whisper timing extractor.",
                "Step 5: Generate transcript text and timestamped segments.",
                "Step 6: Compute total word count from the transcript.",
                "Step 7: Estimate speaking duration from segment boundaries.",
                "Step 8: Estimate total recording duration from the waveform.",
                "Step 9: Derive pause durations between spoken regions.",
                "Step 10: Compute `speaking_rate_wps`, `average_pause_sec`, and `max_pause_sec`.",
                "Step 11: Count long pauses from the retained pause list.",
                "Step 12: Extract the optional Wav2Vec2 embedding for legacy compatibility.",
                "Step 13: Extract raw waveform descriptors for the active dysarthria model.",
                "Step 14: Package transcript, segments, pause data, and acoustic features into structured dictionaries.",
                "Step 15: Forward the timing features, embedding, and waveform descriptors to the downstream analysis services.",
                "Step 16: Preserve these intermediate values so they can be reused by report generation and database storage.",
            ],
        )
    )

    replacements.append(
        (
            467,
            498,
            [
                "Module 2 is the analysis and decision stage of SpeechWell. Rather than classifying the recording with one model only, this module coordinates multiple specialized services and returns a combined analysis payload.",
                "The main inputs to Module 2 are the transcript and timing features from Whisper, the normalized audio path, the optional Wav2Vec2 embedding, and the raw waveform descriptor row extracted from the recording.",
                "Grammar analysis is implemented as a transcript-quality service rather than as a branch of the dysarthria model. The grammar service first normalizes the transcript and then requests a corrected version from the configured provider when available.",
                "The current grammar providers are OpenAI chat completions, Gemini, and local Ollama models. Provider choice is controlled through environment configuration and the service falls back to local estimation logic when remote correction is unavailable.",
                "After correction, grammar quality is not derived from the LLM output alone. The backend estimates error count through token-level differences and blends this with local structural heuristics such as fragments, missing verbs, filler density, and punctuation issues.",
                "The result of grammar analysis is a structured output containing `grammar_error_probability`, `grammar_quality_score`, `error_count_estimate`, and `corrected_text`.",
                "Stuttering analysis is implemented as a rule-based fluency scorer in `backend/app/services/stuttering_service.py`. It uses the transcript, Whisper segments, pause durations, speaking rate, and optionally full-recording acoustic features.",
                "The first stuttering signal is repetition count, which captures repeated tokens and repaired speech starts such as one-letter fragments followed by the intended word.",
                "The second signal is prolongation count, which captures stretched vowel spellings, fragment patterns, unusually slow short segments, and selected acoustic hints that align with drawn-out productions.",
                "The third signal is block count, which is derived from pause durations. The service treats pauses above 0.9 seconds as blocks and marks pauses above 1.5 seconds as severe blocks.",
                "These signals are converted into normalized sub-scores and blended with pause variability, segment-rate variability, and a speaking-rate penalty to produce the final stuttering probability.",
                "The weighted stuttering score is: `0.28*repetition_score + 0.24*prolongation_score + 0.26*block_score + 0.08*severe_block_bonus + 0.09*pause_variability + 0.03*segment_rate_variability + 0.02*speaking_rate_penalty`.",
                "Phonological analysis is also separate from dysarthria and stuttering. The project does not implement a phoneme-by-phoneme recognizer, so `phonological_service.py` instead acts as a lightweight articulation-instability proxy.",
                "This service searches for one-letter fragments, repaired words, elongated spellings, slow short segments, and unstable segment-rate patterns that suggest articulation or sequencing difficulty in the transcript.",
                "The phonological probability is computed from a weighted blend of fragment ratio, repair ratio, elongation ratio, segment instability, and slow-segment ratio, and the output includes both an error count and example affected words.",
                "Dysarthria analysis is the most model-driven part of Module 2. The active backend path prefers the saved runtime artifact `ml/models/dysarthria_best_comparison_model.pkl`, and only falls back to the older v2 RF+SVC model or the legacy v1 logistic path when required artifacts are missing.",
                "According to the saved comparison artifact and report, the current preferred runtime classifier is `HistGradientBoostingClassifier` trained on the combined raw-audio feature table and saved together with a threshold of 0.85.",
                "At inference time, the service extracts the raw-audio feature row, orders it according to the saved feature schema, fills missing fields, and feeds the resulting data frame into the saved pipeline for `predict_proba(...)`.",
                "The service then computes a separate symptom score from waveform evidence. Symptoms increase when RMS is very low, silence ratio is high, spectral flatness is elevated, zero-crossing rate is abnormal, or MFCC variance is unusually large.",
                "This symptom score is bounded from 0 to 5 and represents how much dysarthria-like evidence is visible in the full recording outside the model itself.",
                "The service also counts healthy-speech signals such as adequate word count, reasonable speaking rate, acceptable average pause, acceptable maximum pause, enough duration, acceptable silence ratio, and sufficient RMS.",
                "If the model produces a moderately high raw probability but the symptom score is weak, the backend deliberately reduces the probability. This protects against false positives caused by accent mismatch, unseen speakers, or recordings that do not actually show strong dysarthria symptoms.",
                "If the raw model probability is extremely high and the symptom score shows multiple abnormalities, the backend preserves the positive prediction and returns a dysarthria label with an explanation describing the abnormal speech features detected.",
                "The final deployed decision therefore uses both the learned model score and the symptom-gating rules. In the common path, dysarthria is returned only when the adjusted probability remains high and symptom evidence is present.",
                "The current service-level thresholds are stricter than the saved model threshold alone: `SYMPTOM_GATED_DYSARTHRIA_THRESHOLD` is 0.75 for the final label decision, while the raw-probability override uses 0.95 with symptom support.",
                "A legacy fallback path still exists for backward compatibility. When the modern artifact cannot be used, the service loads the older scaler, PCA transform, and logistic-regression model that combine three fluency features with a 768-dimensional acoustic embedding.",
                "Regardless of the branch taken, the dysarthria service returns `label`, `probability`, `symptom_score`, `explanation`, and `model_version`, which makes the result easier to interpret than a plain class label.",
                "Once grammar, stuttering, phonological, and dysarthria analysis complete, `run_full_analysis(...)` merges their outputs into a single dictionary. Safe fallbacks are used when one service fails so that the whole request does not crash unnecessarily.",
                "The combined analysis payload includes transcript text, timing metrics, dysarthria label and probability, stuttering counts and probability, grammar quality values, phonological counts, and supporting fields that are later persisted in the database.",
                "These stored outputs are then consumed by the Results page, History page, Dashboard summaries, PDF report generation, and AI chat context building.",
                "Module 2 therefore acts as the true analytical core of SpeechWell: it converts normalized speech evidence into multiple interpretable outputs instead of forcing all behavior through one simplified classifier design.",
                "This implementation is more faithful to the real codebase because it documents the deployed comparison model, the symptom-gated dysarthria logic, and the separate heuristic/provider-backed services that are actually used in production.",
            ],
        )
    )

    replacements.append(
        (
            500,
            513,
            [
                "Step 1: Receive transcript, timing features, normalized audio path, and acoustic feature outputs from Module 1.",
                "Step 2: Run grammar correction and local grammar score estimation on the transcript.",
                "Step 3: Run stuttering analysis using repetitions, prolongations, blocks, pause variability, and rate variability.",
                "Step 4: Run phonological proxy analysis using transcript fragments and segment instability patterns.",
                "Step 5: Load the preferred runtime dysarthria artifact if available.",
                "Step 6: Extract or sanitize the raw-audio feature row according to the saved model schema.",
                "Step 7: Predict the raw dysarthria probability from the saved scikit-learn pipeline.",
                "Step 8: Compute symptom evidence from full-recording waveform features.",
                "Step 9: Count healthy-speech signals from transcript and timing behavior.",
                "Step 10: Apply symptom-gated probability adjustment and final label rules.",
                "Step 11: Fall back to the older embedding-based logistic path only when the latest artifact cannot be used.",
                "Step 12: Merge dysarthria, stuttering, grammar, phonological, and transcript outputs into one result dictionary.",
                "Step 13: Return the combined analysis payload to the backend handler for storage and reporting.",
                "Step 14: Expose the final multi-output result to the frontend through the analysis API response.",
            ],
        )
    )

    replacements.append(
        (
            515,
            523,
            [
                "Module 3 is the reporting and therapy-guidance stage of SpeechWell. Its role is to turn analysis outputs into user-facing reports and then direct the user to relevant follow-up practice material.",
                "For analysis requests, the backend writes the final result fields into the `analyses` table and generates a PDF report through `backend/app/services/pdf_report_service.py`. The report summarizes overall score, dysarthria and stuttering analysis, timing metrics, transcript review, and language analysis.",
                "In the simplified diagram-aligned presentation, the therapy portion of this module is represented as a video-guidance layer rather than as an internal training-inference subsystem.",
                "The frontend Therapy Hub loads curated YouTube videos from `speechwell-frontend/src/data/practiceVideos.ts` and groups them by support category such as dysarthria training, stuttering or fluency training, speech sound disorder exercises, and grammar or spoken-English improvement.",
                "Users can browse these categorized videos inside SpeechWell, load the selected item into an embedded player, and open the original video on YouTube when needed.",
                "This keeps the third module lightweight and practical: the system performs analysis and reporting first, then presents helpful therapy content without adding another predictive model stage.",
                "Because the therapy content is delivered through a curated frontend video library, the report does not need to describe a separate recommendation engine, model-loading stage, or internal exercise-scoring loop in this module.",
                "Module 3 therefore centers on report delivery and therapy-video access, which is the clearest high-level description for the current diagram revision.",
                "This framing also leaves room for future changes if the heavier training workflow is removed or redesigned later.",
            ],
        )
    )

    replacements.append(
        (
            525,
            534,
            [
                "Step 1: Store the completed analysis outputs in the `analyses` table.",
                "Step 2: Build a unique report filename and generate the PDF report when possible.",
                "Step 3: Return the stored analysis payload to the frontend Results page.",
                "Step 4: Open the Therapy Hub as the follow-up support view.",
                "Step 5: Load categorized YouTube practice videos from the frontend video list.",
                "Step 6: Display the selected video in the embedded player when possible.",
                "Step 7: Provide the original YouTube link for direct viewing when needed.",
                "Step 8: Let the user browse therapy material by category after reviewing the analysis results.",
                "Step 9: Keep the third module focused on video guidance rather than additional internal model inference.",
                "Step 10: Use the report plus therapy-video display as the final user-facing output of the workflow.",
            ],
        )
    )

    replacements.append(
        (
            536,
            539,
            [
                "The SpeechWell dysarthria pipeline is trained and evaluated on feature tables derived primarily from the TORGO corpus, with optional positive-class augmentation from UASpeech in the combined-data workflow. The current repository therefore does not use UCLASS as the main training dataset for the deployed dysarthria model.",
                "The TORGO feature table `ml/training/torgo_audio_features_v4.csv` contains 17,612 rows. Its label distribution is 11,455 healthy/control rows and 6,157 dysarthria rows, and it is used by the v2 TORGO-only validation scripts stored in `ml/evaluation/validation_report_v2_group.json` and `ml/evaluation/validation_report_v2_rf_svc_ensemble.json`.",
                "The current preferred runtime comparison model is associated with the combined feature table `ml/training/combined_audio_features.csv`, which contains 160,890 rows. The saved comparison report shows a breakdown of 11,455 TORGO healthy rows, 6,145 TORGO dysarthria rows, and 143,290 UASPEECH dysarthria rows, with grouped train, validation, and test splits used during model selection.",
                "The relevant training artifacts are therefore `torgo_audio_features_v4.csv`, `combined_audio_features.csv`, `ml/models/dysarthria_best_comparison_model.pkl`, and the saved evaluation reports in `ml/evaluation/`. UASpeech is used only as dysarthria-positive augmentation in the combined workflow and does not replace the healthy/control speech contributed by TORGO.",
            ],
        )
    )

    replacements.append(
        (
            543,
            582,
            [
                "The performance analysis section must follow the saved evaluation artifacts in the repository rather than hand-written module-wise percentages. In the current codebase, rigorous offline evaluation is available mainly for the dysarthria model family, while stuttering and phonological scoring remain heuristic services and grammar quality depends on a provider-backed transcript correction stage plus local heuristics.",
                "7.1.1 Accuracy",
                "Accuracy measures the fraction of correctly classified samples among all evaluated samples.",
                "Accuracy = (TP + TN) / (TP + TN + FP + FN)",
                "where TP, TN, FP, and FN denote true positives, true negatives, false positives, and false negatives respectively.",
                "Accuracy is still useful as a top-level summary, but it should be interpreted together with precision, recall, and F1 because dysarthria screening involves an imbalanced binary classification problem.",
                "Table 7.1 compares four saved dysarthria evaluation snapshots: the legacy v1 logistic-regression path, the TORGO group-aware v2 model, the TORGO full-data RF+SVC validation result, and the current runtime comparison-model holdout result.",
                f"The legacy v1 validation report records an accuracy of {metric_percent(legacy['accuracy'])}%, showing the baseline performance of the older logistic-regression pipeline that used PCA and acoustic embeddings.",
                f"The group-aware v2 TORGO report improves accuracy to {metric_percent(group_v2['accuracy'])}%, indicating a major gain after moving to the raw-audio feature pipeline and a more realistic speaker-grouped evaluation setting.",
                f"The TORGO full-data RF+SVC validation report records {metric_percent(full_v2['accuracy'])}% accuracy. This number is strong but more optimistic because the validation script evaluates across the full available TORGO feature table rather than a clean grouped holdout.",
                f"The current runtime comparison-model holdout report records {metric_percent(comparison_holdout['accuracy'])}% accuracy. This is the most relevant deployment-oriented figure because the backend now prefers the saved comparison model artifact at runtime.",
                "Taken together, the accuracy trend shows that the repository progressed from a modest legacy baseline to stronger raw-audio classical ML pipelines, with the current runtime path maintaining high holdout accuracy while also adding symptom-gated safety logic at inference time.",
                "7.1.2 Precision",
                "Precision measures how many predicted dysarthria-positive cases are actually positive.",
                "Precision = TP / (TP + FP)",
                "Higher precision is especially valuable in this project because it reduces false alarms when the system is used as a screening or progress-monitoring assistant.",
                f"The legacy v1 report records a precision of {metric_percent(legacy['precision'])}%, which means the older logistic path produced substantially more false positives than the newer models.",
                f"The group-aware v2 TORGO model increases precision to {metric_percent(group_v2['precision'])}%, showing that the updated feature engineering and training workflow made positive predictions much more trustworthy.",
                f"The TORGO full-data RF+SVC validation report records {metric_percent(full_v2['precision'])}% precision, and the current runtime comparison-model holdout report reaches {metric_percent(comparison_holdout['precision'])}% precision.",
                "These very high precision values align with the backend design choice to keep dysarthria predictions conservative. The saved thresholds are already tuned for strong precision, and the runtime symptom-gating layer further protects against false positives when symptom evidence is weak.",
                "As a result, positive dysarthria predictions in the current SpeechWell pipeline are significantly more reliable than those produced by the older legacy path.",
                "7.1.3 F1-Score",
                "F1 score is the harmonic mean of precision and recall and provides a balanced view when both false positives and false negatives matter.",
                "F1 = 2 x (Precision x Recall) / (Precision + Recall)",
                "Because speech-disorder screening should both catch true cases and avoid unnecessary alarms, F1 score is one of the most informative single-number summaries for the dysarthria classifier.",
                f"The legacy v1 model records an F1 score of {metric_percent(legacy['f1_score'])}%, which reflects the weaker balance achieved by the older logistic-regression path.",
                f"The group-aware v2 TORGO model improves the F1 score to {metric_percent(group_v2['f1_score'])}%, confirming that the raw-audio feature pipeline generalizes more effectively across speakers.",
                f"The TORGO full-data RF+SVC validation result reaches {metric_percent(full_v2['f1_score'])}%, while the current runtime comparison-model holdout records {metric_percent(comparison_holdout['f1_score'])}%.",
                "Although the TORGO full-data validation gives the numerically highest F1 score, the runtime comparison-model holdout remains the more deployment-relevant evaluation snapshot because it comes from the same comparison report that selected the active saved artifact.",
                "The F1 progression therefore supports the conclusion that SpeechWell's modern dysarthria path is substantially stronger than the legacy baseline while preserving a healthy balance between missed detections and false alarms.",
                "7.1.4 Recall",
                "Recall measures how many actual dysarthria-positive cases are correctly detected by the model.",
                "Recall = TP / (TP + FN)",
                "Recall is particularly important in speech-support systems because missed disorder cases reduce the usefulness of screening and follow-up monitoring.",
                "Table 7.4 again compares the four saved dysarthria evaluation snapshots from the repository.",
                f"The legacy v1 pipeline records a recall of {metric_percent(legacy['recall'])}%, which means a sizable share of positive cases were missed by the older embedding-plus-logistic workflow.",
                f"The group-aware v2 TORGO model increases recall to {metric_percent(group_v2['recall'])}%, showing that the newer raw-audio feature set improves the system's ability to recover positive cases under grouped evaluation.",
                f"The TORGO full-data RF+SVC validation report records {metric_percent(full_v2['recall'])}% recall, and the current runtime comparison-model holdout report records {metric_percent(comparison_holdout['recall'])}% recall.",
                "The runtime comparison-model recall is slightly lower than the optimistic full-data TORGO validation recall, but it remains strong and is paired with extremely high precision. This tradeoff matches the conservative deployment goal of minimizing false alarms while still catching most positive cases.",
                "Overall, the saved evaluation artifacts show a clear improvement from the legacy v1 model to the currently deployed comparison-model path. They also highlight an important practical point: only the dysarthria classifier has formal offline evaluation reports in the repository, so performance claims for stuttering, grammar, and phonological modules should be framed as implemented service behavior rather than benchmarked classifier accuracy.",
            ],
        )
    )

    replacements.append((584, 598, accuracy_rows))
    replacements.append((599, 599, ["Fig. 7.1 Accuracy comparison chart generated from the saved dysarthria evaluation reports"]))
    replacements.append((601, 615, precision_rows))
    replacements.append((616, 616, ["Fig. 7.2 Precision comparison chart generated from the saved dysarthria evaluation reports"]))
    replacements.append((618, 632, f1_rows))
    replacements.append((633, 633, ["Fig. 7.3 F1 score comparison chart generated from the saved dysarthria evaluation reports"]))
    replacements.append((635, 649, recall_rows))
    replacements.append((650, 650, ["Fig. 7.4 Recall comparison chart generated from the saved dysarthria evaluation reports"]))

    replacements.append(
        (
            651,
            653,
            [
                "The corrected performance analysis shows that the strongest rigorously evaluated component in the repository is the dysarthria model family. The project has moved from a legacy logistic-regression baseline to raw-audio classical ML pipelines with much stronger accuracy, precision, recall, and F1 values.",
                "Among the saved evaluation artifacts, the current deployment-relevant report is `ml/evaluation/dysarthria_model_comparison_report.json`, where the best holdout model is HistGradientBoosting with 94.49% accuracy, 99.96% precision, 93.35% recall, and 96.54% F1 score at a threshold of 0.85.",
                "These metrics should be reported together with the runtime symptom-gating logic, because the live backend is intentionally stricter than the raw classifier output. This combination of strong holdout performance and conservative post-processing is the most accurate description of SpeechWell's current dysarthria pipeline, while the therapy side of the application can be presented separately as curated video guidance.",
            ],
        )
    )

    replacements.append(
        (
            656,
            657,
            [
                "SpeechWell is currently implemented as a full-stack speech analysis application rather than as a single-model research prototype. The deployed workflow starts with browser-based audio upload or recording, normalizes audio in the FastAPI backend, extracts transcript and timing information with Whisper, derives raw waveform features for dysarthria inference, and combines this with separate stuttering, grammar, and phonological services. Analysis results are stored in SQLite, rendered into PDF reports, surfaced through results and history pages, and followed by a Therapy Hub that presents curated YouTube practice videos. The preferred runtime dysarthria path uses the saved comparison-model artifact backed by HistGradientBoosting and symptom-gated decision logic, while legacy logistic-regression artifacts remain only as fallback compatibility paths.",
                "Future enhancement should therefore focus on areas that are genuinely unfinished in the codebase: broader and more balanced clinically validated datasets, formal offline evaluation for the stuttering and phonological services, clearer report-side explanation of symptom-gated predictions, stronger curation and organization of therapy-video content, and possible multilingual or clinically supervised expansion. These directions align with the actual repository and provide a realistic path for improving SpeechWell without overstating functionality that is not yet implemented.",
            ],
        )
    )

    replacements.append((700, 869, appendix_lines))

    return replacements


def main() -> None:
    if not INPUT_DOCX.exists():
        raise FileNotFoundError(f"Input DOCX not found: {INPUT_DOCX}")

    replacements = build_replacements()

    with zipfile.ZipFile(INPUT_DOCX, "r") as zin:
        document_xml = zin.read("word/document.xml")
        root = ET.fromstring(document_xml)
        paragraphs = iter_non_empty_paragraphs(root)

        for start, end, replacement_texts in replacements:
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
