import { useState, useEffect } from 'react';
import { View, createViewConfig, deleteViewConfig, updateView, updateViewConfig } from '../api/views';
import { listEntityTypes, listParameterDefinitions } from '../api/templates';
import { EntityType, ParameterDefinition } from '../types/template';

interface ViewConfigEditorProps {
  templateId: string;
  view: View;
  onSave: () => void;
  onCancel: () => void;
}

interface FilterParam {
  domain: string;
  key: string;
  operator: string;
  value_string?: string;
  value_number?: number;
  value_boolean?: boolean;
}

interface DisplaySlot {
  domain: string;
  key: string;
}

export function ViewConfigEditor({ templateId, view, onSave, onCancel }: ViewConfigEditorProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entityTypes, setEntityTypes] = useState<EntityType[]>([]);
  const [parameterDefinitions, setParameterDefinitions] = useState<Record<string, ParameterDefinition[]>>({});
  const [viewLabel, setViewLabel] = useState(view.label);
  const [viewDescription, setViewDescription] = useState(view.description || '');
  const [savingView, setSavingView] = useState(false);
  
  // Modal state
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [editingConfigId, setEditingConfigId] = useState<string | null>(null);
  const [configForm, setConfigForm] = useState({
    entity_type_id: '',
    filter_params: [] as FilterParam[],
    display_slots: [] as DisplaySlot[],
  });

  useEffect(() => {
    loadEntityTypesAndParameters();
  }, [templateId]);

  const loadEntityTypesAndParameters = async () => {
    setLoading(true);
    try {
      const types = await listEntityTypes(templateId);
      // Filter to only material entity types for selection
      const materialTypes = types.filter((t: EntityType) => t.kind === 'material');
      setEntityTypes(materialTypes);
      
      // Load parameter definitions for each material entity type
      const paramsMap: Record<string, ParameterDefinition[]> = {};
      for (const type of materialTypes) {
        const params = await listParameterDefinitions(templateId, type.id);
        paramsMap[type.id] = params;
      }
      setParameterDefinitions(paramsMap);
    } catch (err) {
      setError('Failed to load entity types');
    } finally {
      setLoading(false);
    }
  };

  const handleAddConfig = async () => {
    if (!configForm.entity_type_id) {
      setError('Please select an entity type');
      return;
    }

    setLoading(true);
    try {
      await createViewConfig(templateId, view.id, {
        entity_type_id: configForm.entity_type_id,
        filter_params: configForm.filter_params,
        display_slots: configForm.display_slots,
        sort_order: view.configs.length,
      });
      setShowConfigModal(false);
      setConfigForm({ entity_type_id: '', filter_params: [], display_slots: [] });
      // Reload view data to get updated configs without navigating away
      onSave();
    } catch (err) {
      setError('Failed to create view config');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConfig = async (configId: string) => {
    if (!confirm('Delete this view config?')) return;
    try {
      await deleteViewConfig(templateId, view.id, configId);
      onSave();
    } catch (err) {
      setError('Failed to delete view config');
    }
  };

  const handleEditConfig = (configId: string) => {
    const config = view.configs.find(c => c.id === configId);
    if (config) {
      setConfigForm({
        entity_type_id: config.entity_type_id || '',
        filter_params: (config.filter_params || []).map(p => ({
          domain: p.domain,
          key: p.key,
          operator: p.operator || '=',
          value_string: p.value_string,
          value_number: p.value_number,
          value_boolean: p.value_boolean,
        })),
        display_slots: (config.display_slots || []).map(s => ({ domain: s.domain, key: s.key })),
      });
      setEditingConfigId(configId);
      setShowConfigModal(true);
    }
  };

  const handleMoveFilter = (index: number, direction: 'up' | 'down') => {
    const newFilters = [...configForm.filter_params];
    if (direction === 'up' && index > 0) {
      [newFilters[index - 1], newFilters[index]] = [newFilters[index], newFilters[index - 1]];
    } else if (direction === 'down' && index < newFilters.length - 1) {
      [newFilters[index], newFilters[index + 1]] = [newFilters[index + 1], newFilters[index]];
    }
    setConfigForm({ ...configForm, filter_params: newFilters });
  };

  const handleMoveSlot = (index: number, direction: 'up' | 'down') => {
    const newSlots = [...configForm.display_slots];
    if (direction === 'up' && index > 0) {
      [newSlots[index - 1], newSlots[index]] = [newSlots[index], newSlots[index - 1]];
    } else if (direction === 'down' && index < newSlots.length - 1) {
      [newSlots[index], newSlots[index + 1]] = [newSlots[index + 1], newSlots[index]];
    }
    setConfigForm({ ...configForm, display_slots: newSlots });
  };

  const handleCancelEditConfig = () => {
    setShowConfigModal(false);
    setEditingConfigId(null);
    setConfigForm({ entity_type_id: '', filter_params: [], display_slots: [] });
  };

  const handleUpdateConfig = async () => {
    if (!editingConfigId || !configForm.entity_type_id) {
      setError('Please select an entity type');
      return;
    }

    setLoading(true);
    try {
      await updateViewConfig(templateId, view.id, editingConfigId, {
        entity_type_id: configForm.entity_type_id,
        filter_params: configForm.filter_params,
        display_slots: configForm.display_slots,
      });
      setShowConfigModal(false);
      setEditingConfigId(null);
      setConfigForm({ entity_type_id: '', filter_params: [], display_slots: [] });
      onSave();
    } catch (err) {
      setError('Failed to update view config');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveView = async () => {
    setSavingView(true);
    setError(null);
    try {
      await updateView(templateId, view.id, {
        label: viewLabel,
        description: viewDescription,
      });
      onSave();
    } catch (err) {
      setError('Failed to update view');
    } finally {
      setSavingView(false);
    }
  };

  const selectedEntityType = entityTypes.find((et: EntityType) => et.id === configForm.entity_type_id);
  const availableParams = parameterDefinitions[configForm.entity_type_id] || [];

  return (
    <div className="card">
      <h2 className="card__title">View Configurations</h2>

      {error && (
        <div className="state-message">
          <p className="state-message__text state-message__text--error">{error}</p>
          <button onClick={() => setError(null)} className="button button--secondary">
            Dismiss
          </button>
        </div>
      )}

      {/* View Details Section */}
      <div className="card__section">
        <h3 className="card__section-title">View Details</h3>
        
        <div className="form-field">
          <label className="form-label">View Key</label>
          <input
            type="text"
            className="form-input"
            value={view.view_key}
            disabled
            title="View key cannot be modified"
          />
        </div>

        <div className="form-field">
          <label className="form-label">Label *</label>
          <input
            type="text"
            className="form-input"
            value={viewLabel}
            onChange={(e) => setViewLabel(e.target.value)}
            placeholder="View label"
          />
        </div>

        <div className="form-field">
          <label className="form-label">Description</label>
          <textarea
            className="form-textarea"
            value={viewDescription}
            onChange={(e) => setViewDescription(e.target.value)}
            placeholder="Description of this view"
          />
        </div>

        <button
          onClick={handleSaveView}
          disabled={savingView}
          className="button button--primary"
        >
          {savingView ? 'Saving...' : 'Save View Details'}
        </button>
      </div>

      {/* Existing configs */}
      <div className="card__section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 className="card__section-title">Existing Configurations</h3>
          <button
            onClick={() => {
              setEditingConfigId(null);
              setConfigForm({ entity_type_id: '', filter_params: [], display_slots: [] });
              setShowConfigModal(true);
            }}
            className="button button--primary"
          >
            Add Configuration
          </button>
        </div>
        {view.configs.length === 0 ? (
          <p className="state-message__text">No configurations yet.</p>
        ) : (
          <div className="template-grid">
            {view.configs.map(config => {
              const entityType = entityTypes.find((et: EntityType) => et.id === config.entity_type_id);
              return (
                <div key={config.id} className="card template-card">
                  <div className="template-card__content">
                    <div className="template-card__title">
                      {entityType?.name || 'Unknown Entity Type'}
                    </div>
                    <p className="template-card__description">
                      {config.filter_params?.length || 0} filter parameters • {config.display_slots?.length || 0} display slots
                    </p>
                    {config.filter_params && config.filter_params.length > 0 && (
                      <p className="template-card__meta">
                        Filters: {config.filter_params.map(p => p.key).join(', ')}
                      </p>
                    )}
                    {config.display_slots && config.display_slots.length > 0 && (
                      <p className="template-card__meta">
                        Display: {config.display_slots.map(s => s.key).join(', ')}
                      </p>
                    )}
                  </div>
                  <div className="template-card__actions">
                    <button
                      onClick={() => handleEditConfig(config.id)}
                      className="button button--secondary"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteConfig(config.id)}
                      className="button button--danger"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Config Modal */}
      {showConfigModal && (
        <div style={{ position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', backgroundColor: 'rgba(10,10,10,0.95)', border: '1px solid rgba(255,255,255,0.1)', padding: '24px', borderRadius: '18px', boxShadow: '0 8px 32px rgba(0,0,0,0.4)', zIndex: 1000, width: '90vw', height: '90vh', overflowY: 'auto' }}>
          <h3 style={{ marginTop: 0 }}>{editingConfigId ? 'Edit Configuration' : 'Add Configuration'}</h3>
          
          <div className="form-field">
            <label className="form-label">Entity Type *</label>
            <select
              className="form-input"
              value={configForm.entity_type_id}
              onChange={(e) => setConfigForm({ ...configForm, entity_type_id: e.target.value })}
            >
              <option value="">Select entity type...</option>
              {entityTypes.map((et: EntityType) => (
                <option key={et.id} value={et.id}>
                  {et.name} ({et.kind})
                </option>
              ))}
            </select>
          </div>

          {selectedEntityType && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '24px' }}>
              {/* Filters Section */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h4 style={{ margin: 0 }}>Filter Parameters</h4>
                  <button
                    onClick={() => {
                      if (availableParams.length > 0) {
                        const param = availableParams[0];
                        setConfigForm({
                          ...configForm,
                          filter_params: [...configForm.filter_params, {
                            domain: param.domain,
                            key: param.key,
                            operator: '=',
                            value_string: param.value_type === 'string' ? '' : undefined,
                            value_number: param.value_type === 'number' ? 0 : undefined,
                            value_boolean: param.value_type === 'boolean' ? false : undefined,
                          }]
                        });
                      }
                    }}
                    className="button button--primary"
                    style={{ fontSize: '12px', padding: '4px 12px' }}
                  >
                    Add Filter
                  </button>
                </div>
                {configForm.filter_params.length === 0 ? (
                  <p style={{ color: '#666', fontSize: '14px' }}>No filters yet. Click "Add Filter" to add one.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {configForm.filter_params.map((fp, index) => {
                      const param = availableParams.find((p: ParameterDefinition) => p.domain === fp.domain && p.key === fp.key);
                      return (
                        <div key={index} className="card template-card" style={{ padding: '12px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <strong style={{ fontSize: '14px' }}>{fp.domain}:{fp.key}</strong>
                            <div style={{ display: 'flex', gap: '4px' }}>
                              <button
                                onClick={() => handleMoveFilter(index, 'up')}
                                disabled={index === 0}
                                className="button button--icon"
                                style={{ padding: '2px 6px', fontSize: '12px' }}
                                title="Move up"
                              >
                                ↑
                              </button>
                              <button
                                onClick={() => handleMoveFilter(index, 'down')}
                                disabled={index === configForm.filter_params.length - 1}
                                className="button button--icon"
                                style={{ padding: '2px 6px', fontSize: '12px' }}
                                title="Move down"
                              >
                                ↓
                              </button>
                              <button
                                onClick={() => setConfigForm({
                                  ...configForm,
                                  filter_params: configForm.filter_params.filter((_, i) => i !== index)
                                })}
                                className="button button--danger"
                                style={{ padding: '2px 8px', fontSize: '12px' }}
                              >
                                Remove
                              </button>
                            </div>
                          </div>
                          <div style={{ marginBottom: '8px' }}>
                            <label style={{ fontSize: '12px', color: '#999' }}>Parameter</label>
                            <select
                              className="form-input"
                              style={{ fontSize: '13px' }}
                              value={availableParams.find((p: ParameterDefinition) => p.domain === fp.domain && p.key === fp.key)?.id || ''}
                              onChange={(e) => {
                                const newParam = availableParams.find((p: ParameterDefinition) => p.id === e.target.value);
                                if (newParam) {
                                  const newFilters = [...configForm.filter_params];
                                  newFilters[index] = {
                                    domain: newParam.domain,
                                    key: newParam.key,
                                    operator: fp.operator,
                                    value_string: newParam.value_type === 'string' ? '' : undefined,
                                    value_number: newParam.value_type === 'number' ? 0 : undefined,
                                    value_boolean: newParam.value_type === 'boolean' ? false : undefined,
                                  };
                                  setConfigForm({ ...configForm, filter_params: newFilters });
                                }
                              }}
                            >
                              {availableParams.map((p: ParameterDefinition) => (
                                <option key={p.id} value={p.id}>
                                  {p.label || p.key} ({p.domain}:{p.key} - {p.value_type})
                                </option>
                              ))}
                            </select>
                          </div>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <div style={{ flex: 1 }}>
                              <label style={{ fontSize: '12px', color: '#999' }}>Operator</label>
                              <select
                                className="form-input"
                                style={{ fontSize: '13px' }}
                                value={fp.operator}
                                onChange={(e) => {
                                  const newFilters = [...configForm.filter_params];
                                  newFilters[index] = { ...fp, operator: e.target.value };
                                  setConfigForm({ ...configForm, filter_params: newFilters });
                                }}
                              >
                                <option value="=">=</option>
                                <option value="!=">!=</option>
                                <option value=">">&gt;</option>
                                <option value="<">&lt;</option>
                                <option value=">=">&gt;=</option>
                                <option value="<=">&lt;=</option>
                                <option value="contains">contains</option>
                              </select>
                            </div>
                            <div style={{ flex: 3 }}>
                              <label style={{ fontSize: '12px', color: '#999' }}>Value</label>
                              {param?.value_type === 'string' && (
                                <input
                                  type="text"
                                  className="form-input"
                                  style={{ fontSize: '13px' }}
                                  value={fp.value_string || ''}
                                  onChange={(e) => {
                                    const newFilters = [...configForm.filter_params];
                                    newFilters[index] = { ...fp, value_string: e.target.value };
                                    setConfigForm({ ...configForm, filter_params: newFilters });
                                  }}
                                  placeholder="Value"
                                />
                              )}
                              {param?.value_type === 'number' && (
                                <input
                                  type="number"
                                  className="form-input"
                                  style={{ fontSize: '13px' }}
                                  value={fp.value_number || ''}
                                  onChange={(e) => {
                                    const newFilters = [...configForm.filter_params];
                                    newFilters[index] = { ...fp, value_number: parseFloat(e.target.value) || 0 };
                                    setConfigForm({ ...configForm, filter_params: newFilters });
                                  }}
                                  placeholder="Value"
                                />
                              )}
                              {param?.value_type === 'boolean' && (
                                <select
                                  className="form-input"
                                  style={{ fontSize: '13px' }}
                                  value={fp.value_boolean?.toString() || 'false'}
                                  onChange={(e) => {
                                    const newFilters = [...configForm.filter_params];
                                    newFilters[index] = { ...fp, value_boolean: e.target.value === 'true' };
                                    setConfigForm({ ...configForm, filter_params: newFilters });
                                  }}
                                >
                                  <option value="true">True</option>
                                  <option value="false">False</option>
                                </select>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Display Slots Section */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h4 style={{ margin: 0 }}>Display Slots</h4>
                  <button
                    onClick={() => {
                      if (availableParams.length > 0) {
                        const param = availableParams[0];
                        setConfigForm({
                          ...configForm,
                          display_slots: [...configForm.display_slots, { domain: param.domain, key: param.key }]
                        });
                      }
                    }}
                    className="button button--primary"
                    style={{ fontSize: '12px', padding: '4px 12px' }}
                  >
                    Add Slot
                  </button>
                </div>
                {configForm.display_slots.length === 0 ? (
                  <p style={{ color: '#666', fontSize: '14px' }}>No display slots yet. Click "Add Slot" to add one.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {configForm.display_slots.map((ds, index) => {
                      const param = availableParams.find((p: ParameterDefinition) => p.domain === ds.domain && p.key === ds.key);
                      return (
                        <div key={index} className="card template-card" style={{ padding: '8px', minHeight: '100px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                            <strong style={{ fontSize: '13px' }}>{ds.domain}:{ds.key}</strong>
                            <div style={{ display: 'flex', gap: '4px' }}>
                              <button
                                onClick={() => handleMoveSlot(index, 'up')}
                                disabled={index === 0}
                                className="button button--icon"
                                style={{ padding: '2px 6px', fontSize: '12px' }}
                                title="Move up"
                              >
                                ↑
                              </button>
                              <button
                                onClick={() => handleMoveSlot(index, 'down')}
                                disabled={index === configForm.display_slots.length - 1}
                                className="button button--icon"
                                style={{ padding: '2px 6px', fontSize: '12px' }}
                                title="Move down"
                              >
                                ↓
                              </button>
                              <button
                                onClick={() => setConfigForm({
                                  ...configForm,
                                  display_slots: configForm.display_slots.filter((_, i) => i !== index)
                                })}
                                className="button button--danger"
                                style={{ padding: '2px 8px', fontSize: '12px' }}
                              >
                                Remove
                              </button>
                            </div>
                          </div>
                          <div>
                            <select
                              className="form-input"
                              style={{ fontSize: '13px' }}
                              value={availableParams.find((p: ParameterDefinition) => p.domain === ds.domain && p.key === ds.key)?.id || ''}
                              onChange={(e) => {
                                const newParam = availableParams.find((p: ParameterDefinition) => p.id === e.target.value);
                                if (newParam) {
                                  const newSlots = [...configForm.display_slots];
                                  newSlots[index] = { domain: newParam.domain, key: newParam.key };
                                  setConfigForm({ ...configForm, display_slots: newSlots });
                                }
                              }}
                            >
                              {availableParams.map((p: ParameterDefinition) => (
                                <option key={p.id} value={p.id}>
                                  {p.label || p.key} ({p.domain}:{p.key})
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="form-actions" style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            <button onClick={handleCancelEditConfig} disabled={loading} className="button button--secondary">
              Cancel
            </button>
            <button
              onClick={editingConfigId ? handleUpdateConfig : handleAddConfig}
              disabled={loading}
              className="button button--primary"
            >
              {loading ? 'Saving...' : editingConfigId ? 'Update Configuration' : 'Create Configuration'}
            </button>
          </div>
        </div>
      )}

      <div className="form-actions">
        <button onClick={onCancel} className="button button--secondary">
          Done
        </button>
      </div>
    </div>
  );
}
