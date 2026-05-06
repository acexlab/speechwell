"""
File Logic Summary: PDF report generator. It renders a polished single-page
clinical-style report with a centered overall score, paired analysis cards,
timing metrics, transcript blocks, and a grammar summary table.
"""

from __future__ import annotations

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from ..paths import REPORTS_DIR
from .score_service import (
    calculate_grammar_quality_score,
    calculate_overall_score,
    percent_display,
)

PAGE_WIDTH, PAGE_HEIGHT = A4
PAGE_MARGIN = 28
CONTENT_LEFT = PAGE_MARGIN
CONTENT_WIDTH = PAGE_WIDTH - (PAGE_MARGIN * 2)

HEADER_BLUE = colors.HexColor("#1F67B3")
HEADER_BLUE_DARK = colors.HexColor("#124D8B")
TEXT_DARK = colors.HexColor("#233B63")
TEXT_MUTED = colors.HexColor("#617A9E")
BORDER = colors.HexColor("#D7E2F0")
SURFACE = colors.white
SURFACE_SOFT = colors.HexColor("#F4F8FD")
TRACK = colors.HexColor("#E6EEF8")
SUCCESS = colors.HexColor("#31A76F")
WARN = colors.HexColor("#F2A541")
DANGER = colors.HexColor("#D95563")
RING_BG = colors.HexColor("#D5E6FA")
RING_FG = colors.HexColor("#7DB4EC")


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value or 0.0)))


def _percent(value: float | int | None) -> int:
    return percent_display(_clamp(value))


def _severity_text(probability: float) -> str:
    if probability < 0.3:
        return "Low"
    if probability < 0.6:
        return "Moderate"
    return "High"


def _grammar_badge(score: float) -> tuple[str, colors.Color]:
    if score >= 0.8:
        return "Strong", SUCCESS
    if score >= 0.6:
        return "Fair", WARN
    return "Needs Work", DANGER


def _display_name(user_name: str | None) -> str:
    cleaned = " ".join((user_name or "").replace("_", " ").replace("-", " ").split()).strip()
    return cleaned if cleaned else "SpeechWell User"


def _draw_rounded_box(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    width: float,
    height: float,
    *,
    fill_color=colors.white,
    stroke_color=BORDER,
    radius: float = 8,
) -> None:
    c.setFillColor(fill_color)
    c.setStrokeColor(stroke_color)
    c.roundRect(x, y_top - height, width, height, radius, stroke=1, fill=1)


