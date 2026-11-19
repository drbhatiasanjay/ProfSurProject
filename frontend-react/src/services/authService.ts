/**
 * Authentication and session service for LifeCycle Leverage React platform.
 * Communicates with FastAPI backend on port 8000.
 */

export interface AuthUser {
  id: string;
  username: string;
  name: string;
  email: string;
  role: 'admin' | 'researcher' | 'viewer';
}

export interface LoginResponse {
  success: boolean;
  token: string;
  user: AuthUser;
}

export interface SessionResponse {
  authenticated: boolean;
  user: AuthUser | null;
}

const API_BASE = 'http://localhost:8000';

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Invalid username or password.');
  }

  return res.json();
}

export async function validateSession(token: string): Promise<SessionResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/auth/session?token=${encodeURIComponent(token)}`);
    if (!res.ok) return { authenticated: false, user: null };
    return res.json();
  } catch {
    return { authenticated: false, user: null };
  }
}

export async function logout(token: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/api/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    });
  } catch (e) {
    console.error('Logout error:', e);
  }
}
