import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { WorkspaceHeader } from '../components/WorkspaceHeader';
import {
  listSlotGroups,
  createSlotGroup,
  updateSlotGroup,
  deleteSlotGroup,
  createGroupConstraint,
  deleteSlotConstraint,
  getTemplate,
  getEntityType,
  listEntityTypes,
  listParameterDefinitions,
} from '../api/templates';
import { EntityType, ParameterDefinition } from '../types/template';

type SlotGroup = {
  id: string;
  entity_type_id: string;
  type: string;
  min_slots: number;
  max_slots: number | null;
  default_slots_qty: number;
  sort_order: number;
  constraints: SlotConstraint[];
  slot_definitions: SlotDefinition[];
};

type SlotDefinition = {
  id: string;
  slot_group_id: string;
  slot_key: string;
  slot_idx: number | null;
  min_occurrences: number;
  max_occurrences: number | null;
  sort_order: number;
  constraints: SlotConstraint[];
};

type ConstraintSpec = {
  origin: 'system' | 'parameter';
  system_key?: string | null;
  entity_type_id?: string | null;
  domain?: string | null;
  key?: string | null;
  operator: string;
  value_string?: string | null;
  value_number?: number | null;
  value_boolean?: boolean | null;
};

type OptionSpec = {
  constraints: ConstraintSpec[];
  quantity: number;
};

type SlotConstraint = {
  id: string;
  slot_group_id: string | null;
  slot_definition_id: string | null;
  domain: string | null;
  key: string | null;
  operator: string | null;
  value_string: string | null;
  value_number: number | null;
  value_boolean: boolean | null;
  is_wildcard: boolean;
  sort_order: number;
};

