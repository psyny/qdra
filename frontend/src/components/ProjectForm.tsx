import { useState } from 'react';

type ProjectFormProps = {
  initialName?: string;
  initialDescription?: string | null;
  submitLabel: string;
  isSubmitting?: boolean;
  errorMessage?: string | null;
  onSubmit: (payload: { name: string; description?: string | null }) => void;
  onCancel?: () => void;
};

export function ProjectForm({
  initialName = '',
  initialDescription = '',
  submitLabel,
  isSubmitting = false,
  errorMessage = null,
  onSubmit,
  onCancel,
}: ProjectFormProps) {
  const [name, setName] = useState(initialName);
  const [description, setDescription] = useState(initialDescription || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      return;
    }
    onSubmit({ name: name.trim(), description: description.trim() || null });
  };

  return (
    <form onSubmit={handleSubmit}>
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
      {errorMessage && (
        <p className="form-error">{errorMessage}</p>
      )}
      <div className="form-actions">
        <button
          type="submit"
          disabled={isSubmitting || !name.trim()}
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
