import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime


def generate_pdf_report(audio_id: str, classification: dict) -> str:
    """
    Generates a clinical-style PDF diagnostic report.
    Returns the path to the generated PDF.
    """

    os.makedirs("storage/reports", exist_ok=True)

    file_path = f"storage/reports/{audio_id}.pdf"
    c = canvas.Canvas(file_path, pagesize=A4)

    width, height = A4
    y = height - 50

    # ---- Title ----
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "SpeechWell – Speech Disorder Diagnostic Report")
    y -= 40

    # ---- Metadata ----
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Audio ID: {audio_id}")
    y -= 20
    c.drawString(50, y, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 30

    # ---- Diagnosis ----
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Diagnosis Summary")
    y -= 25

    c.setFont("Helvetica", 11)

    for disorder, score in classification.items():
        percent = round(score * 100, 1)
        c.drawString(70, y, f"- {disorder.capitalize()}: {percent}%")
        y -= 18

    y -= 20

    # ---- Interpretation ----
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Clinical Interpretation")
    y -= 25

    c.setFont("Helvetica", 11)

    interpretation = []

    if classification.get("stuttering", 0) > 0.3:
        interpretation.append(
            "• Signs of stuttering detected (pauses, fluency breaks)."
        )

    if classification.get("dysarthria", 0) > 0.3:
        interpretation.append(
            "• Possible motor-speech control issues (dysarthria)."
        )

    if classification.get("phonological", 0) > 0.3:
        interpretation.append(
            "• Phonological pattern inconsistencies observed."
        )

    if classification.get("apraxia", 0) > 0.3:
        interpretation.append(
            "• Mild indicators of speech planning difficulty (apraxia)."
        )

    if not interpretation:
        interpretation.append(
            "• Speech appears mostly healthy with minor variations."
        )

    for line in interpretation:
        c.drawString(70, y, line)
        y -= 18

    y -= 20

    # ---- Recommendations ----
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Recommendations")
    y -= 25

    c.setFont("Helvetica", 11)
    c.drawString(70, y, "• Practice slow and rhythmic speech exercises.")
    y -= 18
    c.drawString(70, y, "• Use breathing and pacing techniques.")
    y -= 18
    c.drawString(70, y, "• Consult a certified Speech-Language Pathologist if needed.")

    y -= 40

    # ---- Footer ----
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(
        50,
        y,
        "Note: This report is AI-assisted and not a medical diagnosis."
    )

    c.showPage()
    c.save()

    return file_path
