import { useState, useEffect } from 'react';
import { DraftParameter } from './ParameterRow';
import { ImageUpload } from './ImageUpload';
import { Combobox } from './Combobox';
import { getDistinctParameterValues } from '../api/entities';
import { listSlotGroups } from '../api/templates';

type SlotGroupConfig = {
  type: 'requires' | 'consumes' | 'produces';
  min_slots: number;
  max_slots: number;
};

type ConstraintSpec = {
  origin: 'system' | 'parameter';
  system_key?: string | null; // For system origin (domain __system__)
  entity_type_id?: string | null; // For parameter origin (group)
  domain?: string | null; // For parameter origin
  key?: string | null; // For parameter origin
  operator: string;
  value_string?: string | null;
  value_number?: number | null;
  value_boolean?: boolean | null;
};

type OptionSpec = {
  constraints: ConstraintSpec[];
  quantity: number;
};

type SlotConstraints = {
  [key: string]: OptionSpec[]; // kind -> slotIndex -> options
};

type RecipeFormProps = {
  initialParameters?: DraftParameter[];
  isSubmitting?: boolean;
  errorMessage?: string | null;
  onSubmit: (parameters: DraftParameter[], imageUrl?: string, slotData?: { slotCounts: Record<string, number>; slotConstraints: SlotConstraints }) => void;
  onCancel: () => void;
  submitLabel: string;
  entityId?: string;
  targetImageSize?: number;
  currentImage?: string | null;
  slotGroups?: SlotGroupConfig[];
  materialEntityTypes?: any[];
  template?: any;
  projectId?: string;
  initialSlotCounts?: Record<string, number>;
  initialSlotConstraints?: SlotConstraints;
  group?: string;
};

