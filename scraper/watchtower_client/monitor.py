"""@monitor — decorator that writes job heartbeats to observability.job_runs.

Usage:
    from watchtower_client import monitor

    @monitor(job_name="daily_report", project="wff_intel", expect_every_sec=86400)
    def run_daily_report():
        ...

    @monitor(job_name="async_job", project="x")
    async def run_async_job():
        ...

Design:
- Works transparently for both sync and async functions.
- Insert a "started" row before the job runs.
- On success, update the row to "ok" with finished_at.
- On failure, update the row to "failed" with error_message AND also
  capture the exception to observability.errors (for dedupe + alerting).
- Re-raise exceptions so the host app sees them — we don't swallow errors.
"""
from __future__ import annotations

import asyncio
import functools
from datetime import datetime, timezone
from typing import Any, Callable

from ._supa import obs_table
from .capture import capture_exception


def monitor(
    job_name: str,
    project: str,
    expect_every_sec: int | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                run_id = _start(project, job_name, expect_every_sec)
                try:
                    result = await fn(*args, **kwargs)
                    _finish_ok(run_id)
                    return result
                except Exception as exc:
                    _finish_fail(run_id, exc)
                    capture_exception(
                        exc, project=project, context={"job_name": job_name}
                    )
                    raise
            return async_wrapper

        @functools.wraps(fn)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            run_id = _start(project, job_name, expect_every_sec)
            try:
                result = fn(*args, **kwargs)
                _finish_ok(run_id)
                return result
            except Exception as exc:
                _finish_fail(run_id, exc)
                capture_exception(
                    exc, project=project, context={"job_name": job_name}
                )
                raise

        return sync_wrapper

    return decorator


def _start(project: str, job_name: str, expect_every_sec: int | None) -> int | None:
    try:
        row = (
            obs_table("job_runs")
            .insert(
                {
                    "project": project,
                    "job_name": job_name,
                    "status": "started",
                    "expect_every_sec": expect_every_sec,
                }
            )
            .execute()
        )
        return row.data[0]["id"]
    except Exception:
        return None


def _finish_ok(run_id: int | None) -> None:
    if run_id is None:
        return
    try:
        obs_table("job_runs").update(
            {
                "status": "ok",
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", run_id).execute()
    except Exception:
        pass


def _finish_fail(run_id: int | None, exc: BaseException) -> None:
    if run_id is None:
        return
    try:
        obs_table("job_runs").update(
            {
                "status": "failed",
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "error_message": str(exc),
            }
        ).eq("id", run_id).execute()
    except Exception:
        pass
