from io import BytesIO

import fitz
import pytest
from docx import Document

from coverai.services.resume_files import ResumeFileTextExtractor
from coverai.services.resume_files.errors import (
    ResumeTextNotExtractedError,
    UnsupportedResumeFileError,
)


def test_extracts_plain_text() -> None:
    extractor = ResumeFileTextExtractor()

    assert extractor.extract_text("resume.txt", b" plain text resume ") == (
        "plain text resume"
    )


def test_extracts_markdown_as_plain_text() -> None:
    extractor = ResumeFileTextExtractor()

    assert extractor.extract_text("resume.md", b"# Resume\nPython") == (
        "# Resume\nPython"
    )


def test_extracts_docx_text() -> None:
    extractor = ResumeFileTextExtractor()

    assert extractor.extract_text("resume.docx", docx_bytes("Python developer")) == (
        "Python developer"
    )


def test_extracts_pdf_with_text_layer() -> None:
    extractor = ResumeFileTextExtractor()

    assert "Python developer" in extractor.extract_text(
        "resume.pdf",
        pdf_bytes("Python developer"),
    )


def test_rejects_pdf_without_text_layer() -> None:
    extractor = ResumeFileTextExtractor()

    with pytest.raises(ResumeTextNotExtractedError):
        extractor.extract_text("resume.pdf", blank_pdf_bytes())


def test_rejects_unsupported_file_extension() -> None:
    extractor = ResumeFileTextExtractor()

    with pytest.raises(UnsupportedResumeFileError):
        extractor.extract_text("resume.jpg", b"content")


def docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def blank_pdf_bytes() -> bytes:
    document = fitz.open()
    document.new_page()
    content = document.tobytes()
    document.close()
    return content
