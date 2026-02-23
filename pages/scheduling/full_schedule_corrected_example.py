# ============================================================================
# CORRECTED STREAMLIT FETCH SECTION FOR DATE-FILTERED APPOINTMENTS
# ============================================================================
# This shows the proper way to fetch appointments by date from Supabase
# Copy the relevant sections into your actual full_schedule.py
# ============================================================================

from __future__ import annotations
from datetime import date
import streamlit as st
import pandas as pd

# Import the new function
from data.schedule_repo import load_appointments_by_date, clear_schedule_cache

# ── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(page_title="Full Schedule", layout="wide")
st.markdown("## 📅 Full Schedule")

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ CORRECTED APPROACH: Initialize & Handle Date Selection                    ║
# ╠════════════════════════════════════════════════════════════════════════════╣

# ── Step 1: Initialize selected date in session state (FIRST) ────────────────
# This persists the date across reruns
if "selected_schedule_date" not in st.session_state:
    st.session_state.selected_schedule_date = date.today()
    st.write("🆕 **DEBUG:** Initialized date to today")

# ── Step 2: Create date picker ──────────────────────────────────────────────
st.markdown("### 📆 Select Date")
selected_date = st.date_input(
    "Choose a date",
    value=st.session_state.selected_schedule_date,
    key="sched_date_picker",
    label_visibility="collapsed",
)

# ── Step 3: CRITICAL - Check if date changed and clear cache ────────────────
# This ensures that when user picks a new date, we fetch fresh data
if selected_date != st.session_state.selected_schedule_date:
    st.write(f"📅 **DEBUG:** Date changed from {st.session_state.selected_schedule_date} → {selected_date}")
    st.session_state.selected_schedule_date = selected_date
    clear_schedule_cache()  # Clear cached data
    st.rerun()  # Force re-fetch

# Update session state with current selection (if no change)
st.session_state.selected_schedule_date = selected_date

# ── Step 4: CRITICAL - Fetch appointments for SELECTED date (NOT cached) ────
st.markdown("### 📥 Loading Appointments")
appointments_df = load_appointments_by_date(selected_date)

# ── Step 5: Verify and display results ──────────────────────────────────────
st.markdown(f"**{len(appointments_df)} appointment(s) on {selected_date.strftime('%A, %B %d, %Y')}**")

if len(appointments_df) == 0:
    st.info("No appointments scheduled")
else:
    # Display appointments in a table
    st.dataframe(
        appointments_df,
        use_container_width=True,
        hide_index=True,
    )

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ KEY CHANGES & FIXES EXPLAINED                                             ║
# ╠════════════════════════════════════════════════════════════════════════════╣
#
# 🔧 FIX #1: Date Change Detection
#    ├─ Check if selected_date != session_state.selected_schedule_date
#    ├─ Clear cache when changed (force fresh query)
#    └─ Call st.rerun() to refresh the page
#
# 🔧 FIX #2: New Non-Cached Fetch Function
#    ├─ load_appointments_by_date() doesn't use @st.cache_data
#    ├─ Queries Supabase directly with date filter
#    ├─ Handles both DATE and TIMESTAMP column types
#    └─ Returns ONLY appointments for the selected date
#
# 🔧 FIX #3: No Fallback to Full Dataset
#    ├─ Removed cached _load_from_supabase_cached() usage
#    ├─ No longer loads ALL appointments and filters client-side
#    ├─ Filters happen at Supabase level (more efficient)
#    └─ Old data cannot be accidentally shown
#
# 🔧 FIX #4: Proper Date Formatting
#    ├─ Date converted to ISO format (YYYY-MM-DD) with .isoformat()
#    ├─ Supabase query uses this format: eq("appointment_date", date_str)
#    ├─ Handles both .date and .timestamp column types
#    └─ Fallback with time range for timestamp columns
#
# 🔧 FIX #5: Debug Output
#    ├─ Shows selected date being fetched
#    ├─ Shows number of rows returned from Supabase
#    ├─ Shows column names in result
#    ├─ Shows any errors that occur
#    └─ Remove st.write() calls in production (toggle with debug flag)
#
# ╚════════════════════════════════════════════════════════════════════════════╝

# ── OPTIONAL: Add refresh button to manually reload ─────────────────────────
col_refresh, col_debug = st.columns([1, 2])
with col_refresh:
    if st.button("🔄 Refresh", key="refresh_appts"):
        clear_schedule_cache()
        st.rerun()

with col_debug:
    show_debug = st.checkbox("🐛 Show debug info", value=True)
    if not show_debug:
        st.write("**Debug messages above will be hidden once refreshed**")

# ──────────────────────────────────────────────────────────────────────────────
# TROUBLESHOOTING GUIDE
# ──────────────────────────────────────────────────────────────────────────────
#
# Problem: Still seeing old data after selecting new date?
#   ✓ Make sure you're calling clear_schedule_cache() BEFORE st.rerun()
#   ✓ Check that date picker has key="sched_date_picker" (not changing)
#   ✓ Verify selected_date != old_date check is BEFORE the fetch
#
# Problem: Getting wrong count of appointments?
#   ✓ Check the debug output - see if Supabase is returning them
#   ✓ Try selecting a date you KNOW has data
#   ✓ Check Supabase table structure (is column named "appointment_date"?)
#
# Problem: "appointment_date" column doesn't exist?
#   ✓ Update table="appointments" and appointment_date column name in
#     load_appointments_by_date() function
#   ✓ Check your Supabase schema
#
# Problem: Getting "No data" even for valid dates?
#   ✓ Check date format in Supabase (UTC vs local timezone)
#   ✓ Try changing the query to use CAST(appointment_date AS DATE)
#   ✓ Check if data actually exists for that date
#
# ──────────────────────────────────────────────────────────────────────────────
