from pathlib import Path

from coverai.services.config import SERVICE_CONFIG
from coverai.services.resume_files.docx_text_extractor import extract_docx_text
from coverai.services.resume_files.errors import UnsupportedResumeFileError
from coverai.services.resume_files.pdf_text_extractor import extract_pdf_text

_RESUME_FILE_CONFIG = SERVICE_CONFIG.resume_files


class ResumeFileTextExtractor:
    def extract_text(self, file_name: str, content: bytes) -> str:
        """Извлекает текст."""
        suffix = Path(file_name).suffix.lower()
        if suffix in _RESUME_FILE_CONFIG.plain_text_suffixes:
            return _extract_plain_text(content)
        if suffix == _RESUME_FILE_CONFIG.docx_suffix:
            return extract_docx_text(content)
        if suffix == _RESUME_FILE_CONFIG.pdf_suffix:
            return extract_pdf_text(content)

        raise UnsupportedResumeFileError


def _extract_plain_text(content: bytes) -> str:
    return content.decode(_RESUME_FILE_CONFIG.plain_text_encoding).strip()
