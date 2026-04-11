"""watchtower_client — tiny library that reports exceptions and job heartbeats
to a Supabase observability schema. Used by John's projects to replace Sentry.
"""
from .capture import capture_exception
from .monitor import monitor

__all__ = ["capture_exception", "monitor"]
