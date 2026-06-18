import { useLocation, Link } from 'react-router-dom';

type WorkspaceSidebarProps = {
  projectId: string;
};

const navItems = [
  { path: '', label: 'Project' },
  { path: 'materials', label: 'Material Catalog' },
  { path: 'recipes', label: 'Recipe Catalog' },
  { path: 'planning', label: 'Planning' },
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
