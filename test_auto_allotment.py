#!/usr/bin/env python3
"""
Auto-Allotment Algorithm Test Suite
Tests the dynamic assistant allocation logic with realistic scenarios
"""

import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Set
from enum import Enum
import sys

# ─── ENUM DEFINITIONS ────────────────────────────────────────────────────────

class Rank(Enum):
    SENIOR = "Senior_Assistant"
    JUNIOR = "Junior_Assistant"

class StaffStatus(Enum):
    ACTIVE = "Active"
    WEEK_OFF = "Week_Off"
    LEAVE = "Leave"
    TERMINATED = "Terminated"

class AssistantStatus(Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"

class ProcedureStatus(Enum):
    SCHEDULED = "Scheduled"
    PROVISIONALLY_ALLOTTED = "Provisionally_Allotted"
    CONFIRMED_ALLOTMENT = "Confirmed_Allotment"
    IN_PROGRESS = "In_Progress"
    EXTENDED = "Extended"
    COMPLETED = "Completed"
    CRITICAL_INTERVENTION = "Manual_Intervention_Required"

# ─── DATA MODELS ─────────────────────────────────────────────────────────────

@dataclass
class Staff:
    assistant_id: str
    name: str
    dept_id: int
    rank: Rank
    staff_status: StaffStatus
    current_hours_scheduled: float = 0.0

@dataclass
class Procedure:
    procedure_id: str
    doctor_id: str
    dept_id: int
    scheduled_start: datetime
    estimated_duration: int  # minutes
    required_assistants: int = 2
    assigned_assistants: List[str] = None
    status: ProcedureStatus = ProcedureStatus.SCHEDULED
    current_end_time: Optional[datetime] = None

    def __post_init__(self):
        if self.assigned_assistants is None:
            self.assigned_assistants = []
        if self.current_end_time is None:
            self.current_end_time = self.scheduled_start + timedelta(minutes=self.estimated_duration)

    @property
    def estimated_end(self):
        return self.scheduled_start + timedelta(minutes=self.estimated_duration)

@dataclass
class PunchRecord:
    assistant_id: str
    punch_in_time: Optional[datetime]
    punch_date: datetime.date
    status: AssistantStatus = AssistantStatus.PRESENT

@dataclass
class AvailableStaffItem:
    assistant_id: str
    dept_id: int
    rank: Rank
    current_scheduled_hours: float
    current_status: str  # 'Free', 'In_Procedure', 'Unavailable'
    last_punch_in: Optional[datetime]

# ─── ALGORITHM IMPLEMENTATION ────────────────────────────────────────────────

class AutoAllotmentEngine:
    """Core auto-allotment algorithm engine"""

    def __init__(self, staff_master: List[Staff]):
        self.staff_master = {s.assistant_id: s for s in staff_master}
        self.procedures: Dict[str, Procedure] = {}
        self.punch_records: Dict[str, PunchRecord] = {}
        self.available_pool: Dict[str, AvailableStaffItem] = {}
        self.logs = []

    def log(self, message: str, level: str = "INFO"):
        """Log algorithm decisions"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{level}] {message}"
        self.logs.append(log_msg)
        print(log_msg)

    # ─── PHASE 1: PRE-SCHEDULING (T-1 Day) ───────────────────────────────────

    def provisional_allotment(self, procedures_list: List[Procedure]) -> Dict[str, List[str]]:
        """Build provisional allotment for tomorrow's procedures"""
        self.log("=== PHASE 1: PROVISIONAL ALLOTMENT ===")
        provisional = {}
        shortages = []

        # Filter eligible staff (exclude week-off, leave, terminated)
        eligible_staff = [
            s for s in self.staff_master.values()
            if s.staff_status == StaffStatus.ACTIVE
        ]
        self.log(f"Eligible staff: {len(eligible_staff)}/{len(self.staff_master)}")

        # Group by department
        dept_pools = {}
        for staff in eligible_staff:
            if staff.dept_id not in dept_pools:
                dept_pools[staff.dept_id] = {'seniors': [], 'juniors': []}
            if staff.rank == Rank.SENIOR:
                dept_pools[staff.dept_id]['seniors'].append(staff)
            else:
                dept_pools[staff.dept_id]['juniors'].append(staff)

        # Process each procedure
        for proc in procedures_list:
            self.log(f"\nAllocating for Procedure {proc.procedure_id} (Dept {proc.dept_id})")

            dept_staff = dept_pools.get(proc.dept_id, {'seniors': [], 'juniors': []})
            seniors = dept_staff['seniors']
            juniors = dept_staff['juniors']

            assigned = []

            # Allocate Senior (MANDATORY)
            senior_available = self._find_available_staff(
                seniors, proc.scheduled_start, proc.estimated_end, count=1
            )

            if senior_available:
                assigned.append(senior_available[0].assistant_id)
                self.log(f"  ✓ Senior assigned: {senior_available[0].name}")
            else:
                shortage = {
                    'type': 'Senior_Shortage',
                    'procedure_id': proc.procedure_id,
                    'dept_id': proc.dept_id
                }
                shortages.append(shortage)
                self.log(f"  ✗ NO SENIOR AVAILABLE (SHORTAGE)")

            # Allocate Juniors
            required_juniors = proc.required_assistants - 1
            available_juniors = self._find_available_staff(
                juniors, proc.scheduled_start, proc.estimated_end,
                count=required_juniors, sort_by_load=True
            )

            for junior in available_juniors:
                assigned.append(junior.assistant_id)
                self.log(f"  ✓ Junior assigned: {junior.name} ({junior.current_hours_scheduled}h)")

            if len(assigned) < proc.required_assistants:
                shortage = {
                    'type': 'Junior_Shortage',
                    'procedure_id': proc.procedure_id,
                    'dept_id': proc.dept_id,
                    'required': proc.required_assistants,
                    'assigned': len(assigned)
                }
                shortages.append(shortage)
                self.log(f"  ⚠ Insufficient juniors: need {required_juniors}, got {len(available_juniors)}")

            proc.assigned_assistants = assigned
            proc.status = ProcedureStatus.PROVISIONALLY_ALLOTTED
            provisional[proc.procedure_id] = assigned
            self.procedures[proc.procedure_id] = proc

        if shortages:
            self.log(f"\n⚠ Shortages detected: {len(shortages)}")
            for s in shortages:
                self.log(f"  - {s['type']}: {s}")

        return provisional

    def _find_available_staff(
        self,
        staff_list: List[Staff],
        start_time: datetime,
        end_time: datetime,
        count: Optional[int] = None,
        sort_by_load: bool = False
    ) -> List[Staff]:
        """Find available staff with no time conflicts"""
        # Simple implementation: all are available if in list
        available = staff_list[:count] if count else staff_list

        if sort_by_load:
            available = sorted(available, key=lambda s: s.current_hours_scheduled)

        return available

    # ─── PHASE 2: 09:45 REAL-TIME ADJUSTMENT ─────────────────────────────────

    def realtime_09_45_adjustment(
        self,
        punch_records: List[PunchRecord],
        threshold_time: datetime
    ) -> tuple[Dict[str, List[str]], List[Dict]]:
        """
        Adjust allocations based on punch-in records at 09:45 AM
        threshold_time: typically 09:45 on the day
        """
        self.log("\n=== PHASE 2: 09:45 REAL-TIME ADJUSTMENT ===")
        self.punch_records = {p.assistant_id: p for p in punch_records}

        re_allotted = {}
        critical_alerts = []

        # Filter today's procedures
        today_procedures = [
            p for p in self.procedures.values()
            if p.status == ProcedureStatus.PROVISIONALLY_ALLOTTED
        ]

        for proc in today_procedures:
            self.log(f"\nChecking Procedure {proc.procedure_id}")

            replacement_needed = []
            present_assistants = []

            # Check each assigned assistant's punch status
            for asst_id in proc.assigned_assistants:
                punch = self.punch_records.get(asst_id)

                if punch is None or punch.punch_in_time is None:
                    status = AssistantStatus.ABSENT
                elif punch.punch_in_time > threshold_time:
                    status = AssistantStatus.LATE
                else:
                    status = AssistantStatus.PRESENT

                self.log(f"  {asst_id}: {status.value}")

                if status != AssistantStatus.PRESENT:
                    asst = self.staff_master[asst_id]
                    replacement_needed.append({
                        'absent_id': asst_id,
                        'required_rank': asst.rank,
                        'dept_id': proc.dept_id
                    })
                else:
                    present_assistants.append(asst_id)

            # Try to find replacements
            for repl_req in replacement_needed:
                replacement = self._find_replacement(
                    repl_req['required_rank'],
                    repl_req['dept_id'],
                    proc,
                    exclude_ids=set(present_assistants + [r['absent_id'] for r in replacement_needed])
                )

                if replacement:
                    present_assistants.append(replacement.assistant_id)
                    self.log(f"    → Replacement found: {replacement.name}")
                else:
                    critical_alerts.append({
                        'type': 'Replacement_Failed',
                        'procedure_id': proc.procedure_id,
                        'absent_id': repl_req['absent_id'],
                        'required_rank': repl_req['required_rank'].value
                    })
                    self.log(f"    ✗ No replacement available for {repl_req['absent_id']}")

            # CHECK HIERARCHY RULE
            proc.assigned_assistants = present_assistants
            senior_count = sum(
                1 for asst_id in present_assistants
                if self.staff_master[asst_id].rank == Rank.SENIOR
            )

            if senior_count < 1:
                critical_alerts.append({
                    'type': 'CRITICAL_Senior_Gap',
                    'procedure_id': proc.procedure_id,
                    'severity': 'ESCALATE_TO_ADMIN'
                })
                proc.status = ProcedureStatus.CRITICAL_INTERVENTION
                self.log(f"  🚨 CRITICAL: No senior assistant available!")
            else:
                proc.status = ProcedureStatus.CONFIRMED_ALLOTMENT
                self.log(f"  ✓ Hierarchy check passed ({senior_count} senior)")

            re_allotted[proc.procedure_id] = present_assistants

        return re_allotted, critical_alerts

    def _find_replacement(
        self,
        required_rank: Rank,
        dept_id: int,
        proc: Procedure,
        exclude_ids: Set[str]
    ) -> Optional[Staff]:
        """Find a replacement staff member"""
        # Simple implementation: find first available staff with required rank
        candidates = [
            s for s in self.staff_master.values()
            if s.dept_id == dept_id
            and s.staff_status == StaffStatus.ACTIVE
            and s.assistant_id not in exclude_ids
            and s.rank == required_rank
        ]

        if candidates:
            # Return least busy
            return min(candidates, key=lambda s: s.current_hours_scheduled)

        return None

    # ─── PHASE 3: INTRA-DAY DYNAMIC SCALING ──────────────────────────────────

    def handle_emergency_procedure(
        self,
        new_proc: Procedure,
        current_time: datetime
    ) -> tuple[bool, Dict, List[str]]:
        """
        Handle new emergency procedure with immediate allocation
        Returns: (success, allocation, alerts)
        """
        self.log(f"\n=== EMERGENCY: New Procedure {new_proc.procedure_id} ===")

        available_candidates = self._scan_available_pool(
            dept_id=new_proc.dept_id,
            available_at=new_proc.scheduled_start,
            required_count=new_proc.required_assistants
        )

        self.log(f"Available candidates: {len(available_candidates)}")

        # Check if we have enough seniors
        seniors_available = [
            c for c in available_candidates if c['rank'] == Rank.SENIOR
        ]

        if len(seniors_available) < 1:
            self.log("✗ No seniors available for emergency")
            return False, {}, ["No_Senior_Available"]

        # Assign in FIFO order (least busy first)
        assigned = []
        for candidate in available_candidates[:new_proc.required_assistants]:
            assigned.append(candidate['assistant_id'])

        self.log(f"✓ Assigned {len(assigned)} assistants")
        new_proc.assigned_assistants = assigned
        new_proc.status = ProcedureStatus.CONFIRMED_ALLOTMENT

        return True, {'assigned': assigned}, []

    def _scan_available_pool(
        self,
        dept_id: int,
        available_at: datetime,
        required_count: int
    ) -> List[Dict]:
        """Scan available pool for staff"""
        available = []

        for staff_id, staff in self.staff_master.items():
            if staff.dept_id != dept_id or staff.staff_status != StaffStatus.ACTIVE:
                continue

            # Assume staff is available if not in a procedure
            available.append({
                'assistant_id': staff_id,
                'rank': staff.rank,
                'hours_scheduled': staff.current_hours_scheduled
            })

        # Sort: seniors first, then by least scheduled
        available.sort(key=lambda x: (x['rank'] != Rank.SENIOR, x['hours_scheduled']))

        return available[:required_count]

# ─── TEST SCENARIO SETUP ──────────────────────────────────────────────────────

def create_test_data():
    """Create realistic test data"""

    # Staff Master
    staff = [
        # Cardiology (Dept 3)
        Staff("S1", "Senior_S1", 3, Rank.SENIOR, StaffStatus.ACTIVE, 4.5),
        Staff("S2", "Senior_S2", 3, Rank.SENIOR, StaffStatus.ACTIVE, 3.0),
        Staff("S3", "Senior_S3", 3, Rank.SENIOR, StaffStatus.ACTIVE, 5.0),
        Staff("J1", "Junior_J1", 3, Rank.JUNIOR, StaffStatus.ACTIVE, 2.0),
        Staff("J2", "Junior_J2", 3, Rank.JUNIOR, StaffStatus.ACTIVE, 1.5),
        Staff("J3", "Junior_J3", 3, Rank.JUNIOR, StaffStatus.ACTIVE, 3.0),
        Staff("J4", "Junior_J4", 3, Rank.JUNIOR, StaffStatus.ACTIVE, 2.5),
        Staff("J5", "Junior_J5", 3, Rank.JUNIOR, StaffStatus.ACTIVE, 1.0),
        Staff("J6", "Junior_J6", 3, Rank.JUNIOR, StaffStatus.ACTIVE, 2.0),

        # Orthopedics (Dept 5)
        Staff("S4", "Senior_S4", 5, Rank.SENIOR, StaffStatus.ACTIVE, 4.0),
        Staff("J7", "Junior_J7", 5, Rank.JUNIOR, StaffStatus.ACTIVE, 2.5),
    ]

    # Procedures for today
    base_time = datetime(2026, 3, 18, 10, 0)  # Today 10:00 AM
    procedures = [
        Procedure("PROC_A", "DR_SHARMA", 3, base_time, 60, 3),
        Procedure("PROC_C", "DR_PATEL", 3, base_time + timedelta(minutes=135), 45, 2),
        Procedure("PROC_D", "DR_GUPTA", 3, base_time + timedelta(minutes=210), 50, 2),
        Procedure("PROC_B_EMERGENCY", "DR_VERMA", 3, base_time + timedelta(minutes=50), 60, 3),
    ]

    # Punch records at 09:45 AM
    punch_time = datetime(2026, 3, 18, 9, 45)
    punch_records = [
        # S1 ABSENT (triggers cascade)
        PunchRecord("S1", None, punch_time.date(), AssistantStatus.ABSENT),
        # Others present
        PunchRecord("S2", punch_time - timedelta(minutes=10), punch_time.date(), AssistantStatus.PRESENT),
        PunchRecord("S3", punch_time - timedelta(minutes=5), punch_time.date(), AssistantStatus.PRESENT),
        PunchRecord("J1", punch_time - timedelta(minutes=20), punch_time.date(), AssistantStatus.PRESENT),
        PunchRecord("J2", punch_time - timedelta(minutes=15), punch_time.date(), AssistantStatus.PRESENT),
        PunchRecord("J3", punch_time - timedelta(minutes=10), punch_time.date(), AssistantStatus.PRESENT),
        PunchRecord("J4", punch_time - timedelta(minutes=8), punch_time.date(), AssistantStatus.PRESENT),
        PunchRecord("J5", punch_time - timedelta(minutes=25), punch_time.date(), AssistantStatus.PRESENT),
        PunchRecord("J6", punch_time - timedelta(minutes=5), punch_time.date(), AssistantStatus.PRESENT),
    ]

    return staff, procedures, punch_records

# ─── MAIN TEST EXECUTION ─────────────────────────────────────────────────────

def main():
    print("\n" + "="*80)
    print("AUTO-ALLOTMENT ALGORITHM - LOCAL TEST SUITE")
    print("="*80)

    # Setup
    staff, procedures, punch_records = create_test_data()
    engine = AutoAllotmentEngine(staff)
    punch_time = datetime(2026, 3, 18, 9, 45)

    # ─── SCENARIO: Senior Absent + Emergency Procedure ─────────────────────────
    print("\n### SCENARIO: Senior Assistant Absent @ 09:45 + Emergency Booking ###\n")

    # PHASE 1: Provisional Allotment
    print("\n>>> PHASE 1: Pre-Scheduling (T-1 Day)")
    print("-" * 80)
    provisional = engine.provisional_allotment(procedures[:3])  # First 3 procedures

    print("\nProvisional Allotment Summary:")
    for proc_id, assigned in provisional.items():
        proc = engine.procedures[proc_id]
        print(f"  {proc_id}: {assigned}")

    # PHASE 2: 09:45 Adjustment
    print("\n>>> PHASE 2: 09:45 Real-Time Adjustment")
    print("-" * 80)
    re_allotted, critical = engine.realtime_09_45_adjustment(punch_records, punch_time)

    print("\nRe-allotted Schedule:")
    for proc_id, assigned in re_allotted.items():
        proc = engine.procedures[proc_id]
        print(f"  {proc_id}: {assigned} [Status: {proc.status.value}]")

    if critical:
        print("\n🚨 CRITICAL ALERTS:")
        for alert in critical:
            print(f"  - {alert}")

    # PHASE 3: Emergency Booking at 09:50
    print("\n>>> PHASE 3: Emergency Procedure @ 09:50 AM")
    print("-" * 80)
    emergency_proc = procedures[3]  # PROC_B_EMERGENCY
    success, alloc, alerts = engine.handle_emergency_procedure(
        emergency_proc,
        punch_time + timedelta(minutes=5)
    )

    if success:
        print(f"✓ Emergency allocation successful: {alloc['assigned']}")
    else:
        print(f"✗ Emergency allocation FAILED: {alerts}")

    # ─── FINAL REPORT ────────────────────────────────────────────────────────

    print("\n" + "="*80)
    print("FINAL ALLOCATION REPORT")
    print("="*80)

    print("\nProcedure Status Summary:")
    for proc_id, proc in engine.procedures.items():
        print(f"\n{proc_id}:")
        print(f"  Doctor: {proc.doctor_id}")
        print(f"  Time: {proc.scheduled_start.strftime('%H:%M')} - {proc.estimated_end.strftime('%H:%M')}")
        print(f"  Assigned: {proc.assigned_assistants}")
        print(f"  Status: {proc.status.value}")

        # Validate hierarchy
        senior_count = sum(
            1 for aid in proc.assigned_assistants
            if engine.staff_master[aid].rank == Rank.SENIOR
        )
        print(f"  Seniors: {senior_count}/1 {'✓' if senior_count >= 1 else '✗'}")

    # Logs
    print("\n" + "="*80)
    print("EXECUTION LOGS")
    print("="*80)
    for log in engine.logs:
        print(log)

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
