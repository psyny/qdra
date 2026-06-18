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

export async function getEntityType(templateId: string, entityTypeId: string): Promise<EntityType> {
  const response = await fetch(`${API_URL}/project-templates/${templateId}/entity-types/${entityTypeId}`);
  if (!response.ok) throw new Error('Failed to fetch entity type');
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
      method: 'PUT',
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
  if (!response.ok) {
    if (response.status === 409) {
      throw new Error('Cannot delete entity type because it is used by existing entities.');
    }
    throw new Error('Failed to delete entity type');
  }
}

export async function cloneEntityType(templateId: string, entityTypeId: string): Promise<EntityType> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/entity-types/${entityTypeId}/clone`,
    { method: 'POST' },
  );
  if (!response.ok) throw new Error('Failed to clone entity type');
  return response.json();
}

export async function listParameterDefinitions(
  templateId: string,
  entityTypeId: string,
): Promise<ParameterDefinition[]> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/entity-types/${entityTypeId}/parameter-definitions`,
  );
  if (!response.ok) throw new Error('Failed to fetch parameter definitions');
  return response.json();
}

export async function createParameterDefinition(
  templateId: string,
  entityTypeId: string,
  payload: {
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
    validation_min?: number | null;
    validation_max?: number | null;
    validation_regex?: string | null;
  },
): Promise<ParameterDefinition> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/entity-types/${entityTypeId}/parameter-definitions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) throw new Error('Failed to create parameter definition');
  return response.json();
}

export async function updateParameterDefinition(
  templateId: string,
  entityTypeId: string,
  definitionId: string,
  payload: {
    domain?: string;
    key?: string;
    value_type?: string;
    label?: string;
    description?: string | null;
    required?: boolean;
    sort_order?: number;
    is_label?: boolean;
    is_unique?: boolean;
    is_searchable?: boolean;
    is_hidden?: boolean;
    default_value?: string | null;
    validation_min?: number | null;
    validation_max?: number | null;
    validation_regex?: string | null;
  },
): Promise<ParameterDefinition> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/entity-types/${entityTypeId}/parameter-definitions/${definitionId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) throw new Error('Failed to update parameter definition');
  return response.json();
}

export async function deleteParameterDefinition(
  templateId: string,
  entityTypeId: string,
  definitionId: string,
): Promise<void> {
  const response = await fetch(
    `${API_URL}/project-templates/${templateId}/entity-types/${entityTypeId}/parameter-definitions/${definitionId}`,
    { method: 'DELETE' },
  );
  if (!response.ok) throw new Error('Failed to delete parameter definition');
}

// Slot Group operations

export async function listSlotGroups(entityTypeId: string): Promise<any[]> {
  const response = await fetch(`${API_URL}/project-template-entity-types/${entityTypeId}/slot-groups`);
  if (!response.ok) throw new Error('Failed to fetch slot groups');
  return response.json();
}

export async function createSlotGroup(
  entityTypeId: string,
  payload: {
    kind: string;
    min_slots?: number;
    max_slots?: number | null;
    sort_order?: number;
  },
): Promise<any> {
  const response = await fetch(`${API_URL}/project-template-entity-types/${entityTypeId}/slot-groups`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create slot group');
  return response.json();
}

export async function updateSlotGroup(
  slotGroupId: string,
  payload: {
    kind?: string;
    min_slots?: number;
    max_slots?: number | null;
    sort_order?: number;
  },
): Promise<any> {
  const response = await fetch(`${API_URL}/project-template-slot-groups/${slotGroupId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to update slot group');
  return response.json();
}

export async function deleteSlotGroup(slotGroupId: string): Promise<void> {
  const response = await fetch(`${API_URL}/project-template-slot-groups/${slotGroupId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete slot group');
}

// Slot Definition operations

export async function createSlotDefinition(
  slotGroupId: string,
  payload: {
    slot_key: string;
    min_occurrences?: number;
    max_occurrences?: number | null;
    sort_order?: number;
  },
): Promise<any> {
  const response = await fetch(`${API_URL}/project-template-slot-groups/${slotGroupId}/slot-definitions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create slot definition');
  return response.json();
}

export async function updateSlotDefinition(
  slotDefinitionId: string,
  payload: {
    slot_key?: string;
    min_occurrences?: number;
    max_occurrences?: number | null;
    sort_order?: number;
  },
): Promise<any> {
  const response = await fetch(`${API_URL}/project-template-slot-definitions/${slotDefinitionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to update slot definition');
  return response.json();
}

export async function deleteSlotDefinition(slotDefinitionId: string): Promise<void> {
  const response = await fetch(`${API_URL}/project-template-slot-definitions/${slotDefinitionId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete slot definition');
}

// Slot Constraint operations

export async function createGroupConstraint(
  slotGroupId: string,
  payload: {
    domain?: string | null;
    key?: string | null;
    operator?: string | null;
    value_string?: string | null;
    value_number?: number | null;
    value_boolean?: boolean | null;
    is_wildcard?: boolean;
    sort_order?: number;
  },
): Promise<any> {
  const response = await fetch(`${API_URL}/project-template-slot-groups/${slotGroupId}/constraints`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create constraint');
  return response.json();
}

export async function createDefinitionConstraint(
  slotDefinitionId: string,
  payload: {
    domain?: string | null;
    key?: string | null;
    operator?: string | null;
    value_string?: string | null;
    value_number?: number | null;
    value_boolean?: boolean | null;
    is_wildcard?: boolean;
    sort_order?: number;
  },
): Promise<any> {
  const response = await fetch(`${API_URL}/project-template-slot-definitions/${slotDefinitionId}/constraints`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to create constraint');
  return response.json();
}

export async function updateSlotConstraint(
  constraintId: string,
  payload: {
    domain?: string | null;
    key?: string | null;
    operator?: string | null;
    value_string?: string | null;
    value_number?: number | null;
    value_boolean?: boolean | null;
    is_wildcard?: boolean;
    sort_order?: number;
  },
): Promise<any> {
  const response = await fetch(`${API_URL}/project-template-slot-constraints/${constraintId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error('Failed to update constraint');
  return response.json();
}

export async function deleteSlotConstraint(constraintId: string): Promise<void> {
  const response = await fetch(`${API_URL}/project-template-slot-constraints/${constraintId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete constraint');
}
