import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getMaterial, createMaterial, updateMaterial } from '../api/materials';
import { Material, MaterialParameter } from '../types/material';
import { MaterialForm } from '../components/MaterialForm';

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

  const handleSubmit = async (parameters: MaterialParameter[]) => {
    setIsSubmitting(true);
    setError(null);

    try {
      if (materialId) {
        await updateMaterial(projectId, materialId, { parameters });
      } else {
        await createMaterial(projectId, { parameters });
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
        initialParameters={material?.parameters || []}
        isSubmitting={isSubmitting}
        errorMessage={error}
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        submitLabel={materialId ? 'Save Material' : 'Create Material'}
      />
    </div>
  );
}
