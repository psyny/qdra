import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getProjects, createProject, updateProject, deleteProject } from '../api/projects';
import { getTemplates } from '../api/templates';
import { Project, CreateProjectRequest, UpdateProjectRequest } from '../types/project';
import { ProjectTemplate } from '../types/template';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import { ProjectForm } from '../components/ProjectForm';
import { usePermissionContext } from '../contexts/PermissionContext';

export function ProjectSelectionPage() {
  const { appPermissions } = usePermissionContext();
  const [projects, setProjects] = useState<Project[]>([]);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingProjectId, setEditingProjectId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProjects();
      setProjects(data);
    } catch (err) {
      setError('Could not load projects');
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const data = await getTemplates();
      setTemplates(data);
    } catch (err) {
      console.error('Could not load templates', err);
    }
  };

  useEffect(() => {
    loadProjects();
    loadTemplates();
  }, []);

  const handleCreateProject = async (payload: CreateProjectRequest) => {
    setIsSubmitting(true);
    setFormError(null);
    try {
      const newProject = await createProject(payload);
      setProjects([...projects, newProject]);
      setShowCreateForm(false);
    } catch (err) {
      setFormError('Could not save project');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateProjectWithTemplate = async (payload: { name: string; project_template_id: string; description?: string | null }) => {
    setIsSubmitting(true);
    setFormError(null);
    try {
      const newProject = await createProject(payload as CreateProjectRequest);
      setProjects([...projects, newProject]);
      setShowCreateForm(false);
    } catch (err) {
      setFormError('Could not save project');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateProject = async (projectId: string, payload: UpdateProjectRequest) => {
    setIsSubmitting(true);
    setFormError(null);
    try {
      const updatedProject = await updateProject(projectId, payload);
      setProjects(projects.map((p) => (p.id === projectId ? updatedProject : p)));
      setEditingProjectId(null);
    } catch (err) {
      setFormError('Could not save project');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project?')) {
      return;
    }
    try {
      await deleteProject(projectId);
      setProjects(projects.filter((p) => p.id !== projectId));
    } catch (err) {
      setError('Could not delete project');
    }
  };

  const editingProject = editingProjectId ? projects.find((p) => p.id === editingProjectId) : null;

  const filteredProjects = projects.filter((project) => {
    const query = searchQuery.toLowerCase();
    return (
      project.name.toLowerCase().includes(query) ||
      (project.description && project.description.toLowerCase().includes(query))
    );
  });

  return (
    <div className="page">
      <WorkspaceHeader breadcrumbItems={[{ label: 'Home', to: '/home' }, { label: 'Projects', to: '/projects' }]} />
      <div className="page-header">
        <h1 className="page-title">Projects</h1>
        <p className="page-description">Create, edit, and open Qdra workspaces.</p>
      </div>

      <div className="mt-8">
        <div className="page-actions">
          <input
            type="text"
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          {!showCreateForm && !editingProjectId && appPermissions?.can_create_projects && (
            <button
              onClick={() => setShowCreateForm(true)}
              className="button button--primary page-actions__create"
            >
              + New Project
            </button>
          )}
        </div>

        {(showCreateForm || editingProjectId) && (
          <div className="card form-card mt-6">
            <h2 className="card-title">
              {showCreateForm ? 'Create Project' : 'Edit Project'}
            </h2>
            <ProjectForm
              initialName={editingProject?.name || ''}
              initialDescription={editingProject?.description || ''}
              initialTemplateId={editingProject?.project_template_id || null}
              templates={templates}
              submitLabel={showCreateForm ? 'Create' : 'Save'}
              isSubmitting={isSubmitting}
              errorMessage={formError}
              onSubmit={(payload) => {
                if (showCreateForm) {
                  handleCreateProjectWithTemplate(payload);
                } else if (editingProjectId) {
                  handleUpdateProject(editingProjectId, payload);
                }
              }}
              onCancel={() => {
                setShowCreateForm(false);
                setEditingProjectId(null);
                setFormError(null);
              }}
            />
          </div>
        )}
      </div>

      <div className="mt-8">
        {loading && (
          <div className="card state-message">
            <p className="state-message__text">Loading projects...</p>
          </div>
        )}
        {error && (
          <div className="card state-message">
            <p className="state-message__text">{error}</p>
            <button
              onClick={loadProjects}
              className="button button--secondary"
            >
              Retry
            </button>
          </div>
        )}
        {!loading && !error && filteredProjects.length === 0 && (
          <div className="card state-message">
            <p className="state-message__text">No projects found.</p>
            <p className="state-message__subtext">Try adjusting your search or create a new project.</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="button button--primary"
            >
              Create Project
            </button>
          </div>
        )}
        {!loading && !error && filteredProjects.length > 0 && (
          <div className="project-grid">
            {filteredProjects.map((project) => (
              <div key={project.id} className="card project-card">
                {editingProjectId === project.id ? null : (
                  <>
                    <div>
                      <Link
                        to={`/projects/${project.id}`}
                        className="project-card__title"
                      >
                        {project.name}
                      </Link>
                      {project.description && (
                        <p className="project-card__description">{project.description}</p>
                      )}
                    </div>
                    <div className="project-card__actions">
                      {appPermissions?.can_edit_projects && (
                        <button
                          onClick={() => setEditingProjectId(project.id)}
                          className="button button--secondary"
                        >
                          Edit
                        </button>
                      )}
                      {appPermissions?.can_delete_projects && (
                        <button
                          onClick={() => handleDeleteProject(project.id)}
                          className="button button--secondary"
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
