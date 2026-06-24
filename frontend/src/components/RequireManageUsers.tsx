import { Navigate, Outlet } from 'react-router-dom';
import { usePermissionContext } from '../contexts/PermissionContext';

export function RequireManageUsers() {
  const { appPermissions } = usePermissionContext();

  if (!appPermissions?.can_manage_users) {
    return <Navigate to="/home" replace />;
  }

  return <Outlet />;
}
