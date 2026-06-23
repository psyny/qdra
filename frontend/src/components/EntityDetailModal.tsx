import { useState, useEffect } from 'react';
import { Entity, EntityParameter } from '../types/entity';

type EntityDetailModalProps = {
  projectId: string;
  entity: Entity;
  parameters: EntityParameter[];
  isOpen: boolean;
  onClose: () => void;
  onSelection: (selectedParams: EntityParameter[]) => void;
  preselectedParameters?: Array<{ domain: string; key: string }>;
};

export function EntityDetailModal({
  projectId,
  entity,
  parameters,
  isOpen,
  onClose,
  onSelection,
  preselectedParameters = [],
}: EntityDetailModalProps) {
  const [selectedParams, setSelectedParams] = useState<Set<string>>(new Set());

  // Initialize selected params based on preselected parameters
  useEffect(() => {
    const initialSelected = new Set<string>();
    preselectedParameters.forEach((preselected) => {
      const paramKey = `${preselected.domain}:${preselected.key}`;
      initialSelected.add(paramKey);
    });
    setSelectedParams(initialSelected);
  }, [preselectedParameters]);

  // Handle parameter checkbox toggle
  const handleParamToggle = (param: EntityParameter) => {
    const paramKey = `${param.domain}:${param.key}`;
    const newSelected = new Set(selectedParams);
    
    // Check if this is a preselected parameter (should be locked)
    const isPreselected = preselectedParameters.some(
      (p) => p.domain === param.domain && p.key === param.key
    );
    
    if (isPreselected) {
      // Preselected parameters cannot be unchecked
      return;
    }
    
    if (newSelected.has(paramKey)) {
      newSelected.delete(paramKey);
    } else {
      newSelected.add(paramKey);
    }
    setSelectedParams(newSelected);
  };

  // Check if a parameter is preselected
  const isPreselected = (param: EntityParameter) => {
    return preselectedParameters.some(
      (p) => p.domain === param.domain && p.key === param.key
    );
  };

  // Handle select button click
  const handleSelect = () => {
    const selectedParamsList = parameters.filter((param) => {
      const paramKey = `${param.domain}:${param.key}`;
      return selectedParams.has(paramKey);
    });
    onSelection(selectedParamsList);
  };

  // Get parameter value for display
  const getParamValue = (param: EntityParameter): string => {
    if (param.value_string !== null && param.value_string !== undefined) {
      return param.value_string;
    }
    if (param.value_number !== null && param.value_number !== undefined) {
      return String(param.value_number);
    }
    if (param.value_boolean !== null && param.value_boolean !== undefined) {
      return String(param.value_boolean);
    }
    return '';
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.5)',
      backdropFilter: 'blur(4px)',
      zIndex: 1001,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '50px',
    }}>
      <div className="card" style={{ 
        width: '500px',
        height: '100%',
        maxHeight: 'calc(100vh - 100px)', 
        overflowY: 'auto',
        backgroundColor: '#000',
        color: '#fff',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 className="card-title" style={{ color: '#fff' }}>Entity Details</h2>
          <button onClick={onClose} className="button button--secondary">Close</button>
        </div>

        {/* Entity Image */}
        {entity.image && (
          <div style={{ marginBottom: '16px', textAlign: 'center' }}>
            <img
              src={entity.image.url}
              alt={entity.image.alt_text || entity.id}
              style={{ maxWidth: '100%', maxHeight: '300px', objectFit: 'contain' }}
            />
          </div>
        )}

        {/* Entity Info */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontWeight: 'bold', fontSize: '18px', marginBottom: '8px' }}>{entity.id}</div>
          <div style={{ color: '#666', marginBottom: '4px' }}>
            <strong>Type:</strong> {entity.kind}
          </div>
          <div style={{ color: '#666', marginBottom: '4px' }}>
            <strong>Group:</strong> {entity.group}
          </div>
          <div style={{ color: '#666' }}>
            <strong>Entity Type ID:</strong> {entity.entity_type_id}
          </div>
        </div>

        {/* Parameters List */}
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ fontSize: '16px', marginBottom: '12px' }}>Parameters</h3>
          {parameters.length === 0 ? (
            <p style={{ color: '#666' }}>No parameters available.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {parameters.map((param) => {
                const paramKey = `${param.domain}:${param.key}`;
                const isSelected = selectedParams.has(paramKey);
                const isLocked = isPreselected(param);
                
                return (
                  <div
                    key={paramKey}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '8px',
                      backgroundColor: isSelected ? '#f0f8ff' : 'transparent',
                      borderRadius: '4px',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleParamToggle(param)}
                      disabled={isLocked}
                      style={{ width: '18px', height: '18px' }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                        {param.domain}:{param.key}
                        {isLocked && <span style={{ color: '#666', fontSize: '12px', marginLeft: '8px' }}>(locked)</span>}
                      </div>
                      <div style={{ fontSize: '14px', color: '#333' }}>
                        {getParamValue(param)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Select Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button onClick={onClose} className="button button--secondary">
            Cancel
          </button>
          <button
            onClick={handleSelect}
            className="button button--primary"
            disabled={selectedParams.size === 0}
          >
            Select ({selectedParams.size} parameters)
          </button>
        </div>
      </div>
    </div>
  );
}
