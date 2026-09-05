"""
Basic security & validation helpers:
- Filename sanitization
- Upload size / extension validation
- Generic input sanitization for form fields
"""
import os
import re
import uuid
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def sanitize_filename(filename: str) -> str:
    """Strip path components and unsafe characters, keep extension."""
    filename = os.path.basename(filename)
    name, ext = os.path.splitext(filename)
    name = re.sub(r"[^A-Za-z0-9_\-]", "_", name)[:80]
    return f"{name}_{uuid.uuid4().hex[:8]}{ext.lower()}"


def validate_upload_file(file: UploadFile, max_size_mb: int):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )
    return ext


def validate_file_size(size_bytes: int, max_size_mb: int):
    max_bytes = max_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max allowed size is {max_size_mb}MB.",
        )


def sanitize_string(value: str) -> str:
    """Remove characters commonly used in injection attacks from free-text input."""
    if not isinstance(value, str):
        return value
    return re.sub(r"[<>${}]", "", value).strip()