def _draw_wrapped_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y_top: float,
    width: float,
    *,
    font_name: str = "Helvetica",
    font_size: int = 10,
    line_height: float = 13,
    color=TEXT_DARK,
    max_lines: int | None = None,
) -> float:
    content = (text or "").strip() or "No text available."
    lines = simpleSplit(content, font_name, font_size, width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            last = lines[-1].rstrip()
            if not last.endswith("..."):
                lines[-1] = (last[:-3] + "...") if len(last) > 3 else "..."

    c.setFont(font_name, font_size)
    c.setFillColor(color)
    y = y_top
    for line in lines:
        c.drawString(x, y, line)
        y -= line_height
    return y


def _draw_label_value(
    c: canvas.Canvas,
    x: float,
    y: float,
    label: str,
    value: str,
    *,
    label_font: str = "Helvetica-Bold",
    value_font: str = "Helvetica-Bold",
    label_size: int = 9,
    value_size: int = 10,
    label_color=TEXT_DARK,
    value_color=TEXT_DARK,
    right_x: float | None = None,
) -> None:
    c.setFillColor(label_color)
    c.setFont(label_font, label_size)
    c.drawString(x, y, label)
    c.setFillColor(value_color)
    c.setFont(value_font, value_size)
    if right_x is None:
        c.drawString(x, y - 13, value)
        return
    value_width = stringWidth(value, value_font, value_size)
    c.drawString(right_x - value_width, y, value)


def _draw_progress_bar(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    width: float,
    height: float,
    probability: float,
    fill_color,
) -> None:
    c.setFillColor(TRACK)
    c.roundRect(x, y_top - height, width, height, height / 2, stroke=0, fill=1)
    c.setFillColor(fill_color)
    c.roundRect(
        x,
        y_top - height,
        width * _clamp(probability),
        height,
        height / 2,
        stroke=0,
        fill=1,
    )


def _draw_score_ring(c: canvas.Canvas, center_x: float, center_y: float, score_percent: int) -> None:
    radius = 54
    line_width = 10
    c.setLineWidth(line_width)
    c.setStrokeColor(RING_BG)
    c.circle(center_x, center_y, radius, stroke=1, fill=0)
    c.setStrokeColor(RING_FG)
    c.arc(
        center_x - radius,
        center_y - radius,
        center_x + radius,
        center_y + radius,
        startAng=90,
        extent=-360 * max(0.0, min(1.0, score_percent / 100.0)),
    )
    c.setStrokeColor(colors.black)
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(HEADER_BLUE_DARK)
    score_label = f"{score_percent}%"
    c.drawCentredString(center_x, center_y - 8, score_label)


def _draw_header(c: canvas.Canvas, report_date: str) -> float:
    y_top = PAGE_HEIGHT - PAGE_MARGIN
    header_height = 48
    c.setFillColor(HEADER_BLUE)
    c.rect(CONTENT_LEFT, y_top - header_height, CONTENT_WIDTH, header_height, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    # Keep the title slightly lower so the glyph ascenders never clip at the
    # top edge of the blue header when viewed in PDF readers.
    c.drawCentredString(
        CONTENT_LEFT + (CONTENT_WIDTH / 2),
        y_top - 31,
        "SpeechWell AI - Clinical Speech Report",
    )
    return y_top - header_height


def _draw_name_date_row(c: canvas.Canvas, y_top: float, user_name: str, report_date: str) -> float:
    row_height = 24
    _draw_rounded_box(
        c,
        CONTENT_LEFT,
        y_top,
        CONTENT_WIDTH,
        row_height,
        fill_color=SURFACE,
        stroke_color=BORDER,
        radius=8,
    )
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(TEXT_DARK)
    c.drawString(CONTENT_LEFT + 14, y_top - 15, user_name)
    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_MUTED)
    c.drawRightString(CONTENT_LEFT + CONTENT_WIDTH - 14, y_top - 15, f"Report date: {report_date}")
    return y_top - row_height


def _draw_pill(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    text: str,
    *,
    fill_color,
    text_color=colors.white,
    height: float = 18,
    font_size: int = 8,
) -> float:
    width = max(64, stringWidth(text, "Helvetica-Bold", font_size) + 20)
    c.setFillColor(fill_color)
    c.roundRect(x, y_top - height, width, height, height / 2, stroke=0, fill=1)
    c.setFillColor(text_color)
    c.setFont("Helvetica-Bold", font_size)
    c.drawCentredString(x + (width / 2), y_top - height + 5.5, text)
    return width


def _overall_status(score_percent: int) -> tuple[str, colors.Color, str]:
    if score_percent >= 85:
        return (
            "Healthy",
            SUCCESS,
            "Strong overall performance across motor speech, fluency, and language clarity.",
        )
    if score_percent >= 70:
        return (
            "Mild concern",
            colors.HexColor("#3F83D7"),
            "Overall speech is mostly stable, with a few areas worth monitoring.",
        )
    if score_percent >= 55:
        return (
            "Mixed signals",
            WARN,
            "Some speech patterns may benefit from guided practice and follow-up review.",
        )
    return (
        "Needs support",
        DANGER,
        "Several areas show elevated risk and may need focused speech support.",
    )


def _humanize_identifier(value: str | None) -> str:
    if not value:
        return "Not available"
    normalized = str(value).replace("_", " ").replace("-", " ").strip()
    if normalized.lower() == "runtime comparison model":
        return "Latest comparison model"
    return normalized.title()


def _normalize_preview_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip().lower()


def _draw_mini_stat(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    width: float,
    height: float,
    label: str,
    value: str,
) -> None:
    _draw_rounded_box(
        c,
        x,
        y_top,
        width,
        height,
        fill_color=SURFACE,
        stroke_color=BORDER,
        radius=8,
    )
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(x + (width / 2), y_top - 13, label)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(TEXT_DARK)
    c.drawCentredString(x + (width / 2), y_top - 29, value)


def _draw_metric_rows(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    width: float,
    rows: list[tuple[str, str]],
) -> None:
    label_x = x + 14
    value_x = x + width - 14
    line_y = y_top - 47
    row_height = 15
    for index, (label, value) in enumerate(rows):
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(TEXT_MUTED)
        c.drawString(label_x, line_y, label)
        value_size = 9 if len(value) <= 18 else 8
        c.setFont("Helvetica-Bold", value_size)
        c.setFillColor(TEXT_DARK)
        c.drawRightString(value_x, line_y, value)
        if index < len(rows) - 1:
            c.setStrokeColor(BORDER)
            c.setLineWidth(0.4)
            c.line(label_x, line_y - 4.5, value_x, line_y - 4.5)
        line_y -= row_height


def _draw_overall_section(
    c: canvas.Canvas,
    y_top: float,
    overall_score: int,
    dys_probability: float,
    stut_probability: float,
    grammar_quality: float,
) -> float:
    section_height = 164
    _draw_rounded_box(
        c,
        CONTENT_LEFT,
        y_top,
        CONTENT_WIDTH,
        section_height,
        fill_color=SURFACE_SOFT,
        stroke_color=BORDER,
        radius=12,
    )

    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(HEADER_BLUE_DARK)
    c.drawString(CONTENT_LEFT + 18, y_top - 24, "Overall Speech Health Score")

    status_text, status_color, status_summary = _overall_status(overall_score)
    score_box_x = CONTENT_LEFT + 18
    score_box_y_top = y_top - 34
    score_box_width = 154
    score_box_height = 76
    _draw_rounded_box(
        c,
        score_box_x,
        score_box_y_top,
        score_box_width,
        score_box_height,
        fill_color=SURFACE,
        stroke_color=BORDER,
        radius=12,
    )
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(status_color)
    c.drawCentredString(score_box_x + (score_box_width / 2), score_box_y_top - 16, status_text.upper())
    c.setFont("Helvetica-Bold", 31)
    c.setFillColor(HEADER_BLUE_DARK)
    c.drawCentredString(score_box_x + (score_box_width / 2), score_box_y_top - 49, f"{overall_score}%")

    summary_x = score_box_x + score_box_width + 18
    summary_width = CONTENT_WIDTH - (summary_x - CONTENT_LEFT) - 18
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(TEXT_MUTED)
    c.drawString(summary_x, y_top - 42, "Summary Insight")
    _draw_wrapped_text(
        c,
        status_summary,
        summary_x,
        y_top - 58,
        summary_width,
        font_size=10,
        line_height=13,
        color=TEXT_MUTED,
        max_lines=3,
    )

    tile_y_top = y_top - 108
    tile_gap = 10
    tile_width = (CONTENT_WIDTH - 36 - (tile_gap * 2)) / 3
    pronunciation = f"{round((1.0 - dys_probability) * 100)}%"
    fluency = f"{round((1.0 - stut_probability) * 100)}%"
    clarity = f"{round(grammar_quality * 100)}%"
    tile_x = CONTENT_LEFT + 18
    _draw_mini_stat(c, tile_x, tile_y_top, tile_width, 40, "Pronunciation", pronunciation)
    _draw_mini_stat(c, tile_x + tile_width + tile_gap, tile_y_top, tile_width, 40, "Fluency", fluency)
    _draw_mini_stat(c, tile_x + (tile_width + tile_gap) * 2, tile_y_top, tile_width, 40, "Clarity", clarity)

    return y_top - section_height - 12


def _draw_analysis_card(
    c: canvas.Canvas,
    x: float,
    y_top: float,
    width: float,
    height: float,
    title: str,
    rows: list[tuple[str, str]],
    *,
    accent_color=HEADER_BLUE,
) -> None:
    _draw_rounded_box(
        c,
        x,
        y_top,
        width,
        height,
        fill_color=SURFACE,
        stroke_color=BORDER,
        radius=12,
    )
    c.setFillColor(accent_color)
    c.roundRect(x, y_top - 6, width, 6, 6, stroke=0, fill=1)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(TEXT_DARK)
    c.drawString(x + 14, y_top - 18, title)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.7)
    c.line(x + 12, y_top - 30, x + width - 12, y_top - 30)
    _draw_metric_rows(c, x, y_top, width, rows)


