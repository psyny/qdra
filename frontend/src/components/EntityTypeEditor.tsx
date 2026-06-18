import { useState, useEffect } from 'react';
import { EntityType, ParameterDefinition } from '../types/template';
import {
  listEntityTypes,
  createEntityType,
  updateEntityType,
  deleteEntityType,
  cloneEntityType,
  listParameterDefinitions,
  createParameterDefinition,
  updateParameterDefinition,
  deleteParameterDefinition,
} from '../api/templates';

type EntityTypeEditorProps = {
  templateId: string;
};

type EntityTypeForm = {
  kind: 'material' | 'recipe';
  name: string;
  description: string;
};

type ParameterDefinitionForm = {
  domain: string;
  key: string;
  value_type: 'string' | 'number' | 'boolean';
  label: string;
  description: string;
  required: boolean;
  sort_order: number;
  is_label: boolean;
  is_unique: boolean;
  is_searchable: boolean;
  is_hidden: boolean;
  default_value: string;
  validation: string;
};

export function EntityTypeEditor({ templateId }: EntityTypeEditorProps) {
  const [entityTypes, setEntityTypes] = useState<EntityType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingType, setEditingType] = useState<EntityType | null>(null);
  const [expandedType, setExpandedType] = useState<string | null>(null);

  const [form, setForm] = useState<EntityTypeForm>({
    kind: 'material',
    name: '',
    description: '',
  });

  const [paramForm, setParamForm] = useState<ParameterDefinitionForm>({
    domain: '',
    key: '',
    value_type: 'string',
    label: '',
    description: '',
    required: false,
    sort_order: 0,
    is_label: false,
    is_unique: false,
    is_searchable: false,
    is_hidden: false,
    default_value: '',
    validation: '',
  });

  const [showParamForm, setShowParamForm] = useState(false);
  const [editingParam, setEditingParam] = useState<ParameterDefinition | null>(null);

  useEffect(() => {
    loadEntityTypes();
  }, [templateId]);

  const loadEntityTypes = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listEntityTypes(templateId);
      setEntityTypes(data);
    } catch (err) {
      setError('Failed to load entity types');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!form.name.trim()) {
      setError('Name is required');
      return;
    }
    try {
      await createEntityType(templateId, {
        kind: form.kind,
        name: form.name.trim(),
        description: form.description.trim() || null,
        sort_order: 0,
      });
      setShowCreateForm(false);
      setForm({ kind: 'material', name: '', description: '' });
      loadEntityTypes();
    } catch (err) {
      setError('Failed to create entity type');
    }
  };

  const handleUpdate = async () => {
    if (!editingType || !form.name.trim()) return;
    try {
      await updateEntityType(templateId, editingType.id, {
        name: form.name.trim(),
        description: form.description.trim() || null,
        sort_order: editingType.sort_order,
      });
      setEditingType(null);
      setForm({ kind: 'material', name: '', description: '' });
      loadEntityTypes();
    } catch (err) {
      setError('Failed to update entity type');
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this entity type?')) return;
    try {
      await deleteEntityType(templateId, id);
      loadEntityTypes();
    } catch (err: any) {
      setError(err.message || 'Failed to delete entity type');
    }
  };

  const handleClone = async (id: string) => {
    try {
      await cloneEntityType(templateId, id);
      loadEntityTypes();
    } catch (err) {
      setError('Failed to clone entity type');
    }
  };

  const startEdit = (et: EntityType) => {
    setEditingType(et);
    setForm({
      kind: et.kind as 'material' | 'recipe',
      name: et.name,
      description: et.description || '',
    });
  };

  const cancelEdit = () => {
    setEditingType(null);
    setForm({ kind: 'material', name: '', description: '' });
  };

  const loadParameterDefinitions = async (entityTypeId: string) => {
    try {
      const params = await listParameterDefinitions(templateId, entityTypeId);
      setEntityTypes(entityTypes.map(et => 
        et.id === entityTypeId ? { ...et, parameter_definitions: params } : et
      ));
    } catch (err) {
      setError('Failed to load parameter definitions');
    }
  };

  const handleCreateParam = async (entityTypeId: string) => {
    if (!paramForm.domain.trim() || !paramForm.key.trim()) {
      setError('Domain and key are required');
      return;
    }
    try {
      await createParameterDefinition(templateId, entityTypeId, {
        domain: paramForm.domain.trim(),
        key: paramForm.key.trim(),
        value_type: paramForm.value_type,
        label: paramForm.label.trim(),
        description: paramForm.description.trim() || null,
        required: paramForm.required,
        sort_order: paramForm.sort_order,
        is_label: paramForm.is_label,
        is_unique: paramForm.is_unique,
        is_searchable: paramForm.is_searchable,
        is_hidden: paramForm.is_hidden,
        default_value: paramForm.default_value.trim() || null,
        validation: paramForm.validation.trim() || null,
      });
      setShowParamForm(false);
      setEditingParam(null);
      setParamForm({
        domain: '',
        key: '',
        value_type: 'string',
        label: '',
        description: '',
        required: false,
        sort_order: 0,
        is_label: false,
        is_unique: false,
        is_searchable: false,
        is_hidden: false,
        default_value: '',
        validation: '',
      });
      loadParameterDefinitions(entityTypeId);
    } catch (err) {
      setError('Failed to create parameter definition');
    }
  };

  const handleUpdateParam = async (entityTypeId: string, definitionId: string) => {
    try {
      await updateParameterDefinition(templateId, entityTypeId, definitionId, {
        domain: paramForm.domain.trim(),
        key: paramForm.key.trim(),
        value_type: paramForm.value_type,
        label: paramForm.label.trim(),
        description: paramForm.description.trim() || null,
        required: paramForm.required,
        sort_order: paramForm.sort_order,
        is_label: paramForm.is_label,
        is_unique: paramForm.is_unique,
        is_searchable: paramForm.is_searchable,
        is_hidden: paramForm.is_hidden,
        default_value: paramForm.default_value.trim() || null,
        validation: paramForm.validation.trim() || null,
      });
      setShowParamForm(false);
      setEditingParam(null);
      setParamForm({
        domain: '',
        key: '',
        value_type: 'string',
        label: '',
        description: '',
        required: false,
        sort_order: 0,
        is_label: false,
        is_unique: false,
        is_searchable: false,
        is_hidden: false,
        default_value: '',
        validation: '',
      });
      loadParameterDefinitions(entityTypeId);
    } catch (err) {
      setError('Failed to update parameter definition');
    }
  };

  const handleDeleteParam = async (entityTypeId: string, definitionId: string) => {
    if (!confirm('Are you sure you want to delete this parameter definition?')) return;
    try {
      await deleteParameterDefinition(templateId, entityTypeId, definitionId);
      loadParameterDefinitions(entityTypeId);
    } catch (err) {
      setError('Failed to delete parameter definition');
    }
  };

  const startEditParam = (param: ParameterDefinition) => {
    setEditingParam(param);
    setParamForm({
      domain: param.domain,
      key: param.key,
      value_type: param.value_type as 'string' | 'number' | 'boolean',
      label: param.label,
      description: param.description || '',
      required: param.required,
      sort_order: param.sort_order,
      is_label: param.is_label,
      is_unique: param.is_unique,
      is_searchable: param.is_searchable,
      is_hidden: param.is_hidden,
      default_value: param.default_value || '',
      validation: param.validation ? JSON.stringify(param.validation) : '',
    });
  };

  const cancelEditParam = () => {
    setEditingParam(null);
    setShowParamForm(false);
    setParamForm({
      domain: '',
      key: '',
      value_type: 'string',
      label: '',
      description: '',
      required: false,
      sort_order: 0,
      is_label: false,
      is_unique: false,
      is_searchable: false,
      is_hidden: false,
      default_value: '',
      validation: '',
    });
  };

  if (loading) {
    return <p>Loading entity types...</p>;
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 className="card-title">Entity Types</h2>
        <button
          onClick={() => setShowCreateForm(true)}
          className="button button--primary"
        >
          Add Entity Type
        </button>
      </div>

      {error && (
        <div style={{ padding: '12px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px', marginBottom: '16px' }}>
          <p style={{ color: '#EF4444', margin: 0 }}>{error}</p>
          <button onClick={() => setError(null)} style={{ marginTop: '8px', background: 'none', border: 'none', color: '#EF4444', cursor: 'pointer', textDecoration: 'underline' }}>Dismiss</button>
        </div>
      )}

      {showCreateForm && (
        <div style={{ padding: '16px', backgroundColor: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '18px', marginBottom: '16px' }}>
          <h3 style={{ marginTop: 0 }}>Create Entity Type</h3>
          <div className="form-field">
            <label className="form-label">Kind *</label>
            <select
              className="form-input"
              value={form.kind}
              onChange={(e) => setForm({ ...form, kind: e.target.value as 'material' | 'recipe' })}
              disabled={!!editingType}
            >
              <option value="material">Material</option>
              <option value="recipe">Recipe</option>
            </select>
          </div>
          <div className="form-field">
            <label className="form-label">Name *</label>
            <input
              type="text"
              className="form-input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="e.g., Item"
            />
          </div>
          <div className="form-field">
            <label className="form-label">Description</label>
            <textarea
              className="form-textarea"
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Optional description"
            />
          </div>
          <div className="form-actions">
            <button onClick={() => { setShowCreateForm(false); setForm({ kind: 'material', name: '', description: '' }); }} className="button button--secondary">
              Cancel
            </button>
            <button onClick={handleCreate} className="button button--primary" disabled={!form.name.trim()}>
              Create
            </button>
          </div>
        </div>
      )}

      {entityTypes.length === 0 && !showCreateForm && (
        <p style={{ color: '#666', fontStyle: 'italic' }}>No entity types defined yet. Click "Add Entity Type" to create one.</p>
      )}

      {entityTypes.map((et) => (
        <div key={et.id} style={{ border: '1px solid #ddd', borderRadius: '4px', marginBottom: '12px', padding: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3 style={{ margin: '0 0 4px 0' }}>{et.name}</h3>
              <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>
                <strong>Kind:</strong> {et.kind} | <strong>Parameters:</strong> {et.parameter_definitions?.length || 0}
              </p>
              {et.description && <p style={{ margin: '4px 0 0 0', color: '#666', fontSize: '14px' }}>{et.description}</p>}
              {et.kind === 'recipe' && (
                <p style={{ margin: '8px 0 0 0', color: '#666', fontSize: '13px', fontStyle: 'italic' }}>
                  
                </p>
              )}
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={() => { setExpandedType(expandedType === et.id ? null : et.id); if (expandedType !== et.id) loadParameterDefinitions(et.id); }} className="button button--secondary" style={{ fontSize: '12px' }}>
                {expandedType === et.id ? 'Collapse' : 'Parameters'}
              </button>
              {et.kind === 'recipe' && (
                <button 
                  onClick={() => window.location.href = `/templates/${templateId}/entity-types/${et.id}/slots`}
                  className="button button--secondary" 
                  style={{ fontSize: '12px' }}
                >
                  Slots
                </button>
              )}
              <button onClick={() => startEdit(et)} className="button button--secondary" style={{ fontSize: '12px' }}>
                Edit
              </button>
              <button onClick={() => handleClone(et.id)} className="button button--secondary" style={{ fontSize: '12px' }}>
                Clone
              </button>
              <button onClick={() => handleDelete(et.id)} className="button button--secondary" style={{ fontSize: '12px', color: '#c33' }}>
                Delete
              </button>
            </div>
          </div>

          {editingType?.id === et.id && (
            <div style={{ marginTop: '16px', padding: '12px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
              <h4 style={{ marginTop: 0 }}>Edit Entity Type</h4>
              <div className="form-field">
                <label className="form-label">Name *</label>
                <input
                  type="text"
                  className="form-input"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>
              <div className="form-field">
                <label className="form-label">Description</label>
                <textarea
                  className="form-textarea"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </div>
              <div className="form-actions">
                <button onClick={cancelEdit} className="button button--secondary">Cancel</button>
                <button onClick={handleUpdate} className="button button--primary" disabled={!form.name.trim()}>Save</button>
              </div>
            </div>
          )}

          {expandedType === et.id && (
            <div style={{ marginTop: '16px', borderTop: '1px solid #ddd', paddingTop: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h4 style={{ margin: 0 }}>Parameter Definitions</h4>
                <button onClick={() => { setShowParamForm(true); setEditingParam(null); }} className="button button--primary" style={{ fontSize: '12px' }}>
                  Add Parameter
                </button>
              </div>

              {showParamForm && expandedType === et.id && (
                <div style={{ padding: '12px', backgroundColor: 'rgba(255,255,255,0.03)', borderRadius: '12px', marginBottom: '12px' }}>
                  <h5 style={{ marginTop: 0 }}>{editingParam ? 'Edit' : 'Create'} Parameter Definition</h5>
                  <div className="form-field">
                    <label className="form-label">Domain *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={paramForm.domain}
                      onChange={(e) => setParamForm({ ...paramForm, domain: e.target.value })}
                      placeholder="e.g., identity"
                    />
                  </div>
                  <div className="form-field">
                    <label className="form-label">Key *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={paramForm.key}
                      onChange={(e) => setParamForm({ ...paramForm, key: e.target.value })}
                      placeholder="e.g., name"
                    />
                  </div>
                  <div className="form-field">
                    <label className="form-label">Value Type *</label>
                    <select
                      className="form-input"
                      value={paramForm.value_type}
                      onChange={(e) => setParamForm({ ...paramForm, value_type: e.target.value as 'string' | 'number' | 'boolean' })}
                    >
                      <option value="string">String</option>
                      <option value="number">Number</option>
                      <option value="boolean">Boolean</option>
                    </select>
                  </div>
                  <div className="form-field">
                    <label className="form-label">Label</label>
                    <input
                      type="text"
                      className="form-input"
                      value={paramForm.label}
                      onChange={(e) => setParamForm({ ...paramForm, label: e.target.value })}
                      placeholder="Display label"
                    />
                  </div>
                  <div className="form-field">
                    <label className="form-label">Description</label>
                    <textarea
                      className="form-textarea"
                      value={paramForm.description}
                      onChange={(e) => setParamForm({ ...paramForm, description: e.target.value })}
                    />
                  </div>
                  <div className="form-field">
                    <label>
                      <input
                        type="checkbox"
                        checked={paramForm.required}
                        onChange={(e) => setParamForm({ ...paramForm, required: e.target.checked })}
                      /> Required
                    </label>
                  </div>
                  <div className="form-field">
                    <label>
                      <input
                        type="checkbox"
                        checked={paramForm.is_label}
                        onChange={(e) => setParamForm({ ...paramForm, is_label: e.target.checked })}
                      /> Is Label
                    </label>
                  </div>
                  <div className="form-field">
                    <label>
                      <input
                        type="checkbox"
                        checked={paramForm.is_unique}
                        onChange={(e) => setParamForm({ ...paramForm, is_unique: e.target.checked })}
                      /> Is Unique
                    </label>
                  </div>
                  <div className="form-field">
                    <label>
                      <input
                        type="checkbox"
                        checked={paramForm.is_searchable}
                        onChange={(e) => setParamForm({ ...paramForm, is_searchable: e.target.checked })}
                      /> Is Searchable
                    </label>
                  </div>
                  <div className="form-field">
                    <label>
                      <input
                        type="checkbox"
                        checked={paramForm.is_hidden}
                        onChange={(e) => setParamForm({ ...paramForm, is_hidden: e.target.checked })}
                      /> Is Hidden
                    </label>
                  </div>
                  <div className="form-field">
                    <label className="form-label">Default Value</label>
                    <input
                      type="text"
                      className="form-input"
                      value={paramForm.default_value}
                      onChange={(e) => setParamForm({ ...paramForm, default_value: e.target.value })}
                    />
                  </div>
                  <div className="form-field">
                    <label className="form-label">Validation (JSON)</label>
                    <textarea
                      className="form-textarea"
                      value={paramForm.validation}
                      onChange={(e) => setParamForm({ ...paramForm, validation: e.target.value })}
                      placeholder='{"min": 0, "max": 100}'
                    />
                  </div>
                  <div className="form-actions">
                    <button onClick={cancelEditParam} className="button button--secondary">Cancel</button>
                    <button
                      onClick={() => editingParam ? handleUpdateParam(et.id, editingParam.id) : handleCreateParam(et.id)}
                      className="button button--primary"
                      disabled={!paramForm.domain.trim() || !paramForm.key.trim()}
                    >
                      {editingParam ? 'Update' : 'Create'}
                    </button>
                  </div>
                </div>
              )}

              {et.parameter_definitions && et.parameter_definitions.length > 0 ? (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #ddd' }}>
                      <th style={{ textAlign: 'left', padding: '8px', fontSize: '12px' }}>Domain</th>
                      <th style={{ textAlign: 'left', padding: '8px', fontSize: '12px' }}>Key</th>
                      <th style={{ textAlign: 'left', padding: '8px', fontSize: '12px' }}>Type</th>
                      <th style={{ textAlign: 'left', padding: '8px', fontSize: '12px' }}>Label</th>
                      <th style={{ textAlign: 'left', padding: '8px', fontSize: '12px' }}>Required</th>
                      <th style={{ textAlign: 'left', padding: '8px', fontSize: '12px' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {et.parameter_definitions.map((param) => (
                      <tr key={param.id} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '8px', fontSize: '13px' }}>{param.domain}</td>
                        <td style={{ padding: '8px', fontSize: '13px' }}>{param.key}</td>
                        <td style={{ padding: '8px', fontSize: '13px' }}>{param.value_type}</td>
                        <td style={{ padding: '8px', fontSize: '13px' }}>{param.label || '-'}</td>
                        <td style={{ padding: '8px', fontSize: '13px' }}>{param.required ? 'Yes' : 'No'}</td>
                        <td style={{ padding: '8px', fontSize: '13px' }}>
                          <button onClick={() => { setEditingParam(param); setParamForm({ domain: param.domain, key: param.key, value_type: param.value_type as 'string' | 'number' | 'boolean', label: param.label, description: param.description || '', required: param.required, sort_order: param.sort_order, is_label: param.is_label, is_unique: param.is_unique, is_searchable: param.is_searchable, is_hidden: param.is_hidden, default_value: param.default_value || '', validation: param.validation ? JSON.stringify(param.validation) : '' }); setShowParamForm(true); }} className="button button--secondary" style={{ fontSize: '11px', padding: '4px 8px' }}>
                            Edit
                          </button>
                          <button onClick={() => handleDeleteParam(et.id, param.id)} className="button button--secondary" style={{ fontSize: '11px', padding: '4px 8px', color: '#c33' }}>
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p style={{ color: '#666', fontStyle: 'italic', fontSize: '13px' }}>No parameter definitions yet.</p>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
