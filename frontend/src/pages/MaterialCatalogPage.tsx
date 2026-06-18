import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getProjectTemplate } from '../api/projects';
import { getEntitiesByViewConfig, getEntityParameters, deleteEntity } from '../api/entities';
import { ProjectTemplateDetail, View, ViewConfig } from '../types/template';
import { Entity, EntityParameter } from '../types/entity';

type MaterialCatalogPageProps = {
  projectId: string;
};

export function MaterialCatalogPage({ projectId }: MaterialCatalogPageProps) {
  const [template, setTemplate] = useState<ProjectTemplateDetail | null>(null);
  const [materialCatalogView, setMaterialCatalogView] = useState<View | null>(null);
  const [selectedConfig, setSelectedConfig] = useState<ViewConfig | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [entityParameters, setEntityParameters] = useState<Record<string, EntityParameter[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteConfirmEntity, setDeleteConfirmEntity] = useState<Entity | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const templateData = await getProjectTemplate(projectId);
        setTemplate(templateData);
        
        // Find material_catalog view
        const materialView = templateData.views.find(v => v.view_key === 'material_catalog');
        if (!materialView) {
          setError('Material catalog view not found in template');
          return;
        }
        
        setMaterialCatalogView(materialView);
        
        // Auto-select if only one config
        if (materialView.configs.length === 1) {
          setSelectedConfig(materialView.configs[0]);
        }
      } catch (err) {
        setError('Could not load template');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [projectId]);

  useEffect(() => {
    if (!selectedConfig) return;

    const loadEntities = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getEntitiesByViewConfig(projectId, selectedConfig.id);
        setEntities(data);
        
        // Load parameters for all entities
        const paramsMap: Record<string, EntityParameter[]> = {};
        await Promise.all(
          data.map(async (entity) => {
            try {
              const params = await getEntityParameters(projectId, entity.id);
              paramsMap[entity.id] = params;
            } catch (err) {
              paramsMap[entity.id] = [];
            }
          })
        );
        setEntityParameters(paramsMap);
      } catch (err) {
        setError('Could not load entities');
      } finally {
        setLoading(false);
      }
    };

    loadEntities();
  }, [projectId, selectedConfig]);

  // Helper to resolve display slot value from entity parameters
  const getDisplaySlotValue = (entity: Entity, slotIndex: number): string => {
    const displaySlots = selectedConfig?.display_slots;
    if (!displaySlots || !Array.isArray(displaySlots) || slotIndex >= displaySlots.length) {
      return '';
    }

    const slot = displaySlots[slotIndex];
    if (!slot || typeof slot !== 'object') {
      return '';
    }

    const source = (slot as any).source || 'parameter'; // Default to 'parameter' if not specified
    const domain = (slot as any).domain;
    const key = (slot as any).key;

    if (source !== 'parameter' || !domain || !key) {
      return '';
    }

    const params = entityParameters[entity.id] || [];
    const param = params.find((p: EntityParameter) => p.domain === domain && p.key === key);
    
    if (!param) {
      return '';
    }

    // Return the appropriate value type
    if (param.value_string !== null && param.value_string !== undefined) {
      return param.value_string;
    }
    if (param.value_number !== null && param.value_number !== undefined) {
      return String(param.value_number);
    }
    if (param.value_boolean !== null && param.value_boolean !== undefined) {
      return String(param.value_boolean);
    }

    return '';
  };

  // Helper to get display slot label from parameter definitions
  const getDisplaySlotLabel = (slotIndex: number): string => {
    const displaySlots = selectedConfig?.display_slots;
    if (!displaySlots || !Array.isArray(displaySlots) || slotIndex >= displaySlots.length) {
      return '';
    }

    const slot = displaySlots[slotIndex];
    if (!slot || typeof slot !== 'object') {
      return '';
    }

    const key = (slot as any).key;
    return key || '';
  };

  const filteredEntities = searchQuery
    ? entities.filter((e: Entity) => {
        const slot0 = getDisplaySlotValue(e, 0);
        const slot1 = getDisplaySlotValue(e, 1);
        const searchLower = searchQuery.toLowerCase();
        return (
          slot0.toLowerCase().includes(searchLower) ||
          slot1.toLowerCase().includes(searchLower) ||
          e.id.toLowerCase().includes(searchLower)
        );
      })
    : entities;

  const handleDeleteClick = (entity: Entity) => {
    setDeleteConfirmEntity(entity);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirmEntity) return;
    
    setIsDeleting(true);
    setError(null);
    try {
      await deleteEntity(projectId, deleteConfirmEntity.id);
      setEntities(entities.filter((e: Entity) => e.id !== deleteConfirmEntity.id));
      setDeleteConfirmEntity(null);
    } catch (err) {
      setError('Could not delete material');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmEntity(null);
  };

  if (loading && !materialCatalogView) {
    return (
      <div className="card state-message">
        <p className="state-message__text">Loading material catalog...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card state-message">
        <p className="state-message__text">{error}</p>
        <button onClick={() => window.location.reload()} className="button button--secondary">
          Retry
        </button>
      </div>
    );
  }

  // Show group selection if multiple configs and none selected
  if (materialCatalogView && materialCatalogView.configs.length > 1 && !selectedConfig) {
    return (
      <div>
        <h2 className="card-title">Material Catalog</h2>
        <p className="card-description">Select a material group to view materials.</p>
        <div className="project-grid">
          {materialCatalogView.configs.map((config: ViewConfig) => {
            const entityType = template?.entity_types.find((et) => et.id === config.entity_type_id);
            return (
              <div key={config.id} className="card project-card">
                <h3 className="project-card__title">{entityType?.name || 'Unknown'}</h3>
                <p className="project-card__description">{entityType?.kind || ''}</p>
                <button
                  onClick={() => setSelectedConfig(config)}
                  className="button button--primary"
                >
                  View Materials
                </button>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Show entity list when config is selected
  return (
    <div>
      <div className="catalog-header">
        <div className="catalog-header__title">
          <h2 className="card-title">
            {template?.entity_types.find((et) => et.id === selectedConfig?.entity_type_id)?.name || 'Materials'}
          </h2>
          <p className="card-description">Create and manage project materials.</p>
        </div>
        {selectedConfig && (
          <Link
            to={`/projects/${projectId}/materials/new?configId=${selectedConfig.id}`}
            className="button button--primary"
          >
            + New Material
          </Link>
        )}
      </div>

      {materialCatalogView && materialCatalogView.configs.length > 1 && (
        <button
          onClick={() => setSelectedConfig(null)}
          className="button button--secondary"
          style={{ marginBottom: '16px' }}
        >
          ← Back to Groups
        </button>
      )}

      <div className="mb-6">
        <input
          type="text"
          placeholder="Search materials..."
          value={searchQuery}
          onChange={(e: any) => setSearchQuery((e.target as HTMLInputElement).value)}
          className="form-input"
        />
      </div>

      {filteredEntities.length === 0 ? (
        <div className="card state-message">
          <p className="state-message__text">
            {entities.length === 0 ? 'No materials found.' : 'No materials match your search.'}
          </p>
        </div>
      ) : (
        <div className="project-grid">
          {filteredEntities.map((entity: Entity) => (
            <div key={entity.id} className="card material-card">
              <div className="material-catalog-card__info-region">
                <div className="material-catalog-card__title-region">
                  <h3 className="material-catalog-card__title">{getDisplaySlotValue(entity, 0) || '<title>'}</h3>
                  <p className="material-catalog-card__subtitle">{getDisplaySlotValue(entity, 1) || '<subtitle>'}</p>
                </div>
                <div className="material-catalog-card__data-region">
                  {[2, 3, 4].map((slotIndex) => {
                    const label = getDisplaySlotLabel(slotIndex);
                    const value = getDisplaySlotValue(entity, slotIndex);
                    if (!label && !value) return null;
                    return (
                      <div key={slotIndex} className="material-catalog-card__data-row">
                        <span className="material-catalog-card__data-label">{label || ''}:</span>
                        <span className="material-catalog-card__data-value">{value || ''}</span>
                      </div>
                    );
                  })}
                </div>
                <div className="material-catalog-card__actions">
                  <Link
                    to={`/projects/${projectId}/materials/${entity.id}/edit?configId=${selectedConfig?.id}`}
                    className="button button--secondary"
                    style={{ padding: '1px 4px', fontSize: '10px' }}
                  >
                    Edit
                  </Link>
                  <button
                    onClick={() => handleDeleteClick(entity)}
                    className="button button--danger"
                    style={{ padding: '1px 4px', fontSize: '10px' }}
                  >
                    Delete
                  </button>
                </div>
              </div>
              <div className="material-catalog-card__image-region" />
            </div>
          ))}
        </div>
      )}
      
      {deleteConfirmEntity && (
        <div className="modal-overlay">
          <div className="card" style={{ maxWidth: '400px', margin: 'auto' }}>
            <h3 className="card-title mb-4">Delete Material</h3>
            <p className="mb-4">
              Are you sure you want to delete "{getDisplaySlotValue(deleteConfirmEntity, 0) || deleteConfirmEntity.id}"? This action cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                onClick={handleDeleteCancel}
                disabled={isDeleting}
                className="button button--secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                disabled={isDeleting}
                className="button button--danger"
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
