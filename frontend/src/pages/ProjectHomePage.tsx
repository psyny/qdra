import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getProject, getProjectTemplate } from '../api/projects';
import { getUserProjectPermissions } from '../api/users';
import { Project } from '../types/project';
import { ProjectTemplateDetail } from '../types/template';
import { WorkspaceLayout } from '../components/WorkspaceLayout';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { usePermissionContext } from '../contexts/PermissionContext';

export function ProjectHomePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { currentUserId, setProjectPermissions, clearProjectPermissions } = usePermissionContext();
  const [project, setProject] = useState<Project | null>(null);
  const [template, setTemplate] = useState<ProjectTemplateDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId || !currentUserId) return;

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [projectData, templateData, permissions] = await Promise.all([
          getProject(projectId),
          getProjectTemplate(projectId),
          getUserProjectPermissions(currentUserId, projectId),
        ]);
        setProject(projectData);
        setTemplate(templateData);
        
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

  useEffect(() => {
    if (!loading) {
      window.scrollTo(0, 0);
    }
  }, [loading]);

  if (loading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1 className="page-title">Qdra</h1>
        </div>
        <LoadingSpinner message="Loading project..." />
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

  return (
    <WorkspaceLayout projectId={project.id} projectName={project.name}>
      <h2 className="card-title">Project Details</h2>
      <div className="form-field">
        <label className="form-label">Project Name</label>
        <p className="card-description">{project.name}</p>
      </div>
      <div className="form-field">
        <label className="form-label">Project ID</label>
        <p className="card-description">{project.id}</p>
      </div>
      {template && (
        <>
          <div className="form-field">
            <label className="form-label">Template Name</label>
            <p className="card-description">{template.template.name}</p>
          </div>
          <div className="form-field">
            <label className="form-label">Template ID</label>
            <p className="card-description">{template.template.id}</p>
          </div>
        </>
      )}
      {project.created_at && (
        <div className="form-field">
          <label className="form-label">Created At</label>
          <p className="card-description">{new Date(project.created_at).toLocaleString()}</p>
        </div>
      )}
      {project.updated_at && (
        <div className="form-field">
          <label className="form-label">Updated At</label>
          <p className="card-description">{new Date(project.updated_at).toLocaleString()}</p>
        </div>
      )}
    </WorkspaceLayout>
  );
}
