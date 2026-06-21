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

export async function getDistinctParameterValues(
  projectId: string,
  domain: string,
  key: string,
  groups: string[] = [],
): Promise<string[]> {
  const url = `${API_URL}/api/projects/${projectId}/parameter-values`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain, key, groups }),
  });
  if (!response.ok) throw new Error('Failed to fetch parameter values');
  return response.json();
}

// Recipe slot operations

export async function createRecipeSlot(
  projectId: string,
  recipeId: string,
  kind: string,
  sortOrder: number = 0,
): Promise<any> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/recipes/${recipeId}/slots`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ kind, sort_order: sortOrder }),
  });
  if (!response.ok) throw new Error('Failed to create recipe slot');
  return response.json();
}

export async function createRecipeOption(
  projectId: string,
  recipeId: string,
  slotId: string,
  quantity: number,
  sortOrder: number = 0,
): Promise<any> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/recipes/${recipeId}/slots/${slotId}/options`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quantity, sort_order: sortOrder }),
  });
  if (!response.ok) throw new Error('Failed to create recipe option');
  return response.json();
}

export async function createRecipeConstraint(
  projectId: string,
  recipeId: string,
  slotId: string,
  optionId: string,
  constraint: {
    domain: string;
    key: string;
    operator: string;
    value_string?: string | null;
    value_number?: number | null;
    value_boolean?: boolean | null;
    is_wildcard?: boolean;
  },
): Promise<any> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/recipes/${recipeId}/slots/${slotId}/options/${optionId}/constraints`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(constraint),
  });
  if (!response.ok) throw new Error('Failed to create recipe constraint');
  return response.json();
}

export async function getRecipeSlots(projectId: string, recipeId: string): Promise<any[]> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/recipes/${recipeId}/slots`);
  if (!response.ok) throw new Error('Failed to fetch recipe slots');
  return response.json();
}

export async function getRecipeOptions(projectId: string, recipeId: string, slotId: string): Promise<any[]> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/recipes/${recipeId}/slots/${slotId}/options`);
  if (!response.ok) throw new Error('Failed to fetch recipe options');
  return response.json();
}

export async function getRecipeConstraints(projectId: string, recipeId: string, slotId: string, optionId: string): Promise<any[]> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/recipes/${recipeId}/slots/${slotId}/options/${optionId}/constraints`);
  if (!response.ok) throw new Error('Failed to fetch recipe constraints');
  return response.json();
}

export async function deleteRecipeSlot(projectId: string, recipeId: string, slotId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/recipes/${recipeId}/slots/${slotId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete recipe slot');
}

export async function deleteRecipeOption(projectId: string, recipeId: string, slotId: string, optionId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/recipes/${recipeId}/slots/${slotId}/options/${optionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete recipe option');
}

export async function deleteRecipeConstraint(projectId: string, recipeId: string, slotId: string, optionId: string, constraintId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/recipes/${recipeId}/slots/${slotId}/options/${optionId}/constraints/${constraintId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete recipe constraint');
}
