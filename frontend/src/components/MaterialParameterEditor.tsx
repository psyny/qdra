import { ParameterRow, DraftParameter } from './ParameterRow';

type MaterialParameterEditorProps = {
  parameters: DraftParameter[];
  onChange: (parameters: DraftParameter[]) => void;
};

export function MaterialParameterEditor({ parameters, onChange }: MaterialParameterEditorProps) {
  const handleParameterChange = (index: number, parameter: DraftParameter) => {
    const newParameters = [...parameters];
    newParameters[index] = parameter;
    onChange(newParameters);
  };

  const handleAddParameter = () => {
    onChange([
      ...parameters,
      { domain: '', key: '', value: '', value_type: 'string' } as DraftParameter,
    ]);
  };

  const handleRemoveParameter = (index: number) => {
    const newParameters = parameters.filter((_, i) => i !== index);
    onChange(newParameters);
  };

  return (
    <div>
      <div className="parameter-row parameter-row--header">
        <span className="parameter-row__label">Domain</span>
        <span className="parameter-row__label">Key</span>
        <span className="parameter-row__label">Type</span>
        <span className="parameter-row__label">Value</span>
        <span></span>
      </div>
      {parameters.map((parameter, index) => (
        <ParameterRow
          key={index}
          parameter={parameter}
          index={index}
          onChange={handleParameterChange}
          onRemove={handleRemoveParameter}
        />
      ))}
      <button
        type="button"
        onClick={handleAddParameter}
        className="button button--secondary"
      >
        + Add Parameter
      </button>
    </div>
  );
}
