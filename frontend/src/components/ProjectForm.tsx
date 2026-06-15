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
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Name *
        </label>
        <input
          id="name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={isSubmitting}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
        />
      </div>
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={isSubmitting}
          rows={3}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
        />
      </div>
      {errorMessage && (
        <p className="text-sm text-red-600">{errorMessage}</p>
      )}
      <div className="flex space-x-2">
        <button
          type="submit"
          disabled={isSubmitting || !name.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Saving...' : submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
