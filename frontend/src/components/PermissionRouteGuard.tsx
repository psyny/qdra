import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePermissionContext } from '../contexts/PermissionContext';

interface PermissionRouteGuardProps {
  children: React.ReactNode;
  requireAnyMaterialPermission?: boolean;
  requireAnyRecipePermission?: boolean;
  requireRunPlan?: boolean;
  requireManageProjectUsers?: boolean;
}

export function PermissionRouteGuard({
  children,
  requireAnyMaterialPermission = false,
  requireAnyRecipePermission = false,
  requireRunPlan = false,
  requireManageProjectUsers = false,
}: PermissionRouteGuardProps) {
  const { projectPermissions } = usePermissionContext();
  const navigate = useNavigate();

  useEffect(() => {
    if (!projectPermissions) {
      navigate('/projects');
      return;
    }

    let hasAccess = true;

    if (requireAnyMaterialPermission) {
      hasAccess = hasAccess && (
        projectPermissions.can_create_material ||
        projectPermissions.can_edit_material ||
        projectPermissions.can_delete_material
      );
    }

    if (requireAnyRecipePermission) {
      hasAccess = hasAccess && (
        projectPermissions.can_create_recipe ||
        projectPermissions.can_edit_recipe ||
        projectPermissions.can_delete_recipe
      );
    }

    if (requireRunPlan) {
      hasAccess = hasAccess && projectPermissions.can_run_plan;
    }

    if (requireManageProjectUsers) {
      hasAccess = hasAccess && projectPermissions.can_manage_project_users;
    }

    if (!hasAccess) {
      navigate('/projects');
    }
  }, [
    projectPermissions,
    navigate,
    requireAnyMaterialPermission,
    requireAnyRecipePermission,
    requireRunPlan,
    requireManageProjectUsers,
  ]);

  if (!projectPermissions) {
    return null;
  }

  let hasAccess = true;

  if (requireAnyMaterialPermission) {
    hasAccess = hasAccess && (
      projectPermissions.can_create_material ||
      projectPermissions.can_edit_material ||
      projectPermissions.can_delete_material
    );
  }

  if (requireAnyRecipePermission) {
    hasAccess = hasAccess && (
      projectPermissions.can_create_recipe ||
      projectPermissions.can_edit_recipe ||
      projectPermissions.can_delete_recipe
    );
  }

  if (requireRunPlan) {
    hasAccess = hasAccess && projectPermissions.can_run_plan;
  }

  if (requireManageProjectUsers) {
    hasAccess = hasAccess && projectPermissions.can_manage_project_users;
  }

  if (!hasAccess) {
    return null;
  }

  return <>{children}</>;
}
