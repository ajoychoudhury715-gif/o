// Duty types
export type DutyFrequency = 'WEEKLY' | 'MONTHLY'
export type DutyStatus = 'IN_PROGRESS' | 'DONE' | 'PENDING'

export interface Duty {
  id: string
  name: string
  description?: string
  frequency: DutyFrequency
  durationMinutes: number
  isActive: boolean
  createdAt: string
}

export interface DutyAssignment {
  id: string
  dutyId: string
  assistant: string
  op: string
  estMinutes: number
  isActive: boolean
  createdAt: string
}

export interface DutyRun {
  id: string
  date: string
  assistant: string
  dutyId: string
  status: DutyStatus
  startedAt: string | null
  dueAt: string
  endedAt: string | null
  estMinutes: number
  createdAt: string
}
