const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface View {
  id: string;
  project_template_id: string;
  view_key: string;
  label: string;
  description: string | null;
  is_system: boolean;
  sort_order: number;
  configs: ViewConfig[];
  created_at: string;
  updated_at: string;
}

export interface ViewConfig {
  id: string;
  view_id: string;
  entity_type_id: string | null;
  filter_params: any[] | null;
  display_slots: any[] | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface CreateViewRequest {
  view_key: string;
  label: string;
  description?: string | null;
  sort_order?: number;
}

export interface UpdateViewRequest {
  view_key?: string;
  label?: string;
  description?: string | null;
  sort_order?: number;
}

export interface CreateViewConfigRequest {
  entity_type_id?: string | null;
  filter_params?: any[] | null;
  display_slots?: any[] | null;
  sort_order?: number;
}

export interface UpdateViewConfigRequest {
  entity_type_id?: string | null;
  filter_params?: any[] | null;
  display_slots?: any[] | null;
  sort_order?: number;
}

export async function getTemplateViews(templateId: string): Promise<View[]> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}/views`);
  if (!response.ok) throw new Error('Failed to fetch views');
  return response.json();
}

export async function createView(templateId: string, payload: CreateViewRequest): Promise<View> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}/views`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create view');
  return response.json();
}

export async function updateView(templateId: string, viewId: string, payload: UpdateViewRequest): Promise<View> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}/views/${viewId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to update view');
  return response.json();
}

export async function deleteView(templateId: string, viewId: string): Promise<void> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}/views/${viewId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    if (response.status === 403) {
      throw new Error('Cannot delete system views');
    }
    throw new Error('Failed to delete view');
  }
}

export async function seedSystemViews(templateId: string): Promise<View[]> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}/views/seed-system`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to seed system views');
  return response.json();
}

export async function createViewConfig(
  templateId: string,
  viewId: string,
  payload: CreateViewConfigRequest,
): Promise<ViewConfig> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}/views/${viewId}/configs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create view config');
  return response.json();
}

export async function updateViewConfig(
  templateId: string,
  viewId: string,
  configId: string,
  payload: UpdateViewConfigRequest,
): Promise<ViewConfig> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/views/${viewId}/configs/${configId}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) throw new Error('Failed to update view config');
  return response.json();
}

export async function deleteViewConfig(templateId: string, viewId: string, configId: string): Promise<void> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/views/${viewId}/configs/${configId}`,
    { method: 'DELETE' },
  );
  if (!response.ok) throw new Error('Failed to delete view config');
}
