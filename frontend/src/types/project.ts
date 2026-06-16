export type Project = {
  id: string;
  name: string;
  project_template_id?: string | null;
  description?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type CreateProjectRequest = {
  name: string;
  project_template_id: string;
  description?: string | null;
};

export type UpdateProjectRequest = {
  name: string;
  description?: string | null;
};