export function SlotDefinitionsPage() {
  const { templateId, entityTypeId } = useParams<{ templateId: string; entityTypeId: string }>();
  const navigate = useNavigate();
  
  const [slotGroups, setSlotGroups] = useState<SlotGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [entityName, setEntityName] = useState<string>('');
  const [entityTypes, setEntityTypes] = useState<EntityType[]>([]);
  const [parameterDefinitions, setParameterDefinitions] = useState<Record<string, ParameterDefinition[]>>({});
  
  // State for template constraints (inline builder)
  const [templateConstraints, setTemplateConstraints] = useState<Record<string, OptionSpec[]>>({
    consumes: [],
    requires: [],
    produces: [],
  });
  
  const [showCreateGroupForm, setShowCreateGroupForm] = useState(false);

  const [groupForm, setGroupForm] = useState({
    type: 'consumes',
    min_slots: 0,
    max_slots: '',
    default_slots_qty: 0,
    sort_order: 0,
  });

  // State to track per-slot constraints (similar to RecipeForm)
  const [perSlotConstraints, setPerSlotConstraints] = useState<Record<string, OptionSpec[]>>({
    consumes: [],
    requires: [],
    produces: [],
  });

  useEffect(() => {
    if (entityTypeId) {
      loadSlotGroups();
    }
    if (templateId && entityTypeId) {
      loadEntityName();
    }
    if (templateId) {
      loadEntityTypesAndParameters();
    }
  }, [entityTypeId, templateId]);

  const loadSlotGroups = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listSlotGroups(entityTypeId!);
      setSlotGroups(data);
      
      // Load template constraints for each group
      for (const group of data) {
        loadTemplateConstraints(group.id, group.type as 'consumes' | 'requires' | 'produces');
      }
    } catch (err) {
      setError('Failed to load slot groups');
    } finally {
      setLoading(false);
    }
  };

  const loadEntityName = async () => {
    try {
      const data = await getEntityType(templateId!, entityTypeId!);
      setEntityName(data.name);
    } catch (err) {
      // Don't set error for entity name loading failure
    }
  };

  const loadEntityTypesAndParameters = async () => {
    try {
      const types = await listEntityTypes(templateId!);
      // Filter to only material entity types for slot constraints
      const materialTypes = types.filter((t) => t.kind === 'material');
      setEntityTypes(materialTypes);
      
      // Load parameter definitions for each material entity type
      const paramsMap: Record<string, ParameterDefinition[]> = {};
      for (const type of materialTypes) {
        const params = await listParameterDefinitions(templateId!, type.id);
        paramsMap[type.id] = params;
      }
      setParameterDefinitions(paramsMap);
    } catch (err) {
      // Don't set error for this - it's optional for the constraint UI
    }
  };

  const handleCreateGroup = () => {
    if (!groupForm.type) {
      setError('Type is required');
      return;
    }
    // Add to local state only, don't save to API yet
    const newGroup: SlotGroup = {
      id: `temp-${Date.now()}`,
      entity_type_id: entityTypeId!,
      type: groupForm.type,
      min_slots: groupForm.min_slots,
      max_slots: groupForm.max_slots ? parseInt(groupForm.max_slots) : null,
      default_slots_qty: groupForm.default_slots_qty,
      sort_order: groupForm.sort_order,
      constraints: [],
      slot_definitions: [],
    };
    setSlotGroups((prev: SlotGroup[]) => [...prev, newGroup]);
    setShowCreateGroupForm(false);
    setGroupForm({ type: 'consumes', min_slots: 0, max_slots: '', default_slots_qty: 0, sort_order: 0 });
  };

  const handleUpdateGroup = (groupId: string, updates: Partial<SlotGroup>) => {
    // Update local state only, don't save to API yet
    setSlotGroups((prev: SlotGroup[]) => prev.map((g: SlotGroup) => 
      g.id === groupId ? { ...g, ...updates } : g
    ));
  };

  const handleDeleteGroup = async (groupId: string) => {
    if (!confirm('Are you sure you want to delete this slot group? This will also delete all its slot definitions and constraints.')) return;
    try {
      await deleteSlotGroup(groupId);
      loadSlotGroups();
    } catch (err: any) {
      setError(err.message || 'Failed to delete slot group');
    }
  };


  const getGroupKindLabel = (kind: string) => {
    const labels: Record<string, string> = {
      consumes: 'Consumes',
      requires: 'Requires',
      produces: 'Produces',
    };
    return labels[kind] || kind;
  };

  // Helper to get parameters for an entity type
  const getParametersForEntityType = (entityTypeId: string) => {
    return parameterDefinitions[entityTypeId] || [];
  };

  // Helper to get parameter definition
  const getParameterDefinition = (domain: string, key: string, entityTypeId?: string | null) => {
    if (!domain || !key) return null;
    
    if (entityTypeId) {
      const params = parameterDefinitions[entityTypeId] || [];
      return params.find((p) => p.domain === domain && p.key === key);
    }
    
    // Search across all entity types
    for (const etId of Object.keys(parameterDefinitions)) {
      const params = parameterDefinitions[etId] || [];
      const param = params.find((p) => p.domain === domain && p.key === key);
      if (param) return param;
    }
    return null;
  };

  // Helper to add an OR group (option) to template constraints
  const addTemplateOrGroup = (type: 'consumes' | 'requires' | 'produces') => {
    setTemplateConstraints(prev => {
      const newConstraints = { ...prev };
      if (!newConstraints[type]) {
        newConstraints[type] = [];
      }
      
      const defaultConstraint: ConstraintSpec = {
        origin: 'system',
        system_key: 'group',
        entity_type_id: null,
        domain: null,
        key: null,
        operator: '=',
        value_string: entityTypes[0]?.name || null,
      };

      const newOption: OptionSpec = {
        constraints: [defaultConstraint],
        quantity: 1,
      };

      newConstraints[type] = [...newConstraints[type], newOption];
      return newConstraints;
    });
  };

  // Helper to remove an OR group from template constraints
  const removeTemplateOrGroup = (type: 'consumes' | 'requires' | 'produces', orGroupIndex: number) => {
    setTemplateConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[type] = newConstraints[type].filter((_, i) => i !== orGroupIndex);
      return newConstraints;
    });
  };

  // Helper to update option quantity
  const updateTemplateOptionQuantity = (type: 'consumes' | 'requires' | 'produces', orGroupIndex: number, quantity: number) => {
    setTemplateConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[type] = [...newConstraints[type]];
      newConstraints[type][orGroupIndex] = {
        ...newConstraints[type][orGroupIndex],
        quantity,
      };
      return newConstraints;
    });
  };

  // Helper to add a constraint to an OR group
  const addTemplateConstraint = (type: 'consumes' | 'requires' | 'produces', orGroupIndex: number) => {
    setTemplateConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[type] = [...newConstraints[type]];
      newConstraints[type][orGroupIndex] = { ...newConstraints[type][orGroupIndex] };

      let firstDomain = null;
      let firstKey = null;
      let firstEntityTypeId = entityTypes[0]?.id || null;

      for (const et of entityTypes) {
        const params = getParametersForEntityType(et.id);
        if (params.length > 0) {
          firstDomain = params[0].domain;
          firstKey = params[0].key;
          firstEntityTypeId = et.id;
          break;
        }
      }

      const newConstraint: ConstraintSpec = {
        origin: 'parameter',
        entity_type_id: firstEntityTypeId,
        domain: firstDomain,
        key: firstKey,
        operator: '=',
        value_string: null,
        value_number: undefined,
        value_boolean: undefined,
      };

      newConstraints[type][orGroupIndex] = {
        ...newConstraints[type][orGroupIndex],
        constraints: [...newConstraints[type][orGroupIndex].constraints, newConstraint],
      };

      return newConstraints;
    });
  };

  // Helper to update a constraint
  const updateTemplateConstraint = (
    type: 'consumes' | 'requires' | 'produces',
    orGroupIndex: number,
    constraintIndex: number,
    field: keyof ConstraintSpec,
    value: any
  ) => {
    setTemplateConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[type] = [...newConstraints[type]];
      newConstraints[type][orGroupIndex] = { ...newConstraints[type][orGroupIndex] };
      newConstraints[type][orGroupIndex] = {
        ...newConstraints[type][orGroupIndex],
        constraints: [...newConstraints[type][orGroupIndex].constraints],
      };
      newConstraints[type][orGroupIndex].constraints[constraintIndex][field] = value;
      return newConstraints;
    });
  };

  // Helper to remove a constraint
  const removeTemplateConstraint = (
    type: 'consumes' | 'requires' | 'produces',
    orGroupIndex: number,
    constraintIndex: number
  ) => {
    setTemplateConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[type] = [...newConstraints[type]];
      newConstraints[type][orGroupIndex] = {
        ...newConstraints[type][orGroupIndex],
        constraints: newConstraints[type][orGroupIndex].constraints.filter(
          (_, i) => i !== constraintIndex
        ),
      };
      return newConstraints;
    });
  };

  // Convert template constraints (OptionSpec[]) to backend constraint format
  const templateConstraintsToBackendFormat = (options: OptionSpec[]): any[] => {
    const constraints: any[] = [];
    let sortOrder = 0;

    for (const option of options) {
      for (const constraint of option.constraints) {
        if (constraint.origin === 'system' && constraint.system_key === 'group') {
          // System group constraint
          constraints.push({
            domain: null,
            key: null,
            operator: '=',
            value_string: constraint.value_string,
            value_number: null,
            value_boolean: null,
            is_wildcard: false,
            sort_order: sortOrder++,
          });
        } else if (constraint.origin === 'parameter') {
          // Parameter constraint
          constraints.push({
            domain: constraint.domain,
            key: constraint.key,
            operator: constraint.operator,
            value_string: constraint.value_string,
            value_number: constraint.value_number,
            value_boolean: constraint.value_boolean,
            is_wildcard: false,
            sort_order: sortOrder++,
          });
        }
      }
    }

    return constraints;
  };

  // Convert backend constraints to template constraints (OptionSpec[]) format
  const backendConstraintsToTemplateFormat = (backendConstraints: SlotConstraint[]): OptionSpec[] => {
    const options: OptionSpec[] = [];
    const systemGroupConstraint = backendConstraints.find(c => c.domain === null && c.key === null);
    
    if (systemGroupConstraint) {
      // Create an option with the system group constraint
      const option: OptionSpec = {
        constraints: [{
          origin: 'system',
          system_key: 'group',
          entity_type_id: null,
          domain: null,
          key: null,
          operator: systemGroupConstraint.operator || '=',
          value_string: systemGroupConstraint.value_string,
          value_number: systemGroupConstraint.value_number,
          value_boolean: systemGroupConstraint.value_boolean,
        }],
        quantity: 1,
      };
      
      // Add parameter constraints to this option
      const paramConstraints = backendConstraints.filter(c => c.domain !== null || c.key !== null);
      for (const param of paramConstraints) {
        option.constraints.push({
          origin: 'parameter',
          system_key: null,
          entity_type_id: null,
          domain: param.domain,
          key: param.key,
          operator: param.operator || '=',
          value_string: param.value_string,
          value_number: param.value_number,
          value_boolean: param.value_boolean,
        });
      }
      
      options.push(option);
    } else {
      // No system group constraint, group parameter constraints by their position
      const paramConstraints = backendConstraints.filter(c => c.domain !== null || c.key !== null);
      if (paramConstraints.length > 0) {
        const option: OptionSpec = {
          constraints: paramConstraints.map(c => ({
            origin: 'parameter' as const,
            system_key: null,
            entity_type_id: null,
            domain: c.domain,
            key: c.key,
            operator: c.operator || '=',
            value_string: c.value_string,
            value_number: c.value_number,
            value_boolean: c.value_boolean,
          })),
          quantity: 1,
        };
        options.push(option);
      }
    }

    return options;
  };

  // Save template constraints to backend
  const saveTemplateConstraints = async (slotGroupId: string, type: 'consumes' | 'requires' | 'produces') => {
    try {
      // Delete existing constraints for this slot group
      const group = slotGroups.find((g: SlotGroup) => g.id === slotGroupId);
      if (group) {
        for (const constraint of group.constraints) {
          await deleteSlotConstraint(constraint.id);
        }
      }

      // Convert and create new constraints
      const options = templateConstraints[type] || [];
      const backendConstraints = templateConstraintsToBackendFormat(options);

      for (const constraint of backendConstraints) {
        await createGroupConstraint(slotGroupId, constraint);
      }

      // Update local state to reflect saved constraints without full reload
      setSlotGroups((prev: SlotGroup[]) => prev.map((g: SlotGroup) => {
        if (g.id === slotGroupId) {
          return { ...g, constraints: backendConstraints };
        }
        return g;
      }));
    } catch (err: any) {
      setError(err.message || 'Failed to save template constraints');
    }
  };

  // Load template constraints from backend
  const loadTemplateConstraints = (slotGroupId: string, type: 'consumes' | 'requires' | 'produces') => {
    const group = slotGroups.find((g: SlotGroup) => g.id === slotGroupId);
    if (!group) return;

    const options = backendConstraintsToTemplateFormat(group.constraints);
    setTemplateConstraints((prev: Record<string, OptionSpec[]>) => ({
      ...prev,
      [type]: options,
    }));
  };

  // Helper to add a slot for per-slot definitions
  const addSlot = (kind: 'requires' | 'consumes' | 'produces') => {
    setPerSlotConstraints(prev => {
      const newConstraints = { ...prev };
      const currentArray = newConstraints[kind] || [];
      newConstraints[kind] = [...currentArray, []];
      return newConstraints;
    });
  };

  // Helper to remove a slot by index
  const removeSlot = (kind: 'requires' | 'consumes' | 'produces', index: number) => {
    setPerSlotConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[kind] = newConstraints[kind].filter((_, i) => i !== index);
      return newConstraints;
    });
  };

  // Helper to add an OR group to a slot
  const addPerSlotOrGroup = (kind: 'requires' | 'consumes' | 'produces', slotIndex: number) => {
    setPerSlotConstraints(prev => {
      const newConstraints = { ...prev };
      if (!newConstraints[kind][slotIndex]) {
        newConstraints[kind][slotIndex] = [];
      }
      newConstraints[kind] = [...newConstraints[kind]];

      const defaultConstraint: ConstraintSpec = {
        origin: 'system',
        system_key: 'group',
        entity_type_id: null,
        domain: null,
        key: null,
        operator: '=',
        value_string: entityTypes[0]?.name || null,
      };

      const newOption: OptionSpec = {
        constraints: [defaultConstraint],
        quantity: 1,
      };

      newConstraints[kind][slotIndex] = [...newConstraints[kind][slotIndex], newOption];
      return newConstraints;
    });
  };

  // Helper to remove an OR group from a slot
  const removePerSlotOrGroup = (kind: 'requires' | 'consumes' | 'produces', slotIndex: number, orGroupIndex: number) => {
    setPerSlotConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[kind][slotIndex] = newConstraints[kind][slotIndex].filter((_, i) => i !== orGroupIndex);
      return newConstraints;
    });
  };

  // Helper to update option quantity
  const updatePerSlotOptionQuantity = (kind: 'requires' | 'consumes' | 'produces', slotIndex: number, orGroupIndex: number, quantity: number) => {
    setPerSlotConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[kind] = [...newConstraints[kind]];
      newConstraints[kind][slotIndex] = [...newConstraints[kind][slotIndex]];
      newConstraints[kind][slotIndex][orGroupIndex] = {
        ...newConstraints[kind][slotIndex][orGroupIndex],
        quantity,
      };
      return newConstraints;
    });
  };

  // Helper to add a constraint to an OR group
  const addPerSlotConstraint = (kind: 'requires' | 'consumes' | 'produces', slotIndex: number, orGroupIndex: number) => {
    setPerSlotConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[kind] = [...newConstraints[kind]];
      newConstraints[kind][slotIndex] = [...newConstraints[kind][slotIndex]];

      let firstDomain = null;
      let firstKey = null;
      let firstEntityTypeId = entityTypes[0]?.id || null;

      for (const et of entityTypes) {
        const params = getParametersForEntityType(et.id);
        if (params.length > 0) {
          firstDomain = params[0].domain;
          firstKey = params[0].key;
          firstEntityTypeId = et.id;
          break;
        }
      }

      const newConstraint: ConstraintSpec = {
        origin: 'parameter',
        entity_type_id: firstEntityTypeId,
        domain: firstDomain,
        key: firstKey,
        operator: '=',
        value_string: null,
        value_number: undefined,
        value_boolean: undefined,
      };

      newConstraints[kind][slotIndex][orGroupIndex] = {
        ...newConstraints[kind][slotIndex][orGroupIndex],
        constraints: [...newConstraints[kind][slotIndex][orGroupIndex].constraints, newConstraint],
      };

      return newConstraints;
    });
  };

  // Helper to update a constraint
  const updatePerSlotConstraint = (
    kind: 'requires' | 'consumes' | 'produces',
    slotIndex: number,
    orGroupIndex: number,
    constraintIndex: number,
    field: keyof ConstraintSpec,
    value: any
  ) => {
    setPerSlotConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[kind] = [...newConstraints[kind]];
      newConstraints[kind][slotIndex] = [...newConstraints[kind][slotIndex]];
      newConstraints[kind][slotIndex][orGroupIndex] = {
        ...newConstraints[kind][slotIndex][orGroupIndex],
        constraints: [...newConstraints[kind][slotIndex][orGroupIndex].constraints],
      };
      newConstraints[kind][slotIndex][orGroupIndex].constraints[constraintIndex][field] = value;
      return newConstraints;
    });
  };

  // Helper to remove a constraint
  const removePerSlotConstraint = (
    kind: 'requires' | 'consumes' | 'produces',
    slotIndex: number,
    orGroupIndex: number,
    constraintIndex: number
  ) => {
    setPerSlotConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[kind] = [...newConstraints[kind]];
      newConstraints[kind][slotIndex] = [...newConstraints[kind][slotIndex]];
      newConstraints[kind][slotIndex][orGroupIndex] = {
        ...newConstraints[kind][slotIndex][orGroupIndex],
        constraints: newConstraints[kind][slotIndex][orGroupIndex].constraints.filter(
          (_, i) => i !== constraintIndex
        ),
      };
      return newConstraints;
    });
  };

  if (loading) {
    return <p>Loading slot definitions...</p>;
  }

  return (
    <div className="page">
      <WorkspaceHeader breadcrumbItems={[
        { label: 'Home', to: '/home' },
        { label: 'Templates', to: '/templates' },
        { label: 'Edit Template', to: `/templates/${templateId}/edit` },
        { label: 'Edit Slot Definitions' }
      ]} />

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 className="card-title">Edit Slot Definitions{entityName && ` for ${entityName}`}</h2>
          </div>
          <button
            onClick={() => setShowCreateGroupForm(true)}
            className="button button--primary"
          >
            Add Slot Group
          </button>
        </div>

      {error && (
        <div style={{ padding: '12px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px', marginBottom: '16px' }}>
          <p style={{ color: '#EF4444', margin: 0 }}>{error}</p>
          <button onClick={() => setError(null)} style={{ marginTop: '8px', background: 'none', border: 'none', color: '#EF4444', cursor: 'pointer', textDecoration: 'underline' }}>Dismiss</button>
        </div>
      )}

      {showCreateGroupForm && (
        <div className="card" style={{ marginBottom: '16px' }}>
          <h3 style={{ marginTop: 0 }}>Create Slot Group</h3>
          <div className="form-field">
            <label className="form-label">Type *</label>
            <select
              className="form-input"
              value={groupForm.type}
              onChange={(e) => setGroupForm({ ...groupForm, type: e.target.value })}
            >
              <option value="consumes">Consumes</option>
              <option value="requires">Requires</option>
              <option value="produces">Produces</option>
            </select>
          </div>
          <div className="form-field">
            <label className="form-label">Min Slots</label>
            <input
              type="number"
              className="form-input"
              value={groupForm.min_slots}
              onChange={(e) => setGroupForm({ ...groupForm, min_slots: parseInt(e.target.value) || 0 })}
              min="0"
            />
          </div>
          <div className="form-field">
            <label className="form-label">Max Slots (leave blank for unlimited)</label>
            <input
              type="number"
              className="form-input"
              value={groupForm.max_slots}
              onChange={(e) => setGroupForm({ ...groupForm, max_slots: e.target.value })}
              min="0"
            />
          </div>
          <div className="form-field">
            <label className="form-label">Default Slots Qty</label>
            <input
              type="number"
              className="form-input"
              value={groupForm.default_slots_qty}
              onChange={(e) => setGroupForm({ ...groupForm, default_slots_qty: parseInt(e.target.value) || 0 })}
              min="0"
            />
          </div>
          <div className="form-field">
            <label className="form-label">Sort Order</label>
            <input
              type="number"
              className="form-input"
              value={groupForm.sort_order}
              onChange={(e) => setGroupForm({ ...groupForm, sort_order: parseInt(e.target.value) || 0 })}
            />
          </div>
          <div className="form-actions">
            <button onClick={() => { setShowCreateGroupForm(false); setGroupForm({ kind: 'consumes', min_slots: 0, max_slots: '', sort_order: 0 }); }} className="button button--secondary">Cancel</button>
            <button onClick={handleCreateGroup} className="button button--primary">Create</button>
          </div>
        </div>
      )}

      {['consumes', 'requires', 'produces'].map((type) => {
        const group = slotGroups.find(g => g.type === type);
        if (!group) {
          return (
            <div key={type} className="card" style={{ marginBottom: '12px' }}>
              <p style={{ margin: 0, color: '#666' }}>No {getGroupKindLabel(type)} group defined</p>
              <button
                onClick={() => { setShowCreateGroupForm(true); setGroupForm({ ...groupForm, type }); }}
                className="button button--primary"
                style={{ marginTop: '8px', fontSize: '12px' }}
              >
                Add {getGroupKindLabel(type)} Group
              </button>
            </div>
          );
        }

        return (
          <div key={group.id} className="card" style={{ marginBottom: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ margin: '0 0 4px 0' }}>{getGroupKindLabel(group.type)}</h3>
              </div>
              <button onClick={() => handleDeleteGroup(group.id)} className="button button--danger">
                Delete
              </button>
            </div>

            <div className="card" style={{ marginTop: '16px', padding: '16px' }}>
              <h4 style={{ marginTop: 0 }}>Slot Group Settings</h4>
              <div className="form-field">
                <label className="form-label">Type *</label>
                <select
                  className="form-input"
                  value={group.type}
                  onChange={(e) => handleUpdateGroup(group.id, { type: e.target.value })}
                >
                  <option value="consumes">Consumes</option>
                  <option value="requires">Requires</option>
                  <option value="produces">Produces</option>
                </select>
              </div>
              <div className="form-field">
                <label className="form-label">Min Slots</label>
                <input
                  type="number"
                  className="form-input"
                  value={group.min_slots}
                  onChange={(e) => handleUpdateGroup(group.id, { min_slots: parseInt(e.target.value) || 0 })}
                  min="0"
                />
              </div>
              <div className="form-field">
                <label className="form-label">Max Slots (leave blank for unlimited)</label>
                <input
                  type="number"
                  className="form-input"
                  value={group.max_slots || ''}
                  onChange={(e) => handleUpdateGroup(group.id, { max_slots: e.target.value ? parseInt(e.target.value) : null })}
                  min="0"
                />
              </div>
              <div className="form-field">
                <label className="form-label">Default Slots Qty</label>
                <input
                  type="number"
                  className="form-input"
                  value={group.default_slots_qty}
                  onChange={(e) => handleUpdateGroup(group.id, { default_slots_qty: parseInt(e.target.value) || 0 })}
                  min="0"
                />
              </div>
            </div>

            <div style={{ marginTop: '16px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '12px' }}>
                <div style={{ marginBottom: '16px' }}>
                  <h4 style={{ margin: '0 0 8px 0' }}>Default Slot Template</h4>
                  <p style={{ color: '#888', fontSize: '13px', margin: '0 0 12px 0' }}>
                    These constraints will be applied to all new slots created during recipe creation.
                  </p>
                  
                  {/* Inline Constraint Builder */}
                  <div style={{ marginTop: '8px' }}>
                    <div style={{ fontSize: '11px', color: '#666', marginBottom: '4px' }}>
                      Options:
                    </div>
                    
                    {(templateConstraints[group.type] || []).map((option, orGroupIndex) => (
                      <div key={orGroupIndex} className="card" style={{ padding: '12px', marginBottom: '12px' }}>
                        <div style={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center',
                          marginBottom: '8px',
                          paddingBottom: '8px',
                          borderBottom: '1px solid rgba(255,255,255,0.1)'
                        }}>
                          <div>
                            <span style={{ fontSize: '10px', color: '#666', fontWeight: 'bold' }}>
                              Option {orGroupIndex + 1}
                            </span>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                              <label className="form-label" style={{ fontSize: '11px', marginBottom: '0' }}>Quantity:</label>
                              <input
                                type="number"
                                className="form-input"
                                value={option.quantity || 1}
                                onChange={(e) => updateTemplateOptionQuantity(group.type, orGroupIndex, e.target.value ? Number(e.target.value) : 1)}
                                min="0"
                                step="any"
                                style={{ fontSize: '12px', padding: '4px 8px', width: '60px' }}
                              />
                            </div>
                          </div>
                          <button
                            onClick={() => removeTemplateOrGroup(group.type, orGroupIndex)}
                            style={{ padding: '1px 4px', fontSize: '9px', border: '1px solid #ccc', background: '#fff' }}
                          >
                            ×
                          </button>
                        </div>
                        
                        {option.constraints.map((constraint, constraintIndex) => (
                          <div key={constraintIndex} style={{
                            display: 'flex',
                            gap: '4px',
                            alignItems: 'center',
                            marginBottom: '8px'
                          }}>
                            {/* Type selector */}
                            <select
                              value={constraint.origin || 'parameter'}
                              onChange={(e) => {
                                const newOrigin = e.target.value as 'system' | 'parameter';
                                updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'origin', newOrigin);
                                if (newOrigin === 'system') {
                                  updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'entity_type_id', null);
                                  updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'domain', null);
                                  updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'key', null);
                                } else {
                                  updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'system_key', null);
                                }
                              }}
                              className="form-input"
                              style={{ width: '80px', fontSize: '12px', padding: '5px 6px' }}
                            >
                              <option value="parameter">Parameter</option>
                              <option value="system">System</option>
                            </select>

                            {/* Key selector */}
                            <select
                              value={constraint.origin === 'system' ? (constraint.system_key || '') : (constraint.domain && constraint.key ? `${constraint.domain}:${constraint.key}` : '')}
                              onChange={(e) => {
                                if (constraint.origin === 'system') {
                                  updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'system_key', e.target.value);
                                } else {
                                  const [domain, key] = e.target.value.split(':');
                                  if (domain && key) {
                                    updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'domain', domain);
                                    updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'key', key);
                                  } else {
                                    updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'domain', null);
                                    updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'key', null);
                                  }
                                }
                              }}
                              className="form-input"
                              style={{ width: '200px', fontSize: '12px', padding: '5px 6px' }}
                            >
                              {constraint.origin === 'system' ? (
                                <>
                                  <option value="id">id</option>
                                  <option value="group">group</option>
                                </>
                              ) : (
                                entityTypes.flatMap((et) => 
                                  getParametersForEntityType(et.id).map((param) => ({
                                    domain: param.domain,
                                    key: param.key,
                                    label: `${param.domain}:${param.key}`
                                  }))
                                ).map((param, idx) => (
                                  <option key={`${param.domain}:${param.key}:${idx}`} value={`${param.domain}:${param.key}`}>
                                    {param.label}
                                  </option>
                                ))
                              )}
                            </select>

                            {/* Operator selector */}
                            <select
                              value={constraint.operator || '='}
                              onChange={(e) => updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'operator', e.target.value)}
                              className="form-input"
                              style={{ width: '50px', fontSize: '12px', padding: '5px 6px' }}
                            >
                              <option value="=">=</option>
                              <option value="<">&lt;</option>
                              <option value="<=">&le;</option>
                              <option value=">">&gt;</option>
                              <option value=">=">&ge;</option>
                              <option value="in">in</option>
                            </select>

                            {/* Value input */}
                            {constraint.origin === 'system' ? (
                              constraint.system_key === 'group' ? (
                                <select
                                  value={constraint.value_string || ''}
                                  onChange={(e) => updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'value_string', e.target.value)}
                                  className="form-input"
                                  style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                                >
                                  {entityTypes.map((et) => (
                                    <option key={et.id} value={et.name}>
                                      {et.name}
                                    </option>
                                  ))}
                                </select>
                              ) : (
                                <input
                                  type="text"
                                  value={constraint.value_string || ''}
                                  onChange={(e) => updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'value_string', e.target.value)}
                                  placeholder="Value"
                                  className="form-input"
                                  style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                                />
                              )
                            ) : (
                              (() => {
                                const paramDef = getParameterDefinition(constraint.domain, constraint.key, constraint.entity_type_id);
                                const valueType = paramDef?.value_type || 'string';
                                
                                if (valueType === 'string') {
                                  return (
                                    <input
                                      type="text"
                                      value={constraint.value_string || ''}
                                      onChange={(e) => updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'value_string', e.target.value)}
                                      placeholder="Value"
                                      className="form-input"
                                      style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                                    />
                                  );
                                } else if (valueType === 'number') {
                                  return (
                                    <input
                                      type="number"
                                      value={constraint.value_number ?? ''}
                                      onChange={(e) => updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'value_number', e.target.value ? Number(e.target.value) : null)}
                                      placeholder="Value"
                                      className="form-input"
                                      style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                                    />
                                  );
                                } else if (valueType === 'boolean') {
                                  return (
                                    <select
                                      value={constraint.value_boolean === true ? 'true' : constraint.value_boolean === false ? 'false' : ''}
                                      onChange={(e) => updateTemplateConstraint(group.type, orGroupIndex, constraintIndex, 'value_boolean', e.target.value === 'true' ? true : e.target.value === 'false' ? false : null)}
                                      className="form-input"
                                      style={{ flex: 1 }}
                                    >
                                      <option value="">Select...</option>
                                      <option value="true">True</option>
                                      <option value="false">False</option>
                                    </select>
                                  );
                                }
                                return null;
                              })()
                            )}
                            
                            <button
                              onClick={() => removeTemplateConstraint(group.type, orGroupIndex, constraintIndex)}
                              style={{ padding: '1px 4px', fontSize: '9px', border: '1px solid #ccc', background: '#fff' }}
                            >
                              ×
                            </button>
                          </div>
                        ))}
                        
                        <button
                          onClick={() => addTemplateConstraint(group.type, orGroupIndex)}
                          className="button button--primary"
                          style={{ padding: '4px 8px', fontSize: '12px' }}
                        >
                          + Add Parameter Requirement
                        </button>
                      </div>
                    ))}
                    
                    <button
                      onClick={() => addTemplateOrGroup(group.type)}
                      className="button button--primary"
                      style={{ padding: '4px 8px', fontSize: '12px' }}
                    >
                      + Add Option
                    </button>
                  </div>
                </div>

                <div>
                  <h4 style={{ margin: '0 0 8px 0' }}>Per Slot Definitions</h4>
                  {(perSlotConstraints[group.type] || []).length === 0 ? (
                    <p style={{ color: '#666', fontSize: '14px' }}>No slots defined</p>
                  ) : (
                    (perSlotConstraints[group.type] || []).map((slotOrGroups, slotIndex) => (
                      <div key={`${group.type}-${slotIndex}`} className="card" style={{ padding: '16px', marginBottom: '12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <p style={{ color: '#999', fontStyle: 'italic', margin: 0 }}>
                            {group.type.charAt(0).toUpperCase() + group.type.slice(1)} slot {slotIndex + 1}
                          </p>
                          <button
                            onClick={() => removeSlot(group.type as 'requires' | 'consumes' | 'produces', slotIndex)}
                            className="button button--danger"
                            style={{ padding: '2px 6px', fontSize: '10px' }}
                          >
                            Remove
                          </button>
                        </div>

                        {/* Constraint Builder */}
                        <div style={{ marginTop: '8px' }}>
                          <div style={{ fontSize: '11px', color: '#666', marginBottom: '4px' }}>
                            Options:
                          </div>

                          {slotOrGroups.map((option, orGroupIndex) => (
                            <div key={orGroupIndex} className="card" style={{ padding: '12px', marginBottom: '12px' }}>
                              <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                marginBottom: '8px',
                                paddingBottom: '8px',
                                borderBottom: '1px solid rgba(255,255,255,0.1)'
                              }}>
                                <div>
                                  <span style={{ fontSize: '10px', color: '#666', fontWeight: 'bold' }}>
                                    Option {orGroupIndex + 1}
                                  </span>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                                    <label className="form-label" style={{ fontSize: '11px', marginBottom: '0' }}>Quantity:</label>
                                    <input
                                      type="number"
                                      className="form-input"
                                      value={option.quantity || 1}
                                      onChange={(e) => updatePerSlotOptionQuantity(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, e.target.value ? Number(e.target.value) : 1)}
                                      min="0"
                                      step="any"
                                      style={{ fontSize: '12px', padding: '4px 8px', width: '60px' }}
                                    />
                                  </div>
                                </div>
                                <button
                                  onClick={() => removePerSlotOrGroup(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex)}
                                  style={{ padding: '1px 4px', fontSize: '9px', border: '1px solid #ccc', background: '#fff' }}
                                >
                                  ×
                                </button>
                              </div>

                              {option.constraints.map((constraint, constraintIndex) => (
                                <div key={constraintIndex} style={{
                                  display: 'flex',
                                  gap: '4px',
                                  alignItems: 'center',
                                  marginBottom: '8px'
                                }}>
                                  {/* Type selector */}
                                  <select
                                    value={constraint.origin || 'parameter'}
                                    onChange={(e) => {
                                      const newOrigin = e.target.value as 'system' | 'parameter';
                                      updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'origin', newOrigin);
                                      if (newOrigin === 'system') {
                                        updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'entity_type_id', null);
                                        updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'domain', null);
                                        updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'key', null);
                                      } else {
                                        updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'system_key', null);
                                      }
                                    }}
                                    className="form-input"
                                    style={{ width: '80px', fontSize: '12px', padding: '5px 6px' }}
                                  >
                                    <option value="parameter">Parameter</option>
                                    <option value="system">System</option>
                                  </select>

                                  {/* Key selector */}
                                  <select
                                    value={constraint.origin === 'system' ? (constraint.system_key || '') : (constraint.domain && constraint.key ? `${constraint.domain}:${constraint.key}` : '')}
                                    onChange={(e) => {
                                      if (constraint.origin === 'system') {
                                        updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'system_key', e.target.value);
                                      } else {
                                        const [domain, key] = e.target.value.split(':');
                                        if (domain && key) {
                                          updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'domain', domain);
                                          updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'key', key);
                                        } else {
                                          updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'domain', null);
                                          updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'key', null);
                                        }
                                      }
                                    }}
                                    className="form-input"
                                    style={{ width: '200px', fontSize: '12px', padding: '5px 6px' }}
                                  >
                                    {constraint.origin === 'system' ? (
                                      <>
                                        <option value="id">id</option>
                                        <option value="group">group</option>
                                      </>
                                    ) : (
                                      entityTypes.flatMap((et) =>
                                        getParametersForEntityType(et.id).map((param) => ({
                                          domain: param.domain,
                                          key: param.key,
                                          label: `${param.domain}:${param.key}`
                                        }))
                                      ).map((param, idx) => (
                                        <option key={`${param.domain}:${param.key}:${idx}`} value={`${param.domain}:${param.key}`}>
                                          {param.label}
                                        </option>
                                      ))
                                    )}
                                  </select>

                                  {/* Operator selector */}
                                  <select
                                    value={constraint.operator || '='}
                                    onChange={(e) => updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'operator', e.target.value)}
                                    className="form-input"
                                    style={{ width: '50px', fontSize: '12px', padding: '5px 6px' }}
                                  >
                                    <option value="=">=</option>
                                    <option value="<">&lt;</option>
                                    <option value="<=">&le;</option>
                                    <option value=">">&gt;</option>
                                    <option value=">=">&ge;</option>
                                    <option value="in">in</option>
                                  </select>

                                  {/* Value input */}
                                  {constraint.origin === 'system' ? (
                                    constraint.system_key === 'group' ? (
                                      <select
                                        value={constraint.value_string || ''}
                                        onChange={(e) => updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'value_string', e.target.value)}
                                        className="form-input"
                                        style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                                      >
                                        {entityTypes.map((et) => (
                                          <option key={et.id} value={et.name}>
                                            {et.name}
                                          </option>
                                        ))}
                                      </select>
                                    ) : (
                                      <input
                                        type="text"
                                        value={constraint.value_string || ''}
                                        onChange={(e) => updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'value_string', e.target.value)}
                                        placeholder="Value"
                                        className="form-input"
                                        style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                                      />
                                    )
                                  ) : (
                                    (() => {
                                      const paramDef = getParameterDefinition(constraint.domain, constraint.key, constraint.entity_type_id);
                                      const valueType = paramDef?.value_type || 'string';

                                      if (valueType === 'string') {
                                        return (
                                          <input
                                            type="text"
                                            value={constraint.value_string || ''}
                                            onChange={(e) => updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'value_string', e.target.value)}
                                            placeholder="Value"
                                            className="form-input"
                                            style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                                          />
                                        );
                                      } else if (valueType === 'number') {
                                        return (
                                          <input
                                            type="number"
                                            value={constraint.value_number ?? ''}
                                            onChange={(e) => updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'value_number', e.target.value ? Number(e.target.value) : null)}
                                            placeholder="Value"
                                            className="form-input"
                                            style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                                          />
                                        );
                                      } else if (valueType === 'boolean') {
                                        return (
                                          <select
                                            value={constraint.value_boolean === true ? 'true' : constraint.value_boolean === false ? 'false' : ''}
                                            onChange={(e) => updatePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex, 'value_boolean', e.target.value === 'true' ? true : e.target.value === 'false' ? false : null)}
                                            className="form-input"
                                            style={{ flex: 1 }}
                                          >
                                            <option value="">Select...</option>
                                            <option value="true">True</option>
                                            <option value="false">False</option>
                                          </select>
                                        );
                                      }
                                      return null;
                                    })()
                                  )}

                                  <button
                                    onClick={() => removePerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex, constraintIndex)}
                                    style={{ padding: '1px 4px', fontSize: '9px', border: '1px solid #ccc', background: '#fff' }}
                                  >
                                    ×
                                  </button>
                                </div>
                              ))}

                              <button
                                onClick={() => addPerSlotConstraint(group.type as 'requires' | 'consumes' | 'produces', slotIndex, orGroupIndex)}
                                className="button button--primary"
                                style={{ padding: '4px 8px', fontSize: '12px' }}
                              >
                                + Add Parameter Requirement
                              </button>
                            </div>
                          ))}

                          <button
                            onClick={() => addPerSlotOrGroup(group.type as 'requires' | 'consumes' | 'produces', slotIndex)}
                            className="button button--primary"
                            style={{ padding: '4px 8px', fontSize: '12px' }}
                          >
                            + Add Option
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                  <button
                    onClick={() => addSlot(group.type as 'requires' | 'consumes' | 'produces')}
                    className="button button--primary"
                    style={{ padding: '4px 8px', fontSize: '12px' }}
                  >
                    + Add Slot
                  </button>
                </div>
              </div>
          </div>
        );
      })}

      <div style={{ marginTop: '24px', padding: '16px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
        <button
          onClick={async () => {
            // Save slot groups (create new ones, update existing ones)
            for (const group of slotGroups) {
              if (group.id.startsWith('temp-')) {
                // Create new group
                await createSlotGroup(entityTypeId!, {
                  type: group.type,
                  min_slots: group.min_slots,
                  max_slots: group.max_slots,
                  default_slots_qty: group.default_slots_qty,
                  sort_order: group.sort_order,
                });
              } else {
                // Update existing group
                await updateSlotGroup(group.id, {
                  type: group.type,
                  min_slots: group.min_slots,
                  max_slots: group.max_slots,
                  default_slots_qty: group.default_slots_qty,
                  sort_order: group.sort_order,
                });
              }
            }
            
            // Save template constraints for each group
            for (const group of slotGroups) {
              if (!group.id.startsWith('temp-')) {
                await saveTemplateConstraints(group.id, group.type as 'consumes' | 'requires' | 'produces');
              }
            }
            
            // Reload to get updated data with real IDs
            await loadSlotGroups();
            
            // Navigate back to Edit Template page
            navigate(`/templates/${templateId}/edit`);
          }}
          className="button button--primary"
          style={{ fontSize: '16px', padding: '12px 24px' }}
        >
          Save All Changes
        </button>
      </div>

      </div>
    </div>
  );
}