def _draw_metrics_band(c: canvas.Canvas, y_top: float, whisper_features: dict) -> float:
    band_height = 86
    _draw_rounded_box(
        c,
        CONTENT_LEFT,
        y_top,
        CONTENT_WIDTH,
        band_height,
        fill_color=SURFACE,
        stroke_color=BORDER,
        radius=12,
    )
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_DARK)
    c.drawString(CONTENT_LEFT + 14, y_top - 18, "Speech Timing Metrics")
    c.setStrokeColor(BORDER)
    c.line(CONTENT_LEFT + 12, y_top - 28, CONTENT_LEFT + CONTENT_WIDTH - 12, y_top - 28)

    metrics = [
        ("Speaking Rate", f"{float(whisper_features.get('speaking_rate_wps', 0.0)):.2f} wps"),
        ("Avg. Pause", f"{float(whisper_features.get('average_pause_sec', 0.0)):.1f} sec"),
        ("Max. Pause", f"{float(whisper_features.get('max_pause_sec', 0.0)):.1f} sec"),
        ("Duration", f"{float(whisper_features.get('total_duration_sec', 0.0)):.1f} sec"),
    ]
    tile_gap = 8
    tile_width = (CONTENT_WIDTH - 24 - (tile_gap * 3)) / 4
    tile_y_top = y_top - 38
    for idx, (label, value) in enumerate(metrics):
        tile_x = CONTENT_LEFT + 12 + idx * (tile_width + tile_gap)
        _draw_mini_stat(c, tile_x, tile_y_top, tile_width, 38, label, value)
    return y_top - band_height - 10


