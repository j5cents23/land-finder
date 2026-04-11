"""Lazily-instantiated Supabase client for the watchtower_client package.

Reads credentials from the environment:
    WATCHTOWER_SUPABASE_URL
    WATCHTOWER_SUPABASE_SERVICE_KEY

Lazy initialization keeps import-time cheap and lets projects import
the client library even in environments where Supabase is not reachable
(e.g. offline development).

All writes target the `observability` schema.
"""
import os
from typing import Any

_client: Any = None


def get_client() -> Any:
    global _client
    if _client is None:
        from supabase import create_client
        url = os.environ["WATCHTOWER_SUPABASE_URL"]
        key = os.environ["WATCHTOWER_SUPABASE_SERVICE_KEY"]
        _client = create_client(url, key)
    return _client


def obs_table(name: str) -> Any:
    """Return a supabase table reference bound to the observability schema."""
    return get_client().schema("observability").table(name)


def reset_for_testing() -> None:
    """Test helper — clears the cached client."""
    global _client
    _client = None
