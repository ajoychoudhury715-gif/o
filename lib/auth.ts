import type { AuthSession } from './types';

const AUTH_STORAGE_KEY = 'tdb_auth_session';

export function getStoredSession(): AuthSession | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const rawSession = localStorage.getItem(AUTH_STORAGE_KEY);
  if (!rawSession) {
    return null;
  }

  try {
    return JSON.parse(rawSession) as AuthSession;
  } catch {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    return null;
  }
}

export function storeSession(session: AuthSession): void {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}

export function clearStoredSession(): void {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.removeItem(AUTH_STORAGE_KEY);
}

export function getAuthToken(): string | null {
  return getStoredSession()?.token ?? null;
}

export function isAuthenticated(): boolean {
  return getStoredSession() !== null;
}
