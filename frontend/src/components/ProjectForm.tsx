import { useState } from 'react';
import { ProjectTemplate } from '../types/template';

type ProjectFormProps = {
  initialName?: string;
  initialDescription?: string | null;
  initialTemplateId?: string | null;
  initialImageSizePx?: number;
  templates: ProjectTemplate[];
  submitLabel: string;
  isSubmitting?: boolean;
  errorMessage?: string | null;
  onSubmit: (payload: { name: string; project_template_id: string; description?: string | null; image_size_px?: number }) => void;
  onCancel?: () => void;
};

export function ProjectForm({
  initialName = '',
  initialDescription = '',
  initialTemplateId = null,
  initialImageSizePx = 256,
  templates,
  submitLabel,
  isSubmitting = false,
  errorMessage = null,
  onSubmit,
  onCancel,
}: ProjectFormProps) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription || '');
  const [templateId, setTemplateId] = useState(initialTemplateId || '');
  const [imageSizePx, setImageSizePx] = useState(initialImageSizePx);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !templateId) {
      return;
    }
    onSubmit({ 
      name: name.trim(), 
      project_template_id: templateId, 
      description: description.trim() || null,
      image_size_px: imageSizePx
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-field">
        <label htmlFor="template" className="form-label">
          Project Template *
        </label>
        <select
          id="template"
          value={templateId}
          onChange={(e) => setTemplateId(e.target.value)}
          disabled={isSubmitting}
          className="form-select"
        >
          <option value="">Select a template...</option>
          {templates.map((template) => (
            <option key={template.id} value={template.id}>
              {template.name}
            </option>
          ))}
        </select>
      </div>
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
        />
      </div>
      <div className="form-field">
        <label htmlFor="description" className="form-label">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={isSubmitting}
          rows={3}
          className="form-textarea"
        />
      </div>
      <div className="form-field">
        <label htmlFor="imageSizePx" className="form-label">
          Image Size (px)
        </label>
        <input
          id="imageSizePx"
          type="number"
          min="32"
          max="1024"
          step="32"
          value={imageSizePx}
          onChange={(e) => setImageSizePx(Number(e.target.value))}
          disabled={isSubmitting}
          className="form-input"
        />
        <p className="form-hint">Size for material images (32-1024, must be square)</p>
      </div>
      {errorMessage && (
        <p className="form-error">{errorMessage}</p>
      )}
      <div className="form-actions">
        <button
          type="submit"
          disabled={isSubmitting || !name.trim() || !templateId}
          className="button button--primary"
        >
          {isSubmitting ? 'Saving...' : submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="button button--secondary"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
