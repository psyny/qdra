const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface PlanningRun {
  id: string;
  name: string | null;
  created_at: string;
  updated_at: string | null;
  status: string;
  type: string;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
}

export interface PlanningRunWithResults extends PlanningRun {
  input: any;
  result: any;
}

export async function listPlanningRuns(type?: string, status?: string): Promise<PlanningRun[]> {
  const params = new URLSearchParams();
  if (type) params.append('type', type);
  if (status) params.append('status', status);
  
  const response = await fetch(`${API_URL}/api/planning-runs?${params.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch planning runs');
  }
  return response.json();
}

export async function getPlanningRun(runId: string): Promise<PlanningRun> {
  const response = await fetch(`${API_URL}/api/planning-runs/${runId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch planning run');
  }
  return response.json();
}

export async function getPlanningRunWithResults(runId: string): Promise<PlanningRunWithResults> {
  const response = await fetch(`${API_URL}/api/planning-runs/${runId}/with-results`);
  if (!response.ok) {
    throw new Error('Failed to fetch planning run with results');
  }
  return response.json();
}

export async function createPlanningRun(data: {
  name?: string;
  type: string;
  status?: string;
  input?: any;
}): Promise<PlanningRunWithResults> {
  const response = await fetch(`${API_URL}/api/planning-runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create planning run');
  }
  return response.json();
}
