import { useState, useEffect, useRef } from 'react';
import { getProjectTemplate } from '../api/projects';
import { getEntities, getEntitiesResolved } from '../api/entities';
import { ProjectTemplateDetail, EntityType, ParameterDefinition, View, ViewConfig } from '../types/template';
import { Entity, EntityParameter } from '../types/entity';
import { EntityDetailModal } from './EntityDetailModal';

type EntitySelectorModalProps = {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
  onSelection: (result: EntitySelectorResult) => void;
  initialType?: 'material' | 'recipe';
  initialGroup?: string;
  initialDisplayParameter?: { domain: string; key: string };
  preselectedParameters?: Array<{ domain: string; key: string }>;
};

export type EntitySelectorResult = {
  entity_id: string;
  type: 'material' | 'recipe';
  group: string;
  parameters: Array<{
    domain: string;
    key: string;
    value_string?: string | null;
    value_number?: number | null;
    value_boolean?: boolean | null;
  }>;
};

export function EntitySelectorModal({
  projectId,
  isOpen,
  onClose,
  onSelection,
  initialType,
  initialGroup,
  initialDisplayParameter,
  preselectedParameters = [],
}: EntitySelectorModalProps) {
  const [template, setTemplate] = useState<ProjectTemplateDetail | null>(null);
  const [selectedType, setSelectedType] = useState<'material' | 'recipe'>(initialType || 'material');
  const [selectedGroup, setSelectedGroup] = useState<string>(initialGroup || '');
  const [displayParameter, setDisplayParameter] = useState<{ domain: string; key: string }>(
    initialDisplayParameter || { domain: '', key: '' }
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [entities, setEntities] = useState<Entity[]>([]);
  const [entityParameters, setEntityParameters] = useState<Record<string, EntityParameter[]>>({});
  const [loading, setLoading] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const entityListRef = useRef<HTMLDivElement>(null);

  // Load template
  useEffect(() => {
    if (!isOpen) return;
    const loadTemplate = async () => {
      try {
        const templateData = await getProjectTemplate(projectId);
        setTemplate(templateData);
      } catch (err) {
        console.error('Failed to load template:', err);
      }
    };
    loadTemplate();
  }, [projectId, isOpen]);

  // Load entities when type, group, or template changes
  useEffect(() => {
    if (!isOpen || !template) return;
    loadEntities();
  }, [projectId, selectedType, selectedGroup, template, isOpen]);

  // Auto-focus entity list when modal opens
  useEffect(() => {
    if (isOpen && entityListRef.current) {
      entityListRef.current.focus();
    }
  }, [isOpen]);

  const loadEntities = async () => {
    setLoading(true);
    try {
      // Load base entity data (lightweight)
      const data = await getEntities(projectId, selectedType);
      setEntities(data);

      // Load resolved entities with parameters in bulk
      if (data.length > 0) {
        const entityIds = data.map(e => e.id);
        const resolvedEntities = await getEntitiesResolved(entityIds);
        
        // Map parameters from resolved entities
        const paramsMap: Record<string, EntityParameter[]> = {};
        resolvedEntities.forEach((entity) => {
          const params = entity.parameters || [];
          // Add system parameters (id and group)
          paramsMap[entity.id] = [
            {
              id: 'sys_id',
              entity_id: entity.id,
              domain: '__system__',
              key: 'id',
              value_string: entity.id,
              created_at: '',
              updated_at: '',
            },
            {
              id: 'sys_group',
              entity_id: entity.id,
              domain: '__system__',
              key: 'group',
              value_string: entity.group,
              created_at: '',
              updated_at: '',
            },
            ...params,
          ];
        });
        setEntityParameters(paramsMap);
      } else {
        setEntityParameters({});
      }
    } catch (err) {
      console.error('Failed to load entities:', err);
    } finally {
      setLoading(false);
    }
  };

  // Get available groups for selected type
  const getAvailableGroups = () => {
    if (!template) return [];
    // Get groups from actual entities
    const entityGroups = new Set(entities.map((e: Entity) => e.group));
    return Array.from(entityGroups);
  };

  // Get available parameters for display parameter selector
  const getAvailableParameters = () => {
    if (!template) return [];
    const entityTypes = template.entity_types.filter((et: EntityType) => et.kind === selectedType);
    const allParams: ParameterDefinition[] = [];
    entityTypes.forEach((et: EntityType) => {
      allParams.push(...et.parameter_definitions);
    });
    return allParams;
  };

  // Get searchable parameter definitions
  const getSearchableParameters = () => {
    if (!template) return [];
    const entityTypes = template.entity_types.filter((et: EntityType) => et.kind === selectedType);
    const allParams: ParameterDefinition[] = [];
    entityTypes.forEach((et: EntityType) => {
      allParams.push(...et.parameter_definitions.filter((pd: ParameterDefinition) => pd.is_searchable));
    });
    return allParams;
  };

  // Filter entities based on search query
  const filteredEntities = entities.filter((e: Entity) => {
    // First filter by group if a specific group is selected
    if (selectedGroup && selectedGroup !== '') {
      if (e.group !== selectedGroup) {
        return false;
      }
    }
    
    // Then filter by search query if provided
    if (searchQuery) {
      const searchLower = searchQuery.toLowerCase();
      const searchableParams = getSearchableParameters();
      const params = entityParameters[e.id] || [];
      
      // Check if any searchable parameter matches
      for (const paramDef of searchableParams) {
        const param = params.find((p: EntityParameter) => 
          p.domain === paramDef.domain && p.key === paramDef.key
        );
        if (param) {
          let value = '';
          if (param.value_string !== null && param.value_string !== undefined) {
            value = param.value_string;
          } else if (param.value_number !== null && param.value_number !== undefined) {
            value = String(param.value_number);
          } else if (param.value_boolean !== null && param.value_boolean !== undefined) {
            value = String(param.value_boolean);
          }
          if (value.toLowerCase().includes(searchLower)) {
            return true;
          }
        }
      }
      
      // Also check entity ID
      return e.id.toLowerCase().includes(searchLower);
    }
    
    return true;
  });

  // Get the appropriate view config for the current type and group
  const getViewConfig = (): ViewConfig | null => {
    if (!template) return null;
    
    const viewKey = selectedType === 'material' ? 'material_catalog' : 'recipe_catalog';
    const view = template.views.find(v => v.view_key === viewKey);
    if (!view) return null;
    
    // Find config matching the selected group, or use the first config if no group selected
    if (selectedGroup) {
      const config = view.configs.find(c => c.entity_type_id === selectedGroup);
      if (config) return config;
    }
    
    // Return first config if no group selected or no match found
    return view.configs[0] || null;
  };

  // Helper to get display slot value from entity parameters
  const getDisplaySlotValue = (entity: Entity, slotIndex: number): string => {
    const viewConfig = getViewConfig();
    const displaySlots = viewConfig?.display_slots;
    if (!displaySlots || !Array.isArray(displaySlots) || slotIndex >= displaySlots.length) {
      return entity.id;
    }

    const slot = displaySlots[slotIndex];
    if (!slot || typeof slot !== 'object') {
      return entity.id;
    }

    const source = (slot as any).source || 'parameter';
    const domain = (slot as any).domain;
    const key = (slot as any).key;

    if (source !== 'parameter' || !domain || !key) {
      return entity.id;
    }

    const params = entityParameters[entity.id] || [];
    const param = params.find((p: EntityParameter) => p.domain === domain && p.key === key);
    
    if (!param) {
      return entity.id;
    }
    
    if (param.value_string !== null && param.value_string !== undefined) {
      return param.value_string;
    }
    if (param.value_number !== null && param.value_number !== undefined) {
      return String(param.value_number);
    }
    if (param.value_boolean !== null && param.value_boolean !== undefined) {
      return String(param.value_boolean);
    }
    
    return entity.id;
  };

  // Get display parameter value for an entity (for subtitle)
  const getDisplayParameterValue = (entity: Entity): string => {
    if (!displayParameter.domain || !displayParameter.key) {
      return '';
    }
    const params = entityParameters[entity.id] || [];
    const param = params.find((p: EntityParameter) => 
      p.domain === displayParameter.domain && p.key === displayParameter.key
    );
    if (!param) return '';
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

  // Handle entity click
  const handleEntityClick = (entity: Entity) => {
    setSelectedEntity(entity);
    setDetailModalOpen(true);
  };

  // Handle direct selection (entity passed explicitly, no state dependency)
  const handleDirectSelection = (entity: Entity, selectedParams: EntityParameter[]) => {
    const result: EntitySelectorResult = {
      entity_id: entity.id,
      type: selectedType,
      group: entity.group,
      parameters: selectedParams.map((p) => ({
        domain: p.domain,
        key: p.key,
        value_string: p.value_string,
        value_number: p.value_number,
        value_boolean: p.value_boolean,
      })),
    };
    onSelection(result);
    setDetailModalOpen(false);
    setSelectedEntity(null);
    onClose();
  };

  // Handle selection from detail modal
  const handleSelection = (selectedParams: EntityParameter[]) => {
    if (!selectedEntity) return;
    
    const result: EntitySelectorResult = {
      entity_id: selectedEntity.id,
      type: selectedType,
      group: selectedEntity.group,
      parameters: selectedParams.map((p) => ({
        domain: p.domain,
        key: p.key,
        value_string: p.value_string,
        value_number: p.value_number,
        value_boolean: p.value_boolean,
      })),
    };
    
    onSelection(result);
    setDetailModalOpen(false);
    setSelectedEntity(null);
    onClose();
  };

  // Handle detail modal close
  const handleDetailModalClose = () => {
    setDetailModalOpen(false);
    setSelectedEntity(null);
  };

  if (!isOpen) return null;

  const availableGroups = getAvailableGroups();
  const availableParameters = getAvailableParameters();

  return (
    <>
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          backdropFilter: 'blur(4px)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '50px',
        }}
        onClick={onClose}
      >
        <div
          className="card"
          style={{
            width: '100%',
            height: '100%',
            maxWidth: 'calc(100vw - 100px)',
            maxHeight: 'calc(100vh - 100px)',
            display: 'flex',
            flexDirection: 'column',
            backgroundColor: '#000',
            color: '#fff',
            fontSize: '14px',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h2 className="card-title" style={{ color: '#fff', fontSize: '18px' }}>Entity Selector</h2>
            <button onClick={onClose} className="button button--secondary" style={{ fontSize: '14px' }}>Close</button>
          </div>

          {/* Filters - Horizontal Flex Layout */}
          <div style={{ display: 'flex', gap: '16px', marginBottom: '12px' }}>
            {/* Type Selector */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label className="form-label" style={{ color: '#fff', margin: 0, fontSize: '12px' }}>Type</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value as 'material' | 'recipe')}
                disabled={!!initialType}
                className="form-input"
                style={{ backgroundColor: '#222', color: '#fff', border: '1px solid #444', width: '100%', fontSize: '14px', padding: '6px' }}
              >
                <option value="material">Material</option>
                <option value="recipe">Recipe</option>
              </select>
            </div>

            {/* Group Selector */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label className="form-label" style={{ color: '#fff', margin: 0, fontSize: '12px' }}>Group</label>
              <select
                value={selectedGroup}
                onChange={(e) => setSelectedGroup(e.target.value)}
                disabled={!!initialGroup}
                className="form-input"
                style={{ backgroundColor: '#222', color: '#fff', border: '1px solid #444', width: '100%', fontSize: '14px', padding: '6px' }}
              >
                <option value="">All Groups</option>
                {availableGroups.map((group) => (
                  <option key={group} value={group}>
                    {group}
                  </option>
                ))}
              </select>
            </div>

            {/* Display Parameter Selector */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label className="form-label" style={{ color: '#fff', margin: 0, fontSize: '12px' }}>Display Parameter</label>
              <select
                value={`${displayParameter.domain}:${displayParameter.key}`}
                onChange={(e) => {
                  const [domain, key] = e.target.value.split(':');
                  setDisplayParameter({ domain, key });
                }}
                disabled={!!initialDisplayParameter}
                className="form-input"
                style={{ backgroundColor: '#222', color: '#fff', border: '1px solid #444', width: '100%', fontSize: '14px', padding: '6px' }}
              >
                <option value="">None</option>
                {availableParameters.map((param) => (
                  <option key={`${param.domain}:${param.key}`} value={`${param.domain}:${param.key}`}>
                    {param.domain}:{param.key} ({param.label})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Horizontal Divider */}
          <div style={{ 
            height: '1px', 
            backgroundColor: '#444', 
            marginBottom: '12px' 
          }}></div>

          {/* Search Bar */}
          <div style={{ marginBottom: '12px' }}>
            <input
              type="text"
              placeholder="Search entities..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input"
              style={{ backgroundColor: '#222', color: '#fff', border: '1px solid #444', fontSize: '14px', padding: '8px' }}
            />
          </div>

          {/* Entity List - Scrollable */}
          <div
            ref={entityListRef}
            tabIndex={0}
            style={{
              flex: 1,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px',
              outline: 'none',
            }}
          >
            {loading ? (
              <div className="state-message" style={{ color: '#fff' }}>
                <p className="state-message__text">Loading entities...</p>
              </div>
            ) : filteredEntities.length === 0 ? (
              <div className="state-message" style={{ color: '#fff' }}>
                <p className="state-message__text">
                  {entities.length === 0 ? 'No entities found.' : 'No entities match your search.'}
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {filteredEntities.map((entity) => (
                  <div
                    key={entity.id}
                    onClick={() => {
                      // If preselected parameters exist, auto-select without opening details
                      if (preselectedParameters.length > 0) {
                        const params = entityParameters[entity.id] || [];
                        const selectedParams = params.filter((p: EntityParameter) =>
                          preselectedParameters.some((pp) => pp.domain === p.domain && pp.key === p.key)
                        );
                        handleDirectSelection(entity, selectedParams);
                      } else {
                        handleEntityClick(entity);
                      }
                    }}
                    className="card"
                    style={{
                      padding: '8px',
                      cursor: 'pointer',
                      transition: 'background-color 0.2s',
                      backgroundColor: '#222',
                      border: '1px solid #444',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#333'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#222'}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '2px', color: '#fff', fontSize: '14px' }}>{getDisplaySlotValue(entity, 0)}</div>
                      <div style={{ fontSize: '12px', color: '#ccc' }}>
                        {getDisplayParameterValue(entity)}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEntityClick(entity);
                      }}
                      className="button button--primary"
                      style={{ padding: '4px 8px', fontSize: '12px', marginLeft: '8px' }}
                    >
                      Details
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Entity Detail Modal */}
      {selectedEntity && (
        <EntityDetailModal
          projectId={projectId}
          entity={selectedEntity}
          parameters={entityParameters[selectedEntity.id] || []}
          isOpen={detailModalOpen}
          onClose={handleDetailModalClose}
          onSelection={handleSelection}
          preselectedParameters={preselectedParameters}
        />
      )}
    </>
  );
}
