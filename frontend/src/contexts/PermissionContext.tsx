import { createContext, useContext, useState, ReactNode } from 'react';

interface AppPermissions {
  can_manage_users: boolean;
  can_create_projects: boolean;
  can_edit_projects: boolean;
  can_delete_projects: boolean;
  can_create_templates: boolean;
  can_edit_templates: boolean;
  can_delete_templates: boolean;
}

interface ProjectPermissions {
  can_access: boolean;
  can_manage_project_users: boolean;
  can_create_material: boolean;
  can_edit_material: boolean;
  can_delete_material: boolean;
  can_create_recipe: boolean;
  can_edit_recipe: boolean;
  can_delete_recipe: boolean;
  can_run_plan: boolean;
}

interface PermissionContextType {
  appPermissions: AppPermissions | null;
  projectPermissions: ProjectPermissions | null;
  setAppPermissions: (permissions: AppPermissions) => void;
  setProjectPermissions: (permissions: ProjectPermissions) => void;
  clearProjectPermissions: () => void;
  hasAnyMaterialPermission: () => boolean;
  hasAnyRecipePermission: () => boolean;
}

const PermissionContext = createContext<PermissionContextType | undefined>(undefined);

export function PermissionProvider({ children }: { children: ReactNode }) {
  const [appPermissions, setAppPermissions] = useState<AppPermissions | null>(null);
  const [projectPermissions, setProjectPermissionsState] = useState<ProjectPermissions | null>(null);

  const setProjectPermissions = (permissions: ProjectPermissions) => {
    setProjectPermissionsState(permissions);
  };

  const clearProjectPermissions = () => {
    setProjectPermissionsState(null);
  };

  const hasAnyMaterialPermission = () => {
    if (!projectPermissions) return false;
    return projectPermissions.can_create_material || 
           projectPermissions.can_edit_material || 
           projectPermissions.can_delete_material;
  };

  const hasAnyRecipePermission = () => {
    if (!projectPermissions) return false;
    return projectPermissions.can_create_recipe || 
           projectPermissions.can_edit_recipe || 
           projectPermissions.can_delete_recipe;
  };

  return (
    <PermissionContext.Provider 
      value={{
        appPermissions,
        projectPermissions,
        setAppPermissions,
        setProjectPermissions,
        clearProjectPermissions,
        hasAnyMaterialPermission,
        hasAnyRecipePermission,
      }}
    >
      {children}
    </PermissionContext.Provider>
  );
}

export function usePermissionContext() {
  const context = useContext(PermissionContext);
  if (context === undefined) {
    throw new Error('usePermissionContext must be used within a PermissionProvider');
  }
  return context;
}
