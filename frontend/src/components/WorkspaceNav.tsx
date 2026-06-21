import { useLocation, Link } from 'react-router-dom';

type WorkspaceNavProps = {
  projectId: string;
};

const navItems = [
  { path: '', label: 'Project' },
  { path: 'materials', label: 'Material Catalog' },
  { path: 'recipes', label: 'Recipe Catalog' },
  { path: 'planning', label: 'Planning' },
];

export function WorkspaceNav({ projectId }: WorkspaceNavProps) {
  const location = useLocation();
  const currentPath = location.pathname.split('/').pop() || '';

  return (
    <nav className="workspace-nav">
      {navItems.map((item) => {
        const isActive = currentPath === item.path;
        const to = item.path ? `/projects/${projectId}/${item.path}` : `/projects/${projectId}`;
        return (
          <Link
            key={item.path}
            to={to}
            className={`workspace-nav__item ${isActive ? 'workspace-nav__item--active' : ''}`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
