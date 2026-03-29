// Auth types
export interface User {
  id: string
  username: string
  role: 'admin' | 'frontdesk' | 'assistant' | 'doctor'
  isActive: boolean
  createdAt: string
}

export interface AuthToken {
  user: username
  exp: number
  role: string
}

export interface AuthSession {
  user: User | null
  isAuthenticated: boolean
  token: string | null
}

export interface LoginCredentials {
  username: string
  password: string
}
