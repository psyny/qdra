import { ReactNode } from 'react';
import { usePermissionContext } from '../contexts/PermissionContext';

interface PermissionActionProps {
  children: ReactNode;
  requireCreateMaterial?: boolean;
  requireEditMaterial?: boolean;
  requireDeleteMaterial?: boolean;
  requireCreateRecipe?: boolean;
  requireEditRecipe?: boolean;
  requireDeleteRecipe?: boolean;
  requireRunPlan?: boolean;
  requireManageProjectUsers?: boolean;
  fallback?: ReactNode;
}

export function PermissionAction({
  children,
  requireCreateMaterial = false,
  requireEditMaterial = false,
  requireDeleteMaterial = false,
  requireCreateRecipe = false,
  requireEditRecipe = false,
  requireDeleteRecipe = false,
  requireRunPlan = false,
  requireManageProjectUsers = false,
  fallback = null,
}: PermissionActionProps) {
  const { projectPermissions } = usePermissionContext();

  if (!projectPermissions) {
    return <>{fallback}</>;
  }

  let hasPermission = true;

  if (requireCreateMaterial) {
    hasPermission = hasPermission && projectPermissions.can_create_material;
  }
  if (requireEditMaterial) {
    hasPermission = hasPermission && projectPermissions.can_edit_material;
  }
  if (requireDeleteMaterial) {
    hasPermission = hasPermission && projectPermissions.can_delete_material;
  }
  if (requireCreateRecipe) {
    hasPermission = hasPermission && projectPermissions.can_create_recipe;
  }
  if (requireEditRecipe) {
    hasPermission = hasPermission && projectPermissions.can_edit_recipe;
  }
  if (requireDeleteRecipe) {
    hasPermission = hasPermission && projectPermissions.can_delete_recipe;
  }
  if (requireRunPlan) {
    hasPermission = hasPermission && projectPermissions.can_run_plan;
  }
  if (requireManageProjectUsers) {
    hasPermission = hasPermission && projectPermissions.can_manage_project_users;
  }

  if (!hasPermission) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
