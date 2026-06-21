import { useLocation, Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { getProjectTemplate } from '../api/projects';

type WorkspaceNavProps = {
  projectId: string;
};

const baseNavItems = [
  { path: '', label: 'Project' },
  { path: 'materials', label: 'Material Catalog' },
  { path: 'recipes', label: 'Recipe Catalog' },
  { path: 'planning', label: 'Planning' },
];

export function WorkspaceNav({ projectId }: WorkspaceNavProps) {
  const location = useLocation();
  const currentPath = location.pathname.split('/').pop() || '';
  const [navItems, setNavItems] = useState(baseNavItems);

  useEffect(() => {
    async function fetchViewLabels() {
      try {
        const template = await getProjectTemplate(projectId);
        const views = template.views;
        
        const materialCatalogView = views.find(v => v.view_key === 'material_catalog');
        const recipeCatalogView = views.find(v => v.view_key === 'recipe_catalog');
        
        setNavItems(baseNavItems.map(item => {
          if (item.path === 'materials' && materialCatalogView) {
            return { ...item, label: materialCatalogView.label };
          }
          if (item.path === 'recipes' && recipeCatalogView) {
            return { ...item, label: recipeCatalogView.label };
          }
          return item;
        }));
      } catch (error) {
        console.error('Failed to fetch template views:', error);
      }
    }

    fetchViewLabels();
  }, [projectId]);

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
