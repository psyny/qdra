export type EntityParameter = {
  id: string;
  entity_id: string;
  domain: string;
  key: string;
  value_string?: string | null;
  value_number?: number | null;
  value_boolean?: boolean | null;
  created_at: string;
  updated_at: string;
};

export type EntityImage = {
  id: string;
  url: string;
  mime_type: string;
  alt_text?: string | null;
};

export type Entity = {
  id: string;
  project_id: string;
  entity_type_id: string;
  group: string;
  kind: string;
  created_at: string;
  updated_at: string;
  image?: EntityImage | null;
};

export type CreateEntityRequest = {
  entity_type_id: string;
  group: string;
  parameters?: Array<{
    domain: string;
    key: string;
    value_string?: string | null;
    value_number?: number | null;
    value_boolean?: boolean | null;
  }>;
};

export type AddParameterRequest = {
  domain: string;
  key: string;
  value_string?: string | null;
  value_number?: number | null;
  value_boolean?: boolean | null;
};
