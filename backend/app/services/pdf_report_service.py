"""
File Logic Summary: PDF report generator. It formats analysis outputs into structured clinical sections with severity bars and transcript blocks for download.
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from datetime import datetime
import os
from ..paths import REPORTS_DIR


# ===== LAYOUT CONSTANTS =====
LEFT = 60
RIGHT = 540
TOP_MARGIN = 60
BOTTOM_MARGIN = 70
LINE = 15
SECTION_GAP = 30


def new_page(c):
    c.showPage()
    c.setFont("Helvetica", 11)
    return A4[1] - TOP_MARGIN


def ensure_space(c, y, needed=40):
    if y - needed < BOTTOM_MARGIN:
        return new_page(c)
    return y


def draw_title(c, y):
    c.setFont("Helvetica-Bold", 20)
    c.drawString(LEFT, y, "SpeechWell Clinical Speech Report")
    return y - 35


def draw_metadata(c, y, audio_id):
    c.setFont("Helvetica", 10)
    c.drawString(LEFT, y, f"Audio ID: {audio_id}")
    y -= LINE
    c.drawString(LEFT, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return y - 20


def draw_separator(c, y):
    c.setStrokeColor(colors.lightgrey)
    c.line(LEFT, y, RIGHT, y)
    return y - 15


def draw_section_header(c, y, title):
    y -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(LEFT, y, title)
    return y - 20


def draw_severity_block(c, y, probability, label):
    y = ensure_space(c, y, 70)

    percent = int(probability * 100)

    if probability < 0.3:
        color = colors.green
        level = "LOW"
    elif probability < 0.6:
        color = colors.orange
        level = "MODERATE"
    else:
        color = colors.red
        level = "HIGH"

    # Label
    c.setFont("Helvetica-Bold", 12)
    c.drawString(LEFT, y, label)
    y -= 18

    # Percentage + level
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(color)
    c.drawString(LEFT, y, f"{percent}%")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(LEFT + 80, y + 2, level)
    c.setFillColor(colors.black)

    # Bar
    bar_x = LEFT + 160
    bar_y = y
    bar_width = 300
    bar_height = 16

    c.setStrokeColor(colors.black)
    c.rect(bar_x, bar_y, bar_width, bar_height)

    c.setFillColor(color)
    c.rect(bar_x, bar_y, bar_width * probability, bar_height, fill=1)
    c.setFillColor(colors.black)

    return y - 40


def draw_text_block(c, y, text):
    y = ensure_space(c, y, 60)

    text_obj = c.beginText(LEFT, y)
    text_obj.setLeading(14)

    for sentence in text.split(". "):
        if text_obj.getY() < BOTTOM_MARGIN:
            c.drawText(text_obj)
            y = new_page(c)
            text_obj = c.beginText(LEFT, y)
            text_obj.setLeading(14)

        text_obj.textLine(sentence.strip())

    c.drawText(text_obj)
    return text_obj.getY() - 10


def generate_pdf_report(
    audio_id: str,
    whisper_features: dict,
    classification_result: dict,
    output_dir: str | None = None,
    report_filename: str | None = None,
):
    output_dir = output_dir or str(REPORTS_DIR)
    os.makedirs(output_dir, exist_ok=True)
    file_name = report_filename or f"{audio_id}_report.pdf"
    file_path = os.path.join(output_dir, file_name)

    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4
    y = height - TOP_MARGIN

    # ===== TITLE =====
    y = draw_title(c, y)
    y = draw_metadata(c, y, audio_id)
    y = draw_separator(c, y)

    # ===== DYSARTHRIA =====
    dys = classification_result.get("dysarthria", {})
    y = draw_section_header(c, y, "Motor Speech Analysis – Dysarthria")
    y = draw_severity_block(
        c, y,
        dys.get("probability", 0.0),
        "Confidence Score"
    )
    y = draw_separator(c, y)

    # ===== STUTTERING =====
    stut = classification_result.get("stuttering", {})
    y = draw_section_header(c, y, "Fluency Analysis – Stuttering")

    c.setFont("Helvetica", 12)
    c.drawString(LEFT, y, f"Repetitions: {stut.get('repetitions', 0)}")
    y -= LINE
    c.drawString(LEFT, y, f"Prolongations: {stut.get('prolongations', 0)}")
    y -= LINE
    c.drawString(LEFT, y, f"Blocks: {stut.get('blocks', 0)}")
    y -= 20

    y = draw_severity_block(
        c, y,
        stut.get("stuttering_probability", 0.0),
        "Stuttering Severity"
    )
    y = draw_separator(c, y)

    # ===== SPEECH METRICS =====
    y = draw_section_header(c, y, "Speech Timing Metrics")

    c.setFont("Helvetica", 12)
    c.drawString(LEFT, y, f"Speaking Rate: {whisper_features.get('speaking_rate_wps', 0)} wps")
    y -= LINE
    c.drawString(LEFT, y, f"Average Pause: {whisper_features.get('average_pause_sec', 0)} sec")
    y -= LINE
    c.drawString(LEFT, y, f"Maximum Pause: {whisper_features.get('max_pause_sec', 0)} sec")
    y -= SECTION_GAP

    y = draw_separator(c, y)

    # ===== ORIGINAL TRANSCRIPT =====
    y = draw_section_header(c, y, "Original Transcript")
    y = draw_text_block(
        c, y,
        whisper_features.get("transcript", "No transcript available.")
    )

    # ===== CORRECTED TRANSCRIPT =====
    grammar = classification_result.get("grammar", {})
    corrected = grammar.get("corrected_text", "").strip()

    if corrected:
        y = new_page(c)
        y = draw_section_header(c, y, "AI-Corrected Transcript")
        y = draw_text_block(c, y, corrected)

    # ===== GRAMMAR SCORE PAGE =====
    y = new_page(c)
    y = draw_section_header(c, y, "Language Structure Analysis – Grammar")

    c.setFont("Helvetica", 12)
    c.drawString(LEFT, y, f"Estimated Error Count: {grammar.get('error_count_estimate', 0)}")
    y -= 25

    y = draw_severity_block(
        c, y,
        grammar.get("grammar_error_probability", 0.0),
        "Grammar Quality Score"
    )

    # ===== FOOTER =====
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(
        LEFT,
        40,
        "This report is generated by SpeechWell AI and is not a medical diagnosis."
    )

    c.save()
    return file_path

