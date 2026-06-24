import { apiUrl } from './config';

export interface LoginRequest {
  login: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: {
    id: string;
    login: string;
    display_name: string;
  };
}

export interface CurrentUser {
  id: string;
  login: string;
  display_name: string;
  app_permissions: {
    can_manage_users: boolean;
    can_create_projects: boolean;
    can_edit_projects: boolean;
    can_delete_projects: boolean;
    can_create_templates: boolean;
    can_edit_templates: boolean;
    can_delete_templates: boolean;
  };
}

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(apiUrl('/api/auth/login'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });
  if (!response.ok) {
    throw new Error('Invalid credentials');
  }
  return response.json();
}

export async function getCurrentUser(token: string): Promise<CurrentUser> {
  const response = await fetch(apiUrl('/api/auth/me'), {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }
  return response.json();
}

export function setToken(token: string): void {
  localStorage.setItem('jwt_token', token);
}

export function getToken(): string | null {
  return localStorage.getItem('jwt_token');
}

export function clearToken(): void {
  localStorage.removeItem('jwt_token');
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}
