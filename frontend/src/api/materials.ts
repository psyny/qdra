import { Material } from '../types/material';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getMaterials(projectId: string): Promise<Material[]> {
  const response = await fetch(`${API_URL}/projects/${projectId}/materials`);
  if (!response.ok) {
    throw new Error('Failed to fetch materials');
  }
  return response.json();
}
