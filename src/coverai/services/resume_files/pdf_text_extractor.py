import fitz

from coverai.services.resume_files.errors import ResumeTextNotExtractedError


def extract_pdf_text(content: bytes) -> str:
    """Извлекает текст из PDF."""
    pages: list[str] = []
    with fitz.open(stream=content, filetype="pdf") as document:
        for page in document:
            pages.append(page.get_text("text"))

    text = "\n".join(pages).strip()
    if not text:
        raise ResumeTextNotExtractedError

    return text
