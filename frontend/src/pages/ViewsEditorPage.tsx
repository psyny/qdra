import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getTemplateViews, createView, updateView, deleteView, seedSystemViews, View } from '../api/views';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import { ViewConfigEditor } from '../components/ViewConfigEditor';

export function ViewsEditorPage() {
  const { templateId } = useParams<{ templateId: string }>();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [views, setViews] = useState<View[]>([]);
  const [editingView, setEditingView] = useState<View | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newViewForm, setNewViewForm] = useState({
    view_key: '',
    label: '',
    description: '',
  });

  useEffect(() => {
    if (templateId) {
      loadViews();
    }
  }, [templateId]);

  const loadViews = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTemplateViews(templateId!);
      setViews(data);
    } catch (err) {
      setError('Failed to load views');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateView = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createView(templateId!, {
        view_key: newViewForm.view_key,
        label: newViewForm.label,
        description: newViewForm.description,
        sort_order: views.length,
      });
      setNewViewForm({ view_key: '', label: '', description: '' });
      setShowCreateForm(false);
      loadViews();
    } catch (err) {
      setError('Failed to create view');
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

  const handleSeedSystemViews = async () => {
    try {
      await seedSystemViews(templateId!);
      loadViews();
    } catch (err) {
      setError('Failed to seed system views');
    }
  };

  const handleReorder = async (viewId: string, direction: 'up' | 'down') => {
    const index = views.findIndex(v => v.id === viewId);
    if (index < 0) return;

    const newViews = [...views];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= newViews.length) return;

    // Swap
    [newViews[index], newViews[targetIndex]] = [newViews[targetIndex], newViews[index]];
    
    // Update sort_order
    newViews.forEach((v, i) => {
      v.sort_order = i;
    });

    try {
      // Update each view
      await Promise.all(newViews.map(v => 
        updateView(templateId!, v.id, { sort_order: v.sort_order })
      ));
      setViews(newViews);
    } catch (err) {
      setError('Failed to reorder views');
      loadViews();
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

  if (editingView) {
    return (
      <div className="page">
        <WorkspaceHeader breadcrumbItems={[
          { label: 'Home', to: '/home' },
          { label: 'Templates', to: '/templates' },
          { label: 'Edit Template', to: `/templates/${templateId}/edit` },
          { label: 'Edit View' }
        ]} />
        
        <div className="page-header">
          <h1 className="page-title">Edit View: {editingView.label}</h1>
          <button onClick={() => setEditingView(null)} className="button button--secondary">
            Back to Views
          </button>
        </div>

        <ViewConfigEditor 
          templateId={templateId!}
          view={editingView}
          onSave={() => {
            setEditingView(null);
            loadViews();
          }}
          onCancel={() => setEditingView(null)}
        />
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
        <div className="page-header__actions">
          <button onClick={handleSeedSystemViews} className="button button--secondary">
            Seed System Views
          </button>
          <button onClick={() => setShowCreateForm(true)} className="button button--primary">
            Create View
          </button>
        </div>
      </div>

      {error && (
        <div className="card state-message">
          <p className="state-message__text state-message__text--error">{error}</p>
          <button onClick={() => setError(null)} className="button button--secondary">
            Dismiss
          </button>
        </div>
      )}

      {showCreateForm && (
        <div className="card">
          <h2 className="card__title">Create New View</h2>
          <form onSubmit={handleCreateView}>
            <div className="form-field">
              <label className="form-label">View Key *</label>
              <input
                type="text"
                className="form-input"
                value={newViewForm.view_key}
                onChange={(e) => setNewViewForm({ ...newViewForm, view_key: e.target.value })}
                placeholder="e.g., material_catalog"
                required
              />
            </div>
            <div className="form-field">
              <label className="form-label">Label *</label>
              <input
                type="text"
                className="form-input"
                value={newViewForm.label}
                onChange={(e) => setNewViewForm({ ...newViewForm, label: e.target.value })}
                placeholder="e.g., Material Catalog"
                required
              />
            </div>
            <div className="form-field">
              <label className="form-label">Description</label>
              <input
                type="text"
                className="form-input"
                value={newViewForm.description}
                onChange={(e) => setNewViewForm({ ...newViewForm, description: e.target.value })}
                placeholder="Description of this view"
              />
            </div>
            <div className="form-actions">
              <button type="submit" className="button button--primary">Create</button>
              <button type="button" onClick={() => setShowCreateForm(false)} className="button button--secondary">
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <h2 className="card__title">All Views</h2>
        {views.length === 0 ? (
          <p className="state-message__text">No views yet. Create one or seed system views.</p>
        ) : (
          <div className="list">
            {views.map((view, index) => (
              <div key={view.id} className="list-item">
                <div className="list-item__content">
                  <div className="list-item__title">
                    {view.label}
                    {view.is_system && <span className="badge badge--system">System</span>}
                  </div>
                  <div className="list-item__subtitle">{view.description}</div>
                  <div className="list-item__meta">
                    Key: {view.view_key} • Configs: {view.configs?.length || 0}
                  </div>
                </div>
                <div className="list-item__actions">
                  <button
                    onClick={() => handleReorder(view.id, 'up')}
                    disabled={index === 0}
                    className="button button--icon"
                    title="Move up"
                  >
                    ↑
                  </button>
                  <button
                    onClick={() => handleReorder(view.id, 'down')}
                    disabled={index === views.length - 1}
                    className="button button--icon"
                    title="Move down"
                  >
                    ↓
                  </button>
                  <button
                    onClick={() => setEditingView(view)}
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
