import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getMaterials } from '../api/materials';
import { Material } from '../types/material';
import { MaterialCard } from '../components/MaterialCard';

type MaterialCatalogPageProps = {
  projectId: string;
};

export function MaterialCatalogPage({ projectId }: MaterialCatalogPageProps) {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const loadMaterials = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMaterials(projectId);
      setMaterials(data);
    } catch (err) {
      setError('Could not load materials');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMaterials();
  }, [projectId]);

  const filteredMaterials = materials.filter(material => {
    const name = material.parameters?.find(p => p.domain === 'identity' && p.key === 'name')?.value;
    const category = material.parameters?.find(p => p.domain === 'identity' && p.key === 'category')?.value;
    const query = searchQuery.toLowerCase();
    
    if (typeof name === 'string' && name.toLowerCase().includes(query)) return true;
    if (typeof category === 'string' && category.toLowerCase().includes(query)) return true;
    return false;
  });

  if (loading) {
    return (
      <div className="card state-message">
        <p className="state-message__text">Loading materials...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card state-message">
        <p className="state-message__text">{error}</p>
        <button onClick={loadMaterials} className="button button--secondary">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="catalog-header">
        <div className="catalog-header__title">
          <h2 className="card-title">Materials</h2>
          <p className="card-description">Create and manage project materials.</p>
        </div>
        <Link
          to={`/projects/${projectId}/materials/new`}
          className="button button--primary"
        >
          + New Material
        </Link>
      </div>

      <div className="mb-6">
        <input
          type="text"
          placeholder="Search materials..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="form-input"
        />
      </div>

      {filteredMaterials.length === 0 ? (
        <div className="card state-message">
          <p className="state-message__text">
            {materials.length === 0 ? 'No materials found.' : 'No materials match your search.'}
          </p>
          {materials.length === 0 && (
            <>
              <p className="state-message__subtext">
                Create your first material to start building recipes.
              </p>
              <Link
                to={`/projects/${projectId}/materials/new`}
                className="button button--primary"
              >
                New Material
              </Link>
            </>
          )}
        </div>
      ) : (
        <div className="project-grid">
          {filteredMaterials.map((material) => (
            <MaterialCard
              key={material.id}
              material={material}
              projectId={projectId}
            />
          ))}
        </div>
      )}
    </div>
  );
}
