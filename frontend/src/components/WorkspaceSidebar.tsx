import { useLocation, Link } from 'react-router-dom';

type WorkspaceSidebarProps = {
  projectId: string;
};

const navItems = [
  { path: '', label: 'Home' },
  { path: 'materials', label: 'Materials' },
  { path: 'recipes', label: 'Recipes' },
  { path: 'planning', label: 'Planning' },
  { path: 'templates', label: 'Templates' },
  { path: 'settings', label: 'Settings' },
];

export function WorkspaceSidebar({ projectId }: WorkspaceSidebarProps) {
  const location = useLocation();
  const currentPath = location.pathname.split('/').pop() || '';

  return (
    <div className="workspace-sidebar">
      <div className="card workspace-sidebar__card">
        <nav className="workspace-sidebar__nav">
          {navItems.map((item) => {
            const isActive = currentPath === item.path;
            const to = item.path ? `/projects/${projectId}/${item.path}` : `/projects/${projectId}`;
            return (
              <Link
                key={item.path}
                to={to}
                className={`workspace-sidebar__nav-item ${isActive ? 'workspace-sidebar__nav-item--active' : ''}`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
