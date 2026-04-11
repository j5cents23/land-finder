"""Fingerprint an exception for dedupe purposes.

The fingerprint is a 16-char hex string derived from:
    project || exception type || last frame file || last frame line

Two exceptions with the same type raised from the same file+line in the same
project collapse to one fingerprint. This is intentionally coarse — we want
to group "the same bug" rather than "the same occurrence".
"""
from __future__ import annotations

import hashlib
import traceback


def fingerprint_exception(project: str, exc: BaseException) -> str:
    parts: list[str] = [project, type(exc).__name__]
    tb = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
    if tb:
        last = tb[-1]
        parts.append(last.filename)
        parts.append(str(last.lineno))
    joined = "::".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]
