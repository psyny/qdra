import { Material, MaterialParameter, CreateMaterialRequest } from '../types/material';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getMaterials(projectId: string): Promise<Material[]> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/materials`);
  if (!response.ok) {
    throw new Error('Failed to fetch materials');
  }
  return response.json();
}

export async function getMaterial(projectId: string, materialId: string): Promise<Material> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/materials/${materialId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch material');
  }
  return response.json();
}

export async function createMaterial(projectId: string, payload: CreateMaterialRequest): Promise<Material> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/materials`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error('Failed to create material');
  }
  return response.json();
}

export async function deleteMaterial(projectId: string, materialId: string): Promise<void> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/materials/${materialId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete material');
  }
}

export async function addMaterialParameter(
  projectId: string,
  materialId: string,
  param: { domain: string; key: string; value_string?: string | null; value_number?: number | null; value_boolean?: boolean | null },
): Promise<MaterialParameter> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/materials/${materialId}/parameters`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(param),
  });
  if (!response.ok) {
    throw new Error('Failed to add material parameter');
  }
  return response.json();
}

export async function getMaterialParameters(projectId: string, materialId: string): Promise<MaterialParameter[]> {
  const response = await fetch(`${API_URL}/api/projects/${projectId}/materials/${materialId}/parameters`);
  if (!response.ok) {
    throw new Error('Failed to fetch material parameters');
  }
  return response.json();
}
