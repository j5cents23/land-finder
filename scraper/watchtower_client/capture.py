"""capture_exception — write one row to observability.errors.

Design rules:
- Never raise. A failure in observability must not break the host process.
- Use lazy Supabase client so importing this module is cheap.
- Include hostname and stack trace for postmortem debugging.
"""
from __future__ import annotations

import socket
import traceback
from typing import Any

from ._fingerprint import fingerprint_exception
from ._supa import obs_table


def capture_exception(
    exc: BaseException,
    project: str,
    context: dict[str, Any] | None = None,
) -> None:
    try:
        row = {
            "project": project,
            "hostname": socket.gethostname(),
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "stack_trace": "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            ),
            "context": context or {},
            "fingerprint": fingerprint_exception(project, exc),
        }
        obs_table("errors").insert(row).execute()
    except Exception:
        pass
