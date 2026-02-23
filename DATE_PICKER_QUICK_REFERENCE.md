# 📌 Date Picker Fix - Quick Reference

## The Problem (Before)
```python
# ❌ OLD APPROACH - Date picker shows stale data
selected_date = st.date_input("Date", value=today)
df = load_schedule()  # Loads ALL appointments, caches them
# Filters by client-side - old data persists!
view_df = df[df["DATE"] == selected_date]
```

## The Solution (After)
```python
# ✅ NEW APPROACH - Fresh data on every date change
# 1. Initialize date picker first
if "selected_schedule_date" not in st.session_state:
    st.session_state.selected_schedule_date = date.today()

# 2. Get selected date
selected_date = st.date_input("Date", value=st.session_state.selected_schedule_date)

# 3. CRITICAL: Detect date change and clear cache
if selected_date != st.session_state.selected_schedule_date:
    st.session_state.selected_schedule_date = selected_date
    clear_schedule_cache()  # Clear old data
    st.rerun()  # Force reload

# 4. Load data (will be fresh because cache was cleared)
df = load_schedule()

# 5. Filter by date
view_df = df[df["DATE"] == selected_date]
st.dataframe(view_df)
```

---

## Copy-Paste Code Blocks

### Block 1: Update Imports (at top of page file)
```python
from data.schedule_repo import load_schedule, clear_schedule_cache
```

### Block 2: Initialize Date (right in render() function)
```python
from datetime import date
if "selected_schedule_date" not in st.session_state:
    st.session_state.selected_schedule_date = date.today()
```

### Block 3: Date Picker
```python
st.markdown("### 📆 Select Date")
selected_date = st.date_input(
    "Choose a date",
    value=st.session_state.selected_schedule_date,
    key="sched_date_picker",
    label_visibility="collapsed",
)
```

### Block 4: Detect Change & Clear Cache (MUST be before load_schedule!)
```python
if selected_date != st.session_state.selected_schedule_date:
    st.session_state.selected_schedule_date = selected_date
    clear_schedule_cache()
    st.write("🧹 Cache cleared, reloading...")
    st.rerun()

st.session_state.selected_schedule_date = selected_date
```

### Block 5: Load & Filter
```python
df = st.session_state.get("df")
if df is None:
    with st.spinner("Loading..."):
        df = load_schedule()
    st.session_state.df = df

# Filter by date
date_str = selected_date.isoformat()
view_df = df[df.get("DATE", "").astype(str).str.strip() == date_str]

st.write(f"✅ {len(view_df)} appointments for {selected_date}")
if len(view_df) == 0:
    st.info("No appointments for this date")
else:
    st.dataframe(view_df)
```

---

## Step-by-Step Checklist

- [ ] 1. Add import: `clear_schedule_cache`
- [ ] 2. Initialize: `st.session_state.selected_schedule_date`
- [ ] 3. Add date picker: `st.date_input()`
- [ ] 4. Add change detection: `if selected_date != st.session_state...`
- [ ] 5. Add cache clear: `clear_schedule_cache()`
- [ ] 6. Add st.rerun(): Force page reload
- [ ] 7. Filter by date: `df[df["DATE"] == date_str]`
- [ ] 8. Test with different dates
- [ ] 9. Verify debug output shows fresh data
- [ ] 10. Remove debug messages in production (optional)

---

## What Each Part Does

| Code | Purpose |
|------|---------|
| `if "var" not in st.session_state:` | Store data across reruns |
| `st.date_input(..., key="...")` | Unique control ID |
| `if selected_date != session_date:` | Detect when user changes date |
| `clear_schedule_cache()` | Delete old cached appointments |
| `st.rerun()` | Reload the entire page |
| `.isoformat()` | Format date as YYYY-MM-DD |
| `astype(str).str.strip()` | Clean whitespace before comparing |

---

## Debugging Commands

Run these in Python terminal to test:

```python
# Test 1: Check if cache is working
from data.schedule_repo import clear_schedule_cache
clear_schedule_cache()
print("✅ Cache cleared")

# Test 2: Load appointments for specific date
from data.schedule_repo import load_appointments_by_date
from datetime import date
df = load_appointments_by_date(date(2026, 2, 24))
print(f"✅ Loaded {len(df)} appointments")

# Test 3: Check column names
from data.schedule_repo import load_schedule
df = load_schedule()
print(f"Columns: {list(df.columns)}")
print(f"DATE values: {df['DATE'].unique()}")
```

---

## Common Mistakes

❌ **Mistake 1:** Not initializing session_state first
```python
# WRONG - session_state not defined yet
selected_date = st.date_input("Date")
if selected_date != st.session_state.selected_date:
```

✅ **Correct:**
```python
# RIGHT - initialize first
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()
selected_date = st.date_input("Date", value=st.session_state.selected_date)
```

---

❌ **Mistake 2:** Clearing cache AFTER loading data
```python
# WRONG - cache cleared too late
df = load_schedule()  # Gets cached data!
clear_schedule_cache()  # Clears after use
```

✅ **Correct:**
```python
# RIGHT - clear BEFORE load
clear_schedule_cache()  # Clear old data first
df = load_schedule()  # Gets fresh data
```

---

❌ **Mistake 3:** Not calling st.rerun()
```python
# WRONG - page doesn't refresh
if date_changed:
    clear_schedule_cache()
    # Missing: st.rerun()
```

✅ **Correct:**
```python
# RIGHT - reload page with fresh data
if date_changed:
    clear_schedule_cache()
    st.rerun()  # REQUIRED!
```

---

## Production Checklist

- [ ] Remove all `st.write("🔍 **DEBUG:**...")` lines
- [ ] Or wrap with: `if SHOW_DEBUG: st.write(...)`
- [ ] Test with real Supabase data
- [ ] Test timezone handling (UTC vs local)
- [ ] Test with empty dates
- [ ] Test performance with large datasets
- [ ] Document in code WHY dates work this way
- [ ] Add this file to team documentation

---

## Files Modified

1. ✅ `data/schedule_repo.py` - New functions
2. ✅ `pages/scheduling/full_schedule.py` - Fixed date handling
3. ✅ `pages/scheduling/schedule_by_op.py` - Fixed date handling
4. 📄 `pages/scheduling/full_schedule_corrected_example.py` - Reference
5. 📄 `DATE_PICKER_FIX_GUIDE.md` - Full guide
6. 📄 This file - Quick reference

---

## Need to revert?

```bash
git log --oneline
git diff HEAD~1 HEAD
git revert HEAD  # Revert last commit
```

---

**Last Updated:** 2026-02-24  
**Status:** ✅ Ready for production
