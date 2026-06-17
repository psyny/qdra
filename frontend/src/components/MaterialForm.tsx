import { useState } from 'react';
import { MaterialParameterEditor } from './MaterialParameterEditor';
import { DraftParameter } from './ParameterRow';

type MaterialFormProps = {
  initialParameters?: DraftParameter[];
  isSubmitting?: boolean;
  errorMessage?: string | null;
  onSubmit: (parameters: DraftParameter[]) => void;
  onCancel: () => void;
  submitLabel: string;
};

export function MaterialForm({
  initialParameters = [],
  isSubmitting = false,
  errorMessage = null,
  onSubmit,
  onCancel,
  submitLabel,
}: MaterialFormProps) {
  const [name, setName] = useState('');
  const [category, setCategory] = useState('');
  const [parameters, setParameters] = useState<DraftParameter[]>(initialParameters);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Validate name
    if (!name.trim()) {
      setValidationError('Material name is required');
      return;
    }

    // Build final parameters list
    const finalParameters: DraftParameter[] = [
      { domain: 'identity', key: 'name', value: name.trim(), value_type: 'string' },
    ];

    if (category.trim()) {
      finalParameters.push({
        domain: 'identity',
        key: 'category',
        value: category.trim(),
        value_type: 'string',
      });
    }

    // Add custom parameters
    finalParameters.push(...parameters);

    // Validate no duplicate domain/key pairs
    const seen = new Set<string>();
    for (const param of finalParameters) {
      const key = `${param.domain}:${param.key}`;
      if (seen.has(key)) {
        setValidationError(`Duplicate parameter: ${key}`);
        return;
      }
      seen.add(key);
    }

    // Validate all parameters have domain and key
    for (const param of finalParameters) {
      if (!param.domain.trim() || !param.key.trim()) {
        setValidationError('All parameters must have a domain and key');
        return;
      }
    }

    onSubmit(finalParameters);
  };

  return (
    <form onSubmit={handleSubmit}>
      {errorMessage && <p className="form-error">{errorMessage}</p>}
      {validationError && <p className="form-error">{validationError}</p>}

      <div className="card mb-6">
        <h3 className="card-title mb-4">Material Identity</h3>
        <div className="form-field">
          <label htmlFor="name" className="form-label">
            Name *
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={isSubmitting}
            className="form-input"
            placeholder="e.g., iron_ore"
          />
        </div>
        <div className="form-field">
          <label htmlFor="category" className="form-label">
            Category
          </label>
          <input
            id="category"
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            disabled={isSubmitting}
            className="form-input"
            placeholder="e.g., resource"
          />
        </div>
      </div>

      <div className="card mb-6">
        <h3 className="card-title mb-4">Parameters</h3>
        <MaterialParameterEditor
          parameters={parameters}
          onChange={setParameters}
        />
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
