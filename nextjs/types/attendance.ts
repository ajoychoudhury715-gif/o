// Attendance types
export interface AttendanceRecord {
  id: string
  date: string
  assistant: string
  punchIn: string | null
  punchOut: string | null
  duration?: number // in minutes
  createdAt: string
  updatedAt: string
}

export interface PunchAction {
  type: 'in' | 'out'
  timestamp: string
}
