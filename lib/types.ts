// Utility types for authentication
export interface User {
  id: string;
  username: string;
  role: 'admin' | 'doctor' | 'assistant';
  email?: string;
}

export interface AuthToken {
  token: string;
  user: User;
}

export interface SessionState {
  currentUser: User | null;
  isAuthenticated: boolean;
  permissions: string[];
}
