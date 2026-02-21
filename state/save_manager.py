# state/save_manager.py
"""Save orchestration, conflict detection, hash comparison."""

from __future__ import annotations
import time as time_module
import streamlit as st

from config.settings import USE_SUPABASE


def _get_meta(df) -> dict:
    try:
        if hasattr(df, "attrs"):
            meta = df.attrs.get("meta")
            if isinstance(meta, dict):
                return dict(meta)
    except Exception:
        pass
    return {}


def _set_meta(df, meta: dict) -> None:
    try:
        if hasattr(df, "attrs"):
            df.attrs["meta"] = dict(meta or {})
    except Exception:
        pass


def _apply_time_blocks_to_meta(meta: dict) -> dict:
    from services.availability import serialize_time_blocks
    out = dict(meta or {})
    out["time_blocks"] = serialize_time_blocks(st.session_state.get("time_blocks", []))
    return out


def sync_time_blocks_from_meta(df) -> None:
    """Load persisted time blocks into session_state."""
    try:
        from services.availability import deserialize_time_blocks
        meta = _get_meta(df)
        if "time_blocks" in meta:
            st.session_state.time_blocks = deserialize_time_blocks(meta.get("time_blocks"))
    except Exception:
        pass


def queue_unsaved(df, reason: str = "") -> None:
    try:
        st.session_state.unsaved_df = df.copy(deep=False)
    except Exception:
        st.session_state.unsaved_df = df
    st.session_state.unsaved_df_version = int(st.session_state.get("unsaved_df_version", 0)) + 1
    st.session_state.pending_changes = True
    st.session_state.pending_changes_reason = reason


def save_now(df, show_toast: bool = True, message: str = "Saved!", ignore_conflict: bool = False) -> bool:
    """Persist the DataFrame. Handles conflict detection via save_version comparison."""
    from data.schedule_repo import save_schedule, fetch_remote_save_version, compute_schedule_hash
    from config.settings import IST
    from datetime import datetime

    if st.session_state.get("is_saving"):
        return False
    st.session_state.is_saving = True
    try:
        meta = _get_meta(df)
        meta = _apply_time_blocks_to_meta(meta)
        loaded_version = st.session_state.get("loaded_save_version")
        local_version = _safe_int(meta.get("save_version"), None)
        if local_version is None and loaded_version is not None:
            local_version = _safe_int(loaded_version, 0)

        remote_version = None
        if st.session_state.get("enable_conflict_checks", True) and not ignore_conflict and USE_SUPABASE:
            remote_version = fetch_remote_save_version()
            if remote_version is not None and loaded_version is not None:
                if _safe_int(remote_version, -1) != _safe_int(loaded_version, -1):
                    st.session_state.save_conflict = {
                        "local_version": loaded_version,
                        "remote_version": remote_version,
                        "detected_at": datetime.now(IST).isoformat(),
                    }
                    st.error("⚠️ Save blocked: newer data detected remotely. Reload to sync.")
                    return False

        current_hash = compute_schedule_hash(df)
        if current_hash == st.session_state.get("last_saved_hash"):
            return True

        base_version = max(
            _safe_int(loaded_version, 0),
            _safe_int(remote_version, 0),
            _safe_int(local_version, 0),
        )
        meta["save_version"] = base_version + 1
        meta["saved_at"] = datetime.now(IST).isoformat()
        _set_meta(df, meta)

        success = save_schedule(df)
        if success:
            if show_toast:
                st.toast(message, icon="✅")
            st.session_state.last_saved_hash = current_hash
            st.session_state.loaded_save_version = meta["save_version"]
            st.session_state.loaded_save_at = meta["saved_at"]
            st.session_state.save_conflict = None
            st.session_state.last_save_at = time_module.time()
        return success
    except Exception as e:
        st.error(f"Error saving: {e}")
        return False
    finally:
        st.session_state.is_saving = False


def maybe_save(df, show_toast: bool = True, message: str = "Saved!", force: bool = False, ignore_conflict: bool = False) -> bool:
    """Respect auto-save toggle and debounce."""
    if st.session_state.get("is_saving"):
        queue_unsaved(df, reason=message)
        return True
    if force:
        result = save_now(df, show_toast=show_toast, message=message, ignore_conflict=ignore_conflict)
        if result:
            st.session_state.unsaved_df = None
            st.session_state.pending_changes = False
            st.session_state.pending_changes_reason = ""
        else:
            queue_unsaved(df, reason=message)
        return result
    if st.session_state.get("auto_save_enabled", False):
        debounce = float(st.session_state.get("save_debounce_seconds", 0) or 0)
        if debounce > 0:
            last_at = float(st.session_state.get("last_save_at", 0.0) or 0.0)
            if (time_module.time() - last_at) < debounce:
                queue_unsaved(df, reason=message)
                return True
        result = save_now(df, show_toast=show_toast, message=message, ignore_conflict=ignore_conflict)
        if result:
            st.session_state.unsaved_df = None
            st.session_state.pending_changes = False
        else:
            queue_unsaved(df, reason=message)
        return result
    queue_unsaved(df, reason=message)
    if show_toast:
        st.toast("Auto-save is off. Click 'Save Now' to persist.", icon="⚠")
    return True


def _safe_int(value, default=0):
    try:
        return int(float(str(value)))
    except Exception:
        return default
