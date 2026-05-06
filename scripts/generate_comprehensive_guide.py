"""
Generates a comprehensive PDF guide for the SpeechWell project.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from pathlib import Path
from datetime import datetime

# Output path
OUTPUT_PATH = Path(r"c:\Users\franc\OneDrive\Documents\Projects\SpeechWell\SpeechWell_Complete_Guide.pdf")

# Colors
PRIMARY_COLOR = HexColor("#4F46E5")  # Indigo
SECONDARY_COLOR = HexColor("#6366F1")  # Lighter indigo
DARK_COLOR = HexColor("#1F2937")  # Dark gray
LIGHT_BG = HexColor("#F3F4F6")  # Light gray


def create_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='CoverTitle',
        parent=styles['Heading1'],
        fontSize=36,
        textColor=PRIMARY_COLOR,
        alignment=TA_CENTER,
        spaceAfter=20,
    ))
    
    styles.add(ParagraphStyle(
        name='CoverSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=DARK_COLOR,
        alignment=TA_CENTER,
        spaceAfter=40,
    ))
    
    styles.add(ParagraphStyle(
        name='ChapterTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=PRIMARY_COLOR,
        spaceBefore=20,
        spaceAfter=20,
        borderPadding=(0, 0, 10, 0),
    ))
    
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=SECONDARY_COLOR,
        spaceBefore=15,
        spaceAfter=10,
    ))
    
    styles.add(ParagraphStyle(
        name='SubSection',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=DARK_COLOR,
        spaceBefore=10,
        spaceAfter=6,
    ))
    
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK_COLOR,
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14,
    ))
    
    styles.add(ParagraphStyle(
        name='CodeBlock',
        parent=styles['Code'],
        fontSize=9,
        backColor=LIGHT_BG,
        leftIndent=20,
        rightIndent=20,
        spaceBefore=6,
        spaceAfter=6,
    ))
    
    styles.add(ParagraphStyle(
        name='Equation',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Courier',
        backColor=LIGHT_BG,
        leftIndent=30,
        rightIndent=30,
        spaceBefore=8,
        spaceAfter=8,
    ))
    
    styles.add(ParagraphStyle(
        name='TableOfContentsItem',
        parent=styles['Normal'],
        fontSize=11,
        textColor=DARK_COLOR,
        spaceAfter=6,
        leftIndent=20,
    ))
    
    return styles


def build_document():
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )
    
    styles = create_styles()
    story = []
    
    # ========== COVER PAGE ==========
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("SpeechWell", styles['CoverTitle']))
    story.append(Paragraph("Comprehensive Project Guide", styles['CoverSubtitle']))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(
        "A Complete Reference for Understanding the Speech Analysis<br/>"
        "and Training Platform from A to Z",
        styles['CoverSubtitle']
    ))
    story.append(Spacer(1, 1*inch))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y')}",
        styles['CoverSubtitle']
    ))
    story.append(PageBreak())
    
    # ========== TABLE OF CONTENTS ==========
    story.append(Paragraph("Table of Contents", styles['ChapterTitle']))
    toc_items = [
        "1. Project Overview",
        "2. System Architecture",
        "3. Technology Stack",
        "4. Installation & Setup",
        "5. Backend API Reference",
        "6. Authentication System",
        "7. Speech Analysis Pipeline",
        "8. Machine Learning Models",
        "9. Scoring Algorithms & Equations",
        "10. Guided Speech Training Module",
        "11. Training Exercises & Evaluation",
        "12. Database Schema",
        "13. Frontend Structure",
        "14. API Endpoints Reference",
        "15. Configuration & Environment",
        "16. File Structure Reference",
        "17. Troubleshooting Guide",
        "18. Future Improvements",
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles['TableOfContentsItem']))
    story.append(PageBreak())
    
    # ========== CHAPTER 1: PROJECT OVERVIEW ==========
    story.append(Paragraph("1. Project Overview", styles['ChapterTitle']))
    
    story.append(Paragraph("What is SpeechWell?", styles['SectionTitle']))
    story.append(Paragraph(
        "SpeechWell is a full-stack speech improvement platform that combines React frontend with "
        "FastAPI backend and machine learning models for comprehensive speech analysis. The platform "
        "serves two primary purposes:",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("<b>1. Speech Analysis:</b> Upload or record speech samples to receive detailed "
        "analysis including dysarthria detection, stuttering assessment, grammar evaluation, and "
        "phonological error detection.", styles['CustomBody']))
    
    story.append(Paragraph("<b>2. Guided Speech Training:</b> Structured practice sessions for breath control, "
        "articulation, fluency, and grammar improvement with real-time feedback.", styles['CustomBody']))
    
    story.append(Paragraph("Core Features", styles['SectionTitle']))
    features = [
        "User authentication with JWT tokens",
        "Audio file upload and real-time recording",
        "ML-powered speech analysis (Whisper + Wav2Vec2)",
        "Dysarthria probability detection",
        "Stuttering analysis (repetitions, prolongations, blocks)",
        "Grammar correction using AI providers (OpenAI, Gemini, Ollama)",
        "Phonological error detection",
        "PDF report generation",
        "Interactive training exercises",
        "Progress tracking and dashboard analytics",
        "Multiple theme support (Lavender, Ocean, Forest, Dark)",
        "AI Chat assistant for speech improvement guidance",
    ]
    for feature in features:
        story.append(Paragraph(f"• {feature}", styles['CustomBody']))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 2: SYSTEM ARCHITECTURE ==========
    story.append(Paragraph("2. System Architecture", styles['ChapterTitle']))
    
    story.append(Paragraph("High-Level Architecture", styles['SectionTitle']))
    story.append(Paragraph(
        "SpeechWell follows a modern three-tier architecture with clear separation of concerns:",
        styles['CustomBody']
    ))
    
    arch_data = [
        ["Layer", "Technology", "Purpose"],
        ["Frontend", "React + Vite + TypeScript", "User interface, routing, state management"],
        ["Backend", "FastAPI + Python", "REST API, auth, business logic orchestration"],
        ["ML Layer", "Whisper + Wav2Vec2 + scikit-learn", "Speech transcription, acoustic analysis, classification"],
        ["Database", "SQLite", "User data, analysis records, training progress"],
        ["Storage", "Local filesystem", "Audio files, PDF reports"],
    ]
    
    arch_table = Table(arch_data, colWidths=[1.2*inch, 2.2*inch, 3*inch])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph("Data Flow", styles['SectionTitle']))
    story.append(Paragraph(
        "<b>Analysis Flow:</b><br/>"
        "1. User uploads audio file via frontend<br/>"
        "2. Backend validates and normalizes audio (FFmpeg → mono 16kHz WAV)<br/>"
        "3. Whisper extracts transcript and timing features<br/>"
        "4. Wav2Vec2 extracts acoustic embeddings<br/>"
        "5. ML models compute dysarthria/stuttering/grammar/phonology scores<br/>"
        "6. Results stored in database, PDF report generated<br/>"
        "7. Frontend displays results with visualizations",
        styles['CustomBody']
    ))
    
    story.append(Paragraph(
        "<b>Training Flow:</b><br/>"
        "1. User selects training module and exercise<br/>"
        "2. Backend creates training session<br/>"
        "3. User completes exercise (audio or text input)<br/>"
        "4. Backend evaluates response using Whisper + scoring logic<br/>"
        "5. Progress aggregated per user per module<br/>"
        "6. Dashboard displays training progress",
        styles['CustomBody']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 3: TECHNOLOGY STACK ==========
    story.append(Paragraph("3. Technology Stack", styles['ChapterTitle']))
    
    story.append(Paragraph("Backend Technologies", styles['SectionTitle']))
    backend_tech = [
        ["Technology", "Version", "Purpose"],
        ["Python", "3.9+", "Core backend language"],
        ["FastAPI", "Latest", "REST API framework"],
        ["SQLAlchemy", "Latest", "ORM for database operations"],
        ["SQLite", "Built-in", "Database storage"],
        ["Uvicorn", "Latest", "ASGI server"],
        ["PyJWT", "Latest", "JWT token handling"],
        ["bcrypt", "Latest", "Password hashing"],
        ["ReportLab", "Latest", "PDF report generation"],
    ]
    
    backend_table = Table(backend_tech, colWidths=[1.5*inch, 1*inch, 3.5*inch])
    backend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(backend_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Machine Learning Stack", styles['SectionTitle']))
    ml_tech = [
        ["Technology", "Model", "Purpose"],
        ["OpenAI Whisper", "small.en / base.en", "Speech-to-text transcription"],
        ["Wav2Vec2", "facebook/wav2vec2-base", "Acoustic embedding extraction"],
        ["scikit-learn", "HistGradientBoosting / RF+SVC", "Dysarthria classification"],
        ["librosa", "N/A", "Audio processing and feature extraction"],
        ["NumPy/Pandas", "N/A", "Numerical computations"],
        ["joblib", "N/A", "Model serialization"],
    ]
    
    ml_table = Table(ml_tech, colWidths=[1.5*inch, 1.5*inch, 3*inch])
    ml_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(ml_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Frontend Technologies", styles['SectionTitle']))
    frontend_tech = [
        ["Technology", "Purpose"],
        ["React 18+", "UI component library"],
        ["Vite", "Build tool and dev server"],
        ["TypeScript", "Type-safe JavaScript"],
        ["React Router", "Client-side routing"],
        ["CSS Variables", "Theme system implementation"],
    ]
    
    frontend_table = Table(frontend_tech, colWidths=[2*inch, 4*inch])
    frontend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(frontend_table)
    
    story.append(PageBreak())
    
    # ========== CHAPTER 4: INSTALLATION & SETUP ==========
    story.append(Paragraph("4. Installation & Setup", styles['ChapterTitle']))
    
    story.append(Paragraph("Prerequisites", styles['SectionTitle']))
    prereqs = [
        "Python 3.9 or higher",
        "Node.js 18 or higher (includes npm)",
        "FFmpeg (must be on system PATH for audio normalization)",
        "Git (optional, for version control)",
    ]
    for prereq in prereqs:
        story.append(Paragraph(f"• {prereq}", styles['CustomBody']))
    
    story.append(Paragraph("Backend Setup", styles['SectionTitle']))
    
    story.append(Paragraph("Step 1: Create virtual environment", styles['SubSection']))
    story.append(Paragraph("python -m venv venv", styles['CodeBlock']))
    story.append(Paragraph(".\\venv\\Scripts\\Activate.ps1  # Windows PowerShell", styles['CodeBlock']))
    
    story.append(Paragraph("Step 2: Install dependencies", styles['SubSection']))
    story.append(Paragraph("pip install -r requirements.txt", styles['CodeBlock']))
    
    story.append(Paragraph("Step 3: Configure environment", styles['SubSection']))
    story.append(Paragraph("Copy-Item .env.example .env", styles['CodeBlock']))
    story.append(Paragraph(
        "Edit .env file to configure chat providers (optional):<br/>"
        "• CHAT_PROVIDER=auto<br/>"
        "• OLLAMA_BASE_URL=http://127.0.0.1:11434<br/>"
        "• OLLAMA_MODEL=qwen2.5:30b<br/>"
        "• OPENAI_API_KEY=... (optional)<br/>"
        "• GEMINI_API_KEY=... (optional)",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Step 4: Ensure ML models exist", styles['SubSection']))
    story.append(Paragraph(
        "Primary model: ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl<br/>"
        "If missing, train with:<br/>"
        "python ml/training/train_dysarthria_rf_svc_ensemble.py --group-aware",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Step 5: Start backend server", styles['SubSection']))
    story.append(Paragraph("uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000", styles['CodeBlock']))
    
    story.append(Paragraph("Frontend Setup", styles['SectionTitle']))
    
    story.append(Paragraph("Step 1: Install dependencies", styles['SubSection']))
    story.append(Paragraph("cd speechwell-frontend && npm install", styles['CodeBlock']))
    
    story.append(Paragraph("Step 2: Start development server", styles['SubSection']))
    story.append(Paragraph("npm run dev", styles['CodeBlock']))
    
    story.append(Paragraph("Quick Start (Windows)", styles['SectionTitle']))
    story.append(Paragraph(
        "Use the provided quickstart script: .\\quickstart.ps1<br/>"
        "Or the batch file: start_speechwell.bat",
        styles['CustomBody']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 5: BACKEND API REFERENCE ==========
    story.append(Paragraph("5. Backend API Reference", styles['ChapterTitle']))
    
    story.append(Paragraph("API Base URL", styles['SectionTitle']))
    story.append(Paragraph("http://localhost:8000/api", styles['CodeBlock']))
    
    story.append(Paragraph("Main Entry Point", styles['SectionTitle']))
    story.append(Paragraph(
        "File: backend/app/main.py<br/><br/>"
        "The FastAPI application is configured with:<br/>"
        "• CORS middleware for cross-origin requests<br/>"
        "• Automatic database table creation<br/>"
        "• Schema migration for SQLite compatibility<br/>"
        "• Route handlers for all API endpoints",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Request Flow", styles['SectionTitle']))
    story.append(Paragraph(
        "1. Request arrives at FastAPI endpoint<br/>"
        "2. JWT token validated (for protected routes)<br/>"
        "3. Request body/params validated with Pydantic schemas<br/>"
        "4. Business logic executed via service layer<br/>"
        "5. Database operations via SQLAlchemy session<br/>"
        "6. Response serialized and returned",
        styles['CustomBody']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 6: AUTHENTICATION SYSTEM ==========
    story.append(Paragraph("6. Authentication System", styles['ChapterTitle']))
    
    story.append(Paragraph("Overview", styles['SectionTitle']))
    story.append(Paragraph(
        "SpeechWell uses JWT (JSON Web Token) authentication for securing API endpoints. "
        "The same authenticated user identity is used for both speech analysis and training features.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Key Files", styles['SectionTitle']))
    story.append(Paragraph(
        "• backend/app/services/auth_service.py - Core auth logic<br/>"
        "• backend/app/database/models.py - User model<br/>"
        "• speechwell-frontend/src/api/api.ts - Frontend auth calls",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Authentication Flow", styles['SectionTitle']))
    story.append(Paragraph(
        "1. User registers or logs in with email/password<br/>"
        "2. Backend validates credentials, returns JWT bearer token<br/>"
        "3. Frontend stores token in localStorage<br/>"
        "4. All protected requests include: Authorization: Bearer &lt;token&gt;<br/>"
        "5. Backend validates token via get_current_user() dependency",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Password Security", styles['SectionTitle']))
    story.append(Paragraph(
        "• Passwords hashed using bcrypt<br/>"
        "• Plain text passwords never stored<br/>"
        "• JWT tokens expire after configured duration",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Auth Endpoints", styles['SectionTitle']))
    auth_endpoints = [
        ["Endpoint", "Method", "Purpose"],
        ["/api/auth/register", "POST", "Create new user account"],
        ["/api/auth/login", "POST", "Authenticate and get JWT token"],
        ["/api/profile", "GET", "Get current user profile"],
        ["/api/profile", "PUT", "Update user profile"],
    ]
    
    auth_table = Table(auth_endpoints, colWidths=[2*inch, 1*inch, 3*inch])
    auth_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(auth_table)
    
    story.append(PageBreak())
    
    # ========== CHAPTER 7: SPEECH ANALYSIS PIPELINE ==========
    story.append(Paragraph("7. Speech Analysis Pipeline", styles['ChapterTitle']))
    
    story.append(Paragraph("Pipeline Overview", styles['SectionTitle']))
    story.append(Paragraph(
        "The speech analysis pipeline is the core ML workflow that processes uploaded audio "
        "and generates comprehensive speech metrics.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Main Files", styles['SectionTitle']))
    story.append(Paragraph(
        "• ml/services/speech_analysis_service.py - Main orchestrator<br/>"
        "• ml/feature_extraction/extract_whisper.py - Transcription<br/>"
        "• ml/feature_extraction/extract_acoustic.py - Embeddings<br/>"
        "• backend/app/services/dysarthria_inference_service.py<br/>"
        "• backend/app/services/stuttering_service.py<br/>"
        "• backend/app/services/grammar_service.py<br/>"
        "• backend/app/services/phonological_service.py",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Pipeline Stages", styles['SectionTitle']))
    
    story.append(Paragraph("Stage 1: Audio Normalization", styles['SubSection']))
    story.append(Paragraph(
        "FFmpeg converts input to standardized format:<br/>"
        "ffmpeg -i input -ac 1 -ar 16000 output.wav<br/><br/>"
        "• Converts to mono channel<br/>"
        "• Resamples to 16kHz<br/>"
        "• Reduces model input variation",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Stage 2: Transcript Extraction (Whisper)", styles['SubSection']))
    story.append(Paragraph(
        "Model: small.en or base.en (configurable via WHISPER_MODEL)<br/><br/>"
        "Outputs:<br/>"
        "• Full transcript text<br/>"
        "• Segment timestamps (start, end, text)<br/>"
        "• Word count<br/>"
        "• Speaking rate (words per second)<br/>"
        "• Pause metrics (average, max, durations)",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Stage 3: Acoustic Embedding (Wav2Vec2)", styles['SubSection']))
    story.append(Paragraph(
        "Model: facebook/wav2vec2-base<br/><br/>"
        "Process:<br/>"
        "1. Load waveform<br/>"
        "2. Convert to mono if needed<br/>"
        "3. Resample to 16kHz<br/>"
        "4. Run Wav2Vec2 inference<br/>"
        "5. Mean-pool hidden states<br/><br/>"
        "Output: 768-dimensional acoustic embedding vector",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Stage 4: Analysis Modules", styles['SubSection']))
    story.append(Paragraph(
        "Each module computes specific speech characteristics:<br/>"
        "• Dysarthria: ML classification using features + embeddings<br/>"
        "• Stuttering: Rule-based detection of repetitions, prolongations, blocks<br/>"
        "• Grammar: AI-powered correction and error estimation<br/>"
        "• Phonological: Pattern-based articulation assessment",
        styles['CustomBody']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 8: MACHINE LEARNING MODELS ==========
    story.append(Paragraph("8. Machine Learning Models", styles['ChapterTitle']))
    
    story.append(Paragraph("Dysarthria Detection Model", styles['SectionTitle']))
    story.append(Paragraph(
        "The dysarthria detection system uses a two-stage approach:",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Primary Model (V2): HistGradientBoosting / Ensemble", styles['SubSection']))
    story.append(Paragraph(
        "The project supports multiple model architectures for dysarthria detection:<br/><br/>"
        "<b>HistGradientBoostingClassifier (Current):</b><br/>"
        "• Fast, native handling of missing values<br/>"
        "• learning_rate=0.05, max_depth=6, max_iter=250<br/>"
        "• File: ml/models/dysarthria_best_comparison_model.pkl<br/><br/>"
        "<b>RF/SVC Ensemble (Alternative):</b><br/>"
        "• Random Forest + RBF SVM soft-voting<br/>"
        "• File: ml/models/dysarthria_model_v2_rf_svc_ensemble.pkl<br/><br/>"
        "<b>Features used by all models:</b><br/>"
        "• Raw audio features (RMS, ZCR, spectral flatness, silence ratio)<br/>"
        "• MFCC coefficients and deltas (mean, std)<br/>"
        "• Chroma features<br/>"
        "• Spectral contrast<br/><br/>"
        "Training comparison script:<br/>"
        "python ml/training/train_dysarthria_model_comparison.py --group-aware",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Symptom Gating System", styles['SubSection']))
    story.append(Paragraph(
        "To prevent false positives, the model output is gated by acoustic symptom evidence:<br/><br/>"
        "Symptom score computed from:<br/>"
        "• Low RMS energy (&lt;0.01)<br/>"
        "• High silence ratio (&gt;0.45)<br/>"
        "• Elevated spectral flatness (&gt;0.22)<br/>"
        "• Abnormal zero-crossing rate<br/>"
        "• High MFCC variance<br/><br/>"
        "Final classification requires both high model probability AND symptom evidence.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Legacy Model (V1)", styles['SubSection']))
    story.append(Paragraph(
        "Fallback when V2 unavailable:<br/>"
        "• Fluency features + PCA-reduced acoustic embeddings<br/>"
        "• Logistic regression classifier",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Model Comparison Framework", styles['SectionTitle']))
    story.append(Paragraph(
        "The project includes a model comparison script that evaluates multiple architectures:<br/><br/>"
        "• Calibrated Logistic Regression<br/>"
        "• RBF SVM<br/>"
        "• Random Forest<br/>"
        "• RF + SVM Ensemble<br/>"
        "• <b>HistGradientBoostingClassifier</b> (typically best performer)<br/><br/>"
        "Run comparison: python ml/training/train_dysarthria_model_comparison.py",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Model Artifacts", styles['SectionTitle']))
    model_artifacts = [
        ["File", "Purpose"],
        ["dysarthria_best_comparison_model.pkl", "Best model from comparison (typically HistGradientBoosting)"],
        ["dysarthria_model_v2_rf_svc_ensemble.pkl", "RF/SVC ensemble model + threshold + feature columns"],
        ["dysarthria_model_v1.pkl", "Legacy logistic regression model"],
        ["dysarthria_pca_v1.pkl", "PCA transform for acoustic embeddings"],
        ["dysarthria_scaler_v1.pkl", "Feature scaler for embeddings"],
    ]
    
    artifacts_table = Table(model_artifacts, colWidths=[3*inch, 3*inch])
    artifacts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(artifacts_table)
    
    story.append(PageBreak())
    
    # ========== CHAPTER 9: SCORING ALGORITHMS ==========
    story.append(Paragraph("9. Scoring Algorithms & Equations", styles['ChapterTitle']))
    
    story.append(Paragraph("Speaking Rate Calculation", styles['SectionTitle']))
    story.append(Paragraph(
        "speaking_rate_wps = W / T<br/><br/>"
        "Where:<br/>"
        "• W = total number of transcript words<br/>"
        "• T = speaking duration in seconds",
        styles['Equation']
    ))
    
    story.append(Paragraph("Pause Metrics", styles['SectionTitle']))
    story.append(Paragraph(
        "pause_i = start_i - end_(i-1) for each positive pause<br/><br/>"
        "average_pause_sec = mean(pause_i)<br/>"
        "max_pause_sec = max(pause_i)",
        styles['Equation']
    ))
    
    story.append(Paragraph("Stuttering Probability", styles['SectionTitle']))
    story.append(Paragraph(
        "Components detected:<br/>"
        "• Repetitions: consecutive repeated words<br/>"
        "• Prolongations: vowel stretching, slow segments<br/>"
        "• Blocks: long inter-segment gaps (≥0.9 sec)",
        styles['CustomBody']
    ))
    story.append(Paragraph(
        "stuttering_probability = (\n"
        "    repetition_score × 0.28 +\n"
        "    prolongation_score × 0.24 +\n"
        "    block_score × 0.26 +\n"
        "    severe_block_bonus × 0.08 +\n"
        "    pause_variability × 0.09 +\n"
        "    segment_rate_variability × 0.03 +\n"
        "    speaking_rate_penalty × 0.02\n"
        ")",
        styles['Equation']
    ))
    
    story.append(Paragraph("Grammar Quality Score", styles['SectionTitle']))
    story.append(Paragraph(
        "structural_error_probability = min(\n"
        "    fragment_ratio × 0.28 +\n"
        "    verb_gap_ratio × 0.16 +\n"
        "    repetition_ratio × 0.15 +\n"
        "    filler_ratio × 0.10 +\n"
        "    odd_token_ratio × 0.12 +\n"
        "    boundary_issue_ratio × 0.07 +\n"
        "    telegraphic_ratio × 0.07 +\n"
        "    subject_case_ratio × 0.05,\n"
        "    1.0\n"
        ")<br/><br/>"
        "grammar_quality_score = 1.0 - grammar_error_probability",
        styles['Equation']
    ))
    
    story.append(Paragraph("Overall Analysis Score", styles['SectionTitle']))
    story.append(Paragraph(
        "pronunciation = (1 - dysarthria_probability) × 100<br/>"
        "fluency = (1 - stuttering_probability) × 100<br/>"
        "clarity = grammar_quality_score × 100<br/><br/>"
        "weighted_average = 0.35 × pronunciation + 0.25 × fluency + 0.40 × clarity<br/>"
        "weakest_skill = min(pronunciation, fluency, clarity)<br/><br/>"
        "overall_score = round(0.7 × weighted_average + 0.3 × weakest_skill)",
        styles['Equation']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 10: GUIDED SPEECH TRAINING ==========
    story.append(Paragraph("10. Guided Speech Training Module", styles['ChapterTitle']))
    
    story.append(Paragraph("Overview", styles['SectionTitle']))
    story.append(Paragraph(
        "The training module provides structured speech practice exercises that complement "
        "the analysis features. Users can practice specific skills with real-time feedback.",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Training Modules", styles['SectionTitle']))
    modules = [
        ["Module", "Focus", "Input Type"],
        ["breath_voice", "Breath support, steady voice, smooth onset", "Microphone"],
        ["articulation", "Consonant precision, word clarity", "Microphone"],
        ["fluency", "Pacing, pauses, reduced rushing", "Microphone"],
        ["grammar", "Sentence completion, correction practice", "Text"],
    ]
    
    modules_table = Table(modules, colWidths=[1.5*inch, 2.5*inch, 1.5*inch])
    modules_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(modules_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Breath & Voice Exercises", styles['SectionTitle']))
    story.append(Paragraph(
        "• vowel_hold: Sustain a vowel sound steadily<br/>"
        "• count_on_breath: Count numbers on one breath<br/>"
        "• soft_loud_repeat: Practice volume control",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Articulation Exercises", styles['SectionTitle']))
    story.append(Paragraph(
        "• minimal_pairs: Distinguish similar sounds<br/>"
        "• tongue_tip_drill: Practice tongue-tip consonants<br/>"
        "• sentence_repeat_clear: Repeat sentences clearly",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Fluency Exercises", styles['SectionTitle']))
    story.append(Paragraph(
        "• slow_read: Read at reduced pace<br/>"
        "• easy_onset_phrase: Practice gentle voice starts<br/>"
        "• pause_and_continue: Practice controlled pausing",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Grammar Exercises", styles['SectionTitle']))
    story.append(Paragraph(
        "• complete_sentence: Fill in missing words<br/>"
        "• fix_and_say: Correct grammatical errors<br/>"
        "• daily_topic: Open response practice",
        styles['CustomBody']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 11: TRAINING EVALUATION ==========
    story.append(Paragraph("11. Training Exercises & Evaluation", styles['ChapterTitle']))
    
    story.append(Paragraph("Session Lifecycle", styles['SectionTitle']))
    story.append(Paragraph(
        "<b>Start:</b><br/>"
        "1. Frontend loads module list from GET /api/training/modules<br/>"
        "2. User selects exercise<br/>"
        "3. POST /api/training/session/start creates session row<br/><br/>"
        "<b>Evaluate:</b><br/>"
        "1. User completes exercise (text or audio)<br/>"
        "2. POST /api/training/session/evaluate processes response<br/>"
        "3. Backend computes accuracy, fluency, confidence scores<br/>"
        "4. Progress aggregated for user/module",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Accuracy Calculation", styles['SectionTitle']))
    story.append(Paragraph(
        "For expected-answer drills:<br/>"
        "accuracy = matched_words / total_expected_words<br/><br/>"
        "For open-response drills:<br/>"
        "accuracy = min(word_count / 6, 1.0)",
        styles['Equation']
    ))
    
    story.append(Paragraph("Fluency Calculation", styles['SectionTitle']))
    story.append(Paragraph(
        "For audio exercises:<br/>"
        "fluency = 1.0 - (long_pause_count × 0.15) - (repeated_word_count × 0.1)<br/><br/>"
        "For text exercises:<br/>"
        "fluency = 1.0 - (repeated_word_count × 0.1)",
        styles['Equation']
    ))
    
    story.append(Paragraph("Confidence Score", styles['SectionTitle']))
    story.append(Paragraph(
        "confidence = min(1.0,\n"
        "    accuracy_ratio × 0.5 +\n"
        "    fluency_ratio × 0.3 +\n"
        "    completion_bonus × 0.2\n"
        ")<br/><br/>"
        "For grammar exercises, blended with grammar quality:<br/>"
        "confidence = min(1.0, confidence × 0.8 + grammar_boost × 0.2)",
        styles['Equation']
    ))
    
    story.append(Paragraph("Progress Aggregation", styles['SectionTitle']))
    story.append(Paragraph(
        "Per-user per-module aggregates:<br/>"
        "• sessions_completed = count(completed sessions)<br/>"
        "• avg_accuracy = mean(session.accuracy_score)<br/>"
        "• avg_fluency = mean(session.fluency_score)<br/>"
        "• best_score = max(session.confidence_score)",
        styles['CustomBody']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 12: DATABASE SCHEMA ==========
    story.append(Paragraph("12. Database Schema", styles['ChapterTitle']))
    
    story.append(Paragraph("Database: SQLite (speechwell.db)", styles['SectionTitle']))
    
    story.append(Paragraph("Users Table", styles['SectionTitle']))
    users_schema = [
        ["Column", "Type", "Description"],
        ["id", "INTEGER PK", "Auto-increment primary key"],
        ["email", "VARCHAR UNIQUE", "User email address"],
        ["password_hash", "VARCHAR", "bcrypt hashed password"],
        ["full_name", "VARCHAR", "Display name"],
        ["age", "INTEGER", "User age"],
        ["gender", "VARCHAR", "User gender"],
        ["location", "VARCHAR", "User location"],
        ["occupation", "VARCHAR", "User occupation"],
        ["primary_goal", "VARCHAR", "Speech improvement goal"],
        ["bio", "TEXT", "User biography"],
        ["created_at", "DATETIME", "Account creation time"],
        ["updated_at", "DATETIME", "Last update time"],
    ]
    
    users_table = Table(users_schema, colWidths=[1.5*inch, 1.5*inch, 3*inch])
    users_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(users_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Analyses Table", styles['SectionTitle']))
    analyses_schema = [
        ["Column", "Type", "Description"],
        ["id", "INTEGER PK", "Auto-increment primary key"],
        ["user_id", "INTEGER FK", "Reference to users.id"],
        ["audio_id", "VARCHAR UNIQUE", "UUID for the analysis"],
        ["filename", "VARCHAR", "Original filename"],
        ["transcript", "TEXT", "Whisper transcript"],
        ["dysarthria_probability", "FLOAT", "Dysarthria risk (0-1)"],
        ["dysarthria_label", "VARCHAR", "healthy/dysarthria"],
        ["stuttering_probability", "FLOAT", "Stuttering risk (0-1)"],
        ["stuttering_repetitions", "INTEGER", "Repetition count"],
        ["stuttering_prolongations", "INTEGER", "Prolongation count"],
        ["stuttering_blocks", "INTEGER", "Block count"],
        ["grammar_score", "FLOAT", "Grammar quality (0-1)"],
        ["grammar_error_count", "INTEGER", "Error count estimate"],
        ["corrected_text", "TEXT", "AI-corrected transcript"],
        ["phonological_score", "FLOAT", "Phonology score"],
        ["speaking_rate_wps", "FLOAT", "Words per second"],
        ["average_pause_sec", "FLOAT", "Average pause duration"],
        ["max_pause_sec", "FLOAT", "Maximum pause duration"],
        ["total_duration_sec", "FLOAT", "Total audio duration"],
        ["pdf_path", "VARCHAR", "Path to PDF report"],
        ["status", "VARCHAR", "processing/completed/failed"],
        ["created_at", "DATETIME", "Analysis timestamp"],
    ]
    
    analyses_table = Table(analyses_schema, colWidths=[1.8*inch, 1.2*inch, 3*inch])
    analyses_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(analyses_table)
    
    story.append(PageBreak())
    
    story.append(Paragraph("Training Sessions Table", styles['SectionTitle']))
    training_schema = [
        ["Column", "Type", "Description"],
        ["id", "INTEGER PK", "Auto-increment primary key"],
        ["user_id", "INTEGER FK", "Reference to users.id"],
        ["module_key", "VARCHAR", "Training module identifier"],
        ["exercise_key", "VARCHAR", "Exercise identifier"],
        ["prompt_text", "TEXT", "Exercise prompt shown to user"],
        ["expected_text", "TEXT", "Expected response (if applicable)"],
        ["transcript", "TEXT", "User's response transcript"],
        ["input_mode", "VARCHAR", "mic/text"],
        ["accuracy_score", "FLOAT", "Accuracy (0-1)"],
        ["fluency_score", "FLOAT", "Fluency (0-1)"],
        ["confidence_score", "FLOAT", "Overall confidence (0-1)"],
        ["long_pause_count", "INTEGER", "Long pauses detected"],
        ["repeated_word_count", "INTEGER", "Repeated words detected"],
        ["duration_sec", "FLOAT", "Response duration"],
        ["feedback_summary", "TEXT", "Generated feedback"],
        ["corrected_text", "TEXT", "Grammar-corrected version"],
        ["status", "VARCHAR", "started/completed/failed"],
        ["created_at", "DATETIME", "Session start time"],
    ]
    
    training_table = Table(training_schema, colWidths=[1.8*inch, 1.2*inch, 3*inch])
    training_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(training_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Training Progress Table", styles['SectionTitle']))
    progress_schema = [
        ["Column", "Type", "Description"],
        ["id", "INTEGER PK", "Auto-increment primary key"],
        ["user_id", "INTEGER FK", "Reference to users.id"],
        ["module_key", "VARCHAR", "Training module identifier"],
        ["sessions_completed", "INTEGER", "Total completed sessions"],
        ["avg_accuracy", "FLOAT", "Average accuracy across sessions"],
        ["avg_fluency", "FLOAT", "Average fluency across sessions"],
        ["best_score", "FLOAT", "Best confidence score achieved"],
        ["last_practiced_at", "DATETIME", "Last practice timestamp"],
    ]
    
    progress_table = Table(progress_schema, colWidths=[1.8*inch, 1.2*inch, 3*inch])
    progress_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(progress_table)
    
    story.append(PageBreak())
    
    # ========== CHAPTER 13: FRONTEND STRUCTURE ==========
    story.append(Paragraph("13. Frontend Structure", styles['ChapterTitle']))
    
    story.append(Paragraph("Directory Layout", styles['SectionTitle']))
    story.append(Paragraph(
        "speechwell-frontend/<br/>"
        "├── src/<br/>"
        "│   ├── api/          # API client functions<br/>"
        "│   ├── assets/       # Static assets<br/>"
        "│   ├── components/   # Reusable UI components<br/>"
        "│   ├── data/         # Static data (videos, etc.)<br/>"
        "│   ├── pages/        # Route page components<br/>"
        "│   ├── styles/       # CSS modules<br/>"
        "│   ├── utils/        # Utility functions<br/>"
        "│   ├── App.tsx       # Root component + routes<br/>"
        "│   └── main.tsx      # Entry point<br/>"
        "├── public/           # Static public files<br/>"
        "├── package.json      # Dependencies<br/>"
        "└── vite.config.ts    # Vite configuration",
        styles['CodeBlock']
    ))
    
    story.append(Paragraph("Page Components", styles['SectionTitle']))
    pages = [
        ["Component", "Route", "Purpose"],
        ["Landing.tsx", "/", "Home page with intro"],
        ["Login.tsx", "/login", "User login form"],
        ["Register.tsx", "/register", "User registration"],
        ["Dashboard.tsx", "/dashboard", "Analytics overview"],
        ["Upload.tsx", "/upload", "Audio upload/record"],
        ["Results.tsx", "/results", "Analysis results display"],
        ["History.tsx", "/history", "Past analyses list"],
        ["TherapyHub.tsx", "/therapy-hub", "Training module selection"],
        ["TrainingModule.tsx", "/therapy-hub/:moduleKey", "Exercise selection"],
        ["TrainingExercise.tsx", "/therapy-hub/:moduleKey/:exerciseKey", "Exercise execution"],
        ["TrainingResult.tsx", "/therapy-hub/session/:sessionId/result", "Training results"],
        ["AIChat.tsx", "/ai-chat", "AI chat assistant"],
        ["Profile.tsx", "/profile", "User profile settings"],
    ]
    
    pages_table = Table(pages, colWidths=[1.5*inch, 2.5*inch, 2*inch])
    pages_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(pages_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Theme System", styles['SectionTitle']))
    story.append(Paragraph(
        "Themes are implemented via CSS variables and data-theme attribute:<br/><br/>"
        "Available themes: Lavender, Ocean, Forest, Dark<br/><br/>"
        "Theme file: speechwell-frontend/src/utils/theme.ts<br/>"
        "CSS variables: speechwell-frontend/src/index.css<br/><br/>"
        "Theme can be changed from navbar or profile settings.",
        styles['CustomBody']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 14: API ENDPOINTS ==========
    story.append(Paragraph("14. API Endpoints Reference", styles['ChapterTitle']))
    
    story.append(Paragraph("Authentication Endpoints", styles['SectionTitle']))
    auth_api = [
        ["Method", "Endpoint", "Description"],
        ["POST", "/api/auth/register", "Register new user"],
        ["POST", "/api/auth/login", "Login and get JWT token"],
        ["GET", "/api/profile", "Get current user profile"],
        ["PUT", "/api/profile", "Update user profile"],
    ]
    auth_api_table = Table(auth_api, colWidths=[1*inch, 2.5*inch, 2.5*inch])
    auth_api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(auth_api_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Analysis Endpoints", styles['SectionTitle']))
    analysis_api = [
        ["Method", "Endpoint", "Description"],
        ["POST", "/api/analyze", "Upload and analyze audio file"],
        ["GET", "/api/analyze/{audio_id}", "Get analysis by ID"],
        ["GET", "/api/analyses", "Get user's analysis history"],
        ["GET", "/api/reports/{audio_id}", "Download PDF report"],
    ]
    analysis_api_table = Table(analysis_api, colWidths=[1*inch, 2.5*inch, 2.5*inch])
    analysis_api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(analysis_api_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Training Endpoints", styles['SectionTitle']))
    training_api = [
        ["Method", "Endpoint", "Description"],
        ["GET", "/api/training/modules", "List available training modules"],
        ["POST", "/api/training/session/start", "Start a training session"],
        ["POST", "/api/training/session/evaluate", "Evaluate training response"],
        ["GET", "/api/training/session/{session_id}", "Get session details"],
        ["GET", "/api/training/sessions", "Get user's training history"],
        ["GET", "/api/training/progress", "Get user's training progress"],
    ]
    training_api_table = Table(training_api, colWidths=[1*inch, 2.8*inch, 2.2*inch])
    training_api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(training_api_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Other Endpoints", styles['SectionTitle']))
    other_api = [
        ["Method", "Endpoint", "Description"],
        ["POST", "/api/chat", "Send message to AI assistant"],
        ["GET", "/api/health", "Health check endpoint"],
    ]
    other_api_table = Table(other_api, colWidths=[1*inch, 2.5*inch, 2.5*inch])
    other_api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(other_api_table)
    
    story.append(PageBreak())
    
    # ========== CHAPTER 15: CONFIGURATION ==========
    story.append(Paragraph("15. Configuration & Environment", styles['ChapterTitle']))
    
    story.append(Paragraph("Environment Variables (.env)", styles['SectionTitle']))
    env_vars = [
        ["Variable", "Default", "Description"],
        ["CHAT_PROVIDER", "auto", "Chat provider: auto/openai/gemini/ollama"],
        ["OLLAMA_BASE_URL", "http://127.0.0.1:11434", "Ollama server URL"],
        ["OLLAMA_MODEL", "qwen2.5:30b", "Ollama model name"],
        ["GRAMMAR_OLLAMA_MODEL", "(OLLAMA_MODEL)", "Model for grammar correction"],
        ["OPENAI_API_KEY", "", "OpenAI API key (optional)"],
        ["OPENAI_MODEL", "gpt-4o-mini", "OpenAI model name"],
        ["GEMINI_API_KEY", "", "Gemini API key (optional)"],
        ["GEMINI_MODEL", "gemini-1.5-flash", "Gemini model name"],
        ["WHISPER_MODEL", "small.en", "Whisper model for transcription"],
    ]
    
    env_table = Table(env_vars, colWidths=[1.8*inch, 1.5*inch, 2.7*inch])
    env_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, DARK_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor("#FFFFFF"), LIGHT_BG]),
    ]))
    story.append(env_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Key Configuration Files", styles['SectionTitle']))
    story.append(Paragraph(
        "• .env - Environment variables (copy from .env.example)<br/>"
        "• requirements.txt - Python dependencies<br/>"
        "• speechwell-frontend/package.json - Frontend dependencies<br/>"
        "• ml/dysarthria_pipeline_config.py - ML feature configuration<br/>"
        "• backend/app/paths.py - File path configuration",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Storage Directories", styles['SectionTitle']))
    story.append(Paragraph(
        "• storage/uploaded_audio/ - Original uploaded files<br/>"
        "• storage/processed_audio/ - Normalized WAV files<br/>"
        "• storage/reports/ - Generated PDF reports<br/>"
        "• ml/models/ - Trained ML model artifacts<br/>"
        "• ml/datasets/ - Training datasets (optional)",
        styles['CustomBody']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 16: FILE STRUCTURE ==========
    story.append(Paragraph("16. File Structure Reference", styles['ChapterTitle']))
    
    story.append(Paragraph("Project Root Structure", styles['SectionTitle']))
    story.append(Paragraph(
        "SpeechWell/<br/>"
        "├── backend/                    # Backend API<br/>"
        "│   └── app/<br/>"
        "│       ├── database/           # DB models and session<br/>"
        "│       ├── services/           # Business logic services<br/>"
        "│       ├── main.py             # FastAPI app entry<br/>"
        "│       ├── paths.py            # Path configuration<br/>"
        "│       └── schemas.py          # Pydantic schemas<br/>"
        "├── ml/                         # Machine learning<br/>"
        "│   ├── datasets/               # Training data<br/>"
        "│   ├── evaluation/             # Model evaluation<br/>"
        "│   ├── feature_extraction/     # Feature extractors<br/>"
        "│   ├── models/                 # Trained models<br/>"
        "│   ├── services/               # ML services<br/>"
        "│   └── training/               # Training scripts<br/>"
        "├── speechwell-frontend/        # React frontend<br/>"
        "│   └── src/<br/>"
        "│       ├── api/                # API client<br/>"
        "│       ├── components/         # UI components<br/>"
        "│       ├── pages/              # Page components<br/>"
        "│       └── utils/              # Utilities<br/>"
        "├── storage/                    # File storage<br/>"
        "│   ├── uploaded_audio/<br/>"
        "│   ├── processed_audio/<br/>"
        "│   └── reports/<br/>"
        "├── scripts/                    # Utility scripts<br/>"
        "├── .env                        # Environment config<br/>"
        "├── requirements.txt            # Python deps<br/>"
        "├── quickstart.ps1              # Windows setup<br/>"
        "└── speechwell.db               # SQLite database",
        styles['CodeBlock']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 17: TROUBLESHOOTING ==========
    story.append(Paragraph("17. Troubleshooting Guide", styles['ChapterTitle']))
    
    story.append(Paragraph("Common Issues", styles['SectionTitle']))
    
    story.append(Paragraph("FFmpeg not found", styles['SubSection']))
    story.append(Paragraph(
        "<b>Symptom:</b> Audio normalization fails, error mentions FFmpeg<br/>"
        "<b>Solution:</b> Install FFmpeg and add to system PATH<br/>"
        "Verify with: ffmpeg -version",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Module not found errors", styles['SubSection']))
    story.append(Paragraph(
        "<b>Symptom:</b> Python ImportError on startup<br/>"
        "<b>Solution:</b> Ensure virtual environment is activated and run:<br/>"
        "pip install -r requirements.txt",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Frontend can't reach backend", styles['SubSection']))
    story.append(Paragraph(
        "<b>Symptom:</b> API calls fail with network error<br/>"
        "<b>Solution:</b><br/>"
        "• Confirm backend running on http://localhost:8000<br/>"
        "• Check CORS configuration in backend/app/main.py<br/>"
        "• Verify firewall settings",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Missing ML models", styles['SubSection']))
    story.append(Paragraph(
        "<b>Symptom:</b> Analysis returns default/zero values<br/>"
        "<b>Solution:</b> Train or download model:<br/>"
        "python ml/training/train_dysarthria_rf_svc_ensemble.py --group-aware",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Empty transcripts", styles['SubSection']))
    story.append(Paragraph(
        "<b>Symptom:</b> Whisper returns empty text<br/>"
        "<b>Solution:</b><br/>"
        "• Check audio file is not silent<br/>"
        "• Verify audio format is supported<br/>"
        "• Try different Whisper model (set WHISPER_MODEL)",
        styles['CustomBody']
    ))
    
    story.append(Paragraph("Grammar correction not working", styles['SubSection']))
    story.append(Paragraph(
        "<b>Symptom:</b> No grammar corrections applied<br/>"
        "<b>Solution:</b><br/>"
        "• For local: Ensure Ollama is running with model loaded<br/>"
        "• For cloud: Verify API keys in .env file<br/>"
        "• Check CHAT_PROVIDER setting",
        styles['CustomBody']
    ))
    
    story.append(PageBreak())
    
    # ========== CHAPTER 18: FUTURE IMPROVEMENTS ==========
    story.append(Paragraph("18. Future Improvements", styles['ChapterTitle']))
    
    story.append(Paragraph("Recommended Enhancements", styles['SectionTitle']))
    
    improvements = [
        ("Silence Detection", "Add silence detection in main analysis path to reject empty recordings before scoring."),
        ("MFCC Features for Training", "Introduce mel-frequency features for richer training inference."),
        ("Video Pagination", "Add pagination for video categories (5 videos per page)."),
        ("Automated Testing", "Add tests for auth, upload, training, and theme persistence."),
        ("Schema Cleanup", "Rename grammar_score to grammar_quality_score for clarity."),
        ("Real-time Feedback", "Add WebSocket support for live transcription during recording."),
        ("Mobile Support", "Optimize frontend for mobile devices."),
        ("Batch Processing", "Support bulk audio file upload and processing."),
        ("Export Options", "Add CSV/JSON export for analysis history."),
        ("User Groups", "Support for speech therapy groups and shared progress."),
    ]
    
    for title, desc in improvements:
        story.append(Paragraph(f"<b>{title}:</b> {desc}", styles['CustomBody']))
    
    story.append(Paragraph("Current Limitations", styles['SectionTitle']))
    
    limitations = [
        "Stuttering detection is transcript-driven (screening, not clinical measurement)",
        "Training scoring is rule-based rather than custom ML model",
        "YouTube video player doesn't replicate all youtube.com features",
        "No real-time transcription during recording (post-processing only)",
        "Single-user database (no multi-tenancy support)",
    ]
    
    for limitation in limitations:
        story.append(Paragraph(f"• {limitation}", styles['CustomBody']))
    
    story.append(Spacer(1, 0.5*inch))
    
    story.append(Paragraph("Summary", styles['SectionTitle']))
    story.append(Paragraph(
        "SpeechWell is a comprehensive speech improvement platform combining modern ML models "
        "(Whisper, Wav2Vec2) with practical speech therapy exercises. The system uses a unified "
        "authentication model connecting analysis and training workflows through a React frontend "
        "and FastAPI backend. The platform is designed for extensibility and can be enhanced with "
        "additional ML models, exercises, and features as needed.",
        styles['CustomBody']
    ))
    
    # Build PDF
    doc.build(story)
    print(f"PDF generated: {OUTPUT_PATH}")
    return str(OUTPUT_PATH)


if __name__ == "__main__":
    build_document()
