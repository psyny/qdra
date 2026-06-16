export type MaterialParameter = {
  domain: string;
  key: string;
  value: string | number | boolean | null;
  value_type?: 'string' | 'number' | 'boolean' | 'null';
};

export type Material = {
  id: string;
  project_id: string;
  parameters: MaterialParameter[];
  created_at?: string;
  updated_at?: string;
};

export type CreateMaterialRequest = {
  parameters: MaterialParameter[];
};

export type UpdateMaterialRequest = {
  parameters: MaterialParameter[];
};
