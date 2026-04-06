# Auto-Allotment Algorithm Integration Guide

## Quick Start

### Run Local Tests
```bash
python3 test_auto_allotment.py
```

This demonstrates:
- Phase 1: Pre-scheduling allocation
- Phase 2: 09:45 real-time adjustment when Senior_S1 is absent
- Phase 3: Emergency procedure handling with cascade

**Output:** `TEST_RESULTS.md` with detailed validation report

---

## Integration Checklist

### Step 1: Data Layer Integration
Connect to existing repositories:

```python
# In allocation_engine.py
from data.profile_repo import load_assistants, load_doctors
from data.attendance_repo import get_punch_records  # Add if doesn't exist
from data.schedule_repo import load_schedule

def get_staff_master():
    """Load all active staff"""
    assistants_df = load_assistants()
    return [
        Staff(
            assistant_id=row['ID'],
            name=row['Name'],
            dept_id=row['Department_ID'],
            rank=Rank.SENIOR if row['Rank'] == 'Senior' else Rank.JUNIOR,
            staff_status=StaffStatus[row['Status']],
            current_hours_scheduled=row.get('Hours_Today', 0.0)
        )
        for _, row in assistants_df.iterrows()
    ]

def get_daily_procedures(target_date):
    """Load procedures for a specific date"""
    schedule_df = load_schedule()
    today_schedule = schedule_df[schedule_df['Date'] == target_date]
    return [
        Procedure(
            procedure_id=row['ID'],
            doctor_id=row['Doctor_ID'],
            dept_id=row['Department_ID'],
            scheduled_start=pd.to_datetime(row['Start_Time']),
            estimated_duration=row.get('Duration_Minutes', 60),
            required_assistants=row.get('Required_Staff', 2),
            assigned_assistants=[]
        )
        for _, row in today_schedule.iterrows()
    ]

def get_punch_records_for_date(target_date):
    """Get punch records for specific date"""
    punch_df = get_punch_records(target_date)
    return [
        PunchRecord(
            assistant_id=row['Assistant_ID'],
            punch_in_time=pd.to_datetime(row['Punch_In']) if row['Punch_In'] else None,
            punch_date=target_date,
            status=AssistantStatus[row['Status']]
        )
        for _, row in punch_df.iterrows()
    ]
```

### Step 2: Schedule 09:45 Check
Add to `settings.json`:

```json
{
  "hooks": {
    "on_time": [
      {
        "time": "09:45",
        "prompt": "Run 09:45 adjustment check",
        "script": "services/allotment_hooks.py::run_09_45_check"
      }
    ],
    "on_new_booking": [
      {
        "event": "emergency_procedure_created",
        "prompt": "Handle emergency allocation",
        "script": "services/allotment_hooks.py::handle_emergency"
      }
    ]
  }
}
```

### Step 3: Implement Hook Handlers

Create `services/allotment_hooks.py`:

```python
from services.allocation_engine import AutoAllotmentEngine
from datetime import datetime

def run_09_45_check():
    """Scheduled check at 09:45 AM"""
    from config.settings import IST

    today = datetime.now(IST).date()
    engine = AutoAllotmentEngine(get_staff_master())

    # Load procedures for today
    procedures = get_daily_procedures(today)

    # Run provisional allotment if not already done
    provisional = engine.provisional_allotment(procedures)

    # Get punch records at 09:45
    punch_records = get_punch_records_for_date(today)
    threshold = datetime.now(IST)  # 09:45 AM

    # Run 09:45 adjustment
    re_allotted, critical_alerts = engine.realtime_09_45_adjustment(
        punch_records, threshold
    )

    # Save updated allocations to database
    save_allocations_to_schedule(re_allotted)

    # Handle critical alerts
    if critical_alerts:
        send_admin_alerts(critical_alerts)

    return {'status': 'completed', 'alerts': critical_alerts}

def handle_emergency():
    """Handle new emergency procedure booking"""
    # Get latest procedure from request
    emergency_proc = get_latest_booking()

    engine = AutoAllotmentEngine(get_staff_master())
    success, alloc, alerts = engine.handle_emergency_procedure(
        emergency_proc,
        datetime.now(IST)
    )

    if success:
        save_allocation(emergency_proc)
        notify_doctor(emergency_proc)
    else:
        escalate_to_admin(alerts)

    return {'success': success, 'alerts': alerts}
```

### Step 4: Update Schedule Rendering
Modify `pages/scheduling/full_schedule.py`:

```python
def render():
    # ... existing code ...

    # Load procedures for selected date
    procedures = get_daily_procedures(selected_date)

    # Get current allocations (from Phase 1 & 2)
    allocations = get_current_allocations(selected_date)

    # Render with latest allocation status
    for proc_id, procedure in procedures.items():
        if proc_id in allocations:
            procedure.assigned_assistants = allocations[proc_id]

        # Show allocation status
        render_alloc_status(
            procedure.status.value,
            procedure.assigned_assistants
        )
```

### Step 5: Emergency Booking UI
Add to `pages/scheduling/full_schedule.py`:

