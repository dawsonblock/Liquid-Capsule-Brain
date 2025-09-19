from __future__ import annotations

import io
import mimetypes
import os
import zipfile
from typing import Any

from pypdf import PdfReader

MAX_BYTES = 10 * 1024 * 1024  # 10 MB safety cap per upload
MAX_PREVIEW_CHARS = 4000
SUPPORTED_TXT_EXTS = {".txt", ".md", ".log"}
SUPPORTED_PDF_EXTS = {".pdf"}
SUPPORTED_ARCHIVE_EXTS = {".zip"}


def _safe_decode(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def _extract_text_from_pdf_bytes(data: bytes) -> str:
    buf = io.BytesIO(data)
    reader = PdfReader(buf)
    parts: list[str] = []
    for page in reader.pages:
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        if txt:
            parts.append(txt)
    return "\n\n".join(parts)


def preview_text(text: str, max_chars: int = MAX_PREVIEW_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    # Try to cut on a boundary
    snippet = text[: max_chars - 20]
    # Avoid cutting mid-word if possible
    last_space = snippet.rfind(" ")
    if last_space > 0:
        snippet = snippet[:last_space]
    return snippet + "\n... [truncated]"


def extract_bytes(filename: str, content_type: str | None, data: bytes) -> tuple[str, dict[str, Any]]:
    """Extract textual content from bytes based on file type.

    Returns (text, meta) where meta contains filename, type, size, and extra fields.
    """
    if len(data) > MAX_BYTES:
        data = data[:MAX_BYTES]

    ext = (os.path.splitext(filename)[1] or "").lower()
    ctype = (content_type or mimetypes.guess_type(filename)[0] or "").lower()

    meta: dict[str, Any] = {
        "filename": filename,
        "bytes": len(data),
        "content_type": ctype,
        "ext": ext,
        "type": "unknown",
    }

    # PDF
    if ext in SUPPORTED_PDF_EXTS or ctype == "application/pdf":
        meta["type"] = "pdf"
        text = _extract_text_from_pdf_bytes(data)
        return text, meta

    # TXT-like
    if ext in SUPPORTED_TXT_EXTS or ctype.startswith("text/"):
        meta["type"] = "text"
        return _safe_decode(data), meta

    # ZIP archive
    if ext in SUPPORTED_ARCHIVE_EXTS or ctype in ("application/zip", "application/x-zip-compressed"):
        meta["type"] = "zip"
        extracted_files: list[str] = []
        parts: list[str] = []
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = info.filename
                sub_ext = (os.path.splitext(name)[1] or "").lower()
                try:
                    file_bytes = zf.read(info)
                except Exception:
                    continue
                if sub_ext in SUPPORTED_TXT_EXTS:
                    parts.append(f"===== {name} =====\n" + _safe_decode(file_bytes))
                    extracted_files.append(name)
                elif sub_ext in SUPPORTED_PDF_EXTS:
                    parts.append(f"===== {name} (PDF) =====\n" + _extract_text_from_pdf_bytes(file_bytes))
                    extracted_files.append(name)
                else:
                    # Try generic text decode for unknown small files
                    if len(file_bytes) <= MAX_BYTES and sub_ext not in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                        try:
                            parts.append(f"===== {name} (raw) =====\n" + _safe_decode(file_bytes))
                            extracted_files.append(name)
                        except Exception:
                            pass
        meta["files_extracted"] = extracted_files
        return "\n\n".join(parts), meta

    # Fallback: try to decode as text
    meta["type"] = "text"
    return _safe_decode(data), meta