export function RecipeForm({
  initialParameters = [],
  isSubmitting = false,
  errorMessage = null,
  onSubmit,
  onCancel,
  submitLabel,
  entityId,
  targetImageSize = 256,
  currentImage,
  slotGroups = [],
  materialEntityTypes = [],
  template,
  projectId,
  initialSlotCounts,
  initialSlotConstraints,
  group,
}: RecipeFormProps) {
  const [parameters, setParameters] = useState<DraftParameter[]>(initialParameters);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(currentImage || null);
  const [hoveredDescription, setHoveredDescription] = useState<string | null>(null);
  const [parameterExistingValues, setParameterExistingValues] = useState<Record<string, string[]>>({});
  const [parameterDuplicateWarnings, setParameterDuplicateWarnings] = useState<Record<string, boolean>>({});
  
  // State to track current number of slots for each category
  const [slotCounts, setSlotCounts] = useState<Record<string, number>>(
    initialSlotCounts || {
      requires: slotGroups.find(g => g.type === 'requires')?.min_slots || 0,
      consumes: slotGroups.find(g => g.type === 'consumes')?.min_slots || 0,
      produces: slotGroups.find(g => g.type === 'produces')?.min_slots || 0,
    }
  );

  // State to track constraints for each slot
  const [slotConstraints, setSlotConstraints] = useState<SlotConstraints>(
    initialSlotConstraints || {
      requires: [],
      consumes: [],
      produces: [],
    }
  );

  // Update initial slot counts when slotGroups changes (for new recipes)
  useEffect(() => {
    const hasInitialCounts = initialSlotCounts && Object.keys(initialSlotCounts).length > 0;
    if (!hasInitialCounts && slotGroups.length > 0) {
      setSlotCounts({
        requires: slotGroups.find(g => g.type === 'requires')?.min_slots || 0,
        consumes: slotGroups.find(g => g.type === 'consumes')?.min_slots || 0,
        produces: slotGroups.find(g => g.type === 'produces')?.min_slots || 0,
      });
    }
  }, [slotGroups, initialSlotCounts]);

  // Load template slot definitions for new recipes
  useEffect(() => {
    const hasInitialConstraints = initialSlotConstraints && 
      (initialSlotConstraints.requires?.length > 0 || 
       initialSlotConstraints.consumes?.length > 0 || 
       initialSlotConstraints.produces?.length > 0);
    
    if (!hasInitialConstraints && template && template.entity_types) {
      // Find the recipe entity type from the template
      const recipeEntityType = template.entity_types.find((et: any) => et.kind === 'recipe');
      
      if (recipeEntityType) {
        listSlotGroups(recipeEntityType.id)
          .then((slotGroupsData) => {
            // Convert template per_slots to slot constraints format
            const newConstraints: SlotConstraints = {
              requires: [],
              consumes: [],
              produces: [],
            };
            
            const newCounts: Record<string, number> = {
              requires: 0,
              consumes: 0,
              produces: 0,
            };
            
            slotGroupsData.forEach((sg: any) => {
              if (sg.per_slots && sg.per_slots.length > 0) {
                newConstraints[sg.type] = sg.per_slots.map((perSlot: any) => {
                  // If per_slot has no options, fall back to default_slot
                  const optionsToUse = (!perSlot.options || perSlot.options.length === 0) && sg.default_slot
                    ? sg.default_slot.options
                    : perSlot.options;

                  if (!optionsToUse || optionsToUse.length === 0) {
                    return [];
                  }

                  return optionsToUse.map((option: any) => ({
                    constraints: option.parameter_constraints.map((c: any) => {
                      const isSystem = c.domain === 'system';
                      return {
                        id: c.id,
                        origin: c.domain || 'parameter',
                        system_key: isSystem ? c.key : null,
                        entity_type_id: isSystem ? null : (c.entity_type_id || null),
                        domain: isSystem ? null : c.domain,
                        key: isSystem ? null : c.key,
                        operator: c.operator,
                        value_string: c.value_string,
                        value_number: c.value_number,
                        value_boolean: c.value_boolean,
                        is_wildcard: c.is_wildcard,
                      };
                    }),
                    quantity: option.quantity || 0,
                  }));
                });
                newCounts[sg.type] = sg.per_slots.length;
              }
            });
            
            setSlotConstraints(newConstraints);
            setSlotCounts(newCounts);
          })
          .catch(() => {
            // Silently fail if template loading fails
          });
      }
    }
  }, [template, initialSlotConstraints]);

  // Load existing values for searchable string parameters on mount
  useEffect(() => {
    if (projectId) {
      parameters.forEach(param => {
        if (param.is_searchable && param.value_type === 'string') {
          fetchParameterExistingValues(param.domain, param.key);
        }
      });
    }
  }, [projectId, parameters]);

  // State to track existing parameter values for each constraint
  const [existingValues, setExistingValues] = useState<Record<string, string[]>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Validate required parameters
    for (const param of parameters) {
      if (param.required && (param.value === null || param.value === undefined || param.value === '')) {
        setValidationError(`${param.label || param.key} is required`);
        return;
      }
    }

    // Validate all parameters have domain and key
    for (const param of parameters) {
      if (!param.domain.trim() || !param.key.trim()) {
        setValidationError('All parameters must have a domain and key');
        return;
      }
    }

    onSubmit(parameters, imageUrl || undefined, { slotCounts, slotConstraints });
  };

  const updateParameter = (domain: string, key: string, value: any) => {
    const updated = [...parameters];
    const index = updated.findIndex(p => p.domain === domain && p.key === key);
    if (index === -1) return;
    
    updated[index] = { ...updated[index], value };
    setParameters(updated);

    // Check for duplicates if parameter is unique, searchable, and string
    const param = updated[index];
    if (param.is_unique && param.is_searchable && param.value_type === 'string' && typeof value === 'string') {
      checkParameterForDuplicate(param.domain, param.key, value);
    }
  };

  const sortedParameters = [...parameters].sort((a, b) => {
    // First by sort_order (ascending)
    if (a.sort_order !== b.sort_order) {
      return a.sort_order - b.sort_order;
    }
    // Then by required (required first)
    if (a.required !== b.required) {
      return a.required ? -1 : 1;
    }
    // Then by alphabetical (label or key)
    const labelA = (a.label || a.key).toLowerCase();
    const labelB = (b.label || b.key).toLowerCase();
    return labelA.localeCompare(labelB);
  });

  // Helper to get slot group config for a kind
  const getSlotGroupConfig = (kind: 'requires' | 'consumes' | 'produces') => {
    return slotGroups.find(g => g.type === kind);
  };

  // Helper to add a slot
  const addSlot = async (kind: 'requires' | 'consumes' | 'produces') => {
    const config = getSlotGroupConfig(kind);
    if (!config) return;

    const currentCount = slotCounts[kind];
    // If max_slots is null, it means unlimited
    const maxSlots = config.max_slots === null ? Infinity : config.max_slots;
    if (currentCount < maxSlots) {
      setSlotCounts(prev => ({ ...prev, [kind]: currentCount + 1 }));
      
      // Try to load default slot from template
      if (template && template.entity_types) {
        const recipeEntityType = template.entity_types.find((et: any) => et.kind === 'recipe');
        if (recipeEntityType) {
          try {
            const slotGroupsData = await listSlotGroups(recipeEntityType.id);
            const slotGroup = slotGroupsData.find((sg: any) => sg.type === kind);
            
            if (slotGroup && slotGroup.default_slot) {
              // Convert default slot to slot constraints format
              const defaultSlotConstraints = slotGroup.default_slot.options.map((option: any) => ({
                constraints: option.parameter_constraints.map((c: any) => {
                  const isSystem = c.domain === 'system';
                  return {
                    id: c.id,
                    origin: c.domain || 'parameter',
                    system_key: isSystem ? c.key : null,
                    entity_type_id: isSystem ? null : (c.entity_type_id || null),
                    domain: isSystem ? null : c.domain,
                    key: isSystem ? null : c.key,
                    operator: c.operator,
                    value_string: c.value_string,
                    value_number: c.value_number,
                    value_boolean: c.value_boolean,
                    is_wildcard: c.is_wildcard,
                  };
                }),
                quantity: option.quantity || 0,
              }));
              
              setSlotConstraints(prev => {
                const newConstraints = { ...prev };
                const currentArray = newConstraints[kind] || [];
                newConstraints[kind] = [...currentArray, defaultSlotConstraints];
                return newConstraints;
              });
              return;
            }
          } catch {
            // Silently fail if template loading fails
          }
        }
      }
      
      // Fallback to empty constraints if no template or error
      setSlotConstraints(prev => {
        const newConstraints = { ...prev };
        const currentArray = newConstraints[kind] || [];
        newConstraints[kind] = [...currentArray, []];
        return newConstraints;
      });
    }
  };

  // Helper to remove a specific slot by index
  const removeSlot = (kind: 'requires' | 'consumes' | 'produces', index: number) => {
    const config = getSlotGroupConfig(kind);
    if (!config) return;
    
    const currentCount = slotCounts[kind];
    if (currentCount > config.min_slots) {
      setSlotCounts(prev => ({ ...prev, [kind]: currentCount - 1 }));
      // Remove constraints for this slot
      setSlotConstraints(prev => {
        const newConstraints = { ...prev };
        newConstraints[kind] = newConstraints[kind].filter((_, i) => i !== index);
        return newConstraints;
      });
    }
  };

  // Helper to add an OR group to a slot
  const addOrGroup = (kind: 'requires' | 'consumes' | 'produces', slotIndex: number) => {
    setSlotConstraints(prev => {
      const newConstraints = { ...prev };
      if (!newConstraints[kind][slotIndex]) {
        newConstraints[kind][slotIndex] = [];
      }
      // Create a new array to avoid mutation issues
      newConstraints[kind] = [...newConstraints[kind]];

      // Create a default constraint for system group
      const defaultConstraint = {
        origin: 'system' as const,
        system_key: 'group',
        entity_type_id: null,
        domain: null,
        key: null,
        operator: '=',
        value_string: materialEntityTypes[0]?.name || null,
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
  const removeOrGroup = (kind: 'requires' | 'consumes' | 'produces', slotIndex: number, orGroupIndex: number) => {
    setSlotConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[kind][slotIndex] = newConstraints[kind][slotIndex].filter((_, i) => i !== orGroupIndex);
      return newConstraints;
    });
  };

  // Helper to update option quantity
  const updateOptionQuantity = (kind: 'requires' | 'consumes' | 'produces', slotIndex: number, orGroupIndex: number, quantity: number) => {
    setSlotConstraints(prev => {
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
  const addConstraint = (kind: 'requires' | 'consumes' | 'produces', slotIndex: number, orGroupIndex: number) => {
    setSlotConstraints(prev => {
      const newConstraints = { ...prev };
      // Create new arrays to avoid mutation issues
      newConstraints[kind] = [...newConstraints[kind]];
      newConstraints[kind][slotIndex] = [...newConstraints[kind][slotIndex]];

      // Get the first available domain+key pair
      let firstDomain = null;
      let firstKey = null;
      let firstEntityTypeId = materialEntityTypes[0]?.id || null;

      for (const et of materialEntityTypes) {
        const params = getParametersForEntityType(et.id);
        if (params.length > 0) {
          firstDomain = params[0].domain;
          firstKey = params[0].key;
          firstEntityTypeId = et.id;
          break;
        }
      }

      const newConstraint: ConstraintSpec = {
        origin: 'parameter' as const,
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

      // Fetch existing values for the auto-selected domain+key
      if (firstDomain && firstKey && firstEntityTypeId) {
        const paramDef = getParameterDefinition(firstDomain, firstKey, firstEntityTypeId);
        
        // Only fetch existing values for string parameters
        if (paramDef?.value_type === 'string') {
          const entityType = template?.entity_types?.find((et: any) => et.id === firstEntityTypeId);
          const groupName = entityType?.name || '';
          fetchExistingValues(firstEntityTypeId, groupName, firstDomain, firstKey);
        } else if (paramDef?.value_type === 'number') {
          // Set default value for number parameters
          const defaultValue = paramDef.default_value !== null ? parseFloat(paramDef.default_value) : 0;
          newConstraint.value_number = defaultValue;
        } else if (paramDef?.value_type === 'boolean') {
          // Set default value for boolean parameters
          const defaultValue = paramDef.default_value !== null ? paramDef.default_value === 'true' : false;
          newConstraint.value_boolean = defaultValue;
        }
      }

      return newConstraints;
    });
  };

  // Helper to update a constraint
  const updateConstraint = (
    kind: 'requires' | 'consumes' | 'produces',
    slotIndex: number,
    orGroupIndex: number,
    constraintIndex: number,
    field: keyof ConstraintSpec,
    value: any
  ) => {
    setSlotConstraints(prev => {
      const newConstraints = { ...prev };
      newConstraints[kind] = [...newConstraints[kind]];
      newConstraints[kind][slotIndex] = [...newConstraints[kind][slotIndex]];
      newConstraints[kind][slotIndex][orGroupIndex] = {
        ...newConstraints[kind][slotIndex][orGroupIndex],
        constraints: [...newConstraints[kind][slotIndex][orGroupIndex].constraints],
      };
      newConstraints[kind][slotIndex][orGroupIndex].constraints[constraintIndex][field] = value;

      // Fetch existing values when entity_type_id, domain, or key changes
      const constraint = newConstraints[kind][slotIndex][orGroupIndex].constraints[constraintIndex];
      if (field === 'entity_type_id' || field === 'domain' || field === 'key') {
        if (constraint.origin === 'parameter' && constraint.entity_type_id && constraint.domain && constraint.key && constraint.domain !== 'entity_type') {
          // Get the parameter definition to check value_type
          const paramDef = getParameterDefinition(constraint.domain, constraint.key, constraint.entity_type_id);
          
          // Only fetch existing values for string parameters
          if (paramDef?.value_type === 'string') {
            // Get the group name from the entity type
            const entityType = template?.entity_types?.find((et: any) => et.id === constraint.entity_type_id);
            const groupName = entityType?.name || '';
            fetchExistingValues(constraint.entity_type_id, groupName, constraint.domain, constraint.key);
          } else if (paramDef?.value_type === 'number') {
            // Set default value for number parameters
            const defaultValue = paramDef.default_value !== null ? parseFloat(paramDef.default_value) : 0;
            newConstraints[kind][slotIndex][orGroupIndex].constraints[constraintIndex].value_number = defaultValue;
            newConstraints[kind][slotIndex][orGroupIndex].constraints[constraintIndex].value_string = null;
            newConstraints[kind][slotIndex][orGroupIndex].constraints[constraintIndex].value_boolean = null;
          } else if (paramDef?.value_type === 'boolean') {
            // Set default value for boolean parameters
            const defaultValue = paramDef.default_value !== null ? paramDef.default_value === 'true' : false;
            newConstraints[kind][slotIndex][orGroupIndex].constraints[constraintIndex].value_boolean = defaultValue;
            newConstraints[kind][slotIndex][orGroupIndex].constraints[constraintIndex].value_string = null;
            newConstraints[kind][slotIndex][orGroupIndex].constraints[constraintIndex].value_number = null;
          }
        }
      }

      // When system.group changes, refetch parameter values for other constraints in same OR group
      if (field === 'system_key' || field === 'value_string') {
        if (constraint.origin === 'system' && constraint.system_key === 'group' && constraint.value_string) {
          // Get all groups from system.group constraints in this OR group
          const orGroupConstraints = newConstraints[kind][slotIndex][orGroupIndex].constraints;
          const groupsFromSystem = orGroupConstraints
            .filter((c: any) => c.origin === 'system' && c.system_key === 'group' && c.value_string)
            .map((c: any) => c.value_string);
          
          // Refetch parameter values for all parameter constraints in this OR group
          orGroupConstraints.forEach((c: any) => {
            if (c.origin === 'parameter' && c.domain && c.key) {
              if (projectId) {
                fetchExistingValuesForGroups(c.domain, c.key, groupsFromSystem);
              }
            }
          });
        }
      }

      return newConstraints;
    });
  };

  // Helper to remove a constraint
  const removeConstraint = (
    kind: 'requires' | 'consumes' | 'produces',
    slotIndex: number,
    orGroupIndex: number,
    constraintIndex: number
  ) => {
    setSlotConstraints(prev => {
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

  // Helper to get parameter definitions for a given entity type
  const getParametersForEntityType = (entityTypeId: string, groups: string[] = []) => {
    if (!template) return [];
    const entityType = template.entity_types?.find((et: any) => et.id === entityTypeId);
    const allParams = entityType?.parameter_definitions || [];

    // If groups is empty, return all parameters
    if (groups.length === 0) {
      return allParams;
    }

    // Filter parameters by entity type (group is entity type name)
    // Find entity type IDs that match the group names
    const groupEntityIds = groups.map((groupName) => {
      const et = template.entity_types?.find((e: any) => e.name === groupName);
      return et?.id;
    }).filter(Boolean);

    return allParams.filter((param: any) => groupEntityIds.includes(param.entity_type_id));
  };

  // Helper to get parameter definition for a specific domain+key
  const getParameterDefinition = (domain: string, key: string, entityTypeId?: string | null) => {
    if (!template || !domain || !key) return null;
    
    // Search across all entity types if no specific entityTypeId provided
    const entityTypesToSearch = entityTypeId 
      ? template.entity_types?.filter((et: any) => et.id === entityTypeId)
      : template.entity_types;
    
    for (const et of entityTypesToSearch || []) {
      const param = et.parameter_definitions?.find((p: any) => p.domain === domain && p.key === key);
      if (param) return param;
    }
    return null;
  };

  // Helper to fetch existing parameter values for a constraint
  const fetchExistingValues = async (entityTypeId: string, group: string, domain: string, key: string) => {
    if (!projectId || !domain || !key) return [];

    const cacheKey = `${entityTypeId}:${group}:${domain}:${key}`;
    if (existingValues[cacheKey]) {
      return existingValues[cacheKey];
    }

    try {
      // Send empty groups array to get all parameter values
      const values = await getDistinctParameterValues(projectId, domain, key, []);
      setExistingValues(prev => ({ ...prev, [cacheKey]: values }));
      return values;
    } catch (err) {
      console.error('Failed to fetch existing values:', err);
      return [];
    }
  };

  // Helper to fetch parameter values for specific groups
  const fetchExistingValuesForGroups = async (domain: string, key: string, groups: string[]) => {
    if (!projectId || !domain || !key) return [];

    const cacheKey = `${domain}:${key}:${groups.join(',')}`;
    if (existingValues[cacheKey]) {
      return existingValues[cacheKey];
    }

    try {
      // Send groups array to get parameter values for those groups
      const values = await getDistinctParameterValues(projectId, domain, key, groups);
      setExistingValues(prev => ({ ...prev, [cacheKey]: values }));
      return values;
    } catch (err) {
      console.error('Failed to fetch existing values for groups:', err);
      return [];
    }
  };

  // Helper to fetch existing parameter values for regular recipe parameters
  const fetchParameterExistingValues = async (domain: string, key: string) => {
    if (!projectId || !domain || !key) return [];

    const cacheKey = `${domain}:${key}`;
    if (parameterExistingValues[cacheKey]) {
      return parameterExistingValues[cacheKey];
    }

    try {
      // Send only the current group to filter values
      const groups = group ? [group] : [];
      const values = await getDistinctParameterValues(projectId, domain, key, groups);
      setParameterExistingValues(prev => ({ ...prev, [cacheKey]: values }));
      return values;
    } catch (err) {
      console.error('Failed to fetch existing values:', err);
      return [];
    }
  };

  // Helper to check for duplicate values for unique parameters
  const checkParameterForDuplicate = async (domain: string, key: string, value: string) => {
    if (!value || !projectId || !domain || !key) {
      setParameterDuplicateWarnings(prev => ({ ...prev, [`${domain}:${key}`]: false }));
      return;
    }

    try {
      const groups = group ? [group] : [];
      const existingValues = await getDistinctParameterValues(projectId, domain, key, groups);
      // When editing, the current entity's value will be in the list
      // Only show warning if value appears more than once (actual duplicate)
      const count = existingValues.filter(v => v === value).length;
      const hasDuplicate = entityId ? count > 1 : count > 0;
      setParameterDuplicateWarnings(prev => ({ ...prev, [`${domain}:${key}`]: hasDuplicate }));
    } catch (err) {
      console.error('Failed to check for duplicates:', err);
    }
  };

  // Helper to render empty slots for a category
  const renderEmptySlots = (kind: 'requires' | 'consumes' | 'produces') => {
    const count = slotCounts[kind];
    const config = getSlotGroupConfig(kind);
    
    if (!config || count === 0) return null;

    return Array.from({ length: count }).map((_, index) => {
      const canRemove = count > config.min_slots;
      const slotOrGroups = slotConstraints[kind][index] || [];
      
      return (
        <div key={`${kind}-${index}`} className="card mb-4">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <p style={{ color: '#999', fontStyle: 'italic', margin: 0 }}>
              {kind.charAt(0).toUpperCase() + kind.slice(1)} slot {index + 1}
            </p>
            <button
              type="button"
              onClick={() => removeSlot(kind, index)}
              disabled={!canRemove || isSubmitting}
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
                        onChange={(e) => updateOptionQuantity(kind, index, orGroupIndex, e.target.value ? Number(e.target.value) : 1)}
                        disabled={isSubmitting}
                        min="0"
                        step="any"
                        style={{ fontSize: '12px', padding: '4px 8px', width: '60px' }}
                      />
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeOrGroup(kind, index, orGroupIndex)}
                    disabled={isSubmitting}
                    style={{ padding: '1px 4px', fontSize: '9px', border: '1px solid #ccc', background: '#fff' }}
                  >
                    ×
                  </button>
                </div>
                
                {option.constraints.map((constraint, constraintIndex) => {
                  return (
                  <div key={constraintIndex} style={{
                    display: 'flex',
                    gap: '4px',
                    alignItems: 'center',
                    marginBottom: '8px'
                  }}>
                    {/* Box 1: Type selector */}
                    <select
                      value={constraint.origin || 'parameter'}
                      onChange={(e) => {
                        const newOrigin = e.target.value as 'system' | 'parameter';
                        updateConstraint(kind, index, orGroupIndex, constraintIndex, 'origin', newOrigin);
                        // Reset fields when origin changes
                        if (newOrigin === 'system') {
                          updateConstraint(kind, index, orGroupIndex, constraintIndex, 'entity_type_id', null);
                          updateConstraint(kind, index, orGroupIndex, constraintIndex, 'domain', null);
                          updateConstraint(kind, index, orGroupIndex, constraintIndex, 'key', null);
                        } else {
                          updateConstraint(kind, index, orGroupIndex, constraintIndex, 'system_key', null);
                        }
                      }}
                      disabled={isSubmitting}
                      className="form-input"
                      style={{ width: '80px', fontSize: '12px', padding: '5px 6px' }}
                    >
                      <option value="parameter">Parameter</option>
                      <option value="system">System</option>
                    </select>

                    {/* Box 2: Key selector */}
                    <select
                      value={constraint.origin === 'system' ? (constraint.system_key || '') : (constraint.domain && constraint.key ? `${constraint.domain}:${constraint.key}` : '')}
                      onChange={(e) => {
                        if (constraint.origin === 'system') {
                          updateConstraint(kind, index, orGroupIndex, constraintIndex, 'system_key', e.target.value);
                        } else {
                          const [domain, key] = e.target.value.split(':');
                          if (domain && key) {
                            updateConstraint(kind, index, orGroupIndex, constraintIndex, 'domain', domain);
                            updateConstraint(kind, index, orGroupIndex, constraintIndex, 'key', key);
                          } else {
                            updateConstraint(kind, index, orGroupIndex, constraintIndex, 'domain', null);
                            updateConstraint(kind, index, orGroupIndex, constraintIndex, 'key', null);
                          }
                        }
                      }}
                      disabled={isSubmitting}
                      className="form-input"
                      style={{ width: '200px', fontSize: '12px', padding: '5px 6px' }}
                    >
                      {constraint.origin === 'system' ? (
                        <>
                          <option value="id">id</option>
                          <option value="group">group</option>
                        </>
                      ) : (
                        materialEntityTypes.flatMap((et: any) => {
                          // Check for system.group constraints in the same OR group
                          const orGroupConstraints = slotConstraints[kind][index][orGroupIndex].constraints || [];
                          const groupsFromSystem = orGroupConstraints
                            .filter((c: any) => c.origin === 'system' && c.system_key === 'group' && c.value_string)
                            .map((c: any) => c.value_string);

                          return getParametersForEntityType(et.id, groupsFromSystem).map((param: any) => ({
                            domain: param.domain,
                            key: param.key,
                            label: `${param.domain}:${param.key}`
                          }));
                        }).map((param: any, idx: number) => (
                          <option key={`${param.domain}:${param.key}:${idx}`} value={`${param.domain}:${param.key}`}>
                            {param.label}
                          </option>
                        ))
                      )}
                    </select>

                    {/* Box 3: Operator selector */}
                    <select
                      value={constraint.operator || '='}
                      onChange={(e) => updateConstraint(kind, index, orGroupIndex, constraintIndex, 'operator', e.target.value)}
                      disabled={isSubmitting}
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

                    {/* Box 4: Value input */}
                    {constraint.origin === 'system' ? (
                      constraint.system_key === 'group' ? (
                        <select
                          value={constraint.value_string || ''}
                          onChange={(e) => updateConstraint(kind, index, orGroupIndex, constraintIndex, 'value_string', e.target.value)}
                          disabled={isSubmitting}
                          className="form-input"
                          style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                        >
                          {materialEntityTypes.map((et: any) => (
                            <option key={et.id} value={et.name}>
                              {et.name}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type="text"
                          value={constraint.value_string || ''}
                          onChange={(e: any) => updateConstraint(kind, index, orGroupIndex, constraintIndex, 'value_string', e.target.value)}
                          disabled={isSubmitting}
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
                            <Combobox
                              value={constraint.value_string || ''}
                              onChange={(value) => updateConstraint(kind, index, orGroupIndex, constraintIndex, 'value_string', value)}
                              options={(() => {
                                // Check for system.group constraints in the same OR group
                                const orGroupConstraints = slotConstraints[kind][index][orGroupIndex].constraints || [];
                                const groupsFromSystem = orGroupConstraints
                                  .filter((c: any) => c.origin === 'system' && c.system_key === 'group' && c.value_string)
                                  .map((c: any) => c.value_string);
                                
                                // Use these groups to fetch parameter values
                                const cacheKey = `${constraint.domain}:${constraint.key}:${groupsFromSystem.join(',')}`;
                                if (existingValues[cacheKey]) {
                                  return existingValues[cacheKey];
                                }
                                
                                // Trigger fetch if not cached
                                if (constraint.domain && constraint.key && projectId) {
                                  fetchExistingValuesForGroups(constraint.domain, constraint.key, groupsFromSystem);
                                }
                                
                                return existingValues[cacheKey] || [];
                              })()}
                              disabled={isSubmitting}
                              placeholder="Value"
                              className="form-input"
                              style={{ flex: 1 }}
                            />
                          );
                        } else if (valueType === 'number') {
                          return (
                            <input
                              type="number"
                              value={constraint.value_number ?? ''}
                              onChange={(e: any) => updateConstraint(kind, index, orGroupIndex, constraintIndex, 'value_number', e.target.value ? Number(e.target.value) : null)}
                              disabled={isSubmitting}
                              placeholder="Value"
                              className="form-input"
                              style={{ flex: 1 }}
                            />
                          );
                        } else if (valueType === 'boolean') {
                          return (
                            <select
                              value={constraint.value_boolean === true ? 'true' : constraint.value_boolean === false ? 'false' : ''}
                              onChange={(e) => updateConstraint(kind, index, orGroupIndex, constraintIndex, 'value_boolean', e.target.value === 'true' ? true : e.target.value === 'false' ? false : null)}
                              disabled={isSubmitting}
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
                      type="button"
                      onClick={() => removeConstraint(kind, index, orGroupIndex, constraintIndex)}
                      disabled={isSubmitting}
                      style={{ padding: '1px 4px', fontSize: '9px', border: '1px solid #ccc', background: '#fff' }}
                    >
                      ×
                    </button>
                  </div>
                  );
                })}
                
                <button
                  type="button"
                  onClick={() => addConstraint(kind, index, orGroupIndex)}
                  disabled={isSubmitting}
                  className="button button--primary"
                  style={{ padding: '4px 8px', fontSize: '12px' }}
                >
                  + Add Parameter Requirement
                </button>
              </div>
            ))}
            
            <button
              type="button"
              onClick={() => addOrGroup(kind, index)}
              disabled={isSubmitting}
              className="button button--primary"
              style={{ padding: '4px 8px', fontSize: '12px' }}
            >
              + Add Option
            </button>
          </div>
        </div>
      );
    });
  };

  // Helper to render slot controls for a category
  const renderSlotControls = (kind: 'requires' | 'consumes' | 'produces') => {
    const config = getSlotGroupConfig(kind);
    if (!config) return null;

    const currentCount = slotCounts[kind];
    const maxSlots = config.max_slots === null ? '∞' : config.max_slots;
    const canAdd = config.max_slots === null ? true : currentCount < config.max_slots;

    return (
      <div style={{ display: 'flex', gap: '8px', marginTop: '12px', alignItems: 'center' }}>
        <button
          type="button"
          onClick={() => addSlot(kind)}
          disabled={!canAdd || isSubmitting}
          className="button button--primary"
          style={{ padding: '4px 8px', fontSize: '12px' }}
        >
          + Add Slot
        </button>
        <span style={{ fontSize: '12px', color: '#666' }}>
          ({currentCount}/{maxSlots})
        </span>
      </div>
    );
  };

  return (
    <form onSubmit={handleSubmit}>
      {errorMessage && <p className="form-error">{errorMessage}</p>}
      {validationError && <p className="form-error">{validationError}</p>}

      <div className="card mb-6">
        <h3 className="card-title mb-4">Entity Parameters</h3>
        {sortedParameters.map((param, index) => (
          <div key={`${param.domain}:${param.key}`} style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '12px', alignItems: 'center', marginBottom: '12px' }}>
            {param.value_type === 'boolean' ? (
              <>
                <div style={{ position: 'relative' }}>
                  <label
                    htmlFor={`param-${index}`}
                    className="form-label"
                    style={{ margin: 0, cursor: param.description ? 'help' : 'default' }}
                    onMouseEnter={() => {
                      if (param.description) {
                        setHoveredDescription(param.description);
                      }
                    }}
                    onMouseLeave={() => {
                      setHoveredDescription(null);
                    }}
                  >
                    {param.label || param.key}
                    {param.required && ' *'}
                  </label>
                  {hoveredDescription && hoveredDescription === param.description && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '100%',
                        left: 0,
                        marginTop: '4px',
                        backgroundColor: '#333',
                        color: '#fff',
                        padding: '8px 12px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        maxWidth: '300px',
                        zIndex: 1000,
                        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                        pointerEvents: 'none',
                      }}
                    >
                      {hoveredDescription}
                    </div>
                  )}
                </div>
                <input
                  id={`param-${index}`}
                  type="checkbox"
                  checked={param.value === true}
                  onChange={(e) => updateParameter(param.domain, param.key, e.target.checked)}
                  disabled={isSubmitting}
                  style={{ width: '19px', height: '19px' }}
                />
              </>
            ) : (
              <>
                <div style={{ position: 'relative' }}>
                  <label
                    htmlFor={`param-${index}`}
                    className="form-label"
                    style={{ margin: 0, cursor: param.description ? 'help' : 'default' }}
                    onMouseEnter={() => {
                      if (param.description) {
                        setHoveredDescription(param.description);
                      }
                    }}
                    onMouseLeave={() => {
                      setHoveredDescription(null);
                    }}
                  >
                    {param.label || param.key}
                    {param.required && ' *'}
                  </label>
                  {hoveredDescription && hoveredDescription === param.description && (
                    <div
                      style={{
                        position: 'absolute',
                        top: '100%',
                        left: 0,
                        marginTop: '4px',
                        backgroundColor: '#333',
                        color: '#fff',
                        padding: '8px 12px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        maxWidth: '300px',
                        zIndex: 1000,
                        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                        pointerEvents: 'none',
                      }}
                    >
                      {hoveredDescription}
                    </div>
                  )}
                </div>
                {param.value_type === 'number' && (
                  <input
                    id={`param-${index}`}
                    type="number"
                    value={param.value ?? ''}
                    onChange={(e) => updateParameter(param.domain, param.key, e.target.value ? Number(e.target.value) : null)}
                    disabled={isSubmitting}
                    className="form-input"
                    step="any"
                  />
                )}
                {param.value_type === 'string' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {param.is_searchable ? (
                      <Combobox
                        value={param.value ?? ''}
                        onChange={(value) => updateParameter(param.domain, param.key, value)}
                        options={parameterExistingValues[`${param.domain}:${param.key}`] || []}
                        disabled={isSubmitting}
                        placeholder={`Select or type ${param.label || param.key}...`}
                        style={{ flex: 1 }}
                      />
                    ) : (
                      <input
                        id={`param-${index}`}
                        type="text"
                        value={param.value ?? ''}
                        onChange={(e) => updateParameter(param.domain, param.key, e.target.value)}
                        disabled={isSubmitting}
                        className="form-input"
                        style={{ flex: 1 }}
                      />
                    )}
                    {param.is_unique && param.is_searchable && parameterDuplicateWarnings[`${param.domain}:${param.key}`] && (
                      <span
                        title="This value already exists in another entity"
                        style={{ 
                          color: '#ff6b6b', 
                          fontSize: '16px',
                          cursor: 'help'
                        }}
                      >
                        ⚠️
                      </span>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        ))}
      </div>


      {entityId && (
        <div className="card mb-6">
          <h3 className="card-title mb-4">Recipe Image</h3>
          <ImageUpload
            entityId={entityId}
            targetSize={targetImageSize}
            currentImage={currentImage}
            onUploadComplete={setImageUrl}
            onUploadError={(error) => setValidationError(error)}
            onRemove={() => setImageUrl(null)}
          />
        </div>
      )}

      <div className="card mb-6">
        <h3 className="card-title mb-4">Required</h3>
        {renderEmptySlots('requires')}
        {renderSlotControls('requires')}
      </div>

      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
        <div className="card" style={{ flex: 1 }}>
          <h3 className="card-title mb-4">Consumes</h3>
          {renderEmptySlots('consumes')}
          {renderSlotControls('consumes')}
        </div>
        <div className="card" style={{ flex: 1 }}>
          <h3 className="card-title mb-4">Produces</h3>
          {renderEmptySlots('produces')}
          {renderSlotControls('produces')}
        </div>
      </div>

      <div className="form-actions">
        <button
          type="submit"
          disabled={isSubmitting}
          className="button button--primary"
        >
          {isSubmitting ? 'Saving...' : submitLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isSubmitting}
          className="button button--secondary"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
