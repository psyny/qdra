import { useState, useEffect } from 'react';
import { Combobox } from './Combobox';
import { getDistinctParameterValues } from '../api/entities';
import { ConstraintSpec } from '../api/planning';

type InternalConstraintSpec = {
  origin: 'system' | 'parameter';
  system_key?: string | null;
  entity_type_id?: string | null;
  domain?: string | null;
  key?: string | null;
  operator: string;
  value_string?: string | null;
  value_number?: number | null;
  value_boolean?: boolean | null;
  is_wildcard?: boolean;
};

type ConstraintBuilderProps = {
  constraints: ConstraintSpec[];
  onChange: (constraints: ConstraintSpec[]) => void;
  projectId?: string;
  template?: any;
  disabled?: boolean;
  targetType?: string;
};

export function ConstraintBuilder({
  constraints,
  onChange,
  projectId,
  template,
  disabled = false,
  targetType = 'material',
}: ConstraintBuilderProps) {
  const [existingValues, setExistingValues] = useState<Record<string, string[]>>({});

  // Convert API ConstraintSpec to internal format
  const toInternalConstraints = (apiConstraints: ConstraintSpec[]): InternalConstraintSpec[] => {
    return apiConstraints.map((c) => {
      if (c.domain === '__system__') {
        return {
          origin: 'system',
          system_key: c.key,
          entity_type_id: null,
          domain: null,
          key: null,
          operator: c.operator,
          value_string: c.value_string,
          value_number: c.value_number,
          value_boolean: c.value_boolean,
          is_wildcard: c.is_wildcard,
        };
      } else {
        return {
          origin: 'parameter',
          system_key: null,
          entity_type_id: null,
          domain: c.domain,
          key: c.key,
          operator: c.operator,
          value_string: c.value_string,
          value_number: c.value_number,
          value_boolean: c.value_boolean,
          is_wildcard: c.is_wildcard,
        };
      }
    });
  };

  // Convert internal format to API ConstraintSpec
  const toApiConstraints = (internalConstraints: InternalConstraintSpec[]): ConstraintSpec[] => {
    return internalConstraints.map((c) => {
      const baseConstraint: ConstraintSpec = {
        domain: c.origin === 'system' ? '__system__' : (c.domain || ''),
        key: c.origin === 'system' ? (c.system_key || '') : (c.key || ''),
        operator: c.operator,
        is_wildcard: c.is_wildcard,
      };

      // Only include the value field that's actually set
      if (c.value_string !== null && c.value_string !== undefined && c.value_string !== '') {
        baseConstraint.value_string = c.value_string;
      }
      if (c.value_number !== null && c.value_number !== undefined) {
        baseConstraint.value_number = c.value_number;
      }
      if (c.value_boolean !== null && c.value_boolean !== undefined) {
        baseConstraint.value_boolean = c.value_boolean;
      }

      return baseConstraint;
    });
  };

  const [internalConstraints, setInternalConstraints] = useState<InternalConstraintSpec[]>(
    toInternalConstraints(constraints)
  );

  // Sync internal state with props
  useEffect(() => {
    setInternalConstraints(toInternalConstraints(constraints));
  }, [constraints]);

  // Helper to get parameter definition for a specific domain+key
  const getParameterDefinition = (domain: string, key: string) => {
    if (!template || !domain || !key) return null;
    
    for (const et of template.entity_types || []) {
      const param = et.parameter_definitions?.find((p: any) => p.domain === domain && p.key === key);
      if (param) return param;
    }
    return null;
  };

  // Helper to fetch existing parameter values
  const fetchExistingValues = async (domain: string, key: string) => {
    if (!projectId || !domain || !key) return [];

    const cacheKey = `${domain}:${key}`;
    if (existingValues[cacheKey]) {
      return existingValues[cacheKey];
    }

    try {
      const values = await getDistinctParameterValues(projectId, domain, key, []);
      setExistingValues((prev: Record<string, string[]>) => ({ ...prev, [cacheKey]: values }));
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
      const values = await getDistinctParameterValues(projectId, domain, key, groups);
      setExistingValues((prev: Record<string, string[]>) => ({ ...prev, [cacheKey]: values }));
      return values;
    } catch (err) {
      console.error('Failed to fetch existing values for groups:', err);
      return [];
    }
  };

  // Helper to get all available domain:key pairs (deduplicated)
  const getAvailableParameters = (groupsFromSystem: string[] = []) => {
    if (!template) return [];
    
    const paramMap = new Map<string, { domain: string; key: string; label: string; entity_type_id: string }>();
    
    template.entity_types?.forEach((et: any) => {
      // Filter by target type (material vs recipe) - this should always apply
      if (targetType === 'material' && et.kind !== 'material') {
        return; // Skip non-material entity types for material target
      }
      if (targetType === 'recipe' && et.kind !== 'recipe') {
        return; // Skip non-recipe entity types for recipe target
      }
      
      // Filter parameters by entity type if groups are specified
      if (groupsFromSystem.length > 0) {
        const groupEntityIds = groupsFromSystem.map((groupName) => {
          const entityType = template.entity_types?.find((e: any) => e.name === groupName);
          return entityType?.id;
        }).filter(Boolean);
        
        if (!groupEntityIds.includes(et.id)) {
          return; // Skip this entity type if not in the groups list
        }
      }
      
      et.parameter_definitions?.forEach((param: any) => {
        const key = `${param.domain}:${param.key}`;
        if (!paramMap.has(key)) {
          paramMap.set(key, {
            domain: param.domain,
            key: param.key,
            label: key,
            entity_type_id: et.id,
          });
        }
      });
    });
    
    return Array.from(paramMap.values());
  };

  // Helper to get material entity types (for system.group selector)
  const getMaterialEntityTypes = () => {
    if (!template) return [];
    // Filter by target type
    return template.entity_types?.filter((et: any) => {
      if (targetType === 'material' && et.kind !== 'material') {
        return false;
      }
      if (targetType === 'recipe' && et.kind !== 'recipe') {
        return false;
      }
      return true;
    }) || [];
  };

  const addConstraint = () => {
    const availableParams = getAvailableParameters();
    const firstParam = availableParams[0];
    
    const newConstraint: InternalConstraintSpec = {
      origin: 'parameter',
      system_key: null,
      entity_type_id: firstParam?.entity_type_id || null,
      domain: firstParam?.domain || '',
      key: firstParam?.key || '',
      operator: '=',
      value_string: undefined,
      value_number: undefined,
      value_boolean: undefined,
      is_wildcard: false,
    };

    // Fetch existing values for the auto-selected domain+key
    if (firstParam?.domain && firstParam?.key && projectId) {
      const paramDef = getParameterDefinition(firstParam.domain, firstParam.key);
      
      if (paramDef?.value_type === 'string') {
        fetchExistingValues(firstParam.domain, firstParam.key);
      } else if (paramDef?.value_type === 'number') {
        const defaultValue = paramDef.default_value !== null ? parseFloat(paramDef.default_value) : 0;
        newConstraint.value_number = defaultValue;
      } else if (paramDef?.value_type === 'boolean') {
        const defaultValue = paramDef.default_value !== null ? paramDef.default_value === 'true' : false;
        newConstraint.value_boolean = defaultValue;
      }
    }

    const updated = [...internalConstraints, newConstraint];
    setInternalConstraints(updated);
    onChange(toApiConstraints(updated));
  };

  const updateConstraint = (index: number, field: keyof InternalConstraintSpec, value: any) => {
    const updated = [...internalConstraints];
    
    // Clear other value fields when setting a specific value field
    if (field === 'value_string') {
      updated[index] = { ...updated[index], value_string: value, value_number: undefined, value_boolean: undefined };
    } else if (field === 'value_number') {
      updated[index] = { ...updated[index], value_number: value, value_string: undefined, value_boolean: undefined };
    } else if (field === 'value_boolean') {
      updated[index] = { ...updated[index], value_boolean: value, value_string: undefined, value_number: undefined };
    } else {
      updated[index] = { ...updated[index], [field]: value };
    }
    
    setInternalConstraints(updated);
    onChange(toApiConstraints(updated));

    // Fetch existing values when domain or key changes
    const constraint = updated[index];
    if ((field === 'domain' || field === 'key') && constraint.origin === 'parameter' && constraint.domain && constraint.key && projectId) {
      const paramDef = getParameterDefinition(constraint.domain, constraint.key);
      
      if (paramDef?.value_type === 'string') {
        fetchExistingValues(constraint.domain, constraint.key);
      } else if (paramDef?.value_type === 'number') {
        const defaultValue = paramDef.default_value !== null ? parseFloat(paramDef.default_value) : 0;
        updated[index].value_number = defaultValue;
        updated[index].value_string = undefined;
        updated[index].value_boolean = undefined;
        setInternalConstraints(updated);
        onChange(toApiConstraints(updated));
      } else if (paramDef?.value_type === 'boolean') {
        const defaultValue = paramDef.default_value !== null ? paramDef.default_value === 'true' : false;
        updated[index].value_boolean = defaultValue;
        updated[index].value_string = undefined;
        updated[index].value_number = undefined;
        setInternalConstraints(updated);
        onChange(toApiConstraints(updated));
      }
    }
  };

  const updateConstraintMultiple = (index: number, updates: Partial<InternalConstraintSpec>) => {
    const updated = [...internalConstraints];
    updated[index] = { ...updated[index], ...updates };
    setInternalConstraints(updated);
    onChange(toApiConstraints(updated));

    // Fetch existing values when domain or key changes
    const constraint = updated[index];
    if ((updates.domain !== undefined || updates.key !== undefined) && constraint.origin === 'parameter' && constraint.domain && constraint.key && projectId) {
      const paramDef = getParameterDefinition(constraint.domain, constraint.key);
      
      if (paramDef?.value_type === 'string') {
        fetchExistingValues(constraint.domain, constraint.key);
      } else if (paramDef?.value_type === 'number') {
        const defaultValue = paramDef.default_value !== null ? parseFloat(paramDef.default_value) : 0;
        updated[index].value_number = defaultValue;
        updated[index].value_string = undefined;
        updated[index].value_boolean = undefined;
        setInternalConstraints(updated);
        onChange(toApiConstraints(updated));
      } else if (paramDef?.value_type === 'boolean') {
        const defaultValue = paramDef.default_value !== null ? paramDef.default_value === 'true' : false;
        updated[index].value_boolean = defaultValue;
        updated[index].value_string = undefined;
        updated[index].value_number = undefined;
        setInternalConstraints(updated);
        onChange(toApiConstraints(updated));
      }
    }
  };

  const removeConstraint = (index: number) => {
    const updated = internalConstraints.filter((_: any, i: number) => i !== index);
    setInternalConstraints(updated);
    onChange(toApiConstraints(updated));
  };

  const materialEntityTypes = getMaterialEntityTypes();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {internalConstraints.map((constraint, index) => {
        const paramDef = constraint.origin === 'parameter' 
          ? getParameterDefinition(constraint.domain || '', constraint.key || '')
          : null;
        const valueType = paramDef?.value_type || 'string';
        
        // Check for system.group constraints in the same constraint list
        const groupsFromSystem = internalConstraints
          .filter((c: any) => c.origin === 'system' && c.system_key === 'group' && c.value_string)
          .map((c: any) => c.value_string);
        
        const cacheKey = `${constraint.domain}:${constraint.key}:${groupsFromSystem.join(',')}`;
        const availableParameters = getAvailableParameters(groupsFromSystem);

        return (
          <div key={index} style={{
            display: 'flex',
            gap: '4px',
            alignItems: 'center',
          }}>
            {/* Type selector */}
            <select
              value={constraint.origin || 'parameter'}
              onChange={(e) => {
                const newOrigin = e.target.value as 'system' | 'parameter';
                // Reset fields when origin changes
                if (newOrigin === 'system') {
                  updateConstraintMultiple(index, { 
                    origin: newOrigin,
                    entity_type_id: null,
                    domain: null,
                    key: null,
                    value_string: undefined,
                    value_number: undefined,
                    value_boolean: undefined
                  });
                } else {
                  updateConstraintMultiple(index, { 
                    origin: newOrigin,
                    system_key: null,
                    value_string: undefined,
                    value_number: undefined,
                    value_boolean: undefined
                  });
                }
              }}
              disabled={disabled}
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
                  updateConstraint(index, 'system_key', e.target.value);
                } else {
                  const [domain, key] = e.target.value.split(':');
                  if (domain && key) {
                    updateConstraintMultiple(index, { domain, key });
                  } else {
                    updateConstraintMultiple(index, { domain: '', key: '' });
                  }
                }
              }}
              disabled={disabled}
              className="form-input"
              style={{ width: '200px', fontSize: '12px', padding: '5px 6px' }}
            >
              {constraint.origin === 'system' ? (
                <>
                  <option value="id">id</option>
                  <option value="group">group</option>
                </>
              ) : (
                availableParameters.map((param: any, idx: number) => (
                  <option key={`${param.domain}:${param.key}:${idx}`} value={`${param.domain}:${param.key}`}>
                    {param.label}
                  </option>
                ))
              )}
            </select>

            {/* Operator selector */}
            <select
              value={constraint.operator || '='}
              onChange={(e) => updateConstraint(index, 'operator', e.target.value)}
              disabled={disabled}
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

            {/* Value input based on type */}
            {constraint.origin === 'system' ? (
              constraint.system_key === 'group' ? (
                <select
                  value={constraint.value_string || ''}
                  onChange={(e) => updateConstraint(index, 'value_string', e.target.value)}
                  disabled={disabled}
                  className="form-input"
                  style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                >
                  <option value="">Select group...</option>
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
                  onChange={(e) => updateConstraint(index, 'value_string', e.target.value)}
                  disabled={disabled}
                  placeholder="Value"
                  className="form-input"
                  style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                />
              )
            ) : (
              (() => {
                if (valueType === 'string') {
                  return (
                    <Combobox
                      value={constraint.value_string || ''}
                      onChange={(value) => updateConstraint(index, 'value_string', value)}
                      options={(() => {
                        if (existingValues[cacheKey]) {
                          return existingValues[cacheKey];
                        }
                        // Trigger fetch if not cached
                        if (constraint.domain && constraint.key && projectId) {
                          fetchExistingValuesForGroups(constraint.domain, constraint.key, groupsFromSystem);
                        }
                        return existingValues[cacheKey] || [];
                      })()}
                      disabled={disabled}
                      placeholder="Value"
                      style={{ flex: 1 }}
                    />
                  );
                } else if (valueType === 'number') {
                  return (
                    <input
                      type="number"
                      value={constraint.value_number ?? ''}
                      onChange={(e) => updateConstraint(index, 'value_number', e.target.value ? Number(e.target.value) : undefined)}
                      disabled={disabled}
                      placeholder="Value"
                      className="form-input"
                      style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
                      step="any"
                    />
                  );
                } else if (valueType === 'boolean') {
                  return (
                    <select
                      value={constraint.value_boolean === true ? 'true' : constraint.value_boolean === false ? 'false' : ''}
                      onChange={(e) => updateConstraint(index, 'value_boolean', e.target.value === 'true' ? true : e.target.value === 'false' ? false : undefined)}
                      disabled={disabled}
                      className="form-input"
                      style={{ flex: 1, fontSize: '12px', padding: '5px 6px' }}
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
              onClick={() => removeConstraint(index)}
              disabled={disabled}
              style={{ padding: '1px 4px', fontSize: '9px', border: '1px solid #ccc', background: '#fff' }}
            >
              ×
            </button>
          </div>
        );
      })}
      
      <button
        type="button"
        onClick={addConstraint}
        disabled={disabled}
        className="button button--primary"
        style={{ padding: '4px 8px', fontSize: '12px', alignSelf: 'flex-start' }}
      >
        + Add Constraint
      </button>
    </div>
  );
}
