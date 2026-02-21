# components/time_block_editor.py
"""Time block add/remove UI component."""

from __future__ import annotations
from typing import Callable
import datetime
import streamlit as st


def render_time_block_editor(
    time_blocks: list[dict],
    assistants: list[str],
    on_add: Callable[[dict], None],
    on_remove: Callable[[int], None],
    today_str: str | None = None,
) -> None:
    """Render the time block management UI.

    Args:
        time_blocks: Current list of time block dicts.
            Each has: assistant, date (str YYYY-MM-DD), reason, start_time, end_time
        assistants: List of assistant names.
        on_add: Callback receiving new time block dict.
        on_remove: Callback receiving the index to remove.
        today_str: Today's date string YYYY-MM-DD (defaults to today).
    """
    if today_str is None:
        today_str = datetime.date.today().isoformat()

    st.markdown("### 🚫 Time Blocks")
    st.caption("Block an assistant from being allocated during a specific period.")

    # ── Add form ───────────────────────────────────────────────────────────────
    with st.expander("➕ Add Time Block", expanded=False):
        with st.form("add_time_block_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                asst_opts = [""] + sorted(assistants)
                assistant = st.selectbox("Assistant *", asst_opts, key="tb_assistant")
                reason = st.text_input("Reason", placeholder="e.g. lunch break, training")
            with c2:
                block_date = st.date_input(
                    "Date",
                    value=datetime.date.fromisoformat(today_str),
                    key="tb_date",
                )
                c_start, c_end = st.columns(2)
                with c_start:
                    start_time = st.time_input("Start Time", value=datetime.time(12, 0), key="tb_start")
                with c_end:
                    end_time = st.time_input("End Time", value=datetime.time(13, 0), key="tb_end")

            if st.form_submit_button("➕ Add Block", use_container_width=True):
                if not assistant:
                    st.error("Please select an assistant.")
                elif start_time >= end_time:
                    st.error("End time must be after start time.")
                else:
                    block = {
                        "assistant": str(assistant).strip().upper(),
                        "date": block_date.isoformat(),
                        "reason": reason.strip() or "Blocked",
                        "start_time": start_time,
                        "end_time": end_time,
                    }
                    on_add(block)

    # ── Existing blocks ────────────────────────────────────────────────────────
    today_blocks = [
        (i, b) for i, b in enumerate(time_blocks or [])
        if str(b.get("date", "")) == today_str
    ]
    other_blocks = [
        (i, b) for i, b in enumerate(time_blocks or [])
        if str(b.get("date", "")) != today_str
    ]

    if not time_blocks:
        st.caption("No time blocks defined.")
        return

    if today_blocks:
        st.markdown("**Today's Blocks**")
        for orig_idx, block in today_blocks:
            _render_block_row(block, orig_idx, on_remove)

    if other_blocks:
        with st.expander(f"Other dates ({len(other_blocks)})", expanded=False):
            for orig_idx, block in other_blocks:
                _render_block_row(block, orig_idx, on_remove)


def _render_block_row(block: dict, idx: int, on_remove: Callable[[int], None]) -> None:
    """Render a single time block row with a remove button."""
    assistant = str(block.get("assistant", "")).strip()
    date_str = str(block.get("date", ""))
    reason = str(block.get("reason", "")).strip() or "Blocked"

    start = block.get("start_time")
    end = block.get("end_time")
    start_str = start.strftime("%H:%M") if isinstance(start, datetime.time) else str(start)[:5]
    end_str = end.strftime("%H:%M") if isinstance(end, datetime.time) else str(end)[:5]

    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            f"""<div style="
                background: rgba(255,255,255,0.05);
                border-radius:8px; padding:8px 12px;
                border-left:3px solid #ef4444;
                font-size:13px; margin-bottom:4px;
            ">
            🚫 <b>{assistant}</b> &nbsp;|&nbsp; {date_str}
            &nbsp;|&nbsp; {start_str}–{end_str}
            &nbsp;|&nbsp; <span style="color:#94a3b8;">{reason}</span>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        if st.button("🗑️", key=f"rm_tb_{idx}", help="Remove block", use_container_width=True):
            on_remove(idx)


def render_time_block_summary(time_blocks: list[dict], today_str: str | None = None) -> None:
    """Render a compact read-only summary of today's time blocks."""
    if today_str is None:
        today_str = datetime.date.today().isoformat()
    today_blocks = [b for b in (time_blocks or []) if str(b.get("date", "")) == today_str]
    if not today_blocks:
        return
    lines = []
    for b in today_blocks:
        assistant = str(b.get("assistant", ""))
        start = b.get("start_time")
        end = b.get("end_time")
        start_str = start.strftime("%H:%M") if isinstance(start, datetime.time) else str(start)[:5]
        end_str = end.strftime("%H:%M") if isinstance(end, datetime.time) else str(end)[:5]
        reason = str(b.get("reason", "Blocked"))
        lines.append(f"🚫 **{assistant}** {start_str}–{end_str} _{reason}_")
    st.markdown("\n\n".join(lines))
