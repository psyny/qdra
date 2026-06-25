import { useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import { usePermissionContext } from '../contexts/PermissionContext';

export function HomePage() {
  const { appPermissions } = usePermissionContext();
  const navigate = useNavigate();

  useEffect(() => {
    const hasTemplateAccess = appPermissions?.can_create_templates || appPermissions?.can_edit_templates || appPermissions?.can_delete_templates;
    const hasUserAccess = appPermissions?.can_manage_users;

    if (!hasTemplateAccess && !hasUserAccess) {
      navigate('/projects');
    }
  }, [appPermissions, navigate]);

  return (
    <div className="page">
      <WorkspaceHeader breadcrumbItems={[{ label: 'Home', to: '/home' }]} />
      <div className="page-header">
        <h1 className="page-title">Qdra</h1>
        <p className="page-description">Choose where to start.</p>
      </div>

      <div className="mt-12">
        <div className="hub-grid">
          <Link to="/projects" className="card hub-card">
            <h2 className="hub-card__title">Projects</h2>
            <p className="hub-card__description">Manage your planning workspaces</p>
          </Link>

          {(appPermissions?.can_create_templates || appPermissions?.can_edit_templates || appPermissions?.can_delete_templates) && (
            <Link to="/templates" className="card hub-card">
              <h2 className="hub-card__title">Project Templates</h2>
              <p className="hub-card__description">Define schemas and display configurations</p>
            </Link>
          )}

          {appPermissions?.can_manage_users && (
            <Link to="/settings/users" className="card hub-card">
              <h2 className="hub-card__title">Users</h2>
              <p className="hub-card__description">Manage users and permissions</p>
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
