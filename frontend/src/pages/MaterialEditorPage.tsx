import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getMaterial, createMaterial, addMaterialParameter } from '../api/materials';
import { Material } from '../types/material';
import { MaterialForm } from '../components/MaterialForm';
import { DraftParameter } from '../components/ParameterRow';

type MaterialEditorPageProps = {
  projectId: string;
};

export function MaterialEditorPage({ projectId }: MaterialEditorPageProps) {
  const { materialId } = useParams<{ materialId: string }>();
  const navigate = useNavigate();
  const [material, setMaterial] = useState<Material | null>(null);
  const [loading, setLoading] = useState(!!materialId);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (materialId) {
      loadMaterial();
    }
  }, [materialId, projectId]);

  const loadMaterial = async () => {
    if (!materialId) return;

    setLoading(true);
    setError(null);
    try {
      const data = await getMaterial(projectId, materialId);
      setMaterial(data);
    } catch (err) {
      setError('Could not load material');
    } finally {
      setLoading(false);
    }
  };

  const draftToApiParam = (p: DraftParameter) => {
    if (p.value_type === 'string') return { domain: p.domain, key: p.key, value_string: String(p.value ?? '') };
    if (p.value_type === 'number') return { domain: p.domain, key: p.key, value_number: Number(p.value ?? 0) };
    if (p.value_type === 'boolean') return { domain: p.domain, key: p.key, value_boolean: Boolean(p.value) };
    return { domain: p.domain, key: p.key, value_string: null };
  };

  const handleSubmit = async (parameters: DraftParameter[]) => {
    setIsSubmitting(true);
    setError(null);

    try {
      if (!materialId) {
        const entity = await createMaterial(projectId, {});
        for (const p of parameters) {
          await addMaterialParameter(projectId, entity.id, draftToApiParam(p));
        }
      }
      navigate(`/projects/${projectId}/materials`);
    } catch (err) {
      setError('Could not save material');
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    navigate(`/projects/${projectId}/materials`);
  };

  if (loading) {
    return (
      <div className="card state-message">
        <p className="state-message__text">Loading material...</p>
      </div>
    );
  }

  if (error && !material) {
    return (
      <div className="card state-message">
        <p className="state-message__text">{error}</p>
        <Link to={`/projects/${projectId}/materials`} className="button button--secondary">
          Back to Materials
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h2 className="card-title mb-4">
        {materialId ? 'Edit Material' : 'New Material'}
      </h2>
      <MaterialForm
        initialParameters={[]}
        isSubmitting={isSubmitting}
        errorMessage={error}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        submitLabel={materialId ? 'Save Material' : 'Create Material'}
      />
    </div>
  );
}
