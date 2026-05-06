from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("w", W_NS)


def w_tag(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def parse_markdown(text: str) -> list[tuple[str, str]]:
    blocks: list[tuple[str, str]] = []
    paragraph_buffer: list[str] = []
    code_buffer: list[str] = []
    in_code = False

    def flush_paragraph() -> None:
        if not paragraph_buffer:
            return
        joined = " ".join(part.strip() for part in paragraph_buffer if part.strip()).strip()
        if joined:
            blocks.append(("body", joined))
        paragraph_buffer.clear()

    def flush_code() -> None:
        if not code_buffer:
            return
        blocks.append(("code", "\n".join(code_buffer)))
        code_buffer.clear()

    for raw_line in text.splitlines():
        stripped = raw_line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_buffer.append(raw_line.rstrip("\n"))
            continue

        if not stripped or stripped == "---":
            flush_paragraph()
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            blocks.append(("title", stripped[2:].strip()))
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            blocks.append(("h1", stripped[3:].strip()))
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            blocks.append(("h2", stripped[4:].strip()))
            continue

        if stripped.startswith("#### "):
            flush_paragraph()
            blocks.append(("h3", stripped[5:].strip()))
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            blocks.append(("list", f"• {stripped[2:].strip()}"))
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            blocks.append(("list", re.sub(r"^\d+\.\s+", "", stripped)))
            continue

        paragraph_buffer.append(stripped)

    flush_paragraph()
    if in_code:
        flush_code()
    return blocks


def add_run(paragraph: ET.Element, text: str) -> None:
    run = ET.SubElement(paragraph, w_tag("r"))
    text_el = ET.SubElement(run, w_tag("t"))
    text_el.set(f"{{{XML_NS}}}space", "preserve")
    text_el.text = text


def make_paragraph(text: str, style_id: str) -> ET.Element:
    p = ET.Element(w_tag("p"))
    ppr = ET.SubElement(p, w_tag("pPr"))
    pstyle = ET.SubElement(ppr, w_tag("pStyle"))
    pstyle.set(w_tag("val"), style_id)
    add_run(p, text)
    return p


def make_code_paragraph(text: str) -> ET.Element:
    p = ET.Element(w_tag("p"))
    ppr = ET.SubElement(p, w_tag("pPr"))
    pstyle = ET.SubElement(ppr, w_tag("pStyle"))
    pstyle.set(w_tag("val"), "BodyText")
    r = ET.SubElement(p, w_tag("r"))
    rpr = ET.SubElement(r, w_tag("rPr"))
    ET.SubElement(rpr, w_tag("rFonts")).set(w_tag("ascii"), "Courier New")
    ET.SubElement(rpr, w_tag("rFonts")).set(w_tag("hAnsi"), "Courier New")
    text_el = ET.SubElement(r, w_tag("t"))
    text_el.set(f"{{{XML_NS}}}space", "preserve")
    text_el.text = text
    return p


def build_document_xml(markdown: str, sect_pr: ET.Element | None) -> bytes:
    document = ET.Element(w_tag("document"))
    body = ET.SubElement(document, w_tag("body"))

    style_map = {
        "title": "Title",
        "h1": "Heading1",
        "h2": "Heading2",
        "h3": "Heading3",
        "body": "BodyText",
        "list": "ListParagraph",
    }

    for block_type, block_text in parse_markdown(markdown):
        if block_type == "code":
            for line in block_text.splitlines() or [""]:
                body.append(make_code_paragraph(line))
        else:
            body.append(make_paragraph(block_text, style_map.get(block_type, "BodyText")))

    if sect_pr is not None:
        body.append(sect_pr)

    return ET.tostring(document, encoding="utf-8", xml_declaration=True)


def main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit(
            "Usage: python scripts/render_markdown_to_docx.py <input.md> <template.docx> <output.docx>"
        )

    input_md = Path(sys.argv[1]).resolve()
    template_docx = Path(sys.argv[2]).resolve()
    output_docx = Path(sys.argv[3]).resolve()

    markdown = input_md.read_text(encoding="utf-8")

    with zipfile.ZipFile(template_docx, "r") as zin:
        original_document = ET.fromstring(zin.read("word/document.xml"))
        sect_pr = original_document.find(f".//{w_tag('sectPr')}")
        sect_copy = ET.fromstring(ET.tostring(sect_pr, encoding="utf-8")) if sect_pr is not None else None
        new_document_xml = build_document_xml(markdown, sect_copy)

        with zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    data = new_document_xml
                zout.writestr(item, data)


if __name__ == "__main__":
    main()
