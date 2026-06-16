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

export type CloneTemplateRequest = {
  name?: string | null;
};
