import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { isAuthenticated, getToken, getCurrentUser } from '../api/auth';
import { usePermissionContext } from '../contexts/PermissionContext';

export function RequireAuth() {
  const { appPermissions, setAppPermissions } = usePermissionContext();
  const [loading, setLoading] = useState(appPermissions === null);

  useEffect(() => {
    if (!isAuthenticated() || appPermissions !== null) {
      setLoading(false);
      return;
    }
    const token = getToken()!;
    getCurrentUser(token)
      .then((user) => setAppPermissions(user.app_permissions))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  if (loading) return null;

  return <Outlet />;
}
