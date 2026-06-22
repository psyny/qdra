import { ConstraintBuilder } from './ConstraintBuilder';
import { ConstraintSpec } from '../api/planning';

type ConstraintRuleCardProps = {
  constraints: ConstraintSpec[];
  onChange: (constraints: ConstraintSpec[]) => void;
  onRemove: () => void;
  projectId?: string;
  template?: any;
  disabled?: boolean;
  targetType: 'material' | 'recipe';
  key?: string | number;
};

export function ConstraintRuleCard({
  constraints,
  onChange,
  onRemove,
  projectId,
  template,
  disabled = false,
  targetType,
}: ConstraintRuleCardProps) {
  return (
    <div
      style={{
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '4px',
        padding: '12px',
        marginBottom: '8px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
        <button
          type="button"
          onClick={onRemove}
          disabled={disabled}
          style={{
            padding: '2px 8px',
            fontSize: '12px',
            border: '1px solid #ccc',
            background: '#fff',
            borderRadius: '3px',
          }}
        >
          Remove Rule
        </button>
      </div>
      <ConstraintBuilder
        constraints={constraints}
        onChange={onChange}
        projectId={projectId}
        template={template}
        disabled={disabled}
        targetType={targetType}
      />
    </div>
  );
}
