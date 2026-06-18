import { Project, CreateProjectRequest, UpdateProjectRequest } from '../types/project';
import { ProjectTemplateDetail } from '../types/template';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getProjects(): Promise<Project[]> {
  const response = await fetch(`${API_URL}/projects`);
  if (!response.ok) {
    throw new Error('Failed to fetch projects');
  }
  return response.json();
}

export async function getProject(projectId: string): Promise<Project> {
  const response = await fetch(`${API_URL}/projects/${projectId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch project');
  }
  return response.json();
}

export async function getProjectTemplate(projectId: string): Promise<ProjectTemplateDetail> {
  const response = await fetch(`${API_URL}/projects/${projectId}/template`);
  if (!response.ok) {
    throw new Error('Failed to fetch project template');
  }
  return response.json();
}

export async function createProject(payload: CreateProjectRequest): Promise<Project> {
  const response = await fetch(`${API_URL}/projects`, {
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
  const response = await fetch(`${API_URL}/projects/${projectId}`, {
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
