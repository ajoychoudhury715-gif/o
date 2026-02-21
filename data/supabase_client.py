# data/supabase_client.py
"""Supabase client singleton with connection caching."""

from __future__ import annotations
from typing import Optional, Any
import streamlit as st

_supabase_available = False
try:
    from supabase import create_client  # type: ignore
    _supabase_available = True
except Exception:
    pass

SUPABASE_AVAILABLE = _supabase_available


@st.cache_resource
def _get_client_cached(url: str, key: str):
    return create_client(url, key)


def get_supabase_client(url: str, key: str) -> Optional[Any]:
    """Return a cached Supabase client, or None if unavailable."""
    if not SUPABASE_AVAILABLE:
        return None
    if not url or not key:
        return None
    try:
        return _get_client_cached(url, key)
    except Exception:
        try:
            return create_client(url, key)
        except Exception:
            return None


def get_configured_client() -> Optional[Any]:
    """Get a Supabase client using credentials from settings/env."""
    from config.settings import get_supabase_config, USE_SUPABASE
    if not USE_SUPABASE:
        return None
    url, key, *_ = get_supabase_config()
    if not url or not key:
        return None
    return get_supabase_client(url, key)
