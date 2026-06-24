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

    // If user can access the project, they can view all pages
    // Specific permissions only control what actions they can perform
    if (!projectPermissions.can_access) {
      navigate('/projects');
    }
  }, [projectPermissions, navigate]);

  if (!projectPermissions) {
    return null;
  }

  // If user can access the project, they can view all pages
  // Specific permissions only control what actions they can perform
  if (!projectPermissions.can_access) {
    return null;
  }

  return <>{children}</>;
}
