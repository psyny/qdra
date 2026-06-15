export type MaterialParameter = {
  domain: string;
  key: string;
  value: string | number | boolean | null;
};

export type Material = {
  id: string;
  project_id: string;
  parameters: MaterialParameter[];
};