def _draw_transcript_section(c: canvas.Canvas, y_top: float, original_text: str, corrected_text: str) -> float:
    section_height = 136
    _draw_rounded_box(
        c,
        CONTENT_LEFT,
        y_top,
        CONTENT_WIDTH,
        section_height,
        fill_color=SURFACE_SOFT,
        stroke_color=BORDER,
        radius=12,
    )
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_DARK)
    c.drawString(CONTENT_LEFT + 14, y_top - 18, "Transcript Review")
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_MUTED)
    c.drawString(CONTENT_LEFT + 14, y_top - 31, "Compare the original transcript with the cleaned AI version.")
    c.setStrokeColor(BORDER)
    c.line(CONTENT_LEFT + 12, y_top - 38, CONTENT_LEFT + CONTENT_WIDTH - 12, y_top - 38)

    inner_gap = 14
    inner_width = (CONTENT_WIDTH - 24 - inner_gap) / 2
    inner_height = 82
    left_x = CONTENT_LEFT + 12
    right_x = left_x + inner_width + inner_gap
    inner_y_top = y_top - 46
    texts_match = _normalize_preview_text(original_text) == _normalize_preview_text(corrected_text)

    _draw_rounded_box(c, left_x, inner_y_top, inner_width, inner_height, fill_color=SURFACE, stroke_color=BORDER, radius=10)
    _draw_rounded_box(
        c,
        right_x,
        inner_y_top,
        inner_width,
        inner_height,
        fill_color=colors.HexColor("#EEF6FF"),
        stroke_color=colors.HexColor("#C9DCF2"),
        radius=10,
    )
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.6)
    c.line(CONTENT_LEFT + (CONTENT_WIDTH / 2), inner_y_top - 4, CONTENT_LEFT + (CONTENT_WIDTH / 2), inner_y_top - inner_height + 4)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(TEXT_DARK)
    c.drawString(left_x + 12, inner_y_top - 16, "Original Transcript")
    c.drawString(right_x + 12, inner_y_top - 16, "AI-Corrected Transcript")
    c.setStrokeColor(BORDER)
    c.line(left_x + 10, inner_y_top - 24, left_x + inner_width - 10, inner_y_top - 24)
    c.line(right_x + 10, inner_y_top - 24, right_x + inner_width - 10, inner_y_top - 24)

    _draw_wrapped_text(
        c,
        original_text or "No transcript available.",
        left_x + 12,
        inner_y_top - 38,
        inner_width - 24,
        font_size=9,
        line_height=11.5,
        color=TEXT_MUTED,
        max_lines=5,
    )
    if texts_match:
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(HEADER_BLUE_DARK)
        c.drawString(right_x + 12, inner_y_top - 38, "No correction needed")
        _draw_wrapped_text(
            c,
            "The AI-corrected transcript matches the original transcript for this sample.",
            right_x + 12,
            inner_y_top - 54,
            inner_width - 24,
            font_size=9,
            line_height=11.5,
            color=TEXT_MUTED,
            max_lines=4,
        )
    else:
        _draw_wrapped_text(
            c,
            corrected_text or "No corrected transcript available.",
            right_x + 12,
            inner_y_top - 38,
            inner_width - 24,
            font_size=9,
            line_height=11.5,
            color=TEXT_MUTED,
            max_lines=5,
        )
    return y_top - section_height - 10


