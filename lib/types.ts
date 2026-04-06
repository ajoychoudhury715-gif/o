export type UserRole = 'admin' | 'frontdesk' | 'assistant' | 'doctor';

export interface User {
  id: string;
  username: string;
  role: UserRole;
  isActive: boolean;
  createdAt?: string;
  email?: string;
}

export interface AuthSession {
  token: string;
  user: User;
  authenticatedAt: string;
}

export interface SessionState {
  currentUser: User | null;
  isAuthenticated: boolean;
  permissions: string[];
}
