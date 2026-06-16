import { ProjectTemplate, CreateTemplateRequest, CloneTemplateRequest } from '../types/template';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getTemplates(): Promise<ProjectTemplate[]> {
  const response = await fetch(`${API_URL}/project-templates`);
  if (!response.ok) {
    throw new Error('Failed to fetch templates');
  }
  return response.json();
}

export async function createTemplate(payload: CreateTemplateRequest): Promise<ProjectTemplate> {
  const response = await fetch(`${API_URL}/project-templates`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error('Failed to create template');
  }
  return response.json();
}

export async function deleteTemplate(templateId: string): Promise<void> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    if (response.status === 409) {
      throw new Error('Cannot delete template because it is used by one or more projects.');
    }
    throw new Error('Failed to delete template');
  }
}

export async function cloneTemplate(templateId: string, payload: CloneTemplateRequest): Promise<ProjectTemplate> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}/clone`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error('Failed to clone template');
  }
  return response.json();
}
