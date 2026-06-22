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

export interface ConstraintSpec {
  domain: string;
  key: string;
  operator: string;
  value_string?: string;
  value_number?: number;
  value_boolean?: boolean;
  is_wildcard?: boolean;
}

export interface TargetSpec {
  quantity: number;
  target_type: string;
  constraints: ConstraintSpec[];
}

export interface ConstraintRule {
  constraints: ConstraintSpec[];
}

export interface DomainConstraints {
  do_not_expand_materials_matching: ConstraintRule[];
  forbidden_materials_matching: ConstraintRule[];
  forbidden_recipe_matching: ConstraintRule[];
  required_materials_matching: ConstraintRule[];
  required_recipe_matching: ConstraintRule[];
  max_recipe_depth: number;
  allow_partial_recipe_execution: boolean;
}

export interface SearchParameters {
  max_recursion_depth: number;
  max_branch_width: number;
  allow_loops: boolean;
  max_solutions_returned: number;
  optimization_level: number;
}

export interface UserVariableDef {
  name: string;
  parameter_domain: string;
  parameter_key: string;
  constraints: ConstraintRule[];
}

export interface ScoreFormulaDef {
  name: string;
  formula: string;
}

export interface ScoreRules {
  user_variables: UserVariableDef[];
  score_formulas: ScoreFormulaDef[];
}

export async function createOutputSolverRun(data: {
  project_id: string;
  target: TargetSpec;
  domain_constraints?: DomainConstraints;
  search_parameters?: SearchParameters;
  score_rules?: ScoreRules;
  name?: string;
}): Promise<PlanningRunWithResults> {
  const response = await fetch(`${API_URL}/api/planning-runs/output-solver/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error('Failed to create output solver run');
  }
  return response.json();
}
