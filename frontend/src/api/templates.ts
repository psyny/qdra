import {
  ProjectTemplate,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  CloneTemplateRequest,
  ProjectTemplateDetail,
  EntityType,
  ParameterDefinition,
} from '../types/template';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getTemplates(): Promise<ProjectTemplate[]> {
  const response = await fetch(`${API_URL}/project-templates`);
  if (!response.ok) {
    throw new Error('Failed to fetch templates');
  }
  return response.json();
}

export async function getTemplate(templateId: string): Promise<ProjectTemplateDetail> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch template');
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

export async function updateTemplate(templateId: string, payload: UpdateTemplateRequest): Promise<ProjectTemplate> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error('Failed to update template');
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

export async function listEntityTypes(templateId: string, kind?: string): Promise<EntityType[]> {
  const url = kind
    ? `${API_URL}/project-templates/${templateId}/entity-types?kind=${kind}`
    : `${API_URL}/project-templates/${templateId}/entity-types`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch entity types');
  return response.json();
}

export async function createEntityType(
  templateId: string,
  payload: { kind: string; name: string; description?: string | null; sort_order?: number },
): Promise<EntityType> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}/entity-types`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create entity type');
  return response.json();
}

export async function updateEntityType(
  templateId: string,
  entityTypeId: string,
  payload: { name?: string; description?: string | null; sort_order?: number },
): Promise<EntityType> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/entity-types/${entityTypeId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) throw new Error('Failed to update entity type');
  return response.json();
}

export async function deleteEntityType(templateId: string, entityTypeId: string): Promise<void> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/entity-types/${entityTypeId}`,
    { method: 'DELETE' },
  );
  if (!response.ok) throw new Error('Failed to delete entity type');
}

export async function listParameterDefinitions(
  templateId: string,
  entityTypeId?: string,
): Promise<ParameterDefinition[]> {
  const url = entityTypeId
    ? `${API_URL}/project-templates/${templateId}/parameter-definitions?entity_type_id=${entityTypeId}`
    : `${API_URL}/project-templates/${templateId}/parameter-definitions`;
  const response = await fetch(url);
  if (!response.ok) throw new Error('Failed to fetch parameter definitions');
  return response.json();
}

export async function createParameterDefinition(
  templateId: string,
  payload: {
    entity_type_id: string;
    domain: string;
    key: string;
    value_type: string;
    label?: string;
    description?: string | null;
    required?: boolean;
    sort_order?: number;
    is_label?: boolean;
    is_unique?: boolean;
    is_searchable?: boolean;
    is_hidden?: boolean;
    default_value?: string | null;
    validation?: Record<string, unknown> | null;
  },
): Promise<ParameterDefinition> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/parameter-definitions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) throw new Error('Failed to create parameter definition');
  return response.json();
}

export async function deleteParameterDefinition(
  templateId: string,
  paramDefId: string,
): Promise<void> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/parameter-definitions/${paramDefId}`,
    { method: 'DELETE' },
  );
  if (!response.ok) throw new Error('Failed to delete parameter definition');
}
