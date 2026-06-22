import { ConstraintSpec, ConstraintRule, UserVariableDef } from '../api/planning';
import { ConstraintBuilder } from './ConstraintBuilder';
import { HorizontalLine } from './HorizontalLine';

type UserVariableCardProps = {
  variable: UserVariableDef;
  onChange: (variable: UserVariableDef) => void;
  onRemove: () => void;
  projectId?: string;
  template?: any;
  disabled?: boolean;
};

export function UserVariableCard({
  variable,
  onChange,
  onRemove,
  projectId,
  template,
  disabled = false,
}: UserVariableCardProps) {
  // Helper to get all available domain:key pairs
  const getAvailableParameters = () => {
    if (!template) return [];
    
    const paramMap = new Map<string, { domain: string; key: string; label: string }>();
    
    template.entity_types?.forEach((et: any) => {
      et.parameter_definitions?.forEach((param: any) => {
        const key = `${param.domain}:${param.key}`;
        if (!paramMap.has(key)) {
          paramMap.set(key, {
            domain: param.domain,
            key: param.key,
            label: key,
          });
        }
      });
    });
    
    return Array.from(paramMap.values());
  };

  // Helper to update constraints within a rule
  const updateRuleConstraints = (ruleIndex: number, constraints: ConstraintSpec[]) => {
    const rules = [...variable.constraints];
    rules[ruleIndex] = { constraints };
    onChange({ ...variable, constraints: rules });
  };

  // Helper to add a new constraint rule
  const addConstraintRule = () => {
    const newRule: ConstraintRule = { constraints: [] };
    onChange({ ...variable, constraints: [...variable.constraints, newRule] });
  };

  // Helper to remove a constraint rule
  const removeConstraintRule = (ruleIndex: number) => {
    onChange({
      ...variable,
      constraints: variable.constraints.filter((_: ConstraintRule, i: number) => i !== ruleIndex)
    });
  };

  const availableParameters = getAvailableParameters();

  return (
    <div className="card" style={{ padding: '12px', marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4 style={{ fontSize: '14px', margin: 0 }}>User Variable</h4>
        <button
          type="button"
          onClick={onRemove}
          disabled={disabled}
          className="button button--danger"
          style={{ padding: '2px 8px', fontSize: '12px' }}
        >
          Remove
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {/* Variable Name */}
        <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '8px', alignItems: 'center' }}>
          <label className="form-label" style={{ fontSize: '12px' }}>Variable Name</label>
          <input
            type="text"
            value={variable.name}
            onChange={(e) => onChange({ ...variable, name: e.target.value })}
            disabled={disabled}
            className="form-input"
            style={{ fontSize: '12px', padding: '4px 8px' }}
            placeholder="e.g., total_cost"
          />
        </div>

        {/* Parameter Domain:Key */}
        <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '8px', alignItems: 'center' }}>
          <label className="form-label" style={{ fontSize: '12px' }}>Parameter</label>
          <select
            value={`${variable.parameter_domain}:${variable.parameter_key}`}
            onChange={(e) => {
              const [domain, key] = e.target.value.split(':');
              onChange({ ...variable, parameter_domain: domain, parameter_key: key });
            }}
            disabled={disabled}
            className="form-input"
            style={{ fontSize: '12px', padding: '4px 8px' }}
          >
            {availableParameters.length === 0 ? (
              <option value="">No parameters available</option>
            ) : (
              availableParameters.map((param: any, idx: number) => (
                <option key={`${param.domain}:${param.key}:${idx}`} value={`${param.domain}:${param.key}`}>
                  {param.label}
                </option>
              ))
            )}
          </select>
        </div>

        <HorizontalLine />

        {/* Constraint Rules */}
        <div>
          <h5 style={{ fontSize: '12px', marginBottom: '8px', marginTop: '8px' }}>Constraint Rules (OR semantics)</h5>
          {variable.constraints.map((rule: ConstraintRule, ruleIndex: number) => (
            <div key={ruleIndex} className="card" style={{ padding: '12px', marginBottom: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px', fontWeight: 'bold' }}>Rule {ruleIndex + 1}</span>
                <button
                  type="button"
                  onClick={() => removeConstraintRule(ruleIndex)}
                  disabled={disabled}
                  className="button button--danger"
                  style={{ padding: '2px 8px', fontSize: '12px' }}
                >
                  Remove
                </button>
              </div>
              <ConstraintBuilder
                constraints={rule.constraints}
                onChange={(constraints) => updateRuleConstraints(ruleIndex, constraints)}
                projectId={projectId}
                template={template}
                disabled={disabled}
                targetType="material"
              />
            </div>
          ))}
          <button
            type="button"
            onClick={addConstraintRule}
            disabled={disabled}
            className="button button--secondary"
            style={{ padding: '4px 8px', fontSize: '12px' }}
          >
            + Add Constraint Rule
          </button>
        </div>
      </div>
    </div>
  );
}