def _draw_grammar_table(
    c: canvas.Canvas,
    y_top: float,
    grammar_quality: float,
    grammar_error_count: int,
    grammar_error_probability: float,
) -> float:
    table_height = 102
    _draw_rounded_box(
        c,
        CONTENT_LEFT,
        y_top,
        CONTENT_WIDTH,
        table_height,
        fill_color=SURFACE,
        stroke_color=BORDER,
        radius=12,
    )
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_DARK)
    c.drawString(CONTENT_LEFT + 14, y_top - 18, "Language Analysis")
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_MUTED)
    _draw_wrapped_text(
        c,
        "Higher quality is better. Error rate estimates how much of the transcript may need correction.",
        CONTENT_LEFT + 14,
        y_top - 31,
        CONTENT_WIDTH - 28,
        font_size=8,
        line_height=10,
        color=TEXT_MUTED,
        max_lines=2,
    )
    c.setStrokeColor(BORDER)
    c.line(CONTENT_LEFT + 12, y_top - 42, CONTENT_LEFT + CONTENT_WIDTH - 12, y_top - 42)

    badge_text, _badge_color = _grammar_badge(grammar_quality)
    quality_text = f"{round(grammar_quality * 100)}% ({badge_text})"
    error_rate_text = f"{_percent(grammar_error_probability)}%"
    error_count_text = str(grammar_error_count)

    tile_gap = 10
    tile_width = (CONTENT_WIDTH - 24 - tile_gap * 2) / 3
    tile_y_top = y_top - 50
    _draw_mini_stat(c, CONTENT_LEFT + 12, tile_y_top, tile_width, 38, "Grammar Quality", quality_text)
    _draw_mini_stat(c, CONTENT_LEFT + 12 + tile_width + tile_gap, tile_y_top, tile_width, 38, "Estimated Error Rate", error_rate_text)
    _draw_mini_stat(c, CONTENT_LEFT + 12 + (tile_width + tile_gap) * 2, tile_y_top, tile_width, 38, "Estimated Error Count", error_count_text)
    return y_top - table_height - 12


