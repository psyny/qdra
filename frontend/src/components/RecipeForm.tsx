import { useState } from 'react';
import { DraftParameter } from './ParameterRow';
import { ImageUpload } from './ImageUpload';

type SlotGroupConfig = {
  kind: 'requires' | 'consumes' | 'produces';
  min_slots: number;
  max_slots: number;
};

type RecipeFormProps = {
  initialParameters?: DraftParameter[];
  isSubmitting?: boolean;
  errorMessage?: string | null;
  onSubmit: (parameters: DraftParameter[], imageUrl?: string) => void;
  onCancel: () => void;
  submitLabel: string;
  entityId?: string;
  targetImageSize?: number;
  currentImage?: string | null;
  slotGroups?: SlotGroupConfig[];
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
}: RecipeFormProps) {
  const [parameters, setParameters] = useState<DraftParameter[]>(initialParameters);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState<string | null>(currentImage || null);
  
  // State to track current number of slots for each category
  const [slotCounts, setSlotCounts] = useState<Record<string, number>>({
    requires: slotGroups.find(g => g.kind === 'requires')?.min_slots || 0,
    consumes: slotGroups.find(g => g.kind === 'consumes')?.min_slots || 0,
    produces: slotGroups.find(g => g.kind === 'produces')?.min_slots || 0,
  });

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

  // Helper to get slot group config for a kind
  const getSlotGroupConfig = (kind: 'requires' | 'consumes' | 'produces') => {
    return slotGroups.find(g => g.kind === kind);
  };

  // Helper to add a slot
  const addSlot = (kind: 'requires' | 'consumes' | 'produces') => {
    const config = getSlotGroupConfig(kind);
    if (!config) return;
    
    const currentCount = slotCounts[kind];
    // If max_slots is null, it means unlimited
    const maxSlots = config.max_slots === null ? Infinity : config.max_slots;
    if (currentCount < maxSlots) {
      setSlotCounts(prev => ({ ...prev, [kind]: currentCount + 1 }));
    }
  };

  // Helper to remove a specific slot by index
  const removeSlot = (kind: 'requires' | 'consumes' | 'produces', index: number) => {
    const config = getSlotGroupConfig(kind);
    if (!config) return;
    
    const currentCount = slotCounts[kind];
    if (currentCount > config.min_slots) {
      setSlotCounts(prev => ({ ...prev, [kind]: currentCount - 1 }));
    }
  };

  // Helper to render empty slots for a category
  const renderEmptySlots = (kind: 'requires' | 'consumes' | 'produces') => {
    const count = slotCounts[kind];
    const config = getSlotGroupConfig(kind);
    
    if (!config || count === 0) return null;

    return Array.from({ length: count }).map((_, index) => {
      const canRemove = count > config.min_slots;
      return (
        <div key={`${kind}-${index}`} className="form-field mb-4" style={{ padding: '12px', border: '1px dashed #ccc', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ color: '#999', fontStyle: 'italic', margin: 0 }}>
            {kind.charAt(0).toUpperCase() + kind.slice(1)} slot {index + 1} (empty)
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
          className="button button--secondary"
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
        <h3 className="card-title mb-4">Recipe Parameters</h3>
        {sortedParameters.map((param, index) => (
          <div key={`${param.domain}:${param.key}`} className="form-field mb-4">
            {param.value_type === 'boolean' ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', gap: '12px' }}>
                <input
                  id={`param-${index}`}
                  type="checkbox"
                  checked={param.value === true}
                  onChange={(e) => updateParameter(index, e.target.checked)}
                  disabled={isSubmitting}
                  style={{ width: '19px', height: '19px' }}
                />
                <div>
                  <label htmlFor={`param-${index}`} className="form-label" style={{ marginBottom: param.description ? '4px' : '0' }}>
                    {param.label || param.key}
                    {param.required && ' *'}
                  </label>
                  {param.description && (
                    <p className="form-hint">{param.description}</p>
                  )}
                </div>
              </div>
            ) : (
              <>
                <label htmlFor={`param-${index}`} className="form-label">
                  {param.label || param.key}
                  {param.required && ' *'}
                </label>
                {param.description && (
                  <p className="form-hint">{param.description}</p>
                )}
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
