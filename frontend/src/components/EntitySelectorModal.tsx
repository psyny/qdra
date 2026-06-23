import { useState, useEffect } from 'react';
import { getProjectTemplate } from '../api/projects';
import { getEntities, getEntityParameters } from '../api/entities';
import { ProjectTemplateDetail, EntityType, ParameterDefinition } from '../types/template';
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

  const loadEntities = async () => {
    setLoading(true);
    try {
      const data = await getEntities(projectId, selectedType);
      console.log('EntitySelectorModal - Loaded entities:', data);
      console.log('EntitySelectorModal - Selected group:', selectedGroup);
      console.log('EntitySelectorModal - Entity groups:', data.map(e => ({ id: e.id, group: e.group })));
      
      // Load all entities without filtering - filtering happens in display
      setEntities(data);

      // Load parameters for all entities
      const paramsMap: Record<string, EntityParameter[]> = {};
      await Promise.all(
        data.map(async (entity) => {
          try {
            const params = await getEntityParameters(projectId, entity.id);
            // Add system parameters (id and group)
            paramsMap[entity.id] = [
              {
                id: 'sys_id',
                entity_id: entity.id,
                domain: 'system',
                key: 'id',
                value_string: entity.id,
                created_at: '',
                updated_at: '',
              },
              {
                id: 'sys_group',
                entity_id: entity.id,
                domain: 'system',
                key: 'group',
                value_string: entity.group,
                created_at: '',
                updated_at: '',
              },
              ...params,
            ];
          } catch (err) {
            paramsMap[entity.id] = [];
          }
        })
      );
      setEntityParameters(paramsMap);
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

  console.log('EntitySelectorModal - Rendering:', { 
    entitiesCount: entities.length, 
    filteredCount: filteredEntities.length, 
    loading, 
    searchQuery 
  });

  // Get display parameter value for an entity
  const getDisplayParameterValue = (entity: Entity): string => {
    if (!displayParameter.domain || !displayParameter.key) {
      return entity.id;
    }
    const params = entityParameters[entity.id] || [];
    const param = params.find((p: EntityParameter) => 
      p.domain === displayParameter.domain && p.key === displayParameter.key
    );
    if (!param) return entity.id;
    
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

  // Handle entity click
  const handleEntityClick = (entity: Entity) => {
    setSelectedEntity(entity);
    setDetailModalOpen(true);
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
    
    console.log('EntitySelectorModal - Selection result:', result);
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
      <div style={{
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
      }}>
        <div className="card" style={{ 
          width: '100%',
          height: '100%',
          maxWidth: 'calc(100vw - 100px)', 
          maxHeight: 'calc(100vh - 100px)', 
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#000',
          color: '#fff',
          fontSize: '14px',
        }}>
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
          <div style={{ 
            flex: 1, 
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}>
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
                    onClick={() => handleEntityClick(entity)}
                    className="card"
                    style={{ 
                      padding: '8px', 
                      cursor: 'pointer',
                      transition: 'background-color 0.2s',
                      backgroundColor: '#222',
                      border: '1px solid #444',
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#333'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#222'}
                  >
                    <div style={{ fontWeight: 'bold', marginBottom: '2px', color: '#fff', fontSize: '14px' }}>{entity.id}</div>
                    <div style={{ fontSize: '12px', color: '#ccc' }}>
                      {getDisplayParameterValue(entity)}
                    </div>
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
