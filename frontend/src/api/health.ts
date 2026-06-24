import { apiUrl } from './config';

export interface HealthResponse {
  status: string;
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(apiUrl('/health'));
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}
