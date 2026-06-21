import { useState } from 'react';
import { DraftParameter } from './ParameterRow';
import { ImageUpload } from './ImageUpload';

type MaterialFormProps = {
  initialParameters?: DraftParameter[];
  isSubmitting?: boolean;
  errorMessage?: string | null;
  onSubmit: (parameters: DraftParameter[], imageUrl?: string) => void;
  onCancel: () => void;
  submitLabel: string;
  entityId?: string;
  targetImageSize?: number;
  currentImage?: string | null;
};

export function MaterialForm({
  initialParameters = [],
  isSubmitting = false,
  errorMessage = null,
  onSubmit,
  onCancel,
  submitLabel,
  entityId,
  targetImageSize = 256,
  currentImage,
}: MaterialFormProps) {
  const [parameters, setParameters] = useState<DraftParameter[]>(initialParameters);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(currentImage || null);
  const [hoveredDescription, setHoveredDescription] = useState<string | null>(null);

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

    onSubmit(parameters, imageUrl || undefined);
  };

  const updateParameter = (index: number, value: any) => {
    const updated = [...parameters];
    updated[index] = { ...updated[index], value };
    setParameters(updated);
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

  return (
    <form onSubmit={handleSubmit}>
      {errorMessage && <p className="form-error">{errorMessage}</p>}
      {validationError && <p className="form-error">{validationError}</p>}

      <div className="card mb-6">
        <h3 className="card-title mb-4">Material Parameters</h3>
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
                  onChange={(e) => updateParameter(index, e.target.checked)}
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
                    onChange={(e) => updateParameter(index, e.target.value ? Number(e.target.value) : null)}
                    disabled={isSubmitting}
                    className="form-input"
                    step="any"
                  />
                )}
                {param.value_type === 'string' && (
                  <input
                    id={`param-${index}`}
                    type="text"
                    value={param.value ?? ''}
                    onChange={(e) => updateParameter(index, e.target.value)}
                    disabled={isSubmitting}
                    className="form-input"
                  />
                )}
              </>
            )}
          </div>
        ))}
      </div>


      {entityId && (
        <div className="card mb-6">
          <h3 className="card-title mb-4">Material Image</h3>
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
