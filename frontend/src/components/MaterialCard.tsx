import { Link } from 'react-router-dom';
import { Material } from '../types/material';

type MaterialCardProps = {
  material: Material;
  projectId: string;
  name?: string;
  category?: string | null;
};

export function MaterialCard({ material, projectId, name = 'Unnamed Material', category }: MaterialCardProps) {

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