```python
if st.button("🚑 Emergency Booking", key="emergency_btn"):
    with st.form("emergency_form", clear_on_submit=True):
        doctor = st.selectbox("Doctor", doctors)
        dept = st.selectbox("Department", OP_ROOMS)
        duration = st.number_input("Duration (min)", 30, 240, 60)

        if st.form_submit_button("Create Booking"):
            new_proc = Procedure(
                procedure_id=f"EMERGENCY_{datetime.now().timestamp()}",
                doctor_id=doctor,
                dept_id=dept,
                scheduled_start=datetime.now(),
                estimated_duration=duration,
                required_assistants=2
            )

            success, alloc, alerts = engine.handle_emergency_procedure(new_proc)

            if success:
                st.success(f"✓ Allocated: {alloc['assigned']}")
            else:
                st.error(f"✗ Allocation failed: {alerts}")
```

---

## Database Schema Changes

### Add Columns to Staff Table
```sql
ALTER TABLE assistants ADD COLUMN hours_scheduled_today FLOAT DEFAULT 0;
ALTER TABLE assistants ADD COLUMN rank ENUM('Senior', 'Junior') DEFAULT 'Junior';
ALTER TABLE assistants ADD COLUMN status ENUM('Active', 'Week_Off', 'Leave', 'Terminated') DEFAULT 'Active';
```

### Create Allotment History Table
```sql
CREATE TABLE allotment_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    procedure_id VARCHAR(255),
    assistant_id VARCHAR(255),
    allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    allocation_phase ENUM('Provisional', 'RealTime', 'Emergency'),
    notes TEXT
);
```

### Add Procedure Status Tracking
```sql
ALTER TABLE schedule ADD COLUMN allocation_status VARCHAR(50);
ALTER TABLE schedule ADD COLUMN allocated_at TIMESTAMP;
ALTER TABLE schedule ADD COLUMN last_adjusted_at TIMESTAMP;
```

---

## Testing the Integration

### Test 09:45 Check
```python
# Run manually to test
from datetime import datetime, timedelta
from config.settings import IST

# Set current time to 09:45
mock_time = datetime(2026, 3, 18, 9, 45, tzinfo=IST)

# Mock punch records with some absent staff
punch_records = [
    PunchRecord("SENIOR_01", None, mock_time.date(), AssistantStatus.ABSENT),
    PunchRecord("JUNIOR_02", mock_time - timedelta(minutes=10), mock_time.date(), AssistantStatus.PRESENT),
]

# Run adjustment
engine = AutoAllotmentEngine(staff_master)
re_allotted, alerts = engine.realtime_09_45_adjustment(punch_records, mock_time)

# Verify no critical gaps
critical = [a for a in alerts if a['type'] == 'CRITICAL_Senior_Gap']
assert len(critical) == 0, "Critical senior gap detected!"
```

### Test Emergency Booking
```python
from datetime import datetime
from config.settings import IST

emergency_proc = Procedure(
    procedure_id="EMERGENCY_TEST",
    doctor_id="DR_SHARMA",
    dept_id=3,
    scheduled_start=datetime.now(IST),
    estimated_duration=60,
    required_assistants=2
)

success, alloc, alerts = engine.handle_emergency_procedure(emergency_proc)
assert success, f"Emergency allocation failed: {alerts}"
assert len(alloc['assigned']) >= 1, "No assistants allocated"
```

---

## Monitoring & Alerts

### Key Metrics to Track
1. **Shortage Rate**: % of procedures with insufficient staff
2. **Replacement Success**: % of replacements found for absent staff
3. **Critical Gaps**: Count of procedures without senior assistants
4. **Cascade Failures**: Count of cascade re-allocations that failed
5. **Emergency Response Time**: Time from booking to allocation

### Alert Thresholds
- ⚠️ **Warning**: >20% shortage rate
- 🚨 **Critical**: Any procedure without senior assistant
- 🔴 **Emergency**: >2 cascade failures in an hour

---

## Performance Considerations

For large datasets (1000+ procedures/day):
- **Pre-scheduling**: ~50ms per department
- **09:45 adjustment**: ~100ms for 200+ procedures
- **Emergency handling**: ~30ms per procedure

Optimize with:
- Index on `(dept_id, rank)` for quick staff lookups
- Cache staff master (refresh hourly)
- Batch process adjustments instead of per-procedure

---

## Rollback Plan

If algorithm causes issues:

1. **Revert to Manual Allocation**
   - Set allocation_phase to "Manual" in UI
   - Doctors can override allocations
   - Fall back to existing `allocate_for_slot()` function

2. **Disable 09:45 Check**
   - Remove hook from settings.json
   - Allocations stay at Phase 1 level

3. **Revert Changes**
   ```bash
   git revert <commit-hash>
   ```

---

## Support & Debugging

**Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check Allocation Logs:**
```sql
SELECT * FROM allotment_history
WHERE DATE(allocated_at) = CURDATE()
ORDER BY allocated_at DESC;
```

**View Current Status:**
```python
engine = AutoAllotmentEngine(staff_master)
for proc_id, proc in engine.procedures.items():
    print(f"{proc_id}: {proc.status.value} -> {proc.assigned_assistants}")
```

---

## Next Steps

1. ✅ Test locally → Complete
2. → Integrate data layer
3. → Add 09:45 hook
4. → Test with real data
5. → Deploy to staging
6. → Monitor metrics
7. → Full production rollout
