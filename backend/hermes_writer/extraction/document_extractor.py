from pathlib import Path

from hermes_writer.api.errors import ApiError

PDF_RECOVERY_HINT = (
    "Verify the PDF is not encrypted or corrupted. You may also paste the extracted text manually."
)
DOCX_RECOVERY_HINT = (
    "Verify the DOCX file is valid and not corrupted. You may also paste the extracted text manually."
)
TXT_RECOVERY_HINT = "Verify the file is UTF-8 encoded. You may also paste the extracted text manually."


def extract_text(path: Path, file_type: str) -> tuple[str, str]:
    if file_type == "pdf":
        return _extract_pdf(path), "pymupdf"
    if file_type == "docx":
        return _extract_docx(path), "python-docx"
    if file_type == "txt":
        return _extract_txt(path), "plain-text"
    raise ApiError("INVALID_FILE_TYPE", "Only PDF, DOCX, and TXT files are supported.")


def _extract_pdf(path: Path) -> str:
    try:
        import fitz  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ApiError(
            "EXTRACTION_FAILED",
            "PyMuPDF is required to extract PDF files.",
            status_code=500,
            recovery_hint=PDF_RECOVERY_HINT,
        ) from exc

    try:
        with fitz.open(str(path)) as document:
            return "\n".join(page.get_text().strip() for page in document).strip()
    except Exception as exc:
        raise ApiError(
            "EXTRACTION_FAILED",
            "Unable to extract text from PDF.",
            status_code=500,
            recovery_hint=PDF_RECOVERY_HINT,
        ) from exc


def _extract_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise ApiError(
            "EXTRACTION_FAILED",
            "python-docx is required to extract DOCX files.",
            status_code=500,
            recovery_hint=DOCX_RECOVERY_HINT,
        ) from exc

    try:
        document = Document(str(path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    except Exception as exc:
        raise ApiError(
            "EXTRACTION_FAILED",
            "Unable to extract text from DOCX.",
            status_code=500,
            recovery_hint=DOCX_RECOVERY_HINT,
        ) from exc


def _extract_txt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ApiError(
            "EXTRACTION_FAILED",
            "TXT files must be UTF-8 encoded.",
            status_code=400,
            recovery_hint=TXT_RECOVERY_HINT,
        ) from exc
