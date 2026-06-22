import { ScoreFormulaDef } from '../api/planning';

type ScoreFormulaCardProps = {
  formula: ScoreFormulaDef;
  onChange: (formula: ScoreFormulaDef) => void;
  onRemove: () => void;
  disabled?: boolean;
};

export function ScoreFormulaCard({
  formula,
  onChange,
  onRemove,
  disabled = false,
}: ScoreFormulaCardProps) {
  return (
    <div className="card" style={{ padding: '12px', marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h4 style={{ fontSize: '14px', margin: 0 }}>Score Formula</h4>
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
        {/* Formula Name */}
        <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '8px', alignItems: 'center' }}>
          <label className="form-label" style={{ fontSize: '12px' }}>Formula Name</label>
          <input
            type="text"
            value={formula.name}
            onChange={(e) => onChange({ ...formula, name: e.target.value })}
            disabled={disabled}
            className="form-input"
            style={{ fontSize: '12px', padding: '4px 8px' }}
            placeholder="e.g., total_score"
          />
        </div>

        {/* Formula Expression */}
        <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '8px', alignItems: 'center' }}>
          <label className="form-label" style={{ fontSize: '12px' }}>Formula</label>
          <input
            type="text"
            value={formula.formula}
            onChange={(e) => onChange({ ...formula, formula: e.target.value })}
            disabled={disabled}
            className="form-input"
            style={{ fontSize: '12px', padding: '4px 8px' }}
            placeholder="e.g., var1 * 0.5 + var2 * 0.3"
          />
        </div>

        <p style={{ fontSize: '11px', color: '#666', marginTop: '4px' }}>
          Use variable names defined in User Variables (e.g., total_cost, material_count)
        </p>
      </div>
    </div>
  );
}
