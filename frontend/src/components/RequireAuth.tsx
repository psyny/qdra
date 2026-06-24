import { useEffect, useState } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { getToken, getCurrentUser } from '../api/auth';
import { usePermissionContext } from '../contexts/PermissionContext';

export function RequireAuth() {
  const { appPermissions, setAppPermissions, setCurrentUserId } = usePermissionContext();
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(getToken());

  const loadUser = (currentToken: string) => {
    setLoading(true);
    getCurrentUser(currentToken)
      .then((user) => {
        setAppPermissions(user.app_permissions);
        setCurrentUserId(user.id);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    const currentToken = getToken();
    setToken(currentToken);
    
    if (currentToken) {
      loadUser(currentToken);
    } else {
      setLoading(false);
    }

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'jwt_token') {
        const newToken = e.newValue;
        setToken(newToken);
        if (newToken) {
          loadUser(newToken);
        } else {
          setAppPermissions(null as any);
          setCurrentUserId(null);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [setAppPermissions, setCurrentUserId]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (loading) return null;

  return <Outlet />;
}
