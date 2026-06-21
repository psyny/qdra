import { useState, useEffect } from 'react';
import { DraftParameter } from './ParameterRow';
import { ImageUpload } from './ImageUpload';
import { Combobox } from './Combobox';
import { getDistinctParameterValues } from '../api/entities';

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
  projectId?: string;
  group?: string;
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
  projectId,
  group,
}: MaterialFormProps) {
  const [parameters, setParameters] = useState<DraftParameter[]>(initialParameters);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(currentImage || null);
  const [hoveredDescription, setHoveredDescription] = useState<string | null>(null);
  const [existingValues, setExistingValues] = useState<Record<string, string[]>>({});
  const [duplicateWarnings, setDuplicateWarnings] = useState<Record<string, boolean>>({});

  // Load existing values for searchable string parameters on mount
  useEffect(() => {
    if (projectId) {
      parameters.forEach(param => {
        if (param.is_searchable && param.value_type === 'string') {
          fetchExistingValues(param.domain, param.key);
        }
      });
    }
  }, [projectId, parameters]);

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

  const updateParameter = (domain: string, key: string, value: any) => {
    const updated = [...parameters];
    const index = updated.findIndex(p => p.domain === domain && p.key === key);
    if (index === -1) return;
    
    updated[index] = { ...updated[index], value };
    setParameters(updated);

    // Check for duplicates if parameter is unique, searchable, and string
    const param = updated[index];
    if (param.is_unique && param.is_searchable && param.value_type === 'string' && typeof value === 'string') {
      checkForDuplicate(param.domain, param.key, value);
    }
  };

  // Helper to fetch existing parameter values
  const fetchExistingValues = async (domain: string, key: string) => {
    if (!projectId || !domain || !key) return [];

    const cacheKey = `${domain}:${key}`;
    if (existingValues[cacheKey]) {
      return existingValues[cacheKey];
    }

    try {
      // Send only the current group to filter values
      const groups = group ? [group] : [];
      const values = await getDistinctParameterValues(projectId, domain, key, groups);
      setExistingValues(prev => ({ ...prev, [cacheKey]: values }));
      return values;
    } catch (err) {
      console.error('Failed to fetch existing values:', err);
      return [];
    }
  };

  // Helper to check for duplicate values for unique parameters
  const checkForDuplicate = async (domain: string, key: string, value: string) => {
    if (!value || !projectId || !domain || !key) {
      setDuplicateWarnings(prev => ({ ...prev, [`${domain}:${key}`]: false }));
      return;
    }

    try {
      const groups = group ? [group] : [];
      const existingValues = await getDistinctParameterValues(projectId, domain, key, groups);
      // When editing, the current entity's value will be in the list
      // Only show warning if value appears more than once (actual duplicate)
      const count = existingValues.filter(v => v === value).length;
      const hasDuplicate = entityId ? count > 1 : count > 0;
      setDuplicateWarnings(prev => ({ ...prev, [`${domain}:${key}`]: hasDuplicate }));
    } catch (err) {
      console.error('Failed to check for duplicates:', err);
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
                        options={existingValues[`${param.domain}:${param.key}`] || []}
                        disabled={isSubmitting}
                        placeholder={`Select or type ${param.label || param.key}...`}
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
                    {param.is_unique && param.is_searchable && duplicateWarnings[`${param.domain}:${param.key}`] && (
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
