import { useState, useEffect } from 'react';
import { View, createViewConfig, deleteViewConfig } from '../api/views';
import { listEntityTypes } from '../api/templates';
import { EntityType, ParameterDefinition } from '../types/template';

interface ViewConfigEditorProps {
  templateId: string;
  view: View;
  onSave: () => void;
  onCancel: () => void;
}

export function ViewConfigEditor({ templateId, view, onSave, onCancel }: ViewConfigEditorProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entityTypes, setEntityTypes] = useState<EntityType[]>([]);
  const [selectedEntityTypeId, setSelectedEntityTypeId] = useState<string | null>(null);
  const [selectedParams, setSelectedParams] = useState<string[]>([]);
  const [displaySlots, setDisplaySlots] = useState<string[]>([]);

  useEffect(() => {
    loadEntityTypes();
  }, [templateId]);

  const loadEntityTypes = async () => {
    setLoading(true);
    try {
      const types = await listEntityTypes(templateId);
      setEntityTypes(types);
    } catch (err) {
      setError('Failed to load entity types');
    } finally {
      setLoading(false);
    }
  };

  const handleAddConfig = async () => {
    if (!selectedEntityTypeId) {
      setError('Please select an entity type');
      return;
    }

    setLoading(true);
    try {
      // Generate filter_params from selected parameters
      const filterParams = selectedParams.map(param => {
        const [domain, key] = param.split('.');
        return { domain, key };
      });

      // Generate display_slots from selected display slots
      const displaySlotsData = displaySlots.map(slot => {
        const [domain, key] = slot.split('.');
        return { domain, key };
      });

      await createViewConfig(templateId, view.id, {
        entity_type_id: selectedEntityTypeId,
        filter_params: filterParams,
        display_slots: displaySlotsData,
        sort_order: view.configs.length,
      });
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

  const selectedEntityType = entityTypes.find(et => et.id === selectedEntityTypeId);
  const availableParams = selectedEntityType?.parameter_definitions || [];

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

      {/* Add new config form */}
      <div className="card__section">
        <h3 className="card__section-title">Add Configuration</h3>
        
        <div className="form-field">
          <label className="form-label">Entity Type *</label>
          <select
            className="form-input"
            value={selectedEntityTypeId || ''}
            onChange={(e) => setSelectedEntityTypeId(e.target.value || null)}
          >
            <option value="">Select entity type...</option>
            {entityTypes.map(et => (
              <option key={et.id} value={et.id}>
                {et.name} ({et.kind})
              </option>
            ))}
          </select>
        </div>

        {selectedEntityType && (
          <>
            <div className="form-field">
              <label className="form-label">Filter Parameters</label>
              <p className="form-hint">Select parameters to use as filters</p>
              <div className="checkbox-group">
                {availableParams.map(param => (
                  <label key={param.id} className="checkbox">
                    <input
                      type="checkbox"
                      checked={selectedParams.includes(`${param.domain}.${param.key}`)}
                      onChange={(e) => {
                        const paramKey = `${param.domain}.${param.key}`;
                        if (e.target.checked) {
                          setSelectedParams([...selectedParams, paramKey]);
                        } else {
                          setSelectedParams(selectedParams.filter(p => p !== paramKey));
                        }
                      }}
                    />
                    <span>{param.label || param.key}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="form-field">
              <label className="form-label">Display Slots</label>
              <p className="form-hint">Select parameters to display in the view</p>
              <div className="checkbox-group">
                {availableParams.map(param => (
                  <label key={param.id} className="checkbox">
                    <input
                      type="checkbox"
                      checked={displaySlots.includes(`${param.domain}.${param.key}`)}
                      onChange={(e) => {
                        const paramKey = `${param.domain}.${param.key}`;
                        if (e.target.checked) {
                          setDisplaySlots([...displaySlots, paramKey]);
                        } else {
                          setDisplaySlots(displaySlots.filter(p => p !== paramKey));
                        }
                      }}
                    />
                    <span>{param.label || param.key}</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              onClick={handleAddConfig}
              disabled={loading}
              className="button button--primary"
            >
              Add Configuration
            </button>
          </>
        )}
      </div>

      {/* Existing configs */}
      <div className="card__section">
        <h3 className="card__section-title">Existing Configurations</h3>
        {view.configs.length === 0 ? (
          <p className="state-message__text">No configurations yet.</p>
        ) : (
          <div className="list">
            {view.configs.map(config => {
              const entityType = entityTypes.find(et => et.id === config.entity_type_id);
              return (
                <div key={config.id} className="list-item">
                  <div className="list-item__content">
                    <div className="list-item__title">
                      {entityType?.name || 'Unknown Entity Type'}
                    </div>
                    <div className="list-item__subtitle">
                      {config.filter_params?.length || 0} filters • {config.display_slots?.length || 0} display slots
                    </div>
                  </div>
                  <div className="list-item__actions">
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

      <div className="form-actions">
        <button onClick={onCancel} className="button button--secondary">
          Done
        </button>
      </div>
    </div>
  );
}
