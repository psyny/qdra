import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTemplateViews, View } from '../api/views';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import { ViewConfigEditor } from '../components/ViewConfigEditor';

export function ViewEditorPage() {
  const { templateId, viewId } = useParams<{ templateId: string; viewId: string }>();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View | null>(null);

  useEffect(() => {
    if (templateId && viewId) {
      loadView();
    }
  }, [templateId, viewId]);

  const loadView = async () => {
    setLoading(true);
    setError(null);
    try {
      const views = await getTemplateViews(templateId!);
      const foundView = views.find(v => v.id === viewId);
      if (foundView) {
        setView(foundView);
      } else {
        setError('View not found');
      }
    } catch (err) {
      setError('Failed to load view');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <div className="card state-message">
          <p className="state-message__text">Loading view...</p>
        </div>
      </div>
    );
  }

  if (error || !view) {
    return (
      <div className="page">
        <WorkspaceHeader breadcrumbItems={[
          { label: 'Home', to: '/home' },
          { label: 'Templates', to: '/templates' },
          { label: 'Edit Template', to: `/templates/${templateId}/edit` },
          { label: 'Views', to: `/templates/${templateId}/views` },
          { label: 'Edit View' }
        ]} />
        
        <div className="card state-message">
          <p className="state-message__text state-message__text--error">{error || 'View not found'}</p>
          <button onClick={() => navigate(`/templates/${templateId}/views`)} className="button button--secondary">
            Back to Views
          </button>
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
        { label: 'Views', to: `/templates/${templateId}/views` },
        { label: 'Edit View' }
      ]} />
      
      <div className="page-header">
        <h1 className="page-title">Edit View: {view.label}</h1>
        <button onClick={() => navigate(`/templates/${templateId}/views`)} className="button button--secondary">
          Back to Views
        </button>
      </div>

      <ViewConfigEditor 
        templateId={templateId!}
        view={view}
        onSave={loadView}
        onCancel={() => navigate(`/templates/${templateId}/views`)}
      />
    </div>
  );
}
