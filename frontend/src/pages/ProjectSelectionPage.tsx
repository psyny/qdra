import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getProjects, createProject, updateProject } from '../api/projects';
import { Project, CreateProjectRequest, UpdateProjectRequest } from '../types/project';
import { BackendStatus } from '../components/BackendStatus';
import { ProjectForm } from '../components/ProjectForm';

export function ProjectSelectionPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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

  useEffect(() => {
    loadProjects();
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

  const editingProject = editingProjectId ? projects.find((p) => p.id === editingProjectId) : null;

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900">Qdra</h1>
        <h2 className="text-2xl font-semibold text-gray-800 mt-4">Projects</h2>

        <div className="mt-6">
          {!showCreateForm && !editingProjectId && (
            <button
              onClick={() => setShowCreateForm(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              + New Project
            </button>
          )}

          {(showCreateForm || editingProjectId) && (
            <div className="mt-4 p-6 bg-white rounded-lg shadow">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                {showCreateForm ? 'Create Project' : 'Edit Project'}
              </h3>
              <ProjectForm
                initialName={editingProject?.name || ''}
                initialDescription={editingProject?.description || ''}
                submitLabel={showCreateForm ? 'Create' : 'Save'}
                isSubmitting={isSubmitting}
                errorMessage={formError}
                onSubmit={(payload) => {
                  if (showCreateForm) {
                    handleCreateProject(payload);
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

        <div className="mt-6">
          {loading && <p className="text-gray-600">Loading projects...</p>}
          {error && (
            <div className="p-4 bg-red-50 text-red-700 rounded-md">
              <p>{error}</p>
              <button
                onClick={loadProjects}
                className="mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Retry
              </button>
            </div>
          )}
          {!loading && !error && projects.length === 0 && (
            <div className="p-6 bg-white rounded-lg shadow text-center">
              <p className="text-gray-600">No projects yet.</p>
              <p className="text-gray-500 mt-2">Create your first project to start using Qdra.</p>
            </div>
          )}
          {!loading && !error && projects.length > 0 && (
            <div className="space-y-4">
              {projects.map((project) => (
                <div key={project.id} className="p-6 bg-white rounded-lg shadow">
                  {editingProjectId === project.id ? null : (
                    <>
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <Link
                            to={`/projects/${project.id}`}
                            className="text-xl font-semibold text-gray-900 hover:text-blue-600"
                          >
                            {project.name}
                          </Link>
                          {project.description && (
                            <p className="text-gray-600 mt-2">{project.description}</p>
                          )}
                        </div>
                        <div className="flex space-x-2 ml-4">
                          <button
                            onClick={() => setEditingProjectId(project.id)}
                            className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-8">
          <BackendStatus />
        </div>
      </div>
    </div>
  );
}
