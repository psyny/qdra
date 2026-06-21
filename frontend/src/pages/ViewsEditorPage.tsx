import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTemplateViews, deleteView, seedSystemViews, View } from '../api/views';
import { WorkspaceHeader } from '../components/WorkspaceHeader';

export function ViewsEditorPage() {
  const { templateId } = useParams<{ templateId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [views, setViews] = useState<View[]>([]);

  useEffect(() => {
    if (templateId) {
      loadViews();
    }
  }, [templateId]);

  const loadViews = async () => {
    setLoading(true);
    setError(null);
    try {
      // First seed system views (idempotent - won't create duplicates)
      await seedSystemViews(templateId!);
      // Then load views
      const data = await getTemplateViews(templateId!);
      setViews(data);
    } catch (err) {
      setError('Failed to load views');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteView = async (viewId: string) => {
    if (!confirm('Are you sure you want to delete this view?')) return;
    try {
      await deleteView(templateId!, viewId);
      loadViews();
    } catch (err) {
      setError('Failed to delete view');
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div className="card state-message">
          <p className="state-message__text">Loading views...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <WorkspaceHeader breadcrumbItems={[
        { label: 'Home', to: '/home' },
        { label: 'Templates', to: '/templates' },
        { label: 'Edit Template', to: `/templates/${templateId}/edit` },
        { label: 'Views' }
      ]} />

      <div className="page-header">
        <h1 className="page-title">Views</h1>
      </div>

      {error && (
        <div className="mt-4 card state-message">
          <p className="state-message__text state-message__text--error">{error}</p>
          <button onClick={() => setError(null)} className="button button--secondary">
            Dismiss
          </button>
        </div>
      )}

      <div className="mt-8 card">
        <h2 className="card__title">All Views</h2>
        {views.length === 0 ? (
          <p className="state-message__text">No views yet. System views will be seeded automatically.</p>
        ) : (
          <div className="template-grid">
            {views.map((view) => (
              <div key={view.id} className="card template-card">
                <div className="template-card__content">
                  <div className="template-card__title">
                    {view.label}
                    {view.is_system && <span className="badge badge--system">System</span>}
                  </div>
                  {view.description && (
                    <p className="template-card__description">{view.description}</p>
                  )}
                  <p className="template-card__meta">
                    Key: {view.view_key} • Configs: {view.configs?.length || 0}
                  </p>
                </div>
                <div className="template-card__actions">
                  <button
                    onClick={() => navigate(`/templates/${templateId}/views/${view.id}/edit`)}
                    className="button button--secondary"
                  >
                    Edit
                  </button>
                  {!view.is_system && (
                    <button
                      onClick={() => handleDeleteView(view.id)}
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
