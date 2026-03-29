// Legacy type (keeping for backward compatibility)
export interface AppointmentRecord {
  id: string;
  appointment_date: string;
  patient_name?: string;
  doctor?: string;
  status?: string;
  notes?: string;
}

// Schedule/Appointment types
export interface Appointment {
  id: string
  date: string
  patientId: string
  patientName: string
  inTime: string
  outTime: string
  procedure: string
  doctor: string
  first: string | null
  second: string | null
  third: string | null
  op: string
  status: AppointmentStatus
  reminderRowId: string | null
  reminderDismissed: boolean
  reminderSnoozeUntil: string | null
  statusChangedAt: string | null
  actualStartAt: string | null
  actualEndAt: string | null
  statusLog: string[] | null
  createdAt: string
  updatedAt: string
}

export type AppointmentStatus =
  | 'pending'
  | 'waiting'
  | 'arriving'
  | 'ongoing'
  | 'done'
  | 'cancelled'
  | 'shifted'

export interface AppointmentFilter {
  startDate?: string
  endDate?: string
  doctor?: string
  op?: string
  status?: AppointmentStatus
  pageSize?: number
  pageOffset?: number
}

