const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
import { getToken } from './auth';

export interface User {
  id: string;
  login_name: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export interface UserCreate {
  login_name: string;
  password: string;
  display_name: string;
}

export interface UserUpdate {
  login_name?: string;
  display_name?: string;
  password?: string;
  is_active?: boolean;
}

export interface UserAppPermissions {
  user_id: string;
  can_manage_users: boolean;
  can_create_projects: boolean;
  can_edit_projects: boolean;
  can_delete_projects: boolean;
  can_create_templates: boolean;
  can_edit_templates: boolean;
  can_delete_templates: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserAppPermissionsUpdate {
  can_manage_users?: boolean;
  can_create_projects?: boolean;
  can_edit_projects?: boolean;
  can_delete_projects?: boolean;
  can_create_templates?: boolean;
  can_edit_templates?: boolean;
  can_delete_templates?: boolean;
}

export interface ProjectUserPermissions {
  id: string;
  user_id: string;
  project_id: string;
  can_manage_project_users: boolean;
  can_create_material: boolean;
  can_edit_material: boolean;
  can_delete_material: boolean;
  can_create_recipe: boolean;
  can_edit_recipe: boolean;
  can_delete_recipe: boolean;
  can_run_plan: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectUserPermissionsUpdate {
  can_manage_project_users?: boolean;
  can_create_material?: boolean;
  can_edit_material?: boolean;
  can_delete_material?: boolean;
  can_create_recipe?: boolean;
  can_edit_recipe?: boolean;
  can_delete_recipe?: boolean;
  can_run_plan?: boolean;
}

async function getHeaders() {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function getUsers(includeInactive: boolean = false): Promise<User[]> {
  const headers = await getHeaders();
  const response = await fetch(`${API_URL}/api/users?include_inactive=${includeInactive}`, {
    headers,
  });
  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }
  return response.json();
}

export async function getUser(userId: string): Promise<User> {
  const headers = await getHeaders();
  const response = await fetch(`${API_URL}/api/users/${userId}`, {
    headers,
  });
  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }
  return response.json();
}

export async function createUser(userData: UserCreate): Promise<User> {
  const headers = await getHeaders();
  const response = await fetch(`${API_URL}/api/users`, {
    method: 'POST',
    headers,
    body: JSON.stringify(userData),
  });
  if (!response.ok) {
    throw new Error('Failed to create user');
  }
  return response.json();
}

export async function updateUser(userId: string, userData: UserUpdate): Promise<User> {
  const headers = await getHeaders();
  const response = await fetch(`${API_URL}/api/users/${userId}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(userData),
  });
  if (!response.ok) {
    throw new Error('Failed to update user');
  }
  return response.json();
}

export async function resetPassword(userId: string, newPassword: string): Promise<void> {
  const headers = await getHeaders();
  const response = await fetch(`${API_URL}/api/users/${userId}/reset-password`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ new_password: newPassword }),
  });
  if (!response.ok) {
    throw new Error('Failed to reset password');
  }
}

export async function getUserPermissions(userId: string): Promise<UserAppPermissions> {
  const headers = await getHeaders();
  const response = await fetch(`${API_URL}/api/users/${userId}/permissions`, {
    headers,
  });
  if (!response.ok) {
    throw new Error('Failed to fetch user permissions');
  }
  return response.json();
}

export async function updateUserPermissions(
  userId: string,
  permissions: UserAppPermissionsUpdate
): Promise<UserAppPermissions> {
  const headers = await getHeaders();
  const response = await fetch(`${API_URL}/api/users/${userId}/permissions`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(permissions),
  });
  if (!response.ok) {
    throw new Error('Failed to update user permissions');
  }
  return response.json();
}

export async function listUserProjects(userId: string): Promise<ProjectUserPermissions[]> {
  const headers = await getHeaders();
  const response = await fetch(`${API_URL}/api/users/${userId}/projects`, {
    headers,
  });
  if (!response.ok) {
    throw new Error('Failed to fetch user projects');
  }
  return response.json();
}

export async function getUserProjectPermissions(userId: string, projectId: string): Promise<ProjectUserPermissions> {
  const headers = await getHeaders();
  const response = await fetch(`${API_URL}/api/users/${userId}/projects/${projectId}/permissions`, {
    headers,
  });
  if (!response.ok) {
    throw new Error('Failed to fetch project permissions');
  }
  return response.json();
}

export async function updateUserProjectPermissions(
  userId: string,
  projectId: string,
  permissions: ProjectUserPermissionsUpdate
): Promise<ProjectUserPermissions> {
  const headers = await getHeaders();
  const response = await fetch(`${API_URL}/api/users/${userId}/projects/${projectId}/permissions`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(permissions),
  });
  if (!response.ok) {
    throw new Error('Failed to update project permissions');
  }
  return response.json();
}
