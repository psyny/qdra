import { Link } from 'react-router-dom';
import { Material } from '../types/material';

type MaterialCardProps = {
  material: Material;
  projectId: string;
};

function getMaterialName(material: Material): string {
  const nameParam = material.parameters.find(p => p.domain === 'identity' && p.key === 'name');
  if (nameParam && typeof nameParam.value === 'string') {
    return nameParam.value
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
  return 'Unnamed Material';
}

function getMaterialCategory(material: Material): string | null {
  const categoryParam = material.parameters.find(p => p.domain === 'identity' && p.key === 'category');
  if (categoryParam && typeof categoryParam.value === 'string') {
    return categoryParam.value
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
  return null;
}

export function MaterialCard({ material, projectId }: MaterialCardProps) {
  const name = getMaterialName(material);
  const category = getMaterialCategory(material);

  return (
    <div className="card project-card">
      <div>
        <h3 className="project-card__title">{name}</h3>
        {category && <p className="project-card__description">{category}</p>}
      </div>
      <div className="project-card__actions">
        <Link
          to={`/projects/${projectId}/materials/${material.id}/edit`}
          className="button button--secondary"
        >
          Edit
        </Link>
      </div>
    </div>
  );
}
