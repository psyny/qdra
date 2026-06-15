export type Project = {
  id: string;
  name: string;
  description?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type CreateProjectRequest = {
  name: string;
  description?: string | null;
};

export type UpdateProjectRequest = {
  name: string;
  description?: string | null;
};
