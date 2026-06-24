import { Project, CreateProjectRequest, UpdateProjectRequest } from '../types/project';
import { ProjectTemplateDetail } from '../types/template';
import { getToken } from './auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export async function getProjects(): Promise<Project[]> {
  const response = await fetch(`${API_URL}/api/projects`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch projects');
  }
  return response.json();
}

export async function getProject(projectId: string): Promise<Project> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch project');
  }
  return response.json();
}

export async function getProjectTemplate(projectId: string): Promise<ProjectTemplateDetail> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/template`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error('Failed to fetch project template');
  }
  return response.json();
}

export async function createProject(payload: CreateProjectRequest): Promise<Project> {
  const response = await fetch(`${API_URL}/api/projects`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error('Failed to create project');
  }
  return response.json();
}

export async function updateProject(projectId: string, payload: UpdateProjectRequest): Promise<Project> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error('Failed to update project');
  }
  return response.json();
}
