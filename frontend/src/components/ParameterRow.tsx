import React from 'react';

export type DraftParameter = {
  domain: string;
  key: string;
  value: string | number | boolean | null;
  value_type: 'string' | 'number' | 'boolean' | 'null';
};

type ParameterRowProps = {
  parameter: DraftParameter;
  index: number;
  onChange: (index: number, parameter: DraftParameter) => void;
  onRemove: (index: number) => void;
};

export function ParameterRow({ parameter, index, onChange, onRemove }: ParameterRowProps) {
  const handleDomainChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(index, { ...parameter, domain: e.target.value });
  };

  const handleKeyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(index, { ...parameter, key: e.target.value });
  };

  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const valueType = parameter.value_type || 'string';
    let value: string | number | boolean | null;

    if (valueType === 'number') {
      value = e.target.value === '' ? 0 : parseFloat(e.target.value);
    } else if (valueType === 'boolean') {
      value = e.target.value === 'true';
    } else {
      value = e.target.value;
    }

    onChange(index, { ...parameter, value });
  };

  const handleValueTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newType = e.target.value as 'string' | 'number' | 'boolean' | 'null';
    let value: string | number | boolean | null;

    if (newType === 'number') {
      value = 0;
    } else if (newType === 'boolean') {
      value = false;
    } else if (newType === 'null') {
      value = null;
    } else {
      value = '';
    }

    onChange(index, { ...parameter, value_type: newType, value });
  };

  const valueType = parameter.value_type || 'string';

  return (
    <div className="parameter-row">
      <input
        type="text"
        placeholder="Domain"
        value={parameter.domain}
        onChange={handleDomainChange}
        className="form-input parameter-row__input"
      />
      <input
        type="text"
        placeholder="Key"
        value={parameter.key}
        onChange={handleKeyChange}
        className="form-input parameter-row__input"
      />
      <select
        value={valueType}
        onChange={handleValueTypeChange}
        className="form-input parameter-row__select"
      >
        <option value="string">String</option>
        <option value="number">Number</option>
        <option value="boolean">Boolean</option>
        <option value="null">Null</option>
      </select>
      {valueType === 'boolean' ? (
        <select
          value={String(parameter.value)}
          onChange={handleValueChange}
          className="form-input parameter-row__input"
        >
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      ) : valueType === 'null' ? (
        <input
          type="text"
          value="null"
          disabled
          className="form-input parameter-row__input"
        />
      ) : (
        <input
          type={valueType === 'number' ? 'number' : 'text'}
          placeholder="Value"
          value={String(parameter.value || '')}
          onChange={handleValueChange}
          className="form-input parameter-row__input"
        />
      )}
      <button
        type="button"
        onClick={() => onRemove(index)}
        className="button button--danger parameter-row__remove"
      >
        Remove
      </button>
    </div>
  );
}
