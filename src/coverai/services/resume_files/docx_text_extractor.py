from io import BytesIO

from docx import Document

from coverai.services.resume_files.errors import ResumeTextNotExtractedError


def extract_docx_text(content: bytes) -> str:
    """Извлекает текст из DOCX."""
    document = Document(BytesIO(content))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    if not text:
        raise ResumeTextNotExtractedError

    return text
