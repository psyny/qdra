import { Material, CreateMaterialRequest, UpdateMaterialRequest } from '../types/material';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getMaterials(projectId: string): Promise<Material[]> {
  const response = await fetch(`${API_URL}/projects/${projectId}/materials`);
  if (!response.ok) {
    throw new Error('Failed to fetch materials');
  }
  return response.json();
}

export async function getMaterial(projectId: string, materialId: string): Promise<Material> {
  const response = await fetch(`${API_URL}/projects/${projectId}/materials/${materialId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch material');
  }
  return response.json();
}

export async function createMaterial(projectId: string, payload: CreateMaterialRequest): Promise<Material> {
  const response = await fetch(`${API_URL}/projects/${projectId}/materials`, {
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

export async function updateMaterial(projectId: string, materialId: string, payload: UpdateMaterialRequest): Promise<Material> {
  const response = await fetch(`${API_URL}/projects/${projectId}/materials/${materialId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error('Failed to update material');
  }
  return response.json();
}
