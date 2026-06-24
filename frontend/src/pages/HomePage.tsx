import { Link } from 'react-router-dom';
import { WorkspaceHeader } from '../components/WorkspaceHeader';

export function HomePage() {
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

          <Link to="/templates" className="card hub-card">
            <h2 className="hub-card__title">Project Templates</h2>
            <p className="hub-card__description">Define schemas and display configurations</p>
          </Link>

          <Link to="/settings/users" className="card hub-card">
            <h2 className="hub-card__title">Users</h2>
            <p className="hub-card__description">Manage users and permissions</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
