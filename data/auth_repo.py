# data/auth_repo.py
"""User authentication & password management."""

from __future__ import annotations
import hashlib
import os
from typing import Optional
import streamlit as st

from config.settings import get_supabase_config
from data.supabase_client import get_supabase_client


def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash a password using PBKDF2-SHA256 with a salt.

    Returns:
        (salt_hex, hash_hex) tuple
    """
    if salt is None:
        salt = os.urandom(16).hex()
    salt_bytes = bytes.fromhex(salt)
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        100000
    )
    return salt, hash_bytes.hex()


def _verify_password(password: str, stored_hash_str: str) -> bool:
    """Verify password against stored hash.

    Args:
        password: Plain text password to check
        stored_hash_str: Stored hash in format "salt_hex:hash_hex"

    Returns:
        True if password matches, False otherwise
    """
    try:
        salt_hex, stored_hash_hex = stored_hash_str.split(':', 1)
        _, computed_hash_hex = _hash_password(password, salt_hex)
        return computed_hash_hex == stored_hash_hex
    except Exception:
        return False


def authenticate(username: str, password: str) -> Optional[dict]:
    """Authenticate user against Supabase users table.

    Args:
        username: Username to check
        password: Plain text password to verify

    Returns:
        User dict {id, username, role} on success, None on failure
    """
    try:
        url, key, *_ = get_supabase_config()
        if not url or not key:
            return None

        client = get_supabase_client(url, key)
        if not client:
            return None

        resp = client.table("users").select("id,username,password_hash,role,is_active").eq("username", username).limit(1).execute()
        data = resp.data or []
        if not data:
            return None

        user = data[0]
        if not user.get("is_active"):
            return None

        if not _verify_password(password, user.get("password_hash", "")):
            return None

        return {
            "id": user.get("id"),
            "username": user.get("username"),
            "role": user.get("role"),
        }
    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return None


def get_all_users() -> list[dict]:
    """Get all users (admin only)."""
    try:
        url, key, *_ = get_supabase_config()
        if not url or not key:
            return []

        client = get_supabase_client(url, key)
        if not client:
            return []

        resp = client.table("users").select("id,username,role,is_active,created_at").order("created_at", desc=True).execute()
        return resp.data or []
    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return []


def create_user(username: str, password: str, role: str) -> bool:
    """Create a new user."""
    try:
        # Validate role
        if role not in ("admin", "frontdesk", "assistant"):
            return False

        # Hash password
        salt, hash_hex = _hash_password(password)
        password_hash = f"{salt}:{hash_hex}"

        url, key, *_ = get_supabase_config()
        if not url or not key:
            return False

        client = get_supabase_client(url, key)
        if not client:
            return False

        client.table("users").insert({
            "username": username,
            "password_hash": password_hash,
            "role": role,
            "is_active": True,
        }).execute()
        return True
    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return False


def ensure_admin_exists() -> None:
    """Ensure a default admin account exists. Called on first run."""
    try:
        users = get_all_users()
        if users:
            return  # Users already exist, don't seed

        # Create default admin account
        create_user("SPOIDERMON", "SPOIDERMON123", "admin")
        print("[AUTH] Created default admin account: username=SPOIDERMON, password=SPOIDERMON123")
    except Exception as e:
        print(f"[AUTH ERROR] Failed to ensure admin exists: {e}")
