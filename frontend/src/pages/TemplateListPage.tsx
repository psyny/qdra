import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getTemplates, createTemplate, deleteTemplate, cloneTemplate } from '../api/templates';
import { ProjectTemplate, CreateTemplateRequest, CloneTemplateRequest } from '../types/template';
import { BackendStatus } from '../components/BackendStatus';

export function TemplateListPage() {
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCloning, setIsCloning] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTemplates();
      setTemplates(data);
    } catch (err) {
      setError('Could not load templates');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  const handleCreateTemplate = async () => {
    const payload: CreateTemplateRequest = {
      name: 'New Template',
      description: '',
    };
    try {
      await createTemplate(payload);
      await loadTemplates();
    } catch (err) {
      setActionError('Could not create template');
    }
  };

  const handleCloneTemplate = async (templateId: string) => {
    setIsCloning(templateId);
    setActionError(null);
    try {
      const payload: CloneTemplateRequest = {};
      await cloneTemplate(templateId, payload);
      await loadTemplates();
    } catch (err) {
      setActionError('Could not clone template');
    } finally {
      setIsCloning(null);
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    setIsDeleting(templateId);
    setActionError(null);
    try {
      await deleteTemplate(templateId);
      await loadTemplates();
      setDeleteConfirm(null);
    } catch (err) {
      setActionError((err as Error).message || 'Could not delete template');
    } finally {
      setIsDeleting(null);
    }
  };

  const filteredTemplates = templates.filter((template) => {
    const query = searchQuery.toLowerCase();
    return (
      template.name.toLowerCase().includes(query) ||
      (template.description && template.description.toLowerCase().includes(query))
    );
  });

  return (
    <div className="page">
      <div className="workspace-header">
        <div className="workspace-header__breadcrumb">
          <Link to="/home">Home</Link> &gt; <Link to="/templates">Templates</Link>
        </div>
      </div>
      <div className="page-header">
        <h1 className="page-title">Project Templates</h1>
        <p className="page-description">Define schemas and display configurations for your projects</p>
        <div className="mt-4">
          <BackendStatus />
        </div>
      </div>

      <div className="mt-8">
        <div className="page-actions">
          <input
            type="text"
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
          <button onClick={handleCreateTemplate} className="button button--primary page-actions__create">
            Create Template
          </button>
        </div>
      </div>

      {actionError && (
        <div className="mt-4 card state-message">
          <p className="state-message__text state-message__text--error">{actionError}</p>
          <button onClick={() => setActionError(null)} className="button button--secondary">
            Dismiss
          </button>
        </div>
      )}

      <div className="mt-8">
        {loading && (
          <div className="card state-message">
            <p className="state-message__text">Loading templates...</p>
          </div>
        )}
        {error && (
          <div className="card state-message">
            <p className="state-message__text">{error}</p>
            <button onClick={loadTemplates} className="button button--secondary">
              Retry
            </button>
          </div>
        )}
        {!loading && !error && templates.length === 0 && (
          <div className="card state-message">
            <p className="state-message__text">No project templates yet.</p>
            <p className="state-message__subtext">Create your first template to start defining project schemas.</p>
            <button onClick={handleCreateTemplate} className="button button--primary">
              Create Template
            </button>
          </div>
        )}
        {!loading && !error && templates.length > 0 && filteredTemplates.length === 0 && (
          <div className="card state-message">
            <p className="state-message__text">No templates match your search.</p>
          </div>
        )}
        {!loading && !error && filteredTemplates.length > 0 && (
          <div className="template-grid">
            {filteredTemplates.map((template) => (
              <div key={template.id} className="card template-card">
                <div className="template-card__content">
                  <h3 className="template-card__title">{template.name}</h3>
                  {template.description && (
                    <p className="template-card__description">{template.description}</p>
                  )}
                  <p className="template-card__meta">
                    Updated: {new Date(template.updated_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="template-card__actions">
                  <Link to={`/templates/${template.id}/edit`} className="button button--secondary">
                    Edit
                  </Link>
                  <button
                    onClick={() => handleCloneTemplate(template.id)}
                    disabled={isCloning === template.id}
                    className="button button--secondary"
                  >
                    {isCloning === template.id ? 'Cloning...' : 'Clone'}
                  </button>
                  {deleteConfirm === template.id ? (
                    <>
                      <button
                        onClick={() => handleDeleteTemplate(template.id)}
                        disabled={isDeleting === template.id}
                        className="button button--danger"
                      >
                        {isDeleting === template.id ? 'Deleting...' : 'Confirm'}
                      </button>
                      <button
                        onClick={() => setDeleteConfirm(null)}
                        className="button button--secondary"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setDeleteConfirm(template.id)}
                      className="button button--danger"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
