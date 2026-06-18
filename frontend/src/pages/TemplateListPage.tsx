import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getTemplates, deleteTemplate, cloneTemplate, exportTemplate, importTemplate } from '../api/templates';
import { ProjectTemplate, CloneTemplateRequest } from '../types/template';
import { WorkspaceHeader } from '../components/WorkspaceHeader';

export function TemplateListPage() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isCloning, setIsCloning] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [importTemplateName, setImportTemplateName] = useState('');
  const [importData, setImportData] = useState<any>(null);

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

  const handleCreateTemplate = () => {
    navigate('/templates/new');
  };

  const handleCloneTemplate = async (templateId: string) => {
    setIsCloning(templateId);
    setActionError(null);
    try {
      const payload: CloneTemplateRequest = {};
      const cloned = await cloneTemplate(templateId, payload);
      await loadTemplates();
      navigate(`/templates/${cloned.id}/edit`);
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

  const handleExportTemplate = async (templateId: string) => {
    setIsExporting(templateId);
    setActionError(null);
    try {
      const data = await exportTemplate(templateId);
      const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `template-${templateId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      setActionError('Could not export template');
    } finally {
      setIsExporting(null);
    }
  };

  const handleImportTemplate = async (file: File) => {
    setActionError(null);
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      setImportData(data);
      setImportTemplateName(data.template?.name || '');
    } catch (err) {
      setActionError('Could not read template file');
    }
  };

  const handleConfirmImport = async () => {
    if (!importData) return;
    setIsImporting(true);
    setActionError(null);
    try {
      await importTemplate(importData, importTemplateName);
      await loadTemplates();
      setShowImportDialog(false);
      setImportData(null);
      setImportTemplateName('');
    } catch (err) {
      setActionError('Could not import template');
    } finally {
      setIsImporting(false);
    }
  };

  const handleCancelImport = () => {
    setShowImportDialog(false);
    setImportData(null);
    setImportTemplateName('');
    setActionError(null);
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
      <WorkspaceHeader breadcrumbItems={[{ label: 'Home', to: '/home' }, { label: 'Templates', to: '/templates' }]} />
      <div className="page-header">
        <h1 className="page-title">Project Templates</h1>
        <p className="page-description">Define schemas and display configurations for your projects</p>
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
          <button onClick={() => setShowImportDialog(true)} className="button button--secondary">
            Import Template
          </button>
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
                  <button
                    onClick={() => handleExportTemplate(template.id)}
                    disabled={isExporting === template.id}
                    className="button button--secondary"
                  >
                    {isExporting === template.id ? 'Exporting...' : 'Export'}
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

      {showImportDialog && (
        <div className="modal-overlay">
          <div className="modal">
            <h2 className="modal__title">Import Template</h2>
            <p className="modal__description">Select a JSON file to import a template.</p>
            <input
              type="file"
              accept=".json"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  handleImportTemplate(file);
                }
              }}
              disabled={isImporting}
              className="modal__input"
            />
            {importData && (
              <>
                <label className="form-label">Template Name</label>
                <input
                  type="text"
                  value={importTemplateName}
                  onChange={(e) => setImportTemplateName(e.target.value)}
                  disabled={isImporting}
                  className="modal__input"
                  placeholder="Enter template name..."
                />
              </>
            )}
            <div className="modal__actions">
              <button
                onClick={handleCancelImport}
                disabled={isImporting}
                className="button button--secondary"
              >
                Cancel
              </button>
              {importData && (
                <button
                  onClick={handleConfirmImport}
                  disabled={isImporting || !importTemplateName.trim()}
                  className="button button--primary"
                >
                  {isImporting ? 'Importing...' : 'Import'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
