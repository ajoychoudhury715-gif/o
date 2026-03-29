// Profile types
export type ProfileKind = 'Assistants' | 'Doctors'

export interface Profile {
  id: string
  name: string
  kind: ProfileKind
  role: string
  department: string
  phone?: string
  email?: string
  experience?: number
  weeklyOff?: number
  isActive: boolean
  specialisation?: string
  regNumber?: string
  canFirst?: boolean
  canSecond?: boolean
  canThird?: boolean
  createdAt: string
  updatedAt: string
}

export interface AssistantProfile extends Profile {
  kind: 'Assistants'
  preferences?: {
    first?: number
    second?: number
    third?: number
  }
}

export interface DoctorProfile extends Profile {
  kind: 'Doctors'
  specialisation: string
  regNumber: string
}
