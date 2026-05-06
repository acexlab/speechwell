from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT_MD = ROOT / "PROJECT_TECHNICAL_REPORT.md"
OUTPUT_PDF = ROOT / "PROJECT_TECHNICAL_REPORT.pdf"


def inline_format(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", text)
    return text


def build_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleCustom",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            spaceBefore=10,
            spaceAfter=8,
            textColor=colors.HexColor("#17324D"),
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            spaceBefore=8,
            spaceAfter=6,
            textColor=colors.HexColor("#244E73"),
        ),
        "body": ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=6,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8.5,
            leading=11,
            leftIndent=8,
            rightIndent=8,
            backColor=colors.HexColor("#F4F6F8"),
            borderPadding=6,
            borderWidth=0.5,
            borderColor=colors.HexColor("#D6DCE3"),
            spaceBefore=4,
            spaceAfter=8,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            leftIndent=10,
            firstLineIndent=0,
            spaceAfter=2,
        ),
    }


def flush_paragraph(buffer: list[str], story: list, styles: dict) -> None:
    if not buffer:
        return
    text = " ".join(part.strip() for part in buffer if part.strip())
    if text:
        story.append(Paragraph(inline_format(text), styles["body"]))
    buffer.clear()


def flush_list(items: list[str], story: list, styles: dict) -> None:
    if not items:
        return
    flowable = ListFlowable(
        [
            ListItem(Paragraph(inline_format(item), styles["bullet"]))
            for item in items
        ],
        bulletType="bullet",
        leftIndent=14,
    )
    story.append(flowable)
    story.append(Spacer(1, 4))
    items.clear()


def markdown_to_story(text: str) -> list:
    styles = build_styles()
    story: list = []
    paragraph_buffer: list[str] = []
    bullet_items: list[str] = []
    code_buffer: list[str] = []
    in_code = False
    first_title = True

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph(paragraph_buffer, story, styles)
            flush_list(bullet_items, story, styles)
            if in_code:
                story.append(Preformatted("\n".join(code_buffer), styles["code"]))
                code_buffer.clear()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_buffer.append(line)
            continue

        if stripped == "---":
            flush_paragraph(paragraph_buffer, story, styles)
            flush_list(bullet_items, story, styles)
            story.append(Spacer(1, 6))
            continue

        if not stripped:
            flush_paragraph(paragraph_buffer, story, styles)
            flush_list(bullet_items, story, styles)
            continue

        if stripped.startswith("# "):
            flush_paragraph(paragraph_buffer, story, styles)
            flush_list(bullet_items, story, styles)
            if not first_title:
                story.append(PageBreak())
            story.append(Paragraph(inline_format(stripped[2:]), styles["title"]))
            first_title = False
            continue

        if stripped.startswith("## "):
            flush_paragraph(paragraph_buffer, story, styles)
            flush_list(bullet_items, story, styles)
            story.append(Paragraph(inline_format(stripped[3:]), styles["h1"]))
            continue

        if stripped.startswith("### "):
            flush_paragraph(paragraph_buffer, story, styles)
            flush_list(bullet_items, story, styles)
            story.append(Paragraph(inline_format(stripped[4:]), styles["h2"]))
            continue

        if stripped.startswith("- "):
            flush_paragraph(paragraph_buffer, story, styles)
            bullet_items.append(stripped[2:])
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_paragraph(paragraph_buffer, story, styles)
            bullet_items.append(re.sub(r"^\d+\.\s+", "", stripped))
            continue

        paragraph_buffer.append(stripped)

    flush_paragraph(paragraph_buffer, story, styles)
    flush_list(bullet_items, story, styles)
    if code_buffer:
        story.append(Preformatted("\n".join(code_buffer), styles["code"]))
    return story


def add_page_number(canvas, doc):
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawRightString(190 * mm, 10 * mm, f"Page {doc.page}")


def main() -> None:
    markdown = INPUT_MD.read_text(encoding="utf-8")
    story = markdown_to_story(markdown)
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title="SpeechWell Technical Report",
        author="OpenAI Codex",
    )
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)


if __name__ == "__main__":
    main()
