export type ProjectTemplate = {
  id: string;
  name: string;
  description?: string | null;
  version: number;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
};

export type CreateTemplateRequest = {
  name: string;
  description?: string | null;
};

export type UpdateTemplateRequest = {
  name?: string;
  description?: string | null;
};

export type CloneTemplateRequest = {
  name?: string | null;
};

export type EntityType = {
  id: string;
  project_template_id: string;
  kind: string;
  name: string;
  description?: string | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
  parameter_definitions: ParameterDefinition[];
};

export type ParameterDefinition = {
  id: string;
  project_template_id: string;
  entity_type_id: string;
  domain: string;
  key: string;
  value_type: string;
  label: string;
  description?: string | null;
  required: boolean;
  sort_order: number;
  is_label: boolean;
  is_unique: boolean;
  is_searchable: boolean;
  is_hidden: boolean;
  default_value?: string | null;
  validation_min?: number | null;
  validation_max?: number | null;
  validation_regex?: string | null;
  created_at: string;
  updated_at: string;
};

export type ViewConfig = {
  id: string;
  view_id: string;
  entity_type_id?: string | null;
  filter_params?: Array<Record<string, any>> | null;
  display_slots?: Array<Record<string, any>> | null;
  sort_order: number;
  created_at: string;
  updated_at: string;
};

export type View = {
  id: string;
  project_template_id: string;
  view_key: string;
  label: string;
  description?: string | null;
  is_system: boolean;
  sort_order: number;
  configs: ViewConfig[];
  created_at: string;
  updated_at: string;
};

export type ProjectTemplateDetail = {
  template: ProjectTemplate;
  entity_types: EntityType[];
  parameter_definitions: ParameterDefinition[];
  views: View[];
};

export type EntityTypeDefinition = {
  id?: string;
  kind: string;
  name: string;
  description?: string | null;
  parameters: ParameterDefinition[];
};

export type EntityViewDefinition = {
  id?: string;
  name: string;
  configs: Array<{
    entity_kind?: string | null;
    entity_type_id?: string | null;
    filter_params?: Array<Record<string, any>> | null;
    slots?: Array<Record<string, any>> | null;
    sort_order: number;
  }>;
};

export type ProjectTemplateDraft = {
  id?: string;
  name: string;
  description?: string | null;
  entity_types: EntityTypeDefinition[];
  views: EntityViewDefinition[];
};
