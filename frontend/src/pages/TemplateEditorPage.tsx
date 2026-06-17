import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getTemplate, createTemplate, updateTemplate } from '../api/templates';
import { ProjectTemplateDraft, ProjectTemplateDetail } from '../types/template';
import { EntityTypeEditor } from '../components/EntityTypeEditor';

export function TemplateEditorPage() {
  const { templateId } = useParams<{ templateId?: string }>();
  const navigate = useNavigate();
  const isNew = !templateId;

  const [loading, setLoading] = useState(isNew ? false : true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [draft, setDraft] = useState<ProjectTemplateDraft>({
    name: '',
    description: '',
    entity_types: [],
    views: [],
  });

  useEffect(() => {
    if (!isNew && templateId) {
      loadTemplate(templateId);
    }
  }, [isNew, templateId]);

  const loadTemplate = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data: ProjectTemplateDetail = await getTemplate(id);
      setDraft({
        id: data.template.id,
        name: data.template.name,
        description: data.template.description || '',
        entity_types: data.entity_types ?? [],
        views: data.views ?? [],
      });
    } catch (err) {
      setError('Failed to load template');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      if (isNew) {
        const created = await createTemplate({
          name: draft.name,
          description: draft.description,
        });
        navigate(`/templates/${created.id}/edit`);
      } else if (templateId) {
        await updateTemplate(templateId, {
          name: draft.name,
          description: draft.description,
        });
      }
    } catch (err) {
      setError('Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div className="card state-message">
          <p className="state-message__text">Loading template...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="workspace-header">
        <div className="workspace-header__breadcrumb">
          <Link to="/home">Home</Link> &gt; <Link to="/templates">Templates</Link> &gt; <span>{isNew ? 'New Template' : 'Edit Template'}</span>
        </div>
      </div>

      <div className="page-header">
        <h1 className="page-title">{isNew ? 'Create Template' : 'Edit Template'}</h1>
        <p className="page-description">Define how materials and recipes are represented in your project domain.</p>
      </div>

      {error && (
        <div className="card state-message">
          <p className="state-message__text state-message__text--error">{error}</p>
          <button onClick={() => setError(null)} className="button button--secondary">
            Dismiss
          </button>
        </div>
      )}

      <div className="card form-card">
        <h2 className="card-title">Basic Info</h2>
        
        <div className="form-field">
          <label className="form-label">Name *</label>
          <input
            type="text"
            className="form-input"
            value={draft.name}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            placeholder="Template name"
          />
        </div>

        <div className="form-field">
          <label className="form-label">Description</label>
          <textarea
            className="form-textarea"
            value={draft.description}
            onChange={(e) => setDraft({ ...draft, description: e.target.value })}
            placeholder="What is this template for?"
          />
        </div>

        <div className="form-actions">
          <button
            onClick={() => navigate('/templates')}
            className="button button--secondary"
            disabled={saving}
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="button button--primary"
            disabled={saving || !draft.name.trim()}
          >
            {saving ? 'Saving...' : isNew ? 'Create Template' : 'Save Changes'}
          </button>
        </div>
      </div>

      {templateId && <EntityTypeEditor templateId={templateId} />}

      <div className="card" style={{ marginTop: '24px' }}>
        <h2 className="card-title">Entity Views</h2>
        <p className="card-description">Configure how entities are displayed in different views. (Coming soon)</p>
      </div>
    </div>
  );
}