def _draw_footer_disclaimer(c: canvas.Canvas) -> None:
    footer_y = 52
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.6)
    c.line(CONTENT_LEFT, footer_y + 10, CONTENT_LEFT + CONTENT_WIDTH, footer_y + 10)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#7A8EAB"))
    c.drawCentredString(
        PAGE_WIDTH / 2,
        footer_y - 2,
        "This report is AI-generated and supports screening only. It is not a medical diagnosis.",
    )


def generate_pdf_report(
    audio_id: str,
    whisper_features: dict,
    classification_result: dict,
    output_dir: str | None = None,
    report_filename: str | None = None,
    user_name: str | None = None,
    report_date: str | None = None,
):
    output_dir = output_dir or str(REPORTS_DIR)
    os.makedirs(output_dir, exist_ok=True)
    file_name = report_filename or f"{audio_id}_report.pdf"
    file_path = os.path.join(output_dir, file_name)
    rendered_report_date = (report_date or datetime.now().strftime("%Y-%m-%d")).strip()

    dys = classification_result.get("dysarthria", {})
    stut = classification_result.get("stuttering", {})
    grammar = classification_result.get("grammar", {})

    dys_probability = _clamp(dys.get("probability", 0.0))
    stut_probability = _clamp(stut.get("stuttering_probability", 0.0))
    grammar_error_probability = _clamp(grammar.get("grammar_error_probability", 1.0))
    grammar_quality = calculate_grammar_quality_score(
        error_count=grammar.get("error_count_estimate", 0),
        transcript=whisper_features.get("transcript", ""),
        error_probability=grammar_error_probability,
        fallback_score=grammar.get("grammar_quality_score", 0.0),
    )
    overall_score = calculate_overall_score(
        dys_probability,
        stut_probability,
        grammar_quality,
    )

    c = canvas.Canvas(file_path, pagesize=A4)
    c.setTitle("SpeechWell Clinical Speech Report")
    y = _draw_header(c, rendered_report_date)
    y = _draw_name_date_row(
        c,
        y,
        _display_name(user_name),
        rendered_report_date,
    )
    y -= 12
    y = _draw_overall_section(c, y, overall_score, dys_probability, stut_probability, grammar_quality)

    card_gap = 10
    card_width = (CONTENT_WIDTH - card_gap) / 2
    card_height = 108

    dys_rows = [
        ("Classification", _humanize_identifier(dys.get("label"))),
        ("Risk level", _severity_text(dys_probability)),
        ("Risk score", f"{_percent(dys_probability)}%"),
        (
            "Symptom evidence",
            (
                f"{int(dys.get('symptom_score'))}/5"
                if dys.get("symptom_score") is not None
                else "Not available"
            ),
        ),
    ]

    stut_rows = [
        ("Risk level", _severity_text(stut_probability)),
        ("Risk score", f"{_percent(stut_probability)}%"),
        ("Repetitions", str(int(stut.get("repetitions", 0)))),
        ("Prolongations", str(int(stut.get("prolongations", 0)))),
        ("Blocks", str(int(stut.get("blocks", 0)))),
    ]

    _draw_analysis_card(
        c,
        CONTENT_LEFT,
        y,
        card_width,
        card_height,
        "Motor Speech Analysis (Dysarthria)",
        dys_rows,
        accent_color=colors.HexColor("#7DB4EC"),
    )
    _draw_analysis_card(
        c,
        CONTENT_LEFT + card_width + card_gap,
        y,
        card_width,
        card_height,
        "Fluency Analysis (Stuttering)",
        stut_rows,
        accent_color=colors.HexColor("#8FC2A8"),
    )
    y -= card_height + 10

    y = _draw_metrics_band(c, y, whisper_features)
    y = _draw_transcript_section(
        c,
        y,
        whisper_features.get("transcript", "No transcript available."),
        grammar.get("corrected_text", "").strip() or "No corrected transcript available.",
    )
    y = _draw_grammar_table(
        c,
        y,
        grammar_quality,
        int(grammar.get("error_count_estimate", 0)),
        grammar_error_probability,
    )
    _draw_footer_disclaimer(c)

    c.save()
    return file_path
