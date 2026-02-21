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
        print(f"[AUTH DEBUG] Authenticating user: {username}")
        url, key, *_ = get_supabase_config()
        print(f"[AUTH DEBUG] Config loaded: url={bool(url)}, key={bool(key)}")
        if not url or not key:
            print("[AUTH DEBUG] Missing Supabase config")
            return None

        client = get_supabase_client(url, key)
        print(f"[AUTH DEBUG] Client created: {bool(client)}")
        if not client:
            print("[AUTH DEBUG] Failed to create Supabase client")
            return None

        print(f"[AUTH DEBUG] Querying users table for username: {username}")
        resp = client.table("users").select("id,username,password_hash,role,is_active").eq("username", username).limit(1).execute()
        data = resp.data or []
        print(f"[AUTH DEBUG] Query result count: {len(data)}")

        if not data:
            print(f"[AUTH DEBUG] No user found with username: {username}")
            return None

        user = data[0]
        print(f"[AUTH DEBUG] User found. is_active={user.get('is_active')}")

        if not user.get("is_active"):
            print("[AUTH DEBUG] User is not active")
            return None

        password_hash = user.get("password_hash", "")
        print(f"[AUTH DEBUG] Password hash format: {password_hash[:20]}...")

        if not _verify_password(password, password_hash):
            print("[AUTH DEBUG] Password verification failed")
            return None

        print(f"[AUTH DEBUG] Authentication successful for user: {username}")
        return {
            "id": user.get("id"),
            "username": user.get("username"),
            "role": user.get("role"),
        }
    except Exception as e:
        print(f"[AUTH ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_all_users() -> list[dict]:
    """Get all users (admin only)."""
    try:
        url, key, *_ = get_supabase_config()
        if not url or not key:
            print("[AUTH DEBUG] get_all_users: Missing Supabase config")
            return []

        client = get_supabase_client(url, key)
        if not client:
            print("[AUTH DEBUG] get_all_users: Failed to create client")
            return []

        resp = client.table("users").select("id,username,role,is_active,created_at").order("created_at", desc=True).execute()
        users = resp.data or []
        print(f"[AUTH DEBUG] get_all_users: Retrieved {len(users)} users from database")
        return users
    except Exception as e:
        print(f"[AUTH ERROR] get_all_users failed: {type(e).__name__}: {e}")
        return []


def create_user(username: str, password: str, role: str) -> bool:
    """Create a new user."""
    try:
        # Validate role
        if role not in ("admin", "frontdesk", "assistant"):
            print(f"[AUTH ERROR] Invalid role: {role}")
            return False

        # Hash password
        salt, hash_hex = _hash_password(password)
        password_hash = f"{salt}:{hash_hex}"
        print(f"[AUTH DEBUG] Hashed password for {username}: salt={salt[:8]}..., hash={hash_hex[:20]}...")

        url, key, *_ = get_supabase_config()
        print(f"[AUTH DEBUG] Config for create_user: url={bool(url)}, key={bool(key)}")
        if not url or not key:
            print("[AUTH ERROR] Missing Supabase config for create_user")
            return False

        client = get_supabase_client(url, key)
        print(f"[AUTH DEBUG] Client created for create_user: {bool(client)}")
        if not client:
            print("[AUTH ERROR] Failed to create Supabase client for create_user")
            return False

        print(f"[AUTH DEBUG] Inserting user: username={username}, role={role}")
        result = client.table("users").insert({
            "username": username,
            "password_hash": password_hash,
            "role": role,
            "is_active": True,
        }).execute()
        print(f"[AUTH DEBUG] Insert result: {result}")
        print(f"[AUTH] Successfully created user: {username} with role: {role}")
        return True
    except Exception as e:
        print(f"[AUTH ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def reset_password(username: str, new_password: str) -> bool:
    """Reset password for a user."""
    try:
        # Hash new password
        salt, hash_hex = _hash_password(new_password)
        password_hash = f"{salt}:{hash_hex}"

        url, key, *_ = get_supabase_config()
        if not url or not key:
            return False

        client = get_supabase_client(url, key)
        if not client:
            return False

        # Update password
        result = client.table("users").update({
            "password_hash": password_hash,
        }).eq("username", username).execute()

        return bool(result.data)
    except Exception as e:
        print(f"[AUTH ERROR] {e}")
        return False


def ensure_admin_exists() -> None:
    """Ensure a default admin account exists. Called on first run."""
    try:
        print("[AUTH DEBUG] Checking if admin account exists...")
        users = get_all_users()
        print(f"[AUTH DEBUG] get_all_users returned {len(users)} users")
        if users:
            print("[AUTH DEBUG] Users already exist, skipping admin seed")
            return  # Users already exist, don't seed

        # Create default admin account
        print("[AUTH DEBUG] No users found, creating default admin...")
        success = create_user("SPOIDERMON", "SPOIDERMON123", "admin")
        if success:
            print("[AUTH] ✓ Created default admin account: username=SPOIDERMON, password=SPOIDERMON123")
        else:
            print("[AUTH ERROR] Failed to create default admin account")
    except Exception as e:
        print(f"[AUTH ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
