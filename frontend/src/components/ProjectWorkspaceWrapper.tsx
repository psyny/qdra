import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getProject } from '../api/projects';
import { getUserProjectPermissions } from '../api/users';
import { Project } from '../types/project';
import { WorkspaceLayout } from './WorkspaceLayout';
import { usePermissionContext } from '../contexts/PermissionContext';
import { BreadcrumbItem } from './Breadcrumb';

type ProjectWorkspaceWrapperProps = {
  children: (project: Project) => React.ReactNode;
  additionalBreadcrumbs?: BreadcrumbItem[] | ((project: Project) => BreadcrumbItem[]);
};

export function ProjectWorkspaceWrapper({ children, additionalBreadcrumbs }: ProjectWorkspaceWrapperProps) {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { currentUserId, setProjectPermissions, clearProjectPermissions } = usePermissionContext();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId || !currentUserId) return;

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [projectData, permissions] = await Promise.all([
          getProject(projectId),
          getUserProjectPermissions(currentUserId, projectId),
        ]);
        setProject(projectData);
        
        if (!permissions.can_access) {
          setError('You do not have access to this project');
          return;
        }
        
        setProjectPermissions(permissions);
      } catch (err) {
        setError('Project not found');
      } finally {
        setLoading(false);
      }
    };

    loadData();

    return () => {
      clearProjectPermissions();
    };
  }, [projectId, currentUserId]);

  useEffect(() => {
    if (error === 'You do not have access to this project') {
      navigate('/projects');
    }
  }, [error, navigate]);

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Qdra</h1>
        </div>
        <div className="card state-message">
          <p className="state-message__text">Loading project...</p>
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Qdra</h1>
        </div>
        <div className="card state-message">
          <p className="state-message__text">Project not found</p>
          <Link to="/projects" className="button button--secondary">
            Back to Projects
          </Link>
        </div>
      </div>
    );
  }

  const resolvedBreadcrumbs = typeof additionalBreadcrumbs === 'function' 
    ? additionalBreadcrumbs(project) 
    : additionalBreadcrumbs;

  return (
    <WorkspaceLayout projectId={project.id} projectName={project.name} additionalBreadcrumbs={resolvedBreadcrumbs}>
      {children(project)}
    </WorkspaceLayout>
  );
}
