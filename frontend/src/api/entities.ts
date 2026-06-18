import { Entity, EntityParameter, CreateEntityRequest, AddParameterRequest } from '../types/entity';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getEntities(projectId: string, kind?: string): Promise<Entity[]> {
  const url = kind
    ? `${API_URL}/api/projects/${projectId}/entities?kind=${kind}`
    : `${API_URL}/api/projects/${projectId}/entities`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch entities');
  return response.json();
}

export async function getEntitiesByViewConfig(projectId: string, configId: string): Promise<Entity[]> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/view-configs/${configId}/entities`);
  if (!response.ok) throw new Error('Failed to fetch entities by view config');
  return response.json();
}

export async function getEntity(projectId: string, entityId: string): Promise<Entity> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/entities/${entityId}`);
  if (!response.ok) throw new Error('Failed to fetch entity');
  return response.json();
}

export async function createEntity(projectId: string, payload: CreateEntityRequest): Promise<Entity> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/entities`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create entity');
  return response.json();
}

export async function updateEntity(projectId: string, entityId: string, payload: { parameters?: any[] }): Promise<Entity> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/entities/${entityId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to update entity');
  return response.json();
}

export async function deleteEntity(projectId: string, entityId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/entities/${entityId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete entity');
}

export async function getEntityParameters(projectId: string, entityId: string): Promise<EntityParameter[]> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/entities/${entityId}/parameters`);
  if (!response.ok) throw new Error('Failed to fetch entity parameters');
  return response.json();
}

export async function addEntityParameter(
  projectId: string,
  entityId: string,
  param: AddParameterRequest,
): Promise<EntityParameter> {
  const response = await fetch(
    `${API_URL}/api/projects/${projectId}/entities/${entityId}/parameters`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(param),
    },
  );
  if (!response.ok) throw new Error('Failed to add entity parameter');
  return response.json();
}

export async function deleteEntityParameter(
  projectId: string,
  entityId: string,
  parameterId: string,
): Promise<void> {
  const response = await fetch(
    `${API_URL}/api/projects/${projectId}/entities/${entityId}/parameters/${parameterId}`,
    { method: 'DELETE' },
  );
  if (!response.ok) throw new Error('Failed to delete entity parameter');
}
